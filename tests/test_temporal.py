from dataclasses import replace
from math import isfinite
import unittest
import numpy as np
from gap_solver.core import Decision
from gap_solver.motion import MotionFrame

try:
    from gap_solver.temporal import (MOTION_FEATURES,TemporalPolicy,PortableBoosted,motion_feature_rows,
        swap_feature_row,reflect_feature_row,mask_motion_frames,decode_team_sequence,apply_temporal_policy,infer_temporal)
except ImportError:
    MOTION_FEATURES=TemporalPolicy=PortableBoosted=motion_feature_rows=swap_feature_row=None
    reflect_feature_row=mask_motion_frames=decode_team_sequence=apply_temporal_policy=infer_temporal=None


def motion_fixture(n=80):
    frames=[]
    for i in range(n):
        home=tuple((19+j+.02*i,19+j) for j in range(3));away=tuple((79+j,19+j) for j in range(3))
        frames.append(MotionFrame(ball_x=20+.02*i,ball_y=20,home_distance=.5,away_distance=60,
                      home_xy=home,away_xy=away,home_ids=(0,1,2),away_ids=(3,4,5)))
    return frames


def stump():
    return dict(feature_names=list(MOTION_FEATURES),learning_rate=.1,initial_log_odds=.3,
                trees=[dict(children_left=[1,-1,-1],children_right=[2,-1,-1],
                    feature=[MOTION_FEATURES.index('home_count'),-2,-2],threshold=[.5,0.,0.],value=[0.,-2.,3.])])


class TemporalCore(unittest.TestCase):
    def ready(self):self.assertIsNotNone(motion_feature_rows,'motion/temporal inference is missing')

    def test_player_motion_features_exist_when_ball_is_missing(self):
        self.ready();frames=motion_fixture()
        frames=mask_motion_frames(frames,[10<=i<40 for i in range(80)])
        row=dict(zip(MOTION_FEATURES,list(motion_feature_rows(frames))[20]))
        self.assertEqual(row['ball_available'],0.)
        self.assertAlmostEqual(row['home_count'],3/11)
        self.assertAlmostEqual(row['home_vx'],.5/15)
        self.assertEqual(row['last_owner'],-1.)
        self.assertEqual(row['next_owner'],-1.)
        self.assertGreater(row['last_anchor_age'],0.)
        self.assertTrue(all(isfinite(v) for v in row.values()))

    def test_mask_removes_ball_and_derived_distance_before_anchor_extraction(self):
        self.ready();frames=motion_fixture();masked=mask_motion_frames(frames,[True]*80)
        self.assertTrue(frames[0].ball_observed)
        self.assertTrue(all(not f.ball_observed and f.home_distance is None and f.away_distance is None for f in masked))
        row=dict(zip(MOTION_FEATURES,list(motion_feature_rows(masked))[30]))
        self.assertEqual(row['last_anchor_available'],0.)
        self.assertEqual(row['next_anchor_available'],0.)

    def test_home_away_swap_transforms_features_and_owner_signs(self):
        self.ready();frames=motion_fixture()
        swapped=[replace(f,home_xy=f.away_xy,away_xy=f.home_xy,home_ids=f.away_ids,away_ids=f.home_ids,
                         home_distance=f.away_distance,away_distance=f.home_distance) for f in frames]
        a=list(motion_feature_rows(frames));b=list(motion_feature_rows(swapped))
        np.testing.assert_allclose([swap_feature_row(r) for r in a],b,rtol=0,atol=1e-12)

    def test_coordinate_reflection_is_consistent_with_feature_transform(self):
        self.ready();frames=motion_fixture()
        mirrored=[replace(f,ball_x=105.3-f.ball_x,ball_y=68-f.ball_y,
                  home_xy=tuple((105.3-x,68-y) for x,y in f.home_xy),away_xy=tuple((105.3-x,68-y) for x,y in f.away_xy)) for f in frames]
        np.testing.assert_allclose([reflect_feature_row(r) for r in motion_feature_rows(frames)],
                                  list(motion_feature_rows(mirrored)),rtol=0,atol=1e-12)

    def test_history_resets_at_period_boundaries(self):
        self.ready();frames=motion_fixture(40)
        frames[20:]=[replace(f,period=2,ball_x=None,ball_y=None,home_distance=None,away_distance=None) for f in frames[20:]]
        row=dict(zip(MOTION_FEATURES,list(motion_feature_rows(frames))[25]))
        self.assertEqual(row['last_owner'],0.)
        self.assertEqual(row['last_anchor_available'],0.)

    def test_portable_boosted_logits_follow_leaf_values(self):
        self.ready();model=PortableBoosted(stump());row=[0.]*len(MOTION_FEATURES)
        row[MOTION_FEATURES.index('home_count')]=.4
        self.assertAlmostEqual(model.score(row),.1)
        row[MOTION_FEATURES.index('home_count')]=.6
        self.assertAlmostEqual(model.score(row),.6)

    def test_temporal_decoder_can_recover_opposing_interior_with_same_endpoints(self):
        self.ready();frames=mask_motion_frames(motion_fixture(),[16<=i<41 for i in range(80)])
        baseline=[Decision('X' if 16<=i<41 else 'H') for i in range(80)]
        scores=[8. if 24<=i<34 else -8. for i in range(80)]
        posterior=decode_team_sequence(scores,frames,baseline,switch_cost=2.)
        result=apply_temporal_policy(frames,baseline,posterior,TemporalPolicy(confidence=.9,max_gap_s=2.))
        self.assertTrue(all(d.label=='A' for d in result[25:33]))
        self.assertEqual(result[15].label,'H');self.assertEqual(result[41].label,'H')

    def test_missing_opponent_and_geometry_failure_keep_unknown(self):
        self.ready();frames=mask_motion_frames(motion_fixture(),[16<=i<41 for i in range(80)])
        frames[25]=replace(frames[25],away_xy=(),away_ids=())
        frames[26]=replace(frames[26],geometry_valid=False)
        baseline=[Decision('X' if 16<=i<41 else 'H') for i in range(80)]
        result=apply_temporal_policy(frames,baseline,[-12.]*80,TemporalPolicy(confidence=.9,max_gap_s=2.))
        self.assertEqual(result[25].label,'X');self.assertEqual(result[26].label,'X')

    def test_existing_labels_and_dead_boundaries_are_preserved(self):
        self.ready();frames=mask_motion_frames(motion_fixture(),[16<=i<41 for i in range(80)])
        baseline=[Decision('X' if 16<=i<41 else 'H') for i in range(80)];baseline[25]=Decision('D')
        result=apply_temporal_policy(frames,baseline,[12.]*80,TemporalPolicy(confidence=.9,max_gap_s=2.))
        self.assertEqual(result[25].label,'D')
        self.assertEqual(result[0].label,'H')
        self.assertTrue(all(result[i].label=='X' for i in range(16,41) if i!=25))
