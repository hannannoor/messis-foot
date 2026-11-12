"""Synthetic parity, matched fitting and 22-column export tests; no match data."""
import importlib.util
from dataclasses import replace
import unittest
import numpy as np
from gap_solver.core import Frame
from gap_solver.motion import motion_frame
from gap_solver.selection import mask_frames, ball_mask
from memory_ablation_training import prepare_training, semantic_digest
try:
    import team_shape_training as ts
except ImportError:
    ts = None


def groups(n=60):
    frames = [motion_frame(1, (40.+i/100,34.),
                          tuple((20.+j+i/25,34.) for j in range(7)),
                          tuple((80.+j-i/50,34.) for j in range(7)),
                          tuple(range(7)), tuple(range(10,17))) for i in range(n)]
    cache = [Frame(**{k:getattr(f,k) for k in Frame.__dataclass_fields__}) for f in frames]
    return [dict(match=m, frames=list(frames), cache_frames=list(cache),
                 reference=np.resize(np.array([0,1,2,3],np.uint8),n),
                 periods=np.ones(n,np.uint8), pitch_midpoint=50.)
            for m in ('J03WOH','J03WOY','J03WPY','J03WMX')]


class Training(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(ts, 'team_shape_training is missing')

    def test_matched_rows_labels_weights_and_prefix(self):
        g=groups()
        pair=ts.prepare_pair(g)
        old=prepare_training([dict(v,frames=v['cache_frames']) for v in g])
        for name in ('matrix','target','weights','row_identity'):
            self.assertEqual(semantic_digest(getattr(pair.control,name)),semantic_digest(getattr(old,name)))
        self.assertEqual(pair.candidate.matrix.shape,(len(old.matrix),22))
        self.assertEqual(semantic_digest(pair.candidate.matrix[:,:18]),semantic_digest(old.matrix))
        for name in ('target','weights','row_identity'):
            np.testing.assert_array_equal(getattr(pair.control,name),getattr(pair.candidate,name))
        for i in range(8):
            self.assertAlmostEqual(float(pair.candidate.weights[pair.candidate.row_identity[:,0]*2+
                                  pair.candidate.row_identity[:,1]==i].sum()),1.)

    def test_mask_keeps_shape_history_and_player_tracks(self):
        pair=ts.prepare_pair(groups())
        d=pair.candidate
        late=d.row_identity[:,2]>=25
        self.assertTrue(late.any())
        np.testing.assert_array_equal(d.matrix[late,21],1.)
        for m in range(4):
            natural=(d.row_identity[:,0]==m)&(d.row_identity[:,1]==0)
            masked=(d.row_identity[:,0]==m)&(d.row_identity[:,1]==1)
            np.testing.assert_array_equal(d.matrix[natural,18:20],d.matrix[masked,18:20])

    def test_training_frame_parity_both_regimes_and_failure_stops(self):
        g=groups()[0]
        r=ts.training_frame_parity(g,0)
        self.assertEqual(r['natural'],'identical')
        self.assertEqual(r['mask30'],'identical')
        g['cache_frames'][7]=replace(g['cache_frames'][7],home_distance=123.)
        with self.assertRaisesRegex(ValueError,'parity'):
            ts.training_frame_parity(g,0)

    def test_failed_training_parity_exposes_only_aggregate_mismatch_receipt(self):
        g=groups()[0]
        g['cache_frames'][7]=replace(g['cache_frames'][7],home_distance=123.)
        with self.assertRaises(ts.TrainingFrameMismatch) as caught:
            ts.training_frame_parity(g,0)
        receipt=caught.exception.receipt
        self.assertGreater(receipt['mismatched_rows'],0)
        self.assertEqual(receipt['rows'],60)
        self.assertNotIn('indices',receipt)

    def test_training_reference_and_period_parity(self):
        g=groups()[0]
        g['cache_reference']=g['reference'].copy()
        g['cache_reference'][0]=1
        with self.assertRaisesRegex(ValueError,'reference'):
            ts.training_frame_parity(g,0)
        g=groups()[0]
        g['cache_periods']=g['periods'].copy()
        g['cache_periods'][0]=2
        with self.assertRaisesRegex(ValueError,'period'):
            ts.training_frame_parity(g,0)

    def test_expected_rows_guard(self):
        pair=ts.prepare_pair(groups())
        with self.assertRaises(ValueError):
            ts.require_rows(pair)
        ts.require_rows(pair,len(pair.control.matrix))


@unittest.skipUnless(importlib.util.find_spec('sklearn'), 'pinned training interpreter required')
class Fitting(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(ts, 'team_shape_training is missing')

    def problem(self,new=True):
        from memory_ablation_training import TrainingData
        rng=np.random.RandomState(39)
        x=rng.normal(size=(3000,22)).astype(np.float32)
        y=(x[:,18 if new else 2]>0).astype(np.uint8)
        y[x[:,19 if new else 3]>.8]=2
        if not new:x[:,18:]=0
        ids=np.column_stack((np.zeros(3000),np.zeros(3000),np.arange(3000))).astype(np.int64)
        w=np.full(3000,1/3000)
        return TrainingData(x[:,:18],y,w,ids,()),ts.ResearchTrainingData(x,y,w,ids,())

    def test_two_fits_order_and_exporter_all_rows(self):
        c,k=self.problem()
        claims=[]
        out=ts.fit_research(c,k,claims.append,expected_control_sha=None)
        self.assertEqual(claims,['control','candidate'])
        self.assertTrue(out['candidate']['appended_columns_used'])
        self.assertLessEqual(out['candidate']['parity_max_abs_diff'],1e-12)
        self.assertEqual(len(out['candidate']['model']['feature_names']),22)

    def test_control_mismatch_stops_before_second_fit(self):
        claims=[]
        with self.assertRaises(ts.ControlMismatch):
            ts.fit_research(*self.problem(),claims.append,expected_control_sha='0'*64)
        self.assertEqual(claims,['control'])

    def test_unused_representation_stop(self):
        with self.assertRaisesRegex(ts.UnusedRepresentation,'representation unused'):
            ts.fit_research(*self.problem(False),lambda x:None,expected_control_sha=None)

    def test_threshold_ties_and_float32_export(self):
        model=dict(feature_names=list(ts.RESEARCH_FEATURE_NAMES),children_left=[1,-1,-1],
                   children_right=[2,-1,-1],feature=[21,-2,-2],threshold=[.25,-2.,-2.],
                   probabilities=[[1/3]*3,[1.,0.,0.],[0.,1.,0.]])
        x=np.zeros((3,22),np.float32)
        x[:,21]=[.25,np.nextafter(np.float32(.25),np.float32(1.)),0.]
        np.testing.assert_array_equal(ts.predict_supports_research(x,model).argmax(axis=1),[0,1,0])
        np.testing.assert_array_equal(ts.ResearchTree(model).predict(x[0]),[1.,0.,0.])


if __name__=='__main__':unittest.main()
