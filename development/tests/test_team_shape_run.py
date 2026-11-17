"""The per-case pipeline end to end on synthetic frames with an injected candidate model."""
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

from gap_solver.tactical_model import FROZEN_MODEL
from test_gap_liveness import fixture

try:
    import team_shape_run as run
    import team_shape_features as rf
except ImportError:  # pragma: no cover - red phase
    run = None


def old_frames():
    from dataclasses import replace
    out = []
    for i, f in enumerate(fixture(n=1100, gaps=((300, 500), (700, 800)))):
        out.append(replace(f, home_distance=.5 + (i % 7), away_distance=2. + (i % 11) * .7) if f.ball_observed else f)
    return out



def frames():
    from dataclasses import replace
    return [replace(f, home_xy=tuple((20.+j,34.) for j in range(7)),
                    away_xy=tuple((80.+j,34.) for j in range(7)),
                    home_ids=tuple(range(7)),away_ids=tuple(range(10,17))) for f in old_frames()]


def models():
    control = FROZEN_MODEL['model']
    candidate = dict(control, feature_names=list(rf.RESEARCH_FEATURE_NAMES))
    return dict(control=control, candidate=candidate)


class Pipeline(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(run, 'team_shape_run is missing')
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.ledger = run.Ledger(self.root / 'claims', self.root / 'access.jsonl')
        self.reference = np.resize(np.asarray([0] * 90 + [1] * 70 + [2] * 40 + [0] * 120 + [3] * 20, dtype=np.uint8), 1100)

    def go(self, regime='natural', **kw):
        return run.run_case_regime(self.ledger, regime, 'dfl-J03WR9', frames(), self.reference, models(),
                                   self.root / ('out-' + regime), pitch_midpoint=50., **kw)

    def test_budget_claimed_exactly_and_before_use(self):
        self.go()
        self.assertEqual({k: self.ledger.count(k) for k in run.CAPS},
                         dict(fit=0, prediction=2, score=2, feature_pass=3, decoder_pass=4))
        events = [json.loads(l)['event'] for l in (self.root / 'access.jsonl').read_text().splitlines()]
        self.assertEqual(events[0], 'feature_pass_entry')
        self.assertLess(events.index('prediction_entry'), events.index('score_entry'))

    def test_identical_models_give_identical_methods_and_a_public_safe_receipt(self):
        out = self.go()
        self.assertEqual(out['flats']['control'], out['flats']['candidate'])
        from accuracy_evidence import assert_public_report
        assert_public_report(out)
        self.assertTrue((self.root / 'out-natural' / 'control.npz').is_file())

    def test_a_different_candidate_changes_only_the_candidate(self):
        m = models()
        flip = dict(m['candidate'])
        flip['probabilities'] = [[p[1], p[0], p[2]] for p in m['candidate']['probabilities']]
        out = run.run_case_regime(self.ledger, 'noise', 'dfl-J03WR9', frames(), self.reference,
                                  dict(control=m['control'], candidate=flip), self.root / 'out-noise', pitch_midpoint=50.)
        self.assertNotEqual(out['flats']['control'], out['flats']['candidate'])
        solo = run.run_case_regime(run.Ledger(self.root / 'c2', self.root / 'a2.jsonl'), 'noise', 'dfl-J03WR9', frames(),
                                   self.reference, m, self.root / 'out-solo', pitch_midpoint=50.)
        self.assertEqual(out['flats']['control'], solo['flats']['control'])

    def test_stoppage_regime_reports_restart_counts(self):
        out = self.go('stoppage')
        self.assertIn('restart', out['flats']['control'])

    def test_no_rerun_of_the_same_prediction(self):
        self.go()
        with self.assertRaises(run.BudgetError):
            run.run_case_regime(self.ledger, 'natural', 'dfl-J03WR9', frames(), self.reference, models(), self.root / 'again', pitch_midpoint=50.)

    def test_supplied_matrix_skips_the_prep_claim(self):
        matrix = rf.research_matrix(frames(), pitch_midpoint=50.)
        self.go(matrix=matrix)
        self.assertEqual(self.ledger.count('feature_pass'), 2)

    def test_reference_dimension_mismatch_stops_before_claims(self):
        with self.assertRaises(ValueError):
            run.run_case_regime(self.ledger, 'natural', 'x', frames(), self.reference[:-1], models(), self.root / 'bad')
        self.assertEqual(self.ledger.count('prediction'), 0)

    def test_noise_generator_has_fixed_new_seed_and_preserves_players(self):
        import hashlib, random
        source = frames()
        seed = int(hashlib.sha256(b'team-shape-jitter-v1:1729:dfl-J03WR9').hexdigest()[:8],16)
        rng = random.Random(seed)
        out = run.add_visible_ball_noise(source,'dfl-J03WR9')
        self.assertEqual(out[0].ball_x,source[0].ball_x+rng.gauss(0,.25))
        self.assertEqual(out[0].ball_y,source[0].ball_y+rng.gauss(0,.25))
        for a,b in zip(source,out):
            self.assertEqual(a.home_xy,b.home_xy)
            self.assertEqual(a.away_ids,b.away_ids)
            self.assertEqual(a.ball_observed,b.ball_observed)

    def test_training_parity_claims_do_not_consume_science_budget(self):
        for match in ('J03WOH','J03WOY','J03WPY','J03WMX'):
            self.ledger.claim('parity','training/'+match)
        self.assertEqual(self.ledger.count('parity'),4)
        self.assertEqual(sum(self.ledger.count(k) for k in run.CAPS),0)

    def test_training_preparation_claims_both_control_and_candidate_passes(self):
        run.claim_training_preparation(self.ledger)
        self.assertEqual(self.ledger.count('feature_pass'),16)

    def test_hidden_live_mechanism_uses_exact_mask_inside_existing_score_bundle(self):
        mask=np.zeros(1100,bool)
        mask[100:110]=True
        out=self.go('live-gap',hidden_live=mask)
        self.assertEqual(self.ledger.count('score'),2)
        self.assertEqual(out['hidden_live']['rows'],10)
        for method in ('control','candidate'):
            final=np.load(self.root/'out-live-gap'/(method+'.npz'))['final']
            expected=int((final[mask]==self.reference[mask]).sum())
            self.assertEqual(out['hidden_live'][method]['correct'],expected)
            self.assertEqual(out['hidden_live'][method]['strict_team_accuracy'],expected/10)

    def test_calendar_cutoffs_are_enforced_exactly_in_singapore_time(self):
        from datetime import datetime,timezone,timedelta
        local=timezone(timedelta(hours=8))
        run.enforce_cutoff('natural',datetime(2026,11,14,23,59,tzinfo=local))
        with self.assertRaises(ValueError):
            run.enforce_cutoff('natural',datetime(2026,11,14,23,59,1,tzinfo=local))
        run.enforce_cutoff('stress',datetime(2026,11,15,12,0,tzinfo=local))
        with self.assertRaises(ValueError):
            run.enforce_cutoff('stress',datetime(2026,11,15,12,0,1,tzinfo=local))

    def test_coverage_requires_committed_final_verdict(self):
        with self.assertRaises(ValueError):
            run.require_coverage_verdict({'verdict':'INCOMPLETE'},True)
        with self.assertRaises(ValueError):
            run.require_coverage_verdict({'verdict':'FAIL'},False)
        run.require_coverage_verdict({'verdict':'FAIL'},True)

    def test_coverage_aggregates_player_counts_and_support_without_ball(self):
        from dataclasses import replace
        source=[replace(f,ball_x=None,ball_y=None,home_distance=None,away_distance=None) for f in frames()]
        out=run.coverage_aggregate([run.coverage_components(source)])
        self.assertEqual(out['graded_rows'],1100)
        self.assertEqual(out['home']['shape_valid_share'],1.)
        self.assertEqual(out['away']['counted_players'],dict(p10=7.,p50=7.,p90=7.))
        self.assertEqual(out['shape_support_share'],1075/1100)

    def test_skillcorner_coverage_adapter_never_needs_reference_container(self):
        from gap_solver.motion import motion_frame
        feature=self.root/'geometry.features.npz'
        metadata=self.root/'geometry.metadata.json'
        xy=np.zeros((2,7,2),np.float32)
        np.savez(feature,periods=np.ones(2,np.uint8),home_count=np.full(2,7),away_count=np.full(2,7),
                 home_xy=xy,away_xy=xy,home_ids=np.tile(np.arange(7),(2,1)),
                 away_ids=np.tile(np.arange(10,17),(2,1)),flags=np.ones((2,1),np.uint8))
        metadata.write_text(json.dumps({'notes':{}}))
        result=run.geometry_only_frames('skillcorner-synthetic',{'files':{'case/.features.npz':feature,
                                                                        'case/.metadata.json':metadata}})
        self.assertEqual(len(result),2)
        self.assertEqual(len(result[0].home_xy),7)
        self.assertFalse(result[0].ball_observed)

    def test_recorded_operational_stop_refuses_science_and_coverage(self):
        run.require_open_study(self.root)
        (self.root/'stop.json').write_text('{}')
        with self.assertRaisesRegex(ValueError,'stopped'):
            run.require_open_study(self.root)

    def test_late_final_verdict_records_stop_instead_of_allowing_pass(self):
        from datetime import datetime,timezone
        run.verdict_cutoff(self.root,datetime(2026,11,15,4,0,tzinfo=timezone.utc))
        self.assertFalse((self.root/'stop.json').exists())
        run.verdict_cutoff(self.root,datetime(2026,11,15,4,0,1,tzinfo=timezone.utc))
        self.assertEqual(json.loads((self.root/'stop.json').read_text())['command'],'full-verdict-cutoff')


if __name__ == '__main__':
    unittest.main()
