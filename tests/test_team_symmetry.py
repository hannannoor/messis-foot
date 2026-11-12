"""Experiment C swap map, swap-map validity, symmetrised supports. Synthetic data only."""
import random
import unittest

import numpy as np

from gap_solver.core import Frame
from gap_solver.motion import motion_frame
from gap_solver.tactical import FEATURE_NAMES, feature_rows
from gap_solver.tactical_model import FROZEN_MODEL

try:
    import team_symmetry as ts
except ImportError:  # pragma: no cover - red phase
    ts = None

MODEL = FROZEN_MODEL['model']


def bits(rows):
    return np.asarray(list(rows), dtype=np.float64).tobytes()


def random_frames(n=4000, seed=11):
    """Plain frames with every awkward case: ties, None, non-finite, negative, period 0/1/2 changes, missing ball."""
    rng = random.Random(seed)
    values = [None, float('inf'), float('nan'), -1., 0., .5, 1., 1.5, 1.75, 2., 2.5, 3., 7.25, 12., 40.]
    frames, period = [], 1
    for i in range(n):
        if rng.random() < .004:
            period = rng.choice((0, 1, 2))
        close = rng.random() < .5            # frequent control runs so the six-frame latch builds up and breaks
        side = rng.choice('HA')
        near, far = rng.choice((.5, 1., 1.5)), rng.choice((3., 4.5, 9.))
        if close:
            h, a = (near, far) if side == 'H' else (far, near)
        else:
            h, a = rng.choice(values), rng.choice(values)
        if rng.random() < .1:
            a = h                            # exact ties (signed-zero margin)
        ball = None if rng.random() < .15 else (rng.uniform(0, 105.3), rng.uniform(0, 68.))
        frames.append(Frame(period=period, ball_x=None if ball is None else ball[0], ball_y=None if ball is None else ball[1],
                            home_distance=h, away_distance=a))
    return frames


def latch_frames():
    """Home holds for 5 frames (no latch), 6th frame latches, then away takes over, then a period reset."""
    out = []
    for i in range(5):
        out.append(Frame(period=1, ball_x=10. + i, ball_y=20., home_distance=.8, away_distance=5.))
    out.append(Frame(period=1, ball_x=15., ball_y=20., home_distance=.8, away_distance=5.))
    for i in range(8):
        out.append(Frame(period=1, ball_x=16. + i, ball_y=20., home_distance=6., away_distance=.9))
    out.append(Frame(period=2, ball_x=20., ball_y=20., home_distance=.9, away_distance=5.))      # period reset
    for i in range(7):
        out.append(Frame(period=2, ball_x=21. + i, ball_y=21., home_distance=.9, away_distance=5.))
    out.append(Frame(period=2, ball_x=None, ball_y=None, home_distance=None, away_distance=None))
    out.append(Frame(period=0, ball_x=3., ball_y=3., home_distance=1., away_distance=1.))
    return out


