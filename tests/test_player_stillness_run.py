"""Experiment E: matched 20-column training, ledger identities, protocol constants, case pipeline. Synthetic only."""
import importlib.util
import tempfile
import unittest
from pathlib import Path

import numpy as np

from memory_ablation_training import prepare_training, semantic_digest
from test_team_shape_training import groups

try:
    import player_stillness_training as pt
    import player_stillness_run as run
except ImportError:
    pt = run = None

HAS_SKLEARN = importlib.util.find_spec('sklearn') is not None


class Training(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(pt, 'player_stillness modules are missing')

    def test_candidate_prefix_equals_control_and_rows_match(self):
        g = groups()
        pair = pt.prepare_pair(g)
        old = prepare_training([dict(v, frames=v['cache_frames']) for v in g])
        self.assertEqual(pair.candidate.matrix.shape, (len(old.matrix), 20))
        self.assertEqual(semantic_digest(pair.control.matrix), semantic_digest(old.matrix))
        self.assertEqual(semantic_digest(pair.candidate.matrix[:, :18]), semantic_digest(old.matrix))
        for name in ('target', 'weights', 'row_identity'):
            np.testing.assert_array_equal(getattr(pair.control, name), getattr(pair.candidate, name))

    def test_appended_columns_are_the_two_stillness_features(self):
        self.assertEqual(pt.APPENDED, (18, 19))
        self.assertEqual(pt.RESEARCH_FEATURE_NAMES[18:], ('still_share', 'still_support'))

    @unittest.skipUnless(HAS_SKLEARN, 'pinned training interpreter only')
    def test_unused_new_columns_stop(self):
        g = groups()
        pair = pt.prepare_pair(g)
        with self.assertRaises((pt.UnusedRepresentation, pt.ControlMismatch)):
            pt.fit_research(pair.control, pair.candidate, lambda mode: None, expected_control_sha=None)


class Harness(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(run, 'player_stillness_run is missing')
        self.tmp = tempfile.TemporaryDirectory()
        self.ledger = run.Ledger(Path(self.tmp.name) / 'claims', Path(self.tmp.name) / 'access.jsonl')

    def tearDown(self):
        self.tmp.cleanup()

    def test_parity_identities_are_run_scoped(self):
        for identity in ('training-alignment/2026-11-12-a/J03WOH', 'training-fit/2026-11-12-a/J03WOH',
                         'exporter/2026-11-12-a', 'release/2026-11-12-a/dfl-J03WR9', 'prefix/2026-11-12-a/dfl-J03WR9'):
            self.ledger.claim('parity', identity)
        for bad in ('release/dfl-J03WR9', 'prefix/2026-11-12-a/nope', 'training-fit/2026-11-12-a/J03WQQ', 'exporter'):
            with self.assertRaises((run.BudgetError, ValueError)):
                self.ledger.claim('parity', bad)
        self.assertEqual(self.ledger.count('parity'), 5)

    def test_protocol_parameters_pin_constants(self):
        p = run.protocol_parameters()
        self.assertEqual((p['speed_lag'], p['still_speed'], p['window'], p['min_players']), (5, 1.0, 50, 14))
        self.assertEqual(p['jitter_prefix'], 'player-stillness-jitter-v1:1729:')
        self.assertEqual(p['experiment'], 'player-stillness-2026-11-12')
        self.assertNotIn('closing_radius', p)

    def test_case_receipt_passes_report_guard(self):
        from test_gap_liveness import fixture
        from gap_solver.tactical_model import FROZEN_MODEL
        import player_stillness_features as ps
        frames = fixture(gaps=((300, 500),), players=20)
        matrix = ps.stillness_matrix(frames)
        reference = np.array([0] * 300 + [2] * 200 + [0] * 400, np.uint8)
        candidate = dict(FROZEN_MODEL['model'])
        # a 20-column stand-in tree: the frozen tree's structure with the research schema
        candidate['feature_names'] = list(pt.RESEARCH_FEATURE_NAMES)
        models = dict(control=FROZEN_MODEL['model'], candidate=candidate)
        receipt = run.run_case_regime(self.ledger, 'natural', 'dfl-J03WR9', frames, reference, models,
                                      Path(self.tmp.name) / 'case', matrix=matrix)
        from accuracy_evidence import assert_public_report
        assert_public_report(receipt)
        self.assertEqual(self.ledger.count('prediction'), 2)


if __name__ == '__main__':
    unittest.main()
