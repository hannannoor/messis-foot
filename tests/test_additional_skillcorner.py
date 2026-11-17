"""Data-only compatibility tests. No trainer/model imports, fitting, or predictions."""
import ast
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np

from gap_solver.motion import motion_frame
import prepare_additional_skillcorner as prep
from se_data_catalog import ADDITIONAL_CASES, ADDITIONAL_SKILLCORNER
import se_load


def reader_from_source(file, function, namespace):
    """Run only a trainer's unchanged data reader, without importing its model code."""
    tree = ast.parse((prep.CODE / file).read_text(encoding='utf-8'))
    reader = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == function)
    code = compile(ast.Module(body=[reader], type_ignores=[]), file, 'exec')
    exec(code, namespace)
    return namespace[function]


class AdditionalSkillCornerData(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        frames = [motion_frame(1, (50.0 + (i % 10) * .1, 34.0),
                               ((49.0, 34.0),), ((60.0, 34.0),), (1,), (2,)) for i in range(800)]
        ref = np.asarray(([0] * 200 + [1] * 200 + [3] * 400), np.uint8)
        cls.case = prep.build_case(frames, ref)

    def test_catalog_preserves_historical_split_and_adds_exactly_ten(self):
        self.assertEqual(len(se_load.ALL), 18)
        self.assertEqual(len(se_load.SKILLCORNER), 10)
        self.assertEqual(len(se_load.AVAILABLE), 28)
        self.assertEqual(len(set(se_load.AVAILABLE)), 28)
        self.assertFalse(set(ADDITIONAL_SKILLCORNER) & set(se_load.SKILLCORNER))
        self.assertFalse(set(ADDITIONAL_CASES) & set(se_load.HOLDOUT))
        self.assertEqual(se_load.AVAILABLE[:18], se_load.ALL)
        options = json.loads((prep.CODE / 'benchmark/skillcorner/additional-training-data.json').read_text())
        self.assertEqual(tuple(options['extra_train']), ADDITIONAL_CASES)

    def test_pinned_tracking_content_does_not_duplicate_legacy_matches(self):
        protocol = json.loads((prep.CODE / 'benchmark/skillcorner/protocol.json').read_text())
        objects = {x['path'].split('/')[2]: x['object_sha256'] for x in protocol['tracking_lfs_objects']}
        new = [objects[x] for x in ADDITIONAL_SKILLCORNER]
        old = {objects[x] for x in se_load.SKILLCORNER}
        self.assertEqual(len(set(new)), 10)
        self.assertFalse(set(new) & old)

    def test_loader_routes_only_additions_to_new_cache(self):
        for cid, expected_root in ((ADDITIONAL_CASES[0], se_load.ADDITIONAL_ROOT),
                                   ('skillcorner-1874553', se_load.WORKSPACE / 'independent-reference')):
            match = cid.split('-', 1)[1]
            cache = SimpleNamespace(match_id=match, frames=lambda: [], reference=np.array([], np.uint8))
            with patch('gap_solver.skillcorner.load_motion_cache', return_value=cache) as loader:
                se_load.load(cid)
                loader.assert_called_once_with(expected_root / 'cache' / (match + '-detected'))

    def test_case_readable_by_both_existing_training_readers(self):
        case = self.case
        prep.validate_case(case, case['ref'], case['period'], case['names'].tolist())
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'cases').mkdir()
            p = root / 'cases' / (ADDITIONAL_CASES[0] + '.npz')
            np.savez_compressed(p, **case)
            gbm = reader_from_source('se_train.py', 'load', {'np': np, 'PRIVATE': root})
            keep = list(range(len(case['names'])))
            X, ref, per, observed = gbm(ADDITIONAL_CASES[0], keep)
            for a, b in zip((X, ref, per, observed), (case['X'], case['ref'], case['period'], case['observed'])):
                np.testing.assert_array_equal(a, b)
            gru = reader_from_source('se_gru.py', 'load_path', {'np': np, 'KEEP_NAMES': None, 'XDROP': ()})
            X, ref, per, names = gru(p)
            np.testing.assert_array_equal(X, case['X'])
            np.testing.assert_array_equal(ref, case['ref'])
            np.testing.assert_array_equal(per, case['period'])
            self.assertEqual(names, case['names'].tolist())
            self.assertNotIn('release_sup', case)

    def test_nonfinite_features_and_invented_dead_ball_labels_rejected(self):
        case = {k: v.copy() for k, v in self.case.items()}
        case['X'][0, 0] = np.inf
        with self.assertRaisesRegex(ValueError, 'Non-finite'):
            prep.validate_case(case, case['ref'], case['period'], case['names'].tolist())
        case['X'][0, 0] = 0
        case['ref'][0] = 2
        with self.assertRaisesRegex(ValueError, 'invented D'):
            prep.validate_case(case, case['ref'], case['period'], case['names'].tolist())

    def test_feature_order_and_reference_alignment_rejected(self):
        case = {k: v.copy() for k, v in self.case.items()}
        names = case['names'].tolist()
        case['names'][0], case['names'][1] = case['names'][1], case['names'][0]
        with self.assertRaisesRegex(ValueError, 'names/order'):
            prep.validate_case(case, case['ref'], case['period'], names)
        case['names'] = self.case['names']
        reference = case['ref'].copy()
        reference[0] = 1
        with self.assertRaisesRegex(ValueError, 'alignment'):
            prep.validate_case(case, reference, case['period'], names)


if __name__ == '__main__':
    unittest.main()
