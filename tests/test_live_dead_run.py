"""Live/dead sequence experiment: ledger, deadline and stage guards.  No match data is touched."""
from datetime import datetime, timedelta
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import live_dead_protocol as lp
import live_dead_run as lr


class LedgerTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.ledger = lr.Ledger(root / 'claims', root / 'run/access.jsonl')

    def tearDown(self):
        self.tmp.cleanup()

    def test_caps_match_protocol(self):
        self.assertEqual(lr.CAPS, dict(fit=2, prediction=123, score=123, decoder_pass=246, feature_pass=213))
        self.assertEqual(lr.PARITY_CAP, 36)

    def test_fit_order_enforced(self):
        with self.assertRaises(lr.BudgetError):
            self.ledger.claim('fit', 'temporal')
        self.ledger.claim('fit', 'instant')
        self.ledger.claim('fit', 'temporal')
        with self.assertRaises(lr.BudgetError):
            self.ledger.claim('fit', 'control')

    def test_no_reclaim(self):
        self.ledger.claim('prediction', 'natural/dfl-J03WR9/temporal')
        with self.assertRaises(lr.BudgetError):
            self.ledger.claim('prediction', 'natural/dfl-J03WR9/temporal')

    def test_cap_exhaustion(self):
        for k in range(123):
            self.ledger.claim('score', f'natural/case{k}/release')
        with self.assertRaisesRegex(lr.BudgetError, 'exhausted'):
            self.ledger.claim('score', 'natural/extra/release')

    def test_parity_identities_whitelisted(self):
        self.ledger.claim('parity', 'release/2026-11-14-a/dfl-J03WR9')
        self.ledger.claim('parity', 'disabled/2026-11-14-a/wcsf-used-match')
        self.ledger.claim('parity', 'exporter/2026-11-14-a/instant')
        self.ledger.claim('parity', 'training-alignment/2026-11-14-a/J03WMX')
        for bad in ('release/2026-11-14-a/provided', 'exporter/2026-11-14-a/control', 'other/2026-11-14-a/x',
                    'training-alignment/2026-11-14-a/J03WR9'):
            with self.assertRaises(lr.BudgetError):
                self.ledger.claim('parity', bad)


class GuardTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.patches = [mock.patch.object(lr, 'PRIVATE_ROOT', root / 'private'),
                        mock.patch.object(lr, 'REPORT_ROOT', root / 'public')]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in self.patches:
            p.stop()
        self.tmp.cleanup()

    def test_deadline_checked_on_entry(self):
        late = datetime.fromisoformat(lp.DEADLINE_LOCAL) + timedelta(seconds=1)
        with mock.patch.object(lr, 'now', return_value=late), \
                mock.patch.object(lr, 'frozen', side_effect=AssertionError('data touched')):
            for command in (lr.preflight, lr.fit, lr.parity, lr.natural, lr.stress):
                with self.assertRaisesRegex(ValueError, 'deadline'):
                    command('2026-11-14-a')

    def test_stress_requires_stage1_pass(self):
        _, public = lr.run_paths('2026-11-14-a')
        public.mkdir(parents=True)
        (public / 'stage1.json').write_text(json.dumps(dict(status='complete', decision='NO_ADVANCEMENT')))
        with mock.patch.object(lr, 'frozen', side_effect=AssertionError('data touched')):
            with self.assertRaisesRegex(ValueError, 'stage 1'):
                lr.stress('2026-11-14-a')
        self.assertFalse((lr.PRIVATE_ROOT / 'claims').exists())

    def test_check_repository_rejects_existing_file_edits(self):
        self.assertEqual(lr.foreign_changes(['live_dead_run.py', 'tests/test_live_dead_run.py',
                                             'reports/live-dead/2026-11-14-a/freeze.json',
                                             'docs/live-dead-protocol.md', 'docs/superpowers/plans/x.md']), [])
        self.assertEqual(lr.foreign_changes(['player_stillness_run.py', 'live_dead_run.py']), ['player_stillness_run.py'])

    def test_unsafe_run_id(self):
        for bad in ('../x', 'A', '', 'a' * 65):
            with self.assertRaises(ValueError):
                lr.run_paths(bad)


if __name__ == '__main__':
    unittest.main()


class BundleTest(unittest.TestCase):
    """Synthetic end-to-end bundle: three streams, claims, private arrays and a guard-clean public receipt."""

    def test_run_bundle_synthetic_end_to_end(self):
        import numpy as np
        from gap_solver.tactical import feature_rows
        import live_dead_features as lf
        from tests.test_live_dead_assembly import match

        def stump(width, feature):
            return dict(feature_count=width, n_estimators=1, trees=[dict(
                children_left=[1, -1, -1], children_right=[2, -1, -1], feature=[feature, -2, -2],
                threshold=[.5, -2., -2.], dead=[.5, .05, .95])])

        frames = match()
        reference = np.asarray([2 if 300 <= i < 420 else (i // 90) % 2 for i in range(len(frames))], dtype=np.uint8)
        x = lf.liveness_inputs(frames, lr.PITCH)
        self.assertTrue(x.eligible.any())
        models = dict(instant=stump(10, 5), temporal=stump(210, 105))
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ledger = lr.Ledger(root / 'claims', root / 'access.jsonl')
            receipt = lr.run_bundle(ledger, 'natural', 'dfl-J03WR9', frames, reference, np.asarray(x.instant),
                                    np.asarray(x.eligible), np.asarray(list(feature_rows(frames)), dtype=np.float32),
                                    models, lp.load_frozen_model(), root / 'pred')
            self.assertEqual(set(receipt['flats']), {'release', 'instant', 'temporal'})
            self.assertGreater(receipt['integration_rows'], 0)
            self.assertEqual(ledger.usage(), dict(fits=0, stream_runs=3, score_bundles=3, feature_tree_passes=3,
                                                  decoder_passes=6, parity_checks=0))
            self.assertEqual(sorted(p.name for p in (root / 'pred').iterdir()),
                             ['instant.npz', 'release.npz', 'temporal.npz'])
            with mock.patch.object(lr, 'REPORT_ROOT', root / 'public'):
                stored = lr._store_case(root / 'public', 'natural', receipt, 'dfl-J03WR9')
            self.assertEqual(stored['role'], 'primary')
            self.assertNotEqual(receipt['flats']['temporal']['dead_recall'], None)
