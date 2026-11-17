import csv
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from release_fixtures import tactical_fixture

ROOT = Path(__file__).resolve().parents[1]
PINNED_CODE = {
    'evaluation/possession_metrics.py': '341bad48904b489d6e875397b27687f5d6a4d22a397f3dc8af3a00d48f16874d',
    'evaluation/run_evaluation.py': '1c61564fe52499ba4af3006fb5eb4147b825e92bf516651add80de49d267b19f',
    'evaluation/validate_submission.py': '07ac29499acbd337e1dc1de1832d63f6e1fa1d981e22f6ad08212529e2bbee14',
    'games.py': '3b2122794e9e0476e2b3a871d14880e5fa47c4feaeacf99caef054c2309076ce',
}


class ReleaseContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        value = os.environ.get('FOOTBALL_OFFICIAL_CODE')
        if not value:
            raise RuntimeError('Set FOOTBALL_OFFICIAL_CODE to the pinned official code-only staging directory')
        cls.official = Path(value)
        for name, expected in PINNED_CODE.items():
            if hashlib.sha256((cls.official/name).read_bytes()).hexdigest() != expected:
                raise RuntimeError('Pinned official code differs')
        spec = importlib.util.spec_from_file_location('release_official_metrics', cls.official/'evaluation/possession_metrics.py')
        cls.pm = importlib.util.module_from_spec(spec); spec.loader.exec_module(cls.pm)

    def test_tactical_cli_original_index_and_periods(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); inputs = tactical_fixture(root/'inputs'); prefix = root/'inputs/synthetic'
            for source, suffix in zip(inputs, ('_atd.xml','_atd.txt','_homography.csv')):
                source.rename(str(prefix)+suffix)
            result = subprocess.run([sys.executable,'-I','-S',str(ROOT/'competition_release.py'),
                                     '--prefix',str(prefix),'--out',str(root/'out')],capture_output=True,text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)['rows'], 199319)
            submission = root/'out/submission.csv'
            with submission.open(newline='') as handle:
                table = list(csv.reader(handle))
            self.assertEqual(table[0], ['frame','label'])
            self.assertEqual(len(table)-1, 199319)
            self.assertEqual([row[0] for row in table[1:]], list(map(str,range(199319))))
            for frame, label in ((0,'X'),(11184,'X'),(11185,'D'),(90651,'D'),(90652,'X'),
                                 (110807,'X'),(110808,'D'),(190197,'D'),(190198,'X'),(199318,'X')):
                self.assertEqual(table[frame+1], [str(frame),label])
            valid = subprocess.run([sys.executable,str(self.official/'evaluation/validate_submission.py'),str(submission)],
                                   capture_output=True,text=True)
            self.assertEqual(valid.returncode, 0, valid.stderr+valid.stdout)
            receipt_path = os.environ.get('FOOTBALL_RELEASE_RECEIPT')
            if receipt_path:
                receipt = dict(schema_version=1, scope='fully_synthetic_199319_row_contract',
                               official_revision='f8f2629ff1e0985f81d7e59d8413678514ee1530',
                               official_code_sha256=PINNED_CODE, artifact_sha256=hashlib.sha256((ROOT/'competition_release.py').read_bytes()).hexdigest(),
                               rows=199319, original_index=True, structural_boundaries_checked=True,
                               csv_sha256=hashlib.sha256(submission.read_bytes()).hexdigest(),
                               official_format_validator_passed=True, challenge_data_used=False, reference_labels_used=False)
                target = Path(receipt_path); target.parent.mkdir(parents=True,exist_ok=True)
                target.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n',encoding='utf-8')

    def test_official_rejects_invalid_exports(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'synthetic.csv'
            valid = 'frame,label\n0,H\n1,A\n2,D\n3,X\n'
            path.write_text(valid)
            self.assertIsNone(self.pm.validate_submission(self.pm.read_label_csv(path), 4))
            variants = [valid.rsplit('3,X',1)[0], valid.replace('2,D','1,D'),
                        valid.replace('1,A','1,'), valid.replace('1,A','1,Z')]
            for variant in variants:
                path.write_text(variant)
                self.assertIsNotNone(self.pm.validate_submission(self.pm.read_label_csv(path), 4))


if __name__ == '__main__':
    unittest.main()
