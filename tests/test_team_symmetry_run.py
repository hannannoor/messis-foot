"""Experiment C orchestration: ledger, pipeline, parity gates, stages and unchanged-file checks. Synthetic data only."""
from dataclasses import replace
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from gap_solver.tactical_model import FROZEN_MODEL
from test_gap_liveness import fixture

try:
    import team_symmetry_run as run
    import team_symmetry as ts
except ImportError:  # pragma: no cover - red phase
    run = None

MODEL = FROZEN_MODEL['model']
REPO = Path(__file__).resolve().parents[1]
BASE = '01aea05f545cc366d5112f153f678399a5268dac'


def frames(n=1100, gaps=((300, 500), (700, 800))):
    out = []
    for i, f in enumerate(fixture(n=n, gaps=gaps)):
        out.append(replace(f, home_distance=.5 + (i % 7), away_distance=2. + (i % 11) * .7) if f.ball_observed else f)
    return out


def reference_1100():
    return np.resize(np.asarray([0] * 90 + [1] * 70 + [2] * 40 + [0] * 120 + [3] * 20, dtype=np.uint8), 1100)


class Ledger(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(run, 'team_symmetry_run is missing')
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.ledger = run.Ledger(self.root / 'claims', self.root / 'access.jsonl')

    def events(self):
        return [json.loads(line) for line in (self.root / 'access.jsonl').read_text().splitlines()]

    def test_caps_are_the_brief_numbers_and_there_are_no_fits(self):
        self.assertEqual(run.CAPS, dict(fit=0, prediction=100, score=115, feature_pass=200, decoder_pass=300))
        with self.assertRaises(run.BudgetError):
            self.ledger.claim('fit', 'control')
        with self.assertRaises(run.BudgetError):
            self.ledger.claim('fit', 'candidate')

    def test_claim_is_written_before_returning_and_logged(self):
        self.ledger.claim('prediction', 'natural/dfl-J03WR9/control')
        self.assertTrue((self.root / 'claims' / 'prediction--natural__dfl-J03WR9__control.json').is_file())
        self.assertEqual([e['event'] for e in self.events()], ['prediction_entry'])

    def test_identity_can_only_be_claimed_once_no_reruns(self):
        self.ledger.claim('prediction', 'natural/a/control')
        with self.assertRaises(run.BudgetError):
            self.ledger.claim('prediction', 'natural/a/control')

    def test_every_cap_refuses_the_next_claim_and_counts_survive_restart(self):
        for kind, cap in run.CAPS.items():
            if kind == 'fit':
                continue
            for i in range(cap):
                self.ledger.claim(kind, f'x/{i}')
            with self.assertRaises(run.BudgetError):
                self.ledger.claim(kind, f'x/{cap}')
        again = run.Ledger(self.root / 'claims', self.root / 'access.jsonl')
        for kind in ('prediction', 'score', 'feature_pass', 'decoder_pass'):
            with self.assertRaises(run.BudgetError):
                again.claim(kind, 'x/new')
        self.assertEqual((again.count('prediction'), again.count('score'), again.count('feature_pass'), again.count('decoder_pass')),
                         (100, 115, 200, 300))

    def test_parity_is_a_separate_category_that_never_touches_science_counts(self):
        for case in run.NATURAL_CASES:
            for kind in ('swap', 'symmetry', 'release'):
                self.ledger.claim('parity', f'{kind}/{case}')
        for kind in run.CAPS:
            self.assertEqual(self.ledger.count(kind), 0)
        self.assertEqual(self.ledger.count('parity'), 45)

    def test_parity_identities_are_bounded_unique_and_retry_is_limited(self):
        for bad in ('release/not-a-case', 'sweep', 'exporter', 'prefix/dfl-J03WR9', 'release/dfl-J03WR9/retry3',
                    'release/dfl-J03WR9/anything'):
            with self.assertRaises(run.BudgetError):
                self.ledger.claim('parity', bad)
        self.ledger.claim('parity', 'release/dfl-J03WR9')
        with self.assertRaises(run.BudgetError):
            self.ledger.claim('parity', 'release/dfl-J03WR9')
        self.ledger.claim('parity', 'release/dfl-J03WR9/retry1')
        self.ledger.claim('parity', 'release/dfl-J03WR9/retry2')

    def test_failed_work_does_not_refund_a_claim(self):
        try:
            self.ledger.claim('score', 'a')
            raise RuntimeError('bug after claim')
        except RuntimeError:
            pass
        self.assertEqual(self.ledger.count('score'), 1)

    def test_unknown_kind_and_unsafe_identities_refused(self):
        with self.assertRaises(run.BudgetError):
            self.ledger.claim('sweep', 'x')
        for bad in ('../x', 'a\\b', '', 'a' * 300, 'a__b'):
            with self.assertRaises(run.BudgetError):
                self.ledger.claim('score', bad)

    def test_case_inventory_is_experiment_a_section_7_and_has_no_provided_match(self):
        import recent_geometry_run as a
        self.assertEqual(run.NATURAL_CASES, a.NATURAL_CASES)
        self.assertEqual(len(run.NATURAL_CASES), 15)
        self.assertEqual(sum(run.is_primary(c) for c in run.NATURAL_CASES), 13)
        self.assertEqual(run.STOPPAGE_CASES, a.STOPPAGE_CASES)
        self.assertFalse([c for c in run.NATURAL_CASES if 'provided' in c or 'metrica' in c.lower() or 'barca' in c.lower()])


class Noise(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(run, 'team_symmetry_run is missing')

    def test_with_experiment_a_prefix_it_is_byte_identical_to_experiment_a(self):
        import recent_geometry_regimes as rr
        f = frames()
        self.assertEqual(run.add_visible_ball_noise(f, 'dfl-J03WR9', prefix=rr.JITTER_PREFIX), rr.add_visible_ball_noise(f, 'dfl-J03WR9'))

    def test_own_prefix_and_seed_rule(self):
        import hashlib
        self.assertEqual(run.JITTER_PREFIX, 'team-symmetry-jitter-v1:1729:')
        expect = int(hashlib.sha256(('team-symmetry-jitter-v1:1729:dfl-J03WR9').encode()).hexdigest()[:8], 16)
        self.assertEqual(run.noise_seed('dfl-J03WR9'), expect)
        import recent_geometry_regimes as rr
        f = frames()
        mine, theirs = run.add_visible_ball_noise(f, 'dfl-J03WR9'), rr.add_visible_ball_noise(f, 'dfl-J03WR9')
        self.assertNotEqual([x.ball_x for x in mine], [x.ball_x for x in theirs])

    def test_missing_rows_untouched_and_sigma_is_a_quarter_metre(self):
        f = frames()
        out = run.add_visible_ball_noise(f, 'skillcorner-1874553')
        for before, after in zip(f, out):
            if not before.ball_observed:
                self.assertIs(before, after)
        d = np.asarray([a.ball_x - b.ball_x for a, b in zip(out, f) if b.ball_observed])
        self.assertAlmostEqual(float(d.std()), .25, delta=.03)
        self.assertEqual(run.noise_seed('x'), run.noise_seed('x'))


class Pipeline(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(run, 'team_symmetry_run is missing')
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.ledger = run.Ledger(self.root / 'claims', self.root / 'access.jsonl')
        self.reference = reference_1100()

    def go(self, regime='natural', **kw):
        return run.run_case_regime(self.ledger, regime, 'dfl-J03WR9', frames(), self.reference, MODEL, self.root / ('out-' + regime), **kw)

    def test_budget_claimed_exactly_and_before_use(self):
        self.go()
        self.assertEqual({k: self.ledger.count(k) for k in run.CAPS},
                         dict(fit=0, prediction=2, score=2, feature_pass=4, decoder_pass=4))   # prep + control 1 + candidate 2
        events = [json.loads(l)['event'] for l in (self.root / 'access.jsonl').read_text().splitlines()]
        self.assertEqual(events[0], 'feature_pass_entry')
        self.assertLess(events.index('prediction_entry'), events.index('score_entry'))

    def test_supplied_matrix_skips_the_prep_claim(self):
        import recent_geometry_run  # noqa: F401  (import must work, nothing is mutated)
        from gap_solver.tactical import feature_rows
        matrix = np.asarray(list(feature_rows(frames())), dtype=np.float32)
        self.go(matrix=matrix)
        self.assertEqual(self.ledger.count('feature_pass'), 3)

    def test_full_run_budget_arithmetic_fits_the_caps(self):
        """50 case-regimes x (2 predictions, 2 scores, 4 decoder passes, 3 tree passes) + 50 prep passes."""
        self.assertEqual(50 * 2, run.CAPS['prediction'])
        self.assertLessEqual(50 * 2, run.CAPS['score'] - 15)
        self.assertLessEqual(50 * 4, run.CAPS['decoder_pass'])
        self.assertEqual(50 * 3 + 50, run.CAPS['feature_pass'])

    def test_control_is_the_real_release_and_candidate_uses_symmetrised_supports(self):
        from gap_solver.tactical import feature_rows
        import restart_release
        out = self.go()
        matrix = np.asarray(list(feature_rows(frames())), dtype=np.float32)
        with np.load(self.root / 'out-natural' / 'control.npz') as c, np.load(self.root / 'out-natural' / 'candidate.npz') as k:
            np.testing.assert_array_equal(c['supports'], ts.control_supports(matrix, MODEL))
            np.testing.assert_array_equal(k['supports'], ts.candidate_supports(matrix, MODEL))
            self.assertGreater(float(np.abs(c['supports'] - k['supports']).max()), 0.)
            real = restart_release.assemble(frames(), (), use_restart=True).final
            self.assertEqual(c['final'].tolist(), ['HADX'.index(s) for s in real])
        from accuracy_evidence import assert_public_report
        assert_public_report(out)

    def test_support_sets_cannot_be_mixed_between_methods(self):
        from gap_solver.tactical import feature_rows
        import recent_geometry_assembly as ra
        matrix = np.asarray(list(feature_rows(frames())), dtype=np.float32)
        control = ra.SupportSet('control', ts.control_supports(matrix, MODEL))
        candidate = ra.SupportSet('candidate', ts.candidate_supports(matrix, MODEL))
        run.require_method(control, 'control')
        run.require_method(candidate, 'candidate')
        with self.assertRaises(ValueError):
            run.require_method(candidate, 'control')
        with self.assertRaises(ValueError):
            run.require_method(control, 'candidate')

    def test_no_rerun_of_the_same_prediction(self):
        self.go()
        with self.assertRaises(run.BudgetError):
            run.run_case_regime(self.ledger, 'natural', 'dfl-J03WR9', frames(), self.reference, MODEL, self.root / 'again')

    def test_reference_dimension_mismatch_stops_before_claims(self):
        with self.assertRaises(ValueError):
            run.run_case_regime(self.ledger, 'natural', 'x', frames(), self.reference[:-1], MODEL, self.root / 'bad')
        self.assertEqual(self.ledger.count('prediction'), 0)

    def test_stoppage_regime_reports_restart_counts(self):
        self.assertIn('restart', self.go('stoppage')['flats']['control'])

    def test_a_budget_refusal_mid_case_leaves_no_scores(self):
        for i in range(run.CAPS['decoder_pass'] - 1):
            self.ledger.claim('decoder_pass', f'x/{i}')
        with self.assertRaises(run.BudgetError):
            self.go()
        self.assertEqual(self.ledger.count('score'), 0)


class ParityPieces(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(run, 'team_symmetry_run is missing')

    def test_swap_validity_passes_on_synthetic_frames_and_fails_on_a_non_swap(self):
        self.assertTrue(run.swap_validity(frames())['identical'])
        with patch.object(ts, 'swap_frames', lambda f: list(f)):
            self.assertFalse(run.swap_validity(frames())['identical'])

    def test_release_parity_on_synthetic_frames(self):
        out = run.release_parity(frames(), MODEL)
        self.assertTrue(all(out['fields'].values()), out)
        self.assertEqual(out['replica'].decoder_passes, 3)       # first decode + verification decode + restart decode

    def test_release_parity_detects_a_different_support_set(self):
        flip = dict(MODEL, probabilities=[[p[1], p[0], p[2]] for p in MODEL['probabilities']])
        import restart_release
        from gap_solver.tactical import feature_rows
        import recent_geometry_assembly as ra
        f = frames()
        matrix = np.asarray(list(feature_rows(f)), dtype=np.float32)
        wrong = ra.assemble_research(f, ra.SupportSet('control', ts.control_supports(matrix, flip)))
        real = restart_release.assemble(f, (), use_restart=True)
        self.assertNotEqual(wrong.final, real.final)

    def test_model_must_be_the_frozen_one(self):
        self.assertEqual(run.load_model(), FROZEN_MODEL['model'])
        with patch.object(run, 'MODEL_SHA', '0' * 64):
            with self.assertRaises(ValueError):
                run.load_model()

    def test_reconcile_and_primary_check_are_the_experiment_a_rules(self):
        import copy
        hist = REPO / 'reports/memory-ablation/2026-11-09-v3'
        historical = json.loads((hist / 'dfl-J03WR9--natural.json').read_text())['variants']['control']
        self.assertTrue(run.reconcile_against_history(copy.deepcopy(historical), historical))
        bad = copy.deepcopy(historical)
        bad['spells']['per_iou']['0.5']['n_matched'] += 1
        self.assertFalse(run.reconcile_against_history(bad, historical))
        summary = json.loads((hist / 'summary.json').read_text())['primary']['natural']['control']
        cases = {c: summary for c in run.NATURAL_CASES}
        self.assertTrue(run.primary_natural_check(cases, summary)[1])
        cases['wcsf-used-match'] = summary + 1e-3
        self.assertFalse(run.primary_natural_check(cases, summary)[1])

    def test_mask_seal_comparison_with_experiment_a(self):
        seals = {c: format(i, '064x') for i, c in enumerate(run.NATURAL_CASES)}
        path = Path(tempfile.mkdtemp()) / 'a.json'
        path.write_text(json.dumps(dict(cases={c: dict(mask_seal_sha256=s) for c, s in seals.items()})))
        with patch.object(run, 'A_PREFLIGHT', path):
            self.assertTrue(all(run.check_mask_seals(seals).values()))
            changed = dict(seals, **{'dfl-J03WR9': '0' * 64})
            result = run.check_mask_seals(changed)
            self.assertFalse(result['dfl-J03WR9'])
            self.assertEqual(sum(result.values()), 14)
        with patch.object(run, 'A_PREFLIGHT', path.with_name('missing.json')):
            with self.assertRaises(ValueError):
                run.check_mask_seals(seals)

    def test_protocol_parameters_are_public_safe_and_round_trip(self):
        from accuracy_evidence import assert_public_report
        value = run.protocol_parameters()
        assert_public_report(value)
        self.assertEqual(json.loads(json.dumps(value)), value)
        import recent_geometry_metrics as m
        self.assertEqual(value['gain_threshold'], m.GAIN_THRESHOLD)
        self.assertEqual(value['gain_threshold'], .010)
        self.assertEqual(value['jitter_prefix'], 'team-symmetry-jitter-v1:1729:')
        self.assertEqual(value['caps']['fits'], 0)
        self.assertEqual(value['base_commit'], BASE)
        self.assertEqual(value['model_sha256'], '363c45c70838b398cd87aee7474d7e281fd392f059a31b85712e312058aaab4d')


class Stages(unittest.TestCase):
    """preflight -> parity -> natural -> stress -> summarise on synthetic cases (loaders and paths patched)."""

    def setUp(self):
        self.assertIsNotNone(run, 'team_symmetry_run is missing')
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.private, self.public = root / 'private', root / 'public'
        self.private.mkdir()
        self.public.mkdir()
        (self.public / 'freeze.json').write_text('{}')
        self.frames = frames(2400, ((300, 500), (1300, 1420)))
        pattern = [0] * 400 + [1] * 300 + [2] * 60 + [0] * 500 + [2] * 40 + [1] * 350 + [3] * 30 + [0] * 720
        self.ref = np.asarray(pattern[:2400], dtype=np.uint8)
        self.patches = [
            patch.object(run, 'PRIVATE_ROOT', root / 'pr'),
            patch.object(run, 'run_paths', lambda rid: (self.private, self.public)),
            patch.object(run, 'frozen', lambda rid, role=None: ({}, {})),
            patch.object(run, 'adapter_load', self.adapter),
            patch.object(run, 'check_mask_seals', lambda seals: {c: True for c in seals}),
        ]
        for p in self.patches:
            p.start()
            self.addCleanup(p.stop)

    def adapter(self, ledger, cid, bindings, purpose):
        ledger.event('evaluation_adapter_entry', case_id=cid, purpose=purpose)
        return dict(frames=list(self.frames), reference=lambda: self.ref, reference_loaded_by_adapter=False)

    def ready_preflight(self):
        out = run.preflight('run-a')
        path = self.public / 'preflight.json'
        value = json.loads(path.read_text())
        value['status'] = 'ready'
        path.write_text(json.dumps(value))
        return out

    def stub_history(self):
        summary = json.loads((run.ROOT / 'reports/memory-ablation/2026-11-09-v3/summary.json').read_text())['primary']['natural']['control']
        return patch.object(run, 'reconcile_against_history', lambda s, h: True), \
            patch.object(run, 'primary_natural_check', lambda f1, h: (summary, True))

    def test_preflight_writes_sealed_masks_counts_and_claims(self):
        out = self.ready_preflight()
        value = json.loads((self.public / 'preflight.json').read_text())
        self.assertEqual(len(value['cases']), 15)
        self.assertEqual(out['status'], 'blocked_insufficient_support')
        for cid, row in value['cases'].items():
            self.assertEqual(len(row['mask_seal_sha256']), 64)
            self.assertTrue(row['mask_seal_matches_experiment_a'])
        ledger = run.open_ledger('run-a')
        self.assertEqual((ledger.count('feature_pass'), ledger.count('parity')), (15, 0))
        self.assertEqual(value['model_sha256'], '363c45c70838b398cd87aee7474d7e281fd392f059a31b85712e312058aaab4d')
        with self.assertRaises(ValueError):
            run.preflight('run-a')

    def test_preflight_stops_when_a_mask_differs_from_experiment_a(self):
        with patch.object(run, 'check_mask_seals', lambda seals: {c: c != 'dfl-J03WR9' for c in seals}):
            out = run.preflight('run-a')
        self.assertEqual(out['status'], 'stopped_mask_mismatch')
        self.assertEqual(json.loads((self.public / 'preflight.json').read_text())['status'], 'stopped_mask_mismatch')

    def test_parity_runs_all_four_gates_and_reconciliation_and_writes_bias(self):
        self.ready_preflight()
        a, b = self.stub_history()
        with a, b:
            out = run.parity('run-a')
        self.assertEqual(out['status'], 'passed')
        ledger = run.open_ledger('run-a')
        self.assertEqual(ledger.count('parity'), 45)
        self.assertEqual(ledger.count('score'), 15)                      # reconciliation bundles only
        self.assertEqual((ledger.count('prediction'), ledger.count('decoder_pass'), ledger.count('feature_pass')), (0, 0, 15))
        value = json.loads((self.public / 'parity.json').read_text())
        self.assertEqual((value['swap_validity_cases'], value['release_parity_cases'], value['reconciliation_cases'],
                          value['symmetry_cases']), (15, 15, 15, 15))
        self.assertLessEqual(value['candidate_symmetry_max_abs_diff'], 1e-12)
        bias = json.loads((self.public / 'bias.json').read_text())
        self.assertEqual(set(bias['providers']), {'skillcorner', 'dfl', 'wcsf'})
        row = bias['providers']['dfl']
        self.assertAlmostEqual(row['label_lean_removed_mean'], row['control_mean_h_minus_a'] - row['candidate_mean_h_minus_a'], places=12)
        self.assertGreater(row['usable_rows'], 0)
        from accuracy_evidence import assert_public_report
        assert_public_report(bias)

    def test_parity_stops_before_any_science_claim_if_the_swap_map_is_wrong(self):
        self.ready_preflight()
        a, b = self.stub_history()
        with a, b, patch.object(ts, 'swap_frames', lambda f: list(f)):
            with self.assertRaises(ValueError):
                run.parity('run-a')
        ledger = run.open_ledger('run-a')
        self.assertEqual((ledger.count('score'), ledger.count('prediction')), (0, 0))
        self.assertFalse((self.public / 'parity.json').exists())

    def test_parity_stops_if_the_replica_ever_differs_from_the_real_release(self):
        self.ready_preflight()
        a, b = self.stub_history()
        import recent_geometry_assembly as ra
        real = ra.assemble_research

        def broken(*args, **kw):
            result = real(*args, **kw)
            return replace(result, final=('X',) + result.final[1:])
        with a, b, patch.object(ra, 'assemble_research', broken):
            with self.assertRaises(ValueError):
                run.parity('run-a')
        self.assertEqual(run.open_ledger('run-a').count('score'), 0)
        self.assertFalse((self.public / 'parity.json').exists())

    def test_stage_one_refuses_without_passed_parity(self):
        self.ready_preflight()
        with self.assertRaises(ValueError):
            run.natural('run-a')
        self.assertEqual(run.open_ledger('run-a').count('prediction'), 0)

    def test_stage_one_then_stress_refusal_then_summary(self):
        self.ready_preflight()
        (self.public / 'parity.json').write_text(json.dumps(dict(status='passed')))
        result = run.natural('run-a')
        stage1 = json.loads((self.public / 'stage1.json').read_text())
        self.assertEqual(result['decision'], stage1['decision'])
        self.assertEqual(len(list(self.public.glob('*--natural.json'))), 15)
        ledger = run.open_ledger('run-a')
        self.assertEqual((ledger.count('prediction'), ledger.count('score'), ledger.count('decoder_pass')), (30, 30, 60))
        self.assertEqual(ledger.count('feature_pass'), 15 + 45)          # preflight prep + 3 tree passes per case
        if not stage1['advance_to_stage2']:
            with self.assertRaises(ValueError):
                run.stress('run-a')
            self.assertEqual(ledger.count('prediction'), 30)
        out = run.summarise('run-a')
        summary = json.loads((self.public / 'summary.json').read_text())
        self.assertEqual(summary['budget_used']['case_runs'], 30)
        self.assertEqual(summary['budget_used']['fits'], 0)
        self.assertIn(out['verdict'], ('FAIL', 'PASS - qualifies for a separate release decision', 'INCOMPLETE'))

    def test_stress_runs_all_three_regimes_when_stage_one_advanced(self):
        self.ready_preflight()
        (self.public / 'stage1.json').write_text(json.dumps(dict(status='complete', decision='PASS', advance_to_stage2=True, failing={}, gates={})))
        out = run.stress('run-a')
        self.assertEqual(out['status'], 'complete')
        ledger = run.open_ledger('run-a')
        self.assertEqual(ledger.count('prediction'), 2 * (15 + 15 + 5))
        self.assertEqual(ledger.count('score'), 70)
        self.assertEqual(ledger.count('feature_pass'), 15 + 35 * 4)
        for regime, n in (('noise', 15), ('live-gap', 15), ('stoppage', 5)):
            self.assertEqual(len(list(self.public.glob(f'*--{regime}.json'))), n)
        stage2 = json.loads((self.public / 'stage2.json').read_text())
        self.assertIn('G6_support_restart', stage2['gates'])
        self.assertIn('G5_noise_mechanism', stage2['gates'])

    def test_masks_are_checked_against_their_seal_before_use(self):
        self.ready_preflight()
        (self.public / 'stage1.json').write_text(json.dumps(dict(status='complete', decision='PASS', advance_to_stage2=True, failing={}, gates={})))
        path = self.public / 'preflight.json'
        value = json.loads(path.read_text())
        value['cases']['skillcorner-1874553']['mask_seal_sha256'] = '0' * 64
        path.write_text(json.dumps(value))
        with self.assertRaises(ValueError):
            run.stress('run-a')
        self.assertEqual(run.open_ledger('run-a').count('prediction'), 0)


class Freeze(unittest.TestCase):
    """freeze() on a fresh run id creates its output folder and writes a verifiable receipt (heavy checks patched)."""

    def test_freeze_creates_public_folder_and_receipt(self):
        import memory_ablation_protocol as p
        a = json.loads(run.A_FREEZE.read_text())
        bindings = dict(evaluation={cid: dict(expected=h, files={}) for cid, h in a['input_sha256']['evaluation'].items()})
        root = Path(tempfile.mkdtemp())
        private, public = root / 'private', root / 'public' / 'run-x'
        with patch.object(run, 'run_paths', lambda rid: (private, public)), \
                patch.object(run, 'check_repository', lambda: 'a' * 40), \
                patch.object(run, 'verified_bindings', lambda: bindings), \
                patch.object(run, 'PRIVATE_ROOT', root / 'pr'), \
                patch.object(p, 'runtime_info', lambda *a_, **k: a['environment']['scoring']):
            out = run.freeze('run-x')
        self.assertEqual(out['status'], 'frozen')
        receipt = json.loads((public / 'freeze.json').read_text())
        self.assertEqual(receipt['protocol'], run.protocol_parameters())
        self.assertEqual(receipt['protocol_doc_sha256'], run.file_sha(run.ROOT / run.PROTOCOL_DOC))
        self.assertEqual(receipt['input_sha256']['evaluation'], a['input_sha256']['evaluation'])
        self.assertEqual(receipt['environment']['scoring'], a['environment']['scoring'])
        self.assertTrue((private / 'freeze-anchor.json').is_file())

    def test_freeze_refuses_a_different_environment(self):
        import memory_ablation_protocol as p
        a = json.loads(run.A_FREEZE.read_text())
        root = Path(tempfile.mkdtemp())
        with patch.object(run, 'run_paths', lambda rid: (root / 'private', root / 'public')), \
                patch.object(run, 'check_repository', lambda: 'a' * 40), \
                patch.object(p, 'runtime_info', lambda *a_, **k: dict(a['environment']['scoring'], python='3.0.0')):
            with self.assertRaises(ValueError):
                run.freeze('run-x')
        self.assertFalse((root / 'public' / 'freeze.json').exists())


class GatesAreExperimentA(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(run, 'team_symmetry_run is missing')

    def test_gate_logic_and_constants_are_the_unchanged_experiment_a_module(self):
        import recent_geometry_metrics as m
        self.assertIs(run.metrics, m)
        for name, value in dict(EPS=1e-6, ROUNDOFF=1e-12, GAIN_THRESHOLD=.010, STRESS_PRIMARY_LOSS=.005, MATCH_LOSS=.020,
                                DEAD_LOSS=.010, FALSE_D_RISE=.005, SHORT_RECALL_LOSS=.020, SHORT_SUPPORT=20, INTERIOR_MARGIN=50,
                                RESTART_WINDOW=25, RECOVERY_FRAMES=50, MIN_LIVE_WINDOWS=5, MIN_RESTART_EVENTS=20).items():
            self.assertEqual(getattr(m, name), value, name)
        self.assertEqual(m.METHODS, ('control', 'candidate'))

    def test_experiment_a_modules_are_byte_identical_to_the_base_commit(self):
        for name in ('recent_geometry_assembly.py', 'recent_geometry_metrics.py', 'recent_geometry_regimes.py',
                     'recent_geometry_run.py', 'recent_geometry_features.py', 'recent_geometry_training.py',
                     'restart_release.py', 'release_runtime.py', 'gap_liveness.py', 'kickoff_patch.py',
                     'touch_decoder.py', 'touch_evidence.py', 'gap_solver/tactical.py', 'gap_solver/selection.py'):
            try:
                base = subprocess.run(['git', 'show', f'{BASE}:{name}'], cwd=REPO, capture_output=True, check=True).stdout
            except (OSError, subprocess.CalledProcessError):
                self.skipTest('base commit not available')
            self.assertEqual((REPO / name).read_bytes().replace(b'\r\n', b'\n'), base.replace(b'\r\n', b'\n'), name)

    def test_no_existing_file_changed_and_gitignore_is_append_only(self):
        try:
            names = subprocess.run(['git', 'diff', '--name-only', BASE, '--', '.', ':!team_symmetry*.py', ':!tests/test_team_symmetry*',
                                    ':!docs/team-symmetry-protocol.md', ':!reports/team-symmetry', ':!.gitignore'],
                                   cwd=REPO, capture_output=True, text=True, check=True).stdout.split()
            ignore = subprocess.run(['git', 'diff', BASE, '--', '.gitignore'], cwd=REPO, capture_output=True, text=True, check=True).stdout
        except (OSError, subprocess.CalledProcessError):
            self.skipTest('base commit not available')
        self.assertEqual(names, [])
        removed = [l for l in ignore.splitlines() if l.startswith('-') and not l.startswith('---')]
        self.assertEqual(removed, [])


if __name__ == '__main__':
    unittest.main()
