import hashlib,json,tempfile,unittest
from pathlib import Path
try:
    from gap_solver.temporal_protocol import load_temporal_frozen,local_eligible,digest
except ImportError:
    load_temporal_frozen=local_eligible=digest=None


class TemporalFreeze(unittest.TestCase):
    def fixture(self,root):
        code=root/'code';code.mkdir();(code/'source.py').write_text('x=1\n')
        artifact=dict(schema_version=1,eligibility='rejected_before_final_test',validation_passed=False)
        manifest=dict(frozen_before_final_test=True,artifact_sha256=digest(artifact),
            source_sha256={'source.py':hashlib.sha256((code/'source.py').read_bytes()).hexdigest()},
            split={'development':[1],'calibration':[2],'validation':[3],'test':[4]})
        (root/'temporal-selected.json').write_text(json.dumps(artifact));(root/'freeze-manifest.json').write_text(json.dumps(manifest))
        return code,artifact,manifest

    def test_rejected_challenger_cannot_become_local_eligible_from_a_good_test(self):
        self.assertIsNotNone(local_eligible)
        with tempfile.TemporaryDirectory() as d:
            code,artifact,manifest=self.fixture(Path(d))
            loaded,_=load_temporal_frozen(d,code)
            self.assertFalse(local_eligible(loaded,dict(artifact_sha256=manifest['artifact_sha256'],acceptance={'passes':True})))

    def test_freeze_detects_source_artifact_and_partition_changes(self):
        self.assertIsNotNone(load_temporal_frozen)
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);code,artifact,manifest=self.fixture(root)
            load_temporal_frozen(root,code)
            (code/'source.py').write_text('x=2\n')
            with self.assertRaises(ValueError):load_temporal_frozen(root,code)
            (code/'source.py').write_text('x=1\n')
            manifest['split']['test']=[3];(root/'freeze-manifest.json').write_text(json.dumps(manifest))
            with self.assertRaises(ValueError):load_temporal_frozen(root,code)
