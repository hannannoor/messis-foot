"""Replay committed metrics from existing verified EXTERNAL score/reference caches.

No acquisition, fitting, target data or mutation of the published receipts.
"""
from pathlib import Path
import json,sys,hashlib
import numpy as np
ROOT=Path(__file__).resolve().parent
CODE=ROOT.parent/'ball-gap-work'
sys.path.insert(0,str(CODE))
import ball_gap_experiment as e
import ball_gap_run as runner
from ball_gap_candidate import selected_artifact
from accuracy_evidence import RAW_LOAD_CASE,canonical_map,canonical_key,boundary_summary,assert_public_report


def main():
    artifact,_=selected_artifact();runner.activate();frozen,core=e.load_freeze();e.verify_old();cases=[];checked=0
    for stage in ('validation','regression'):
        for r in e.sealed_stage(stage,frozen):
            c,m,regime=r['cohort'],r['match'],r['regime'];arrays,record=RAW_LOAD_CASE(c,m,regime,core)
            gt,periods=e.original.engine.reference(c,m);assert np.array_equal(periods,arrays['periods'])
            paths=e.original.engine.input_paths(c,m);logical,feature=next((k,p) for k,p in paths.items() if str(p).endswith('.features.npz'))
            observed=e.load_availability(feature,canonical_map(core['input_sha256'][f'{c}-{m}'])[canonical_key(logical)],periods,c,regime)
            latent,diag=e.decode_ball_gap(arrays['supports'],periods,arrays['usable'].tolist(),observed.tolist())
            candidate=e.original.engine.encode(e.materialize_abstentions(latent,periods))
            base_latent=e.decode_soft(e.soft_emissions(arrays['supports'],arrays['motion_scores'],0.),periods,arrays['usable'],32.)
            baseline=e.original.engine.encode(e.materialize_abstentions(base_latent,periods))
            for name,pred in ((e.BASELINE,baseline),(e.POLICY_ID,candidate),('agreement-plus-carry',arrays['agreement-plus-carry'])):
                actual=e.original.aggregate_metrics(gt,pred,periods,arrays['incumbent']);expected=r['variants'][name]
                assert actual=={k:expected[k] for k in actual},(stage,c,m,regime,name,'aggregate')
                assert e.dead_metrics(gt,pred,periods)==expected['dead_metrics'],(stage,c,m,regime,name,'dead_metrics')
                assert boundary_summary(gt,pred,periods)==expected['boundary_metrics'],(stage,c,m,regime,name,'boundaries')
                for scope,mask in (('ball_available',observed),('ball_missing',~observed)):
                    at=(gt<3)&mask&(periods>0);cm=np.bincount((gt[at]*4+pred[at]).astype(np.int64),minlength=16).reshape(4,4)
                    assert cm.tolist()==expected['input_strata'][scope]['confusion']
                    assert int(at.sum())==expected['input_strata'][scope]['known_frames']
                checked+=1
            for key,value in diag.items():assert value==r['policy_diagnostics'][key]
            assert sum(p>0 and l=='X' for p,l in zip(periods,latent))==r['policy_diagnostics']['latent_unknown_active']
            cases.append(dict(stage=stage,cohort=c,match=m,regime=regime,variants_checked=3,
                aggregate_metrics_match=True,dead_interval_counts_match=True,boundary_metrics_match=True,input_strata_match=True,
                original_scored_receipt_sha256=e.sha256(e.output_path(stage,c,m,regime))))
            print(f'Verified {stage} {c}-{m} {regime}: all3variants and supplementary metrics',flush=True)
    selected_artifact()
    result=dict(schema_version=1,cases=cases,case_receipts_checked=len(cases),variant_scoring_replays=checked,
        source_release_sha256=e.digest(artifact),all_published_metrics_reproduce=True,
        existing_external_cache_and_score_arrays_used=True,raw_acquisition_rebuilt=False,
        independent_provider_truth_verified=False,new_holdout=False,target_data_used=False,model_fitting=False,
        public_source_snapshot_commit='cee674190775e9356745f461ba1561e9f2a46f7e',
        verification_script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    assert len(cases)==26 and checked==78;assert_public_report(result)
    (ROOT/'external-score-replay.json').write_text(json.dumps(result,indent=2)+'\n')
    print('All26published case receipts and78variant scores/supplements reproduced from retained external caches',flush=True)

if __name__=='__main__':main()
