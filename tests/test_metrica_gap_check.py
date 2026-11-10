from pathlib import Path
import tempfile,unittest,hashlib
try:
    import metrica_gap_check as m
except ImportError:m=None

class MetricaCheck(unittest.TestCase):
    def setUp(self):self.assertIsNotNone(m,'metrica_gap_check missing')
    def records(self):return [dict(game=g,control=dict(metrics=dict(spell_f1_mean=.5)),candidate=dict(metrics=dict(spell_f1_mean=.5)),gap={}) for g in m.GAMES]
    def test_mean_gate_and_exact_inventory(self):
        rows=self.records();self.assertTrue(m.decide(rows)['passed'])
        rows[0]['candidate']['metrics']['spell_f1_mean']=.49
        self.assertFalse(m.decide(rows)['passed'])
        for bad in (rows[:-1],rows+[rows[0]]):
            with self.assertRaises(ValueError):m.decide(bad)
    def test_source_blob_identity_and_missing_file(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()/'.tmp') as d:
            root=Path(d);data=b'public sample';(root/'source').write_bytes(data)
            asset=dict(path='source',bytes=len(data),git_blob_sha1=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest())
            m.verify_asset(root,asset)
            (root/'source').write_bytes(b'changed')
            with self.assertRaises(ValueError):m.verify_asset(root,asset)
    def test_claim_budget_is_per_variant_and_exclusive(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()/'.tmp') as d:
            root=Path(d);m.claim(root,'control',m.GAMES[0]);m.claim(root,'rule',m.GAMES[0])
            with self.assertRaises(FileExistsError):m.claim(root,'control',m.GAMES[0])
            with self.assertRaises(ValueError):m.claim(root,'control','unknown-game')
    def test_provisional_receipt_cannot_be_overwritten(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()/'.tmp') as d:
            root=Path(d);m.provisional(root,'control',m.GAMES[0],{'score':.5})
            with self.assertRaises(FileExistsError):m.provisional(root,'control',m.GAMES[0],{'score':.6})
