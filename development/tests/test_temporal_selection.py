import importlib.util
import unittest
import numpy as np

try:
    from gap_solver.temporal_selection import export_boosted,fit_temperature,validation_gate,contiguous_mask
    from gap_solver.temporal import MOTION_FEATURES,PortableBoosted
except ImportError:
    export_boosted=fit_temperature=validation_gate=contiguous_mask=MOTION_FEATURES=PortableBoosted=None


class TemporalTraining(unittest.TestCase):
    @unittest.skipUnless(importlib.util.find_spec('sklearn'),'training-only sklearn unavailable')
    def test_portable_ensemble_reproduces_sklearn_logits(self):
        self.assertIsNotNone(export_boosted,'temporal training/export contract is missing')
        from sklearn.ensemble import GradientBoostingClassifier
        rng=np.random.RandomState(81);x=rng.normal(size=(600,len(MOTION_FEATURES))).astype(np.float32)
        y=(x[:,0]+x[:,1]>.2).astype(np.uint8)
        classifier=GradientBoostingClassifier(n_estimators=7,max_depth=2,min_samples_leaf=5,random_state=81).fit(x,y)
        portable=PortableBoosted(export_boosted(classifier))
        np.testing.assert_allclose([portable.score(row) for row in x],classifier.decision_function(x),rtol=0,atol=1e-12)

    def test_temperature_reduces_demonstrably_overconfident_scores(self):
        self.assertIsNotNone(fit_temperature,'external-only temperature fitting is missing')
        scores=np.array([10.]*8+[-10.]*8);target=np.array([1]*6+[0]*2+[0]*6+[1]*2)
        temperature=fit_temperature(scores,target)
        self.assertGreater(temperature,1.)
        probability=1/(1+np.exp(-10/temperature))
        self.assertAlmostEqual(probability,.75,places=4)

    def test_label_independent_mask_respects_structural_periods_and_exact_rate(self):
        self.assertIsNotNone(contiguous_mask)
        periods=np.array([0]*10+[1]*100+[0]*5+[2]*100)
        mask=contiguous_mask(periods,.3,71)
        np.testing.assert_array_equal(mask,contiguous_mask(periods,.3,71))
        self.assertEqual(int(mask.sum()),60)
        self.assertFalse(mask[periods==0].any())

    def test_zero_hidden_recovery_cannot_pass_by_tying_zero(self):
        self.assertIsNotNone(validation_gate)
        reports,endpoint=self.gate_fixture(hits=0)
        result=validation_gate(reports,endpoint)
        self.assertFalse(result['passes'])
        self.assertFalse(result['checks']['positive_hidden_recovery'])

    def test_weak_new_away_labels_cannot_hide_in_strong_home_labels(self):
        self.assertIsNotNone(validation_gate)
        reports,endpoint=self.gate_fixture(hits=5)
        for report in reports:
            report['change']['newly_resolved_by_label']['A']['correct_fraction']=.7
            report['gap_strata']['per_label']['A']['correct']=700
        self.assertFalse(validation_gate(reports,endpoint)['passes'])

    @staticmethod
    def gate_fixture(hits):
        import copy
        report=dict(baseline=dict(metrics={'spell_f1_mean':.5},coverage={'undecided_fraction':.3}),
            selected=dict(metrics={'spell_f1_mean':.6},coverage={'undecided_fraction':.2}),
            change={'newly_resolved_by_label':{'H':{'frames':1000,'correct_fraction':.99},'A':{'frames':1000,'correct_fraction':.99}}},
            gap_strata={'per_label':{'H':{'frames':1000,'correct':990,'gaps':20},'A':{'frames':1000,'correct':990,'gaps':20}}},
            hidden_opponents={'reference_short_spells':20,'baseline_hits':0,'selected_hits':hits,'selected_false_opposing_spells':0},
            source_quality_gate_passed=True)
        endpoints=copy.deepcopy(report);endpoints['hidden_opponents']['selected_hits']=0
        endpoints['selected']['metrics']['spell_f1_mean']=.59
        return [copy.deepcopy(report),copy.deepcopy(report)],[copy.deepcopy(endpoints),copy.deepcopy(endpoints)]
