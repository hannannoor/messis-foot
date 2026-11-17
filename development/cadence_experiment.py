"""Bounded external-only cadence pilot. Inference functions accept no reference."""
from dataclasses import dataclass,replace
from pathlib import Path
import numpy as np

from cadence_features import cadence_feature_rows
from cadence_baselines import baseline_family_predictions
from cadence_protocol import CONTROL,CANDIDATE,MATCHES,REGIMES
from gap_solver.tactical import PortableTree
from gap_solver.tactical_model import FROZEN_MODEL
from gap_solver.temporal import mask_motion_frames
from gap_solver.temporal_selection import contiguous_mask
from gap_solver.soft_sequence import sequence_usable
from gap_solver.materialization_control import materialize_abstentions
from ball_gap_policy import decode_ball_gap


ROOT=Path(__file__).resolve().parent
REPORTS=ROOT/'reports/cadence-v2'


@dataclass
class CaseInput:
    cohort: str
    match: str
    frames: list
    reference: np.ndarray
    periods: np.ndarray
    input_paths: dict


def apply_regime(frames,regime):
    if regime not in REGIMES:raise ValueError('Unknown frozen input regime')
    if regime=='natural':return list(frames)
    if regime=='mask30-seed1729':
        mask=contiguous_mask([f.period for f in frames],.30,1729)
    else:
        stride=int(regime.rsplit('-',1)[1]);mask=[];previous=None;offset=0
        for f in frames:
            if f.period!=previous:offset=0
            mask.append(bool(f.period and offset%stride));offset+=1;previous=f.period
    return mask_motion_frames(frames,mask)


def _supports(rows):
    model=FROZEN_MODEL['model'];tree=PortableTree(model)
    if not rows:return np.empty((0,3),dtype=np.float64)
    x=np.asarray(rows,dtype=np.float32)
    nodes=np.zeros(len(x),dtype=np.int32)
    left=np.asarray(model['children_left']);right=np.asarray(model['children_right'])
    feature=np.asarray(model['feature']);threshold=np.asarray(model['threshold'])
    while True:
        active=np.flatnonzero(left[nodes]!=-1)
        if not len(active):break
        at=nodes[active]
        nodes[active]=np.where(x[active,feature[at]]<=threshold[at],left[at],right[at])
    support=np.asarray(model['probabilities'],dtype=np.float64)[nodes]
    for i in range(0,len(rows),257):
        if tuple(support[i])!=tuple(tree.predict(rows[i])):
            raise ValueError('Portable/vectorized frozen tree mismatch')
    return support


def _infer_heads(frames):
    if any(f.dead_evidence or f.tag_team or f.restart_hint for f in frames):
        raise ValueError('Geometry-only inputs required')
    rows=list(cadence_feature_rows(frames))
    periods=[f.period for f in frames];usable=[bool(sequence_usable(f)) for f in frames]
    observed=[bool(f.ball_observed) for f in frames]
    result={}
    for name,features in ((CONTROL,[r.legacy for r in rows]),(CANDIDATE,[r.candidate for r in rows])):
        support=_supports(features)
        latent,diagnostics=decode_ball_gap(support,periods,usable,observed)
        final=materialize_abstentions(latent,periods)
        result[name]=dict(latent=latent,final=final,raw_distance_ties=0,
            policy_diagnostics=diagnostics,sidecars=rows,raw_HA_ties=(support[:,0]==support[:,1]).tolist())
    return result


def infer_variants(frames):
    result=_infer_heads(frames)
    result.update(baseline_family_predictions(frames))
    return result


def case_input_paths(cohort,match):
    match=str(match)
    if (cohort,match) not in MATCHES:raise ValueError('Case is not in the fixed development cohort')
    directory='independent-reference' if cohort=='skillcorner' else 'external-reference'
    prefix=ROOT.parent/directory/'cache'/(match+'-detected' if cohort=='skillcorner' else match)
    files={f'{cohort}/{match}{suffix}':Path(str(prefix)+suffix)
           for suffix in ('.metadata.json','.features.npz','.reference.npz')}
    if cohort=='dfl':
        raw=[p for p in (ROOT.parent/'external-reference/raw').glob('*'+match+'*.xml')
             if 'matchinformation' in p.name or 'positions' in p.name.lower()]
        if len(raw)!=2:raise ValueError('Expected exact DFL metadata/positions pair')
        files.update({f'dfl/raw/{p.name}':p for p in raw})
    return files


