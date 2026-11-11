"""Release parity, restart mechanism and deterministic export on synthetic inputs."""
import ast
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from gap_liveness import apply_gap_rule
from gap_release import assemble as old_assemble
from gap_solver.materialization_control import materialize_abstentions
from release_runtime import load_source, predict_selected, submission_bytes
from touch_decoder import decode_variable
from touch_evidence import prepare_evidence
from touch_transfer import restart_decode
from test_gap_liveness import fixture
import restart_release as r

ROOT = Path(__file__).resolve().parents[1]


class RestartRelease(unittest.TestCase):
    def test_parity_with_experiment_and_disabled_candidate(self):
        for frames in (fixture(), fixture(gaps=()), fixture(gap_speed=4.)):
            control = predict_selected(frames).labels
            prepared = prepare_evidence(frames, [], 0, 32)
            rows, costs, periods, usable, _ = prepared
            expected, _ = restart_decode(frames, rows, periods, usable, costs, control)
            actual = r.assemble(frames, ())
            self.assertEqual(actual.restarted, expected.labels)
            disabled = r.assemble(frames, (), use_restart=False)
            self.assertEqual(disabled.final, old_assemble(frames, control, ()).final)

    def test_no_stoppage_is_identity(self):
        frames = fixture(gaps=())
        self.assertEqual(r.assemble(frames, ()).final, r.assemble(frames, (), use_restart=False).final)

    def test_restart_changes_first_post_gap_owner(self):
        frames = fixture()
        rows = [(0., -10., -20.)]*300 + [(0.,)*3]*200 + [(-2., 0., -20.)]*20 + [(0., -10., -20.)]*380
        periods, usable, costs = [1]*900, [True]*900, [(32.,)*3]*900
        control = tuple(materialize_abstentions(decode_variable(rows, periods, usable, costs), periods))
        prepared = rows, costs, periods, usable, {}
        first, second, flags = r.decode_stoppages(frames, control, prepared)
        self.assertEqual(first.labels[500], 'H')
        self.assertEqual(second.labels[500], 'A')
        self.assertEqual(flags[300:500], [False]*200)
        self.assertEqual(first.stoppage_gaps, second.stoppage_gaps)

    def test_parity_failure_is_refused(self):
        frames = fixture(gaps=())
        prepared = prepare_evidence(frames, [], 0, 32)
        with self.assertRaises(ValueError):
            r.decode_stoppages(frames, ('X',)*len(frames), prepared)

    def test_two_exports_identical_and_existing_output_refused(self):
        frames = fixture()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tags = root/'tags.xml'; tags.write_text('<root/>')
            with patch('release_runtime.load_source', return_value=(frames, {})):
                a = r.generate('synthetic', tags, root/'one')
                b = r.generate('synthetic', tags, root/'two')
                self.assertEqual((root/'one/submission.csv').read_bytes(), (root/'two/submission.csv').read_bytes())
                self.assertEqual(a, b)
                self.assertEqual(a['rows'], len(frames))
                self.assertEqual(a['stoppage_gaps'], 1)
                with self.assertRaises(FileExistsError):
                    r.generate('synthetic', tags, root/'one')

    def test_module_is_standard_library_and_no_truth_or_experiment_import(self):
        source = (ROOT/'restart_release.py').read_text(encoding='utf-8')
        tree = ast.parse(source)
        allowed = {'argparse','dataclasses','hashlib','json','pathlib','sys','gap_liveness','gap_release',
                   'kickoff_patch','release_runtime','touch_decoder','touch_evidence','gap_solver'}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                self.assertTrue(all(x.name.split('.')[0] in allowed for x in node.names))
            elif isinstance(node, ast.ImportFrom):
                self.assertIn(node.module.split('.')[0], allowed)
        for forbidden in ('touch_transfer','ground_truth','gt_public','read_label_csv'):
            self.assertNotIn(forbidden, source)

    def test_provided_disabled_csv_reproduces_existing_candidate(self):
        handling = ROOT/'.superpowers/release/target-handling.json'
        if not handling.exists():
            self.skipTest('Local provided inputs absent')
        prefix = json.loads(handling.read_text(encoding='utf-8'))['input_prefix']
        if not Path(prefix+'_atd.txt').exists():
            self.skipTest('Local provided inputs absent')
        from kickoff_patch import kickoff_starts
        frames, _ = load_source(*(Path(prefix+s) for s in ('_atd.xml','_atd.txt','_homography.csv')))
        labels = r.assemble(frames, kickoff_starts(prefix+'_smart_tagging.xml'), use_restart=False).final
        self.assertEqual(hashlib.sha256(submission_bytes(labels)).hexdigest(),
                         '31b947d3b250b6267a7d8f0aac0c4e4eafd82a4fc873c82759806e676b1bf963')


if __name__ == '__main__':
    unittest.main()
