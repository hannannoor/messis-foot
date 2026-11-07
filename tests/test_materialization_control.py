import random,unittest
from gap_solver.temporal_metrics import score_temporal
try:
    from gap_solver.materialization_control import materialize_abstentions
except ImportError:
    materialize_abstentions=None


class ScorerMaterialization(unittest.TestCase):
    def test_backfill_forward_fill_and_dead_anchors(self):
        self.assertIsNotNone(materialize_abstentions)
        self.assertEqual(materialize_abstentions(list('XXDXXHXX'),[1]*8),list('DDDDDHHH'))

    def test_period_reset_and_all_unknown_block(self):
        self.assertIsNotNone(materialize_abstentions)
        self.assertEqual(materialize_abstentions(list('HXXXAX'),[1,1,1,2,2,2]),list('HHHAAA'))
        self.assertEqual(materialize_abstentions(list('XXXX'),[0,1,1,0]),list('XDDX'))

    def test_fully_graded_periods_preserve_spell_score_and_do_not_reduce_frame_accuracy(self):
        self.assertIsNotNone(materialize_abstentions);rng=random.Random(1729)
        for _ in range(20):
            gt=[rng.randrange(3) for _ in range(50)];pred=[rng.randrange(4) for _ in range(50)];periods=[1]*25+[2]*25
            new=['HADX'.index(v) for v in materialize_abstentions(['HADX'[v] for v in pred],periods)]
            a=score_temporal(gt,pred,periods);b=score_temporal(gt,new,periods)
            self.assertEqual(a['metrics']['spell_f1_mean'],b['metrics']['spell_f1_mean'])
            self.assertGreaterEqual(b['metrics']['accuracy'],a['metrics']['accuracy'])

    def test_reference_holes_break_general_equivalence_and_are_not_an_input(self):
        self.assertIsNotNone(materialize_abstentions)
        gt=[0,3,1,1];pred=[0,3,3,1];periods=[1]*4
        new=['HADX'.index(v) for v in materialize_abstentions(['HADX'[v] for v in pred],periods)]
        self.assertNotEqual(score_temporal(gt,pred,periods)['metrics']['spell_f1_mean'],score_temporal(gt,new,periods)['metrics']['spell_f1_mean'])
        import inspect
        self.assertEqual(list(inspect.signature(materialize_abstentions).parameters),['labels','periods'])

    def test_malformed_inputs_fail_and_existing_decisions_are_immutable(self):
        self.assertIsNotNone(materialize_abstentions)
        labels=list('HXD');before=list(labels)
        self.assertEqual(materialize_abstentions(labels,[1]*3),list('HHD'));self.assertEqual(labels,before)
        for bad,periods in ((['Q'],[1]),(['H'],[3]),(['H'],[])):
            with self.assertRaises(ValueError):materialize_abstentions(bad,periods)
