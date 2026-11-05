"""Meaningful publication regression: recover a known partial copy; preserve unrelated data."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
LOCAL_DELIVERY_FIXTURES=all(path.is_file() for path in (
    ROOT/'football_pipeline.pre_tactical.py',ROOT/'four-goal-test-evidence.log',
    ROOT.parent/'analysis/tactical-validated/submission.csv',
    ROOT.parent/'analysis/four-goal-completion-audit.json',
    ROOT.parent/'external-reference/reports/final-heldout.json'))

@unittest.skipUnless(os.name=='nt','Windows installer')
@unittest.skipUnless(LOCAL_DELIVERY_FIXTURES,'local delivery artifacts intentionally excluded from repository')
class DeliveryRecovery(unittest.TestCase):
    def install(self,target,*args):
        return subprocess.run(['pwsh','-NoProfile','-ExecutionPolicy','Bypass','-File',
                               str(ROOT/'install_four_goal_results.ps1'),'-TargetRunDirectory',str(target),*args],
                              capture_output=True,text=True)

    def test_partial_publication_can_resume_and_verify(self):
        with tempfile.TemporaryDirectory() as d:
            target=Path(d)/'run files';target.mkdir()
            shutil.copyfile(ROOT/'football_pipeline.pre_tactical.py',target/'football_pipeline.py')
            result=target/'outputs/tactical-validated';result.mkdir(parents=True)
            shutil.copyfile(ROOT.parent/'analysis/tactical-validated/submission.csv',result/'submission.csv')
            run=self.install(target)
            self.assertEqual(run.returncode,0,run.stderr)
            check=self.install(target,'-VerifyOnly')
            self.assertEqual(check.returncode,0,check.stderr)
            self.assertEqual((target/'football_pipeline.py').read_bytes(),(ROOT/'football_pipeline.py').read_bytes())

    def test_unrelated_partial_folder_is_preserved(self):
        with tempfile.TemporaryDirectory() as d:
            target=Path(d)/'run files';target.mkdir()
            original=(ROOT/'football_pipeline.pre_tactical.py').read_bytes()
            (target/'football_pipeline.py').write_bytes(original)
            result=target/'outputs/tactical-validated';result.mkdir(parents=True)
            unrelated=result/'keep.txt';unrelated.write_text('keep this')
            run=self.install(target)
            self.assertNotEqual(run.returncode,0)
            self.assertEqual(unrelated.read_text(),'keep this')
            self.assertEqual((target/'football_pipeline.py').read_bytes(),original)
