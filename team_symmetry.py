"""Experiment C: team-symmetric emissions for the frozen decision tree.  No fits, no parameters.

The swap map exchanges the roles of the home and away team in an 18-column ``gap_solver.tactical.feature_rows`` row.
The candidate's supports are the frozen tree's supports symmetrised over that swap:

    p = tree(x), q = tree(swap(x))          sH = (pH + qA) / 2,  sA = (pA + qH) / 2,  sD = (pD + qD) / 2

Nothing here touches a protected release module; the tree is evaluated with ``memory_ablation.predict_supports``
(the same float32 split comparisons as the release's portable tree).
"""
from dataclasses import replace
from math import isfinite

import numpy as np

from gap_solver.tactical import FEATURE_NAMES
from memory_ablation import predict_supports

# (feature name, rule) per zero-based column.  Rules: same | exchange:<partner> | negate.
ROLES = (
    ('ball_observed', 'same'),
    ('home_observed', 'exchange:2'), ('away_observed', 'exchange:1'),
    ('home_distance', 'exchange:4'), ('away_distance', 'exchange:3'),
    ('distance_margin', 'negate'),                       # a - h
    ('min_distance', 'same'),
    ('ball_edge_x', 'same'), ('ball_edge_y', 'same'),    # absolute offsets from the centre
    ('ball_speed', 'same'), ('recent_speed', 'same'), ('slow_ball_age', 'same'), ('missing_ball_age', 'same'),
    ('last_home_distance', 'exchange:14'), ('last_away_distance', 'exchange:13'),
    ('last_control_home', 'exchange:16'), ('last_control_away', 'exchange:15'),
    ('last_control_age', 'same'),
)
PERMUTATION = tuple(int(rule.split(':')[1]) if rule.startswith('exchange:') else i for i, (_, rule) in enumerate(ROLES))
NEGATED = tuple(i for i, (_, rule) in enumerate(ROLES) if rule == 'negate')
LEAF = 22


def check_schema(feature_names=FEATURE_NAMES):
    """Stop if any feature's team role differs from the swap table."""
    if tuple(feature_names) != tuple(name for name, _ in ROLES):
        raise ValueError('Feature schema differs from the swap table')
    for i, (name, rule) in enumerate(ROLES):
        if rule.startswith('exchange:'):
            partner = int(rule.split(':')[1])
            if ROLES[partner][1] != 'exchange:' + str(i) or partner == i:
                raise ValueError('Swap table is not an involution')
            if name.replace('home', 'X').replace('away', 'home').replace('X', 'away') != ROLES[partner][0]:
                raise ValueError('Exchanged features are not a home/away pair')
    return True


check_schema()


def swap_row(row):
    """Team-swap one 18-value feature row.  Negation is ``0.0 - x`` so a tied margin stays +0.0 (never -0.0)."""
    values = tuple(row)
    if len(values) != len(ROLES):
        raise ValueError('Feature row must have 18 values')
    out = [values[j] for j in PERMUTATION]
    for i in NEGATED:
        out[i] = 0.0 - values[i]
    return tuple(out)


def swap_matrix(matrix):
    """Team-swap an (n, 18) matrix; returns a new array of the same dtype."""
    x = np.asarray(matrix)
    if x.ndim != 2 or x.shape[1] != len(ROLES):
        raise ValueError('Feature matrix must have 18 columns')
    out = np.array(x[:, PERMUTATION], copy=True)
    for i in NEGATED:
        out[:, i] = x.dtype.type(0.0) - x[:, i]
    return out


def swap_frame(frame):
    """The same moment with the roles of the two teams exchanged."""
    changes = dict(home_distance=frame.away_distance, away_distance=frame.home_distance)
    if hasattr(frame, 'home_xy'):
        changes.update(home_xy=frame.away_xy, away_xy=frame.home_xy, home_ids=frame.away_ids, away_ids=frame.home_ids)
    if frame.tag_team in ('H', 'A'):
        changes['tag_team'] = 'A' if frame.tag_team == 'H' else 'H'
    return replace(frame, **changes)


def swap_frames(frames):
    return [swap_frame(f) for f in frames]


def _supports(value):
    x = np.asarray(value, dtype=np.float64)
    if x.ndim != 2 or x.shape[1] != 3 or not np.isfinite(x).all():
        raise ValueError('Supports must be a finite (n, 3) array')
    return x


def symmetrise(p, q):
    """sH = (pH + qA)/2, sA = (pA + qH)/2, sD = (pD + qD)/2 where q are the supports of the swapped rows."""
    p, q = _supports(p), _supports(q)
    if p.shape != q.shape:
        raise ValueError('Support shapes differ')
    return np.stack([(p[:, 0] + q[:, 1]) / 2, (p[:, 1] + q[:, 0]) / 2, (p[:, 2] + q[:, 2]) / 2], axis=1)


def control_supports(matrix, model):
    """The frozen tree's own supports (one tree pass)."""
    return predict_supports(matrix, model)


def candidate_supports(matrix, model):
    """Team-symmetrised supports (two tree passes: the rows and their swap)."""
    matrix = np.asarray(matrix, dtype=np.float32)
    return symmetrise(predict_supports(matrix, model), predict_supports(swap_matrix(matrix), model))


