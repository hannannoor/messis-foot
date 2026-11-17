import unittest

from gap_solver.core import Decision, Frame, summary
from gap_solver.fusion import Scene, Verification, verify_geometry, fuse_vote


def scene(ball=(40, 30), valid=True, error=0.2, shift=0):
    return Scene(home=((10+shift, 10), (20+shift, 15), (30+shift, 20), (40+shift, 25)),
                 away=((12+shift, 40), (22+shift, 45), (32+shift, 50), (42+shift, 55)),
                 ball=ball, homography_valid=valid, reprojection_error=error)


class CameraFusion(unittest.TestCase):
    def test_geometry_agreement_supports_broadcast_when_tactical_ball_missing(self):
        verification = verify_geometry(scene(ball=None), scene())
        self.assertTrue(verification.accepted)
        vote = fuse_vote(Decision(), Decision('H', 'observed_control', 'direct_heuristic'),
                         verification, uncertainty_s=0.1)
        self.assertEqual(vote.decision.label, 'H')
        self.assertEqual(vote.decision.reason, 'broadcast_rescue')

    def test_invalid_homography_or_geometry_cannot_rescue_unknown(self):
        for other in (scene(valid=False), scene(shift=20), scene(ball=(90, 1))):
            verification = verify_geometry(scene(), other)
            self.assertFalse(verification.accepted)
            self.assertEqual(fuse_vote(Decision(), Decision('A', '', 'direct_heuristic'),
                                       verification, 0.1).decision.label, 'X')

    def test_missing_player_geometry_is_not_a_verified_alignment(self):
        self.assertFalse(verify_geometry(Scene(), Scene()).accepted)

    def test_duplicated_tracks_do_not_supply_three_independent_matches(self):
        collapsed = Scene(home=((10,10),)*3, away=((12,40),)*3,
                          ball=(40,30), homography_valid=True, reprojection_error=.2)
        self.assertFalse(verify_geometry(scene(), collapsed).accepted)

    def test_direct_tactical_disagreement_is_retained_and_flagged(self):
        vote = fuse_vote(Decision('H', '', 'direct_heuristic'),
                         Decision('A', '', 'direct_heuristic'), verify_geometry(scene(), scene()), 0.1)
        self.assertEqual(vote.decision.label, 'H')
        self.assertEqual(vote.status, 'conflict_keep_tactical')

    def test_strong_broadcast_can_replace_weak_inferred_tactical_vote(self):
        vote = fuse_vote(Decision('H', '', 'inferred_heuristic'),
                         Decision('A', '', 'direct_heuristic'), verify_geometry(scene(), scene()), 0.02)
        self.assertEqual(vote.decision.label, 'A')

    def test_inferred_broadcast_cannot_fill_tactical_unknown(self):
        vote = fuse_vote(Decision(), Decision('H', '', 'inferred_heuristic'),
                         verify_geometry(scene(), scene()), 0.02)
        self.assertEqual(vote.decision.label, 'X')

    def test_excess_timing_uncertainty_disables_secondary(self):
        vote = fuse_vote(Decision(), Decision('H', '', 'direct_heuristic'),
                         verify_geometry(scene(), scene()), 0.8)
        self.assertEqual(vote.decision.label, 'X')

    def test_missing_secondary_never_dilutes_primary(self):
        original = Decision('A', 'observed_control', 'direct_heuristic')
        vote = fuse_vote(original, Decision(), verify_geometry(scene(), scene()), 0.02)
        self.assertEqual(vote.decision, original)

    def test_rescued_frames_are_counted_as_inferred_in_coverage_report(self):
        report = summary([Frame()], [Decision('H', 'broadcast_rescue', 'fused_heuristic')])
        self.assertEqual(report['inferred_frames'], 1)

    def test_nonfinite_verification_quality_cannot_rescue(self):
        vote = fuse_vote(Decision(), Decision('H', '', 'direct_heuristic'),
                         Verification(True, float('nan'), 'bad'), .02)
        self.assertEqual(vote.decision.label, 'X')
