"""Synthetic falsification and published-parameter tests; no match inputs are read."""
import copy
from dataclasses import replace
import itertools
import json
import math
from pathlib import Path
import random
import unittest

from gap_solver.core import Decision
from gap_solver.motion import MotionFrame
from gap_solver.temporal import (MOTION_FEATURES, PortableBoosted, TemporalPolicy,
                                 decode_team_sequence, swap_feature_row)
try:
    from gap_solver.temporal_feasibility import symmetric_logit_bound, confidence_feasibility
except ImportError:
    symmetric_logit_bound = confidence_feasibility = None

ROOT = Path(__file__).resolve().parents[1]


def model(low=-2., high=3., initial=.3, rate=.1):
    return dict(feature_names=list(MOTION_FEATURES), learning_rate=rate, initial_log_odds=initial,
                trees=[dict(children_left=[1,-1,-1], children_right=[2,-1,-1],
                            feature=[1,-2,-2], threshold=[.5,0.,0.], value=[1e6,low,high])])


class ConfidenceBounds(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(confidence_feasibility, 'confidence feasibility preflight is missing')

    def test_leaf_ranges_bound_symmetric_scores_and_ignore_internal_values(self):
        # Catches using all node values or forgetting the factor 1/2.
        m=model(); bound=symmetric_logit_bound(m)
        self.assertAlmostEqual(bound['exact_real_bound'], .25)
        self.assertGreaterEqual(bound['runtime_bound'], .25)
        self.assertLess(bound['runtime_bound'], .25000000001)
        portable=PortableBoosted(m)
        for h,a in itertools.product((0.,.4,.5,.6,1.),repeat=2):
            row=[0.]*len(MOTION_FEATURES);row[1]=h;row[2]=a
            score=portable.symmetric_score(row)
            self.assertLessEqual(abs(score),bound['runtime_bound'])
            self.assertEqual(score,-portable.symmetric_score(swap_feature_row(row)))

    def test_random_ensembles_cannot_exceed_range_even_after_team_swap(self):
        rng=random.Random(1729)
        for _ in range(50):
            m=model(initial=rng.uniform(-20,20),rate=rng.uniform(.01,1))
            m['trees']=[model(rng.uniform(-10,0),rng.uniform(0,10))['trees'][0] for _ in range(9)]
            bound=symmetric_logit_bound(m)['runtime_bound'];portable=PortableBoosted(m)
            for _ in range(20):
                row=[rng.uniform(-1,1) for _ in MOTION_FEATURES]
                self.assertLessEqual(abs(portable.symmetric_score(row)),bound)

    def test_two_hard_neighbours_falsify_emission_only_or_one_message_bound(self):
        frames=[MotionFrame() for _ in range(3)];baseline=[Decision('A'),Decision('X'),Decision('A')]
        z=decode_team_sequence([0.,0.,0.],frames,baseline,2.)
        self.assertAlmostEqual(z[1],4.)
        result=confidence_feasibility(model(0,0),2.,1.,TemporalPolicy(confidence=.99))
        self.assertGreaterEqual(result['posterior_logit_bound'],4.)
        self.assertLess(result['posterior_logit_bound'],4.000001)
        self.assertEqual(result['status'],'provably_impossible')

    def test_anchor_confidence_is_outside_the_x_row_claim(self):
        result=confidence_feasibility(model(0,0),0.,1.,TemporalPolicy(confidence=.9))
        z=decode_team_sequence([0.,0.],[MotionFrame(),MotionFrame()],[Decision('H'),Decision('X')],0.)
        self.assertEqual(z,[-50.,0.])
        self.assertLess(result['confidence_ceiling'],.50000001)
        self.assertEqual(result['scope'],'baseline_X_only')

    def test_random_decoder_sequences_with_anchors_and_boundaries_obey_ceiling(self):
        # Catches missing messages, barrier handling, and incorrectly including hard anchors.
        rng=random.Random(182);m=model(-8,10,rate=.4)
        bound=confidence_feasibility(m,1.8,2.3,TemporalPolicy(confidence=.95))
        portable=PortableBoosted(m)
        for _ in range(150):
            frames=[MotionFrame(period=rng.choice((0,1,1,2)),geometry_valid=rng.random()>.1) for _ in range(20)]
            base=[Decision(rng.choice(('X','X','H','A','D'))) for _ in frames]
            rows=[[rng.uniform(-1,1) for _ in MOTION_FEATURES] for _ in frames]
            scores=[portable.symmetric_score(row) for row in rows]
            z=decode_team_sequence(scores,frames,base,1.8)
            for frame,decision,value in zip(frames,base,z):
                if decision.label=='X':
                    self.assertLessEqual(abs(value),bound['posterior_logit_bound'])
                    p=1/(1+math.exp(-max(-50,min(50,value/2.3))))
                    self.assertLessEqual(max(p,1-p),bound['confidence_ceiling'])

    def test_tiny_sequences_agree_with_independent_path_enumeration(self):
        # Independently enumerates path weights, rather than duplicating messages.
        rng=random.Random(111)
        for _ in range(25):
            n=7;s=rng.uniform(0,3);scores=[rng.uniform(-2,2) for _ in range(n)]
            labels=[rng.choice(('H','A','X','X')) for _ in range(n)]
            paths=[]
            for path in itertools.product((0,1),repeat=n):
                if any(label in ('H','A') and state!=('H','A').index(label) for label,state in zip(labels,path)):continue
                energy=sum(z*state for z,state,label in zip(scores,path,labels) if label=='X')
                energy-=s*sum(a!=b for a,b in zip(path,path[1:]))
                paths.append((path,math.exp(energy)))
            posterior=decode_team_sequence(scores,[MotionFrame() for _ in range(n)],[Decision(x) for x in labels],s)
            for i,label in enumerate(labels):
                if label=='X':
                    h=sum(w for path,w in paths if path[i]==0);a=sum(w for path,w in paths if path[i]==1)
                    self.assertAlmostEqual(posterior[i],math.log(a/h),places=11)

    def test_decoder_clip_precedes_temperature_and_policy_clip_follows(self):
        result=confidence_feasibility(model(-1000,1000,rate=1),10.,100.,TemporalPolicy(confidence=.7))
        self.assertEqual(result['posterior_logit_bound'],50.)
        self.assertAlmostEqual(result['calibrated_logit_bound'],.5)
        self.assertGreaterEqual(result['confidence_ceiling'],.6224593312018546)
        self.assertLess(result['confidence_ceiling'],.62245934)
        self.assertEqual(result['status'],'provably_impossible')
        saturated=confidence_feasibility(model(-1000,1000,rate=1),10.,1e-300,TemporalPolicy(confidence=1.))
        self.assertEqual(saturated['confidence_ceiling'],1.)
        self.assertEqual(saturated['status'],'not_ruled_out')

    def test_high_ceiling_is_not_an_attainability_claim(self):
        # Constant leaves have no symmetric emission; the loose range need not be attainable.
        result=confidence_feasibility(model(-20,20,rate=1),10.,1.,TemporalPolicy(confidence=.9))
        self.assertEqual(result['status'],'not_ruled_out')
        self.assertNotIn('attainable',result)
        near=confidence_feasibility(model(0,0),0.,1.,TemporalPolicy(confidence=math.nextafter(.5,1)))
        self.assertEqual(near['status'],'not_ruled_out')

    def test_float_score_cancellation_must_not_use_exact_real_bound_alone(self):
        m=model(0,3,initial=1e16,rate=1)
        row=[0.]*len(MOTION_FEATURES);row[1]=1
        actual=abs(PortableBoosted(m).symmetric_score(row))
        self.assertEqual(actual,2.)  # exact-real B is only 1.5
        bounds=symmetric_logit_bound(m)
        self.assertGreaterEqual(bounds['runtime_bound'],actual)

    def test_extreme_finite_arithmetic_is_inconclusive_without_false_proof(self):
        for m,s,t in ((model(1e308,1e308,initial=1e308,rate=1),0.,1.),
                       (model(),1e308,1.),(model(),1.,1e-320)):
            result=confidence_feasibility(m,s,t,TemporalPolicy(confidence=1.))
            self.assertEqual(result['status'],'not_ruled_out')
            self.assertEqual(result['confidence_ceiling'],1.)

    def test_many_large_finite_tree_ranges_decline_proof_without_overflow(self):
        m=model(-1e307,1e307,rate=1)
        m['trees']*=40
        result=confidence_feasibility(m,1.,1.,TemporalPolicy(confidence=1.))
        self.assertEqual(result['status'],'not_ruled_out')
        self.assertEqual(result['confidence_ceiling'],1.)

    def test_malformed_models_fail_cleanly(self):
        mutations=[lambda m:m.update(feature_names=['bad']),lambda m:m.update(trees=[]),
                   lambda m:m.update(learning_rate=float('nan')),lambda m:m.update(initial_log_odds=True),
                   lambda m:m['trees'][0]['value'].__setitem__(1,float('inf')),
                   lambda m:m['trees'][0]['feature'].__setitem__(0,1.5),
                   lambda m:m['trees'][0]['children_left'].__setitem__(0,0),
                   lambda m:m['trees'][0]['children_right'].__setitem__(1,2),
                   lambda m:m['trees'][0]['threshold'].__setitem__(0,False),
                   lambda m:m['trees'][0].update(value=[0.])]
        for mutate in mutations:
            m=model();mutate(m)
            with self.subTest(model=m),self.assertRaises(ValueError):symmetric_logit_bound(m)
        m=model();m['trees'][0]['feature'] += [-2];m['trees'][0]['children_left'] += [-1]
        m['trees'][0]['children_right'] += [-1];m['trees'][0]['threshold'] += [0.];m['trees'][0]['value'] += [0.]
        with self.assertRaises(ValueError):symmetric_logit_bound(m)

    def test_nonfinite_or_malformed_policy_and_scales_fail_cleanly(self):
        bad=[({'confidence':float('nan')},1.,1.),({'confidence':True},1.,1.),
             ({'confidence':.5},1.,1.),({'minimum_players':True},1.,1.),
             ({'max_gap_s':-1},1.,1.),({'switch_multiplier':0},1.,1.),
             ({'unknown':1},1.,1.),({},-1.,1.),({},True,1.),({},float('inf'),1.),
             ({},1.,0.),({},1.,False),({},1.,'1')]
        for p,s,t in bad:
            with self.subTest(p=p,s=s,t=t),self.assertRaises(ValueError):confidence_feasibility(model(),s,t,p)

    def test_published_rejected_artifact_is_mathematically_unreachable(self):
        artifact=json.loads((ROOT/'benchmark/skillcorner/frozen/temporal-selected.json').read_text())
        result=confidence_feasibility(artifact['model'],artifact['transition_cost'],artifact['temperature'],artifact['policy'])
        self.assertEqual(result['status'],'provably_impossible')
        self.assertAlmostEqual(result['symmetric_logit_bound'],2.8585186401957086)
        self.assertGreater(result['confidence_ceiling'],.899)
        self.assertLess(result['confidence_ceiling'],.9)
        self.assertEqual(result['confidence_threshold'],.975)

    def test_inspection_does_not_mutate_model_or_policy(self):
        m=model();p=TemporalPolicy();before=copy.deepcopy(m)
        confidence_feasibility(m,1.,10.,p)
        self.assertEqual(m,before);self.assertEqual(p,TemporalPolicy())


if __name__=='__main__':unittest.main()
