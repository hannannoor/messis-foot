import unittest
from dataclasses import replace

from gap_solver.core import Config, Frame, infer, interpolate_ball, summary, unresolved_intervals


def team(label, n=8, period=1):
    return [Frame(period=period, ball_x=10.0, ball_y=10.0,
                  home_distance=0.5 if label == 'H' else 8.0,
                  away_distance=0.5 if label == 'A' else 8.0) for _ in range(n)]


def gap(n, **kwargs):
    return [Frame(**kwargs) for _ in range(n)]


class GapBehaviour(unittest.TestCase):
    def test_short_occlusion_keeps_team_without_claiming_observation(self):
        result = infer(team('H') + gap(10) + team('H'))
        self.assertEqual([d.label for d in result], ['H'] * 26)
        self.assertTrue(all(d.reason == 'short_same_team_bridge' for d in result[8:18]))

    def test_brief_opponent_touch_does_not_create_turnover(self):
        result = infer(team('H') + team('A', 2) + team('H'))
        self.assertEqual(set(d.label for d in result), {'H'})

    def test_genuine_control_switch_backdates_to_first_supporting_frame(self):
        result = infer(team('H') + team('A'))
        self.assertEqual([d.label for d in result], ['H'] * 8 + ['A'] * 8)

    def test_opposing_gap_anchors_remain_unresolved(self):
        frames = team('H') + gap(10) + team('A')
        result = infer(frames)
        self.assertEqual([d.label for d in result[8:18]], ['X'] * 10)
        self.assertEqual(unresolved_intervals(frames, result)[0]['cause'], 'opposing_anchors')

    def test_long_same_team_gap_is_not_filled_without_tags(self):
        result = infer(team('H') + gap(30) + team('H'))
        self.assertEqual([d.label for d in result[8:38]], ['X'] * 30)

    def test_consistent_tags_extend_only_bounded_same_team_bridge(self):
        result = infer(team('H') + gap(30, tag_team='H') + team('H'))
        self.assertTrue(all(d.reason == 'tag_supported_bridge' for d in result[8:38]))
        result = infer(team('H') + gap(60, tag_team='H') + team('H'))
        self.assertTrue(all(d.label == 'X' for d in result[8:68]))

    def test_tags_cannot_overrule_opposing_anchors(self):
        result = infer(team('H') + gap(20, tag_team='H') + team('A'))
        self.assertTrue(all(d.label == 'X' for d in result[8:28]))

    def test_restart_blocks_even_short_continuity(self):
        result = infer(team('H') + gap(5, restart_hint=True) + team('H'))
        self.assertTrue(all(d.label == 'X' for d in result[8:13]))

    def test_restart_phase_does_not_veto_sustained_observed_control(self):
        frames = [replace(f, restart_hint=True) for f in team('H', 10)]
        self.assertEqual([d.label for d in infer(frames)], ['H']*10)

    def test_confirmation_cannot_accumulate_across_restart_phase_edges(self):
        frames = team('A', 3) + [replace(f, restart_hint=True) for f in team('A', 3)]
        self.assertEqual([d.label for d in infer(frames)], ['X']*6)

    def test_explicit_dead_overrides_observed_control_inside_restart_phase(self):
        frames = [replace(f, restart_hint=True, dead_evidence=True) for f in team('H', 10)]
        self.assertEqual([d.label for d in infer(frames)], ['D']*10)

    def test_legacy_restart_veto_can_be_reproduced_for_controlled_comparison(self):
        import inspect
        self.assertIn('legacy_restart_veto', inspect.signature(infer).parameters)
        frames = [replace(f, restart_hint=True) for f in team('H', 10)]
        self.assertEqual([d.label for d in infer(frames, legacy_restart_veto=True)], ['X']*10)

    def test_explicit_dead_evidence_splits_same_team_possessions(self):
        result = infer(team('H') + gap(8, dead_evidence=True) + team('H'))
        self.assertEqual([d.label for d in result], ['H'] * 8 + ['D'] * 8 + ['H'] * 8)

    def test_missing_ball_alone_never_means_dead(self):
        result = infer(gap(100))
        self.assertEqual(set(d.label for d in result), {'X'})

    def test_confirmation_cannot_accumulate_across_occlusions(self):
        frames = sum((team('A', 1) + gap(2) for _ in range(8)), [])
        self.assertEqual(set(d.label for d in infer(frames)), {'X'})

    def test_one_observation_after_long_gap_cannot_reestablish_old_owner(self):
        frames = team('H') + gap(100) + team('H', 1)
        self.assertEqual(infer(frames)[-1].label, 'X')

    def test_halves_do_not_share_anchors(self):
        frames = team('H') + gap(5) + gap(5, period=2) + team('H', period=2)
        self.assertTrue(all(d.label == 'X' for d in infer(frames)[8:18]))

    def test_ungraded_frames_are_ignored_in_coverage(self):
        frames = gap(4, period=0) + team('H')
        result = infer(frames)
        self.assertEqual([d.label for d in result[:4]], ['X'] * 4)
        report = summary(frames, result)
        self.assertEqual(report['active_frames'], 8)
        self.assertEqual(report['resolved_fraction'], 1.0)

    def test_ball_without_near_player_does_not_force_ownership(self):
        frames = [Frame(ball_x=1, ball_y=1, home_distance=8, away_distance=9)] * 10
        self.assertEqual(set(d.label for d in infer(frames)), {'X'})

    def test_interpolation_is_short_bounded_and_does_not_mutate_evidence(self):
        frames = [Frame(ball_x=10, ball_y=10)] + gap(4) + [Frame(ball_x=11, ball_y=10)]
        xy = interpolate_ball(frames)
        self.assertAlmostEqual(xy[1][0], 10.2)
        self.assertIsNone(frames[1].ball_x)
        self.assertEqual(set(d.label for d in infer(frames)), {'X'})

    def test_impossible_speed_or_half_change_rejects_interpolation(self):
        frames = [Frame(ball_x=0, ball_y=0)] + gap(2) + [Frame(ball_x=100, ball_y=0)]
        self.assertIsNone(interpolate_ball(frames)[1])
        frames = [Frame(ball_x=0, ball_y=0)] + gap(2, period=2) + [Frame(period=2, ball_x=1, ball_y=0)]
        self.assertIsNone(interpolate_ball(frames)[1])

    def test_invalid_configuration_fails(self):
        with self.assertRaises(ValueError):
            infer(team('H'), Config(fps=0))
