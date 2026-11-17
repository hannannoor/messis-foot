import copy
import unittest
import numpy as np
try:
    import memory_ablation_metrics as metrics
except ImportError:
    metrics=None


def codes(text):return np.asarray(['HADX'.index(s) for s in text],dtype=np.uint8)


def score(value=.5,cohort='dfl'):
    return dict(metrics=dict(spell_f1_mean=value),support=dict(H=100,A=100,D=0 if cohort=='skillcorner' else 100),
        predicted_on_known=dict(H=100,A=100,D=100),dead=dict(precision=None if cohort=='skillcorner' else .9,recall=None if cohort=='skillcorner' else .9),
        known_live_false_D_rate=.01,short_spells=dict(n_gt=25,n_matched=20,recall=.8))


class MemoryMetrics(unittest.TestCase):
    def setUp(self):self.assertIsNotNone(metrics,'Bounded scoring/gates are missing')

    def receipts(self):
        return [dict(case_id=cid,cohort=cohort,role=role,regime=regime,variants={
            'control':score(.5,cohort),'memory-ablated':score(.51,cohort)})
            for cid,cohort,role in metrics.MATCHES for regime in metrics.REGIMES]

    def test_literal_all_state_short_spell_and_boundary_counts(self):
        result=metrics.score_variant(codes('HHDDAA'),codes('HHHHAA'),[1]*6,[True,False]*3)
        self.assertEqual(result['confusion'],[[2,0,0,0],[0,2,0,0],[2,0,0,0],[0,0,0,0]])
        self.assertAlmostEqual(result['metrics']['accuracy'],2/3)
        self.assertEqual(result['short_spells'],dict(n_gt=2,n_matched=2,recall=1.))
        self.assertEqual(result['spells']['per_iou']['0.5']['n_matched'],2)
        self.assertEqual(result['spells']['per_iou']['0.7']['n_matched'],1)
        self.assertAlmostEqual(result['metrics']['spell_f1_mean'],.8)
        for tolerance in ('12','25'):
            all_states=result['all_state_boundaries'][tolerance];ha=result['HA_boundaries'][tolerance]
            self.assertEqual((all_states['n_gt'],all_states['n_pred'],all_states['n_matched']),(2,1,1))
            self.assertEqual((ha['n_gt'],ha['n_pred'],ha['n_spurious']),(0,1,1))
        self.assertEqual(result['strata']['ball_observed']['known'],3)
        self.assertEqual(result['strata']['ball_missing']['known'],3)

    def test_unequal_period_pooling_and_zero_support_conventions(self):
        result=metrics.score_variant(codes('HHHHAHA'),codes('HHHDDDD'),[1,1,1,2,2,2,2],[True]*7)
        self.assertEqual((result['spells']['n_gt'],result['spells']['n_pred']),(5,1))
        self.assertAlmostEqual(result['metrics']['spell_f1_mean'],1/3)
        dead=metrics.score_variant(codes('DDDDDD'),codes('DDDDDD'),[1]*6,[True]*6)
        self.assertEqual(dead['metrics']['spell_f1_mean'],0.)
        self.assertIsNone(dead['short_spells']['recall']);self.assertEqual(dead['dead']['recall'],1.)
        unknown=metrics.score_variant(codes('XXXXXX'),codes('HHHHHH'),[1]*6,[True]*6)
        self.assertIsNone(unknown['metrics']['accuracy']);self.assertIsNone(unknown['metrics']['spell_f1_mean'])
        self.assertIsNone(unknown['known_live_false_D_rate'])

    def test_primary_weights_providers_and_excludes_fitting_overlap(self):
        receipts=self.receipts()
        for row in receipts:
            candidate=row['variants']['memory-ablated']
            if row['role']=='fitting-overlap':candidate['metrics']['spell_f1_mean']=1.
            else:candidate['metrics']['spell_f1_mean']={'skillcorner':.51,'dfl':.52,'wcsf':.53}[row['cohort']]
        result=metrics.summarize_cases(receipts)
        self.assertEqual(result['primary_matches'],13);self.assertEqual(result['case_count'],30)
        self.assertAlmostEqual(result['primary']['natural']['control'],.5)
        self.assertAlmostEqual(result['primary']['natural']['memory-ablated'],.52)
        self.assertEqual(result['decision'],'pass')

    def test_exact_primary_edge_fails_and_small_gain_passes(self):
        for delta,want in ((0.,'fail'),(1e-6,'fail'),(2e-6,'pass')):
            receipts=self.receipts()
            for row in receipts:
                row['variants']['control']['metrics']['spell_f1_mean']=0.
                row['variants']['memory-ablated']['metrics']['spell_f1_mean']=delta
            self.assertEqual(metrics.summarize_cases(receipts)['checks']['natural_primary_gain']['status'],want)

    def test_provider_case_mask_D_and_collapse_failures_are_not_hidden(self):
        for kind in ('provider','case','masked','D','false_D','collapse'):
            receipts=self.receipts()
            if kind=='provider':
                for row in receipts:
                    if row['cohort']=='wcsf':row['variants']['memory-ablated']['metrics']['spell_f1_mean']=.49
            elif kind=='case':receipts[0]['variants']['memory-ablated']['metrics']['spell_f1_mean']=.48
            elif kind=='masked':
                for row in receipts:
                    if row['regime']!='natural':row['variants']['memory-ablated']['metrics']['spell_f1_mean']=.49
            elif kind=='D':next(r for r in receipts if r['cohort']=='dfl')['variants']['memory-ablated']['dead']['recall']=.88
            elif kind=='false_D':receipts[0]['variants']['memory-ablated']['known_live_false_D_rate']=.021
            else:receipts[0]['variants']['memory-ablated']['predicted_on_known']['A']=0
            with self.subTest(kind=kind):self.assertEqual(metrics.summarize_cases(receipts)['decision'],'fail')

    def test_short_support_and_required_missing_support_are_explicit(self):
        for n,baseline,candidate,want in ((0,0,0,'non_applicable'),(19,10,9,'fail'),(20,10,9,'fail'),(50,40,39,'pass')):
            receipts=self.receipts()
            for row in receipts:
                for mode,count in (('control',baseline),('memory-ablated',candidate)):
                    row['variants'][mode]['short_spells']=dict(n_gt=n,n_matched=count,recall=count/n if n else None)
            with self.subTest(n=n):self.assertEqual(metrics.summarize_cases(receipts)['checks']['short_spell_safeguard']['status'],want)
        receipts=self.receipts();next(r for r in receipts if r['cohort']=='dfl')['variants']['memory-ablated']['dead']['precision']=None
        self.assertEqual(metrics.summarize_cases(receipts)['decision'],'unresolved')

    def test_threshold_slack_and_exact_inventory(self):
        receipts=self.receipts();receipts[0]['variants']['memory-ablated']['metrics']['spell_f1_mean']=.49-5e-7
        self.assertEqual(metrics.summarize_cases(receipts)['checks']['fit_disjoint_case_spell_loss']['status'],'pass')
        receipts[0]['variants']['memory-ablated']['metrics']['spell_f1_mean']=.49-2e-6
        self.assertEqual(metrics.summarize_cases(receipts)['checks']['fit_disjoint_case_spell_loss']['status'],'fail')
        for bad in (receipts[:-1],receipts+[copy.deepcopy(receipts[0])]):
            with self.assertRaises(ValueError):metrics.summarize_cases(bad)
        receipts[0]['role']='fitting-overlap'
        with self.assertRaises(ValueError):metrics.summarize_cases(receipts)


if __name__=='__main__':unittest.main()
