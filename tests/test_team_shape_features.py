"""Synthetic contract checks for the four prospective team-shape features."""
from dataclasses import replace
import unittest
import numpy as np
from gap_solver.motion import motion_frame
from gap_solver.tactical import feature_rows

try:
    import team_shape_features as ts
except ImportError:
    ts = None


def frame(i=0, n=7, period=1, ball=True):
    home = tuple((20. + i / 25 + j - 3, 34.) for j in range(n))
    away = tuple((80. - i / 50 + (j - 3) * 2, 34.) for j in range(n))
    return motion_frame(period, (50., 34.) if ball else None, home, away,
                        tuple(range(n)), tuple(range(10, 10 + n)))


class Features(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(ts, 'team_shape_features is missing')

    def matrix(self, frames):
        return ts.research_matrix(frames, pitch_midpoint=50.)

    def test_spread_is_rms_distance_and_advance_is_team_relative(self):
        rows = self.matrix([frame(i) for i in range(26)])
        self.assertEqual(rows.shape, (26, 22))
        # RMS for offsets -3..3 is 2m; away offsets doubled -> 4m.
        np.testing.assert_allclose(rows[:, 18], -2., atol=1e-6)
        np.testing.assert_array_equal(rows[:25, 19], 0.)
        self.assertAlmostEqual(float(rows[25, 19]), .5, places=5)
        np.testing.assert_array_equal(rows[:25, 21], 0.)
        self.assertEqual(rows[25, 21], 1.)

    def test_original_feature_rows_are_bit_identical_including_missing_ball(self):
        frames = [frame(i, ball=(i % 3 != 0)) for i in range(60)]
        rows = list(ts.research_rows(frames, pitch_midpoint=50.))
        self.assertEqual([tuple(r[:18]) for r in rows], list(feature_rows(frames)))
        self.assertEqual(self.matrix(frames)[:, :18].tobytes(),
                         np.asarray(list(feature_rows(frames)), np.float32).tobytes())

    def test_closing_uses_matching_ids_and_strict_speed_threshold(self):
        frames = [frame(i) for i in range(6)]
        # All seven home players close at 2m/s; away moves at <=1m/s.
        for i in range(6):
            h = tuple((40. + j / 10 + i * .08, 34.) for j in range(7))
            a = tuple((60. + j / 10 - i * .02, 34.) for j in range(7))
            frames[i] = motion_frame(1, (50., 34.), h, a, tuple(range(7)), tuple(range(10,17)))
        self.assertEqual(self.matrix(frames)[5, 20], 7.)
        frames[5] = replace(frames[5], home_ids=tuple(range(1,8)))
        self.assertEqual(self.matrix(frames)[5, 20], 6.)

    def test_closing_excludes_distant_stationary_and_unmatched_players(self):
        frames = [frame(i) for i in range(6)]
        self.assertEqual(self.matrix(frames)[5, 20], 0.)

    def test_closing_counts_matched_individuals_without_seven_player_endpoint_gate(self):
        frames=[]
        for i in range(27):
            n=6 if i==26 else 7
            h=tuple((40.+j/10+i*.08,34.) for j in range(n))
            a=tuple((60.+j/10,34.) for j in range(7))
            frames.append(motion_frame(1,(50.,34.),h,a,tuple(range(n)),tuple(range(10,17))))
        self.assertEqual(self.matrix(frames)[26,20],6.)
        self.assertEqual(self.matrix(frames)[26,21],0.)

    def test_no_ids_and_missing_ball_make_closing_unsupported(self):
        frames = [replace(frame(i), home_ids=(), away_ids=()) for i in range(30)]
        np.testing.assert_array_equal(self.matrix(frames)[:, 20], 0.)
        self.assertFalse(ts.id_support(frames))
        frames = [frame(i, ball=False) for i in range(30)]
        self.assertEqual(self.matrix(frames)[-1, 21], 1.)
        np.testing.assert_array_equal(self.matrix(frames)[:, 20], 0.)

    def test_seven_player_threshold_and_nonfinite_players_excluded(self):
        frames = [frame(i) for i in range(27)]
        frames[25] = frame(25, n=6)
        rows = self.matrix(frames)
        self.assertEqual(rows[25, 19], 0.)
        self.assertEqual(rows[25, 21], 0.)
        bad = replace(frame(), home_xy=frame().home_xy[:6] + ((float('nan'), 34.),))
        self.assertFalse(ts.shape_valid(bad, 'home'))
        self.assertTrue(ts.shape_valid(frame(), 'home'))

    def test_spread_uses_only_joint_valid_rows_within_25_slots(self):
        frames = [frame(0)] + [frame(0, n=6) for _ in range(25)]
        rows = self.matrix(frames)
        self.assertEqual(rows[24, 18], -2.)
        self.assertEqual(rows[25, 18], 0.)

    def test_period_and_invalid_geometry_clear_all_new_windows(self):
        frames = [frame(i) for i in range(27)]
        frames += [replace(frame(27), geometry_valid=False)]
        frames += [frame(28), frame(29, period=0), frame(30, period=2)]
        rows = self.matrix(frames)
        np.testing.assert_array_equal(rows[27, 18:], 0.)
        self.assertEqual(rows[28, 21], 0.)
        np.testing.assert_array_equal(rows[29, 18:], 0.)
        self.assertEqual(rows[30, 21], 0.)

    def test_team_swap_flips_three_differences_and_preserves_support(self):
        frames = [frame(i) for i in range(60)]
        swapped = [replace(f, home_xy=f.away_xy, away_xy=f.home_xy,
                           home_ids=f.away_ids, away_ids=f.home_ids,
                           home_distance=f.away_distance, away_distance=f.home_distance) for f in frames]
        a, b = self.matrix(frames), self.matrix(swapped)
        np.testing.assert_array_equal(a[:, 18:21], -b[:, 18:21])
        np.testing.assert_array_equal(a[:, 21], b[:, 21])

    def test_direction_is_per_period_and_uses_all_shape_valid_rows(self):
        a = frame()
        b = replace(a, period=2, home_xy=a.away_xy, away_xy=a.home_xy)
        self.assertEqual(ts.attacking_directions([a,b], 50.), {1:(1,-1),2:(-1,1)})

    def test_one_team_mean_on_midpoint_has_unambiguous_lower_team(self):
        self.assertEqual(ts.attacking_directions([frame()],20.),{1:(1,-1)})

    def test_direction_stops_on_same_side_or_no_valid_team_rows(self):
        with self.assertRaisesRegex(ValueError, 'same side|midpoint'):
            ts.attacking_directions([frame()], 100.)
        with self.assertRaisesRegex(ValueError, 'no shape-valid'):
            ts.attacking_directions([frame(n=6)], 50.)

    def test_geometry_flag_and_pitch_midpoint_fail_closed(self):
        with self.assertRaises(ValueError):
            self.matrix([replace(frame(), geometry_valid=None)])
        with self.assertRaises(ValueError):
            ts.attacking_directions([frame()], float('nan'))

    def test_coverage_support_needs_no_direction_ball_or_reference(self):
        frames = [frame(i,ball=False) for i in range(60)]
        np.testing.assert_array_equal(ts.coverage_support(frames),self.matrix(frames)[:,21].astype(bool))
        frames[30]=replace(frames[30],geometry_valid=False)
        out=ts.coverage_support(frames)
        self.assertFalse(any(out[30:56]))
        self.assertTrue(out[56])

    def test_wcsf_native_pitch_centre_maps_exactly_to_canonical_centre(self):
        from wcsf_geometry import _canonical
        self.assertEqual(_canonical(0,0),(52.65,34.0))

    def test_provider_midpoints_use_loader_native_centre_mapping_and_exact_assertion(self):
        for provider in ('dfl','skillcorner'):
            self.assertEqual(ts.provider_midpoint(provider,{'canonical_pitch_m':[105.3,68.]}),52.65)
            with self.assertRaises(ValueError):
                ts.provider_midpoint(provider,{'canonical_pitch_m':[105.30000000001,68.]})
        self.assertEqual(ts.provider_midpoint('wcsf'),52.65)


if __name__ == '__main__':
    unittest.main()
