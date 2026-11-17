"""Live/dead sequence experiment: fitting rows, the two forests and a portable forest exporter.

Rows: every fifth canonical row with known H/A/D reference that is temporally eligible (windows are built on the full
natural motion frames first).  Target 1 for D, 0 for H/A.  Each training match has unit total weight; classes are not
balanced.  Exactly two fits with the fixed recipe: ``instant`` (ten centre values) then ``temporal`` (210 values), on
identical rows, targets and weights.

The exported forest replays scikit-learn exactly: X as float32, ``x <= threshold`` against the float64 threshold,
per-node class-1 fraction ``v1 / (v0 + v1)``, accumulated tree by tree and divided by the tree count.
"""
from dataclasses import dataclass
from math import isfinite

import numpy as np

from live_dead_features import FRAME_COLUMNS, OFFSETS, WINDOW_COLUMNS, liveness_inputs
from memory_ablation_training import model_digest, semantic_digest

PARAMETERS = dict(n_estimators=32, max_depth=6, min_samples_leaf=125, max_features=1.0, bootstrap=True,
                  criterion='gini', class_weight=None, random_state=1729, n_jobs=1)
FIT_ORDER = ('instant', 'temporal')
MIN_ROWS, MIN_CLASS = 1000, 125
PARITY_TOLERANCE = 1e-12
MAX_NODES = 4095


def _frozen(array, dtype=None):
    value = np.array(array, dtype=dtype, copy=True, order='C')
    value.setflags(write=False)
    return value


@dataclass(frozen=True)
class TrainingSet:
    instant: object
    temporal: object
    target: object
    weights: object
    row_identity: object
    counts: tuple

    def __post_init__(self):
        n = len(self.target)
        checks = ((self.instant, (n, FRAME_COLUMNS)), (self.temporal, (n, WINDOW_COLUMNS)))
        if any(np.shape(a) != s for a, s in checks) or np.shape(self.weights) != (n,) or np.shape(self.row_identity) != (n, 2):
            raise ValueError('Inconsistent training set dimensions')
        for name, dtype in (('instant', np.float32), ('temporal', np.float32), ('target', np.uint8),
                            ('weights', np.float64), ('row_identity', np.int64)):
            object.__setattr__(self, name, _frozen(getattr(self, name), dtype))
        if not (np.isfinite(self.instant).all() and np.isfinite(self.temporal).all()):
            raise ValueError('Non-finite training features')
        if not np.isin(self.target, (0, 1)).all() or (n and not (np.isfinite(self.weights).all() and (self.weights > 0).all())):
            raise ValueError('Invalid targets or weights')
        object.__setattr__(self, 'counts', tuple(dict(c) for c in self.counts))


def select_training(groups, pitch):
    instants, temporals, targets, weights, identities, counts = [], [], [], [], [], []
    for g, group in enumerate(groups):
        frames = list(group['frames'])
        reference = np.asarray(group['reference'])
        if reference.shape != (len(frames),):
            raise ValueError('Reference/frame dimensions differ')
        x = liveness_inputs(frames, pitch)
        take = (np.arange(len(frames)) % 5 == 0) & (reference < 3) & x.eligible
        rows = np.flatnonzero(take)
        target = (reference[rows] == 2).astype(np.uint8)
        instants.append(x.instant[rows])
        temporals.append(x.temporal[rows])
        targets.append(target)
        weights.append(np.full(len(rows), 1. / max(len(rows), 1)))
        identities.append(np.column_stack((np.full(len(rows), g, dtype=np.int64), rows.astype(np.int64))))
        counts.append(dict(match=group['match'], rows=len(rows), D=int(target.sum()), live=int(len(rows) - target.sum()),
                           eligible_known=int(((reference < 3) & x.eligible).sum()), frames=len(frames)))
    return TrainingSet(np.concatenate(instants), np.concatenate(temporals), np.concatenate(targets),
                       np.concatenate(weights), np.concatenate(identities), tuple(counts))


def check_floors(training):
    counts = training.counts if isinstance(training, TrainingSet) else training
    problems = []
    for c in counts:
        if c['rows'] < MIN_ROWS:
            problems.append(f"{c['match']}: selected rows {c['rows']} < {MIN_ROWS}")
        if c['D'] < MIN_CLASS:
            problems.append(f"{c['match']}: D targets {c['D']} < {MIN_CLASS}")
        if c['live'] < MIN_CLASS:
            problems.append(f"{c['match']}: live targets {c['live']} < {MIN_CLASS}")
    return problems


# ----- portable forest ----------------------------------------------------------------------------

def export_forest(classifier, n_features):
    if list(classifier.classes_) != [0, 1] or classifier.n_features_in_ != n_features:
        raise ValueError('Binary classifier with the declared feature count required')
    trees = []
    for estimator in classifier.estimators_:
        tree = estimator.tree_
        values = tree.value[:, 0, :].astype(np.float64)
        normalizer = values[:, 0] + values[:, 1]
        normalizer[normalizer == 0] = 1.
        trees.append(dict(children_left=tree.children_left.tolist(), children_right=tree.children_right.tolist(),
                          feature=tree.feature.tolist(), threshold=tree.threshold.tolist(),
                          dead=(values[:, 1] / normalizer).tolist()))
    model = dict(feature_count=int(n_features), n_estimators=len(trees), trees=trees)
    validate_forest(model, n_features)
    return model