class SwapMap(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(ts, 'team_symmetry is missing')

    def test_roles_match_the_feature_generator_by_name(self):
        ts.check_schema()                                       # raises on any role/name mismatch
        self.assertEqual(len(ts.ROLES), 18)
        self.assertEqual(tuple(name for name, _ in ts.ROLES), FEATURE_NAMES)

    def test_schema_drift_is_refused(self):
        with self.assertRaises(ValueError):
            ts.check_schema(feature_names=FEATURE_NAMES[:5] + ('x',) + FEATURE_NAMES[6:])

    def test_hand_made_row(self):
        row = (1., 1., 0., 2.5, 7.0, 4.5, 2.5, .1, .2, 3., 4., .5, 0., 3.5, 8.0, 1., 0., 2.)
        self.assertEqual(ts.swap_row(row), (1., 0., 1., 7.0, 2.5, -4.5, 2.5, .1, .2, 3., 4., .5, 0., 8.0, 3.5, 0., 1., 2.))

    def test_swap_is_an_involution_bit_for_bit(self):
        rows = list(feature_rows(random_frames(800)))
        for row in rows:
            self.assertEqual(bits([ts.swap_row(ts.swap_row(row))]), bits([row]))

    def test_tie_margin_is_positive_zero_not_negative_zero(self):
        row = (1., 1., 1., 3., 3., 0., 3., .1, .1, 0., 0., 0., 0., 3., 3., 0., 0., 10.)
        self.assertEqual(bits([ts.swap_row(row)]), bits([row]))
        matrix = np.asarray([row], dtype=np.float32)
        self.assertEqual(ts.swap_matrix(matrix).tobytes(), matrix.tobytes())

    def test_matrix_and_row_swaps_agree_and_do_not_mutate(self):
        rows = list(feature_rows(random_frames(500, seed=3)))
        matrix = np.asarray(rows, dtype=np.float32)
        before = matrix.copy()
        swapped = ts.swap_matrix(matrix)
        np.testing.assert_array_equal(matrix, before)
        self.assertEqual(swapped.dtype, np.float32)
        np.testing.assert_array_equal(swapped, np.asarray([ts.swap_row(r) for r in rows], dtype=np.float32))

    def test_wrong_shapes_refused(self):
        with self.assertRaises(ValueError):
            ts.swap_row((0.,) * 17)
        with self.assertRaises(ValueError):
            ts.swap_matrix(np.zeros((3, 20), dtype=np.float32))


class SwapMapValidity(unittest.TestCase):
    """feature_rows(swapped frames) must equal swap(feature_rows(frames)) bit for bit."""

    def setUp(self):
        self.assertIsNotNone(ts, 'team_symmetry is missing')

    def check(self, frames):
        direct = list(feature_rows(frames))
        swapped = list(feature_rows(ts.swap_frames(frames)))
        self.assertEqual(len(direct), len(swapped))
        self.assertEqual(bits(swapped), bits(ts.swap_row(r) for r in direct))
        return direct

    def test_random_sequences_with_ties_missing_values_and_period_changes(self):
        for seed in (11, 12, 13):
            self.check(random_frames(3000, seed=seed))

    def test_latch_build_up_exchange_and_period_reset(self):
        rows = self.check(latch_frames())
        self.assertEqual(rows[4][15:17], (0., 0.))           # five frames: not latched
        self.assertEqual(rows[5][15:17], (1., 0.))           # sixth frame latches home
        self.assertTrue(any(r[16] == 1. for r in rows))      # away latches later
        self.assertEqual(rows[14][15:17], (0., 0.))          # period change clears the latch (and age restarts)

    def test_motion_frames_exchange_players_and_distances(self):
        home = ((10., 10.), (14., 12.), (30., 5.))
        away = ((10.5, 10.), (50., 50.))
        frames = [motion_frame(1, (10.2 + i * .01, 10.), home, away, (1, 2, 3), (21, 22)) for i in range(20)]
        frames += [motion_frame(1, None, home, away, (1, 2, 3), (21, 22))]
        swapped = ts.swap_frames(frames)
        self.assertEqual(swapped[0].home_xy, away)
        self.assertEqual(swapped[0].away_xy, home)
        self.assertEqual(swapped[0].home_ids, (21, 22))
        self.assertEqual(swapped[0].away_ids, (1, 2, 3))
        self.assertEqual(swapped[0].home_distance, frames[0].away_distance)
        self.assertEqual(swapped[0].away_distance, frames[0].home_distance)
        self.check(frames)

    def test_swap_frames_does_not_mutate_inputs_and_is_an_involution(self):
        frames = latch_frames()
        again = ts.swap_frames(ts.swap_frames(frames))
        self.assertEqual(again, frames)

    def test_tag_team_letters_are_exchanged_if_present(self):
        f = Frame(period=1, ball_x=1., ball_y=1., home_distance=1., away_distance=2., tag_team='H')
        self.assertEqual(ts.swap_frames([f])[0].tag_team, 'A')

    def test_a_wrong_map_is_detected(self):
        """Mutation check: if the margin were not negated the validity comparison must fail."""
        frames = random_frames(500)
        direct = list(feature_rows(frames))
        swapped = list(feature_rows(ts.swap_frames(frames)))
        broken = []
        for r in direct:
            s = list(ts.swap_row(r))
            s[5] = r[5]
            broken.append(tuple(s))
        self.assertNotEqual(bits(swapped), bits(broken))


class Supports(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(ts, 'team_symmetry is missing')

    def test_formula_by_hand(self):
        p = np.asarray([[.7, .2, .1]])
        q = np.asarray([[.1, .6, .3]])
        np.testing.assert_allclose(ts.symmetrise(p, q), [[.65, .15, .2]], rtol=0, atol=1e-15)

    def test_formula_rows_sum_to_one_and_stay_in_range(self):
        rng = np.random.default_rng(5)
        p, q = rng.dirichlet((1, 1, 1), 500), rng.dirichlet((1, 1, 1), 500)
        s = ts.symmetrise(p, q)
        np.testing.assert_allclose(s.sum(axis=1), 1., rtol=0, atol=1e-12)
        self.assertTrue(((s >= 0) & (s <= 1)).all())

    def test_formula_rejects_bad_shapes_and_non_finite(self):
        with self.assertRaises(ValueError):
            ts.symmetrise(np.zeros((2, 3)), np.zeros((3, 3)))
        with self.assertRaises(ValueError):
            ts.symmetrise(np.full((2, 3), np.nan), np.zeros((2, 3)))

    def test_candidate_is_exactly_the_formula_on_the_frozen_tree(self):
        matrix = np.asarray(list(feature_rows(random_frames(1500, seed=21))), dtype=np.float32)
        p = ts.control_supports(matrix, MODEL)
        q = ts.control_supports(ts.swap_matrix(matrix), MODEL)
        np.testing.assert_array_equal(ts.candidate_supports(matrix, MODEL), ts.symmetrise(p, q))

    def test_control_is_the_release_tree(self):
        from memory_ablation import predict_supports
        matrix = np.asarray(list(feature_rows(random_frames(600, seed=2))), dtype=np.float32)
        np.testing.assert_array_equal(ts.control_supports(matrix, MODEL), predict_supports(matrix, MODEL))
        from gap_solver.tactical import PortableTree
        tree = PortableTree(MODEL)
        rows = list(feature_rows(random_frames(300, seed=2)))
        np.testing.assert_array_equal(ts.control_supports(np.asarray(rows, dtype=np.float32), MODEL),
                                      np.asarray([tree.predict(r) for r in rows]))

    def test_candidate_symmetry_property(self):
        """Swapping the teams in the input exchanges H and A in the output, D unchanged, to 1e-12."""
        for seed in (31, 32):
            matrix = np.asarray(list(feature_rows(random_frames(2000, seed=seed))), dtype=np.float32)
            s = ts.candidate_supports(matrix, MODEL)
            t = ts.candidate_supports(ts.swap_matrix(matrix), MODEL)
            self.assertLessEqual(float(np.abs(t - s[:, [1, 0, 2]]).max()), 1e-12)
            self.assertEqual(ts.symmetry_error(matrix, MODEL), float(np.abs(t - s[:, [1, 0, 2]]).max()))

    def test_candidate_on_arbitrary_rows_is_still_symmetric(self):
        rng = np.random.default_rng(9)
        matrix = rng.uniform(-1, 12, size=(3000, 18)).astype(np.float32)
        self.assertLessEqual(ts.symmetry_error(matrix, MODEL), 1e-12)

    def test_control_is_not_symmetric_on_this_tree(self):
        """Premise of the experiment: the frozen tree does treat the teams differently on some rows."""
        matrix = np.asarray(list(feature_rows(random_frames(3000, seed=41))), dtype=np.float32)
        p = ts.control_supports(matrix, MODEL)
        q = ts.control_supports(ts.swap_matrix(matrix), MODEL)
        self.assertGreater(float(np.abs(q - p[:, [1, 0, 2]]).max()), 1e-3)

    def test_symmetric_rows_have_no_home_lean(self):
        row = (1., 1., 1., 4., 4., 0., 4., .3, .2, 1., 2., 0., 0., 4., 4., 0., 0., 10.)
        self.assertEqual(ts.swap_row(row), row)
        s = ts.candidate_supports(np.asarray([row], dtype=np.float32), MODEL)
        self.assertEqual(s[0, 0], s[0, 1])

    def test_leaf_index_agrees_with_supports(self):
        matrix = np.asarray(list(feature_rows(random_frames(1000, seed=51))), dtype=np.float32)
        leaves = ts.leaf_index(matrix, MODEL)
        np.testing.assert_array_equal(np.asarray(MODEL['probabilities'], dtype=np.float64)[leaves],
                                      ts.control_supports(matrix, MODEL))
        self.assertTrue((np.asarray(MODEL['children_left'])[leaves] == -1).all())

    def test_leaf_22_is_the_described_leaf(self):
        ts.check_leaf_22(MODEL)                                  # recent_speed>.0104, no away control, age>1.54, slow<=.02
        broken = dict(MODEL, threshold=list(MODEL['threshold']))
        broken['threshold'][0] = 99.
        with self.assertRaises(ValueError):
            ts.check_leaf_22(broken)


class BiasSummary(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(ts, 'team_symmetry is missing')

    def test_numbers_by_hand(self):
        p = np.asarray([[.7, .2, .1], [.5, .3, .2], [.2, .7, .1], [.9, .05, .05]])
        s = np.asarray([[.5, .4, .1], [.4, .4, .2], [.4, .5, .1], [.5, .45, .05]])
        usable = np.asarray([True, True, True, False])
        observed = np.asarray([True, False, True, True])
        leaves = np.asarray([22, 22, 5, 22])
        out = ts.bias_summary(p, s, usable, observed, leaves, leaf=22)
        self.assertEqual(out['usable_rows'], 3)
        self.assertAlmostEqual(out['control_mean_h_minus_a'], ((.5) + (.2) + (-.5)) / 3)
        self.assertEqual(out['ball_missing_rows'], 1)
        self.assertAlmostEqual(out['control_mean_h_minus_a_ball_missing'], .2)
        self.assertAlmostEqual(out['leaf22_share'], 2 / 3)
        self.assertAlmostEqual(out['candidate_mean_h_minus_a'], (.1 + 0. - .1) / 3)
        self.assertAlmostEqual(out['candidate_mean_h_minus_a_ball_missing'], 0.)
        # argmax: control H,H,A ; candidate H,(tie H/A -> H),A
        self.assertEqual(out['argmax_differs_rows'], 0)
        self.assertEqual(out['argmax_differs_share'], 0.)

    def test_label_lean_removed_is_the_swap_averaged_lean(self):
        """mean (lean(x) + lean(swap x)) / 2 over usable rows == control mean - candidate mean, and is 0 for the candidate."""
        matrix = np.asarray(list(feature_rows(random_frames(2500, seed=61))), dtype=np.float32)
        p = ts.control_supports(matrix, MODEL)
        q = ts.control_supports(ts.swap_matrix(matrix), MODEL)
        s = ts.candidate_supports(matrix, MODEL)
        usable = np.ones(len(matrix), dtype=bool)
        observed = np.arange(len(matrix)) % 3 != 0
        out = ts.bias_summary(p, s, usable, observed, ts.leaf_index(matrix, MODEL))
        direct = float((((p[:, 0] - p[:, 1]) + (q[:, 0] - q[:, 1])) / 2).mean())
        self.assertAlmostEqual(out['label_lean_removed_mean'], direct, places=12)
        self.assertNotEqual(direct, 0.)
        missing = ~observed
        direct_missing = float((((p[:, 0] - p[:, 1]) + (q[:, 0] - q[:, 1])) / 2)[missing].mean())
        self.assertAlmostEqual(out['label_lean_removed_mean_ball_missing'], direct_missing, places=12)
        # the symmetrised supports carry no label lean at all
        s_swapped = ts.candidate_supports(ts.swap_matrix(matrix), MODEL)
        self.assertLessEqual(float(np.abs(((s[:, 0] - s[:, 1]) + (s_swapped[:, 0] - s_swapped[:, 1]))).max()), 1e-12)

    def test_merge_pools_counts_and_sums_not_means(self):
        a = dict(usable_rows=1, ball_missing_rows=0, leaf22_rows=1, argmax_differs_rows=0, control_sum=.5, control_missing_sum=0.,
                 candidate_sum=.1, candidate_missing_sum=0.)
        b = dict(usable_rows=3, ball_missing_rows=1, leaf22_rows=0, argmax_differs_rows=1, control_sum=-.3, control_missing_sum=-.1,
                 candidate_sum=.0, candidate_missing_sum=0.)
        out = ts.merge_bias([a, b])
        self.assertEqual(out['usable_rows'], 4)
        self.assertAlmostEqual(out['control_mean_h_minus_a'], .2 / 4)
        self.assertAlmostEqual(out['control_mean_h_minus_a_ball_missing'], -.1)
        self.assertAlmostEqual(out['leaf22_share'], .25)
        self.assertAlmostEqual(out['argmax_differs_share'], .25)

    def test_counts_argmax_changes_and_handles_no_missing_rows(self):
        p = np.asarray([[.6, .3, .1], [.2, .3, .5]])
        s = np.asarray([[.4, .5, .1], [.2, .3, .5]])
        out = ts.bias_summary(p, s, np.asarray([True, True]), np.asarray([True, True]), np.asarray([22, 3]), leaf=22)
        self.assertEqual(out['argmax_differs_rows'], 1)
        self.assertAlmostEqual(out['argmax_differs_share'], .5)
        self.assertIsNone(out['control_mean_h_minus_a_ball_missing'])
        self.assertEqual(out['ball_missing_rows'], 0)

    def test_empty_usable_set_gives_none_not_nan(self):
        out = ts.bias_summary(np.zeros((1, 3)) + [.5, .3, .2], np.zeros((1, 3)) + [.4, .4, .2],
                              np.asarray([False]), np.asarray([True]), np.asarray([1]), leaf=22)
        self.assertEqual(out['usable_rows'], 0)
        self.assertIsNone(out['control_mean_h_minus_a'])
        self.assertIsNone(out['leaf22_share'])


if __name__ == '__main__':
    unittest.main()
