"""Player-only liveness features for the live/dead sequence experiment.

Ten values per canonical 25 Hz row (index 0-9):
  0 spatial player count (cap 22) / 22         5 share of usable speeds < 1 m/s
  1 usable speed pairs (cap 22) / 22           6 share of usable speeds > 3 m/s
  2-4 speed quartiles .25/.50/.75 / 12 m/s     7 pooled RMS distance to pooled centroid / pitch diagonal
                                               8 spatial-support mask   9 motion-support mask

A spatial player has a non-null id unique within its team on that row and a finite position.  A usable speed needs
that (team, id) spatial on rows t and t-5, rows t-5..t in one barrier run (same nonzero period, valid geometry) and
displacement / 0.2 s below 12 m/s (faster pairs are dropped, not clipped).  Spatial support needs >= 10 players and
motion support >= 10 speeds; unsupported groups are zero with a zero mask.  Teams are pooled, so swapping home and
away changes nothing.  No ball, availability, status, tag, reference, provider, match, time or half field is read;
the period only forms barriers.

Windows stack the ten values at offsets -50, -45, ..., +50 rows (21 positions, chronological, 210 columns).  A
position outside the recording or in a different barrier run is all zero; nothing is padded.  A row is eligible when
its centre has spatial and motion support and at least five motion-supported positions lie strictly before and five
strictly after it.
"""
from collections import Counter, namedtuple
from math import fsum, hypot, isfinite, sqrt

import numpy as np

from recent_geometry_features import geometry_valid

FRAME_COLUMNS = 10
OFFSETS = tuple(range(-50, 51, 5))
WINDOW_COLUMNS = FRAME_COLUMNS * len(OFFSETS)
CENTRE = OFFSETS.index(0)
SPEED_LAG = 5
MAX_SPEED = 12.
SLOW, FAST = 1., 3.
CAP = 22
MIN_SUPPORT = 10
MIN_SIDE = 5

LivenessInputs = namedtuple('LivenessInputs', 'instant temporal eligible')


def _active(frame):
    return frame.period in (1, 2) and geometry_valid(frame)


def _spatial(frame):
    """{(team, id): (x, y)} for unique non-null ids with finite positions; a team whose ids do not match its
    positions contributes nobody on that row."""
    out = {}
    for team in ('home', 'away'):
        xy = tuple(getattr(frame, team + '_xy', ()) or ())
        ids = tuple(getattr(frame, team + '_ids', ()) or ())
        if len(ids) != len(xy):
            continue
        counts = Counter(ids)
        for pid, (x, y) in zip(ids, xy):
            if pid is not None and counts[pid] == 1 and isfinite(x) and isfinite(y):
                out[(team, pid)] = (float(x), float(y))
    return out


def id_mismatch_rows(frames):
    """Rows where some team's id list length differs from its positions (reported in coverage)."""
    return sum(1 for f in frames for team in ('home', 'away')
               if len(tuple(getattr(f, team + '_ids', ()) or ())) != len(tuple(getattr(f, team + '_xy', ()) or ())))


def barrier_ids(frames):
    """Run id per row; a new run starts at each period change, and every inactive row is its own run."""
    out = np.empty(len(frames), dtype=np.int64)
    run, previous = -1, None
    for i, f in enumerate(frames):
        if not _active(f):
            run += 1
            out[i] = run
            previous = None
            continue
        if previous != f.period:
            run += 1
        out[i] = run
        previous = f.period
    return out


def frame_vectors(frames, pitch):
    frames = list(frames)
    diagonal = hypot(*pitch)
    if not isfinite(diagonal) or diagonal <= 0:
        raise ValueError('Invalid canonical pitch')
    barriers = barrier_ids(frames)
    spatial = [(_spatial(f) if _active(f) else None) for f in frames]
    out = np.zeros((len(frames), FRAME_COLUMNS), dtype=np.float32)
    for t, now in enumerate(spatial):
        if now is None:
            continue
        row = [0.] * FRAME_COLUMNS
        if len(now) >= MIN_SUPPORT:
            pts = list(now.values())
            n = len(pts)
            cx, cy = fsum(p[0] for p in pts) / n, fsum(p[1] for p in pts) / n
            row[0] = min(n, CAP) / CAP
            row[7] = sqrt(fsum((x - cx) ** 2 + (y - cy) ** 2 for x, y in pts) / n) / diagonal
            row[8] = 1.
        s = t - SPEED_LAG
        if s >= 0 and barriers[s] == barriers[t] and spatial[s] is not None:
            before = spatial[s]
            speeds = [v for v in (hypot(x - before[k][0], y - before[k][1]) / (SPEED_LAG / 25.)
                                  for k, (x, y) in now.items() if k in before) if v < MAX_SPEED]
            if len(speeds) >= MIN_SUPPORT:
                values = np.asarray(speeds, dtype=np.float64)
                row[1] = min(len(speeds), CAP) / CAP
                row[2:5] = (np.quantile(values, (.25, .5, .75), method='linear') / MAX_SPEED).tolist()
                row[5] = sum(1 for v in speeds if v < SLOW) / len(speeds)
                row[6] = sum(1 for v in speeds if v > FAST) / len(speeds)
                row[9] = 1.
        out[t] = row
    if not np.isfinite(out).all():
        raise ValueError('Non-finite liveness features')
    return out


def window_matrix(vectors, barriers):
    vectors = np.asarray(vectors, dtype=np.float32)
    barriers = np.asarray(barriers)
    n = len(vectors)
    if vectors.shape != (n, FRAME_COLUMNS) or barriers.shape != (n,):
        raise ValueError('Invalid window inputs')
    out = np.zeros((n, len(OFFSETS), FRAME_COLUMNS), dtype=np.float32)
    rows = np.arange(n)
    for j, k in enumerate(OFFSETS):
        src = rows + k
        ok = (src >= 0) & (src < n)
        ok[ok] &= barriers[src[ok]] == barriers[rows[ok]]
        out[ok, j] = vectors[src[ok]]
    return out.reshape(n, WINDOW_COLUMNS)


def eligibility(windows, active):
    w = np.asarray(windows).reshape(len(windows), len(OFFSETS), FRAME_COLUMNS)
    motion = w[:, :, 9] == 1
    return (np.asarray(active, dtype=bool) & (w[:, CENTRE, 8] == 1) & motion[:, CENTRE]
            & (motion[:, :CENTRE].sum(axis=1) >= MIN_SIDE) & (motion[:, CENTRE + 1:].sum(axis=1) >= MIN_SIDE))


def liveness_inputs(frames, pitch):
    frames = list(frames)
    vectors = frame_vectors(frames, pitch)
    temporal = window_matrix(vectors, barrier_ids(frames))
    active = np.fromiter((_active(f) for f in frames), dtype=bool, count=len(frames))
    eligible = eligibility(temporal, active)
    for array in (vectors, temporal, eligible):
        array.setflags(write=False)
    return LivenessInputs(vectors, temporal, eligible)
