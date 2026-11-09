import unittest
from dataclasses import replace
from math import nan

from cadence_fixtures import moving_fixture
from gap_solver.tactical import feature_rows,PortableTree
from gap_solver.tactical_model import FROZEN_MODEL
from gap_solver.soft_sequence import sequence_usable
from ball_gap_policy import decode_ball_gap

try:
    from cadence_features import cadence_feature_rows
except ImportError:
    cadence_feature_rows=None


class CadenceFeatures(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(cadence_feature_rows,'bounded cadence feature module is not implemented')

    def rows(self,frames):
        return list(cadence_feature_rows(frames))

    def test_two_m_per_second_reacquisition_is_measured(self):
        for stride in (2,3,5):
            with self.subTest(stride=stride):
                rows=self.rows(moving_fixture(31,stride))
                for i in range(stride,31,stride):
                    self.assertTrue(rows[i].repaired)
                    self.assertTrue(rows[i].velocity_valid)
                    self.assertEqual(rows[i].time_basis,'source')
                    self.assertAlmostEqual(rows[i].candidate[9],2.)
                    self.assertAlmostEqual(rows[i].pair_dt_s,stride/25)
                    self.assertEqual(rows[i].legacy[9],0.)

    def test_true_zero_is_valid(self):
        frames=[replace(f,ball_x=25. if f.ball_observed else None) for f in moving_fixture(6,2)]
        row=self.rows(frames)[2]
        self.assertTrue(row.repaired)
        self.assertTrue(row.velocity_valid)
        self.assertEqual(row.candidate[9],0.)

    def test_first_observation_is_unknown(self):
        row=self.rows(moving_fixture(1))[0]
        self.assertFalse(row.velocity_valid)
        self.assertFalse(row.repaired)
        self.assertIsNone(row.pair_dt_s)
        self.assertEqual(row.candidate,row.legacy)

    def test_timestamp_pair_rejected_without_fallback(self):
        for time in (0.,-.1,nan,float('inf'),.25):
            with self.subTest(time=time):
                frames=moving_fixture(3,2)
                frames[2]=replace(frames[2],ball_sample_time_s=time)
                row=self.rows(frames)[2]
                self.assertFalse(row.repaired)
                self.assertFalse(row.velocity_valid)
                self.assertEqual(row.candidate,row.legacy)
                self.assertNotEqual(row.time_basis,'canonical_grid')

    def test_missing_clock_uses_labeled_grid(self):
        frames=moving_fixture(3,2)
        frames[2]=replace(frames[2],ball_sample_time_s=None)
        row=self.rows(frames)[2]
        self.assertTrue(row.repaired)
        self.assertEqual(row.time_basis,'canonical_grid')
        self.assertAlmostEqual(row.candidate[9],2.)

    def test_pair_five_rows_allowed_six_rejected(self):
        self.assertTrue(self.rows(moving_fixture(6,5))[5].repaired)
        self.assertFalse(self.rows(moving_fixture(7,6))[6].repaired)

    def test_large_clock_boundary_roundoff_is_arithmetic_only(self):
        frames=[replace(f,ball_sample_time_s=1800+i/25 if f.ball_observed else None)
                for i,f in enumerate(moving_fixture(6,5))]
        row=self.rows(frames)[5]
        self.assertTrue(row.repaired)
        self.assertAlmostEqual(row.candidate[9],2.)

    def test_no_cross_geometry_barrier(self):
        frames=moving_fixture(3,2)
        frames[1]=replace(frames[1],geometry_valid=False)
        self.assertFalse(self.rows(frames)[2].repaired)

    def test_no_cross_eligibility_barrier(self):
        frames=moving_fixture(3,2)
        frames[1]=replace(frames[1],home_xy=(),away_xy=())
        self.assertFalse(self.rows(frames)[2].repaired)

    def test_no_cross_period(self):
        frames=moving_fixture(3,2)
        frames[2]=replace(frames[2],period=2)
        self.assertFalse(self.rows(frames)[2].repaired)

    def test_recent_speed_uses_exact_twelve_rows(self):
        rows=self.rows(moving_fixture(15,2))
        self.assertAlmostEqual(rows[2].candidate[10],2/3)
        self.assertAlmostEqual(rows[12].candidate[10],1.)
        self.assertAlmostEqual(rows[13].candidate[10],1.)
        self.assertEqual(rows[12].legacy[10],0.)

    def test_period_reset_does_not_inherit_recent_speed(self):
        frames=moving_fixture(15,2)
        frames[14]=replace(frames[14],period=2)
        row=self.rows(frames)[14]
        self.assertEqual(row.candidate[10],0.)
        self.assertFalse(row.repaired)

    def test_only_speed_columns_can_change(self):
        for row in self.rows(moving_fixture(30,3)):
            self.assertEqual(len(row.candidate),18)
            for j in range(18):
                if j not in (9,10):self.assertEqual(row.candidate[j],row.legacy[j])

    def test_dense_rows_are_identical(self):
        frames=moving_fixture()
        expected=list(feature_rows(frames))
        rows=self.rows(frames)
        self.assertEqual([row.candidate for row in rows],expected)
        self.assertFalse(any(row.repaired for row in rows))

    def test_original_dense_and_sparse_failure_is_preserved(self):
        tree=PortableTree(FROZEN_MODEL['model'])
        for stride,label in ((1,'H'),(2,'D')):
            frames=moving_fixture(stride=stride)
            support=[tree.predict(row) for row in feature_rows(frames)]
            labels,_=decode_ball_gap(support,[f.period for f in frames],
                [sequence_usable(f) for f in frames],[f.ball_observed for f in frames])
            self.assertEqual(labels,[label]*180)

    def test_no_forward_fill_into_missing_speed(self):
        row=self.rows(moving_fixture(4,2))[3]
        self.assertFalse(row.repaired)
        self.assertEqual(row.candidate[9],0.)
        self.assertFalse(row.velocity_valid)

    def test_invalid_horizon_rejected(self):
        for value in (0,-1,.30,nan,True):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):list(cadence_feature_rows(moving_fixture(2),value))


if __name__=='__main__':
    unittest.main()
