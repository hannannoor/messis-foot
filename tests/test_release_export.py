from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
import subprocess
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import ball_gap_candidate
import release_runtime as runtime
from release_fixtures import release_fixture


class ReleaseExport(unittest.TestCase):
    def setUp(self):
        self.assertTrue(hasattr(runtime, 'run_source'), 'Exact release exporter is missing')

    def test_csv_bytes_and_incumbent_parity(self):
        self.assertEqual(runtime.submission_bytes(tuple('HADX')),
                         b'frame,label\r\n0,H\r\n1,A\r\n2,D\r\n3,X\r\n')
        for labels in (('h',), ('',), ('H', None), ('H,A',)):
            with self.assertRaises(ValueError):
                runtime.submission_bytes(labels)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); inputs = release_fixture(root/'inputs')
            ball_gap_candidate.run_source(*inputs, root/'old', scope='synthetic')
            report = runtime.run_source(*inputs, root/'new', scope='synthetic')
            self.assertEqual((root/'new/submission.csv').read_bytes(), (root/'old/submission.csv').read_bytes())
            self.assertEqual(report['csv_sha256'], hashlib.sha256((root/'old/submission.csv').read_bytes()).hexdigest())

    def test_same_source_different_directories_same_hashes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); inputs = release_fixture(root/'inputs')
            a = runtime.run_source(*inputs, root/'a', scope='synthetic')
            b = runtime.run_source(*inputs, root/'b', scope='synthetic')
            self.assertEqual(a, b)
            self.assertEqual((root/'a/release-receipt.json').read_bytes(), (root/'b/release-receipt.json').read_bytes())
            self.assertEqual(runtime._verify_generation(root/'a'), a)
            serialized = json.dumps(a)
            self.assertNotIn(str(root), serialized)
            self.assertNotIn('timestamp', serialized)
            self.assertNotIn('generation_id', serialized)
            (root/'a/submission.csv').write_bytes(b'frame,label\r\n0,X\r\n')
            with self.assertRaises(ValueError):
                runtime._verify_generation(root/'a')

    def test_existing_empty_populated_and_input_aliases_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); inputs = release_fixture(root/'inputs')
            empty = root/'empty'; empty.mkdir()
            populated = root/'populated'; populated.mkdir(); (populated/'keep').write_bytes(b'keep')
            for target in (empty, populated, inputs[0], inputs[1], inputs[2]):
                with self.subTest(target=target.name), self.assertRaises((ValueError, FileExistsError)):
                    runtime.run_source(*inputs, target, scope='synthetic')
            self.assertEqual(list(empty.iterdir()), [])
            self.assertEqual((populated/'keep').read_bytes(), b'keep')
            self.assertTrue(inputs[0].read_text().startswith('<Match>'))

    def test_concurrent_claim_only_one_winner(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); inputs = release_fixture(root/'inputs')
            def worker():
                try:
                    return runtime.run_source(*inputs, root/'output', scope='synthetic')
                except (ValueError, FileExistsError):
                    return None
            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(lambda _: worker(), range(2)))
            self.assertEqual(sum(value is not None for value in results), 1)
            self.assertEqual(runtime._verify_generation(root/'output')['rows'], 500)

    def test_mutation_and_interruption_leave_incomplete(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for failure in ('input-mutation', 'receipt-write'):
                inputs = release_fixture(root/failure)
                output = root/(failure+'-output')
                original = runtime._write_exclusive
                def write(path, data):
                    if failure == 'receipt-write' and path.name == 'release-receipt.json':
                        raise OSError('injected disk failure')
                    original(path, data)
                    if failure == 'input-mutation' and path.name == 'submission.csv':
                        inputs[1].write_bytes(inputs[1].read_bytes()+b'\n')
                with patch.object(runtime, '_write_exclusive', side_effect=write):
                    with self.assertRaises((ValueError, OSError)):
                        runtime.run_source(*inputs, output, scope='synthetic')
                self.assertTrue((output/'.incomplete').exists())
                with self.assertRaises(ValueError):
                    runtime._verify_generation(output)
                with self.assertRaises((ValueError, FileExistsError)):
                    runtime.run_source(*inputs, output, scope='synthetic')
                fresh = release_fixture(root/(failure+'-fresh'))
                self.assertEqual(runtime.run_source(*fresh, root/(failure+'-retry'), scope='synthetic')['rows'], 500)

    def test_corrupt_written_csv_cannot_clear_incomplete_marker(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); inputs = release_fixture(root/'inputs')
            original = runtime._write_exclusive
            def corrupt(path, data):
                original(path, data)
                if path.name == 'submission.csv':
                    path.write_bytes(b'corrupt\r\n')
            with patch.object(runtime, '_write_exclusive', side_effect=corrupt):
                with self.assertRaises(ValueError):
                    runtime.run_source(*inputs, root/'out', scope='synthetic')
            self.assertTrue((root/'out/.incomplete').exists())

    def test_linked_ancestor_and_hardlink_alias_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); inputs = release_fixture(root/'inputs')
            alias = root/'alias'; alias.mkdir()
            os.link(inputs[0], alias/'submission.csv')
            before = inputs[0].read_bytes()
            with self.assertRaises((ValueError, FileExistsError)):
                runtime.run_source(*inputs, alias, scope='synthetic')
            self.assertEqual(inputs[0].read_bytes(), before)
            link = root/'link'
            try:
                link.symlink_to(root/'inputs', target_is_directory=True)
            except OSError as error:
                if os.name != 'nt':
                    self.skipTest('Native directory-link creation unavailable')
                result = subprocess.run(['cmd', '/c', 'mklink', '/J', str(link), str(root/'inputs')], capture_output=True)
                if result.returncode:
                    self.skipTest('Native directory-link creation unavailable')
            with self.assertRaises(ValueError):
                runtime.run_source(*inputs, link/'new', scope='synthetic')
            self.assertFalse((root/'inputs/new').exists())


if __name__ == '__main__':
    unittest.main()
