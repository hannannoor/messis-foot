"""Ball-flag reference for the public Metrica samples (round 10 audit fix).

In these samples the ball coordinates are an in-play flag: they disappear one frame after play stops and return on the
restart frame. Dead ball therefore comes from the ball flag; owners still come from the event log exactly as in
metrica_event_reference. Thresholds were fixed from the gap structure of the three games, before any rescoring
(docs/superpowers/specs/2026-11-16-round10-audit-fixes-design.md). External public data only.
"""
from collections import defaultdict

from metrica_event_reference import ACTIONS, KINDS

DEAD_GAP = 25     # frames: a ball-missing run at least this long is dead ball
GLITCH_GAP = 12   # frames: a ball-missing run at most this long is a tracking glitch (the owner carries)
SEEN, UNKNOWN, DEAD = 0, 1, 2


def gap_classes(periods, observed):
    """Per frame: SEEN (ball seen or a glitch), UNKNOWN (13-24 frame gap) or DEAD (gap of DEAD_GAP or more)."""
    n = len(periods)
    result = [SEEN] * n
    i = 0
    while i < n:
        if not periods[i] or observed[i]:
            i += 1
            continue
        first, period = i, periods[i]
        while i < n and periods[i] == period and not observed[i]:
            i += 1
        length = i - first
        if length > GLITCH_GAP:
            result[first:i] = [DEAD if length >= DEAD_GAP else UNKNOWN] * length
    return result


def _single(teams):
    teams = set(teams)
    return next(iter(teams)) if len(teams) == 1 and '' not in teams else 'X'


def build_ball_reference(events, periods, observed):
    n = len(periods)
    if len(observed) != n or any(type(p) is not int or p not in (0, 1, 2) for p in periods):
        raise ValueError('Invalid reference periods/observed flags')
    for e in events:
        if (e.period not in (1, 2) or type(e.start) is not int or type(e.end) is not int or not -1 <= e.start <= e.end
                or e.team not in ('H', 'A', '') or e.kind not in KINDS):
            raise ValueError('Invalid normalized event')
    gap = gap_classes(periods, observed)
    labels = ['X'] * n
    conflicts = reopened = reopened_frames = 0
    i = 0
    while i < n:
        if not periods[i]:
            i += 1
            continue
        first, period = i, periods[i]
        while i < n and periods[i] == period:
            i += 1
        stop = i
        selected = [e for e in events if e.period == period and e.end >= first and e.start < stop and e.kind != 'CARD']
        if not selected:
            continue
        coverage_end = max(min(e.end, stop - 1) for e in selected)
        points = defaultdict(list)
        for e in selected:
            start, end = max(first, e.start), min(stop - 1, e.end)
            is_stop = e.kind in ('BALL OUT', 'FAULT RECEIVED') or bool({'FAULT', 'GOAL'}.intersection(e.subtypes))
            if e.kind in ACTIONS:
                points[start].append(('owner', e.team))
            if e.kind == 'SET PIECE':
                points[start].append(('restart', e.team))
            if e.kind == 'CHALLENGE' and not is_stop:
                if 'WON' in e.subtypes and 'LOST' in e.subtypes:
                    raise ValueError('Conflicting challenge outcomes')
                team = e.team if 'WON' in e.subtypes else {'H': 'A', 'A': 'H'}.get(e.team, '') if 'LOST' in e.subtypes else ''
                points[end].append(('owner', team))
            if is_stop:
                points[end].append(('stop', 'D'))
        owner = 'X'
        pending = None   # first frame of an event stop that no ball gap or set piece has confirmed yet
        for at in range(first, coverage_end + 1):
            point = points.get(at, ())
            restarts = [team for kind, team in point if kind == 'restart']
            stops = any(kind == 'stop' for kind, _ in point)
            owners = [team for kind, team in point if kind == 'owner']
            if gap[at] == DEAD:
                if at == first or gap[at - 1] != DEAD:
                    owner = 'X'   # a stoppage clears the owner; the restart or the next owner event sets it again
                pending = None    # the ball flag confirms any pending event stop
                if restarts:
                    owner = _single(restarts)
                elif owners:
                    owner = _single(owners)
                labels[at] = 'D'
                continue
            if restarts:
                owner = _single(restarts)
                conflicts += int(owner == 'X')
                pending = None
            elif stops:
                if pending is None:
                    pending = at
            elif owners:
                if pending is not None:   # play went on with the ball in view: not a stoppage, status unknown
                    for j in range(pending, at):
                        if labels[j] == 'D' and gap[j] != DEAD:
                            labels[j] = 'X'
                            reopened_frames += 1
                    pending = None
                    reopened += 1
                owner = _single(owners)
                conflicts += int(owner == 'X')
            labels[at] = 'X' if gap[at] == UNKNOWN else 'D' if pending is not None else owner
    summary = dict(events=len(events), conflict_frames=conflicts, reopened_stops=reopened, reopened_frames=reopened_frames,
                   dead_gap_frames=sum(v == DEAD for v in gap), unknown_gap_frames=sum(v == UNKNOWN for v in gap),
                   known_frames=sum(v != 'X' for v in labels), label_counts={v: labels.count(v) for v in 'HADX'})
    return tuple(labels), summary
