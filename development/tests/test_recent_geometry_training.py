"""Matched control/candidate preparation, fitting contract and 20-column exporter on synthetic data.

sklearn-dependent tests only run under the pinned training interpreter; others run everywhere.
"""
import importlib.util
import struct
import unittest

import numpy as np

from gap_solver.core import Frame
from gap_solver.motion import motion_frame

try:
    import recent_geometry_training as rt
    import memory_ablation_training as old
except ImportError:  # pragma: no cover - red phase
    rt = None

SKLEARN = importlib.util.find_spec('sklearn') is not None
NAMES = ('J03WOH', 'J03WOY', 'J03WPY', 'J03WMX')


def groups(n=11, motion=True, reference=None):
    home = [(10., 10.), (11., 10.), (12., 10.)]
    away = [(70., 40.), (71., 40.), (72., 40.)]
    frames = [motion_frame(1, (10. + i * .001, 10.), home, away) for i in range(n)]
    ref = np.asarray([0, 0, 0, 2, 0, 3, 0, 0, 0, 0, 1][:n] if reference is None else reference, dtype=np.uint8)
    return [dict(match=m, frames=list(frames), reference=ref.copy(), periods=np.ones(n, dtype=np.uint8)) for m in NAMES]


def plain_groups(n=11):
    frames = [Frame(period=1, ball_x=52.65, ball_y=34., home_distance=1., away_distance=1. + (i % 4)) for i in range(n)]
    ref = np.resize(np.asarray([0, 0, 0, 2, 0, 3, 0, 0, 0, 0, 1], dtype=np.uint8), n)
    return [dict(match=m, frames=list(frames), reference=ref.copy(), periods=np.ones(n, dtype=np.uint8)) for m in NAMES]


