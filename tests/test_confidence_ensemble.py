import unittest
from gap_solver.core import Decision,Frame
try:
    from gap_solver.confidence_ensemble import aggregate_decisions
except ImportError:
    aggregate_decisions=None


def ds(labels):return [Decision(x) for x in labels]


class ConfidenceEnsemble(unittest.TestCase):
    def test_supported_agreement_is_a_subset_even_for_inconsistent_caller_votes(self):
        self.assertIsNotNone(aggregate_decisions)
        result=aggregate_decisions([Frame()],ds('X'),ds('H'),ds('A'),ds('A'))
        self.assertEqual(result['supported_head_agreement_on_X'][0].label,'X')

    def test_unmeasured_dead_assignment_is_counted_without_claiming_correctness(self):
        import ablate_ensemble as driver
        self.assertTrue(hasattr(driver,'outside_reference_counts'))
        self.assertEqual(driver.outside_reference_counts([0,3],[1,1],[0,3],[0,2]),{'H':0,'A':0,'D':1})

    def test_receipt_requires_all_three_comparisons(self):
        import ablate_ensemble as driver
        import hashlib,tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'predictions.npz';path.write_bytes(b'fixed')
            report=dict(identity={},variants={},prediction_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
            with self.assertRaises(ValueError):driver.check_receipt(report,{},path)

    def test_agreement_fills_only_matching_team_choices_and_support_stays_distinct(self):
        self.assertIsNotNone(aggregate_decisions)
        frames=[Frame() for _ in range(4)]
        result=aggregate_decisions(frames,ds('XXXX'),ds('HAAH'),ds('HAHD'),ds('HXAH'))
        self.assertEqual(''.join(d.label for d in result['gated_plus_raw_HAD']), 'HAHD')
        self.assertEqual(''.join(d.label for d in result['head_agreement_on_X']), 'HAXX')
        self.assertEqual(''.join(d.label for d in result['supported_head_agreement_on_X']), 'HXXX')

    def test_current_decisions_and_structural_unknown_are_preserved(self):
        self.assertIsNotNone(aggregate_decisions)
        frames=[Frame(),Frame(),Frame(),Frame(period=0)]
        result=aggregate_decisions(frames,ds('HADX'),ds('AAHX'),ds('DAHX'),ds('AAHX'))
        self.assertTrue(all(''.join(d.label for d in values)=='HADX' for values in result.values()))

    def test_abstention_is_not_an_agreeing_vote(self):
        self.assertIsNotNone(aggregate_decisions)
        result=aggregate_decisions([Frame(),Frame()],ds('XX'),ds('HX'),ds('XX'),ds('XX'))
        self.assertTrue(all(''.join(d.label for d in values)=='XX' for values in result.values()))

    def test_bad_dimensions_or_labels_fail_without_mutation(self):
        self.assertIsNotNone(aggregate_decisions)
        baseline=ds('X');before=list(baseline)
        with self.assertRaises(ValueError):aggregate_decisions([Frame()],baseline,ds('HA'),ds('H'),ds('H'))
        with self.assertRaises(ValueError):aggregate_decisions([Frame()],baseline,ds('Q'),ds('H'),ds('H'))
        self.assertEqual(baseline,before)