def load_case(cohort,match):
    from gap_solver.skillcorner import load_motion_cache
    from gap_solver.external import load_cache
    from gap_solver.dfl_motion import load_dfl_motion
    files=case_input_paths(cohort,match)
    prefix=next(p for p in files.values() if str(p).endswith('.features.npz'))
    prefix=Path(str(prefix)[:-len('.features.npz')])
    if cohort=='skillcorner':
        data=load_motion_cache(prefix);frames=data.frames()
    else:
        data=load_cache(prefix)
        meta=next(p for p in files.values() if 'matchinformation' in p.name)
        raw=next(p for p in files.values() if 'positions' in p.name.lower())
        frames=load_dfl_motion(meta,raw,data)
    expected=str(match) if cohort=='skillcorner' else 'DFL-MAT-'+str(match)
    if str(data.match_id)!=expected:raise ValueError('Cache match identity does not match declared case')
    return CaseInput(cohort,str(match),frames,data.reference,data.periods,files)


def build_receipt(case,regime,frozen):
    from cadence_metrics import diagnostic_metrics
    from cadence_receipts import receipt_variant,validate_receipt
    from cadence_protocol import digest,hash_files
    from accuracy_experiment import aggregate_metrics
    from ball_gap_experiment import dead_metrics
    from accuracy_evidence import boundary_summary
    periods=np.asarray(case.periods);gt=np.asarray(case.reference)
    if (case.cohort,str(case.match)) not in MATCHES or regime not in REGIMES:raise ValueError('Undeclared case/regime')
    if periods.ndim!=1 or gt.ndim!=1 or len(periods)!=len(case.frames) or len(gt)!=len(periods):
        raise ValueError('External reference/input structure differs')
    if not np.isin(periods,[0,1,2]).all() or not np.isin(gt,[0,1,2,3]).all() or not (gt<3).any():
        raise ValueError('Invalid or unsupported external reference')
    if ((periods==0)&(gt!=3)).any() or not np.array_equal(periods,[f.period for f in case.frames]):
        raise ValueError('External reference/input structure differs')
    before=hash_files(case.input_paths)
    if any(frozen['input_sha256'].get(k)!=v for k,v in before.items()):raise ValueError('Unfrozen external input')
    frames=apply_regime(case.frames,regime)
    result=infer_variants(frames)
    encode=lambda labels:np.fromiter(('HADX'.index(s) for s in labels),dtype=np.uint8,count=len(labels))
    incumbent=encode(result[CONTROL]['final']);active=periods>0
    variants={};feature=None
    for name,row in result.items():
        pred=encode(row['final'])
        extra=diagnostic_metrics(gt,pred,periods,result[CANDIDATE]['sidecars'])
        feature=extra['observation']
        latent=np.asarray(row['latent']);final=np.asarray(row['final'])
        whole_unknown=sum(int(at.sum()) for p in (1,2) if (at:=(periods==p)).any() and np.all(latent[at]=='X'))
        diagnostics=row.get('policy_diagnostics',{})
        coverage=dict(active_rows=int(active.sum()),latent_X_rows=int((active&(latent=='X')).sum()),
            materialized_rows=int((active&(latent=='X')&(final!='X')).sum()),
            neutral_rows=int(diagnostics.get('neutral_active_usable_rows',0)),unsupported_rows=int(diagnostics.get('unsupported_active_rows',0)),
            raw_distance_ties=int(row['raw_distance_ties']),wholly_unknown_period_D_rows=whole_unknown)
        variants[name]=receipt_variant(aggregate_metrics(gt,pred,periods,incumbent),
            dead_metrics(gt,pred,periods),boundary_summary(gt,pred,periods),extra,coverage)
    exchanged=[replace(f,home_distance=f.away_distance,away_distance=f.home_distance,
        home_xy=f.away_xy,away_xy=f.home_xy,home_ids=f.away_ids,away_ids=f.home_ids) for f in frames]
    swapped=_infer_heads(exchanged);live=(gt<2)&active;exchange={}
    for name in (CONTROL,CANDIDATE):
        original=encode(result[name]['final']);back=np.asarray([1,0,2,3],dtype=np.uint8)[encode(swapped[name]['final'])]
        changed=live&(original!=back);tied=np.asarray(result[name]['raw_HA_ties'],dtype=bool)
        with_tie=int((changed&tied).sum())
        exchange[name]=dict(known_live_rows=int(live.sum()),changed_after_exchange=int(changed.sum()),
            changed_with_original_raw_HA_tie=with_tie,changed_without_original_raw_HA_tie=int(changed.sum())-with_tie,
            changed_on_ball_missing=int((changed&~np.asarray([f.ball_observed for f in frames])).sum()),path_uniqueness_measured=False)
    if hash_files(case.input_paths)!=before:raise ValueError('External inputs changed during scoring')
    value=dict(schema_version=1,experiment_sha256=digest(frozen),cohort=case.cohort,match=str(case.match),regime=regime,
        fresh_holdout=False,target_data_used=False,head_fitting_performed=False,input_sha256=before,
        variants=variants,feature_diagnostics=feature,exchange_diagnostics=exchange)
    validate_receipt(value,frozen,case.input_paths)
    return value


