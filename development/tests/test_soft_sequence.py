import itertools
import math
import unittest
from gap_solver.motion import motion_frame
try:
    from gap_solver.soft_sequence import soft_emissions,decode_soft,sequence_usable
except ImportError:
    soft_emissions=decode_soft=sequence_usable=None


class SoftSequence(unittest.TestCase):
    def setUp(self):self.assertIsNotNone(decode_soft,'soft sequence decoder missing')

    def test_finite_evidence_revises_a_wrong_single_frame_without_hard_anchors(self):
        rows=[(4.,0.,-9.),(0.,1.,-9.),(4.,0.,-9.)]
        self.assertEqual(decode_soft(rows,[1]*3,[True]*3,0),list('HAH'))
        self.assertEqual(decode_soft(rows,[1]*3,[True]*3,2),list('HHH'))
        self.assertEqual(decode_soft([(4.,0.,0.),(0.,20.,0.),(4.,0.,0.)],[1]*3,[True]*3,2),list('HAH'))

    def test_quality_period_and_unusable_frames_are_real_barriers(self):
        rows=[(3.,0.,0.),(0.,10.,0.),(0.,10.,0.),(0.,10.,0.),(0.,0.,3.)]
        self.assertEqual(decode_soft(rows,[1,1,0,2,2],[True,False,True,True,True],100),list('HXXAA'))
        self.assertEqual(decode_soft([],[],[],1),[])
        self.assertEqual(decode_soft([(1.,2.,3.)],[0],[True],0),['X'])

    def test_global_path_score_matches_independently_enumerated_paths(self):
        rows=[(2.,1.,0.),(0.,1.,2.),(2.,0.,1.),(0.,3.,0.)]
        for cost in (0.,.5,3.):
            labels=decode_soft(rows,[1]*4,[True]*4,cost);path=['HAD'.index(x) for x in labels]
            actual=sum(rows[i][s] for i,s in enumerate(path))-cost*sum(a!=b for a,b in zip(path,path[1:]))
            best=max(sum(rows[i][s] for i,s in enumerate(p))-cost*sum(a!=b for a,b in zip(p,p[1:])) for p in itertools.product(range(3),repeat=4))
            self.assertAlmostEqual(actual,best)

    def test_team_reversal_dead_state_and_ties(self):
        rows=[(4.,0.,0.),(0.,4.,0.),(0.,0.,10.)]
        self.assertEqual(decode_soft(rows,[1]*3,[True]*3,1),list('HAD'))
        self.assertEqual(decode_soft([(a,h,d) for h,a,d in rows],[1]*3,[True]*3,1),list('AHD'))
        self.assertEqual(decode_soft([(0.,0.,0.)]*3,[1]*3,[True]*3,0),list('HHH'))

    def test_emissions_and_eligibility_are_input_only_and_finite(self):
        values=soft_emissions([(1.,0.,0.)],[100.],1.)
        self.assertTrue(all(math.isfinite(x) for x in values[0]))
        self.assertEqual(decode_soft(values,[1],[True],0),['A'])
        players=[(10,10),(20,20),(30,30)]
        self.assertTrue(sequence_usable(motion_frame(1,None,players,players)))
        self.assertFalse(sequence_usable(motion_frame(1,None,players[:2],players)))
        self.assertFalse(sequence_usable(motion_frame(1,None,players,players,geometry_valid=False)))
        self.assertFalse(sequence_usable(motion_frame(0,(10,10),players,players)))

    def test_malformed_scores_dimensions_and_parameters_fail(self):
        for rows,periods,usable,cost in [([(1,2)],[1],[True],0),([(1,float('nan'),0)],[1],[True],0),([(1,2,3)],[3],[True],0),([(1,2,3)],[],[True],0),([(1,2,3)],[1],[True],-1)]:
            with self.assertRaises(ValueError):decode_soft(rows,periods,usable,cost)
        for supports,scores,weight in [([(1,0,0)],[],1),([(2,0,0)],[0],1),([(1,0,0)],[float('inf')],1),([(1,0,0)],[0],-1)]:
            with self.assertRaises(ValueError):soft_emissions(supports,scores,weight)

if __name__=='__main__':unittest.main()
