import hashlib
from pathlib import Path
import tempfile
import unittest

try:
    from gap_solver.acquisition import acquire_asset
except ImportError:
    acquire_asset=None


class VerifiedAcquisition(unittest.TestCase):
    def test_verified_source_is_published_and_cached_without_network(self):
        self.assertIsNotNone(acquire_asset,'verified external acquisition is missing')
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);source=root/'source.bin';source.write_bytes(b'licensed synthetic fixture')
            target=root/'raw'/'asset.bin';sha=hashlib.sha256(source.read_bytes()).hexdigest()
            acquire_asset(source.as_uri(),target,len(source.read_bytes()),sha,'sha256')
            self.assertEqual(target.read_bytes(),source.read_bytes())
            source.unlink()
            acquire_asset(source.as_uri(),target,len(target.read_bytes()),sha,'sha256')
            self.assertEqual(target.read_bytes(),b'licensed synthetic fixture')

    def test_bad_download_never_publishes_and_does_not_resume_invalid_eof(self):
        self.assertIsNotNone(acquire_asset)
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);source=root/'source.bin';source.write_bytes(b'right')
            target=root/'raw'/'asset.bin';target.parent.mkdir()
            (target.parent/'asset.bin.partial').write_bytes(b'wrong')
            with self.assertRaises(ValueError):acquire_asset(source.as_uri(),target,5,'0'*64,'sha256')
            self.assertFalse(target.exists())
            self.assertEqual((target.parent/'asset.bin.partial').read_bytes(),b'wrong')
            acquire_asset(source.as_uri(),target,5,hashlib.sha256(b'right').hexdigest(),'sha256')
            self.assertEqual(target.read_bytes(),b'right')

    def test_existing_edited_destination_is_preserved(self):
        self.assertIsNotNone(acquire_asset)
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);source=root/'source.bin';source.write_bytes(b'right');target=root/'asset.bin';target.write_bytes(b'edited')
            with self.assertRaises(ValueError):acquire_asset(source.as_uri(),target,5,hashlib.sha256(b'right').hexdigest(),'sha256')
            self.assertEqual(target.read_bytes(),b'edited')