def _validate_tree(tree, n_features):
    names = ('children_left', 'children_right', 'feature', 'threshold', 'dead')
    if any(name not in tree for name in names):
        raise ValueError('Incomplete exported tree')
    n = len(tree['feature'])
    if not n or n > MAX_NODES or any(len(tree[name]) != n for name in names):
        raise ValueError('Invalid exported tree dimensions')
    reachable = {0}
    for i in range(n):
        left, right = tree['children_left'][i], tree['children_right'][i]
        dead, threshold = tree['dead'][i], tree['threshold'][i]
        if not isinstance(dead, float) or not isfinite(dead) or not 0 <= dead <= 1 or not isfinite(threshold):
            raise ValueError('Invalid exported node values')
        if left == right == -1:
            continue
        if (type(left) is not int or type(right) is not int or not i < left < n or not i < right < n
                or left == right or not 0 <= tree['feature'][i] < n_features):
            raise ValueError('Invalid or cyclic exported tree')
        if i in reachable:
            reachable.update((left, right))
    if len(reachable) != n:
        raise ValueError('Unreachable exported tree nodes')


def validate_forest(model, n_features):
    if model.get('feature_count') != n_features or not model.get('trees') or model.get('n_estimators') != len(model['trees']):
        raise ValueError('Invalid exported forest header')
    for tree in model['trees']:
        _validate_tree(tree, n_features)


def dead_scores(matrix, model):
    n_features = model['feature_count']
    try:
        with np.errstate(over='raise', invalid='raise'):
            x = np.array(matrix, dtype=np.float32, copy=True, order='C')
    except (TypeError, ValueError, FloatingPointError):
        raise ValueError('Invalid float32 liveness matrix') from None
    if x.ndim != 2 or x.shape[1] != n_features or not np.isfinite(x).all():
        raise ValueError('Invalid liveness matrix dimensions/values')
    validate_forest(model, n_features)
    total = np.zeros(len(x), dtype=np.float64)
    rows = np.arange(len(x))
    for tree in model['trees']:
        left, right = np.asarray(tree['children_left']), np.asarray(tree['children_right'])
        feature, threshold = np.asarray(tree['feature']), np.asarray(tree['threshold'], dtype=np.float64)
        nodes = np.zeros(len(x), dtype=np.int64)
        while True:
            active = np.flatnonzero(left[nodes] != -1)
            if not len(active):
                break
            at = nodes[active]
            nodes[active] = np.where(x[rows[active], feature[at]] <= threshold[at], left[at], right[at])
        total += np.asarray(tree['dead'], dtype=np.float64)[nodes]
    total /= len(model['trees'])
    return total


# ----- fitting -------------------------------------------------------------------------------------

def _fit_one(x, y, w, **override):
    """The fixed recipe; ``override`` exists only for synthetic tests (production callers pass none)."""
    from sklearn.ensemble import RandomForestClassifier
    classifier = RandomForestClassifier(**dict(PARAMETERS, **override))
    classifier.fit(np.asarray(x, dtype=np.float32), y, sample_weight=w)
    return classifier


def split_offsets(model):
    """Split counts by window offset (temporal) or by centre column (instant): what the forest actually used."""
    counts = {}
    for tree in model['trees']:
        for f, left in zip(tree['feature'], tree['children_left']):
            if left == -1:
                continue
            key = str(OFFSETS[f // FRAME_COLUMNS]) if model['feature_count'] == WINDOW_COLUMNS else 'centre'
            counts[key] = counts.get(key, 0) + 1
    return counts


def fit_pair(training, on_fit_entry, *, _override=None):
    """Exactly two fits, instant first.  ``on_fit_entry(mode)`` claims the budget before each fit."""
    if not isinstance(training, TrainingSet) or not callable(on_fit_entry):
        raise ValueError('TrainingSet and entry callback required')
    override = dict(_override or {})
    names = ('instant', 'temporal', 'target', 'weights', 'row_identity')
    snapshot = {name: semantic_digest(getattr(training, name)) for name in names}
    results = {}
    for mode in FIT_ORDER:
        matrix = getattr(training, mode)
        on_fit_entry(mode)
        classifier = _fit_one(matrix, training.target, training.weights, **override)
        model = export_forest(classifier, matrix.shape[1])
        parity = float(np.abs(dead_scores(matrix, model) - classifier.predict_proba(matrix)[:, 1]).max())
        if parity > PARITY_TOLERANCE:
            raise ValueError('Portable forest differs from fitted scores: ' + mode)
        results[mode] = dict(model=model, model_sha256=model_digest(model), parity_max_abs_diff=parity,
                             rows=len(matrix), class_support=dict(live=int((training.target == 0).sum()),
                                                                  D=int(training.target.sum())),
                             training_sha256=dict(matrix=snapshot[mode], target=snapshot['target'],
                                                  weights=snapshot['weights'], row_identity=snapshot['row_identity']),
                             parameters=dict(PARAMETERS, **override),
                             node_count=sum(len(t['feature']) for t in model['trees']),
                             split_counts=split_offsets(model))
    if {name: semantic_digest(getattr(training, name)) for name in names} != snapshot:
        raise ValueError('Fitting mutated the training set')
    return results
