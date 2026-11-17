from pathlib import Path
import io,tempfile,unittest,hashlib
try:
    import metrica_sample_source as s
except ImportError:
    s=None

class MetricaSource(unittest.TestCase):
    def setUp(self):self.assertIsNotNone(s,'metrica_sample_source missing')
    def test_streamed_asset_identity_and_no_overwrite(self):
        data=b'synthetic tracking\n';oid=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
        with tempfile.TemporaryDirectory(dir=Path.cwd()/'.tmp') as d:
            item=dict(path='data/test.csv',bytes=len(data),git_blob_sha1=oid)
            result=s.download_asset(Path(d),item,'a'*40,opener=lambda req,**kw:io.BytesIO(data))
            self.assertEqual(result['sha256'],hashlib.sha256(data).hexdigest())
            with self.assertRaises(FileExistsError):s.download_asset(Path(d),item,'a'*40,opener=lambda req,**kw:io.BytesIO(data))
    def test_bad_identity_retains_claim_and_partial_file(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()/'.tmp') as d:
            item=dict(path='data/test.csv',bytes=4,git_blob_sha1='0'*40)
            with self.assertRaises(ValueError):s.download_asset(Path(d),item,'a'*40,opener=lambda req,**kw:io.BytesIO(b'bad!'))
            self.assertTrue((Path(d)/'data/test.csv').is_file())
            self.assertEqual(len(list((Path(d)/'claims').glob('*.json'))),1)
    def test_unsafe_paths_rejected(self):
        for name in ('../escape','/absolute','C:/escape','data\\escape'):
            with tempfile.TemporaryDirectory(dir=Path.cwd()/'.tmp') as d:
                with self.assertRaises(ValueError):s.download_asset(Path(d),dict(path=name,bytes=1,git_blob_sha1='0'*40),'a'*40)
