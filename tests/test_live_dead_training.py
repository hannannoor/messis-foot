"""Live/dead sequence experiment: training rows, forests and the portable exporter.  Synthetic only.

Run under the pinned training interpreter (scikit-learn 1.5.1).
"""
import unittest

import numpy as np

import live_dead_training as lt
from memory_ablation_training import semantic_digest
from tests.test_live_dead_features import frame, PITCH


def group(match, count=400, dead_every=3):
    frames = [frame(i, speeds=[(.2 if (i // 50) % 2 else 2.5) + .05 * j for j in range(22)]) for i in range(count)]
    ref = np.asarray([2 if (i // 50) % dead_every == 0 else (i // 50) % 2 for i in range(count)], dtype=np.uint8)
    ref[7] = 3                                                     # reference X never a target
    return dict(match=match, frames=frames, reference=ref)


class SelectionTest(unittest.TestCase):
    def setUp(self):
        self.groups = [group('A'), group('B', count=300)]
        self.ts = lt.select_training(self.groups, PITCH)

    def test_selection_every_fifth_known_eligible(self):
        from live_dead_features import liveness_inputs
        for g, data in enumerate(self.groups):
            rows = self.ts.row_identity[self.ts.row_identity[:, 0] == g, 1]
            eligible = liveness_inputs(data['frames'], PITCH).eligible
            self.assertTrue(len(rows) > 0)
            self.assertTrue(np.all(rows % 5 == 0))
            self.assertTrue(np.all(data['reference'][rows] < 3))
            self.assertTrue(np.all(eligible[rows]))
            expected = np.flatnonzero((np.arange(len(eligible)) % 5 == 0) & (data['reference'] < 3) & eligible)
            np.testing.assert_array_equal(rows, expected)
            np.testing.assert_array_equal(self.ts.target[self.ts.row_identity[:, 0] == g],
                                          (data['reference'][rows] == 2).astype(np.uint8))

    def test_matrices_are_the_shared_rows(self):
        self.assertEqual(self.ts.instant.shape, (len(self.ts.target), 10))
        self.assertEqual(self.ts.temporal.shape, (len(self.ts.target), 210))
        np.testing.assert_array_equal(self.ts.instant, self.ts.temporal[:, 100:110])

    def test_unit_weight_per_match(self):
        for g in range(2):
            self.assertAlmostEqual(float(self.ts.weights[self.ts.row_identity[:, 0] == g].sum()), 1., delta=1e-12)

    def test_floors_report_shortfalls(self):
        problems = lt.check_floors(self.ts)
        self.assertTrue(any('A' in p and 'rows' in p for p in problems))       # 400-row fixture: < 1,000 selected
        counts = (dict(match='M', rows=1000, D=124, live=876),)
        self.assertEqual(lt.check_floors(counts), ['M: D targets 124 < 125'])
        self.assertEqual(lt.check_floors((dict(match='M', rows=1000, D=125, live=875),)), [])

    def test_read_only(self):
        with self.assertRaises(ValueError):
            self.ts.temporal[0, 0] = 1.


class FitTest(unittest.TestCase):
    def test_parameters_exact(self):
        self.assertEqual(lt.PARAMETERS, dict(n_estimators=32, max_depth=6, min_samples_leaf=125, max_features=1.0,
                                             bootstrap=True, criterion='gini', class_weight=None, random_state=1729,
                                             n_jobs=1))

    def test_fit_order_count_and_shared_rows(self):
        ts = lt.select_training([group('A', 900), group('B', 900)], PITCH)
        seen = []
        before = {k: semantic_digest(getattr(ts, k)) for k in ('instant', 'temporal', 'target', 'weights', 'row_identity')}
        results = lt.fit_pair(ts, seen.append, _override=dict(min_samples_leaf=5))
        self.assertEqual(seen, ['instant', 'temporal'])
        self.assertEqual(set(results), {'instant', 'temporal'})
        for mode in results:
            self.assertEqual(results[mode]['training_sha256'], dict(target=before['target'], weights=before['weights'],
                                                                     row_identity=before['row_identity'],
                                                                     matrix=before[mode]))
            self.assertLessEqual(results[mode]['parity_max_abs_diff'], 1e-12)
        self.assertEqual({k: semantic_digest(getattr(ts, k)) for k in before}, before)

    def test_override_refused_without_test_flag(self):
        with self.assertRaises(TypeError):
            lt.fit_pair(None, print, min_samples_leaf=5)


class ExporterTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rng = np.random.default_rng(3)
        cls.x = rng.normal(size=(600, 7)).astype(np.float32)
        cls.y = ((cls.x[:, 0] + .5 * cls.x[:, 3] + rng.normal(scale=.5, size=600)) > 0).astype(np.uint8)
        cls.w = np.full(600, 1 / 600)
        cls.clf = lt._fit_one(cls.x, cls.y, cls.w, min_samples_leaf=3)
        cls.model = lt.export_forest(cls.clf, 7)

    def test_exporter_parity_fitting_rows(self):
        diff = np.abs(lt.dead_scores(self.x, self.model) - self.clf.predict_proba(self.x)[:, 1])
        self.assertLessEqual(float(diff.max()), 1e-12)

    def test_exporter_parity_threshold_edges(self):
        rows = []
        for tree in self.clf.estimators_[:8]:
            f, t = int(tree.tree_.feature[0]), float(tree.tree_.threshold[0])
            for value in (np.float32(t), np.nextafter(np.float32(t), np.float32(np.inf)),
                          np.nextafter(np.float32(t), np.float32(-np.inf))):
                row = self.x[0].copy()
                row[f] = value
                rows.append(row)
        edge = np.asarray(rows, dtype=np.float32)
        diff = np.abs(lt.dead_scores(edge, self.model) - self.clf.predict_proba(edge)[:, 1])
        self.assertLessEqual(float(diff.max()), 1e-12)

    def test_validate_rejects_cycle_and_bad_dead(self):
        import copy
        lt.validate_forest(self.model, 7)
        bad = copy.deepcopy(self.model)
        bad['trees'][0]['children_left'][0] = 0
        with self.assertRaises(ValueError):
            lt.validate_forest(bad, 7)
        bad = copy.deepcopy(self.model)
        leaf = bad['trees'][0]['children_left'].index(-1)
        bad['trees'][0]['dead'][leaf] = 1.5
        with self.assertRaises(ValueError):
            lt.validate_forest(bad, 7)
        with self.assertRaises(ValueError):
            lt.validate_forest(self.model, 210)

    def test_dead_scores_rejects_bad_matrix(self):
        with self.assertRaises(ValueError):
            lt.dead_scores(np.full((2, 7), np.nan, dtype=np.float32), self.model)
        with self.assertRaises(ValueError):
            lt.dead_scores(np.zeros((2, 6), dtype=np.float32), self.model)


if __name__ == '__main__':
    unittest.main()
