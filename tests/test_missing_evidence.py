"""Experiment F: half-weight dead-ball evidence on missing-ball rows."""
import math
from math import log
import unittest

import numpy as np

from gap_solver.soft_sequence import soft_emissions
from recent_geometry_assembly import SupportSet, assemble_research
from test_gap_liveness import fixture

try:
    import missing_evidence as m
except ImportError:
    m = None


def supports(n, row):
    return np.tile(np.asarray(row, dtype=float), (n, 1))


def varied(n, seed):
    rng = np.random.default_rng(seed)
    x = rng.random((n, 3)) + .05
    return x / x.sum(axis=1, keepdims=True)


class MissingRow(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(m, 'missing_evidence is missing')

    def test_missing_row_d_only(self):
        r = m.missing_row((0.07, 0.07, 0.86), 0.5)
        self.assertEqual((r[0], r[1]), (0.0, 0.0))
        self.assertLess(abs(r[2] - 0.5 * (log(0.86) - log(0.07))), 1e-12)

    def test_missing_row_never_negative(self):
        self.assertEqual(m.missing_row((0.49, 0.49, 0.02), 0.5), (0.0, 0.0, 0.0))

    def test_missing_row_lambda_zero_is_neutral(self):
        self.assertEqual(m.missing_row((0.2, 0.3, 0.5), 0.0), (0.0, 0.0, 0.0))

    def test_missing_row_floors_keep_finite(self):
        self.assertTrue(all(map(math.isfinite, m.missing_row((0.0, 0.0, 1.0), 0.5))))
        self.assertTrue(all(map(math.isfinite, m.missing_row((0.5, 0.5, 0.0), 0.5))))

    def test_rejects_bad_lambda(self):
        for lam in (-0.1, float('nan'), float('inf')):
            with self.assertRaises(ValueError):
                m.missing_row((0.2, 0.3, 0.5), lam)

    def test_lambda_constant(self):
        self.assertEqual(m.LAMBDA, 0.5)


class Assembly(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(m, 'missing_evidence is missing')

    def sets(self, n, control, still):
        return SupportSet('control', control), SupportSet('candidate', still)

    def test_visible_rows_unchanged(self):
        n = 50
        control, still = varied(n, 1), varied(n, 2)
        observed = [i % 3 != 0 for i in range(n)]
        rows = m.emission_rows(control.tolist(), still.tolist(), observed, 0.5)
        expected = soft_emissions(control.tolist(), [0.] * n, 0.)
        for i in range(n):
            if observed[i]:
                self.assertEqual(rows[i], expected[i])
            else:
                self.assertEqual(rows[i], m.missing_row(tuple(still[i]), 0.5))

    def test_unusable_missing_rows_stay_unlabelled(self):
        frames = fixture(n=400, gaps=((0, 120),), gap_speed=4., periods=[0] * 100 + [1] * 300)
        c, s = self.sets(400, varied(400, 3), supports(400, (0.07, 0.07, 0.86)))
        out = m.assemble_missing(frames, c, s, lam=0.5)
        ref = assemble_research(frames, c)
        self.assertEqual(out.latent[:100], ('X',) * 100)
        self.assertEqual(out.final[:100], ref.final[:100])

    def test_unseen_segment_still_unusable(self):
        frames = fixture(n=400, gaps=((200, 400),), gap_speed=4., periods=[1] * 200 + [2] * 200)
        c, s = self.sets(400, supports(400, (0.8, 0.1, 0.1)), supports(400, (0.07, 0.07, 0.86)))
        out = m.assemble_missing(frames, c, s, lam=0.5)
        self.assertEqual(out.latent[200:], ('X',) * 200)
        self.assertEqual(out, assemble_research(frames, c))

    def test_lambda_zero_equals_research_replica(self):
        for seed in range(6):
            frames = fixture(n=900)  # slow 200-row gap: the gap rule and the restart mask both run
            c, s = self.sets(900, varied(900, seed), varied(900, seed + 50))
            ref = assemble_research(frames, c)
            self.assertTrue(ref.stoppage_gaps)
            self.assertEqual(m.assemble_missing(frames, c, s, lam=0.), ref)

    def test_strong_still_evidence_creates_d(self):
        frames = fixture(n=600, gaps=((240, 360),), gap_speed=4.)  # fast players: the gap rule leaves it live
        c, s = self.sets(600, supports(600, (0.8, 0.1, 0.1)), supports(600, (0.07, 0.07, 0.86)))
        on = m.assemble_missing(frames, c, s, lam=0.5)
        off = m.assemble_missing(frames, c, s, lam=0.)
        self.assertFalse(on.stoppage_gaps)
        self.assertIn('D', on.final[240:360])
        self.assertNotIn('D', off.final)
        self.assertNotIn('D', on.final[:240] + on.final[360:])


if __name__ == '__main__':
    unittest.main()
