"""Experiment G: transition-count cost rule and the pair-cost assembly."""
from math import log
import unittest

import numpy as np

from recent_geometry_assembly import SupportSet, assemble_research
from test_gap_liveness import fixture

try:
    import pair_costs as m
    from pair_decoder import uniform_matrix
except ImportError:
    m = None


def group(reference, periods):
    return dict(reference=np.asarray(reference), periods=np.asarray(periods))


def all_pairs():
    ref = [0, 0, 1, 1, 0, 2, 2, 0, 0, 1, 2, 1, 1, 2, 2, 2, 0]
    return [group(ref, [1] * len(ref))]


PRIOR_COUNTS = [[167241 - 903, 688, 215], [689, 147819 - 887, 198], [210, 197, 256860 - 407]]


class Rule(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(m, 'pair_costs is missing')

    def test_counts_within_period_only(self):
        n = m.transition_counts([group([0, 0, 1, 1], [1, 1, 2, 2])])
        self.assertEqual((n[0][0], n[1][1], n[0][1]), (1, 1, 0))

    def test_invalid_codes_break_pairs(self):
        n = m.transition_counts([group([0, 3, 1, 0, 1], [1, 1, 1, 0, 1])])
        self.assertEqual(sum(map(sum, n)), 0)

    def test_rule_mean_is_32(self):
        rule = m.pair_cost_rule(all_pairs())
        C = rule['matrix']
        off = [C[i][j] for i in range(3) for j in range(3) if i != j]
        self.assertLess(abs(sum(off) / 6 - 32.), 1e-12)
        self.assertEqual([C[i][i] for i in range(3)], [0., 0., 0.])
        self.assertEqual(rule['mean'], 32.)

    def test_rule_proportional_to_q(self):
        rule = m.pair_cost_rule(all_pairs())
        C, q = rule['matrix'], rule['q']
        self.assertAlmostEqual(C[0][1] / C[2][0], q[0][1] / q[2][0], places=12)
        self.assertAlmostEqual(C[1][2] / C[0][2], q[1][2] / q[0][2], places=12)

    def test_zero_count_pair_gets_max_q(self):
        # A -> H never observed directly (the only A -> H crosses a period boundary)
        ref = [0, 0, 1, 1, 2, 2, 0, 0, 2, 2, 1, 1, 0, 0]
        per = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2]
        rule = m.pair_cost_rule([group(ref, per)])
        self.assertEqual(rule['counts'][1][0], 0)
        observed = [rule['q'][i][j] for i in range(3) for j in range(3) if i != j and rule['counts'][i][j]]
        self.assertEqual(rule['q'][1][0], max(observed))
        self.assertTrue(all(np.isfinite(v) for r in rule['matrix'] for v in r))

    def test_no_transitions_raises(self):
        with self.assertRaises(ValueError):
            m.pair_cost_rule([group([0] * 10, [1] * 10)])

    def test_audit_counts_reproduce_prior(self):
        rule = m.costs_from_counts(PRIOR_COUNTS)
        C = rule['matrix']
        expected = {(0, 1): 27.5, (0, 2): 33.3, (1, 0): 26.8, (1, 2): 33.1, (2, 0): 35.5, (2, 1): 35.9}
        for (i, j), value in expected.items():
            self.assertLess(abs(C[i][j] - value), .05, (i, j, C[i][j]))
        self.assertAlmostEqual(rule['q'][0][1], -log(688 / 167241), places=12)


class Assembly(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(m, 'pair_costs is missing')

    def test_uniform_matrix_assembly_equals_replica(self):
        rng = np.random.default_rng(5)
        for seed in range(5):
            frames = fixture(n=900)   # slow 200-row gap: gap rule and restart masking both run
            x = rng.random((900, 3)) + .05
            support = SupportSet('control', x / x.sum(axis=1, keepdims=True))
            ref = assemble_research(frames, support)
            self.assertTrue(ref.stoppage_gaps)
            self.assertEqual(m.assemble_pairs(frames, support, matrix=uniform_matrix(32.)), ref)

    def test_cheap_team_switch_changes_labels(self):
        frames = fixture(n=600, gaps=())
        x = np.tile([.6, .3, .1], (600, 1))
        x[200:230] = [.3, .6, .1]
        support = SupportSet('control', x)
        uniform = m.assemble_pairs(frames, support, matrix=uniform_matrix(32.))
        cheap = m.assemble_pairs(frames, support, matrix=((0., 5., 32.), (5., 0., 32.), (32., 32., 0.)))
        self.assertNotIn('A', uniform.final)
        self.assertIn('A', cheap.final[200:230])


if __name__ == '__main__':
    unittest.main()
