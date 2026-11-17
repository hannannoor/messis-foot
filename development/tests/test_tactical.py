from dataclasses import replace
import math
import struct
import unittest
from gap_solver.core import Frame

try:
    from gap_solver import tactical
except ImportError:
    tactical=None


def control(side,n=12,period=1):
    return [Frame(period=period,ball_x=20,ball_y=20,home_distance=.5 if side=='H' else 10,
                  away_distance=.5 if side=='A' else 10) for _ in range(n)]


def leaf(label):
    probabilities=[0.,0.,0.]
    probabilities['HAD'.index(label)]=1.
    return dict(feature_names=list(tactical.FEATURE_NAMES),children_left=[-1],children_right=[-1],
                feature=[-2],threshold=[0.],probabilities=[probabilities])


class TacticalInference(unittest.TestCase):
    def module(self):
        self.assertIsNotNone(tactical,'portable tactical improvement is missing')
        return tactical

    def test_features_ignore_reference_like_context_and_tags(self):
        module=self.module()
        frames=control('H')
        changed=[replace(f,tag_team='A',restart_hint=True,dead_evidence=True,dead_source='provider_label') for f in frames]
        self.assertEqual(list(module.feature_rows(frames)),list(module.feature_rows(changed)))

    def test_period_reset_clears_velocity_and_retained_owner(self):
        module=self.module()
        rows=list(module.feature_rows(control('H')+[Frame(period=2)]))
        names=module.FEATURE_NAMES
        self.assertEqual(rows[-1][names.index('last_control_home')],0)
        self.assertEqual(rows[-1][names.index('ball_speed')],0)
        self.assertTrue(all(math.isfinite(x) for row in rows for x in row))

    def test_masked_ball_cannot_create_dead_or_unanchored_team(self):
        module=self.module()
        for label in ('H','A','D'):
            decisions=module.infer_tactical([Frame()]*40,leaf(label),module.Policy())
            self.assertTrue(all(d.label=='X' for d in decisions))

    def test_retained_owner_is_bounded_and_cannot_switch_team_during_occlusion(self):
        module=self.module()
        frames=control('H')+[Frame()]*100
        decisions=module.infer_tactical(frames,leaf('H'),module.Policy(max_gap_s=.6,bridge_s=0))
        self.assertTrue(any(d.label=='H' for d in decisions[12:25]))
        self.assertTrue(all(d.label=='X' for d in decisions[30:]))
        opposite=module.infer_tactical(frames,leaf('A'),module.Policy(max_gap_s=.6,bridge_s=0))
        self.assertTrue(all(d.label=='X' for d in opposite[12:]))

    def test_missing_opponent_does_not_become_certain_control(self):
        module=self.module()
        frames=[replace(f,away_distance=None) for f in control('H')]
        self.assertTrue(all(d.label=='X' for d in module.infer_tactical(frames,leaf('H'),module.Policy())))

    def test_missing_opponent_cannot_alone_support_dead_ball(self):
        module=self.module()
        frames=[replace(f,away_distance=None) for f in control('H')]
        self.assertTrue(all(d.label=='X' for d in module.infer_tactical(frames,leaf('D'),module.Policy())))

    def test_stable_observed_dead_model_can_repair_proximity_calls(self):
        module=self.module()
        decisions=module.infer_tactical(control('H'),leaf('D'),module.Policy())
        self.assertTrue(all(d.label=='D' for d in decisions))
        self.assertTrue(all(d.evidence_level=='external_model' for d in decisions))

    def test_publication_d_shortcut_is_rejected_but_independent_dead_evidence_is_honored(self):
        module=self.module()
        with self.assertRaises(ValueError):
            module.infer_tactical([Frame(dead_evidence=True,dead_source='published_pre_kickoff')],leaf('H'),module.Policy())
        result=module.infer_tactical([Frame(dead_evidence=True,dead_source='upstream_detector')],leaf('H'),module.Policy())
        self.assertEqual(result[0].label,'D')

    def test_tree_structure_and_feature_schema_are_validated(self):
        module=self.module()
        broken=leaf('H');broken['feature_names']=['target_label']
        with self.assertRaises(ValueError):
            module.infer_tactical(control('H'),broken,module.Policy())
        broken=leaf('H');broken.update(children_left=[0],children_right=[0],feature=[0],threshold=[0.])
        with self.assertRaises(ValueError):
            module.infer_tactical(control('H'),broken,module.Policy())

    def test_tree_uses_training_float32_input_semantics_at_split_ties(self):
        module=self.module()
        lower=struct.unpack('f',struct.pack('I',0x3dcccccd))[0]
        upper=struct.unpack('f',struct.pack('I',0x3dccccce))[0]
        threshold=(lower+upper)/2
        model=dict(feature_names=list(module.FEATURE_NAMES),children_left=[1,-1,-1],children_right=[2,-1,-1],
                   feature=[3,-2,-2],threshold=[threshold,0.,0.],
                   probabilities=[[.5,.5,0.],[1.,0.,0.],[0.,1.,0.]])
        row=[0.]*len(module.FEATURE_NAMES);row[3]=threshold
        self.assertEqual(module.PortableTree(model).predict(row),[0.,1.,0.])


if __name__=='__main__':
    unittest.main()
