import csv
from dataclasses import replace
import tempfile
import unittest
from pathlib import Path

from release_fixtures import release_fixture
from gap_solver.motion import motion_frame
from gap_solver.tactical import PortableTree, FEATURE_NAMES, feature_rows
from gap_solver.tactical_model import FROZEN_MODEL
from gap_solver.soft_sequence import sequence_usable
from gap_solver.materialization_control import materialize_abstentions
from ball_gap_policy import decode_ball_gap
import ball_gap_candidate
import soft_candidate as incumbent

try:
    import release_runtime as runtime
except ImportError:
    runtime = None


def incumbent_path(inputs):
    contract = incumbent.read_epts_contract(inputs[0])
    frames = list(incumbent.iter_records(contract, inputs[1], [(1, 0, contract.rows-1)]))
    mask = incumbent.quality_mask(inputs[2], len(frames))
    frames = [f if ok else replace(f, geometry_valid=False) for f, ok in zip(frames, mask)]
    frames, _ = incumbent.associate_anonymous(frames)
    tree = PortableTree(FROZEN_MODEL['model'])
    latent, _ = decode_ball_gap([tree.predict(r) for r in feature_rows(frames)],
        [f.period for f in frames], [sequence_usable(f) for f in frames],
        [f.ball_observed for f in frames])
    return frames, latent


class ReleaseRuntime(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(runtime, 'Selected-only runtime is missing')

    def test_selected_runtime_matches_incumbent_complete_arrays(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for case in ('positive', 'invalid', 'unsupported'):
                with self.subTest(case=case):
                    inputs = release_fixture(root/case, case)
                    ball_gap_candidate.run_source(*inputs, root/(case+'-old'), scope='synthetic')
                    with (root/(case+'-old')/'submission.csv').open(newline='') as handle:
                        old_labels = tuple(row['label'] for row in csv.DictReader(handle))
                    old_frames, old_latent = incumbent_path(inputs)
                    frames, audit = runtime.load_source(*inputs, scope='synthetic')
                    new = runtime.predict_selected(frames)
                    self.assertEqual(frames, old_frames)
                    self.assertEqual(new.labels, old_labels)
                    self.assertEqual(new.latent, tuple(old_latent))
                    self.assertEqual(len(new.labels), 500)
                    self.assertEqual(set(new.labels)-set('HADX'), set())
                    self.assertEqual(audit['rows'], 500)
                    if case == 'positive':
                        self.assertEqual(set(new.labels), set('HAD'))
                        self.assertEqual(new.labels[100:200], ('H',)*100)
                    elif case == 'unsupported':
                        self.assertEqual(new.latent, ('X',)*500)
                        self.assertEqual(new.labels, ('D',)*500)

    def test_float32_branch_semantics(self):
        threshold = 1.00000003
        model = dict(feature_names=list(FEATURE_NAMES), children_left=[1,-1,-1],
                     children_right=[2,-1,-1], feature=[0,-2,-2],
                     threshold=[threshold,-2.,-2.], probabilities=[[.5,.5,0.],[1.,0.,0.],[0.,1.,0.]])
        row = [1.00000004] + [0.]*(len(FEATURE_NAMES)-1)
        self.assertGreater(row[0], threshold)
        self.assertEqual(PortableTree(model).predict(row), [1.,0.,0.])

    def test_neutral_tie_order_and_period_reset(self):
        labels, _ = decode_ball_gap([(1/3,1/3,1/3)]*4, [1]*4, [True]*4, [True]*4)
        self.assertEqual(labels, ['H']*4)
        empty = [motion_frame(p, None, [(1.,1.)]*3, [(80.,40.)]*3) for p in (1,1,0,2,2)]
        prediction = runtime.predict_selected(empty)
        self.assertEqual(prediction.latent, tuple('XXXXX'))
        self.assertEqual(prediction.labels, tuple('DDXDD'))
        self.assertEqual(materialize_abstentions(list('HXXXA'), [1,1,0,2,2]), list('HHXAA'))
        frames = [motion_frame(p, (21.,20.), [(21.,20.),(22.,20.),(23.,20.)],
                               [(80.,40.),(81.,40.),(82.,40.)]) for p in ([1]*80+[0]+[2]*80)]
        latent, _ = decode_ball_gap([PortableTree(FROZEN_MODEL['model']).predict(r) for r in feature_rows(frames)],
                    [f.period for f in frames], [sequence_usable(f) for f in frames], [f.ball_observed for f in frames])
        new = runtime.predict_selected(frames)
        self.assertEqual(new.latent, tuple(latent))
        self.assertEqual(new.labels[80], 'X')

    def test_reference_hints_rejected(self):
        frame = motion_frame(1, (1.,2.), [(1.,2.)], [(80.,40.)])
        for hint in ({'tag_team':'H'}, {'restart_hint':True}, {'dead_evidence':True}, {'dead_source':'manual'}):
            with self.subTest(hint=hint), self.assertRaises(ValueError):
                runtime.predict_selected([replace(frame, **hint)])

    def test_semantic_identity_excludes_paths_but_detects_geometry_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            left, _ = runtime.load_source(*release_fixture(root/'a'), scope='synthetic')
            right, _ = runtime.load_source(*release_fixture(root/'b'), scope='synthetic')
            self.assertEqual(runtime.semantic_sha256(left), runtime.semantic_sha256(right))
            changed = [replace(left[0], ball_x=left[0].ball_x+.01), *left[1:]]
            self.assertNotEqual(runtime.semantic_sha256(left), runtime.semantic_sha256(changed))
            with self.assertRaises(ValueError):
                runtime.semantic_sha256([replace(left[0], ball_x=float('nan'))])


if __name__ == '__main__':
    unittest.main()
