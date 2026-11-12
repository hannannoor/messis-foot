"""Window arithmetic, expiry, clearing and prefix identity of the 20-column research adapter (synthetic only)."""
from dataclasses import dataclass, replace
from math import fsum, nan, inf
import unittest

import numpy as np

from gap_solver.core import Frame
from gap_solver.motion import motion_frame
from gap_solver.tactical import feature_rows

try:
    import recent_geometry_features as rg
except ImportError:  # pragma: no cover - red phase
    rg = None


def fr(period=1, h=2., a=5., ball=True, **kw):
    return Frame(period=period, ball_x=50. if ball else None, ball_y=30. if ball else None,
                 home_distance=h, away_distance=a, **kw)


def tail(rows):
    return [(r[18], r[19]) for r in rows]


class Features(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(rg, 'recent_geometry_features is missing')

    def test_names_and_width(self):
        self.assertEqual(len(rg.RESEARCH_FEATURE_NAMES), 20)
        self.assertEqual(rg.RESEARCH_FEATURE_NAMES[18:], ('recent_distance_margin', 'recent_distance_support'))
        self.assertEqual(rg.WINDOW, 12)

    def test_window_arithmetic_is_trailing_mean_of_distance_margin(self):
        rows = list(rg.research_rows([fr(h=2., a=3.), fr(h=2., a=4.), fr(h=2., a=8.)]))
        self.assertEqual(tail(rows), [(1., 1/12), (1.5, 2/12), (fsum([1., 2., 6.])/3, 3/12)])

    def test_margin_uses_the_clipped_existing_column(self):
        rows = list(rg.research_rows([fr(h=50., a=40.)]))
        self.assertEqual(rows[0][5], 0.)   # both clipped to 30 in column 5
        self.assertEqual(rows[0][18], 0.)

    def test_negative_margin_is_signed(self):
        rows = list(rg.research_rows([fr(h=6., a=1.)]))
        self.assertEqual(tail(rows), [(-5., 1/12)])

    def test_twelve_slot_expiry_includes_current_row(self):
        frames = [fr(h=2., a=12.)] + [fr(h=2., a=2.) for _ in range(12)]
        rows = list(rg.research_rows(frames))
        self.assertEqual(rows[11][18], fsum([10.] + [0.]*11)/12)   # window rows 0..11 still holds row 0
        self.assertEqual(rows[11][19], 1.)
        self.assertEqual(rows[12][18], 0.)                         # row 0 expired; window rows 1..12
        self.assertEqual(rows[12][19], 1.)

    def test_unsupported_rows_occupy_slots_and_are_not_zero_observations(self):
        frames = [fr(h=2., a=8.)] + [fr(ball=False, h=None, a=None) for _ in range(11)] + [fr(ball=False, h=None, a=None)]
        rows = list(rg.research_rows(frames))
        self.assertEqual(tail(rows)[1], (6., 1/12))       # mean of the single qualifying row, not 3.0
        self.assertEqual(tail(rows)[11], (6., 1/12))      # still inside the 12-row window
        self.assertEqual(tail(rows)[12], (0., 0.))        # expired after 12 slots despite no new evidence

    def test_missing_ball_with_distances_present_does_not_qualify(self):
        rows = list(rg.research_rows([fr(ball=False, h=2., a=5.), fr(h=2., a=5.)]))
        self.assertEqual(tail(rows), [(0., 0.), (3., 1/12)])

    def test_bad_distances_are_unsupported_slots(self):
        for bad in ((None, 5.), (2., None), (-1., 5.), (2., -0.5), (nan, 5.), (2., inf)):
            rows = list(rg.research_rows([fr(h=2., a=8.), fr(h=bad[0], a=bad[1])]))
            self.assertEqual(tail(rows)[1], (6., 1/12), bad)

    def test_empty_qualifying_set_is_zero_not_nan(self):
        rows = list(rg.research_rows([fr(ball=False, h=None, a=None)]))
        self.assertEqual(tail(rows), [(0., 0.)])

    def test_support_at_period_start_is_over_twelve(self):
        rows = list(rg.research_rows([fr(period=2)]))
        self.assertEqual(rows[0][19], 1/12)

    def test_period_change_clears_only_the_new_window(self):
        frames = [fr(period=1, h=2., a=12.) for _ in range(5)] + [fr(period=2, h=2., a=3.)]
        rows = list(rg.research_rows(frames))
        self.assertEqual(tail(rows)[5], (1., 1/12))
        # the original recent-speed / retained state is untouched by the new window
        self.assertEqual(rows[5][:18], list(feature_rows(frames))[5])

    def test_period_zero_clears_every_row_and_contributes_nothing(self):
        frames = [fr(period=1, h=2., a=12.), fr(period=0, h=2., a=12.), fr(period=0), fr(period=1, h=2., a=3.)]
        rows = list(rg.research_rows(frames))
        self.assertEqual(tail(rows), [(10., 1/12), (0., 0.), (0., 0.), (1., 1/12)])

    def test_invalid_geometry_clears_and_contributes_nothing(self):
        good = motion_frame(1, (50., 30.), [(49., 30.)], [(55., 30.)])
        bad = replace(good, geometry_valid=False)
        rows = list(rg.research_rows([good, good, bad, good]))
        self.assertEqual(tail(rows), [(4., 1/12), (4., 2/12), (0., 0.), (4., 1/12)])

    def test_geometry_contract_plain_frame_is_valid(self):
        self.assertTrue(rg.geometry_valid(fr()))

    def test_geometry_contract_motion_frame_needs_real_bool(self):
        good = motion_frame(1, (50., 30.), [(49., 30.)], [(55., 30.)])
        self.assertTrue(rg.geometry_valid(good))
        for bad in (1, 0, 'True', None, 1.0):
            with self.assertRaises(ValueError):
                list(rg.research_rows([replace(good, geometry_valid=bad)]))

    def test_any_record_declaring_the_field_must_supply_a_bool(self):
        @dataclass(frozen=True)
        class Declares(Frame):
            geometry_valid: object = True
        with self.assertRaises(ValueError):
            list(rg.research_rows([Declares(period=1, ball_x=1., ball_y=1., home_distance=1., away_distance=2., geometry_valid=None)]))
        ok = list(rg.research_rows([Declares(period=1, ball_x=1., ball_y=1., home_distance=1., away_distance=2., geometry_valid=True)]))
        self.assertEqual(tail(ok), [(1., 1/12)])

    def test_bad_flag_stops_even_in_period_zero(self):
        good = motion_frame(0, (50., 30.), [(49., 30.)], [(55., 30.)])
        with self.assertRaises(ValueError):
            list(rg.research_rows([replace(good, geometry_valid='x')]))

    def test_invalid_period_stops_like_the_original(self):
        with self.assertRaises(ValueError):
            list(rg.research_rows([fr(period=3)]))

    def test_first_eighteen_columns_are_bit_identical_to_feature_rows(self):
        mf = motion_frame(1, (50., 30.), [(49., 30.)], [(55., 30.)])
        frames = []
        for i in range(120):
            period = 1 if i < 50 else 0 if i < 55 else 2
            if i % 17 == 3:
                frames.append(fr(period=period, ball=False, h=None, a=None))
            elif i % 23 == 5:
                frames.append(replace(mf, period=period, geometry_valid=False))
            elif i % 11 == 0:
                frames.append(fr(period=period, h=1.5, a=1.0 + i/10))
            else:
                frames.append(fr(period=period, h=(i % 7) + .3, a=(i % 5) + 1.1))
        mine = list(rg.research_rows(frames))
        theirs = list(feature_rows(frames))
        self.assertEqual(len(mine), len(theirs))
        for a, b in zip(mine, theirs):
            self.assertEqual(len(a), 20)
            self.assertEqual(tuple(a[:18]), tuple(b))

    def test_labels_tags_and_dead_fields_never_enter_the_new_columns(self):
        plain = [fr(h=2., a=2.5 + i % 4) for i in range(30)]
        tagged = [replace(f, tag_team='H', restart_hint=True, dead_evidence=True, dead_source='x') for f in plain]
        self.assertEqual([r[18:] for r in rg.research_rows(plain)], [r[18:] for r in rg.research_rows(tagged)])

    def test_matrix_is_float32_20_wide_and_finite(self):
        m = rg.research_matrix([fr(h=2., a=2.5), fr(ball=False, h=None, a=None)])
        self.assertEqual(m.dtype, np.float32)
        self.assertEqual(m.shape, (2, 20))
        self.assertTrue(np.isfinite(m).all())
        self.assertEqual(m[0, 18], np.float32(.5))

    def test_summation_is_exact_fsum_independent_of_interpreter(self):
        margins = [.1, .2, .3, 1e-9, 7.7, -2.2]
        frames = [fr(h=3., a=3. + m) for m in margins]
        rows = list(rg.research_rows(frames))
        used = [frames[i].away_distance - frames[i].home_distance for i in range(len(frames))]
        self.assertEqual(rows[-1][18], fsum(used)/len(used))


if __name__ == '__main__':
    unittest.main()