from cadence_receipts import validate_receipt


def case_filename(cohort,match,regime):
    from cadence_protocol import case_keys
    if (cohort,str(match),regime) not in case_keys():raise ValueError('Unexpected case filename')
    return f'{cohort}-{match}-{regime}.json'


def read_receipt(path,frozen,input_paths):
    import json
    from gap_solver.input_contract import reject_linked_ancestors
    reject_linked_ancestors(path)
    value=json.loads(Path(path).read_text(encoding='utf-8'))
    validate_receipt(value,frozen,input_paths)
    return value


def store_receipt(path,value,frozen,input_paths):
    from cadence_protocol import write_new,digest
    validate_receipt(value,frozen,input_paths)
    if Path(path).exists():
        if digest(read_receipt(path,frozen,input_paths))!=digest(value):raise ValueError('Preserve the original receipt generation')
        return
    write_new(path,value,input_paths.values())


def read_stage(directory,frozen,inputs_by_case):
    from cadence_protocol import case_keys
    directory=Path(directory)
    expected={case_filename(c,m,r) for c,m,r in case_keys()}
    if not directory.is_dir() or {p.name for p in directory.iterdir()}!=expected:
        raise ValueError('Incomplete or unexpected receipt paths')
    result=[]
    for c,m,r in case_keys():
        value=read_receipt(directory/case_filename(c,m,r),frozen,inputs_by_case[c,m])
        if (value['cohort'],value['match'],value['regime'])!=(c,m,r):raise ValueError('Receipt name/case identity differs')
        result.append(value)
    return result


