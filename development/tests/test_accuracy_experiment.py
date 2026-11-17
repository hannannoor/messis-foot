import unittest
import numpy as np
from gap_solver.motion import motion_frame
from gap_solver.candidate_cli import predict_four,ROOT
from gap_solver.temporal_protocol import load_temporal_frozen
from gap_solver.tactical import PortableTree,feature_rows
from gap_solver.temporal import PortableBoosted,motion_feature_rows
from gap_solver.tactical_model import FROZEN_MODEL
try:
    from accuracy_experiment import score_heads,four_from_scores,aggregate_metrics
except ImportError:
    score_heads=four_from_scores=aggregate_metrics=None


class AccuracyExperiment(unittest.TestCase):
    def setUp(self):self.assertIsNotNone(score_heads,'external score-only experiment missing')

    def test_vectorized_heads_and_four_controls_match_frozen_runtime(self):
        artifact,_=load_temporal_frozen(ROOT/'benchmark/skillcorner/frozen',ROOT)
        frames=[motion_frame(1,(10+i*.01,20),[(10,20),(30,30),(50,40)],[(70,20),(80,30),(90,40)]) for i in range(25)]
        frames += [motion_frame(1,None,(),(),geometry_valid=False)]*30
        frames += [motion_frame(2,(70,20),[(10,20),(30,30),(50,40)],[(70,20),(80,30),(90,40)])]*25
        p,z=score_heads(frames,artifact)
        tree=PortableTree(FROZEN_MODEL['model']);boost=PortableBoosted(artifact['model'])
        np.testing.assert_allclose(p,[tree.predict(r) for r in feature_rows(frames)],atol=0,rtol=0)
        np.testing.assert_allclose(z,[boost.symmetric_score(r) for r in motion_feature_rows(frames)],atol=1e-12,rtol=0)
        self.assertEqual(four_from_scores(frames,p,z,artifact),predict_four(frames,artifact))

    def test_metrics_keep_unknown_reference_unknown_and_count_corrections(self):
        gt=np.array([0,0,3,1,1,2]);old=np.array([0,1,0,1,0,2]);new=np.array([0,0,1,1,1,2]);periods=np.ones(6,dtype=np.uint8)
        report=aggregate_metrics(gt,new,periods,old)
        self.assertEqual(report['changes']['already_decided_corrections'],2)
        self.assertEqual(report['changes']['already_decided_regressions'],0)
        self.assertEqual(report['unmeasured_emitted_by_label'],{'H':0,'A':1,'D':0})
        self.assertAlmostEqual(report['metrics']['accuracy'],1.)
        self.assertNotIn('transitions',report['metrics'])

    def test_overlap_counts_identify_literal_false_split_and_merge(self):
        periods=np.ones(6,dtype=np.uint8)
        split=np.array([0,0,1,1,0,0]);continuous=np.zeros(6,dtype=np.uint8)
        report=aggregate_metrics(split,continuous,periods,split)
        self.assertEqual(report['overlap_diagnostics']['predicted_spells_merging'],1)
        self.assertEqual(report['overlap_diagnostics']['reference_spells_split'],0)
        report=aggregate_metrics(continuous,split,periods,continuous)
        self.assertEqual(report['overlap_diagnostics']['reference_spells_split'],1)
        self.assertEqual(report['overlap_diagnostics']['predicted_spells_merging'],0)

if __name__=='__main__':unittest.main()
