"""Matched control/candidate fitting for Experiment A, plus the 20-column research exporter/evaluator.

The control is the historical ``memory_ablation_training.prepare_training`` output, unmodified.  The
candidate has the same rows, labels, weights and row identities with two appended feature columns.
Exactly two fits are made: control (must reproduce the frozen model digest) and then candidate.
"""
from dataclasses import dataclass
import hashlib
import json
import struct
from math import isfinite

import numpy as np

from gap_solver.selection import ball_mask, export_tree, mask_frames
from memory_ablation import MODEL_SHA, predict_supports
from memory_ablation_training import TRAIN_MATCHES, TrainingData, model_digest, prepare_training, semantic_digest
from recent_geometry_features import RESEARCH_FEATURE_NAMES, research_matrix

EXPECTED_ROWS = 228776
CONTROL_TRAINING_SEMANTIC_SHA = '2730cd91f67ceef88548a0fe65bf3bd899a5bc0526b6a92f937d08b2e37c55fd'
APPENDED = (18, 19)
PARAMETERS = dict(max_depth=4, min_samples_leaf=125, random_state=1729)
PARITY_TOLERANCE = 1e-12


def array_identity(arrays):
    value = {key: semantic_digest(array) for key, array in sorted(arrays.items())}
    return hashlib.sha256((json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()).hexdigest()


def _matrix20(matrix):
    try:
        with np.errstate(over='raise', invalid='raise'):
            values = np.array(matrix, dtype=np.float32, copy=True, order='C')
    except (TypeError, ValueError, FloatingPointError):
        raise ValueError('Invalid float32 research feature matrix') from None
    if values.ndim != 2 or values.shape[1] != 20 or not np.isfinite(values).all():
        raise ValueError('Invalid research feature dimensions/values')
    return values


@dataclass(frozen=True)
class ResearchTrainingData:
    matrix: object
    target: object
    weights: object
    row_identity: object
    group_counts: tuple

    def __post_init__(self):
        matrix = _matrix20(self.matrix)
        target = np.array(self.target, copy=True)
        weights = np.array(self.weights, dtype=np.float64, copy=True)
        identity = np.array(self.row_identity, copy=True)
        n = len(matrix)
        if not n or target.shape != (n,) or target.dtype.kind not in 'ui' or not np.isin(target, [0, 1, 2]).all():
            raise ValueError('Invalid fitting targets')
        if weights.shape != (n,) or not np.isfinite(weights).all() or np.any(weights <= 0):
            raise ValueError('Invalid fitting weights')
        if identity.shape != (n, 3) or identity.dtype.kind not in 'ui':
            raise ValueError('Invalid private row identities')
        for name, value in (('matrix', matrix), ('target', target.astype(np.uint8)),
                            ('weights', weights), ('row_identity', identity.astype(np.int64))):
            value.setflags(write=False)
            object.__setattr__(self, name, value)
        object.__setattr__(self, 'group_counts', tuple(dict(v) for v in self.group_counts))


@dataclass(frozen=True)
class Pair:
    control: object
    candidate: object
    prefix_semantic_sha256: str


def _candidate_training(groups):
    matrices, targets, weights, identities, counts = [], [], [], [], []
    for group_index, group in enumerate(groups):
        frames = list(group['frames'])
        target = np.asarray(group['reference'])
        take = (np.arange(len(frames)) % 5 == 0) & (target < 3)
        selected = np.flatnonzero(take)
        periods = np.asarray(group['periods'])
        for regime, rate in enumerate((0., .3)):
            inputs = frames if rate == 0 else mask_frames(frames, ball_mask(periods, rate, 1729 + group_index))
            matrix = research_matrix(inputs)       # full history before selecting any row
            matrices.append(matrix[take])
            targets.append(target[take])
            weights.append(np.full(len(selected), 1. / len(selected), dtype=np.float64))
            identities.append(np.column_stack((np.full(len(selected), group_index),
                                               np.full(len(selected), regime), selected)))
            counts.append(dict(match=group['match'], regime='natural' if regime == 0 else 'mask30', rows=len(selected)))
    return ResearchTrainingData(np.concatenate(matrices), np.concatenate(targets), np.concatenate(weights),
                                np.concatenate(identities), tuple(counts))


def prepare_pair(groups):
    """Historical control (18 columns) and 20-column candidate over identical rows."""
    groups = list(groups)
    control = prepare_training(groups)                 # enforces order, codes, geometry-only frames
    candidate = _candidate_training(groups)
    _check_shared(control, candidate)
    return Pair(control, candidate, semantic_digest(control.matrix))


def _check_shared(control, candidate):
    for name in ('target', 'weights', 'row_identity'):
        if semantic_digest(getattr(control, name)) != semantic_digest(getattr(candidate, name)):
            raise ValueError('Candidate row/label/weight identities differ from control: ' + name)
    if candidate.matrix.shape[1] != 20 or control.matrix.shape[1] != 18:
        raise ValueError('Unexpected column counts')
    if semantic_digest(candidate.matrix[:, :18]) != semantic_digest(control.matrix):
        raise ValueError('Feature-prefix digest differs between candidate and control matrices')
    if tuple(control.group_counts) != tuple(candidate.group_counts):
        raise ValueError('Group counts differ')


def require_rows(pair, expected=EXPECTED_ROWS):
    if len(pair.control.matrix) != expected or len(pair.candidate.matrix) != expected:
        raise ValueError('Selected row count differs from the expected fitting size')


class ControlMismatch(ValueError):
    def __init__(self, model, receipt):
        super().__init__('Historical control reconstruction failed; candidate not fitted')
        self.model = model
        self.receipt = receipt


class UnusedRepresentation(ValueError):
    def __init__(self, model, receipt, results):
        super().__init__('representation unused, no advancement')
        self.model = model
        self.receipt = receipt
        self.results = results


# ----- 20-column portable tree ------------------------------------------------------------------

def export_research_tree(classifier):
    if list(classifier.classes_) != [0, 1, 2] or classifier.n_features_in_ != len(RESEARCH_FEATURE_NAMES):
        raise ValueError('research classifier needs the 20-column schema and H/A/D targets')
    tree = classifier.tree_
    values = tree.value[:, 0, :].astype(float)
    values /= values.sum(axis=1, keepdims=True)
    return dict(feature_names=list(RESEARCH_FEATURE_NAMES), children_left=tree.children_left.tolist(),
                children_right=tree.children_right.tolist(), feature=tree.feature.tolist(),
                threshold=tree.threshold.tolist(), probabilities=values.tolist())


class ResearchTree:
    """Same validation and float32 comparison as ``gap_solver.tactical.PortableTree``, 20 features."""

    def __init__(self, model):
        if tuple(model.get('feature_names', ())) != RESEARCH_FEATURE_NAMES:
            raise ValueError('exported tree feature schema differs from the research features')
        names = ('children_left', 'children_right', 'feature', 'threshold', 'probabilities')
        if any(name not in model for name in names):
            raise ValueError('incomplete exported tree')
        n = len(model['feature'])
        if not n or n > 4095 or any(len(model[name]) != n for name in names):
            raise ValueError('invalid exported tree dimensions')
        reachable = {0}
        for i in range(n):
            left, right = model['children_left'][i], model['children_right'][i]
            probabilities = model['probabilities'][i]
            if (len(probabilities) != 3 or any(not isfinite(p) or not 0 <= p <= 1 for p in probabilities)
                    or abs(sum(probabilities) - 1) > 1e-6 or not isfinite(model['threshold'][i])):
                raise ValueError('invalid exported leaf support')
            if left == right == -1:
                continue
            if (type(left) is not int or type(right) is not int or not i < left < n or not i < right < n
                    or left == right or not 0 <= model['feature'][i] < len(RESEARCH_FEATURE_NAMES)):
                raise ValueError('invalid/cyclic exported tree')
            if i in reachable:
                reachable.update((left, right))
        if len(reachable) != n:
            raise ValueError('unreachable exported tree nodes')
        self.model = model

    def predict(self, row):
        if len(row) != len(RESEARCH_FEATURE_NAMES) or any(not isfinite(x) for x in row):
            raise ValueError('invalid research feature row')
        node = 0
        while self.model['children_left'][node] != -1:
            key = self.model['feature'][node]
            value = struct.unpack('<f', struct.pack('<f', row[key]))[0]
            node = (self.model['children_left'][node] if value <= self.model['threshold'][node]
                    else self.model['children_right'][node])
        return self.model['probabilities'][node]


def predict_supports_research(matrix, model):
    x = _matrix20(matrix)
    ResearchTree(model)
    nodes = np.zeros(len(x), dtype=np.int32)
    left, right = np.asarray(model['children_left']), np.asarray(model['children_right'])
    feature = np.asarray(model['feature'])
    threshold = np.asarray(model['threshold'], dtype=np.float64)
    while True:
        active = np.flatnonzero(left[nodes] != -1)
        if not len(active):
            break
        at = nodes[active]
        nodes[active] = np.where(x[active, feature[at]] <= threshold[at], left[at], right[at])
    return np.asarray(model['probabilities'], dtype=np.float64)[nodes]


# ----- fitting -----------------------------------------------------------------------------------

def _used_splits(model):
    return [dict(node=i, feature=f, name=RESEARCH_FEATURE_NAMES[f] if f < 20 else None, threshold=t)
            for i, (f, t, l) in enumerate(zip(model['feature'], model['threshold'], model['children_left'])) if l != -1]


def _receipt(mode, classifier, model, data, matrix, parity, original):
    splits = _used_splits(model)
    used = sorted({s['feature'] for s in splits})
    return dict(mode=mode, model_sha256=model_digest(model), portable_all_rows_match=True, parity_max_abs_diff=parity,
                rows=len(matrix), class_support={name: int((data.target == k).sum()) for k, name in enumerate('HAD')},
                training_sha256={**original, 'fitted_matrix': semantic_digest(matrix)}, parameters=dict(PARAMETERS),
                node_count=int(classifier.tree_.node_count), depth=int(classifier.get_depth()),
                split_features=used, appended_columns_used=[f for f in used if f in APPENDED],
                appended_splits=[s for s in splits if s['feature'] in APPENDED])


def fit_research(control, candidate, on_fit_entry, expected_control_sha=MODEL_SHA):
    """Exactly two fits, control first.  ``on_fit_entry(mode)`` claims the budget before each fit."""
    from sklearn.tree import DecisionTreeClassifier
    if not isinstance(control, TrainingData) or not isinstance(candidate, ResearchTrainingData) or not callable(on_fit_entry):
        raise ValueError('Training contracts and entry callback required')
    _check_shared(control, candidate)                      # before any fit is claimed
    snapshot = {name: (semantic_digest(getattr(control, name)), semantic_digest(getattr(candidate, name)))
                for name in ('matrix', 'target', 'weights', 'row_identity')}
    results = {}
    for mode, data in (('control', control), ('candidate', candidate)):
        matrix = np.array(data.matrix, dtype=np.float32, copy=True, order='C')
        original = {name: semantic_digest(getattr(data, name)) for name in ('matrix', 'target', 'weights', 'row_identity')}
        classifier = DecisionTreeClassifier(**PARAMETERS)
        on_fit_entry(mode)
        classifier.fit(matrix, data.target, sample_weight=data.weights)
        if mode == 'control':
            model = export_tree(classifier)
            portable = predict_supports(matrix, model)
        else:
            model = export_research_tree(classifier)
            portable = predict_supports_research(matrix, model)
        expected = classifier.predict_proba(matrix)
        parity = float(np.abs(portable - expected).max())
        if parity > PARITY_TOLERANCE:
            raise ValueError('Portable model differs from fitted supports')
        receipt = _receipt(mode, classifier, model, data, matrix, parity, original)
        if mode == 'control' and expected_control_sha is not None and receipt['model_sha256'] != expected_control_sha:
            raise ControlMismatch(model, receipt)
        results[mode] = dict(model=model, **receipt)
        if mode == 'candidate' and not receipt['appended_columns_used']:
            raise UnusedRepresentation(model, receipt, results)
    after = {name: (semantic_digest(getattr(control, name)), semantic_digest(getattr(candidate, name)))
             for name in ('matrix', 'target', 'weights', 'row_identity')}
    if snapshot != after:
        raise ValueError('Fitting mutated source data')
    return results
