"""Live/dead sequence experiment: player-only liveness features and ordered windows. Synthetic only."""
from dataclasses import replace
from math import fsum, hypot, sqrt
import unittest

import numpy as np

from gap_solver.motion import motion_frame

import live_dead_features as lf

PITCH = (105., 68.)


def frame(i, speeds=None, period=1, home_ids=None, away_ids=None, ball=(50., 34.), valid=True, n=22):
    """Player j moves along x at speeds[j] m/s (default 0.5); 11/11 split; 25 Hz."""
    speeds = [.5] * n if speeds is None else speeds
    players = [(10. + 3 * j + v * i / 25, 5. + 2 * j) for j, v in enumerate(speeds)]
    half = len(players) // 2
    home, away = tuple(players[:half]), tuple(players[half:])
    hid = tuple(range(len(home))) if home_ids is None else home_ids
    aid = tuple(range(100, 100 + len(away))) if away_ids is None else away_ids
    return motion_frame(period, ball, home, away, hid, aid, geometry_valid=valid)


def frames(count=120, **kw):
    return [frame(i, **kw) for i in range(count)]


class FrameVectorTest(unittest.TestCase):
    def test_team_swap_invariant(self):
        fs = frames(40, speeds=[.2 * j for j in range(22)])
        swapped = [replace(f, home_xy=f.away_xy, away_xy=f.home_xy, home_ids=f.away_ids, away_ids=f.home_ids)
                   for f in fs]
        self.assertEqual(lf.frame_vectors(fs, PITCH).tobytes(), lf.frame_vectors(swapped, PITCH).tobytes())

    def test_ignores_ball_and_status(self):
        fs = frames(140)
        other = [replace(f, ball_x=None if i % 3 else 1., ball_y=None if i % 3 else 2.,
                         home_distance=None, away_distance=None, ball_provenance='missing')
                 for i, f in enumerate(fs)]
        a, b = lf.liveness_inputs(fs, PITCH), lf.liveness_inputs(other, PITCH)
        for name in ('instant', 'temporal', 'eligible'):
            self.assertEqual(getattr(a, name).tobytes(), getattr(b, name).tobytes())

    def test_duplicate_and_null_ids_excluded(self):
        home_ids = (0, 1, 2, 3, 4, 5, 6, 7, 8, 3, None)       # id 3 twice (both out) and one None
        v = lf.frame_vectors(frames(20, home_ids=home_ids), PITCH)
        self.assertAlmostEqual(float(v[10, 0]), 19 / 22, places=6)
        self.assertAlmostEqual(float(v[10, 1]), 19 / 22, places=6)

    def test_speed_outlier_rejected(self):
        fs = frames(60)
        fs = [f if i < 30 else replace(f, home_xy=((f.home_xy[0][0] + 3., f.home_xy[0][1]),) + f.home_xy[1:])
              for i, f in enumerate(fs)]
        v = lf.frame_vectors(fs, PITCH)
        self.assertAlmostEqual(float(v[30, 1]), 21 / 22, places=6)
        self.assertLess(float(v[30, 4]), 1.)
        self.assertAlmostEqual(float(v[35, 1]), 1., places=6)

    def test_speed_requires_six_valid_rows(self):
        fs = [frame(i, valid=(i != 27)) for i in range(60)]
        v = lf.frame_vectors(fs, PITCH)
        self.assertEqual(float(v[27, 9]), 0.)
        self.assertEqual(float(v[30, 9]), 0.)
        self.assertEqual(float(v[32, 9]), 0.)
        self.assertEqual(float(v[33, 9]), 1.)
        self.assertTrue(np.all(v[27] == 0))

    def test_sparse_support_zeroes_group(self):
        v = lf.frame_vectors(frames(20, n=9), PITCH)
        self.assertTrue(np.all(v[10] == 0))
        full = lf.frame_vectors(frames(20), PITCH)
        self.assertEqual(float(full[0, 8]), 1.)
        self.assertTrue(np.all(full[0, 1:7] == 0) and full[0, 9] == 0)
        self.assertGreater(float(full[0, 0]), 0)

    def test_quantiles_fractions_rms(self):
        speeds = [.5 * j + .1 for j in range(22)]   # off the 1 and 3 m/s boundaries
        fs = frames(20, speeds=speeds)
        v = lf.frame_vectors(fs, PITCH)
        got = np.asarray(sorted(speeds), dtype=np.float64)
        q = np.quantile(got, (.25, .5, .75), method='linear') / 12
        np.testing.assert_allclose(v[10, 2:5], q.astype(np.float32), rtol=0, atol=2e-7)
        self.assertAlmostEqual(float(v[10, 5]), 2 / 22, places=6)
        self.assertAlmostEqual(float(v[10, 6]), 16 / 22, places=6)
        pts = fs[10].home_xy + fs[10].away_xy
        cx, cy = fsum(p[0] for p in pts) / 22, fsum(p[1] for p in pts) / 22
        rms = sqrt(fsum((x - cx) ** 2 + (y - cy) ** 2 for x, y in pts) / 22) / hypot(*PITCH)
        self.assertAlmostEqual(float(v[10, 7]), rms, places=6)


