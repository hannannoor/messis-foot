"""Experiment D: duration-aware decoder. Synthetic only; no match data."""
import random
import unittest

from gap_solver.soft_sequence import decode_soft
from touch_decoder import decode_variable

try:
    from duration_decoder import duration_decode, uniform_costs
except ImportError:
    duration_decode = uniform_costs = None


def random_case(seed, n=300, tie=False):
    rng = random.Random(seed)
    periods = [1] * (n // 2) + [2] * (n - n // 2)
    periods[0:5] = [0] * 5
    usable = [rng.random() > .05 for _ in range(n)]
    rows = []
    for _ in range(n):
        if tie:
            v = float(rng.choice((-1, 0, 1)))
            rows.append((v, v, float(rng.choice((-1, 0)))))
        else:
            rows.append(tuple(float(round(rng.uniform(-8, 8), 1)) for _ in range(3)))
    costs = [tuple(float(rng.choice((0, 8, 16, 32, 32, 32))) for _ in range(3)) for _ in range(n)]
    return rows, periods, usable, costs


def blip(n_before=40, n_blip=6, n_after=40):
    rows = [(3., 0., -5.)] * n_before + [(0., 12., -5.)] * n_blip + [(3., 0., -5.)] * n_after
    n = len(rows)
    return rows, [1] * n, [True] * n


class DurationDecoder(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(duration_decode, 'duration_decoder is missing')

    def test_extra_zero_equals_decode_variable_on_random_sequences(self):
        for seed in range(200):
            rows, periods, usable, costs = random_case(seed)
            expected = decode_variable(rows, periods, usable, costs)
            for L in (1, 5, 17, 50):
                self.assertEqual(duration_decode(rows, periods, usable, costs, min_run=L, extra=0.), expected, (seed, L))

    def test_extra_zero_uniform_equals_decode_soft(self):
        for seed in range(50):
            rows, periods, usable, _ = random_case(seed)
            self.assertEqual(duration_decode(rows, periods, usable, uniform_costs(len(rows), 32.), min_run=12, extra=0.),
                             decode_soft(rows, periods, usable, 32.))

    def test_exact_tie_across_run_lengths_matches_reference(self):
        for seed in range(100):
            rows, periods, usable, costs = random_case(seed, tie=True)
            self.assertEqual(duration_decode(rows, periods, usable, costs, min_run=8, extra=0.),
                             decode_variable(rows, periods, usable, costs), seed)

    def test_short_blip_is_removed_only_when_extra_applies(self):
        rows, periods, usable = blip()
        costs = uniform_costs(len(rows), 32.)
        plain = duration_decode(rows, periods, usable, costs, min_run=10, extra=0.)
        self.assertEqual(plain[40:46], ['A'] * 6)
        self.assertEqual(duration_decode(rows, periods, usable, costs, min_run=10, extra=32.), ['H'] * len(rows))

    def test_long_enough_spell_survives_extra(self):
        rows, periods, usable = blip(n_blip=12)
        self.assertEqual(duration_decode(rows, periods, usable, uniform_costs(len(rows), 32.), min_run=10, extra=32.)[40:52],
                         ['A'] * 12)

    def test_every_segment_start_has_no_short_penalty(self):
        # Segment 2 opens with a 3-row A spell: leaving it early would cost extra if k started at 1.
        rows = [(3., 0., -5.)] * 30 + [(0., 0., 0.)] + [(0., 20., -5.)] * 3 + [(3., 0., -5.)] * 30
        usable = [True] * 30 + [False] + [True] * 33
        periods = [1] * len(rows)
        labels = duration_decode(rows, periods, usable, uniform_costs(len(rows), 32.), min_run=10, extra=32.)
        self.assertEqual(labels[30], 'X')
        # A spell of 3 rows worth 60 vs switch 32: stays A only if its own origin is penalty-free and
        # leaving it costs extra 32 (total 64 > 60) -> the whole segment is A? No: H rows after are worth 3 each,
        # so the decoder keeps A through segment 2 rather than pay 64 to leave a 3-row spell.
        self.assertEqual(labels[31:34], ['A'] * 3)

    def test_invalid_inputs_raise(self):
        rows, periods, usable, costs = random_case(1)
        with self.assertRaises(ValueError):
            duration_decode(rows, periods, usable, costs, min_run=0, extra=0.)
        with self.assertRaises(ValueError):
            duration_decode(rows, periods, usable, costs, min_run=5, extra=-1.)
        with self.assertRaises(ValueError):
            duration_decode(rows, periods, usable, costs, min_run=5, extra=float('nan'))
        with self.assertRaises(ValueError):
            duration_decode(rows[:-1], periods, usable, costs, min_run=5, extra=0.)

    def test_uniform_costs_shape(self):
        self.assertEqual(uniform_costs(3, 32.), [(32., 32., 32.)] * 3)


if __name__ == '__main__':
    unittest.main()
