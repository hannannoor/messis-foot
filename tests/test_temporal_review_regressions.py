import copy,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
import test_temporal_selection as fixtures
from test_temporal_metrics import gap_fixture
from gap_solver.temporal_metrics import hidden_opponent_scores
from gap_solver.temporal_selection import validation_gate
from gap_solver.temporal_protocol import digest
import select_temporal_recovery as selection
import evaluate_temporal_final as final


class ReviewRegressions(unittest.TestCase):
    def test_all_positive_gate_fixture_can_still_pass(self):
        reports,endpoints=fixtures.TemporalTraining.gate_fixture(5)
        self.assertTrue(validation_gate(reports,endpoints)['passes'])

    def test_single_opposing_frame_cannot_recover_an_abstained_ten_frame_spell(self):
        frames,gt,before,after=gap_fixture();after=before.copy();after[24]=1;after[34:41]=0
        self.assertEqual(hidden_opponent_scores(gt,before,after,frames)['selected_hits'],0)

    def test_candidate_cannot_lose_existing_hidden_hits_or_primary_spell_to_endpoints(self):
        reports,endpoints=fixtures.TemporalTraining.gate_fixture(5)
        for report in reports:report['hidden_opponents']['baseline_hits']=10
        for report in endpoints:report['selected']['metrics']['spell_f1_mean']=.9
        result=validation_gate(reports,endpoints)
        self.assertFalse(result['passes'])

    def test_masked_support_does_not_hide_natural_recovery_regression(self):
        reports,endpoints=fixtures.TemporalTraining.gate_fixture(5)
        for report in reports:
            report['hidden_opponents'].update(reference_short_spells=1,baseline_hits=1,selected_hits=0)
        masked,masked_endpoints=fixtures.TemporalTraining.gate_fixture(5)
        self.assertFalse(validation_gate(reports,endpoints,masked,masked_endpoints)['passes'])

    def test_final_worker_owns_both_regimes_for_each_unique_match(self):
        jobs=final.build_jobs('test',{'split':{'test':[11,12]}})
        self.assertEqual(len(jobs),2)
        self.assertEqual([args for _,args in jobs],[(11,),(12,)])
        calls=[]
        with patch.object(final,'prepare_one',side_effect=lambda m:calls.append(('prepare',m))),patch.object(final,'evaluate_one',side_effect=lambda *a,**kw:calls.append(('evaluate',a[1])) or a[1]):
            final.evaluate_test_match(11)
        self.assertEqual(calls,[('prepare',11),('evaluate','natural'),('evaluate','masked')])

    def test_full_rules_have_their_own_budget_when_motion_adds_zero(self):
        from test_temporal import motion_fixture
        from gap_solver.core import Decision
        from gap_solver.temporal import mask_motion_frames
        frames=mask_motion_frames(motion_fixture(),[16<=i<41 for i in range(80)])
        base=[Decision('X' if 16<=i<41 else 'H') for i in range(80)]
        rules=selection.full_endpoint_rules(frames,base,2.)
        self.assertEqual(set(rules),{'last_owner','two_sided'})
        self.assertTrue(all(sum(d.label!='X' and b.label=='X' for d,b in zip(pred,base))==25 for pred in rules.values()))

    def test_scoring_source_change_invalidates_evidence_without_refitting(self):
        from gap_solver.temporal_protocol import evidence_identity,require_evidence
        with tempfile.TemporaryDirectory() as d:
            code=Path(d);source=code/'metric.py';source.write_text('x=1\n');inputs=code/'cache.json';inputs.write_text('{}')
            old=evidence_identity({'metric.py':source},{'cache':inputs},'artifact')
            report={'identity':old};source.write_text('x=2\n')
            new=evidence_identity({'metric.py':source},{'cache':inputs},'artifact')
            with self.assertRaises(ValueError):require_evidence(report,new)

    def test_regression_summary_rejects_other_artifacts_missing_cases_duplicates_and_extras(self):
        good=dict(match='m1',identity={'artifact_sha256':'current'},cases={'natural':{},'masked':{}},passes=True)
        for records in ([dict(good,identity={'artifact_sha256':'old'})],[dict(good,cases={'natural':{}})],[good,good],[good,dict(good,match='extra')]):
            with self.assertRaises(ValueError):final.validate_receipts(records,['m1'],lambda m:{'artifact_sha256':'current'},{'natural','masked'})

    def test_rebuilt_cache_generation_preserves_frozen_source_contract_but_changed_input_does_not(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'cache').mkdir();path=root/'cache/7-detected.metadata.json'
            identity=dict(schema_version=2,match_id='7',position_regime='detected_only',input_identity='raw-and-adapter',adapter_sources={'adapter.py':'unchanged'})
            path.write_text(json.dumps(dict(identity,generation_id='new-generation')))
            manifest=dict(split={'test':[7]},source_cache_sha256={'7':'old-generation-digest'},source_cache_identity={'7':identity})
            with patch.object(final,'ROOT',root),patch.object(final,'load_temporal_frozen',return_value=({},manifest)),patch.object(final,'protocol',return_value={'split':manifest['split']}):
                final.frozen()
                path.write_text(json.dumps(dict(identity,input_identity='different-raw-input')))
                with self.assertRaises(ValueError):final.frozen()
