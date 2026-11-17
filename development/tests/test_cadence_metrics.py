import copy
import unittest
import numpy as np

from cadence_protocol import case_keys,VARIANTS,CONTROL,CANDIDATE
from cadence_fixtures import moving_fixture
from cadence_features import cadence_feature_rows

try:
    from cadence_metrics import diagnostic_metrics,assess_continuation
except ImportError:
    diagnostic_metrics=assess_continuation=None


def fake_receipts():
    rows=[]
    for cohort,match,regime in case_keys():
        variants={}
        for name in VARIANTS:
            improved=name==CANDIDATE and regime.startswith('retain-')
            variants[name]=dict(metrics=dict(spell_f1_mean=.51 if improved else .5,accuracy=.8),
                dead_metrics=dict(n_live=80,n_dead=20 if cohort=='dfl' else 0,
                    false_D=4 if improved else 8,recall=.9 if cohort=='dfl' else None))
        rows.append(dict(cohort=cohort,match=match,regime=regime,variants=variants))
    return rows


class CadenceMetrics(unittest.TestCase):
    def setUp(self):self.assertIsNotNone(diagnostic_metrics,'cadence metrics are not implemented')

    def test_spell_duration_bins_and_matched_recall(self):
        truth=np.asarray([0]*20+[1]*40+[0]*100+[1]*300,dtype=np.uint8)
        report=diagnostic_metrics(truth,truth,np.ones(len(truth),dtype=np.uint8),())
        for name in ('short','medium','long','very_long'):
            row=report['spell_duration'][name]
            self.assertEqual(row['n_gt'],1)
            self.assertEqual(row['per_iou']['0.5']['recall'],1.)
        self.assertEqual(report['HA_boundaries']['12']['n_matched'],3)

    def test_pair_typed_latency_and_misses(self):
        truth=np.asarray([0]*30+[1]*30+[0]*30,dtype=np.uint8)
        prediction=np.asarray([0]*35+[1]*25+[0]*30,dtype=np.uint8)
        row=diagnostic_metrics(truth,prediction,[1]*90,())['HA_boundaries']['12']
        self.assertEqual(row['n_matched'],2)
        self.assertEqual(row['mean_latency_frames'],2.5)
        missed=diagnostic_metrics(truth,np.zeros(90,dtype=np.uint8),[1]*90,())['HA_boundaries']['12']
        self.assertEqual(missed['n_missed'],2)
        self.assertIsNone(missed['mean_latency_frames'])

    def test_matching_never_crosses_reference_unknown_runs(self):
        truth=np.asarray([0]*5+[1]*5+[3]+[0]*5+[1]*5,dtype=np.uint8)
        prediction=np.asarray([0]*12+[1]*9,dtype=np.uint8)
        row=diagnostic_metrics(truth,prediction,[1]*21,())['HA_boundaries']['12']
        self.assertEqual(row['n_matched'],1)
        self.assertEqual(row['n_missed'],1)
        self.assertEqual(row['mean_latency_frames'],-4.)

    def test_outside_input_periods_is_not_scored(self):
        report=diagnostic_metrics([0,1],[0,1],[0,0],())
        self.assertEqual(sum(row['n_gt'] for row in report['spell_duration'].values()),0)
        self.assertEqual(report['HA_boundaries']['25']['n_gt'],0)

    def test_valid_zero_and_unknown_are_separate(self):
        frames=moving_fixture(6,2)
        sidecars=list(cadence_feature_rows(frames))
        report=diagnostic_metrics([0]*6,[0]*6,[1]*6,sidecars)['observation']
        self.assertEqual(report['velocity_available_rows'],2)
        self.assertEqual(report['velocity_unavailable_rows'],4)
        self.assertEqual(report['repaired_rows'],2)
        self.assertEqual(report['observed_ball_rows'],3)

    def test_seven_checks_and_automatic_continuation(self):
        report=assess_continuation(fake_receipts())
        self.assertEqual(len(report['checks']),7)
        self.assertTrue(report['aggregate_gate_passed'])
        self.assertFalse(report['per_match_review_required'])
        self.assertTrue(report['automatic_continuation_allowed'])
        self.assertFalse(report['fresh_holdout'])

    def test_mean_gain_cannot_hide_per_match_cadence_loss(self):
        rows=fake_receipts()
        for row in rows:
            if row['cohort']=='skillcorner' and row['regime'].startswith('retain-'):
                row['variants'][CANDIDATE]['metrics']['spell_f1_mean']=.49 if row['match']=='1874553' else .6
        report=assess_continuation(rows)
        self.assertTrue(report['aggregate_gate_passed'])
        self.assertTrue(report['per_match_review_required'])
        self.assertFalse(report['automatic_continuation_allowed'])
        self.assertTrue(report['cases'])

    def test_missing_dead_support_is_not_perfect_recall(self):
        rows=fake_receipts()
        for row in rows:
            if row['cohort']=='dfl':
                for name in VARIANTS:
                    row['variants'][name]['dead_metrics'].update(n_dead=0,recall=None)
        report=assess_continuation(rows)
        self.assertFalse(report['checks']['natural_dfl_D_recall_preserved'])
        self.assertFalse(report['checks']['masked_dfl_D_recall_preserved'])
        self.assertFalse(report['automatic_continuation_allowed'])

    def test_preservation_has_no_acceptance_tolerance(self):
        rows=fake_receipts()
        for row in rows:
            if row['regime']=='natural':row['variants'][CANDIDATE]['metrics']['accuracy']=.8-1e-10
        report=assess_continuation(rows)
        self.assertFalse(report['checks']['natural_accuracy_preserved'])

    def test_duplicate_or_missing_cases_fail(self):
        rows=fake_receipts()
        with self.assertRaises(ValueError):assess_continuation(rows[:-1])
        rows[-1]=copy.deepcopy(rows[0])
        with self.assertRaises(ValueError):assess_continuation(rows)

    def test_nonfinite_metric_fails(self):
        rows=fake_receipts();rows[0]['variants'][CANDIDATE]['metrics']['spell_f1_mean']=float('nan')
        with self.assertRaises(ValueError):assess_continuation(rows)

    def test_invalid_label_shape_fails(self):
        with self.assertRaises(ValueError):diagnostic_metrics([0,1],[0],[1,1],())
        with self.assertRaises(ValueError):diagnostic_metrics([0,9],[0,0],[1,1],())


if __name__=='__main__':unittest.main()
