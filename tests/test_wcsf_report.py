"""Protect official pooling, support semantics and bounded publication schema."""
import copy
from pathlib import Path
import tempfile
import unittest
import numpy as np


class ReportTests(unittest.TestCase):
    def setUp(self):
        try:
            import wcsf_report
            from wcsf_audit import score_fixed
        except ImportError:self.fail('Missing bounded scoring/report implementation')
        self.api=wcsf_report;self.score=score_fixed

    def case(self,gt=None,pred=None,periods=None):
        from wcsf_audit import METHODS
        if gt is None:gt=np.array([0]*10+[1]*10+[2]*10+[0]*100+[1]*100+[2]*20,dtype=np.uint8)
        if periods is None:periods=np.array([1]*30+[2]*(len(gt)-30),dtype=np.uint8)
        if pred is None:pred=np.array(list(gt[:30])+[2]*(len(gt)-30),dtype=np.uint8)
        return self.score(gt,periods,{METHODS[0]:pred,METHODS[1]:gt.copy(),METHODS[2]:gt.copy()})

    def test_pool_both_halves_counts_not_mean_f1(self):
        r=self.case();c=r['match']['w0-c32-neutral-missing']
        self.assertEqual(c['spells']['per_iou']['0.5']['n_matched'],2)
        self.assertEqual(c['spells']['per_iou']['0.5']['n_missed'],2)
        self.assertAlmostEqual(c['metrics']['spell_f1_mean'],2/3)
        self.assertAlmostEqual(r['halves']['1']['w0-c32-neutral-missing']['metrics']['spell_f1_mean'],1.)
        self.assertAlmostEqual(r['halves']['2']['w0-c32-neutral-missing']['metrics']['spell_f1_mean'],0.)
        self.assertAlmostEqual(r['deltas']['matched-input-w50']['spell_f1_mean'],1/3)
        self.api.validate_report(r)

    def test_wholly_X_half_has_nulls_and_other_half_scores(self):
        gt=np.array([0]*10+[1]*10+[2]*10+[3]*50,dtype=np.uint8)
        r=self.case(gt=gt,pred=gt.copy());empty=r['halves']['2']['w0-c32-neutral-missing']
        self.assertEqual(empty['support']['known'],0)
        self.assertTrue(all(v is None for v in empty['metrics'].values()))
        self.assertEqual(r['match']['w0-c32-neutral-missing']['metrics']['accuracy'],1.)
        self.api.validate_report(r)

    def test_absent_class_official_and_supported_macro_conventions(self):
        gt=np.array([0]*15+[1]*15,dtype=np.uint8);r=self.case(gt,gt,np.ones(30,dtype=np.uint8))
        c=r['match']['w0-c32-neutral-missing'];self.assertEqual(c['metrics']['accuracy'],1.)
        self.assertAlmostEqual(c['metrics']['official_macro_f1'],2/3)
        self.assertIsNone(c['metrics']['supported_macro_f1']);self.assertFalse(r['full_state_complete'])

    def test_event_both_absent_null_but_predicted_only_zero(self):
        gt=np.full(30,2,dtype=np.uint8);p=np.ones(30,dtype=np.uint8)
        none=self.case(gt,gt,np.ones(30,dtype=np.uint8))['match']['w0-c32-neutral-missing']
        predicted=self.case(gt,p,np.ones(30,dtype=np.uint8))['match']['w0-c32-neutral-missing']
        self.assertIsNone(none['metrics']['spell_f1_mean']);self.assertEqual(predicted['metrics']['spell_f1_mean'],0.)
        self.assertIsNone(none['HA_boundaries']['12']['f1'])

    def test_null_operand_delta_is_null(self):
        gt=np.full(30,2,dtype=np.uint8);r=self.case(gt,gt,np.ones(30,dtype=np.uint8))
        self.assertIsNone(r['deltas']['official-convention-w50']['spell_f1_mean'])

    def test_support_nulls_exact_ints_and_ratios(self):
        base=self.case()
        changes=[('boolean',lambda r:r['match']['w0-c32-neutral-missing']['support'].update(known=True)),
                 ('ratio',lambda r:r['match']['w0-c32-neutral-missing']['metrics'].update(accuracy=1.)),
                 ('dict',lambda r:r['match']['w0-c32-neutral-missing']['metrics'].update(accuracy={'values':[1]})),
                 ('zero_support',lambda r:r['match']['w0-c32-neutral-missing']['HA_boundaries']['12'].update(recall=1.))]
        for name,change in changes:
            r=copy.deepcopy(base);change(r)
            with self.subTest(name=name),self.assertRaises(ValueError):self.api.validate_report(r)

    def test_reject_unknown_method_vectors_duplicate_json_keys_and_nonfinite(self):
        for kind in ('method','vector','nonfinite'):
            r=self.case()
            if kind=='method':r['match']['extra']=copy.deepcopy(next(iter(r['match'].values())))
            elif kind=='vector':r['labels']=[0,1,2]
            else:r['match']['w0-c32-neutral-missing']['metrics']['accuracy']=float('nan')
            with self.subTest(kind=kind),self.assertRaises(ValueError):self.api.validate_report(r)
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'duplicate.json';p.write_text('{"schema_version":1,"schema_version":1}')
            with self.assertRaises(ValueError):self.api.read_json(p)

    def test_boundary_latency_and_ambiguity_respect_their_own_support(self):
        for kind in ('latency','ambiguity'):
            r=self.case();row=r['match']['w0-c32-neutral-missing']['HA_boundaries']['12']
            if kind=='latency':row.update(mean_latency_frames=12.5,mean_abs_latency_frames=12.5)
            else:row['n_ambiguous']=row['n_gt']+1
            with self.subTest(kind=kind),self.assertRaises(ValueError):self.api.validate_report(r)


if __name__=='__main__':unittest.main()
