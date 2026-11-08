import unittest
from dataclasses import replace
import numpy as np

from gap_solver.motion import motion_frame
from official_baseline_reference import smooth as upstream_smooth
from cadence_fixtures import moving_fixture

try:
    from cadence_baselines import nearest_codes,smooth_votes,baseline_predictions
except ImportError:
    nearest_codes=smooth_votes=baseline_predictions=None


class CadenceBaselines(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(nearest_codes,'nearest/majority comparators are not implemented')

    def test_nearest_any_team_and_no_observation(self):
        frames=[motion_frame(1,(0,0),[(2,0)],[(1,0)]),
                motion_frame(1,(0,0),[],[(1,0)]),
                motion_frame(1,(0,0),[],[]),
                motion_frame(1,None,[(1,0)],[(2,0)])]
        self.assertEqual(nearest_codes(frames),[1,1,-1,-1])

    def test_nearest_uses_metre_distance_and_canonical_tie(self):
        frames=[motion_frame(1,(0,0),[(3,4)],[(5,0)]),
                motion_frame(1,(0,0),[(4,0)],[(0,3)])]
        self.assertEqual(nearest_codes(frames),[0,1])
        report=baseline_predictions(frames,0,'official-convention')
        self.assertEqual(report['raw_distance_ties'],1)

    def test_only_home_and_away_vote(self):
        self.assertEqual(smooth_votes([0,-1,1],1),['H','H','A'])
        self.assertEqual(smooth_votes([-1]*3,1),['D']*3)
        self.assertEqual(smooth_votes([1,-1,0],0),['A','D','H'])

    def test_exact_upstream_smoothing_parity(self):
        rng=np.random.default_rng(1729)
        for n in (0,1,2,10,301):
            codes=rng.choice([-1,0,1],n)
            for half_width in (0,25,50,125):
                self.assertEqual(smooth_votes(codes,half_width),upstream_smooth(codes,half_width).tolist())

    def test_small_independent_window_oracle(self):
        codes=[0,-1,1,1,-1,0,-1,1]
        def oracle(width):
            out=[]
            for i in range(len(codes)):
                window=codes[max(0,i-width):i+width+1]
                h=window.count(0);a=window.count(1)
                out.append('D' if h+a==0 else 'H' if h>=a else 'A')
            return out
        for width in (0,1,2,25):self.assertEqual(smooth_votes(codes,width),oracle(width))

    def test_periods_do_not_share_votes(self):
        frames=[motion_frame(1,(0,0),[(1,0)],[(10,0)]),
                motion_frame(2,(0,0),[(10,0)],[(1,0)])]
        for mode in ('official-convention','matched-input'):
            result=baseline_predictions(frames,25,mode)
            self.assertEqual(result['final'],['H','A'])

    def test_official_and_matched_missing_conventions_differ(self):
        frames=[motion_frame(1,None,[(1,0)]*3,[(2,0)]*3) for _ in range(3)]
        literal=baseline_predictions(frames,0,'official-convention')
        matched=baseline_predictions(frames,0,'matched-input')
        self.assertEqual(literal['latent'],['D']*3)
        self.assertEqual(matched['latent'],['X']*3)
        self.assertEqual(matched['final'],['D']*3) # Explicit whole-period materialization convention.

    def test_matched_geometry_barrier_is_latent_x(self):
        frames=moving_fixture(3)
        frames[1]=replace(frames[1],geometry_valid=False)
        literal=baseline_predictions(frames,25,'official-convention')
        matched=baseline_predictions(frames,25,'matched-input')
        self.assertEqual(literal['latent'],['H']*3)
        self.assertEqual(matched['latent'],['H','X','H'])
        self.assertEqual(matched['final'],['H']*3)

    def test_period_zero_stays_unknown(self):
        frame=motion_frame(0,(0,0),[(1,0)],[(2,0)])
        for mode in ('official-convention','matched-input'):
            self.assertEqual(baseline_predictions([frame],0,mode)['final'],['X'])

    def test_matched_votes_do_not_cross_input_barrier(self):
        frames=[motion_frame(1,(0,0),[(1,0)],[(10,0)]),
                replace(moving_fixture(1)[0],geometry_valid=False),
                motion_frame(1,(0,0),[(10,0)],[(1,0)])]
        result=baseline_predictions(frames,125,'matched-input')
        self.assertEqual(result['latent'],['H','X','A'])

    def test_invalid_modes_and_windows_fail(self):
        for width in (-1,True,1.5):
            with self.assertRaises(ValueError):smooth_votes([0],width)
        for width in (1,2):
            with self.assertRaises(ValueError):baseline_predictions(moving_fixture(1),width,'official-convention')
        with self.assertRaises(ValueError):baseline_predictions(moving_fixture(1),0,'best-case')
        with self.assertRaises(ValueError):smooth_votes([2],0)

    def test_family_has_all_eight_declared_comparators(self):
        from cadence_baselines import baseline_family_predictions
        family=baseline_family_predictions(moving_fixture(4))
        self.assertEqual(set(family),{f'{mode}-w{width}' for mode in ('official-convention','matched-input') for width in (0,25,50,125)})
        for result in family.values():self.assertEqual(result['final'],['H']*4)


if __name__=='__main__':
    unittest.main()