def summarize_receipts(receipts,frozen):
    from statistics import fmean
    from cadence_protocol import VARIANTS,REGIMES,digest
    from cadence_metrics import assess_continuation
    from accuracy_evidence import assert_public_report
    assessment=assess_continuation(receipts)
    if any(r['experiment_sha256']!=digest(frozen) for r in receipts):raise ValueError('Summary contains another experiment')
    def average(values):
        values=list(values)
        return None if any(v is None for v in values) else fmean(values)
    def stats(rows,name):
        selected=[r['variants'][name] for r in rows]
        result={k:average(v['metrics'][k] for v in selected) for k in ('spell_f1_mean','accuracy','macro_f1','alive_dead_f1')}
        result['D_recall']=average(v['dead_metrics']['recall'] if v['dead_metrics']['n_dead'] else None for v in selected)
        result['false_D_rate']=average(v['dead_metrics']['false_D']/v['dead_metrics']['n_live'] if v['dead_metrics']['n_live'] else None for v in selected)
        result['short_spell_recall_iou_05']=average(v['supplementary']['spell_duration']['short']['per_iou']['0.5']['recall'] for v in selected)
        result['HA_boundary_recall_25']=average(v['supplementary']['HA_boundaries']['25']['recall'] for v in selected)
        return result
    by_provider={c:{regime:{name:stats([r for r in receipts if r['cohort']==c and r['regime']==regime],name)
                 for name in VARIANTS} for regime in REGIMES} for c in ('dfl','skillcorner')}
    balanced={regime:{name:{k:average(by_provider[c][regime][name][k] for c in ('dfl','skillcorner'))
              for k in by_provider['dfl'][regime][name]} for name in VARIANTS} for regime in REGIMES}
    value=dict(schema_version=1,experiment_sha256=digest(frozen),cases_scored=20,variant_scorings=200,
        prior_aborted_variant_scorings=frozen['protocol']['prior_aborted_variant_scorings'],
        total_external_variant_scoring_invocations=frozen['protocol']['max_total_external_variant_scoring_invocations'],
        fresh_holdout=False,target_accuracy_measured=False,head_fitting_performed=False,
        by_provider=by_provider,equal_provider=balanced,assessment=assessment,
        receipt_digest_sha256={case_filename(r['cohort'],r['match'],r['regime']):digest(r) for r in receipts},
        limitations=['Four previously examined development matches; no fresh qualification.',
            'One fixed .20s compatibility contrast; unknown velocities can retain legacy zero encoding.',
            'SkillCorner has known-live H/A reference, not positive D truth.',
            'Cadence and masking are artificial corruptions, not calibrated sensor failure.',
            'External majority port uses canonical raw ties and input-period resets.',
            'Raw head tie flags do not establish complete-path uniqueness.',
            'No challenge assets, target correctness labels, new target inference or model fitting.'])
    assert_public_report(value)
    return value


def source_paths():
    from ball_gap_candidate import selected_artifact
    artifact,path=selected_artifact()
    names=set(artifact['source_sha256'])|set(artifact['evidence_file_sha256'])|{path.relative_to(ROOT).as_posix()}
    names.update(p.relative_to(ROOT).as_posix() for p in (ROOT/'gap_solver').glob('*.py'))
    names.update(p.relative_to(ROOT).as_posix() for p in ROOT.glob('cadence_*.py'))
    names.update(p.relative_to(ROOT).as_posix() for p in (ROOT/'tests').glob('test_cadence_*.py'))
    names.update(('tests/cadence_fixtures.py','tests/official_baseline_reference.py','tests/official-baseline-source.json',
        'licenses/official-baseline-MIT.txt','docs/superpowers/specs/2026-11-08-post-audit-roadmap-design.md',
        'docs/superpowers/plans/2026-11-08-cadence-and-baselines.md'))
    required={'cadence_features.py','cadence_baselines.py','cadence_protocol.py','cadence_metrics.py','cadence_receipts.py','cadence_experiment.py'}
    if not required<=names:raise ValueError('Implementation must be complete before freezing')
    return {name:ROOT/name for name in sorted(names)}


def all_input_paths():
    return {key:path for c,m in MATCHES for key,path in case_input_paths(c,m).items()}


def freeze():
    import json
    from cadence_protocol import make_freeze,validate_freeze,write_new
    sources,inputs=source_paths(),all_input_paths()
    value=make_freeze(sources,inputs)
    path=REPORTS/'comparison-freeze.json'
    if path.exists():
        old=json.loads(path.read_text(encoding='utf-8'));validate_freeze(old,sources,inputs)
        if old!=value:raise ValueError('Keep original freeze')
    else:write_new(path,value,(*sources.values(),*inputs.values()))
    print('Frozen 20 cases / 10 variants; no fitting or target inference',flush=True)
    return value


def load_freeze():
    import json
    from cadence_protocol import validate_freeze
    value=json.loads((REPORTS/'comparison-freeze.json').read_text(encoding='utf-8'))
    validate_freeze(value,source_paths(),all_input_paths())
    return value


def _store_identical(path,value,inputs):
    import json
    from cadence_protocol import write_new,digest
    if path.exists():
        if digest(json.loads(path.read_text(encoding='utf-8')))!=digest(value):raise ValueError('Preserve original sealed evidence')
    else:write_new(path,value,inputs)


