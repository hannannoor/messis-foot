"""Experiment G run harness: ledger identities, protocol constants, cut-offs, repository guard, rule receipt. Synthetic only."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import subprocess
import tempfile
import unittest

import numpy as np

from gap_solver.tactical import feature_rows
from gap_solver.tactical_model import FROZEN_MODEL
from test_gap_liveness import fixture

try:
    import pair_costs_run as run
except ImportError:
    run = None

LOCAL = timezone(timedelta(hours=8))
PRIOR = ((0., 27.5, 33.3), (26.8, 0., 33.1), (35.5, 35.9, 0.))


class Harness(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(run, 'pair_costs_run is missing')
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.ledger = run.Ledger(Path(self.tmp.name) / 'claims', Path(self.tmp.name) / 'access.jsonl')

    def test_parity_identities_run_scoped(self):
        for identity in ('equivalence/run-a/dfl-J03WR9', 'release/run-a/dfl-J03WR9', 'training-rule/run-a'):
            self.ledger.claim('parity', identity)
        for bad in ('release/dfl-J03WR9', 'equivalence/run-a/nope', 'training-rule/BAD', 'still-supports/run-a/dfl-J03WR9'):
            with self.assertRaises(run.BudgetError):
                self.ledger.claim('parity', bad)
        self.assertEqual(self.ledger.count('parity'), 3)

    def test_protocol_parameters_pin_mean_and_matches(self):
        p = run.protocol_parameters()
        self.assertEqual(p['mean_cost'], 32.)
        self.assertEqual(p['training_matches'], 'J03WOH,J03WOY,J03WPY,J03WMX')
        self.assertEqual(p['short_spell_threshold'], 23)
        self.assertEqual(p['jitter_prefix'], 'pair-costs-jitter-v1:1729:')
        self.assertEqual(p['experiment'], 'pair-costs-2026-11-12')
        self.assertEqual(p['caps']['fits'], 0)

    def test_cutoffs_are_15_and_16_november(self):
        run.enforce_cutoff('natural', datetime(2026, 11, 15, 23, 59, tzinfo=LOCAL))
        with self.assertRaises(ValueError):
            run.enforce_cutoff('natural', datetime(2026, 11, 16, 0, 0, tzinfo=LOCAL))
        run.enforce_cutoff('stress', datetime(2026, 11, 16, 12, 0, tzinfo=LOCAL))
        with self.assertRaises(ValueError):
            run.enforce_cutoff('stress', datetime(2026, 11, 16, 12, 1, tzinfo=LOCAL))
        p = run.protocol_parameters()
        self.assertEqual((p['stage1_cutoff_local'], p['full_cutoff_local']), ('2026-11-15T23:59', '2026-11-16T12:00'))

    def test_check_repository_rejects_foreign_file(self):
        repo = Path(self.tmp.name) / 'repo'
        repo.mkdir()

        def git(*args):
            return subprocess.check_output(['git', '-c', 'user.name=T', '-c', 'user.email=t@example.invalid', *args],
                                           cwd=repo, text=True, stderr=subprocess.DEVNULL).strip()
        git('init', '-q')
        git('checkout', '-q', '-b', run.BRANCH)
        (repo / 'old.py').write_text('x=1\n')
        git('add', '.')
        git('commit', '-q', '-m', 'base')
        base = git('rev-parse', 'HEAD')
        for name in ('pair_x.py', 'tests/test_pair_x.py', 'docs/pair-costs-protocol.md', 'reports/pair-costs/a.md', '.gitignore'):
            (repo / name).parent.mkdir(parents=True, exist_ok=True)
            (repo / name).write_text('y\n')
        git('add', '.')
        git('commit', '-q', '-m', 'allowed')
        self.assertEqual(run.check_repository(root=repo, base=base), git('rev-parse', 'HEAD'))
        (repo / 'old.py').write_text('x=2\n')
        git('commit', '-q', '-am', 'foreign')
        with self.assertRaisesRegex(ValueError, 'Existing files changed'):
            run.check_repository(root=repo, base=base)

    def test_training_rule_records_aggregates_only(self):
        from accuracy_evidence import assert_public_report
        ref = np.array([0, 0, 1, 1, 0, 2, 2, 0, 0, 1, 2, 1, 1, 2, 2, 2, 0])
        groups = [dict(reference=ref, periods=np.ones(len(ref), int))]
        rule = run.training_rule(self.ledger, 'run-a', groups=groups)
        self.assertEqual(set(rule), {'matrix', 'counts', 'q', 'mean'})
        assert_public_report(rule)
        self.assertEqual(set(rule['matrix']), {'HA', 'HD', 'AH', 'AD', 'DH', 'DA'})
        self.assertEqual(len(rule['counts']), 9)
        self.assertEqual(run.cost_matrix_of(dict(pair_costs=rule))[0][1], rule['matrix']['HA'])
        self.assertEqual(self.ledger.count('parity'), 1)

    def test_case_pipeline_uses_matrix_for_candidate_only(self):
        from accuracy_evidence import assert_public_report
        frames = fixture(gaps=((300, 500),))
        matrix = np.asarray(list(feature_rows(frames)), dtype=np.float32)
        reference = np.array([0] * 300 + [2] * 200 + [0] * 400, np.uint8)
        receipt = run.run_case_regime(self.ledger, 'natural', 'dfl-J03WR9', frames, reference, FROZEN_MODEL['model'],
                                      Path(self.tmp.name) / 'case', matrix=matrix, cost_matrix=PRIOR)
        self.assertEqual(self.ledger.count('prediction'), 2)
        self.assertEqual(self.ledger.count('decoder_pass'), 4)
        self.assertEqual(self.ledger.count('feature_pass'), 2)
        self.assertEqual(set(receipt['short_spells']), {'control', 'candidate'})
        self.assertEqual(receipt['short_spell_threshold'], 23)
        assert_public_report(receipt)
        with self.assertRaises(ValueError):
            run.run_case_regime(self.ledger, 'natural', 'dfl-J03WN1', frames, reference, FROZEN_MODEL['model'],
                                Path(self.tmp.name) / 'case2', matrix=matrix, cost_matrix=None)


if __name__ == '__main__':
    unittest.main()
