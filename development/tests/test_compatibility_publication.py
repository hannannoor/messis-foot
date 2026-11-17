import unittest
try:
    from audit_anonymous_compatibility import aggregate_score
except ImportError:
    aggregate_score=None


class AggregatePublication(unittest.TestCase):
    def test_only_named_aggregate_metrics_are_exported_never_event_arrays(self):
        self.assertIsNotNone(aggregate_score,'aggregate score export is missing')
        report={'selected':{'metrics':{'accuracy':.75,'spell_f1_mean':.5,'n_gt_spells':4,
            'transitions':{'H':{'pairs':[[2,3]],'missed':[4],'spurious':[5]}},'gt_frame':42},
            'coverage':{'undecided_fraction':.2,'graded_frames':100,'reference':[1,2,3]}}}
        result=aggregate_score(report)
        self.assertEqual(result['metrics'],{'accuracy':.75,'spell_f1_mean':.5,'n_gt_spells':4})
        self.assertEqual(result['coverage']['undecided_fraction'],.2)
        def check(value):
            if isinstance(value,dict):
                self.assertFalse(set(value)&{'pairs','missed','spurious','gt_frame','reference'})
                for v in value.values():check(v)
            else:self.assertIsInstance(value,(float,int,type(None)))
        check(result)

if __name__=='__main__':unittest.main()
