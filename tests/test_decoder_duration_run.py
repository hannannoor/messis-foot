"""Experiment D run harness: ledger identities, protocol constants, one case pipeline. Synthetic only."""
import tempfile
import unittest
from pathlib import Path

import numpy as np

from gap_solver.tactical import feature_rows
from gap_solver.tactical_model import FROZEN_MODEL
from test_gap_liveness import fixture

try:
    import decoder_duration_run as run
except ImportError:
    run = None


class Harness(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(run, 'decoder_duration_run is missing')
        self.tmp = tempfile.TemporaryDirectory()
        self.ledger = run.Ledger(Path(self.tmp.name) / 'claims', Path(self.tmp.name) / 'access.jsonl')

    def tearDown(self):
        self.tmp.cleanup()

    def test_parity_identities_are_run_scoped_and_bounded(self):
        self.ledger.claim('parity', 'equivalence/2026-11-12-a/dfl-J03WR9')
        self.ledger.claim('parity', 'release/2026-11-12-a/dfl-J03WR9')
        self.ledger.claim('parity', 'training-rule/2026-11-12-a')
        self.ledger.claim('parity', 'equivalence/2026-11-12-b/dfl-J03WR9')
        for bad in ('equivalence/2026-11-12-a/not-a-case', 'swap/dfl-J03WR9', 'release/dfl-J03WR9', 'training-rule/BAD'):
            with self.assertRaises(run.BudgetError):
                self.ledger.claim('parity', bad)
        with self.assertRaises(run.BudgetError):
            self.ledger.claim('parity', 'training-rule/2026-11-12-a')
        self.assertEqual(self.ledger.count('parity'), 4)
        self.assertEqual(self.ledger.count('score'), 0)

    def test_protocol_parameters_pin_constants(self):
        p = run.protocol_parameters()
        self.assertEqual(p['extra'], 32.)
        self.assertEqual(p['min_run_rule'], 'nearest-rank p10 of pooled DFL training reference runs (H/A/D, periods 1-2), clamp [5,50]')
        self.assertEqual(p['jitter_prefix'], 'decoder-duration-jitter-v1:1729:')
        self.assertEqual(p['caps']['fits'], 0)
        self.assertEqual(p['training_matches'], 'J03WOH,J03WOY,J03WPY,J03WMX')

    def test_short_spell_counts(self):
        final = np.array([0] * 20 + [1] * 3 + [0] * 10 + [2] * 2 + [1] * 30 + [3] * 5, np.uint8)
        periods = np.array([1] * 65 + [0] * 5, np.uint8)
        self.assertEqual(run.short_spell_counts(final, periods, 12), dict(spells=5, shorter_than_min_run=3))

    def test_case_pipeline_claims_budget_and_uses_the_duration_decoder_for_candidate_only(self):
        frames = fixture(gaps=((300, 500),))
        matrix = np.asarray(list(feature_rows(frames)), dtype=np.float32)
        reference = np.array([0] * 300 + [2] * 200 + [0] * 400, np.uint8)
        receipt = run.run_case_regime(self.ledger, 'natural', 'dfl-J03WR9', frames, reference, FROZEN_MODEL['model'],
                                      Path(self.tmp.name) / 'case', matrix=matrix, min_run=12)
        self.assertEqual(self.ledger.count('prediction'), 2)
        self.assertEqual(self.ledger.count('decoder_pass'), 4)
        self.assertEqual(self.ledger.count('score'), 2)
        self.assertEqual(self.ledger.count('feature_pass'), 2)
        self.assertEqual(set(receipt['short_spells']), {'control', 'candidate'})
        from accuracy_evidence import assert_public_report
        assert_public_report(receipt)

    def test_case_pipeline_refuses_missing_min_run(self):
        frames = fixture(gaps=())
        matrix = np.asarray(list(feature_rows(frames)), dtype=np.float32)
        with self.assertRaises(ValueError):
            run.run_case_regime(self.ledger, 'natural', 'dfl-J03WR9', frames, np.zeros(len(frames), np.uint8),
                                FROZEN_MODEL['model'], Path(self.tmp.name) / 'case', matrix=matrix, min_run=None)


if __name__ == '__main__':
    unittest.main()
