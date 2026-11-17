import unittest
from gap_solver.materialization_control import materialize_abstentions
try:
    from ball_gap_policy import decode_ball_gap
except ImportError:
    decode_ball_gap=None


class BallGapPolicy(unittest.TestCase):
    def setUp(self):self.assertIsNotNone(decode_ball_gap,'neutral missing-ball policy absent')

    def test_missing_D_scores_do_not_invent_a_stoppage_between_live_observations(self):
        supports=[(1,0,0)]*30+[(0,0,1)]*200+[(1,0,0)]*30
        labels,counts=decode_ball_gap(supports,[1]*260,[True]*260,[True]*30+[False]*200+[True]*30)
        self.assertEqual(labels,['H']*260)
        self.assertEqual(counts,dict(neutral_active_usable_rows=200,unsupported_segments=0,unsupported_active_rows=0))

    def test_observed_stationary_dead_and_all_three_positive_states_survive(self):
        supports=[(1,0,0)]*30+[(0,1,0)]*30+[(0,0,1)]*30
        labels,_=decode_ball_gap(supports,[1]*90,[True]*90,[True]*90)
        self.assertEqual(labels,list('H'*30+'A'*30+'D'*30))

    def test_missing_slots_can_continue_a_real_D_interval(self):
        labels,_=decode_ball_gap([(0,0,1)]*20+[(1,0,0)]*100+[(0,0,1)]*20,[1]*140,[True]*140,[True]*20+[False]*100+[True]*20)
        self.assertEqual(labels,['D']*140)

    def test_wholly_unsupported_segments_are_latent_X_then_explicitly_materialized(self):
        labels,counts=decode_ball_gap([(0,0,1)]*6,[1,1,0,2,2,2],[True]*6,[False]*6)
        self.assertEqual(labels,['X']*6)
        self.assertEqual(counts['unsupported_segments'],2)
        self.assertEqual(counts['unsupported_active_rows'],5)
        self.assertEqual(materialize_abstentions(labels,[1,1,0,2,2,2]),list('DDXDDD'))

    def test_barriers_do_not_borrow_observation_from_another_segment(self):
        labels,counts=decode_ball_gap([(1,0,0)]*5,[1,1,1,1,2],[True,True,False,True,True],[True,False,False,False,True])
        self.assertEqual(labels,list('HHXXH'))
        self.assertEqual(counts['unsupported_segments'],1)
        self.assertEqual(decode_ball_gap([],[],[],[])[0],[])

    def test_team_swap_unique_optimum_and_missing_input_invariance(self):
        observed=[True]*20+[False]*100+[True]*20
        a=[(1,0,0)]*140
        original=decode_ball_gap(a,[1]*140,[True]*140,observed)[0]
        changed=decode_ball_gap([(1,0,0)]*20+[(0,0,1)]*100+[(1,0,0)]*20,[1]*140,[True]*140,observed)[0]
        swapped=decode_ball_gap([(0,1,0)]*140,[1]*140,[True]*140,observed)[0]
        self.assertEqual(original,changed)
        self.assertEqual(swapped,[{'H':'A','A':'H','D':'D','X':'X'}[v] for v in original])

    def test_bad_dimensions_flags_and_scores_fail_even_in_neutral_slots(self):
        for supports,periods,usable,observed in [([(1,0,0)],[1],[True],[]),([(1,0,0)],[1],[True],[1]),([(1,0,0)],[1],[None],[False]),([(2,0,0)],[1],[True],[False]),([(1,0,0)],[3],[True],[False])]:
            with self.assertRaises(ValueError):decode_ball_gap(supports,periods,usable,observed)

if __name__=='__main__':unittest.main()
