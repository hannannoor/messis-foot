import copy
from contextlib import redirect_stderr
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import build_competition_release as builder
import release_runtime as runtime
from release_fixtures import release_fixture
from test_release_bundle import ROOT, assignments, copy_selected


class ReleaseReview(unittest.TestCase):
    def test_corrupted_persisted_receipt_never_completes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); inputs = release_fixture(root/'inputs')
            original = runtime._write_exclusive
            def corrupt(path, data):
                if path.name == 'release-receipt.json':
                    value = json.loads(data)
                    value.update(model_sha256='oops', input_sha256={}, release=None, semantic_sha256='')
                    data = json.dumps(value).encode()
                original(path, data)
            with patch.object(runtime, '_write_exclusive', side_effect=corrupt):
                with self.assertRaises(ValueError):
                    runtime.run_source(*inputs, root/'out', scope='synthetic')
            self.assertTrue((root/'out/.incomplete').exists())

    def test_consumer_rejects_invalid_identity_and_unbounded_counts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); inputs = release_fixture(root/'inputs')
            original = runtime.run_source(*inputs, root/'out', scope='synthetic')
            variants = [dict(model_sha256='oops'), dict(input_sha256={}), dict(semantic_sha256=''),
                        dict(release=None), dict(policy_counts={'trace':[1,2,3]})]
            for changes in variants:
                value = copy.deepcopy(original); value.update(changes)
                (root/'out/release-receipt.json').write_text(json.dumps(value))
                with self.subTest(changes=list(changes)), self.assertRaises(ValueError):
                    runtime._verify_generation(root/'out')

    def test_preloaded_owned_modules_rejected_without_mutation(self):
        code = '''
import importlib,runpy,sys
sys.path.insert(0,sys.argv[2])
existing=importlib.import_module(sys.argv[3])
before=getattr(existing,'_BUNDLE_MANIFEST',None)
finders=len(sys.meta_path)
rejected=False
try:runpy.run_path(sys.argv[1])
except SystemExit:rejected=True
assert rejected, 'Conflicting preloaded code was reused'
assert getattr(existing,'_BUNDLE_MANIFEST',None)==before
assert len(sys.meta_path)==finders
'''
        with tempfile.TemporaryDirectory() as directory:
            artifact = Path(directory)/'release.py'; artifact.write_bytes(builder.build_release(ROOT))
            for name in ('release_runtime', 'gap_solver.core'):
                with self.subTest(module=name):
                    result = subprocess.run([sys.executable,'-I','-S','-c',code,str(artifact),str(ROOT),name],capture_output=True,text=True)
                    self.assertEqual(result.returncode, 0, result.stderr)

    def test_loaded_artifact_and_source_are_pinned(self):
        code = '''
import pathlib,runpy,sys
if sys.argv[1]=='bundle':
    module=runpy.run_path(sys.argv[2]); runtime=module['_runtime']; target=pathlib.Path(sys.argv[2])
else:
    sys.path.insert(0,sys.argv[2]); import release_runtime as runtime
    target=pathlib.Path(sys.argv[2])/'ball_gap_policy.py'
runtime._release_identity()
target.write_bytes(target.read_bytes()+b'\\n# changed after loading\\n')
rejected=False
try:runtime._release_identity()
except ValueError:rejected=True
assert rejected, 'Loaded code was relabelled as changed disk bytes'
'''
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); artifact = root/'release.py'; artifact.write_bytes(builder.build_release(ROOT))
            source = copy_selected(root/'source')
            for kind, path in (('bundle',artifact), ('source',source)):
                with self.subTest(kind=kind):
                    result = subprocess.run([sys.executable,'-I','-S','-c',code,kind,str(path)],capture_output=True,text=True)
                    self.assertEqual(result.returncode, 0, result.stderr)

    def test_malformed_xml_cli_has_no_input_echo(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); inputs = release_fixture(root/'inputs'); prefix = root/'bad'
            token = 'private-probe-token'
            for source, suffix in zip(inputs, ('_atd.xml','_atd.txt','_homography.csv')):
                data = source.read_bytes()
                if suffix == '_atd.xml':
                    data = ('<?xml version="1.0" encoding="'+token+'"?>').encode()+data
                Path(str(prefix)+suffix).write_bytes(data)
            artifact = root/'release.py'; artifact.write_bytes(builder.build_release(ROOT))
            result = subprocess.run([sys.executable,'-I','-S',str(artifact),'--prefix',str(prefix),'--out',str(root/'out')],capture_output=True,text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertNotIn(token, result.stderr+result.stdout)
            self.assertNotIn('Traceback', result.stderr)
            self.assertEqual(result.stdout, '')

    def test_cli_parser_errors_are_sanitized(self):
        for error in (LookupError, csv.Error, OverflowError):
            stderr = io.StringIO()
            with self.subTest(error=error.__name__), redirect_stderr(stderr), patch.object(runtime, 'load_source', side_effect=error('private-probe-token')):
                with self.assertRaises(SystemExit):
                    runtime.main(['--prefix','synthetic','--out','not-created'])
                self.assertNotIn('private-probe-token', stderr.getvalue())
                self.assertNotIn('Traceback', stderr.getvalue())

    def test_builder_linked_outputs_preserve_other_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); source = copy_selected(root/'source')
            outside = root/'outside'; outside.mkdir(); user_file = outside/'user.py'; user_file.write_bytes(b'user bytes\n')
            os.link(user_file, source/'competition_release.py')
            with self.subTest(case='hardlink'):
                with patch.object(builder, '__file__', str(source/'build_competition_release.py')):
                    with self.assertRaises(ValueError):
                        builder.main([])
                self.assertEqual(user_file.read_bytes(), b'user bytes\n')
            # New source copy for the ancestor case; no deletion of the hardlink case.
            second = copy_selected(root/'second')
            if os.name == 'nt':
                result = subprocess.run(['cmd','/c','mklink','/J',str(second/'release'),str(outside)],capture_output=True)
                self.assertEqual(result.returncode, 0)
            else:
                (second/'release').symlink_to(outside, target_is_directory=True)
            with self.subTest(case='junction'):
                with patch.object(builder, '__file__', str(second/'build_competition_release.py')):
                    with self.assertRaises(ValueError):
                        builder.main([])
                self.assertFalse((outside/'manifest.json').exists())
                self.assertFalse((second/'competition_release.py').exists())

    def test_builder_uses_one_coherent_source_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); source = copy_selected(root/'source'); original = builder._parts
            changed = False
            def parts(path):
                nonlocal changed
                value = original(path)
                if not changed:
                    policy = source/'ball_gap_policy.py'; policy.write_bytes(policy.read_bytes()+b'\n# concurrent save\n')
                    changed = True
                return value
            with patch.object(builder, '__file__', str(source/'build_competition_release.py')), patch.object(builder, '_parts', side_effect=parts):
                self.assertEqual(builder.main([]), 0)
            embedded = assignments((source/'competition_release.py').read_bytes())['MANIFEST']
            external = json.loads((source/'release/manifest.json').read_text())
            self.assertEqual(embedded, external)


if __name__ == '__main__':
    unittest.main()
