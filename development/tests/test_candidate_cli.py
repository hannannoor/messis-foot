import csv
import json
import os
from pathlib import Path
import tempfile
import unittest
from test_input_contract import fixture
from gap_solver.motion import motion_frame
from gap_solver.temporal_protocol import load_temporal_frozen
try:
    from gap_solver.candidate_cli import run_source,protect_output,OUTPUT_FILES,predict_four,ROOT
except ImportError:
    run_source=protect_output=None
    OUTPUT_FILES=()


class CandidateCommand(unittest.TestCase):
    def setUp(self):self.assertIsNotNone(run_source,'experimental candidate entry point missing')

    def test_four_policies_original_indices_separate_uncertainty_and_reproducibility(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);inputs=fixture(root)
            a=run_source(*inputs,root/'a',scope='synthetic')
            b=run_source(*inputs,root/'b',scope='synthetic')
            self.assertEqual(a['csv_sha256'],b['csv_sha256'])
            self.assertEqual(set(a['policies']),{'incumbent','carry','agreement','agreement-plus-carry'})
            self.assertTrue(a['experimental']);self.assertFalse(a['accuracy_measured'])
            for name in ['submission','incumbent','carry','agreement','agreement-plus-carry']:
                with (root/'a'/f'{name}.csv').open(newline='') as f:rows=list(csv.DictReader(f))
                self.assertEqual([r['frame'] for r in rows],['0','1','2'])
                self.assertTrue(all(r['label'] in 'HAD' for r in rows) if name in ['submission','carry','agreement-plus-carry'] else True)
            with (root/'a'/'uncertainty.csv').open(newline='') as f:rows=list(csv.DictReader(f))
            self.assertEqual(len(rows),3)
            self.assertIn('latent_label',rows[0]);self.assertIn('materialized',rows[0])
            self.assertNotIn('ball_x',rows[0])
            self.assertEqual(a['published_dead_interval_applied'],False)

    def test_bad_contract_and_nonowned_outputs_do_not_write(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);inputs=fixture(root);out=root/'output';out.mkdir();(out/'user.txt').write_text('keep')
            with self.assertRaises(ValueError):run_source(*inputs,out,scope='synthetic')
            self.assertEqual((out/'user.txt').read_text(),'keep')
            inputs[1].write_text('bad')
            with self.assertRaises(ValueError):run_source(*inputs,root/'new',scope='synthetic')
            self.assertFalse((root/'new').exists())
            with self.assertRaises(ValueError):run_source(*inputs,root/'wrong',scope='broadcast')

    def test_hardlink_input_alias_cannot_be_overwritten(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);inputs=fixture(root);out=root/'alias';out.mkdir();before=inputs[0].read_bytes()
            os.link(inputs[0],out/'submission.csv')
            with self.assertRaises(ValueError):protect_output(out,inputs)
            self.assertEqual(inputs[0].read_bytes(),before)

    def test_skipped_temporal_geometry_cannot_become_latent_home_or_away_agreement(self):
        artifact,_=load_temporal_frozen(ROOT/'benchmark/skillcorner/frozen',ROOT)
        for home_control in (True,False):
            home=[(10,20),(20,30),(30,40)];away=[(70,20),(80,30),(90,40)]
            observed=motion_frame(1,(10,20) if home_control else (70,20),home,away)
            rejected=motion_frame(1,None,(),(),geometry_valid=False)
            frames=[observed]*20+[rejected]*500
            result=predict_four(frames,artifact)
            for i in range(20,len(frames)):
                if result['incumbent'][i]=='X':
                    self.assertEqual(result['agreement'][i],'X','decoder placeholders are not evaluated H/A proposals')

if __name__=='__main__':unittest.main()
