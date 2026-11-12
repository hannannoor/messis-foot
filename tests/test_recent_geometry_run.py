"""The per-case pipeline end to end on synthetic frames with an injected candidate model."""
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

from gap_solver.tactical_model import FROZEN_MODEL
from test_gap_liveness import fixture

try:
    import recent_geometry_run as run
    import recent_geometry_features as rf
except ImportError:  # pragma: no cover - red phase
    run = None


def frames():
    from dataclasses import replace
    out = []
    for i, f in enumerate(fixture(n=1100, gaps=((300, 500), (700, 800)))):
        out.append(replace(f, home_distance=.5 + (i % 7), away_distance=2. + (i % 11) * .7) if f.ball_observed else f)
    return out


def models():
    control = FROZEN_MODEL['model']
    candidate = dict(control, feature_names=list(rf.RESEARCH_FEATURE_NAMES))
    return dict(control=control, candidate=candidate)


class Pipeline(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(run, 'recent_geometry_run is missing')
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.ledger = run.Ledger(self.root / 'claims', self.root / 'access.jsonl')
        self.reference = np.resize(np.asarray([0] * 90 + [1] * 70 + [2] * 40 + [0] * 120 + [3] * 20, dtype=np.uint8), 1100)

    def go(self, regime='natural', **kw):
        return run.run_case_regime(self.ledger, regime, 'dfl-J03WR9', frames(), self.reference, models(),
                                   self.root / ('out-' + regime), **kw)

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
                                  dict(control=m['control'], candidate=flip), self.root / 'out-noise')
        self.assertNotEqual(out['flats']['control'], out['flats']['candidate'])
        solo = run.run_case_regime(run.Ledger(self.root / 'c2', self.root / 'a2.jsonl'), 'noise', 'dfl-J03WR9', frames(),
                                   self.reference, m, self.root / 'out-solo')
        self.assertEqual(out['flats']['control'], solo['flats']['control'])

    def test_stoppage_regime_reports_restart_counts(self):
        out = self.go('stoppage')
        self.assertIn('restart', out['flats']['control'])

    def test_no_rerun_of_the_same_prediction(self):
        self.go()
        with self.assertRaises(run.BudgetError):
            run.run_case_regime(self.ledger, 'natural', 'dfl-J03WR9', frames(), self.reference, models(), self.root / 'again')

    def test_supplied_matrix_skips_the_prep_claim(self):
        matrix = rf.research_matrix(frames())
        self.go(matrix=matrix)
        self.assertEqual(self.ledger.count('feature_pass'), 2)

    def test_reference_dimension_mismatch_stops_before_claims(self):
        with self.assertRaises(ValueError):
            run.run_case_regime(self.ledger, 'natural', 'x', frames(), self.reference[:-1], models(), self.root / 'bad')
        self.assertEqual(self.ledger.count('prediction'), 0)


if __name__ == '__main__':
    unittest.main()
