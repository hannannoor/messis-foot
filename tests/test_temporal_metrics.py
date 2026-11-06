from types import SimpleNamespace
import unittest
import numpy as np
from gap_solver.core import Frame

try:
    from gap_solver.temporal_metrics import score_temporal,compare_temporal,native_gap_statistics
except ImportError:
    score_temporal=compare_temporal=native_gap_statistics=None


def gap_fixture():
    frames=[Frame(ball_x=20,ball_y=20,home_distance=.5,away_distance=10) for _ in range(80)]
    for i in range(16,41):frames[i]=Frame()
    reference=np.zeros(80,dtype=np.uint8);reference[24:34]=1
    before=np.zeros(80,dtype=np.uint8);before[16:41]=3
    after=before.copy();after[24:34]=1
    return frames,reference,before,after


class TemporalMetricContract(unittest.TestCase):
    def ready(self):self.assertIsNotNone(score_temporal,'independent temporal metrics are missing')

    def test_unknown_hole_does_not_merge_same_team_spells(self):
        self.ready()
        report=score_temporal([0,3,0],[0,3,0],[1,1,1])
        self.assertEqual(report['metrics']['n_gt_spells'],2)
        self.assertEqual(report['coverage']['graded_frames'],2)
        self.assertEqual(report['metrics']['spell_f1_mean'],1.)

    def test_fractional_or_wrapped_codes_are_rejected_before_uint8_conversion(self):
        for gt,pred in (([.5],[0]),([0],[256]),([0],[-256])):
            with self.assertRaises(ValueError):score_temporal(gt,pred,[1])

    def test_structural_unknown_period_is_preserved_as_a_scoring_hole(self):
        self.ready()
        report=score_temporal([0,3,0,3,1],[0,3,0,3,1],[1,0,1,0,2])
        self.assertEqual(report['metrics']['n_gt_spells'],3)
        self.assertEqual(report['scope']['canonical_frames'],5)
        self.assertEqual(report['scope']['structural_period_frames'],3)

    def test_hidden_opponent_is_recovered_without_equal_endpoints_erasing_it(self):
        self.ready();frames,gt,before,after=gap_fixture()
        report=compare_temporal(gt,before,after,[1]*80,frames)
        hidden=report['hidden_opponents']
        self.assertEqual(hidden['reference_short_spells'],1)
        self.assertEqual(hidden['baseline_hits'],0)
        self.assertEqual(hidden['selected_hits'],1)
        self.assertEqual(report['gap_strata']['per_label']['A']['frames'],10)
        self.assertEqual(report['gap_strata']['per_label']['A']['correct'],10)
        self.assertEqual(report['gap_strata']['per_label']['A']['gaps'],1)
        self.assertGreater(report['selected']['metrics']['spell_f1_mean'],report['baseline']['metrics']['spell_f1_mean'])

    def test_invented_opposing_spell_is_counted(self):
        self.ready();frames,gt,before,after=gap_fixture();gt[:]=0
        hidden=compare_temporal(gt,before,after,[1]*80,frames)['hidden_opponents']
        self.assertEqual(hidden['reference_short_spells'],0)
        self.assertEqual(hidden['selected_false_opposing_spells'],1)

    def test_new_assignments_outside_reference_are_visible_but_not_called_correct(self):
        self.ready()
        frames=[Frame() for _ in range(20)]
        report=compare_temporal([3]*10+[0]*10,[3]*20,[0]*20,[1]*20,frames)
        self.assertEqual(report['unmeasured_new_ha_outside_reference'],10)
        self.assertEqual(report['change']['newly_resolved_frames'],10)
        self.assertEqual(report['selected']['coverage']['graded_frames'],10)

    def test_native_missing_intervals_are_not_inflated_by_resampling(self):
        self.ready()
        data=SimpleNamespace(native_ball_available=np.array([True,False,False,True]),
                             native_periods=np.ones(4,dtype=np.uint8),notes={'native_fps':10})
        stats=native_gap_statistics(data)
        self.assertEqual(stats['missing_native_frames'],2)
        self.assertEqual(stats['missing_native_intervals'],1)
        self.assertAlmostEqual(stats['missing_native_seconds'],.2)
