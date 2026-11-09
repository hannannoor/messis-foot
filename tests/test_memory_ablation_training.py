import hashlib
import importlib.util
import json
import subprocess
import sys
import unittest
from unittest.mock import patch
import numpy as np
from gap_solver.motion import motion_frame
from gap_solver.selection import export_tree
try:
    import memory_ablation_training as training
except ImportError:
    training=None

SKLEARN=importlib.util.find_spec('sklearn') is not None


def model_sha(model):return hashlib.sha256(json.dumps(model,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


class MemoryTraining(unittest.TestCase):
    def setUp(self):self.assertIsNotNone(training,'Matched training preparation is missing')

    def groups(self):
        home=[(10.,10.),(11.,10.),(12.,10.)];away=[(70.,40.),(71.,40.),(72.,40.)]
        frames=[motion_frame(1,(10.+i*.001,10.),home,away) for i in range(11)]
        ref=np.asarray([0,0,0,2,0,3,0,0,0,0,1],dtype=np.uint8)
        return [dict(match=m,frames=frames,reference=ref.copy(),periods=np.ones(11,dtype=np.uint8))
            for m in ('J03WOH','J03WOY','J03WPY','J03WMX')]

    def test_literal_order_indices_weights_and_full_history_before_take(self):
        groups=self.groups();data=training.prepare_training(groups)
        expected=np.asarray([[g,regime,i] for g in range(4) for regime in range(2) for i in (0,10)])
        np.testing.assert_array_equal(data.row_identity,expected)
        np.testing.assert_array_equal(data.target,[0,1]*8)
        np.testing.assert_array_equal(data.weights,[.5]*16)
        self.assertEqual(data.matrix.dtype,np.float32);self.assertEqual(data.weights.dtype,np.float64)
        self.assertEqual(data.matrix[1,15],1.) # Row10 sees all11 source rows, not just the sampled pair.
        self.assertEqual([(v['match'],v['regime'],v['rows']) for v in data.group_counts],
            [(m,r,2) for m in ('J03WOH','J03WOY','J03WPY','J03WMX') for r in ('natural','mask30')])
        self.assertEqual(data.matrix[7,0],0.) # Seed1730 masks original row10, unlike seed1729.
        with self.assertRaises(ValueError):data.matrix[0,0]=99

    def test_reference_changes_only_selection_targets_not_generated_features(self):
        groups=self.groups();before=training.prepare_training(groups);groups[0]['reference'][5]=2
        after=training.prepare_training(groups)
        np.testing.assert_array_equal(after.row_identity[:3],[[0,0,0],[0,0,5],[0,0,10]])
        np.testing.assert_array_equal(after.target[:3],[0,2,1])
        np.testing.assert_array_equal(before.matrix[:2],after.matrix[[0,2]])
        with self.assertRaises(ValueError):training.prepare_training(list(reversed(groups)))
        groups[0]['periods'][0]=2
        with self.assertRaises(ValueError):training.prepare_training(groups)

    def test_historical_training_mask_durations_are_not_evaluation_mask(self):
        groups=self.groups()
        for group in groups:
            group['frames']=(group['frames']*23)[:250]
            group['periods']=np.ones(250,dtype=np.uint8);group['reference']=np.zeros(250,dtype=np.uint8)
        data=training.prepare_training(groups)
        at=(data.row_identity[:,0]==0)&(data.row_identity[:,1]==1)
        hidden=data.row_identity[at,2][data.matrix[at,0]==0].tolist()
        self.assertEqual(hidden,[25,30,35,145,150,155,160,165,170,175,180,185,190,245])

    def test_import_does_not_load_estimator_or_training_script(self):
        result=subprocess.run([sys.executable,'-c',
            "import sys,memory_ablation,memory_ablation_training;assert 'sklearn' not in sys.modules;assert 'select_external_improvement' not in sys.modules"],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)

    @unittest.skipUnless(SKLEARN,'Run explicitly in the pinned Python3.12 training environment')
    def test_synthetic_pair_has_two_callbacks_fixed_parameters_and_export_parity(self):
        from sklearn.tree import DecisionTreeClassifier
        matrix=np.zeros((900,18),dtype=np.float32);matrix[:300,15]=1;matrix[300:600,16]=1;matrix[:,17]=np.repeat([0.,1.,10.],300)
        target=np.repeat(np.arange(3,dtype=np.uint8),300);weights=np.full(900,1/900,dtype=np.float64)
        oracle=DecisionTreeClassifier(max_depth=4,min_samples_leaf=125,random_state=1729).fit(matrix,target,sample_weight=weights)
        expected=model_sha(export_tree(oracle));events=[];original_fit=DecisionTreeClassifier.fit
        def tracked(classifier,x,y,**kwargs):
            events.append(('fit',classifier.max_depth,classifier.min_samples_leaf,classifier.random_state))
            return original_fit(classifier,x,y,**kwargs)
        data=training.TrainingData(matrix,target,weights,np.column_stack([np.zeros(900),np.zeros(900),np.arange(900)]).astype(np.int64),())
        with patch.object(DecisionTreeClassifier,'fit',new=tracked):
            result=training.fit_pair(data,lambda mode:events.append(('entry',mode)),expected_control_sha=expected)
        self.assertEqual(events,[('entry','control'),('fit',4,125,1729),('entry','memory-ablated'),('fit',4,125,1729)])
        self.assertEqual(result['control']['model_sha256'],expected)
        self.assertTrue(result['control']['portable_all_rows_match']);self.assertTrue(result['memory-ablated']['portable_all_rows_match'])
        self.assertFalse(set(result['memory-ablated']['model']['feature'])&{15,16,17})
        np.testing.assert_array_equal(data.matrix,matrix)

    @unittest.skipUnless(SKLEARN,'Run explicitly in the pinned Python3.12 training environment')
    def test_control_mismatch_stops_before_candidate_estimator_entry(self):
        matrix=np.zeros((900,18),dtype=np.float32);target=np.repeat(np.arange(3,dtype=np.uint8),300)
        data=training.TrainingData(matrix,target,np.full(900,1/900),np.column_stack([np.zeros(900),np.zeros(900),np.arange(900)]).astype(np.int64),())
        events=[]
        with self.assertRaises(training.ControlMismatch) as caught:
            training.fit_pair(data,events.append,expected_control_sha='0'*64)
        self.assertEqual(events,['control']);self.assertEqual(len(caught.exception.model['children_left']),1)


if __name__=='__main__':unittest.main()
