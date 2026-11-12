"""Claim-on-entry ledger: caps, ordering, uniqueness, separate parity category."""
import json
from pathlib import Path
import tempfile
import unittest

try:
    import team_shape_run as run
except ImportError:  # pragma: no cover - red phase
    run = None

NATURAL = ('skillcorner-1874553', 'dfl-J03WR9')


class Ledger(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(run, 'team_shape_run is missing')
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.ledger = run.Ledger(self.root / 'claims', self.root / 'access.jsonl')

    def events(self):
        return [json.loads(line) for line in (self.root / 'access.jsonl').read_text().splitlines()]

    def test_caps_are_the_brief_numbers(self):
        self.assertEqual(run.CAPS, dict(fit=2, prediction=100, score=115, feature_pass=200, decoder_pass=300))

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
        with self.assertRaises(run.BudgetError):
            again.claim('prediction', 'x/new')
        self.assertEqual(again.count('prediction'), 100)

    def test_fit_order_and_budget(self):
        with self.assertRaises(run.BudgetError):
            self.ledger.claim('fit', 'candidate')
        self.ledger.claim('fit', 'control')
        self.ledger.claim('fit', 'candidate')
        with self.assertRaises(run.BudgetError):
            self.ledger.claim('fit', 'control')
        with self.assertRaises(run.BudgetError):
            self.ledger.claim('fit', 'third')

    def test_unknown_kind_refused(self):
        with self.assertRaises(run.BudgetError):
            self.ledger.claim('sweep', 'x')

    def test_parity_is_a_separate_category_that_never_touches_science_counts(self):
        for case in run.NATURAL_CASES:
            self.ledger.claim('parity', 'release/' + case)
            self.ledger.claim('parity', 'prefix/' + case)
        self.ledger.claim('parity', 'exporter')
        for kind in run.CAPS:
            self.assertEqual(self.ledger.count(kind), 0)
        self.assertEqual(self.ledger.count('parity'), 31)

    def test_parity_identities_are_bounded_and_unique(self):
        with self.assertRaises(run.BudgetError):
            self.ledger.claim('parity', 'release/not-a-case')
        with self.assertRaises(run.BudgetError):
            self.ledger.claim('parity', 'sweep')
        self.ledger.claim('parity', 'release/dfl-J03WR9')
        with self.assertRaises(run.BudgetError):
            self.ledger.claim('parity', 'release/dfl-J03WR9')

    def test_failed_work_does_not_refund_a_claim(self):
        try:
            self.ledger.claim('score', 'a')
            raise RuntimeError('bug after claim')
        except RuntimeError:
            pass
        self.assertEqual(self.ledger.count('score'), 1)

    def test_unsafe_identity_characters_refused(self):
        for bad in ('../x', 'a\\b', '', 'a' * 300):
            with self.assertRaises(run.BudgetError):
                self.ledger.claim('score', bad)

    def test_case_inventory(self):
        self.assertEqual(len(run.NATURAL_CASES), 15)


if __name__ == '__main__':
    unittest.main()
