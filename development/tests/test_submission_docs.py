"""Synthetic aggregate contracts and, after release, submission-document guards."""
from pathlib import Path
import json
import re
import tempfile
import unittest


class AggregateContracts(unittest.TestCase):
    def test_reporting_tag_transition_uses_first_transition_and_period(self):
        import restart_provided_aggregates as a
        xml = ('<root><instance><code>SET PIECES</code><start>4</start><end>5</end>'
               '<label><group>Team</group><text>FC Barcelona</text></label>'
               '<label><group>Type</group><text>Corner</text></label></instance></root>')
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'tags.xml'; path.write_text(xml)
            labels = ['D']*110 + ['A']*20 + ['D']*20 + ['H']*100
            value = a.tag_check(path, [1]*len(labels), labels)
            self.assertEqual(value['total'], dict(match=0, mismatch=1, no_transition=0))
            self.assertEqual(value['by_type']['CORNER'], value['total'])
            self.assertEqual(a.tag_check(path, [1]*len(labels), ['D']*len(labels))['total']['no_transition'], 1)
            boundary = a.tag_check(path, [1]*100+[2]*(len(labels)-100), ['D']*100+['H']*(len(labels)-100))
            self.assertEqual(boundary['total']['no_transition'], 1)

    def test_spell_statistics_split_period_and_unknown(self):
        import restart_provided_aggregates as a
        from gap_solver.motion import motion_frame
        frames = [motion_frame(p, None, (), ()) for p in [1]*5+[2]*5]
        value = a.label_stats(frames, tuple('HHXAAHHHHH'))
        self.assertEqual(value['spells'], 3)
        self.assertEqual(value['median_spell'], 2)
        self.assertEqual(value['spells_under_25'], 3)
        self.assertEqual(value['spells_under_50'], 3)

    def test_gap_support_quantiles_and_near_threshold_frame_share(self):
        import gap_support_aggregates as a
        values = [None]*30
        values[0:4] = [.5, .5, .5, None]
        values[10:14] = [.95, None, None, None]
        values[20:24] = [1.1, 1.1, None, None]
        result = a.support_summary(values, ((0,4),(10,14),(20,24)), ((0,4),(10,14)), 1.)
        chosen = result['relabelled']
        self.assertEqual(chosen['gaps'], 2)
        self.assertEqual(chosen['minimum_samples'], 1)
        self.assertEqual(chosen['p10_samples'], 1)
        self.assertEqual(chosen['median_samples'], 2)
        self.assertEqual(chosen['fewer_than_5_samples'], 2)
        self.assertEqual(chosen['no_samples'], 0)
        self.assertEqual(chosen['near_threshold_gaps'], 1)
        self.assertEqual(chosen['near_threshold_frame_share'], .5)
        values[10] = .9
        self.assertEqual(a.support_summary(values, ((0,4),(10,14)), ((0,4),(10,14)), 1.)['relabelled']['near_threshold_gaps'], 0)


class SubmissionDocs(unittest.TestCase):
    root = Path(__file__).resolve().parents[1]

    def test_first_readme_command_is_the_restart_release(self):
        source = (self.root/'README.md').read_text(encoding='utf-8')
        command = re.search(r'```[^\n]*\n(.*?)```', source, re.S).group(1)
        self.assertIn('restart_release.py', command)

    def test_full_hash_matches_decision_and_status(self):
        decision = json.loads((self.root/'reports/submission/release-decision.json').read_text())
        expected = decision['csv_sha256']
        self.assertRegex(expected, r'^[0-9a-f]{64}$')
        for name in ('README.md', 'docs/technical-document.md'):
            self.assertIn(expected, (self.root/name).read_text(encoding='utf-8'))
        design = (self.root/'DESIGN.md').read_text(encoding='utf-8')
        status = re.search(r'## Status\s*\n\n([^\n]+)', design).group(1)
        self.assertIn(expected, status)

    def test_technical_document_pins_code_and_uses_absolute_links(self):
        decision = json.loads((self.root/'reports/submission/release-decision.json').read_text())
        source = (self.root/'docs/technical-document.md').read_text(encoding='utf-8')
        for text in ('Smart Tagging', 'Kick Off (Start)', decision['release_code_commit']):
            self.assertIn(text, source)
        for target in re.findall(r'\]\(([^)]+)\)', source):
            self.assertTrue(target.startswith('https://'), target)
        for placeholder in ('H_STAR','C_STAR','PROVIDED_EVIDENCE','PUBLIC_EVIDENCE','SUPPORT_EVIDENCE','SET_PIECE_EVIDENCE'):
            self.assertNotIn(placeholder, source)

    def test_stale_kickoff_offset_and_universal_safety_claim_are_removed(self):
        for name in ('DESIGN.md', 'docs/technical-document.md'):
            source = (self.root/name).read_text(encoding='utf-8')
            self.assertNotIn('82 frames', source)
            if name == 'DESIGN.md':
                self.assertNotIn('safe in every regime', source)

    def test_documents_are_cleanly_encoded_and_free_of_internal_notes(self):
        # UTF-8 text decoded as cp1252 and saved again shows up as these lead characters followed by a continuation.
        garbled = re.compile('[\u00c2\u00c3\u00e2][\u0080-\u00bf\u02c6\u02dc\u2018-\u203a\u20ac]')
        for name in ('README.md', 'DESIGN.md', 'docs/technical-document.md'):
            source = (self.root/name).read_bytes().decode('utf-8')
            self.assertIsNone(garbled.search(source), name)
        document = (self.root/'docs/technical-document.md').read_text(encoding='utf-8')
        for note in ('Team to confirm', 'is pushed', 'has been published'):
            self.assertNotIn(note, document)
        self.assertNotIn('/tree/codex/', document)
