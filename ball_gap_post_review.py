"""Additive carry/delta audit and release-anchored verification; frozen scores unchanged."""
import argparse,json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
DESIGN='docs/superpowers/specs/2026-11-07-ball-gap-evidence-design.md'


def carry_counts(latent,periods,final):
    if len(latent)!=len(periods) or len(final)!=len(periods):raise ValueError('Carry audit dimensions differ')
    if any(v not in 'HADX' for v in (*latent,*final)) or any(p not in (0,1,2) for p in periods):raise ValueError('Invalid carry audit codes')
    counts=dict(wholly_latent_X_periods=0,wholly_latent_X_period_rows=0,fallback_D_rows=0,
        latent_X_carried_to_D_rows=0,latent_X_carried_to_H_rows=0,latent_X_carried_to_A_rows=0,materialized_active_rows=0)
    i=0
    while i<len(periods):
        if not periods[i]:i+=1;continue
        first=i;period=periods[i]
        while i<len(periods) and periods[i]==period:i+=1
        if all(v=='X' for v in latent[first:i]):
            if any(v!='D' for v in final[first:i]):raise ValueError('Entire unknown-period carry must be explicit D convention')
            counts['wholly_latent_X_periods']+=1;counts['wholly_latent_X_period_rows']+=i-first;counts['fallback_D_rows']+=i-first
    for p,before,after in zip(periods,latent,final):
        if p and before!=after:
            counts['materialized_active_rows']+=1
            if before=='X' and after in 'HAD':counts['latent_X_carried_to_'+after+'_rows']+=1
    return counts


def paired_deltas(rows):
    result=[]
    for r in rows:
        old=r['variants']['w0-c32']['metrics'];new=r['variants']['w0-c32-neutral-missing']['metrics']
        result.append(dict(stage=r['stage'],cohort=r['cohort'],match=r['match'],regime=r['regime'],
            **{m+'_delta':new[m]-old[m] for m in ('accuracy','macro_f1','spell_f1_mean')}))
    return result


def check_structure(root=ROOT):
    from gap_solver.accuracy_protocol import SPLITS
    from gap_solver.input_contract import sha256
    root=Path(root);reports=root/'reports/ball-gap';runner=json.loads((reports/'runner-source.json').read_text())
    if set(runner['source_sha256'])!={'ball_gap_run.py'}:raise ValueError('Runner seal needs exact source key')
    frozen=json.loads((reports/'comparison-freeze.json').read_text())
    if sha256(root/DESIGN)!=frozen['approved_design_sha256']:raise ValueError('Actual approved design bytes changed')
    for stage,groups in SPLITS.items():
        expected={f'{c}-{m}-{regime}.json' for c,ids in groups.items() for m in ids for regime in ('natural','masked')}
        if {p.name for p in (reports/stage).glob('*.json')}!=expected:raise ValueError('Stage receipt inventory differs from declared cases')


def source_paths():return {n:ROOT/n for n in ('ball_gap_post_review.py','ball_gap_runtime.py')}


def seal():
    import ball_gap_experiment as e
    import ball_gap_run as runner
    from gap_solver.accuracy_protocol import hash_files
    check_structure();runner.activate();e.load_freeze()
    names=['comparison-freeze','runner-source','validation-seal','validation-disposition','regression-seal','summary']
    value=dict(schema_version=1,source_sha256=hash_files(source_paths()),
        original_evidence_file_sha256=hash_files({n+'.json':e.REPORTS/(n+'.json') for n in names}),
        inference_or_parameter_change=False,scope='additive carry counts and paired deltas only')
    if (e.REPORTS/'post-review-diagnostics.json').exists():raise ValueError('Do not create or alter audit seal after its report exists')
    e.store_identical(e.REPORTS/'post-review-source.json',value)


def check_audit_source():
    import ball_gap_experiment as e
    from accuracy_evidence import portable_require_files
    value=json.loads((e.REPORTS/'post-review-source.json').read_text())
    portable_require_files(value['source_sha256'],source_paths())
    portable_require_files(value['original_evidence_file_sha256'],{n:e.REPORTS/n for n in value['original_evidence_file_sha256']})
    check_structure()


def build_supplement():
    import ball_gap_experiment as e
    import ball_gap_run as runner
    from accuracy_evidence import RAW_LOAD_CASE,canonical_map,canonical_key
    from gap_solver.accuracy_protocol import digest
    check_audit_source();runner.activate();frozen,core=e.load_freeze();e.verify_old();e.verified_disposition(frozen)
    rows=[r for stage in ('validation','regression') for r in e.sealed_stage(stage,frozen)];cases=paired_deltas(rows)
    for r,case in zip(rows,cases):
        c,m,regime=r['cohort'],r['match'],r['regime'];a,_=RAW_LOAD_CASE(c,m,regime,core);periods=a['periods']
        paths=e.original.engine.input_paths(c,m);logical,feature=next((k,p) for k,p in paths.items() if str(p).endswith('.features.npz'))
        observed=e.load_availability(feature,canonical_map(core['input_sha256'][f'{c}-{m}'])[canonical_key(logical)],periods,c,regime)
        latent,diag=e.decode_ball_gap(a['supports'],periods,a['usable'].tolist(),observed.tolist());final=e.materialize_abstentions(latent,periods)
        counts=carry_counts(latent,periods,final)
        if counts['materialized_active_rows']!=r['policy_diagnostics']['materialized_active'] or any(diag[k]!=r['policy_diagnostics'][k] for k in diag):raise ValueError('Additive replay changed original policy diagnostics')
        case['materialization']=counts
    return dict(schema_version=1,experiment_sha256=digest(frozen),audit_source_sha256=e.sha256(e.REPORTS/'post-review-source.json'),
        inference_or_parameter_change=False,fresh_holdout=False,target_accuracy_measured=False,cases=cases)


def verify():
    from ball_gap_candidate import selected_artifact
    import ball_gap_experiment as e
    selected_artifact()  # independent constant anchors runtime, runner seal, design and every receipt
    check_structure();value=build_supplement()
    if value!=json.loads((e.REPORTS/'post-review-diagnostics.json').read_text()):raise ValueError('Post-review diagnostics differ on exact replay')
    frozen,_=e.load_freeze()
    if e.summary_value(frozen)!=json.loads((e.REPORTS/'summary.json').read_text()):raise ValueError('Sealed summary differs')
    print('Released source/model/design/runner/receipt bindings, all26 carry/delta replays and dispositions verified',flush=True)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('stage',choices=['seal','supplement','verify']);args=p.parse_args()
    if args.stage=='seal':seal()
    elif args.stage=='supplement':
        import ball_gap_experiment as e
        value=build_supplement();e.store_identical(e.REPORTS/'post-review-diagnostics.json',value);print('26 additive carry diagnostics and signed paired deltas complete',flush=True)
    else:verify()

if __name__=='__main__':main()
