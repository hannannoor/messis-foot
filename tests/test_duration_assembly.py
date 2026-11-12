"""Experiment D: spell-length rule and duration research assembly. Synthetic only."""
import random
import unittest

import numpy as np

import recent_geometry_assembly as ra
from test_gap_liveness import fixture

try:
    import duration_assembly as da
except ImportError:
    da = None


def groups_with_runs(lengths):
    reference, label = [], 0
    for n in lengths:
        reference += [label] * n
        label = (label + 1) % 3
    return [dict(reference=np.array(reference, np.uint8), periods=np.ones(len(reference), np.uint8))]


def supports_for(frames, seed, flips=()):
    """Deterministic synthetic supports: mostly H with A stretches and short A blips."""
    rng = random.Random(seed)
    rows = []
    for i, _ in enumerate(frames):
        if any(lo <= i < hi for lo, hi in flips):
            rows.append((.0005, .999, .0005))       # ln(.999/.0005) = 7.6 per row: 10 rows beat two switches (64)
        else:
            a = .1 + rng.random() * .05
            rows.append((1 - a - .02, a, .02))
    return np.array(rows)


class SpellLengthRule(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(da, 'duration_assembly is missing')

    def test_rule_uses_nearest_rank_10th_percentile(self):
        r = da.spell_length_rule(groups_with_runs(list(range(1, 101))))
        self.assertEqual((r['min_run'], r['runs'], r['percentile_rank']), (10, 100, 10))

    def test_rule_clamps_low_and_high(self):
        self.assertEqual(da.spell_length_rule(groups_with_runs([1] * 10 + [30] * 90))['min_run'], 5)
        self.assertEqual(da.spell_length_rule(groups_with_runs([100] * 100))['min_run'], 50)

    def test_rule_breaks_runs_at_unknown_codes_and_period_changes(self):
        g = [dict(reference=np.array([0, 0, 3, 0, 0, 1, 1], np.uint8), periods=np.array([1, 1, 1, 1, 2, 2, 2], np.uint8))]
        self.assertEqual(da.spell_length_rule(g)['runs'], 4)       # [0,0] | 3 | [0] | p2: [0] [1,1]

    def test_rule_ignores_period_zero_and_requires_runs(self):
        g = [dict(reference=np.array([0, 0, 1], np.uint8), periods=np.array([0, 0, 1], np.uint8))]
        self.assertEqual(da.spell_length_rule(g)['runs'], 1)
        with self.assertRaises(ValueError):
            da.spell_length_rule([dict(reference=np.array([3, 3], np.uint8), periods=np.array([1, 1], np.uint8))])


class DurationAssembly(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(da, 'duration_assembly is missing')

    def cases(self):
        yield fixture(), ((100, 110), (600, 700))
        yield fixture(gaps=((300, 500), (650, 660))), ((150, 158), (520, 531), (700, 800))
        yield fixture(n=600, gaps=(), periods=[1] * 300 + [2] * 300), ((290, 320), (400, 409))

    def test_extra_zero_assembly_equals_research_assembly(self):
        for seed, (frames, flips) in enumerate(self.cases()):
            support = ra.SupportSet('candidate', supports_for(frames, seed, flips))
            a = da.assemble_duration(frames, support, min_run=12, extra=0.)
            b = ra.assemble_research(frames, support)
            self.assertEqual((a.control, a.gapped, a.restarted, a.final, a.stoppage_gaps),
                             (b.control, b.gapped, b.restarted, b.final, b.stoppage_gaps), seed)
            self.assertEqual(a.decoder_passes, 2)

    def test_extra_removes_short_blips_in_first_and_restart_decodes(self):
        frames = fixture(gaps=((300, 500),))
        flips = ((100, 110), (560, 570))           # a 10-row blip before and after the stoppage gap
        support = ra.SupportSet('candidate', supports_for(frames, 3, flips))
        plain = da.assemble_duration(frames, support, min_run=12, extra=0.)
        strict = da.assemble_duration(frames, support, min_run=12, extra=32.)
        self.assertIn('A', plain.control[100:110])
        self.assertIn('A', plain.final[560:570])
        # With the penalty the optimum pads a strong short spell up to min_run rather than deleting it.
        def a_run(labels, inside):
            lo = hi = inside
            while labels[lo - 1] == 'A':
                lo -= 1
            while labels[hi] == 'A':
                hi += 1
            return hi - lo
        self.assertLess(a_run(plain.control, 105), 12)
        self.assertGreaterEqual(a_run(strict.control, 105), 12)
        self.assertGreaterEqual(a_run(strict.final, 565), 12)

    def test_restart_segment_start_has_no_short_penalty(self):
        # A short A spell right at the start of the restart segment after the stoppage gap survives extra=32.
        frames = fixture(gaps=((300, 500),))
        support = ra.SupportSet('candidate', supports_for(frames, 4, ((500, 505),)))
        strict = da.assemble_duration(frames, support, min_run=12, extra=32.)
        plain = da.assemble_duration(frames, support, min_run=12, extra=0.)
        self.assertEqual(strict.final[500:505], plain.final[500:505])

    def test_rejects_label_hints_and_wrong_lengths(self):
        frames = fixture()
        support = ra.SupportSet('candidate', supports_for(frames, 0))
        with self.assertRaises(ValueError):
            da.assemble_duration(frames[:-1], support, min_run=12, extra=32.)


if __name__ == '__main__':
    unittest.main()
