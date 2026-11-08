from dataclasses import replace
import unittest
from gap_solver.motion import motion_frame
from gap_solver.temporal import motion_feature_rows
try:
    from gap_solver.anonymous_motion import associate_anonymous
except ImportError:
    associate_anonymous=None


class AnonymousMotion(unittest.TestCase):
    def setUp(self): self.assertIsNotNone(associate_anonymous,'anonymous correspondence adapter missing')

    def test_slot_permutation_cannot_change_motion_features(self):
        frames=[motion_frame(1,(10,20),[(10+i*.1,20),(30,30),(50,40)],[(70,10),(80,20),(90,30)]) for i in range(4)]
        swapped=[replace(f,home_xy=tuple(reversed(f.home_xy)),away_xy=tuple(reversed(f.away_xy)),home_ids=(99,1,33)) for f in frames]
        a,_=associate_anonymous(frames);b,_=associate_anonymous(swapped)
        self.assertEqual(list(motion_feature_rows(a)),list(motion_feature_rows(b)))
        self.assertEqual(a[0].home_ids,a[1].home_ids)
        self.assertEqual(frames[0].home_ids,())

    def test_far_ambiguous_missing_period_and_quality_reset(self):
        def f(points,period=1,valid=True):return motion_frame(period,None,points,(),geometry_valid=valid)
        frames=[f([(0,0),(2,0)]),f([(1,0)]),f([(1,0)]),f([]),f([(1,0)]),f([(1,0)],2),f([(1,0)],2,False),f([(1,0)],2),f([(5,0)],2)]
        values,report=associate_anonymous(frames)
        self.assertNotIn(values[1].home_ids[0],values[0].home_ids)
        self.assertEqual(values[1].home_ids,values[2].home_ids)
        self.assertNotEqual(values[2].home_ids,values[4].home_ids)
        self.assertNotEqual(values[4].home_ids,values[5].home_ids)
        self.assertEqual(values[6].home_xy,())
        self.assertNotEqual(values[5].home_ids,values[7].home_ids)
        self.assertNotEqual(values[7].home_ids,values[8].home_ids)
        self.assertFalse(report['player_identity_verified'])

if __name__=='__main__':unittest.main()
