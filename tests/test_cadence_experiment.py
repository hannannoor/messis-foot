import unittest
import copy
import tempfile
from pathlib import Path
import json
from unittest.mock import patch
from dataclasses import replace
import numpy as np

from cadence_fixtures import moving_fixture
from cadence_protocol import VARIANTS
from gap_solver.tactical import feature_rows,PortableTree
from gap_solver.tactical_model import FROZEN_MODEL
from gap_solver.soft_sequence import sequence_usable
from gap_solver.materialization_control import materialize_abstentions
from ball_gap_policy import decode_ball_gap

try:
    from cadence_experiment import CaseInput,apply_regime,infer_variants
except ImportError:
    CaseInput=apply_regime=infer_variants=None


class CadenceExperiment(unittest.TestCase):
    def setUp(self):self.assertIsNotNone(infer_variants,'cadence driver is not implemented')

    def test_regime_resets_stride_at_input_periods(self):
        frames=moving_fixture(12)
        frames=[replace(f,period=1 if i<5 else 2) for i,f in enumerate(frames)]
        result=apply_regime(frames,'retain-2')
        self.assertEqual([i for i,f in enumerate(result) if f.ball_observed],[0,2,4,5,7,9,11])
        for i,f in enumerate(result):
            self.assertEqual(f.home_xy,frames[i].home_xy)
            self.assertEqual(f.period,frames[i].period)
            if not f.ball_observed:
                self.assertIsNone(f.home_distance)
                self.assertIsNone(f.away_distance)
                self.assertIsNone(f.ball_sample_time_s)
                self.assertEqual(f.ball_provenance,'missing')

    def test_fixed_mask_is_deterministic_and_has_no_label_input(self):
        frames=moving_fixture(100)
        one=apply_regime(frames,'mask30-seed1729')
        two=apply_regime(frames,'mask30-seed1729')
        self.assertEqual(one,two)
        self.assertEqual(sum(not f.ball_observed for f in one),30)
        with self.assertRaises(ValueError):apply_regime(frames,'retain-7')

    def test_control_replays_original_functions(self):
        frames=moving_fixture(60,2)
        tree=PortableTree(FROZEN_MODEL['model'])
        support=[tree.predict(row) for row in feature_rows(frames)]
        latent,_=decode_ball_gap(support,[f.period for f in frames],
            [sequence_usable(f) for f in frames],[f.ball_observed for f in frames])
        result=infer_variants(frames)
        self.assertEqual(set(result),set(VARIANTS))
        self.assertEqual(result['frozen-control']['latent'],latent)
        self.assertEqual(result['frozen-control']['final'],materialize_abstentions(latent,[f.period for f in frames]))

    def test_dense_candidate_parity(self):
        result=infer_variants(moving_fixture(40))
        self.assertEqual(result['frozen-control']['final'],result['bounded-reacquisition-speed-v1']['final'])

    def test_reference_mask_cannot_affect_inference(self):
        frames=moving_fixture(25,3)
        case=CaseInput('skillcorner','1874553',frames,np.zeros(25,dtype=np.uint8),np.ones(25,dtype=np.uint8),{})
        first=infer_variants(case.frames)
        altered=replace(case,reference=np.full(25,3,dtype=np.uint8))
        second=infer_variants(altered.frames)
        for name in VARIANTS:self.assertEqual(first[name]['final'],second[name]['final'])

    def test_tags_and_explicit_dead_inputs_are_rejected(self):
        f=moving_fixture(1)[0]
        for changed in (replace(f,tag_team='H'),replace(f,dead_evidence=True),replace(f,restart_hint=True)):
            with self.assertRaises(ValueError):infer_variants([changed])

    def test_wholly_missing_and_period_zero_follow_existing_conventions(self):
        frames=apply_regime(moving_fixture(8),'retain-2')
        frames=[replace(f,ball_x=None,ball_y=None,home_distance=None,away_distance=None) for f in frames]
        result=infer_variants(frames)
        self.assertEqual(result['frozen-control']['latent'],['X']*8)
        self.assertEqual(result['bounded-reacquisition-speed-v1']['final'],['D']*8)
        outside=infer_variants([replace(f,period=0) for f in frames])
        for row in outside.values():self.assertEqual(row['final'],['X']*8)

    def test_complete_synthetic_receipt_is_bound_and_aggregate_only(self):
        import cadence_experiment as driver
        build_receipt=getattr(driver,'build_receipt',None)
        self.assertIsNotNone(build_receipt,'complete receipt builder is not implemented')
        validate_receipt=driver.validate_receipt
        from cadence_protocol import make_freeze
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'input';p.write_text('synthetic')
            inputs={'fixture':p};frozen=make_freeze({'source':p},inputs)
            frames=moving_fixture(80,2)
            case=CaseInput('skillcorner','1874553',frames,np.zeros(80,dtype=np.uint8),np.ones(80,dtype=np.uint8),inputs)
            value=build_receipt(case,'natural',frozen)
            validate_receipt(value,frozen,inputs)
            self.assertEqual(set(value['variants']),set(VARIANTS))
            self.assertIsNone(value['variants']['frozen-control']['dead_metrics']['recall'])
            self.assertEqual(value['variants']['frozen-control']['coverage']['active_rows'],80)
            self.assertFalse(value['exchange_diagnostics']['frozen-control']['path_uniqueness_measured'])
            for mutate in ('extra','array','variant','identity','nested'):
                altered=copy.deepcopy(value)
                if mutate=='extra':altered['event_position']=42
                elif mutate=='array':altered['feature_diagnostics']['repaired_rows']=[1,2,3]
                elif mutate=='variant':altered['variants']['extra-policy']=altered['variants']['frozen-control']
                elif mutate=='identity':altered['experiment_sha256']='0'*64
                else:altered['variants']['frozen-control']['metrics']['hidden_coordinates']=[1,2]
                with self.subTest(mutate=mutate):
                    with self.assertRaises(ValueError):validate_receipt(altered,frozen,inputs)
            p.write_text('changed')
            with self.assertRaises(ValueError):validate_receipt(value,frozen,inputs)

    def test_scoring_rejects_input_period_disagreement(self):
        import cadence_experiment as driver
        from cadence_protocol import make_freeze
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'input';p.write_text('synthetic')
            frozen=make_freeze({'source':p},{'fixture':p})
            case=CaseInput('skillcorner','1874553',moving_fixture(10),np.zeros(10,dtype=np.uint8),np.full(10,2,dtype=np.uint8),{'fixture':p})
            with self.assertRaises(ValueError):driver.build_receipt(case,'natural',frozen)

    def test_unknown_reference_confusion_is_diagnostic_not_scored(self):
        import cadence_experiment as driver
        from cadence_protocol import make_freeze
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'input';p.write_text('synthetic')
            frozen=make_freeze({'source':p},{'fixture':p})
            truth=np.zeros(80,dtype=np.uint8);truth[10:20]=3
            case=CaseInput('skillcorner','1874553',moving_fixture(80,2),truth,np.ones(80,dtype=np.uint8),{'fixture':p})
            receipt=driver.build_receipt(case,'natural',frozen)
            for result in receipt['variants'].values():
                self.assertEqual(len(result['metrics']['confusion']),3)
                self.assertEqual(sum(map(sum,result['metrics']['confusion'])),70)
                self.assertEqual(result['metrics']['n_gt_spells'],2)

    def test_real_synthetic_cache_loader_checks_match_identity(self):
        import cadence_experiment as driver
        from test_skillcorner import write_source
        from gap_solver.skillcorner import load_skillcorner,save_motion_cache
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);paths=write_source(root)
            prefix=root/'independent-reference/cache/1874553-detected'
            save_motion_cache(load_skillcorner(*paths),prefix) # Metadata's actual ID is 7.
            with patch.object(driver,'ROOT',root/'code'):
                with self.assertRaises(ValueError):driver.load_case('skillcorner','1874553')
            meta=json.loads(paths[0].read_text());meta['id']=1874553;paths[0].write_text(json.dumps(meta))
            save_motion_cache(load_skillcorner(*paths),prefix)
            with patch.object(driver,'ROOT',root/'code'):
                loaded=driver.load_case('skillcorner','1874553')
            self.assertEqual(len(loaded.frames),10)
            self.assertEqual(loaded.match,'1874553')


if __name__=='__main__':unittest.main()
