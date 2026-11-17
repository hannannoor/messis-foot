"""Noise seeding/draw order, live-gap windows and stoppage masks on synthetic data."""
from dataclasses import replace
import hashlib
import random
import unittest

import numpy as np

from gap_solver.motion import motion_frame

try:
    import recent_geometry_regimes as rr
except ImportError:  # pragma: no cover - red phase
    rr = None


def mf(period=1, ball=(50., 30.), home=((49., 30.),), away=((55., 30.),)):
    return motion_frame(period, ball, home, away)


class Noise(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(rr, 'recent_geometry_regimes is missing')

    def test_seed_is_first_eight_hex_digits_of_the_prefixed_case_id(self):
        digest = hashlib.sha256(b'recent-geometry-jitter-v1:1729:dfl-J03WR9').hexdigest()
        self.assertEqual(rr.noise_seed('dfl-J03WR9'), int(digest[:8], 16))

    def test_draw_order_x_then_y_ascending_rows_fresh_generator(self):
        frames = [mf(ball=(10., 20.)), mf(ball=(11., 21.)), mf(ball=(12., 22.))]
        out = rr.add_visible_ball_noise(frames, 'case-a')
        rng = random.Random(rr.noise_seed('case-a'))
        for original, noisy in zip(frames, out):
            dx = rng.gauss(0, .25)
            dy = rng.gauss(0, .25)
            self.assertEqual(noisy.ball_x, original.ball_x + dx)
            self.assertEqual(noisy.ball_y, original.ball_y + dy)

    def test_no_draws_on_missing_rows_and_visibility_unchanged(self):
        frames = [mf(ball=(10., 20.)), mf(ball=None), mf(ball=None), mf(ball=(12., 22.))]
        out = rr.add_visible_ball_noise(frames, 'case-b')
        rng = random.Random(rr.noise_seed('case-b'))
        d1 = (rng.gauss(0, .25), rng.gauss(0, .25))
        d2 = (rng.gauss(0, .25), rng.gauss(0, .25))   # second visible row uses draws 3 and 4
        self.assertEqual((out[0].ball_x, out[0].ball_y), (10. + d1[0], 20. + d1[1]))
        self.assertEqual((out[3].ball_x, out[3].ball_y), (12. + d2[0], 22. + d2[1]))
        self.assertEqual([f.ball_observed for f in out], [True, False, False, True])
        self.assertIsNone(out[1].ball_x)
        self.assertIsNone(out[1].home_distance)

    def test_distances_are_recomputed_from_players_and_ball(self):
        out = rr.add_visible_ball_noise([mf()], 'case-c')[0]
        from math import hypot
        self.assertEqual(out.home_distance, hypot(49. - out.ball_x, 30. - out.ball_y))
        self.assertEqual(out.away_distance, hypot(55. - out.ball_x, 30. - out.ball_y))

    def test_players_labels_and_flags_are_untouched(self):
        original = mf()
        out = rr.add_visible_ball_noise([original], 'case-d')[0]
        self.assertEqual((out.home_xy, out.away_xy, out.period, out.geometry_valid),
                         (original.home_xy, original.away_xy, original.period, original.geometry_valid))

    def test_no_clipping_even_outside_the_pitch(self):
        out = rr.add_visible_ball_noise([mf(ball=(0., 0.))], 'case-e')[0]
        self.assertTrue(out.ball_x != 0. or out.ball_y != 0.)

    def test_different_cases_use_independent_generators(self):
        a = rr.add_visible_ball_noise([mf()], 'x')[0].ball_x
        b = rr.add_visible_ball_noise([mf()], 'y')[0].ball_x
        self.assertNotEqual(a, b)
        self.assertEqual(a, rr.add_visible_ball_noise([mf()], 'x')[0].ball_x)

    def test_nonfinite_transformed_record_stops_preparation(self):
        far = motion_frame(1, (1e308, 0.), [(-1e308, 0.)], [(0., 0.)])
        with self.assertRaises(ValueError):
            rr.add_visible_ball_noise([far], 'case-f')

    def test_records_without_player_positions_cannot_be_recomputed(self):
        from gap_solver.core import Frame
        with self.assertRaises(ValueError):
            rr.add_visible_ball_noise([Frame(period=1, ball_x=1., ball_y=2., home_distance=1., away_distance=2.)], 'case-g')


def _digest(case, period, index):
    return hashlib.sha256(f'{case}:live250-v1:{period}:{index}'.encode()).hexdigest()


class LiveGaps(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(rr, 'recent_geometry_regimes is missing')

    def arrays(self, n=1100, period=1):
        return (np.full(n, period, dtype=np.uint8), np.zeros(n, dtype=np.uint8), np.ones(n, dtype=bool))

    def test_windows_tile_from_period_start_and_need_visible_neighbours(self):
        periods, ref, seen = self.arrays()
        out = rr.live_gap_windows('c', periods, ref, seen)
        # window 0 has no preceding frame; windows 1..3 are eligible; frames 1000..1099 are not a complete window
        self.assertEqual(sorted(w['index'] for w in out['eligible']), [1, 2, 3])
        self.assertEqual(out['eligible'][0]['first'] % 250, 0)

    def test_each_frame_must_be_reference_live(self):
        periods, ref, seen = self.arrays(1600)
        ref[400] = 2            # D inside window 1 (250..499)
        ref[760] = 3            # X inside window 3 (750..999)
        out = rr.live_gap_windows('c', periods, ref, seen)
        self.assertEqual(sorted(w['index'] for w in out['eligible']), [2, 4, 5])

    def test_turnovers_inside_are_allowed(self):
        periods, ref, seen = self.arrays()
        ref[300:320] = 1
        out = rr.live_gap_windows('c', periods, ref, seen)
        self.assertIn(1, [w['index'] for w in out['eligible']])

    def test_visibility_threshold_is_at_least_eighty_percent(self):
        periods, ref, seen = self.arrays(1600)
        seen[260:310] = False       # window 1: exactly 50/250 hidden = 80% visible -> eligible
        seen[600:651] = False       # window 2: 51/250 hidden = 79.6% -> not eligible
        out = rr.live_gap_windows('c', periods, ref, seen)
        idx = [w['index'] for w in out['eligible']]
        self.assertIn(1, idx)
        self.assertNotIn(2, idx)

    def test_neighbouring_frames_must_be_visible_and_in_the_same_period(self):
        periods, ref, seen = self.arrays(1100)
        seen[249] = False            # frame before window 1
        seen[1000] = False           # frame after window 3
        out = rr.live_gap_windows('c', periods, ref, seen)
        self.assertEqual(sorted(w['index'] for w in out['eligible']), [2])
        periods2 = np.r_[np.full(600, 1), np.full(600, 2)].astype(np.uint8)
        ref2 = np.zeros(1200, dtype=np.uint8); seen2 = np.ones(1200, dtype=bool)
        out2 = rr.live_gap_windows('c', periods2, ref2, seen2)
        for w in out2['eligible']:
            self.assertEqual(periods2[w['first'] - 1], periods2[w['stop'] - 1])
            self.assertEqual(periods2[w['stop']], periods2[w['stop'] - 1])

    def test_second_period_tiles_from_its_own_start(self):
        periods = np.r_[np.full(777, 1), np.full(1100, 2)].astype(np.uint8)
        ref = np.zeros(len(periods), dtype=np.uint8); seen = np.ones(len(periods), dtype=bool)
        out = rr.live_gap_windows('c', periods, ref, seen)
        second = [w for w in out['eligible'] if w['period'] == 2]
        self.assertTrue(all((w['first'] - 777) % 250 == 0 for w in second))

    def test_selection_order_is_sha256_of_case_period_index_and_cap_is_ten_percent(self):
        periods, ref, seen = self.arrays(5001 + 500)
        known_live = int((ref < 2).sum())
        out = rr.live_gap_windows('case-z', periods, ref, seen)
        order = sorted((w['index'] for w in out['eligible']), key=lambda i: _digest('case-z', 1, i))
        want = 0
        while want * 250 * 10 < known_live and want < 10:
            want += 1
        self.assertEqual([w['index'] for w in out['selected']], order[:want])
        self.assertEqual(int(out['mask'].sum()), 250 * want)

    def test_masked_length_must_reach_ten_percent_exactly_at_boundary(self):
        # known live = 5000 -> target 500 -> two windows; 5001 -> three windows
        for n, expected in ((5000 + 0, 2), (5001, 3)):
            periods = np.full(n + 1, 1, dtype=np.uint8)
            periods = np.r_[periods, np.full(2000, 1)].astype(np.uint8)
            ref = np.zeros(len(periods), dtype=np.uint8)
            ref[n:] = 3   # exclude the tail from known-live; keep exactly n live frames
            seen = np.ones(len(periods), dtype=bool)
            out = rr.live_gap_windows('b', periods, ref, seen)
            self.assertEqual(len(out['selected']), expected, n)

    def test_at_most_ten_windows_per_period(self):
        periods, ref, seen = self.arrays(100000)
        out = rr.live_gap_windows('t', periods, ref, seen)
        self.assertEqual(len(out['selected']), 10)

    def test_no_eligible_windows_means_empty_mask(self):
        periods, ref, seen = self.arrays(1100)
        ref[:] = 3
        out = rr.live_gap_windows('c', periods, ref, seen)
        self.assertEqual(int(out['mask'].sum()), 0)
        self.assertEqual(out['selected'], [])

    def test_mask_hides_ball_provenance_and_distances_but_keeps_players(self):
        frames = [mf() for _ in range(5)]
        mask = np.array([False, True, True, False, False])
        out = rr.apply_ball_mask(frames, mask)
        for i in (1, 2):
            f = out[i]
            self.assertIsNone(f.ball_x); self.assertIsNone(f.home_distance); self.assertIsNone(f.away_distance)
            self.assertEqual(f.ball_provenance, 'missing'); self.assertFalse(f.ball_native_observation)
            self.assertEqual(f.home_xy, frames[i].home_xy)
        self.assertIs(out[0], frames[0])


class Stoppage(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(rr, 'recent_geometry_regimes is missing')

    def mask(self, ref, periods=None):
        ref = np.asarray(ref, dtype=np.uint8)
        periods = np.ones(len(ref), dtype=np.uint8) if periods is None else np.asarray(periods, dtype=np.uint8)
        return rr.stoppage_mask(periods, ref)

    def test_hides_full_d_run_plus_25_post_frames(self):
        ref = [0]*10 + [2]*5 + [0]*60
        m = self.mask(ref)
        self.assertEqual(np.flatnonzero(m).tolist(), list(range(10, 15 + 25)))

    def test_tail_stops_at_reference_x(self):
        ref = [0]*10 + [2]*5 + [0]*3 + [3]*10 + [0]*30
        m = self.mask(ref)
        self.assertEqual(np.flatnonzero(m).tolist(), list(range(10, 18)))

    def test_d_followed_directly_by_x_has_no_tail(self):
        m = self.mask([0]*5 + [2]*3 + [3]*5 + [0]*30)
        self.assertEqual(np.flatnonzero(m).tolist(), [5, 6, 7])

    def test_tail_stops_at_period_edge(self):
        ref = [0]*5 + [2]*3 + [0]*4 + [0]*40
        periods = [1]*12 + [2]*40
        m = self.mask(ref, periods)
        self.assertEqual(np.flatnonzero(m).tolist(), list(range(5, 12)))

    def test_overlapping_runs_merge(self):
        ref = [0]*5 + [2]*3 + [0]*10 + [2]*3 + [0]*60
        m = self.mask(ref)
        self.assertEqual(np.flatnonzero(m).tolist(), list(range(5, 21 + 25)))

    def test_d_run_at_start_and_end_of_period(self):
        m = self.mask([2]*3 + [0]*40)
        self.assertEqual(np.flatnonzero(m).tolist(), list(range(0, 28)))
        m = self.mask([0]*10 + [2]*3)
        self.assertEqual(np.flatnonzero(m).tolist(), [10, 11, 12])

    def test_no_d_means_empty_mask(self):
        self.assertFalse(self.mask([0]*20 + [1]*20).any())

    def test_d_runs_do_not_cross_period_boundary(self):
        ref = [0]*5 + [2]*3 + [2]*3 + [0]*40
        periods = [1]*8 + [2]*43
        m = self.mask(ref, periods)
        # period-1 run hides 5..7 (edge); period-2 run hides 8..10 plus a 25 frame tail
        self.assertEqual(np.flatnonzero(m).tolist(), list(range(5, 11 + 25)))

    def test_period_zero_frames_are_never_hidden(self):
        ref = [0]*3 + [2]*3 + [0]*3
        periods = [1]*6 + [0]*3
        m = self.mask(ref, periods)
        self.assertFalse(m[6:].any())


class DistanceAudit(unittest.TestCase):
    def test_exact_match_and_every_kind_of_disagreement_is_counted(self):
        good = [mf(), mf(ball=None), mf(home=(), away=((55., 30.),))]
        out = rr.distance_recompute_audit(good)
        self.assertEqual((out['checked_rows'], out['exact_rows'], out['mismatched_rows'], out['max_abs_diff']), (2, 2, 0, 0.))
        shifted = replace(mf(), home_distance=mf().home_distance + 1e-9)
        out = rr.distance_recompute_audit([mf(), shifted])
        self.assertEqual((out['exact_rows'], out['mismatched_rows']), (1, 1))
        self.assertGreater(out['max_abs_diff'], 0.)
        out = rr.distance_recompute_audit([replace(mf(), away_distance=None)])
        self.assertEqual(out['none_disagreements'], 1)
        out = rr.distance_recompute_audit([replace(mf(ball=None), home_distance=3.)])
        self.assertEqual(out['unobserved_rows_with_stored_distance'], 1)

    def test_noise_with_zero_displacement_equals_the_audit_recomputation(self):
        frame = mf(ball=(10.123, 20.456))
        zero = replace(frame, home_distance=rr._nearest(frame.home_xy, frame.ball_x, frame.ball_y),
                       away_distance=rr._nearest(frame.away_xy, frame.ball_x, frame.ball_y))
        self.assertEqual(zero, frame)


class Seal(unittest.TestCase):
    def test_seal_is_deterministic_over_dtype_and_shape(self):
        a = np.array([True, False, True]); b = np.array([True, False, True])
        self.assertEqual(rr.seal_digest({'m': a}), rr.seal_digest({'m': b}))
        self.assertNotEqual(rr.seal_digest({'m': a}), rr.seal_digest({'m': ~a}))


if __name__ == '__main__':
    unittest.main()
