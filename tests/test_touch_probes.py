import unittest
from gap_solver.motion import motion_frame
try:
    import touch_probes as p
except ImportError:
    p=None

class TouchProbes(unittest.TestCase):
    def test_width_scale_metres(self):
        self.assertIsNotNone(p, 'touch_probes missing')
        self.assertAlmostEqual(p.width_scale((1053,0,0,0,680,0,0,0,1),52.65,34),10)
    def test_run_counts_and_period_reset(self):
        self.assertIsNotNone(p, 'touch_probes missing')
        frames=[motion_frame(k,b,((0,0),),((20,20),)) for k,b in [(0,None),(1,(0,0)),(1,(0,0)),(1,None),(2,None),(2,(0,0))]]
        result=p.probe(frames,[(1053,0,0,0,680,0,0,0,1)]*6)
        self.assertEqual(result['ball_runs']['count'],2)
        self.assertEqual(result['ball_runs']['total_frames'],3)
        self.assertEqual(result['gaps']['count'],2)
        self.assertEqual(result['observed_near_player_share'],1)
        self.assertAlmostEqual(result['player_height_px']['q50'],18)
    def test_invalid_scale_rejected(self):
        self.assertIsNotNone(p, 'touch_probes missing')
        with self.assertRaises(ValueError): p.width_scale((0,)*9,0,0)
