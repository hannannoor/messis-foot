import tempfile
import csv
import inspect
import unittest
from pathlib import Path

from gap_solver.io import load_atd, load_tags, read_evidence, write_outputs
from gap_solver.core import Frame, infer
from gap_solver import io


META = '<root><Team id="h"><Name>Barcelona</Name></Team><Team id="a"><Name>Atletic Club</Name></Team><Player teamId="h"/><Player teamId="a"/></root>'


class Adapters(unittest.TestCase):
    def test_audit_labels_extend_existing_diagnostics_without_extra_prediction_files(self):
        self.assertIn('audit_stages', inspect.signature(write_outputs).parameters)
        frames = [Frame()]*4
        from gap_solver.core import Decision
        stages = {'legacy_tactical':[Decision(x) for x in 'HXXH'],
                  'restart_repaired':[Decision('H')]*4,
                  'published_context':[Decision('H')]*4}
        write_outputs(self.root, frames, stages['published_context'], audit_stages=stages)
        with (self.root/'diagnostics.csv').open(newline='') as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(rows[1]['legacy_tactical_label'], 'X')
        self.assertEqual(rows[1]['scorer_legacy_tactical_label'], 'H')
        self.assertEqual(rows[1]['scorer_final_label'], 'H')
        self.assertEqual(len(list(self.root.glob('submission*.csv'))), 1)

    def test_published_dead_interval_is_exact_and_keeps_input_unchanged(self):
        apply = getattr(io, 'apply_published_dead', None)
        self.assertIsNotNone(apply, 'missing published context adapter')
        frames = [Frame(period=0)] * 199319
        frames[110808:190198] = [Frame(period=2)] * (190198-110808)
        corrected = apply(frames)
        self.assertFalse(corrected[110807].dead_evidence)
        self.assertTrue(corrected[110808].dead_evidence)
        self.assertTrue(corrected[113741].dead_evidence)
        self.assertFalse(corrected[113742].dead_evidence)
        self.assertFalse(frames[110808].dead_evidence)
        self.assertEqual(sum(f.dead_evidence for f in corrected), 2934)
        self.assertEqual(infer(corrected)[110808].reason, 'published_pre_kickoff')

    def test_published_context_rejects_foreign_dimensions_and_halves(self):
        apply = getattr(io, 'apply_published_dead', None)
        self.assertIsNotNone(apply, 'missing published context adapter')
        for frames in ([Frame()] * 10, [Frame(period=1)] * 199319):
            with self.assertRaises(ValueError):
                apply(frames)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.meta = self.root / 'meta.xml'
        self.meta.write_text(META)

    def tearDown(self):
        self.tmp.cleanup()

    def test_atd_uses_metres_and_zero_based_submission_index(self):
        raw = self.root / 'raw.txt'
        raw.write_text('1:0.1,0.2,0;0.8,0.2,0:0.11,0.2,0\n2:0.1,0.2,0;0.8,0.2,0:NaN,NaN,NaN\n')
        frames, names = load_atd(self.meta, raw, n_frames=2, blocks=[(1, 0, 1)])
        self.assertAlmostEqual(frames[0].home_distance, 1.053)
        self.assertFalse(frames[1].ball_observed)
        self.assertEqual(names, ('Barcelona', 'Atletic Club'))

    def test_out_of_order_or_wrong_slot_count_is_rejected(self):
        raw = self.root / 'raw.txt'
        for text in ['2:0,0,0;1,1,0:0,0,0\n', '1:0,0,0:0,0,0\n']:
            raw.write_text(text)
            with self.assertRaises(ValueError):
                load_atd(self.meta, raw, n_frames=1, blocks=[(1, 0, 0)])

    def test_missing_entire_team_is_not_treated_as_far_away(self):
        raw = self.root / 'raw.txt'
        raw.write_text('1:0.1,0.2,0;NaN,NaN,NaN:0.11,0.2,0\n')
        frames, _ = load_atd(self.meta, raw, n_frames=1, blocks=[(1, 0, 0)])
        self.assertIsNone(frames[0].away_distance)

    def test_defending_tags_support_opponent_and_throwins_only_flag_restart(self):
        xml = self.root / 'tags.xml'
        xml.write_text('''<root><instance><start>0</start><end>0.4</end><code>DEFENDING IN MIDDLE THIRD</code><label><group>Team</group><text>Atletic Club</text></label></instance><instance><start>0.4</start><end>0.8</end><code>SET PIECES</code><label><group>Team</group><text>N/A</text></label></instance></root>''')
        frames = load_tags(xml, [Frame()] * 20, ('Barcelona', 'Atletic Club'))
        self.assertEqual(frames[0].tag_team, 'H')
        self.assertEqual(frames[10].tag_team, '')
        self.assertTrue(frames[10].restart_hint)
        self.assertFalse(frames[10].dead_evidence)

    def test_contradictory_phases_are_retained_as_conflict(self):
        xml = self.root / 'tags.xml'
        xml.write_text('''<root><instance><start>0</start><end>1</end><code>BUILD UP</code><label><group>Team</group><text>Barcelona</text></label></instance><instance><start>0</start><end>1</end><code>PROGRESSION</code><label><group>Team</group><text>Atletic Club</text></label></instance></root>''')
        self.assertEqual(load_tags(xml, [Frame()], ('Barcelona', 'Atletic Club'))[0].tag_team, 'CONFLICT')

    def test_provider_aliases_follow_metadata_team_order(self):
        xml = self.root / 'tags.xml'
        xml.write_text('''<root><instance><start>0</start><end>1</end><code>BUILD UP</code><label><group>Team</group><text>Barcelona</text></label></instance></root>''')
        self.assertEqual(load_tags(xml, [Frame()], ('Athletic Club', 'FC Barcelona'))[0].tag_team, 'A')

    def test_evidence_frame_sequence_and_boolean_values_are_checked(self):
        path = self.root / 'evidence.csv'
        path.write_text('frame,period,dead_evidence\n0,1,False\n1,1,true\n')
        frames = read_evidence(path)
        self.assertFalse(frames[0].dead_evidence)
        self.assertTrue(frames[1].dead_evidence)
        path.write_text('frame,period\n1,1\n')
        with self.assertRaises(ValueError):
            read_evidence(path)

    def test_output_contract_and_diagnostics(self):
        frames = [Frame()] * 20
        write_outputs(self.root, frames, infer(frames))
        lines = (self.root / 'submission.csv').read_text().splitlines()
        self.assertEqual(lines[0], 'frame,label')
        self.assertEqual(lines[-1], '19,X')
        self.assertTrue((self.root / 'unresolved_intervals.json').is_file())
