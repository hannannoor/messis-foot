import ast
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import release_runtime
from release_fixtures import release_fixture

try:
    import build_competition_release as builder
except ImportError:
    builder = None

ROOT = Path(__file__).resolve().parents[1]
API_CODE = '''
import json,runpy,sys
module=runpy.run_path(sys.argv[1])
report=module['run_source'](*sys.argv[2:5],sys.argv[5],scope='synthetic')
print(json.dumps({'rows':report['rows'],'csv_sha256':report['csv_sha256']}))
'''


def assignments(data):
    return {node.targets[0].id: ast.literal_eval(node.value) for node in ast.parse(data).body
            if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id in ('SOURCES', 'MANIFEST', 'SOURCE_PATHS')}


def copy_selected(destination):
    destination.mkdir()
    for path in release_runtime.SOURCE_FILES.values():
        target = destination/path; target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT/path, target)
    return destination


class ReleaseBundle(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(builder, 'Deterministic release builder is missing')

    def test_repeated_builds_exact_and_owned_sources_pinned(self):
        first = builder.build_release(ROOT)
        self.assertEqual(first, builder.build_release(ROOT))
        embedded = assignments(first)
        self.assertEqual(set(embedded['SOURCES']), set(release_runtime.SOURCE_FILES))
        for module, path in release_runtime.SOURCE_FILES.items():
            raw = (ROOT/path).read_bytes()
            self.assertEqual(embedded['SOURCES'][module].encode('utf-8'), raw)
            self.assertEqual(embedded['MANIFEST']['sources'][path], hashlib.sha256(raw).hexdigest())
        self.assertEqual(embedded['MANIFEST']['policy_id'], 'w0-c32-neutral-missing')
        self.assertEqual(embedded['MANIFEST']['switch_cost'], 32.)
        self.assertEqual(embedded['MANIFEST']['motion_weight'], 0.)

    def test_clean_isolated_artifact(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); artifact = root/'competition_release.py'; artifact.write_bytes(builder.build_release(ROOT))
            inputs = release_fixture(root/'inputs'); elsewhere = root/'elsewhere'; elsewhere.mkdir()
            for flag in ('--version', '--help'):
                result = subprocess.run([sys.executable,'-I','-S',str(artifact),flag],cwd=elsewhere,capture_output=True,text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
            result = subprocess.run([sys.executable,'-I','-S','-c',API_CODE,str(artifact),*map(str,inputs),str(root/'out')],
                                    cwd=elsewhere,capture_output=True,text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)['rows'], 500)
            prefix = root/'short'
            for source, suffix in zip(inputs, ('_atd.xml','_atd.txt','_homography.csv')):
                shutil.copyfile(source, str(prefix)+suffix)
            result = subprocess.run([sys.executable,'-I','-S',str(artifact),'--prefix',str(prefix),'--out',str(root/'short-out')],
                                    cwd=elsewhere,capture_output=True,text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse((root/'short-out').exists())

    def test_unrelated_research_mutation_has_no_effect(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); source = copy_selected(root/'source')
            original = builder.build_release(source)
            path = source/'reports/ball-gap/summary.json'; path.parent.mkdir(parents=True); path.write_text('{}')
            path = source/'benchmark/skillcorner/frozen/temporal-selected.json'; path.parent.mkdir(parents=True); path.write_text('broken research file')
            self.assertEqual(builder.build_release(source), original)
            artifact = root/'competition_release.py'; artifact.write_bytes(original)
            inputs = release_fixture(root/'inputs')
            result = subprocess.run([sys.executable,'-I','-S','-c',API_CODE,str(artifact),*map(str,inputs),str(root/'out')],capture_output=True,text=True)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_owned_source_tamper_has_new_identity_and_corrupt_embedding_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); source = copy_selected(root/'source')
            original = builder.build_release(source)
            policy = source/'ball_gap_policy.py'; policy.write_bytes(policy.read_bytes()+b'\n# changed source\n')
            changed = builder.build_release(source)
            self.assertNotEqual(changed, original)
            self.assertNotEqual(assignments(changed)['MANIFEST']['sources'], assignments(original)['MANIFEST']['sources'])
            old = assignments(original)['SOURCES']; bad = dict(old, ball_gap_policy=old['ball_gap_policy']+'\n# unsealed\n')
            artifact = root/'bad.py'; artifact.write_bytes(original.replace(('SOURCES = '+repr(old)).encode(), ('SOURCES = '+repr(bad)).encode()))
            result = subprocess.run([sys.executable,'-I','-S',str(artifact),'--version'],capture_output=True,text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('Embedded source identity mismatch', result.stderr)

    def test_missing_research_imports_never_executed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); artifact = root/'competition_release.py'; artifact.write_bytes(builder.build_release(ROOT))
            inputs = release_fixture(root/'inputs')
            blocker = '''
import importlib.abc,sys
class Block(importlib.abc.MetaPathFinder):
    def find_spec(self,fullname,path=None,target=None):
        if fullname.split('.')[0] in ('numpy','pandas','sklearn','soft_candidate','ball_gap_candidate') or fullname in ('gap_solver.accuracy_protocol','gap_solver.temporal_protocol','gap_solver.candidate_cli'):
            raise ImportError('Forbidden research import')
sys.meta_path.insert(0,Block())
'''
            result = subprocess.run([sys.executable,'-I','-S','-c',blocker+API_CODE,str(artifact),*map(str,inputs),str(root/'out')],capture_output=True,text=True)
            self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
