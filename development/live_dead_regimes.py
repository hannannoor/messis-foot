"""Live/dead sequence experiment: reference-independent stress regimes (stage 2 only).

jitter_ball: the existing visible-ball jitter (sigma .25 m, rows ascending, x then y, nothing drawn on missing rows,
distances recomputed), seeded from this experiment's prefix.  Players are untouched, so liveness inputs are identical.

degrade_players: blocks of 125 rows counted from each period run's first row.  Within a (period, block), distinct
non-null (team, id) pairs are ranked by sha256('{prefix}{case}:{period}:{block}:{team}:{id}') ascending and the first
n // 4 are removed from every row of that block.  Retained players then receive independent Gaussian noise (.25 m):
one random.Random per case, rows ascending, home then away, stored order, x then y; non-finite players draw nothing.
Ball-to-nearest-player distances are recomputed on observed-ball rows.  Ball, periods, flags and anything
reference-like are never changed or read.  IDs are the adapter's associations, applied before degradation.
"""
from dataclasses import replace
import hashlib
from math import isfinite
import random

from live_dead_protocol import SEED_PREFIX
from recent_geometry_regimes import JITTER_SIGMA, _nearest

BLOCK = 125
REMOVE_DEN = 4


def _seed(tag, cid):
    return int(hashlib.sha256((SEED_PREFIX + tag + ':' + cid).encode('utf-8')).hexdigest()[:8], 16)


def jitter_seed(cid):
    return _seed('jitter', cid)


def jitter_ball(frames, cid):
    rng = random.Random(jitter_seed(cid))
    out = []
    for f in frames:
        if not f.ball_observed:
            out.append(f)
            continue
        x, y = f.ball_x + rng.gauss(0, JITTER_SIGMA), f.ball_y + rng.gauss(0, JITTER_SIGMA)
        distances = [_nearest(f.home_xy, x, y), _nearest(f.away_xy, x, y)]
        if not (isfinite(x) and isfinite(y)) or any(d is not None and not isfinite(d) for d in distances):
            raise ValueError('Non-finite transformed record')
        out.append(replace(f, ball_x=x, ball_y=y, home_distance=distances[0], away_distance=distances[1]))
    return out


def _blocks(frames):
    """(period, block) per row; None for period 0."""
    out, start, previous = [], 0, None
    for i, f in enumerate(frames):
        if f.period == 0:
            out.append(None)
            previous = None
            continue
        if f.period != previous:
            start = i
        previous = f.period
        out.append((f.period, (i - start) // BLOCK))
    return out


def removal_keys(frames, cid):
    frames = list(frames)
    members = {}
    for f, key in zip(frames, _blocks(frames)):
        if key is None:
            continue
        group = members.setdefault(key, set())
        for team in ('home', 'away'):
            ids = tuple(getattr(f, team + '_ids', ()) or ())
            if len(ids) == len(tuple(getattr(f, team + '_xy', ()) or ())):
                group.update((team, pid) for pid in ids if pid is not None)
    removed = set()
    for (period, block), group in members.items():
        ranked = sorted(group, key=lambda tp: hashlib.sha256(
            f'{SEED_PREFIX}{cid}:{period}:{block}:{tp[0]}:{tp[1]}'.encode('utf-8')).hexdigest())
        removed.update((period, block, team, pid) for team, pid in ranked[:len(ranked) // REMOVE_DEN])
    return removed


def degrade_players(frames, cid):
    frames = list(frames)
    removed = removal_keys(frames, cid)
    rng = random.Random(_seed('degrade-noise', cid))
    out = []
    for f, key in zip(frames, _blocks(frames)):
        if key is None:
            out.append(f)
            continue
        changes = {}
        for team in ('home', 'away'):
            xy = tuple(getattr(f, team + '_xy', ()) or ())
            ids = tuple(getattr(f, team + '_ids', ()) or ())
            if len(ids) == len(xy):
                kept = [(p, pid) for p, pid in zip(xy, ids) if pid is None or key + (team, pid) not in removed]
            else:
                kept = [(p, None) for p in xy]                     # unassociated rows: nothing removable by id
            noisy = []
            for (x, y), pid in kept:
                if isfinite(x) and isfinite(y):
                    x, y = x + rng.gauss(0, JITTER_SIGMA), y + rng.gauss(0, JITTER_SIGMA)
                noisy.append(((x, y), pid))
            changes[team + '_xy'] = tuple(p for p, _ in noisy)
            if len(ids) == len(xy):
                changes[team + '_ids'] = tuple(pid for _, pid in noisy)
        if f.ball_observed:
            changes['home_distance'] = _nearest(changes['home_xy'], f.ball_x, f.ball_y)
            changes['away_distance'] = _nearest(changes['away_xy'], f.ball_x, f.ball_y)
        out.append(replace(f, **changes))
    return out
