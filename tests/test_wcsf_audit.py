"""No real acquisition: stage-integrity tests use synthetic ZIP responses."""
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from wcsf_fixtures import rows,csv_zip
import wcsf_source

ROOT=Path(__file__).resolve().parents[1]


class AuditTests(unittest.TestCase):
    def setUp(self):
        import wcsf_audit
        if not hasattr(wcsf_audit,'AuditSession'):self.fail('Missing frozen stage driver')
        self.api=wcsf_audit;self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.folder=Path(self.tmp.name);self.assets=[];self.responses={}
        for i,(name,_,_) in enumerate(wcsf_source.ASSETS):
            p=csv_zip(self.folder/name,rows());b=p.read_bytes();h=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
            self.assets.append((name,h,len(b)));self.responses[name]=b
        self.patch_assets=patch('wcsf_source.ASSETS',tuple(self.assets));self.patch_assets.start();self.addCleanup(self.patch_assets.stop)
        self.session=self.api.AuditSession(ROOT,self.folder/'reports',self.folder/'private')

    def acquire(self):
        self.session.freeze()
        with patch('wcsf_source.urllib.request.urlopen',side_effect=lambda req,**kw:io.BytesIO(self.responses[req.full_url.rsplit('/',1)[1]])):
            self.session.acquire()

    def ready(self):
        self.acquire();self.session.qualify()

    def test_freeze_covers_transitive_wrappers_and_protocol(self):
        freeze=self.session.freeze()
        for p in ('accuracy_experiment.py','accuracy_experiment_frozen.py','accuracy_evidence.py','ball_gap_candidate.py','wcsf_reference.py','wcsf_report.py'):
            self.assertIn(p,freeze['source_sha256'])
        self.assertIn('docs/superpowers/specs/2026-11-09-wcsf-transfer-design.md',freeze['source_sha256'])
        self.assertFalse(self.session.private.exists())

    def test_source_input_or_protocol_change_stops_before_scoring(self):
        self.ready();self.session.infer()
        with self.session.paths.geometry_db.open('ab') as f:f.write(b'changed')
        with self.assertRaises(ValueError):self.session.score()
        self.assertFalse((self.session.public/'results.json').exists())

    def test_protocol_tamper_rejected(self):
        self.session.freeze();p=self.session.public/'freeze.json';d=json.loads(p.read_text());d['methods']=['extra'];p.write_text(json.dumps(d))
        with self.assertRaises(ValueError):self.session.acquire()
        self.assertFalse(self.session.private.exists())

    def test_frozen_schema_boolean_is_not_identity_equal(self):
        self.session.freeze();p=self.session.public/'freeze.json';d=json.loads(p.read_text());d['schema_version']=True;p.write_text(json.dumps(d))
        with self.assertRaises(ValueError):self.session._freeze()

    def test_all_predictions_sealed_before_reference_summary(self):
        self.ready()
        with self.assertRaises(ValueError):self.session.score()
        self.assertFalse((self.session.public/'results.json').exists())
        self.session.infer();self.session.score();self.assertTrue((self.session.public/'results.json').exists())
        events=[json.loads(s)['event'] for s in self.session.paths.access_log.read_text().splitlines()]
        self.assertLess(events.index('predictions_sealed'),events.index('reference_summary_and_outcomes_opened'))

    def test_failed_geometry_has_zero_scoring_calls(self):
        for name,_,_ in self.assets:
            data=rows()
            for r in data:r['y_ball']=0
            p=csv_zip(self.folder/name,data);b=p.read_bytes();self.responses[name]=b
        self.assets=[(n,hashlib.sha1(b'blob '+str(len(self.responses[n])).encode()+b'\0'+self.responses[n]).hexdigest(),len(self.responses[n])) for n,_,_ in self.assets]
        with patch('wcsf_source.ASSETS',tuple(self.assets)):
            self.ready();self.assertIsNone(self.session.geometry()['decision']['selected'])
            with self.assertRaises(ValueError):self.session.infer()
            with self.assertRaises(ValueError):self.session.score()
            self.assertEqual(self.session.attempts(),[]);self.session.verify()

    def test_resume_reuses_seals_without_new_calls(self):
        self.ready();self.session.infer();self.session.score();before=self.session.attempts()
        self.session.infer();self.session.score();self.session.verify();self.assertEqual(self.session.attempts(),before)
        self.assertEqual(sum(e['stage']=='score' for e in before),3)

    def test_partial_or_conflicting_receipts_preserved(self):
        self.ready();p=self.session.private/'predictions';p.mkdir();(p/'partial').write_text('preserve')
        with self.assertRaises(ValueError):self.session.infer()
        self.assertEqual((p/'partial').read_text(),'preserve')

    def test_attempt_counter_includes_aborted_call(self):
        self.ready();self.session.infer()
        with patch('wcsf_audit.score_fixed',side_effect=ValueError('synthetic failure')):
            with self.assertRaises(ValueError):self.session.score()
        attempts=self.session.attempts();self.assertEqual(sum(a['stage']=='score' for a in attempts),1)
        with self.assertRaises(ValueError):self.session.score()
        self.assertEqual(self.session.attempts(),attempts)


if __name__=='__main__':unittest.main()
