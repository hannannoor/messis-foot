import csv
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from gap_solver.core import Frame
from gap_solver.tactical import FEATURE_NAMES

try:
    from gap_solver import tactical_cli
except ImportError:
    tactical_cli=None


def model():
    return dict(schema_version=1,model=dict(feature_names=list(FEATURE_NAMES),children_left=[-1],children_right=[-1],
                feature=[-2],threshold=[0.],probabilities=[[0.,0.,1.]]),
                policy=dict(confidence=.9,minimum_run_frames=6,max_gap_s=2.,bridge_s=2.))


def evidence(path,n=20):
    with path.open('w',newline='') as handle:
        writer=csv.writer(handle)
        writer.writerow(['frame','period','ball_x_m','ball_y_m','home_distance_m','away_distance_m'])
        writer.writerows([i,1,20,20,.5,10] for i in range(n))


class TacticalCLI(unittest.TestCase):
    def entry(self):
        path=os.environ.get('FOOTBALL_STANDALONE')
        return [sys.executable,'-I',path,'tactical'] if path else [sys.executable,'-m','gap_solver.tactical_cli']

    def test_evidence_output_preserves_all_original_indices_and_reports_unmeasured_accuracy(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);source=root/'evidence.csv';evidence(source)
            artifact=root/'model.json';artifact.write_text(json.dumps(model()))
            output=root/'out'
            run=subprocess.run(self.entry()+['evidence','--input',str(source),'--model',str(artifact),'--out',str(output)],
                               capture_output=True,text=True)
            self.assertEqual(run.returncode,0,run.stderr)
            with (output/'submission.csv').open(newline='') as handle:
                rows=list(csv.DictReader(handle))
            self.assertEqual([int(r['frame']) for r in rows],list(range(20)))
            report=json.loads((output/'tactical_report.json').read_text())
            self.assertFalse(report['accuracy_measured'])
            self.assertFalse(report['model_externally_validated'])
            self.assertEqual(report['after']['published_dead_frames'],0)
            self.assertTrue(json.loads((output/'report.json').read_text())['live_dead_classifier_included'])

    def test_nonempty_unowned_output_and_input_alias_are_protected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);source=root/'submission.csv';evidence(source)
            artifact=root/'model.json';artifact.write_text(json.dumps(model()))
            before=source.read_bytes()
            run=subprocess.run(self.entry()+['evidence','--input',str(source),'--model',str(artifact),'--out',str(root)],
                               capture_output=True,text=True)
            self.assertNotEqual(run.returncode,0)
            self.assertEqual(source.read_bytes(),before)

    def test_invalid_homography_masks_geometry_without_creating_dead_labels(self):
        self.assertIsNotNone(tactical_cli,'tactical CLI and quality adapter are missing')
        frames=[Frame(ball_x=20,ball_y=20,home_distance=.5,away_distance=10)]*20
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'homography.csv'
            with path.open('w',newline='') as handle:
                writer=csv.writer(handle)
                writer.writerow(['frame','valid','reprojection_error']+['h'+str(a)+str(b) for a in range(3) for b in range(3)])
                for i in range(20):
                    writer.writerow([i,1,4]+[1 if a==b else 0 for a in range(3) for b in range(3)])
            changed,valid=tactical_cli.apply_geometry_quality(frames,path)
            self.assertFalse(any(valid))
            self.assertTrue(all(not f.ball_observed and not f.dead_evidence for f in changed))
            self.assertTrue(all(f.ball_observed for f in frames))

    def test_negative_reprojection_error_is_not_accepted_as_reliable(self):
        self.assertIsNotNone(tactical_cli)
        frames=[Frame(ball_x=20,ball_y=20,home_distance=.5,away_distance=10)]
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'homography.csv'
            with path.open('w',newline='') as handle:
                writer=csv.writer(handle)
                writer.writerow(['frame','valid','reprojection_error']+['h'+str(a)+str(b) for a in range(3) for b in range(3)])
                writer.writerow([0,1,-1]+[1 if a==b else 0 for a in range(3) for b in range(3)])
            changed,valid=tactical_cli.apply_geometry_quality(frames,path)
            self.assertEqual(valid,[False])
            self.assertFalse(changed[0].ball_observed)

    def test_geometry_evidence_rejects_dead_label_injection(self):
        for source_value in ('published_pre_kickoff',''):
            with tempfile.TemporaryDirectory() as d:
                root=Path(d);source=root/'evidence.csv'
                source.write_text('frame,period,dead_evidence,dead_source\n0,1,1,'+source_value+'\n')
                artifact=root/'model.json';artifact.write_text(json.dumps(model()))
                run=subprocess.run(self.entry()+['evidence','--input',str(source),'--model',str(artifact),'--out',str(root/'out')],capture_output=True,text=True)
                self.assertNotEqual(run.returncode,0,run.stdout)
                self.assertIn('geometry',run.stderr.lower())
                self.assertFalse((root/'out').exists())

    def test_identical_input_baseline_ignores_evidence_tags(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);source=root/'evidence.csv'
            with source.open('w',newline='') as handle:
                writer=csv.writer(handle)
                writer.writerow(['frame','period','ball_x_m','ball_y_m','home_distance_m','away_distance_m','tag_team'])
                for i in range(49):
                    observed=i<12 or i>=37
                    writer.writerow([i,1,20 if observed else '',20 if observed else '',.5 if observed else '',10 if observed else '','H'])
            artifact=root/'model.json';artifact.write_text(json.dumps(model()))
            run=subprocess.run(self.entry()+['evidence','--input',str(source),'--model',str(artifact),'--out',str(root/'out')],capture_output=True,text=True)
            self.assertEqual(run.returncode,0,run.stderr)
            report=json.loads((root/'out'/'tactical_report.json').read_text())
            self.assertEqual(report['before']['labels']['X'],0)
            self.assertEqual(report['baseline_on_model_inputs']['labels']['X'],25)


if __name__=='__main__':
    unittest.main()
