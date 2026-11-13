"""Experiment F harness: pinned E artifacts, no fit, run-scoped parity, cut-offs, repository guard. Synthetic only."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

try:
    import missing_evidence_run as run
except ImportError:
    run = None

LOCAL = timezone(timedelta(hours=8))


class Harness(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(run, 'missing_evidence_run is missing')
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.ledger = run.Ledger(Path(self.tmp.name) / 'claims', Path(self.tmp.name) / 'access.jsonl')

    def test_still_model_hash_checked(self):
        from memory_ablation_training import model_digest
        self.assertEqual(run.MODEL_FILES['control'][1], '061780ef57a57e663ef1770ba5e38d97b320550b1ff622c8222ed8c0060e7a47')
        self.assertEqual(run.MODEL_FILES['candidate'][1], '36f78e793e3ad295551743653f43362f51c5cc9dc2d6e7eac130dedff8357ef4')
        models = run.load_models()
        self.assertEqual(model_digest(models['candidate']), '4c5467062e327d11b38f7c34117a9bb33ef853c2faba0ba3efcd9acc2fd69f0e')
        self.assertEqual(model_digest(models['control']), '363c45c70838b398cd87aee7474d7e281fd392f059a31b85712e312058aaab4d')
        copy = Path(self.tmp.name) / 'candidate.json'
        shutil.copyfile(run.MODEL_FILES['candidate'][0], copy)
        copy.write_bytes(copy.read_bytes().replace(b'0', b'1', 1))
        files = dict(run.MODEL_FILES, candidate=(copy, run.MODEL_FILES['candidate'][1]))
        with self.assertRaises(ValueError):
            run.load_models(files)

    def test_no_fit_command(self):
        self.assertNotIn('fit', run.COMMANDS)
        self.assertEqual(run.COMMANDS, ('freeze', 'preflight', 'parity', 'natural', 'stress', 'summarise'))
        self.assertEqual(run.CAPS['fit'], 0)

    def test_parity_identities_run_scoped(self):
        for identity in ('release/run-a/dfl-J03WR9', 'equivalence/run-a/dfl-J03WR9',
                         'still-supports/run-a/dfl-J03WR9', 'prefix/run-a/dfl-J03WR9'):
            self.ledger.claim('parity', identity)
        for bad in ('release/dfl-J03WR9', 'equivalence/run-a/nope', 'exporter/run-a', 'training-fit/run-a/J03WOH'):
            with self.assertRaises((run.BudgetError, ValueError)):
                self.ledger.claim('parity', bad)
        self.assertEqual(self.ledger.count('parity'), 4)

    def test_protocol_parameters_pin_lambda(self):
        p = run.protocol_parameters()
        self.assertEqual(p['lambda'], 0.5)
        self.assertEqual(p['experiment'], 'missing-evidence-2026-11-12')
        self.assertEqual(p['jitter_prefix'], 'missing-evidence-jitter-v1:1729:')
        self.assertEqual(p['still_model_artifact_sha256'], run.MODEL_FILES['candidate'][1])
        self.assertEqual(p['still_model_sha256'], '4c5467062e327d11b38f7c34117a9bb33ef853c2faba0ba3efcd9acc2fd69f0e')
        self.assertEqual(p['caps']['fits'], 0)

    def test_cutoffs_are_15_and_16_november(self):
        run.enforce_cutoff('natural', datetime(2026, 11, 15, 23, 59, tzinfo=LOCAL))
        with self.assertRaises(ValueError):
            run.enforce_cutoff('natural', datetime(2026, 11, 16, 0, 0, tzinfo=LOCAL))
        run.enforce_cutoff('stress', datetime(2026, 11, 16, 12, 0, tzinfo=LOCAL))
        with self.assertRaises(ValueError):
            run.enforce_cutoff('stress', datetime(2026, 11, 16, 12, 1, tzinfo=LOCAL))
        p = run.protocol_parameters()
        self.assertEqual((p['cutoff_local'], p['full_cutoff_local']), ('2026-11-15T23:59', '2026-11-16T12:00'))

    def test_branch_constant_used(self):
        self.assertEqual(run.BRANCH, 'experiment/missing-evidence')
        with patch.object(run, 'git', side_effect=lambda *a, **k: 'experiment/player-stillness'):
            with self.assertRaisesRegex(ValueError, 'Wrong branch'):
                run.check_repository()

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
        for name in ('missing_evidence_x.py', 'tests/test_missing_evidence_x.py', 'docs/missing-evidence-protocol.md',
                     'reports/missing-evidence/a.md', '.gitignore'):
            (repo / name).parent.mkdir(parents=True, exist_ok=True)
            (repo / name).write_text('y\n')
        git('add', '.')
        git('commit', '-q', '-m', 'allowed')
        self.assertEqual(run.check_repository(root=repo, base=base), git('rev-parse', 'HEAD'))
        (repo / 'old.py').write_text('x=2\n')
        git('commit', '-q', '-am', 'foreign')
        with self.assertRaisesRegex(ValueError, 'Existing files changed'):
            run.check_repository(root=repo, base=base)

    def test_case_receipt_passes_report_guard_and_claims(self):
        from test_gap_liveness import fixture
        import player_stillness_features as ps
        from accuracy_evidence import assert_public_report
        frames = fixture(gaps=((300, 500),), players=20)
        matrix = ps.stillness_matrix(frames)
        reference = np.array([0] * 300 + [2] * 200 + [0] * 400, np.uint8)
        receipt = run.run_case_regime(self.ledger, 'natural', 'dfl-J03WR9', frames, reference, run.load_models(),
                                      Path(self.tmp.name) / 'case', matrix=matrix)
        assert_public_report(receipt)
        self.assertEqual(self.ledger.count('prediction'), 2)
        self.assertEqual(self.ledger.count('feature_pass'), 2)
        self.assertEqual(self.ledger.count('decoder_pass'), 4)
        self.assertEqual(self.ledger.count('score'), 2)
        self.assertIn('missing_rows_to_d', receipt)


if __name__ == '__main__':
    unittest.main()
