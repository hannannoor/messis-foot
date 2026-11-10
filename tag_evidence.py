"""Smart Tagging as weak ownership evidence: one extra term in the control's emissions.

Pure functions, standard library only. With no usable tags every function leaves the control's
emissions untouched, so the decoded labels equal the control's.
"""
from dataclasses import dataclass
from math import log
import xml.etree.ElementTree as ET

from gap_solver.soft_sequence import decode_soft, soft_emissions

FPS = 25
SWITCH_COST = 32.
ATTACK_CODES = frozenset({'BUILD UP', 'PROGRESSION', 'CREATING CHANCES', 'ATTACKING TRANSITION', 'LONG BALL'})
MIN_FRAMES = 2000
MIN_RELIABILITY = .65
MAX_RELIABILITY = .95
CONFIDENT_QUANTILE_NUM = 3   # 75th percentile = 3/4


@dataclass(frozen=True)
class Tag:
    team: str
    start: float
    end: float


@dataclass(frozen=True)
class Estimate:
    enabled: bool
    reason: str
    mapping: object      # {team name: 'H' or 'A'} or None
    p: float             # reliability, capped
    agreement: float     # a: share where "first name means H" agrees
    frames: int          # confident frames that have a tag owner
    threshold: float     # margin threshold (75th percentile)


def _normal(text):
    return ' '.join((text or '').upper().split())


def read_tags(path):
    """Attacking-code instances with a real team, in file order."""
    result = []
    for item in ET.parse(path).iter('instance'):
        if _normal(item.findtext('code')) not in ATTACK_CODES:
            continue
        team = None
        for label in item.findall('label'):
            if _normal(label.findtext('group')) == 'TEAM':
                team = ' '.join((label.findtext('text') or '').split())
        if not team or _normal(team) == 'N/A':
            continue
        result.append(Tag(team, float(item.findtext('start')), float(item.findtext('end'))))
    return tuple(result)


def owner_track(tags, periods):
    """Per frame: index into the sorted team names when exactly one team's windows cover it, else -1."""
    n = len(periods)
    names = tuple(sorted({tag.team for tag in tags}))
    cover = {name: bytearray(n) for name in names}
    for tag in tags:
        first, stop = max(0, round(tag.start * FPS)), min(n, round(tag.end * FPS))
        if stop > first:
            cover[tag.team][first:stop] = b'\1' * (stop - first)
    owner = [-1] * n
    for i in range(n):
        if periods[i] not in (1, 2):
            continue
        hits = [k for k, name in enumerate(names) if cover[name][i]]
        if len(hits) == 1:
            owner[i] = hits[0]
    return owner, names


def control_rows(supports, periods, usable, observed):
    """The control's emission rows and decoding mask, built as decode_ball_gap builds them."""
    n = len(periods)
    rows = soft_emissions(supports, [0.] * n, 0.)
    rows = [row if seen else (0., 0., 0.) for row, seen in zip(rows, observed)]
    effective = list(usable)
    i = 0
    while i < n:
        if not periods[i] or not usable[i]:
            i += 1
            continue
        first, period = i, periods[i]
        while i < n and periods[i] == period and usable[i]:
            i += 1
        if not any(observed[first:i]):
            effective[first:i] = [False] * (i - first)
    return rows, effective


def decode_rows(rows, periods, effective):
    return decode_soft(rows, periods, effective, SWITCH_COST)


def _margin(row, label):
    return row[0] - row[1] if label == 'H' else row[1] - row[0]


def margins(labels, rows, observed, periods):
    """Control owner margins on graded, ball-observed frames the control labelled H or A (index, margin)."""
    return [(i, _margin(rows[i], v)) for i, v in enumerate(labels) if v in ('H', 'A') and observed[i] and periods[i] in (1, 2)]


def estimate_mapping(labels, rows, observed, periods, owner, names):
    pairs = margins(labels, rows, observed, periods)
    if not pairs:
        return Estimate(False, 'no confident frames', None, .5, .5, 0, 0.)
    ordered = sorted(m for _, m in pairs)
    threshold = ordered[(CONFIDENT_QUANTILE_NUM * len(ordered) + 3) // 4 - 1]
    agree = total = 0
    for i, m in pairs:
        if m < threshold or owner[i] < 0:
            continue
        total += 1
        agree += (owner[i] == 0) == (labels[i] == 'H')
    a = agree / total if total else .5
    p = min(max(a, 1 - a), MAX_RELIABILITY)
    reason = ''
    if len(names) != 2:
        reason = 'tags do not name exactly two teams'
    elif total < MIN_FRAMES:
        reason = 'fewer than the minimum confident tagged frames'
    elif max(a, 1 - a) < MIN_RELIABILITY:
        reason = 'reliability below minimum'
    if reason:
        return Estimate(False, reason, None, p, a, total, threshold)
    first, second = ('H', 'A') if a >= .5 else ('A', 'H')
    return Estimate(True, '', {names[0]: first, names[1]: second}, p, a, total, threshold)


def fuse(rows, owner, mapping, names, p):
    """Add ln(2p) to the mapped side and ln(2(1-p)) to the other side on frames with an owner; D unchanged."""
    gain, loss = log(2 * p), log(2 * (1 - p))
    side = {k: 0 if mapping[name] == 'H' else 1 for k, name in enumerate(names)}
    result = []
    for row, who in zip(rows, owner):
        if who < 0:
            result.append(row)
            continue
        mine = side[who]
        new = list(row)
        new[mine] += gain
        new[1 - mine] += loss
        result.append(tuple(new))
    return result
