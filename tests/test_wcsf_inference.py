"""Frozen three-method inference uses geometry and original method semantics."""
from dataclasses import replace
from pathlib import Path
import tempfile
import unittest
import numpy as np
from wcsf_fixtures import rows,source_paths
from wcsf_source import ingest
from wcsf_geometry import qualify,canonical_input
from gap_solver.motion import motion_frame
from gap_solver.tactical import PortableTree,feature_rows
from gap_solver.tactical_model import FROZEN_MODEL
from gap_solver.soft_sequence import sequence_usable
from gap_solver.materialization_control import materialize_abstentions
from cadence_baselines import baseline_predictions
from ball_gap_policy import decode_ball_gap


class InferenceTests(unittest.TestCase):
    def setUp(self):
        try:import wcsf_audit
        except ImportError:self.fail('Missing fixed reference-free inference')
        self.api=wcsf_audit

    def frames(self):
        out=[]
        for period in (1,2):
            for i in range(160):
                ball=(5.,5.) if i<70 else (25.,5.)
                out.append(motion_frame(period,ball if i%31 else None,((5.,5.),(8.,9.),(10.,2.)),((25.,5.),(28.,9.),(30.,2.)),(1,2,3),(4,5,6)))
        return out

    def test_control_matches_released_functions(self):
        frames=self.frames();actual=self.api.infer_fixed(frames)
        tree=PortableTree(FROZEN_MODEL['model']);supports=[tree.predict(r) for r in feature_rows(frames)]
        periods=[f.period for f in frames]
        labels,_=decode_ball_gap(supports,periods,[bool(sequence_usable(f)) for f in frames],[bool(f.ball_observed) for f in frames])
        expected=materialize_abstentions(labels,periods)
        np.testing.assert_array_equal(actual['w0-c32-neutral-missing'],['HADX'.index(s) for s in expected])

    def test_only_two_w50_comparators(self):
        frames=self.frames();got=self.api.infer_fixed(frames)
        self.assertEqual(set(got),{'w0-c32-neutral-missing','official-convention-w50','matched-input-w50'})
        for mode in ('official-convention','matched-input'):
            want=baseline_predictions(frames,50,mode)['final']
            np.testing.assert_array_equal(got[mode+'-w50'],['HADX'.index(s) for s in want])

    def test_reference_flip_leaves_all_three_predictions_identical(self):
        with tempfile.TemporaryDirectory() as tmp:
            data=rows();flipped=[dict(r,AliveFlag=0,PossessionFlag=999) for r in data];result=[]
            for name,items in [('a',data),('b',flipped)]:
                paths=source_paths(Path(tmp)/name,items,items);ingest(paths)
                frames=canonical_input(paths.geometry_db,qualify(paths.geometry_db)).frames
                result.append(self.api.infer_fixed(frames))
            for method in result[0]:np.testing.assert_array_equal(result[0][method],result[1][method])

    def test_unsupported_and_period_barrier_behaviour(self):
        frames=[motion_frame(0,None,(),()),motion_frame(1,None,(),()),motion_frame(2,None,(),())]
        got=self.api.infer_fixed(frames)
        for values in got.values():self.assertEqual(values[0],3);self.assertTrue(np.isin(values,[0,1,2,3]).all())
        bad=[replace(self.frames()[0],dead_evidence=True)]
        with self.assertRaises(ValueError):self.api.infer_fixed(bad)
        with self.assertRaises(TypeError):self.api.infer_fixed(frames,np.array([0,1,2]))


if __name__=='__main__':unittest.main()