def run_cases(cohort=None,match=None,regime=None):
    import time
    from cadence_protocol import case_keys,hash_files,digest,write_new
    frozen=load_freeze()
    jobs=[(c,m,r) for c,m,r in case_keys() if (cohort is None or c==cohort) and (match is None or m==str(match)) and (regime is None or r==regime)]
    if not jobs:raise ValueError('No declared case matches request')
    loaded=None;case=None
    for c,m,r in jobs:
        destination=REPORTS/'cases'/case_filename(c,m,r);inputs=case_input_paths(c,m)
        if destination.exists():
            read_receipt(destination,frozen,inputs);print(f'Preserved {c}-{m} {r}',flush=True);continue
        attempt=ROOT/'.tmp/cadence-v2-attempts'/case_filename(c,m,r)
        if attempt.exists():raise ValueError('An unfinished attempt exists; do not silently exceed the fixed scoring budget')
        if loaded!=(c,m):case=load_case(c,m);loaded=(c,m)
        write_new(attempt,dict(experiment_sha256=digest(frozen),cohort=c,match=m,regime=r,started=True),inputs.values())
        start=time.perf_counter();value=build_receipt(case,r,frozen)
        if frozen['source_sha256']!=hash_files(source_paths()):raise ValueError('Source changed during case scoring')
        store_receipt(destination,value,frozen,inputs)
        print(f'Scored {c}-{m} {r}: ten fixed variants; {time.perf_counter()-start:.1f}s',flush=True)
    print('Requested fixed cases complete',flush=True)


def summarize():
    from cadence_protocol import hash_files,digest
    frozen=load_freeze();inputs={(c,m):case_input_paths(c,m) for c,m in MATCHES}
    rows=read_stage(REPORTS/'cases',frozen,inputs)
    value=summarize_receipts(rows,frozen)
    files={case_filename(c,m,r):REPORTS/'cases'/case_filename(c,m,r) for c,m,r in __import__('cadence_protocol').case_keys()}
    seal=dict(experiment_sha256=digest(frozen),case_file_sha256=hash_files(files),cases_scored=20,variant_scorings=200)
    protected=all_input_paths().values()
    _store_identical(REPORTS/'case-seal.json',seal,protected)
    _store_identical(REPORTS/'summary.json',value,protected)
    print('Summary complete; automatic continuation: '+str(value['assessment']['automatic_continuation_allowed']),flush=True)
    return value


def verify():
    import json
    from cadence_protocol import hash_files,digest
    frozen=load_freeze();rows=read_stage(REPORTS/'cases',frozen,{(c,m):case_input_paths(c,m) for c,m in MATCHES})
    files={case_filename(c,m,r):REPORTS/'cases'/case_filename(c,m,r) for c,m,r in __import__('cadence_protocol').case_keys()}
    seal=json.loads((REPORTS/'case-seal.json').read_text(encoding='utf-8'))
    expected=dict(experiment_sha256=digest(frozen),case_file_sha256=hash_files(files),cases_scored=20,variant_scorings=200)
    if seal!=expected:raise ValueError('Case bytes/inventory/seal changed')
    summary=json.loads((REPORTS/'summary.json').read_text(encoding='utf-8'))
    if digest(summary)!=digest(summarize_receipts(rows,frozen)):raise ValueError('Summary does not reproduce from sealed receipts')
    proof=dict(experiment_sha256=digest(frozen),cases_verified=20,variant_scores_verified=200,
        sources_and_inputs_verified=True,receipt_schemas_verified=True,summary_reproduces=True,
        new_holdout=False,target_data_used=False,head_fitting_performed=False)
    _store_identical(REPORTS/'verification.json',proof,all_input_paths().values())
    print('Verified 20 receipts / 200 aggregate scores and unchanged source/input identities',flush=True)
    return proof


def main():
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage',choices=('freeze','run','summarize','verify'))
    parser.add_argument('--cohort',choices=('dfl','skillcorner'));parser.add_argument('--match');parser.add_argument('--regime',choices=REGIMES)
    args=parser.parse_args()
    if args.stage=='run':return run_cases(args.cohort,args.match,args.regime)
    if any(x is not None for x in (args.cohort,args.match,args.regime)):parser.error('Case arguments apply only to run')
    return {'freeze':freeze,'summarize':summarize,'verify':verify}[args.stage]()


if __name__=='__main__':main()
