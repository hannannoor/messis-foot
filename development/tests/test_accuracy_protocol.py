import tempfile
from pathlib import Path
import unittest
try:
    from gap_solver.accuracy_protocol import PARAMETERS,select_validation,hash_files,require_files,assert_aggregate
except ImportError:
    PARAMETERS=();select_validation=hash_files=require_files=assert_aggregate=None


def selection_reports():
    result=[]
    for cohort,match in [('dfl','J03WQQ'),('skillcorner',2006229),('skillcorner',2006363)]:
        variants={name:{'metrics':{'spell_f1_mean':.4,'macro_f1':.5}} for name,_,_ in PARAMETERS}
        variants['agreement-plus-carry']={'metrics':{'spell_f1_mean':.3,'macro_f1':.5}}
        result.append(dict(cohort=cohort,match=match,regime='natural',variants=variants))
    return result


class AccuracyProtocol(unittest.TestCase):
    def setUp(self):self.assertIsNotNone(select_validation,'prospective accuracy selection missing')

    def test_provider_balance_and_named_tie_breaks(self):
        reports=selection_reports();a,b=PARAMETERS[:2]
        # A provider-balanced score=.6 beats B=.55; match-pooled A=.533 loses B=.6.
        for r in reports:
            r['variants'][a[0]]['metrics']['spell_f1_mean']=.8 if r['cohort']=='dfl' else .4
            r['variants'][b[0]]['metrics']['spell_f1_mean']=.4 if r['cohort']=='dfl' else .7
        selected=select_validation(reports)
        self.assertEqual(selected['selected_id'],a[0]);self.assertAlmostEqual(selected['score'],.6)
        reports=selection_reports();reports[0]['variants'][b[0]]['metrics']['macro_f1']=.8
        self.assertEqual(select_validation(reports)['selected_id'],b[0])

    def test_incomplete_duplicate_regression_and_nonfinite_results_rejected(self):
        for mode in ('missing','duplicate','regression','variants','nonfinite'):
            reports=selection_reports()
            if mode=='missing':reports.pop()
            if mode=='duplicate':reports.append(reports[0])
            if mode=='regression':reports[0]['match']='J03WR9'
            if mode=='variants':reports[0]['variants'].pop(PARAMETERS[0][0])
            if mode=='nonfinite':reports[0]['variants'][PARAMETERS[0][0]]['metrics']['spell_f1_mean']=float('nan')
            with self.subTest(mode=mode):
                with self.assertRaises(ValueError):select_validation(reports)

    def test_mutated_consumed_file_fails_binding(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'source';path.write_text('before');paths={'source':path};expected=hash_files(paths)
            require_files(expected,paths);path.write_text('after')
            with self.assertRaises(ValueError):require_files(expected,paths)

    def test_recursive_aggregate_export_rejects_event_and_per_frame_fields(self):
        assert_aggregate({'confusion':[[2,1],[1,3]],'metrics':{'accuracy':.75}})
        for key in ('pairs','missed','spurious','prediction','reference','home_xy','source_frames'):
            with self.assertRaises(ValueError):assert_aggregate({'nested':[{key:[1,2]}]})

if __name__=='__main__':unittest.main()
