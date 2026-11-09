"""Public-only verification and explicit new-run CLI need no private sibling."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from wcsf_fixtures import scored_session

ROOT=Path(__file__).resolve().parents[1]


class PostrunTests(unittest.TestCase):
    def setUp(self):
        try:import wcsf_postrun_verify
        except ImportError:self.fail('Missing portable public verifier and historical post-run guard')
        self.api=wcsf_postrun_verify

    def test_public_verification_needs_no_private_data_or_matching_environment(self):
        with tempfile.TemporaryDirectory() as tmp,scored_session(tmp) as session:
            session.private.rename(Path(tmp)/'hidden-private')
            with patch.object(sys,'version','different interpreter environment'):
                result=self.api.verify_public(session.public)
            self.assertTrue(result['public_numeric_and_hash_chain_verified'])
            self.assertFalse(result['private_inputs_verified'])

    def test_public_hash_chain_tamper_fails(self):
        with tempfile.TemporaryDirectory() as tmp,scored_session(tmp) as session:
            p=session.public/'geometry.json';data=json.loads(p.read_text());data['decision']['eligible']+=1;p.write_text(json.dumps(data))
            with self.assertRaises(ValueError):self.api.verify_public(session.public)

    def test_fresh_cli_freeze_and_public_verify_preserve_published_receipts(self):
        with tempfile.TemporaryDirectory() as tmp:
            checkout=Path(tmp)/'checkout'
            shutil.copytree(ROOT,checkout,ignore=shutil.ignore_patterns('.tmp','.superpowers','__pycache__'))
            old=checkout/'reports/wcsf-transfer-v2/freeze.json';before=hashlib.sha256(old.read_bytes()).hexdigest()
            run=subprocess.run([sys.executable,str(checkout/'wcsf_audit.py'),'freeze','--run-id','fresh-check'],cwd=checkout,capture_output=True,text=True,timeout=60)
            self.assertEqual(run.returncode,0,run.stderr+run.stdout)
            self.assertTrue((checkout/'.tmp/wcsf-runs/fresh-check/reports/freeze.json').is_file())
            self.assertEqual(hashlib.sha256(old.read_bytes()).hexdigest(),before)
            self.assertFalse((checkout.parent/'wcsf-reference/fresh-check').exists())
            check=subprocess.run([sys.executable,str(checkout/'wcsf_postrun_verify.py'),'public'],cwd=checkout,capture_output=True,text=True,timeout=60)
            self.assertEqual(check.returncode,0,check.stderr+check.stdout)
            self.assertEqual(hashlib.sha256(old.read_bytes()).hexdigest(),before)


if __name__=='__main__':unittest.main()
