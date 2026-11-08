import tempfile
from pathlib import Path
import unittest
from test_external import META,xml
from gap_solver.external import load_external
try:
    from gap_solver.dfl_motion import load_dfl_motion
except ImportError:
    load_dfl_motion=None


class DflMotionRegression(unittest.TestCase):
    def test_seen_provider_motion_retains_players_without_ball_and_ignores_labels(self):
        self.assertIsNotNone(load_dfl_motion)
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);meta=root/'meta.xml';raw=root/'raw.xml';meta.write_text(META)
            raw.write_text(xml([(100,1,1),(102,0,0)]));base=load_external(meta,raw)
            first=load_dfl_motion(meta,raw,base)
            raw.write_text(xml([(100,0,0),(102,1,2)]));base=load_external(meta,raw)
            second=load_dfl_motion(meta,raw,base)
            self.assertEqual(first,second)
            self.assertEqual(len(first),3)
            self.assertFalse(first[1].ball_observed)
            self.assertEqual(len(first[1].home_xy),1)
            self.assertEqual(first[1].home_ids,first[0].home_ids)
            self.assertIsNone(first[0].ball_native_observation)
