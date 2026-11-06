import unittest
from gap_solver.core import Decision
from gap_solver.temporal import TemporalPolicy,mask_motion_frames
from test_temporal import motion_fixture
try:
    from gap_solver.temporal_diagnostics import eligibility_diagnostics
except ImportError:
    eligibility_diagnostics=None


class TemporalEligibility(unittest.TestCase):
    def test_reasons_partition_unknown_rows_without_using_reference(self):
        self.assertIsNotNone(eligibility_diagnostics)
        frames=mask_motion_frames(motion_fixture(),[16<=i<41 for i in range(80)])
        base=[Decision('X' if 16<=i<41 else 'H') for i in range(80)]
        short=eligibility_diagnostics(frames,base,TemporalPolicy(max_gap_s=2.))
        self.assertEqual(short['baseline_unknown_rows'],25)
        self.assertEqual(short['reasons']['eligible_before_confidence'],25)
        long=eligibility_diagnostics(frames,base,TemporalPolicy(max_gap_s=.5))
        self.assertEqual(long['reasons']['anchor_span_exceeds_cap'],25)
        self.assertEqual(sum(long['reasons'].values()),25)
