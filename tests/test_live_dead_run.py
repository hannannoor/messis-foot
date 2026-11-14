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
            self.assertIn('restart', receipt['bundles']['temporal']['extras'])          # DFL/WCSF restart diagnostics


class ReviewFixTest(unittest.TestCase):
    """Fixes from the pre-execution whole-branch review."""

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

    def test_protocol_parameters_pass_public_guard(self):
        from accuracy_evidence import assert_public_report
        assert_public_report(dict(protocol=lr.protocol_parameters()))

    def test_stress_stops_on_regime_support_shortfall(self):
        import numpy as np
        from tests.test_live_dead_features import frame
        run = '2026-11-14-a'
        _, public = lr.run_paths(run)
        public.mkdir(parents=True)
        (public / 'stage1.json').write_text(json.dumps(dict(status='complete', decision='PASS')))
        sparse = [frame(i, n=9) for i in range(300)]                  # never eligible: every floor fails
        ref = np.zeros(300, dtype=np.uint8)
        arrays = dict(reference=ref, instant=np.zeros((300, 10), np.float32), eligible=np.zeros(300, bool))
        pre = dict(status='ready', cases={c: dict(case_arrays_sha256='0' * 64) for c in lp.CASES})
        with mock.patch.object(lr, 'frozen', return_value=({}, dict(evaluation={}))), \
                mock.patch.object(lr, 'require', return_value=pre), \
                mock.patch.object(lr, 'load_models', return_value=({}, {})), \
                mock.patch.object(lp, 'load_frozen_model', return_value={}), \
                mock.patch.object(lr, 'load_arrays', return_value=arrays), \
                mock.patch.object(lr, 'adapter_load', return_value=dict(frames=sparse)), \
                mock.patch.object(lr, 'run_bundle', side_effect=AssertionError('predicted despite shortfall')):
            result = lr.stress(run)
        self.assertEqual(result['decision'], 'UNRESOLVED')
        stage2 = json.loads((public / 'stage2.json').read_text())
        self.assertEqual(stage2['status'], 'UNRESOLVED_support')
        self.assertIn('jitter', stage2['problems'])
        self.assertIn('skillcorner-1874553', stage2['problems'])
        self.assertIn('skillcorner-1874553', stage2['coverage']['jitter'])
        ledger = lr.open_ledger(run)
        self.assertEqual((ledger.count('prediction'), ledger.count('score')), (0, 0))

    def test_finish_stage_retains_results_after_deadline(self):
        late = datetime.fromisoformat(lp.DEADLINE_LOCAL) + timedelta(seconds=1)
        path = Path(self.tmp.name) / 'stage1.json'
        with mock.patch.object(lr, 'now', return_value=late):
            value = lr.finish_stage(path, dict(status='complete', decision='PASS', advance_to_stage2=True))
        stored = json.loads(path.read_text())
        self.assertEqual((stored['status'], stored['decision'], stored['advance_to_stage2']), ('timeout', 'UNRESOLVED', False))
        self.assertEqual(stored['decision_before_timeout'], 'PASS')
        self.assertEqual(value, stored)

    def test_summarise_writes_report(self):
        _, public = lr.run_paths('2026-11-14-a')
        public.mkdir(parents=True)
        (public / 'preflight.json').write_text(json.dumps(dict(status='ready', problems='')))
        gates = dict(spell_gain=dict(status='fail', value=.001, threshold=.01),
                     interior_accuracy=dict(status='reported', release=.8, instant=.8, temporal=.8))
        (public / 'stage1.json').write_text(json.dumps(dict(status='complete', decision='NO_ADVANCEMENT', gates=gates)))
        value = lr.summarise('2026-11-14-a')
        self.assertEqual(value['verdict'], 'NO_ADVANCEMENT')
        text = (public / 'report.md').read_text(encoding='utf-8')
        self.assertIn('NO_ADVANCEMENT', text)
        self.assertIn('spell_gain', text)
        self.assertIn('fail', text)

    def test_stage_and_coverage_values_pass_public_guard(self):
        import numpy as np
        from accuracy_evidence import assert_public_report
        import live_dead_assembly as la
        import live_dead_features as lf
        import live_dead_metrics as lm
        from tests.test_live_dead_assembly import match
        from tests.test_live_dead_metrics import flats
        frames = match()
        x = lf.liveness_inputs(frames, lr.PITCH)
        cov = lr.coverage(frames, np.zeros(len(frames), np.uint8), x.eligible, la.integration_mask(frames, x.eligible),
                          la.denominator_mask(frames))
        f = flats()
        assert_public_report(dict(status='complete', decision='PASS', advance_to_stage2=True, gates=lm.gate_natural(f)))
        primary = {c: v for c, v in f.items() if c in lp.PRIMARY}
        assert_public_report(dict(status='complete', regimes=dict(jitter='PASS'), gates=dict(jitter=lm.gate_stress(primary)),
                                  coverage=dict(jitter={'dfl-J03WR9': dict(cov, stress_arrays_sha256='0' * 64)})))
        assert_public_report(dict(status='ready', cases={'dfl-J03WR9': dict(cov, case_arrays_sha256='0' * 64)}))
