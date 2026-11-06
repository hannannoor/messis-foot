import copy,unittest
import test_temporal_selection as fixtures
try:
    from gap_solver.temporal_acceptance import final_acceptance
except ImportError:
    final_acceptance=None


class FinalAcceptance(unittest.TestCase):
    def test_final_tolerance_and_bootstrap_do_not_erase_validation_rejection(self):
        self.assertIsNotNone(final_acceptance)
        reports,endpoints=fixtures.TemporalTraining.gate_fixture(5)
        reports=reports*4;endpoints=endpoints*4
        result=final_acceptance(reports,endpoints,validation_passed=False,regression_passed=True)
        self.assertFalse(result['passes'])
        self.assertFalse(result['checks']['validation_eligibility'])
        self.assertTrue(result['checks']['paired_bootstrap_lower_bound'])

    def test_large_single_match_decline_fails_despite_positive_mean(self):
        self.assertIsNotNone(final_acceptance)
        reports,endpoints=fixtures.TemporalTraining.gate_fixture(5)
        reports=[copy.deepcopy(reports[0]) for _ in range(8)];endpoints=endpoints*4
        reports[0]['selected']['metrics']['spell_f1_mean']=.47
        result=final_acceptance(reports,endpoints,validation_passed=True,regression_passed=True)
        self.assertFalse(result['checks']['team_spell_match_tolerance'])
        self.assertFalse(result['passes'])
