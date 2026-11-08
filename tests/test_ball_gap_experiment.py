import json,tempfile,unittest
from pathlib import Path
import numpy as np
from gap_solver.accuracy_protocol import SPLITS
try:
    from ball_gap_experiment import dead_metrics,load_availability,assess,store_identical,seal_reports,verify_report_seal,sha256,POLICY_ID
except ImportError:
    dead_metrics=load_availability=assess=store_identical=seal_reports=verify_report_seal=sha256=None
    POLICY_ID='w0-c32-neutral-missing'


def reports(stage):
    result=[]
    for cohort,ids in SPLITS[stage].items():
        for match in ids:
            for regime in ('natural','masked'):
                variants={}
                for name in ('w0-c32',POLICY_ID):
                    new=name==POLICY_ID
                    variants[name]=dict(metrics=dict(spell_f1_mean=.6,accuracy=.8+(.02 if new and regime=='masked' else 0)),
                        dead_metrics=dict(false_D_fraction=.01 if new else .02,recall=.9 if cohort=='dfl' else None))
                result.append(dict(stage=stage,cohort=cohort,match=match,regime=regime,variants=variants))
    return result


class BallGapExperiment(unittest.TestCase):
    def setUp(self):self.assertIsNotNone(dead_metrics,'bound ball-gap experiment absent')

    def test_false_and_missed_dead_have_explicit_denominators(self):
        m=dead_metrics(np.array([0,1,2,2,3]),np.array([2,1,2,0,2]),np.ones(5,dtype=np.uint8))
        self.assertEqual((m['n_live'],m['n_dead'],m['false_D'],m['missed_D'],m['true_D']),(2,2,1,1,1))
        self.assertEqual(m['false_D_fraction'],.5);self.assertEqual(m['recall'],.5);self.assertEqual(m['precision'],.5)

    def test_dead_intervals_split_at_unknown_and_period_boundaries(self):
        for gt,periods in [([2,2,3,2,2],[1]*5),([2]*4,[1,1,2,2])]:
            m=dead_metrics(np.array(gt),np.array(gt),np.array(periods))['dead_interval']
            self.assertEqual(m['n_gt'],2);self.assertEqual(m['n_pred'],2);self.assertEqual(m['mean_f1'],1.)
            self.assertEqual(m['per_iou']['0.7']['n_matched'],2)

    def test_empty_dead_support_is_null_and_not_perfect(self):
        m=dead_metrics(np.array([0,1]),np.array([0,1]),np.array([1,1]))
        self.assertIsNone(m['recall']);self.assertIsNone(m['precision']);self.assertIsNone(m['dead_interval']['mean_f1'])
        rows=reports('validation');next(r for r in rows if r['cohort']=='dfl')['variants'][POLICY_ID]['dead_metrics']['recall']=None
        self.assertFalse(assess(rows,'validation')['eligible'])

    def test_each_acceptance_rule_is_real_and_exact_membership_is_required(self):
        rows=reports('validation');self.assertTrue(assess(rows,'validation')['eligible'])
        bad=reports('validation');bad[0]['variants'][POLICY_ID]['metrics']['spell_f1_mean']=.59
        self.assertFalse(assess(bad,'validation')['eligible'])
        bad=reports('validation');bad[0]['variants'][POLICY_ID]['metrics']['accuracy']=.79
        self.assertFalse(assess(bad,'validation')['eligible'])
        for cohort,regime,section,field,value in [('skillcorner','masked','metrics','accuracy',.8),('skillcorner','masked','dead_metrics','false_D_fraction',.02),('dfl','masked','metrics','spell_f1_mean',.59),('dfl','natural','dead_metrics','recall',.89),('dfl','masked','dead_metrics','recall',.89)]:
            bad=reports('validation')
            for r in bad:
                if r['cohort']==cohort and r['regime']==regime:r['variants'][POLICY_ID][section][field]=value
            self.assertFalse(assess(bad,'validation')['eligible'],(cohort,regime,field))
        for bad in (rows[:-1],rows+[rows[0]]):
            with self.assertRaises(ValueError):assess(bad,'validation')

    def test_availability_binds_feature_bytes_periods_and_exact_input_mask(self):
        from gap_solver.temporal_selection import contiguous_mask
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'features.npz';periods=np.ones(100,dtype=np.uint8)
            ball=np.ones((100,2));ball[2]=np.nan;np.savez(p,periods=periods,ball=ball)
            pinned=sha256(p)
            self.assertEqual(load_availability(p,pinned,periods,'skillcorner','natural').sum(),99)
            expected=np.isfinite(ball).all(axis=1)&~contiguous_mask(periods,.3,1729)
            np.testing.assert_array_equal(load_availability(p,pinned,periods,'skillcorner','masked'),expected)
            with self.assertRaises(ValueError):load_availability(p,pinned,np.zeros(100,dtype=np.uint8),'skillcorner','natural')
            with p.open('ab') as h:h.write(b'changed')
            with self.assertRaises(ValueError):load_availability(p,pinned,periods,'skillcorner','natural')

    def test_disposition_and_receipts_cannot_be_silently_rewritten(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p=root/'case.json';store_identical(p,{'score':.5})
            seal=root/'seal.json';seal_reports([p],seal)
            self.assertEqual(verify_report_seal([p],seal),{'case.json':sha256(p)})
            with self.assertRaises(ValueError):store_identical(p,{'score':.6})
            p.write_text(json.dumps({'score':.6}))
            with self.assertRaises(ValueError):verify_report_seal([p],seal)

    def test_new_metrics_pass_strict_export_without_event_arrays(self):
        from accuracy_evidence import assert_public_report
        report=dead_metrics(np.array([0,2,2,1]),np.array([0,2,2,1]),np.ones(4,dtype=np.uint8))
        assert_public_report(report)
        with self.assertRaises(ValueError):assert_public_report(report|{'hidden':[[0,1,2]]})

if __name__=='__main__':unittest.main()