def symmetry_error(matrix, model):
    """max |candidate(swap x) - candidate(x) with H and A exchanged|; zero up to round-off by construction."""
    matrix = np.asarray(matrix, dtype=np.float32)
    s = candidate_supports(matrix, model)
    t = candidate_supports(swap_matrix(matrix), model)
    return float(np.abs(t - s[:, [1, 0, 2]]).max()) if len(s) else 0.0


def leaf_index(matrix, model):
    """Leaf node reached by each row (same float32 comparisons as ``predict_supports``)."""
    x = np.asarray(matrix, dtype=np.float32)
    nodes = np.zeros(len(x), dtype=np.int32)
    left, right = np.asarray(model['children_left']), np.asarray(model['children_right'])
    feature, threshold = np.asarray(model['feature']), np.asarray(model['threshold'], dtype=np.float64)
    while True:
        active = np.flatnonzero(left[nodes] != -1)
        if not len(active):
            return nodes
        at = nodes[active]
        nodes[active] = np.where(x[active, feature[at]] <= threshold[at], left[at], right[at])


def check_leaf_22(model):
    """Leaf 22 must be: recent_speed > 0.0104, last_control_away <= 0.5, last_control_age > 1.54, slow_ball_age <= 0.02."""
    names = list(model['feature_names'])
    left, right = model['children_left'], model['children_right']
    if left[LEAF] != -1:
        raise ValueError('Node 22 is not a leaf')
    parent = {}
    for i, (l, r) in enumerate(zip(left, right)):
        if l != -1:
            parent[l], parent[r] = (i, '<='), (i, '>')
    path, node = [], LEAF
    while node in parent:
        i, direction = parent[node]
        path.append((names[model['feature'][i]], direction, model['threshold'][i]))
        node = i
    expect = (('recent_speed', '>', .0104), ('last_control_away', '<=', .5), ('last_control_age', '>', 1.54), ('slow_ball_age', '<=', .02))
    path = path[::-1]
    if len(path) != 4 or any(a[0] != b[0] or a[1] != b[1] or abs(a[2] - b[2]) > 1e-3 for a, b in zip(path, expect)):
        raise ValueError('Node 22 is not the described leaf')
    return True


_SUMS = ('usable_rows', 'ball_missing_rows', 'leaf22_rows', 'argmax_differs_rows', 'control_sum', 'control_missing_sum',
         'candidate_sum', 'candidate_missing_sum')


def _derive(raw):
    n, m = raw['usable_rows'], raw['ball_missing_rows']
    return dict(raw,
                control_mean_h_minus_a=raw['control_sum'] / n if n else None,
                control_mean_h_minus_a_ball_missing=raw['control_missing_sum'] / m if m else None,
                candidate_mean_h_minus_a=raw['candidate_sum'] / n if n else None,
                candidate_mean_h_minus_a_ball_missing=raw['candidate_missing_sum'] / m if m else None,
                # (lean(x) + lean(swap x)) / 2 = lean_p - lean_s: the team-label lean the symmetrisation removes.  It is 0 for
                # the candidate by construction; the candidate's own mean above is NOT expected to be 0 when the match
                # itself is lopsided (it then reflects who is actually in control).
                label_lean_removed_mean=(raw['control_sum'] - raw['candidate_sum']) / n if n else None,
                label_lean_removed_mean_ball_missing=(raw['control_missing_sum'] - raw['candidate_missing_sum']) / m if m else None,
                leaf22_share=raw['leaf22_rows'] / n if n else None,
                argmax_differs_share=raw['argmax_differs_rows'] / n if n else None)


def bias_summary(p, s, usable, observed, leaves, leaf=LEAF):
    """Descriptive home-lean statistics over usable rows (no score, no gate).

    ``p`` frozen supports, ``s`` symmetrised supports; the argmax is over (H, A, D) with ties to the first class.
    """
    p, s = _supports(p), _supports(s)
    usable, observed, leaves = np.asarray(usable, dtype=bool), np.asarray(observed, dtype=bool), np.asarray(leaves)
    if not (len(p) == len(s) == len(usable) == len(observed) == len(leaves)):
        raise ValueError('Bias inputs differ in length')
    missing = usable & ~observed
    lean_p, lean_s = p[:, 0] - p[:, 1], s[:, 0] - s[:, 1]
    raw = dict(usable_rows=int(usable.sum()), ball_missing_rows=int(missing.sum()),
               leaf22_rows=int((usable & (leaves == leaf)).sum()),
               argmax_differs_rows=int((usable & (p.argmax(axis=1) != s.argmax(axis=1))).sum()),
               control_sum=float(lean_p[usable].sum()), control_missing_sum=float(lean_p[missing].sum()),
               candidate_sum=float(lean_s[usable].sum()), candidate_missing_sum=float(lean_s[missing].sum()))
    return _derive(raw)


def merge_bias(summaries):
    """Pool several summaries by adding counts and sums (not by averaging means)."""
    summaries = list(summaries)
    return _derive({key: sum(row[key] for row in summaries) for key in _SUMS})