class Preparation(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(rt, 'recent_geometry_training is missing')

    def test_control_is_the_historical_prepare_training_output_exactly(self):
        g = plain_groups()
        pair = rt.prepare_pair(g)
        hist = old.prepare_training(g)
        for name in ('matrix', 'target', 'weights', 'row_identity'):
            self.assertEqual(old.semantic_digest(getattr(pair.control, name)), old.semantic_digest(getattr(hist, name)), name)
        self.assertEqual(pair.control.group_counts, hist.group_counts)

    def test_candidate_shares_rows_labels_weights_identities_and_prefix(self):
        pair = rt.prepare_pair(plain_groups())
        c, k = pair.control, pair.candidate
        self.assertEqual(k.matrix.shape, (len(c.matrix), 20))
        self.assertEqual(k.matrix.dtype, np.float32)
        for name in ('target', 'weights', 'row_identity'):
            np.testing.assert_array_equal(getattr(c, name), getattr(k, name))
        self.assertEqual(old.semantic_digest(k.matrix[:, :18]), old.semantic_digest(c.matrix))
        self.assertEqual(pair.prefix_semantic_sha256, old.semantic_digest(c.matrix))

    def test_exact_row_selection_and_weights_and_full_history_before_take(self):
        pair = rt.prepare_pair(plain_groups())
        k = pair.candidate
        expected = np.asarray([[g, regime, i] for g in range(4) for regime in range(2) for i in (0, 10)])
        np.testing.assert_array_equal(k.row_identity, expected)
        np.testing.assert_array_equal(k.target, [0, 1] * 8)
        np.testing.assert_array_equal(k.weights, [.5] * 16)
        # row 10 sees all eleven rows of history for the new window, not only the sampled rows
        natural_last = k.matrix[1]
        margins = [(1. + (i % 4)) - 1. for i in range(11)]
        window = margins[-11:]     # 11 qualifying rows, all inside the 12-row window
        self.assertAlmostEqual(float(natural_last[18]), sum(window) / len(window), places=5)
        self.assertEqual(float(natural_last[19]), np.float32(11 / 12))
        with self.assertRaises(ValueError):
            k.matrix[0, 0] = 9.

    def test_masked_regime_has_unsupported_slots(self):
        pair = rt.prepare_pair(plain_groups(60))
        k = pair.candidate
        regime, index = k.row_identity[:, 1], k.row_identity[:, 2]
        full = (regime == 0) & (index >= 11)
        self.assertTrue(full.any())
        np.testing.assert_array_equal(k.matrix[full, 19], np.ones(int(full.sum()), dtype=np.float32))
        self.assertTrue((k.matrix[regime == 1, 19] < 1.).any())

    def test_reference_only_selects_rows_never_changes_features(self):
        g = plain_groups()
        before = rt.prepare_pair(g).candidate
        g[0]['reference'][5] = 2
        after = rt.prepare_pair(g).candidate
        np.testing.assert_array_equal(after.row_identity[:3], [[0, 0, 0], [0, 0, 5], [0, 0, 10]])
        np.testing.assert_array_equal(before.matrix[:2], after.matrix[[0, 2]])

    def test_literal_order_is_required(self):
        with self.assertRaises(ValueError):
            rt.prepare_pair(list(reversed(plain_groups())))

    def test_nonfinite_features_stop(self):
        g = plain_groups()
        data = rt.prepare_pair(g).candidate
        bad = data.matrix.copy()
        bad[0, 19] = np.nan
        with self.assertRaises(ValueError):
            rt.ResearchTrainingData(bad, data.target, data.weights, data.row_identity, data.group_counts)

    def test_expected_row_guard(self):
        pair = rt.prepare_pair(plain_groups())
        self.assertEqual(rt.EXPECTED_ROWS, 228776)
        with self.assertRaises(ValueError):
            rt.require_rows(pair, 228776)
        rt.require_rows(pair, len(pair.control.matrix))

    def test_array_identity_matches_the_protocol_definition(self):
        import hashlib, json
        arrays = {'a': np.arange(4, dtype=np.int64), 'b': np.ones((2, 2), dtype=np.float32)}
        want = hashlib.sha256((json.dumps({k: old.semantic_digest(v) for k, v in sorted(arrays.items())},
                                          sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()).hexdigest()
        self.assertEqual(rt.array_identity(arrays), want)


def random_problem(n=3000, seed=3, signal_new=True):
    rng = np.random.RandomState(seed)
    x = np.zeros((n, 20), dtype=np.float32)
    x[:, :18] = rng.rand(n, 18)
    x[:, 18] = rng.randn(n) * 3
    x[:, 19] = rng.randint(0, 13, n) / 12
    if signal_new:
        y = (x[:, 18] > 0.5).astype(np.uint8)
        y[x[:, 19] < .3] = 2
    else:
        x[:, 18:] = 0
        y = (x[:, 3] > .5).astype(np.uint8)
        y[x[:, 4] > .8] = 2
    return x, y


@unittest.skipUnless(SKLEARN, 'training-only: needs the pinned scikit-learn interpreter')
class Fitting(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(rt, 'recent_geometry_training is missing')

    def data(self, signal_new=True):
        x, y = random_problem(signal_new=signal_new)
        n = len(x)
        identity = np.column_stack((np.zeros(n), np.zeros(n), np.arange(n))).astype(np.int64)
        weights = np.full(n, 1. / n)
        candidate = rt.ResearchTrainingData(x, y, weights, identity, ({'match': 'x', 'regime': 'natural', 'rows': n},))
        control = old.TrainingData(x[:, :18], y, weights, identity, ({'match': 'x', 'regime': 'natural', 'rows': n},))
        return control, candidate

    def test_exporter_parity_and_float32_comparisons(self):
        from sklearn.tree import DecisionTreeClassifier
        x, y = random_problem()
        clf = DecisionTreeClassifier(max_depth=4, min_samples_leaf=125, random_state=1729).fit(x, y)
        model = rt.export_research_tree(clf)
        self.assertEqual(len(model['feature_names']), 20)
        vector = rt.predict_supports_research(x, model)
        self.assertLessEqual(float(np.abs(vector - clf.predict_proba(x)).max()), 1e-12)
        tree = rt.ResearchTree(model)
        scalar = np.asarray([tree.predict(tuple(float(v) for v in row)) for row in x[:300]])
        np.testing.assert_array_equal(scalar, vector[:300])

    def test_threshold_ties_use_less_or_equal_in_float32(self):
        model = dict(feature_names=list(rt.RESEARCH_FEATURE_NAMES), children_left=[1, -1, -1], children_right=[2, -1, -1],
                     feature=[19, -2, -2], threshold=[float(np.float32(.25)), -2., -2.],
                     probabilities=[[1/3, 1/3, 1/3], [1., 0., 0.], [0., 1., 0.]])
        x = np.zeros((3, 20), dtype=np.float32)
        x[:, 19] = [.25, np.nextafter(np.float32(.25), np.float32(1)), 0.]
        out = rt.predict_supports_research(x, model)
        np.testing.assert_array_equal(out.argmax(axis=1), [0, 1, 0])

    def test_fit_pair_order_budget_callback_and_hashes(self):
        control, candidate = self.data()
        claims = []
        out = rt.fit_research(control, candidate, claims.append, expected_control_sha=None)
        self.assertEqual(claims, ['control', 'candidate'])
        self.assertEqual(set(out), {'control', 'candidate'})
        for mode in out:
            self.assertTrue(out[mode]['portable_all_rows_match'])
            self.assertLessEqual(out[mode]['parity_max_abs_diff'], 1e-12)
        self.assertEqual(out['candidate']['parameters'], dict(max_depth=4, min_samples_leaf=125, random_state=1729))
        self.assertTrue(set(out['candidate']['split_features']) & {18, 19})
        self.assertTrue(out['candidate']['appended_columns_used'])
        self.assertLessEqual(out['candidate']['depth'], 4)

    def test_control_mismatch_stops_before_the_candidate_fit(self):
        control, candidate = self.data()
        claims = []
        with self.assertRaises(rt.ControlMismatch) as caught:
            rt.fit_research(control, candidate, claims.append, expected_control_sha='0' * 64)
        self.assertEqual(claims, ['control'])
        self.assertIn('model_sha256', caught.exception.receipt)

    def test_unused_appended_columns_stop(self):
        control, candidate = self.data(signal_new=False)
        with self.assertRaises(rt.UnusedRepresentation) as caught:
            rt.fit_research(control, candidate, lambda mode: None, expected_control_sha=None)
        self.assertEqual(caught.exception.receipt['appended_columns_used'], [])

    def test_prefix_mismatch_between_control_and_candidate_stops_before_any_fit(self):
        control, candidate = self.data()
        shifted = candidate.matrix.copy()
        shifted[0, 3] += 1.
        broken = rt.ResearchTrainingData(shifted, candidate.target, candidate.weights, candidate.row_identity, candidate.group_counts)
        claims = []
        with self.assertRaises(ValueError):
            rt.fit_research(control, broken, claims.append, expected_control_sha=None)
        self.assertEqual(claims, [])

    def test_row_identity_mismatch_stops(self):
        control, candidate = self.data()
        ident = candidate.row_identity.copy(); ident[0, 2] = 99
        broken = rt.ResearchTrainingData(candidate.matrix, candidate.target, candidate.weights, ident, candidate.group_counts)
        with self.assertRaises(ValueError):
            rt.fit_research(control, broken, lambda m: None, expected_control_sha=None)

    def test_sources_are_not_mutated(self):
        control, candidate = self.data()
        before = (old.semantic_digest(control.matrix), old.semantic_digest(candidate.matrix))
        rt.fit_research(control, candidate, lambda m: None, expected_control_sha=None)
        self.assertEqual(before, (old.semantic_digest(control.matrix), old.semantic_digest(candidate.matrix)))


class Portable(unittest.TestCase):
    def test_schema_validation_rejects_wrong_feature_names_and_cycles(self):
        good = dict(feature_names=list(rt.RESEARCH_FEATURE_NAMES), children_left=[1, -1, -1], children_right=[2, -1, -1],
                    feature=[19, -2, -2], threshold=[.5, -2., -2.], probabilities=[[1/3, 1/3, 1/3], [1., 0., 0.], [0., 1., 0.]])
        rt.ResearchTree(good)
        for key, value in (('feature_names', list(rt.RESEARCH_FEATURE_NAMES[:18])), ('children_left', [2, -1, -1]),
                           ('feature', [20, -2, -2])):
            bad = dict(good); bad[key] = value
            with self.assertRaises(ValueError):
                rt.ResearchTree(bad)


if __name__ == '__main__':
    unittest.main()
