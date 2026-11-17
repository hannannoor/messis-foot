"""Research-only whole-team geometry; the original eighteen features remain untouched.

Pitch midpoint is required from the caller's loader metadata. Direction uses tracking
only, once per team/period. Unsupported slots occupy time and never become observations.
"""
from collections import deque
from math import fsum, hypot, isfinite, sqrt
import numpy as np
from gap_solver.tactical import FEATURE_NAMES, feature_rows
from recent_geometry_features import geometry_valid

WINDOW = 25
VELOCITY_LAG = 5
MIN_PLAYERS = 7
NEW_NAMES = ('shape_spread_diff', 'shape_advance_diff', 'shape_closing_diff', 'shape_support')
RESEARCH_FEATURE_NAMES = tuple(FEATURE_NAMES) + NEW_NAMES


def provider_midpoint(provider, notes=None):
    """Canonical x of the loader's native pitch centre, with the authorised exact check.

    DFL and SkillCorner both map centred native x as (x / length + .5) *
    canonical_length. At their native centre x/length is exactly zero. Use
    the loader's canonical pitch metadata for its scale, before float32 storage.
    WCSF exposes its own canonical transform directly.
    """
    if provider == 'wcsf':
        from wcsf_geometry import _canonical
        midpoint = _canonical(0,0)[0]
    elif provider in ('dfl','skillcorner'):
        pitch = notes['canonical_pitch_m']
        if len(pitch) != 2 or any(not isfinite(v) or v <= 0 for v in pitch):
            raise ValueError('Invalid loader pitch metadata')
        midpoint = (0.0 + .5) * pitch[0]
    else:
        raise ValueError('Unknown external provider')
    if midpoint != 52.65:
        raise ValueError('Loader native-centre midpoint differs from exactly 52.65')
    return midpoint


def counted_players(frame, side):
    return tuple((float(x), float(y)) for x, y in getattr(frame, side + '_xy')
                 if isfinite(x) and isfinite(y))


def shape_valid(frame, side):
    return frame.period in (1, 2) and geometry_valid(frame) and len(counted_players(frame, side)) >= MIN_PLAYERS


def _centroid(points):
    return tuple(fsum(p[k] for p in points) / len(points) for k in (0, 1))


def attacking_directions(frames, pitch_midpoint):
    if not isfinite(pitch_midpoint):
        raise ValueError('Finite loader pitch midpoint required')
    values = {}
    for f in frames:
        geometry_valid(f)
        if f.period not in (1, 2):
            continue
        pair = values.setdefault(f.period, ([], []))
        for k, side in enumerate(('home', 'away')):
            if shape_valid(f, side):
                pair[k].append(_centroid(counted_players(f, side))[0])
    out = {}
    for period, pair in values.items():
        if any(not v for v in pair):
            raise ValueError(f'period {period}: no shape-valid rows for a team')
        h, a = (fsum(v) / len(v) for v in pair)
        # Amendment 2: direction comes from the order of the two team means only; a dominant team can
        # pull both means to one side of halfway, so only an exact tie is ambiguous.
        if h == a:
            raise ValueError(f'period {period}: team means tied')
        out[period] = (1, -1) if h < a else (-1, 1)
    return out


def id_support(frames):
    return all(any(getattr(f, side + '_ids', ()) for f in frames) for side in ('home', 'away'))


def _identified(frame, side):
    points, ids = getattr(frame, side + '_xy'), getattr(frame, side + '_ids')
    if not ids:
        return None
    if len(points) != len(ids) or len(set(ids)) != len(ids):
        raise ValueError('Malformed player identity/position correspondence')
    return {pid: (float(x), float(y)) for pid, (x,y) in zip(ids, points) if isfinite(x) and isfinite(y)}


def _closing(frame, earlier, side):
    now, old = _identified(frame, side), _identified(earlier, side)
    if now is None or old is None:
        return None
    count = 0
    for pid, (x,y) in now.items():
        if pid not in old:
            continue
        dx, dy = frame.ball_x - x, frame.ball_y - y
        distance = hypot(dx, dy)
        if 0 < distance <= 15.:
            px, py = old[pid]
            towards = ((x-px)*dx + (y-py)*dy) / (.2 * distance)
            count += int(towards > 1.)
    return count


def research_rows(frames, *, pitch_midpoint):
    frames = list(frames)
    directions = attacking_directions(frames, pitch_midpoint)
    has_ids = id_support(frames)
    history = deque(maxlen=26)
    previous = None
    for f, base in zip(frames, feature_rows(frames)):
        valid = geometry_valid(f)
        if f.period != previous or f.period == 0 or not valid:
            history.clear()
        previous = f.period
        if f.period not in (1,2) or not valid:
            yield tuple(base) + (0.,0.,0.,0.)
            continue
        points = tuple(counted_players(f, s) for s in ('home','away'))
        joint = all(len(p) >= MIN_PLAYERS for p in points)
        centroids = tuple(_centroid(p) for p in points) if joint else None
        spread = None
        if joint:
            rms = [sqrt(fsum((x-c[0])**2 + (y-c[1])**2 for x,y in p) / len(p))
                   for p,c in zip(points,centroids)]
            spread = rms[0] - rms[1]
        history.append((f, centroids, spread))
        supported = [v[2] for v in list(history)[-25:] if v[2] is not None]
        spread_value = fsum(supported) / len(supported) if supported else 0.
        advance = closing = 0.
        advance_supported = joint and len(history) == 26 and history[0][1] is not None
        if advance_supported:
            before = history[0][1]
            hdir, adir = directions[f.period]
            advance = hdir * (centroids[0][0] - before[0][0]) - adir * (centroids[1][0] - before[1][0])
        if has_ids and len(history) >= 6 and f.ball_observed:
            earlier = history[-6][0]
            counts = [_closing(f, earlier, side) for side in ('home','away')]
            if all(c is not None for c in counts):
                closing = float(counts[0] - counts[1])
        yield tuple(base) + (spread_value, advance, closing, float(bool(supported) and advance_supported))


def research_matrix(frames, *, pitch_midpoint):
    matrix = np.asarray(list(research_rows(frames, pitch_midpoint=pitch_midpoint)), dtype=np.float32)
    if matrix.ndim != 2 or matrix.shape[1] != 22 or not np.isfinite(matrix).all():
        raise ValueError('Invalid research feature matrix')
    return matrix


def coverage_support(frames):
    """Geometry-only support indicator; no ball, direction, tree or reference access."""
    history = deque(maxlen=26)
    previous = None
    out = []
    for f in frames:
        valid = geometry_valid(f)
        if f.period != previous or f.period == 0 or not valid:
            history.clear()
        previous = f.period
        if f.period not in (1,2) or not valid:
            out.append(False)
            continue
        joint = all(shape_valid(f,side) for side in ('home','away'))
        history.append(joint)
        out.append(bool(joint and len(history)==26 and history[0]))
    return out
