import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from gap_solver.tactical import FEATURE_NAMES

try:
    from gap_solver.frozen_protocol import load_frozen
except ImportError:
    load_frozen=None


class FrozenProtocol(unittest.TestCase):
    def fixture(self,root):
        frozen=root/'frozen';frozen.mkdir()
        code=root/'code';code.mkdir()
        (code/'tactical.py').write_bytes(b'fixed implementation')
        split={'development':['train'],'validation':['val'],'test':['held-out']}
        model=dict(feature_names=list(FEATURE_NAMES),children_left=[-1],children_right=[-1],feature=[-2],threshold=[0.],probabilities=[[1.,0.,0.]])
        artifact=dict(schema_version=1,model=model,policy=dict(confidence=.9,minimum_run_frames=6,max_gap_s=2.,bridge_s=2.),
                      training_matches=split['development'],validation_matches=split['validation'],test_matches=split['test'],
                      features_exclude_reference_labels=True)
        digest=hashlib.sha256(json.dumps(artifact,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        manifest=dict(artifact_sha256=digest,source_sha256={'tactical.py':hashlib.sha256(b'fixed implementation').hexdigest()},
                      split=split,frozen_before_test_scores=True)
        (frozen/'tactical-selected.json').write_text(json.dumps(artifact))
        (frozen/'freeze-manifest.json').write_text(json.dumps(manifest))
        (root/'provenance.json').write_text(json.dumps({'split':split}))
        return frozen,code,artifact,manifest

    def test_frozen_artifact_and_prediction_sources_must_match(self):
        self.assertIsNotNone(load_frozen,'pre-test freeze verification is missing')
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);frozen,code,artifact,manifest=self.fixture(root)
            result=load_frozen(root,code)
            self.assertEqual(result[1]['artifact_sha256'],manifest['artifact_sha256'])
            (code/'tactical.py').write_bytes(b'changed implementation')
            with self.assertRaises(ValueError):
                load_frozen(root,code)

    def test_mutated_model_or_overlapping_split_cannot_enter_final_test(self):
        self.assertIsNotNone(load_frozen,'pre-test freeze verification is missing')
        for change in ('model','split'):
            with tempfile.TemporaryDirectory() as d:
                root=Path(d);frozen,code,artifact,manifest=self.fixture(root)
                if change=='model':
                    artifact['policy']['confidence']=.1
                    (frozen/'tactical-selected.json').write_text(json.dumps(artifact))
                else:
                    manifest['split']['test']=['train']
                    (frozen/'freeze-manifest.json').write_text(json.dumps(manifest))
                with self.subTest(change=change),self.assertRaises(ValueError):
                    load_frozen(root,code)


if __name__=='__main__':
    unittest.main()
