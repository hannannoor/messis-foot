"""preflight -> natural -> stress -> summarise driven end to end on synthetic cases (loaders and paths patched)."""
from dataclasses import replace
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from gap_solver.tactical_model import FROZEN_MODEL
from test_gap_liveness import fixture

try:
    import recent_geometry_run as run
    import recent_geometry_features as rf
except ImportError:  # pragma: no cover - red phase
    run = None


def frames():
    out = []
    for i, f in enumerate(fixture(n=2400, gaps=((300, 500), (1300, 1420)))):
        out.append(replace(f, home_distance=.5 + (i % 7), away_distance=2. + (i % 11) * .7) if f.ball_observed else f)
    return out


def reference():
    pattern = [0] * 400 + [1] * 300 + [2] * 60 + [0] * 500 + [2] * 40 + [1] * 350 + [3] * 30 + [0] * 720
    return np.asarray(pattern[:2400], dtype=np.uint8)


class Stages(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(run, 'recent_geometry_run is missing')
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.private, self.public = root / 'private', root / 'public'
        self.private.mkdir(); self.public.mkdir()
        (self.public / 'freeze.json').write_text('{}')
        self.frames = frames()
        self.patches = [
            patch.object(run, 'PRIVATE_ROOT', root / 'pr'),
            patch.object(run, 'run_paths', lambda rid: (self.private, self.public)),
            patch.object(run, 'frozen', lambda rid, role=None: ({}, {})),
            patch.object(run, 'adapter_load', self.adapter),
        ]
        for p in self.patches:
            p.start(); self.addCleanup(p.stop)

    def adapter(self, ledger, cid, bindings, purpose):
        ledger.event('evaluation_adapter_entry', case_id=cid, purpose=purpose)
        return dict(frames=list(self.frames), reference=lambda: reference(), reference_loaded_by_adapter=False)

    def ready_preflight(self):
        out = run.preflight('run-a')
        path = self.public / 'preflight.json'
        value = json.loads(path.read_text())
        value['status'] = 'ready'
        path.write_text(json.dumps(value))
        return out

    def write_models(self):
        control = FROZEN_MODEL['model']
        models = {'control': control, 'candidate': dict(control, feature_names=list(rf.RESEARCH_FEATURE_NAMES))}
        (self.public / 'models').mkdir()
        hashes = {}
        for mode, model in models.items():
            path = self.public / 'models' / (mode + '.json')
            path.write_text(json.dumps(dict(model=model)))
            hashes[mode] = run.file_sha(path)
        (self.public / 'fit.json').write_text(json.dumps(dict(status='complete', model_artifact_sha256=hashes)))

    def test_preflight_writes_sealed_masks_counts_and_prefix_parity_claims(self):
        out = self.ready_preflight()
        value = json.loads((self.public / 'preflight.json').read_text())
        self.assertEqual(len(value['cases']), 15)
        self.assertEqual(out['status'], 'blocked_insufficient_support')     # a single synthetic match cannot reach 20 events
        for cid, row in value['cases'].items():
            self.assertEqual(row['feature_prefix'], 'identical')
            self.assertEqual(len(row['mask_seal_sha256']), 64)
        ledger = run.open_ledger('run-a')
        self.assertEqual(ledger.count('parity'), 15)
        self.assertEqual(ledger.count('feature_pass'), 15)
        for cid in run.STOPPAGE_CASES:
            self.assertIsNotNone(value['cases'][cid]['stoppage_masked_rows'])
        self.assertIsNone(value['cases']['skillcorner-1874553']['stoppage_masked_rows'])
        with self.assertRaises(ValueError):
            run.preflight('run-a')

    def test_stage_one_then_stress_then_summary(self):
        self.ready_preflight()
        self.write_models()
        (self.public / 'parity.json').write_text(json.dumps(dict(status='passed')))
        result = run.natural('run-a')
        self.assertEqual(result['decision'], 'FAIL')                          # identical models: no gain
        stage1 = json.loads((self.public / 'stage1.json').read_text())
        self.assertFalse(stage1['advance_to_stage2'])
        self.assertIn('G1_natural_benefit/spell_gain', stage1['failing'])
        self.assertEqual(len(list(self.public.glob('*--natural.json'))), 15)
        ledger = run.open_ledger('run-a')
        self.assertEqual((ledger.count('prediction'), ledger.count('score'), ledger.count('decoder_pass')), (30, 30, 60))
        with self.assertRaises(ValueError):
            run.stress('run-a')                                               # stage 1 failed: no stress inference
        self.assertEqual(ledger.count('prediction'), 30)
        out = run.summarise('run-a')
        self.assertEqual(out['verdict'], 'FAIL')
        summary = json.loads((self.public / 'summary.json').read_text())
        self.assertFalse(summary['stage2_run'])
        self.assertEqual(summary['budget_used']['case_runs'], 30)

    def test_stress_runs_all_three_regimes_when_stage_one_advanced(self):
        self.ready_preflight()
        self.write_models()
        stage1 = dict(status='complete', decision='PASS', advance_to_stage2=True, failing={}, gates={})
        (self.public / 'stage1.json').write_text(json.dumps(stage1))
        out = run.stress('run-a')
        self.assertEqual(out['status'], 'complete')
        ledger = run.open_ledger('run-a')
        self.assertEqual(ledger.count('prediction'), 2 * (15 + 15 + 5))
        self.assertEqual(ledger.count('score'), 70)
        self.assertEqual(len(list(self.public.glob('*--noise.json'))), 15)
        self.assertEqual(len(list(self.public.glob('*--live-gap.json'))), 15)
        self.assertEqual(len(list(self.public.glob('*--stoppage.json'))), 5)
        stage2 = json.loads((self.public / 'stage2.json').read_text())
        self.assertIn('G6_support_restart', stage2['gates'])
        self.assertIn('G5_noise_mechanism', stage2['gates'])

    def test_masks_are_checked_against_their_seal_before_use(self):
        self.ready_preflight()
        self.write_models()
        (self.public / 'stage1.json').write_text(json.dumps(dict(status='complete', decision='PASS', advance_to_stage2=True, failing={}, gates={})))
        path = self.public / 'preflight.json'
        value = json.loads(path.read_text())
        value['cases']['skillcorner-1874553']['mask_seal_sha256'] = '0' * 64
        path.write_text(json.dumps(value))
        with self.assertRaises(ValueError):
            run.stress('run-a')
        self.assertEqual(run.open_ledger('run-a').count('prediction'), 0)

    def test_stage_one_refuses_without_a_passed_parity_receipt(self):
        self.ready_preflight()
        self.write_models()
        with self.assertRaises(ValueError):
            run.natural('run-a')
        self.assertEqual(run.open_ledger('run-a').count('prediction'), 0)


class ParityPieces(unittest.TestCase):
    HIST = Path(__file__).resolve().parents[1] / 'reports/memory-ablation/2026-11-09-v3'

    def test_reconcile_accepts_the_historical_receipt_and_rejects_any_count_or_scalar_change(self):
        import copy
        historical = json.loads((self.HIST / 'dfl-J03WR9--natural.json').read_text())['variants']['control']
        self.assertTrue(run.reconcile_against_history(copy.deepcopy(historical), historical))
        for mutate in (lambda s: s['spells']['per_iou']['0.5'].__setitem__('n_matched', s['spells']['per_iou']['0.5']['n_matched'] + 1),
                       lambda s: s['spells']['per_iou']['0.3'].__setitem__('n_spurious', 0),
                       lambda s: s['metrics'].__setitem__('spell_f1_mean', s['metrics']['spell_f1_mean'] + 2e-9),
                       lambda s: s['spells'].__setitem__('n_pred', s['spells']['n_pred'] + 1)):
            bad = copy.deepcopy(historical)
            mutate(bad)
            self.assertFalse(run.reconcile_against_history(bad, historical))
        near = copy.deepcopy(historical)
        near['metrics']['spell_f1_mean'] += 5e-10
        self.assertTrue(run.reconcile_against_history(near, historical))

    def test_primary_mean_check_reproduces_the_historical_value_only(self):
        summary = json.loads((self.HIST / 'summary.json').read_text())['primary']['natural']['control']
        self.assertAlmostEqual(summary, 0.551816, places=6)
        cases = {c: summary for c in run.NATURAL_CASES}
        self.assertEqual(run.primary_natural_check(cases, summary)[1], True)
        cases['wcsf-used-match'] = summary + 1e-3
        self.assertEqual(run.primary_natural_check(cases, summary)[1], False)
        cases = {c: summary for c in run.NATURAL_CASES}
        cases['dfl-J03WOH'] = 0.0                      # secondary cases never enter the mean
        self.assertEqual(run.primary_natural_check(cases, summary)[1], True)

    def test_protocol_parameters_are_public_report_safe(self):
        from accuracy_evidence import assert_public_report
        assert_public_report(run.protocol_parameters())
        assert_public_report(dict(protocol=run.protocol_parameters(), source_sha256={'a.py': '0' * 64},
                                  input_sha256={'training': {'m': {'f': '0' * 64}}}))

    def test_protocol_parameters_survive_a_json_round_trip(self):
        self.assertEqual(json.loads(json.dumps(run.protocol_parameters())), run.protocol_parameters())


class ParityRun(Stages):
    """The real parity() on synthetic frames, with only the historical comparison stubbed."""

    def test_parity_matches_the_real_release_function_and_logs_separately(self):
        self.ready_preflight()
        self.write_models()
        fit = json.loads((self.public / 'fit.json').read_text())
        fit.update(candidate_parity_max_abs_diff=0.0, control_parity_max_abs_diff=0.0)
        (self.public / 'fit.json').write_text(json.dumps(fit))
        summary = json.loads((run.ROOT / 'reports/memory-ablation/2026-11-09-v3/summary.json').read_text())['primary']['natural']['control']
        with patch.object(run, 'reconcile_against_history', lambda s, h: True), \
                patch.object(run, 'primary_natural_check', lambda f1, h: (summary, True)):
            out = run.parity('run-a')
        self.assertEqual(out['status'], 'passed')
        ledger = run.open_ledger('run-a')
        self.assertEqual(ledger.count('parity'), 15 + 15 + 1)          # prefix (preflight) + release + exporter
        self.assertEqual(ledger.count('score'), 15)                    # reconciliation bundles only
        self.assertEqual((ledger.count('prediction'), ledger.count('decoder_pass'), ledger.count('feature_pass')), (0, 0, 15))
        value = json.loads((self.public / 'parity.json').read_text())
        self.assertEqual((value['release_parity_cases'], value['reconciliation_cases']), (15, 15))

    def test_parity_stops_if_the_replica_ever_differs_from_the_real_release(self):
        self.ready_preflight()
        self.write_models()
        fit = json.loads((self.public / 'fit.json').read_text())
        fit.update(candidate_parity_max_abs_diff=0.0, control_parity_max_abs_diff=0.0)
        (self.public / 'fit.json').write_text(json.dumps(fit))
        import recent_geometry_assembly as ra
        real = ra.assemble_research

        def broken(*a, **k):
            result = real(*a, **k)
            from dataclasses import replace as r
            return r(result, final=('X',) + result.final[1:])
        with patch.object(ra, 'assemble_research', broken):
            with self.assertRaises(ValueError):
                run.parity('run-a')
        self.assertFalse((self.public / 'parity.json').exists())


if __name__ == '__main__':
    unittest.main()
