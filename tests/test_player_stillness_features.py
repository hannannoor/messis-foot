"""Experiment E: player stillness features. Synthetic only; no match data."""
from dataclasses import replace
import unittest

import numpy as np

from gap_solver.motion import motion_frame
from gap_solver.tactical import feature_rows

try:
    import player_stillness_features as ps
except ImportError:
    ps = None


def frame(i, slow=14, fast=6, period=1, home_ids=None, away_ids=None, ball=(50., 34.)):
    """slow players move 0.5 m/s, fast players 3 m/s, along x; 20 players split 10/10 by default."""
    players = []
    for j in range(slow + fast):
        speed = .5 if j < slow else 3.
        players.append((10. + j * 3 + speed * i / 25, 5. + j))
    home, away = tuple(players[:10]), tuple(players[10:])
    hid = tuple(range(len(home))) if home_ids is None else home_ids
    aid = tuple(range(100, 100 + len(away))) if away_ids is None else away_ids
    return motion_frame(period, ball, home, away, hid, aid)


def frames(n=80, **kw):
    return [frame(i, **kw) for i in range(n)]


class Stillness(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(ps, 'player_stillness_features is missing')

    def rows(self, f):
        return list(ps.stillness_rows(f))

    def test_constants(self):
        self.assertEqual((ps.SPEED_LAG, ps.STILL_SPEED, ps.WINDOW, ps.MIN_PLAYERS), (5, 1.0, 50, 14))
        self.assertEqual(ps.NEW_NAMES, ('still_share', 'still_support'))

    def test_first_18_columns_equal_feature_rows(self):
        f = frames()
        self.assertEqual([r[:18] for r in self.rows(f)], [tuple(b) for b in feature_rows(f)])

    def test_still_share_counts_players_below_threshold_over_both_teams(self):
        r = self.rows(frames())
        self.assertAlmostEqual(r[60][18], 14 / 20)
        self.assertEqual(r[60][19], 1.0)

    def test_speed_needs_same_id_five_rows_earlier(self):
        r = self.rows(frames())
        self.assertEqual(r[4][19], 0.0)          # no row five earlier yet
        self.assertEqual(r[4][18], 0.0)
        self.assertEqual(r[5][19], 1.0)

    def test_window_averages_only_rows_with_enough_measurable_players(self):
        f = frames(n=80)
        # rows 40-49: only 13 players carry ids -> those rows do not qualify and do not enter the average
        for i in range(40, 50):
            f[i] = replace(f[i], away_ids=tuple(range(100, 103)) + (-1,) * 7)
        r = self.rows(f)
        self.assertEqual(r[45][19], 0.0)
        self.assertAlmostEqual(r[60][18], 14 / 20)

    def test_no_qualifying_row_in_window_gives_zero(self):
        f = frames(n=80, slow=7, fast=6)                  # 13 players only
        r = self.rows(f)
        self.assertEqual((r[70][18], r[70][19]), (0.0, 0.0))

    def test_one_team_without_ids_and_duplicate_ids(self):
        f = frames(away_ids=())
        r = self.rows(f)
        self.assertEqual(r[60][19], 0.0)                  # only 10 home players can have a speed
        dup = frames(home_ids=(0, 0, 2, 3, 4, 5, 6, 7, 8, 9))
        r = self.rows(dup)
        self.assertEqual(r[60][19], 1.0)                  # 18 measurable players remain
        self.assertAlmostEqual(r[60][18], 12 / 18)        # both id-0 players excluded

    def test_window_clears_at_period_change_and_period0(self):
        f = frames(n=40) + [frame(i, period=2) for i in range(40, 80)]
        r = self.rows(f)
        self.assertEqual((r[42][18], r[42][19]), (0.0, 0.0))
        g = frames(n=40) + [frame(40, period=0)] + frames(n=40)[1:]
        r = self.rows(g)
        self.assertEqual((r[40][18], r[40][19]), (0.0, 0.0))

    def test_ball_and_tags_do_not_affect_new_columns(self):
        f = frames()
        g = [replace(x, ball_x=None, ball_y=None, home_distance=None, away_distance=None) for x in f]
        self.assertEqual([r[18:] for r in self.rows(f)], [r[18:] for r in self.rows(g)])

    def test_matrix_shape_and_finiteness(self):
        m = ps.stillness_matrix(frames())
        self.assertEqual(m.shape, (80, 20))
        self.assertEqual(m.dtype, np.float32)
        self.assertTrue(np.isfinite(m).all())


if __name__ == '__main__':
    unittest.main()