class WindowTest(unittest.TestCase):
    def test_shape_and_offsets(self):
        self.assertEqual(lf.OFFSETS, tuple(range(-50, 51, 5)))
        self.assertEqual((lf.FRAME_COLUMNS, lf.WINDOW_COLUMNS), (10, 210))

    def test_window_order_and_offsets(self):
        fs = frames(200, speeds=[.1 * (j + 1) + .01 * j for j in range(22)])
        fs = [replace(f, home_xy=tuple((x + (i % 7) * .01, y) for x, y in f.home_xy)) for i, f in enumerate(fs)]
        x = lf.liveness_inputs(fs, PITCH)
        t = 100
        for j, k in enumerate(lf.OFFSETS):
            self.assertEqual(x.temporal[t, 10 * j:10 * j + 10].tobytes(), x.instant[t + k].tobytes())

    def test_window_barriers_never_pad(self):
        fs = [frame(i, period=1 if i < 100 else 2, valid=(i != 150)) for i in range(220)]
        x = lf.liveness_inputs(fs, PITCH)
        w = x.temporal.reshape(len(fs), 21, 10)
        idx = {k: j for j, k in enumerate(lf.OFFSETS)}
        self.assertTrue(np.all(w[90, idx[10]:] == 0))           # crosses the period change
        self.assertTrue(np.any(w[90, idx[5]] != 0))
        self.assertTrue(np.all(w[20, :idx[-20]] == 0))          # before the recording start
        self.assertTrue(np.all(w[140, idx[10]:] == 0))          # reaches/passes the invalid row
        self.assertTrue(np.all(w[215, idx[5]:] == 0))           # after the recording end
        self.assertTrue(np.all(w[160, :idx[-10] + 1] == 0))     # behind the invalid row

    def test_eligibility_needs_five_each_side(self):
        x = lf.liveness_inputs(frames(200), PITCH)
        self.assertFalse(x.eligible[25])                        # rows 20,15,10,5 supported: four
        self.assertTrue(x.eligible[30])
        self.assertFalse(x.eligible[199 - 20])                  # four after
        self.assertTrue(x.eligible[199 - 25])

    def test_period_zero_never_eligible(self):
        fs = frames(200, period=0)
        x = lf.liveness_inputs(fs, PITCH)
        self.assertFalse(x.eligible.any())
        self.assertTrue(np.all(x.instant == 0))

    def test_instant_is_window_centre(self):
        x = lf.liveness_inputs(frames(150), PITCH)
        self.assertEqual(x.instant.tobytes(), np.ascontiguousarray(x.temporal[:, 100:110]).tobytes())
        self.assertEqual((x.instant.dtype, x.temporal.dtype), (np.float32, np.float32))


if __name__ == '__main__':
    unittest.main()
