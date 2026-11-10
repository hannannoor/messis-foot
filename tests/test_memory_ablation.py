import ast
from dataclasses import replace
from pathlib import Path
import unittest
import numpy as np

from gap_solver.motion import motion_frame
from gap_solver.tactical import FEATURE_NAMES,PortableTree
from gap_solver.tactical_model import FROZEN_MODEL
import release_runtime
try:
    import memory_ablation as ablation
except ImportError:
    ablation=None


def memory_tree():
    return dict(feature_names=list(FEATURE_NAMES),children_left=[1,-1,-1],children_right=[2,-1,-1],
        feature=[15,-2,-2],threshold=[.5,-2.,-2.],probabilities=[[.5,.5,0.],[0.,1.,0.],[1.,0.,0.]])


class MemoryAblation(unittest.TestCase):
    def setUp(self):self.assertIsNotNone(ablation,'Reference-free memory ablation is missing')

    def test_literal_three_column_transform_preserves_control_and_source(self):
        row=tuple(range(18));matrix=np.asarray([row,row],dtype=np.float32);before=matrix.tobytes()
        self.assertEqual(ablation.transform_row(row,'control'),row)
        self.assertEqual(ablation.transform_row(row,'memory-ablated'),tuple(range(15))+(0.,0.,10.))
        actual=ablation.transform_matrix(matrix,'memory-ablated')
        self.assertEqual(actual.dtype,np.float32);self.assertEqual(actual[:,:15].tobytes(),matrix[:,:15].tobytes())
        np.testing.assert_array_equal(actual[:,15:],[[0,0,10],[0,0,10]])
        np.testing.assert_array_equal(ablation.transform_matrix(matrix,'control'),matrix)
        self.assertEqual(matrix.tobytes(),before)
        self.assertEqual(tuple(actual[0]),ablation.transform_row(row,'memory-ablated'))

    def test_invalid_modes_dimensions_nonfinite_and_float32_overflow_fail(self):
        for row,mode in (([0.]*17,'control'),([0.]*18,'unknown'),([float('nan')]*18,'control')):
            with self.assertRaises(ValueError):ablation.transform_row(row,mode)
        for matrix in (np.zeros(18),np.zeros((2,17)),np.full((1,18),np.inf),np.full((1,18),1e100)):
            with self.assertRaises(ValueError):ablation.transform_matrix(matrix,'memory-ablated')

    def frames(self):
        home=[(21.,20.),(22.,20.),(23.,20.)];away=[(80.,40.),(81.,40.),(82.,40.)]
        frames=[motion_frame(1,(21.+i*.02,20.),home,away) for i in range(25)]
        frames[10]=replace(frames[10],geometry_valid=False)
        return frames+[motion_frame(0,None,home,away)]+[motion_frame(2,None,home,away) for _ in range(6)]

    def test_control_matches_release_on_barriers_periods_and_unsupported_carry(self):
        frames=self.frames();inputs=ablation.prepare_inputs(frames)
        result=ablation.infer_prepared(inputs,FROZEN_MODEL['model'],'control');released=release_runtime.predict_selected(frames)
        self.assertEqual(result.latent,released.latent);self.assertEqual(result.final,released.labels)
        self.assertEqual(result.latent[-6:],tuple('XXXXXX'));self.assertEqual(result.final[-6:],tuple('DDDDDD'))
        self.assertEqual(result.final[25],'X')
        with self.assertRaises(ValueError):inputs.matrix[0,0]=17
        for key,value in (('dead_evidence',True),('restart_hint',True),('tag_team','H'),('dead_source','annotation')):
            with self.assertRaises(ValueError):ablation.prepare_inputs([replace(frames[0],**{key:value})])

    def test_candidate_transform_reaches_model_and_does_not_mutate_control(self):
        matrix=np.zeros((6,18),dtype=np.float32);matrix[:,15]=1;matrix[:,17]=.4
        inputs=ablation.PreparedInputs(matrix,np.ones(6,dtype=np.uint8),np.ones(6,dtype=bool),np.ones(6,dtype=bool))
        control=ablation.infer_prepared(inputs,memory_tree(),'control')
        candidate=ablation.infer_prepared(inputs,memory_tree(),'memory-ablated')
        self.assertEqual(control.final,tuple('HHHHHH'));self.assertEqual(candidate.final,tuple('AAAAAA'))
        self.assertEqual(ablation.infer_prepared(inputs,memory_tree(),'control').final,control.final)
        np.testing.assert_array_equal(inputs.matrix[:,15],np.ones(6))

    def test_vectorized_supports_equal_portable_float32_threshold_semantics(self):
        inputs=ablation.prepare_inputs(self.frames());actual=ablation.predict_supports(inputs.matrix,FROZEN_MODEL['model'])
        expected=np.asarray([PortableTree(FROZEN_MODEL['model']).predict(row) for row in inputs.matrix])
        np.testing.assert_array_equal(actual,expected)
        row=np.zeros((1,18));row[0,15]=.5+1e-10
        np.testing.assert_array_equal(ablation.predict_supports(row,memory_tree()),[[0,1,0]])

    def test_prepare_is_reference_free_and_new_source_has_python39_grammar(self):
        import inspect
        self.assertEqual(list(inspect.signature(ablation.prepare_inputs).parameters),['frames'])
        a=ablation.prepare_inputs(self.frames());b=ablation.prepare_inputs(self.frames())
        np.testing.assert_array_equal(a.matrix,b.matrix)
        ast.parse((Path(__file__).resolve().parents[1]/'memory_ablation.py').read_text(encoding='utf-8'),feature_version=(3,9))


if __name__=='__main__':unittest.main()
