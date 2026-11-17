import importlib
import importlib.util
import unittest
from dataclasses import replace

from gap_solver.core import Decision, Frame, infer


class ControlledAudit(unittest.TestCase):
    def module(self):
        self.assertIsNotNone(importlib.util.find_spec('gap_solver.audit'), 'missing audit module')
        return importlib.import_module('gap_solver.audit')

    def test_scorer_expansion_respects_half_heads_and_ungraded_gaps(self):
        audit = self.module()
        frames = [Frame(period=1)]*5 + [Frame(period=0)] + [Frame(period=2)]*4
        decisions = [Decision(label) for label in 'XXHXAXXXDX']
        self.assertEqual(audit.scorer_expanded_labels(frames, decisions), list('HHHHAXDDDD'))
        self.assertEqual(audit.scorer_expanded_labels([Frame()]*3, [Decision()]*3), ['X']*3)

    def test_more_assignments_can_have_no_effect_after_scorer_expansion(self):
        audit = self.module()
        frames = [Frame()]*4
        before = [Decision(x) for x in 'HXXH']
        after = [Decision('H')]*4
        report = audit.compare_decisions(frames, before, after)
        self.assertEqual(report['raw_label_changes'], 2)
        self.assertEqual(report['scorer_expanded_label_changes'], 0)
        self.assertEqual(report['raw_changes_without_scorer_effect'], 2)

    def test_first_anchor_can_change_surrounding_unchanged_raw_frames(self):
        audit = self.module()
        report = audit.compare_decisions([Frame()]*4,
                                         [Decision(x) for x in 'XXXH'],
                                         [Decision(x) for x in 'AXXH'])
        self.assertEqual(report['raw_label_changes'], 1)
        self.assertEqual(report['scorer_expanded_label_changes'], 3)
        self.assertEqual(report['propagated_changes_on_raw_unchanged_frames'], 2)
        self.assertEqual(report['possession_spells_before'], 1)
        self.assertEqual(report['possession_spells_after'], 2)

    def test_audit_rejects_truncated_or_different_half_inputs(self):
        audit = self.module()
        with self.assertRaises(ValueError):
            audit.scorer_expanded_labels([Frame()], [])
        with self.assertRaises(ValueError):
            audit.build_baseline_audit([Frame(period=1)], [Frame(period=2)], [Decision()])

    def test_restart_and_published_context_changes_are_isolated(self):
        audit = self.module()
        raw = [Frame(ball_x=10, ball_y=10, home_distance=.5, away_distance=8,
                     restart_hint=True)]*10
        corrected = raw[:6] + [replace(f, dead_evidence=True, dead_source='published_pre_kickoff')
                                   for f in raw[6:]]
        report, stages = audit.build_baseline_audit(raw, corrected, infer(corrected))
        self.assertEqual(report['stages']['legacy_tactical']['labels']['X'], 10)
        self.assertEqual(report['stages']['restart_repaired']['labels']['H'], 10)
        self.assertEqual(report['stages']['published_context']['labels']['D'], 4)
        self.assertEqual(report['comparisons']['restart_repair']['raw_label_changes'], 10)
        self.assertEqual(report['comparisons']['published_context']['raw_label_changes'], 4)
        self.assertEqual(report['comparisons']['broadcast_fusion']['raw_label_changes'], 0)
        self.assertEqual(len(stages['legacy_tactical']), 10)

    def test_gap_diagnostics_explain_existing_bridge_limits(self):
        audit = self.module()
        anchor = [Frame(ball_x=10, ball_y=10, home_distance=.5, away_distance=8)]*8
        long_gap = anchor + [Frame()]*30 + anchor
        report = audit.bridge_diagnostics(long_gap, infer(long_gap))
        self.assertEqual(report['intervals_by_cause'], {'duration_or_tag_support': 1})
        self.assertEqual(report['unresolved_missing_ball_frames'], 30)
        restart_gap = anchor + [Frame(restart_hint=True)]*5 + anchor
        self.assertEqual(audit.bridge_diagnostics(restart_gap, infer(restart_gap))['intervals_by_cause'],
                         {'restart_or_dead_context': 1})
