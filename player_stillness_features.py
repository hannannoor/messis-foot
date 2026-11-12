"""Experiment E: player stillness as dead-ball evidence; the original eighteen features stay untouched.

A player's speed on row t is the distance from their position on row t - 5 (same period, same player id on the
same team, both positions finite, id unique within its row) divided by 0.2 s.  ``still_share`` is the share of
players with a speed whose speed is below 1.0 m/s, over both teams, averaged over the trailing 50 rows on which at
least 14 players have a speed.  ``still_support`` is 1.0 when the current row has at least 14 such players.
History clears at a period change, at period 0 and on invalid geometry.  No ball, reference, status or tag field
is read for the new columns.
"""
from collections import Counter, deque
from math import fsum, hypot, isfinite

import numpy as np

from gap_solver.tactical import FEATURE_NAMES, feature_rows
from recent_geometry_features import geometry_valid

SPEED_LAG = 5
STILL_SPEED = 1.0
WINDOW = 50
MIN_PLAYERS = 14
NEW_NAMES = ('still_share', 'still_support')
RESEARCH_FEATURE_NAMES = tuple(FEATURE_NAMES) + NEW_NAMES


def _positions(frame):
    """{(side, id): (x, y)} for players with a finite position and an id unique within its team on this row."""
    out = {}
    for side in ('home', 'away'):
        xy = getattr(frame, side + '_xy', ()) or ()
        ids = getattr(frame, side + '_ids', ()) or ()
        if len(ids) != len(xy):
            continue
        counts = Counter(ids)
        for pid, (x, y) in zip(ids, xy):
            if counts[pid] == 1 and isfinite(x) and isfinite(y):
                out[(side, pid)] = (float(x), float(y))
    return out


def stillness_rows(frames):
    frames = list(frames)
    history = deque(maxlen=SPEED_LAG + 1)      # positions of the last six rows
    window = deque(maxlen=WINDOW)              # per row: share if the row qualifies, else None
    previous = None
    for f, base in zip(frames, feature_rows(frames)):
        valid = geometry_valid(f)
        if f.period != previous or f.period == 0 or not valid:
            history.clear()
            window.clear()
        previous = f.period
        if f.period not in (1, 2) or not valid:
            yield tuple(base) + (0., 0.)
            continue
        now = _positions(f)
        history.append(now)
        share = None
        if len(history) == SPEED_LAG + 1:
            before = history[0]
            speeds = [hypot(x - before[key][0], y - before[key][1]) / (SPEED_LAG / 25.)
                      for key, (x, y) in now.items() if key in before]
            if len(speeds) >= MIN_PLAYERS:
                share = sum(1 for v in speeds if v < STILL_SPEED) / len(speeds)
        window.append(share)
        qualified = [v for v in window if v is not None]
        value = fsum(qualified) / len(qualified) if qualified else 0.
        yield tuple(base) + (value, 1. if share is not None else 0.)


def stillness_matrix(frames):
    matrix = np.asarray(list(stillness_rows(frames)), dtype=np.float32)
    if matrix.ndim != 2 or matrix.shape[1] != 20 or not np.isfinite(matrix).all():
        raise ValueError('Invalid stillness feature matrix')
    return matrix
