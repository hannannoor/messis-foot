import unittest
import numpy as np
from gap_solver.core import Decision
from test_temporal import motion_fixture

try:
    from gap_solver.temporal_development import training_sample,endpoint_predictions,feature_cases
except ImportError:
    training_sample=endpoint_predictions=feature_cases=None


class ExternalExperiment(unittest.TestCase):
    def test_training_uses_only_unknown_baseline_known_teams_with_balanced_cases(self):
        self.assertIsNotNone(training_sample)
        x=np.zeros((30,39),dtype=np.float32);gt=np.array([0,1,3]*10);old=np.full(30,3)
        old[0]=0
        result=training_sample(x,gt,old,offset=0,stride=1)
        self.assertEqual(len(result[0]),19*4)
        self.assertAlmostEqual(result[2].sum(),1.)
        self.assertEqual(set(result[1]),{0,1})

    def test_endpoint_comparator_matches_added_count_without_reference(self):
        self.assertIsNotNone(endpoint_predictions)
        frames=motion_fixture(80)
        baseline=[Decision('X' if 16<=i<41 else 'H') for i in range(80)]
        proposal=list(baseline)
        for i in range(20,30):proposal[i]=Decision('A')
        predicted,details=endpoint_predictions(frames,baseline,proposal,max_gap_s=5.)
        self.assertEqual(sum(d.label!='X' and b.label=='X' for d,b in zip(predicted,baseline)),10)
        self.assertTrue(all(d.label=='H' for d,b in zip(predicted,baseline) if b.label=='X' and d.label!='X'))
        self.assertEqual(details['matched_added_count'],10)

    def test_reference_holes_cannot_change_features_baseline_or_mask(self):
        self.assertIsNotNone(feature_cases)
        frames=motion_fixture(80)
        a=feature_cases(frames,seed=17)
        b=feature_cases(frames,seed=17)
        for regime in ('natural','masked'):
            np.testing.assert_array_equal(a[regime]['x'],b[regime]['x'])
            np.testing.assert_array_equal(a[regime]['baseline'],b[regime]['baseline'])
        # API deliberately takes frames only: neither phases nor targets are inputs.
        import inspect
        self.assertEqual(list(inspect.signature(feature_cases).parameters),['frames','seed'])
