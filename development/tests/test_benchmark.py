import unittest
import numpy as np
from gap_solver import official_metrics

try:
    from gap_solver.benchmark import evaluate_external,evaluation_arrays
except ImportError:
    evaluate_external=evaluation_arrays=None


class ExternalMetrics(unittest.TestCase):
    def module(self):
        self.assertIsNotNone(evaluate_external,'external benchmark is missing')

    def test_halves_are_separate_spells_and_fill_does_not_cross(self):
        self.module()
        gt=np.array([0]*50+[0]*50,dtype=np.uint8)
        pred=np.array([0]*50+[3]*50,dtype=np.uint8)
        result=evaluate_external(gt,pred,[1]*50+[2]*50)
        self.assertEqual(result['metrics']['n_gt_spells'],2)
        self.assertEqual(result['metrics']['n_pred_spells'],1)
        self.assertEqual(result['coverage']['graded_frames'],100)
        self.assertEqual(result['coverage']['undecided_frames'],50)

    def test_exact_official_metric_parity_with_unknown_annotation_hole(self):
        self.module()
        gt=np.array([0]*20+[3]*5+[1]*20+[2]*20,dtype=np.uint8)
        pred=np.array([0]*25+[3]*10+[1]*10+[2]*20,dtype=np.uint8)
        a,b=evaluation_arrays(gt,pred,[1]*len(gt))
        direct=official_metrics.evaluate(a,b)
        result=evaluate_external(gt,pred,[1]*len(gt))
        self.assertEqual(result['metrics']['spell_f1_mean'],direct['spell_f1_mean'])
        self.assertEqual(result['metrics']['confusion'],direct['confusion'])
        self.assertEqual(result['coverage']['graded_frames'],60)

    def test_all_x_predictions_remain_abstentions(self):
        self.module()
        result=evaluate_external([0]*40,[3]*40,[1]*40)
        self.assertEqual(result['metrics']['n_pred_spells'],0)
        self.assertEqual(result['coverage']['undecided_fraction'],1)

    def test_invalid_or_empty_reference_is_rejected(self):
        self.module()
        for gt,pred,periods in [([4],[0],[1]),([0],[0,1],[1]),([3]*10,[0]*10,[1]*10),([0,1],[0,1],[1,0])]:
            with self.subTest(gt=gt),self.assertRaises(ValueError):
                evaluate_external(gt,pred,periods)

    def test_new_resolution_reports_correctness_and_decided_replacements_separately(self):
        from gap_solver import benchmark
        function=getattr(benchmark,'compare_external',None)
        self.assertIsNotNone(function,'new-resolution quality accounting is missing')
        result=function([0,1,2,3],[3,3,0,3],[0,0,2,1],[1,1,1,1])
        self.assertEqual(result['newly_resolved_frames'],2)
        self.assertEqual(result['newly_resolved_correct_fraction'],.5)
        self.assertEqual(result['changed_already_decided_frames'],1)
        self.assertEqual(result['newly_resolved_by_label']['H']['frames'],2)


if __name__=='__main__':
    unittest.main()
