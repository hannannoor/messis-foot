"""One frozen diagnostic test, independent ablations/stresses and explicitly seen regressions."""
import argparse,json
from concurrent.futures import ProcessPoolExecutor,as_completed
from dataclasses import replace
from pathlib import Path
import numpy as np
from select_temporal_recovery import CODE,ROOT,WORK,sha,write_json,protocol,prepare_one,load_case,case_frames,compare
from gap_solver.core import infer
from gap_solver.motion import motion_frame
from gap_solver.temporal import (PortableBoosted,TemporalPolicy,motion_feature_rows,anchor_context,
    mask_motion_frames,decode_team_sequence,apply_temporal_policy)
from gap_solver.temporal_development import codes,decisions,symmetric_scores,endpoint_predictions
from gap_solver.temporal_protocol import load_temporal_frozen,digest,evidence_identity,require_evidence
from gap_solver.temporal_acceptance import final_acceptance
from gap_solver.temporal_selection import contiguous_mask
from gap_solver.skillcorner import load_motion_cache
from gap_solver.tactical import infer_tactical,Policy
from gap_solver.tactical_model import FROZEN_MODEL
from gap_solver.external import load_cache
from gap_solver.dfl_motion import load_dfl_motion
from gap_solver.temporal_metrics import score_temporal,native_gap_statistics
from freeze_temporal import cache_source_identity


def frozen():
    artifact,manifest=load_temporal_frozen(WORK/'frozen',CODE)
    if manifest['split']!=protocol()['split']:raise ValueError('frozen/source split changed')
    for match,expected in manifest['source_cache_identity'].items():
        if cache_source_identity(ROOT/'cache'/f'{match}-detected.metadata.json')!=expected:raise ValueError('frozen source cache changed')
    return artifact,manifest


def report_identity(match,regime='detected',mask_regime='natural'):
    _,manifest=frozen()
    return dict(artifact_sha256=manifest['artifact_sha256'],source_sha256=manifest['source_sha256'],match=match,mask_regime=mask_regime,position_regime=regime,
        source_cache_sha256=sha(ROOT/'cache'/f'{match}-{regime}.metadata.json'))


def regression_identity(match):
    _,manifest=frozen();root=CODE.parent/'external-reference'
    inputs={p.relative_to(root).as_posix():p for p in (root/'raw').glob('*'+match+'*.xml') if 'matchinformation' in p.name or 'positions' in p.name}
    inputs.update({f'cache/{match}'+suffix:root/'cache'/(match+suffix) for suffix in ('.features.npz','.reference.npz','.metadata.json')})
    value=evidence_identity({},inputs,manifest['artifact_sha256']);value['source_sha256']=manifest['source_sha256'];return value


def validate_receipts(records,expected_matches,identity_for,expected_cases):
    ids=[r['match'] for r in records]
    if len(ids)!=len(set(ids)) or set(ids)!=set(expected_matches):raise ValueError('Missing, duplicate or extra completion receipts')
    for record in records:
        require_evidence(record,identity_for(record['match']))
        if set(record.get('cases',{}))!=set(expected_cases):raise ValueError('Missing or unexpected receipt cases')


def predict(frames,base,artifact,x=None):
    if x is None:x=np.asarray(list(motion_feature_rows(frames)),dtype=np.float32)
    scores=symmetric_scores(artifact['model'],x)
    indices=np.linspace(0,len(x)-1,min(100,len(x)),dtype=int);portable=PortableBoosted(artifact['model'])
    np.testing.assert_allclose([portable.symmetric_score(x[i]) for i in indices],scores[indices],rtol=0,atol=1e-12)
    scores[codes(base)!=3]=0.
    policy=TemporalPolicy(**artifact['policy'])
    posterior=np.asarray(decode_team_sequence(scores,frames,base,artifact['transition_cost']*policy.switch_multiplier))/artifact['temperature']
    return apply_temporal_policy(frames,base,posterior,policy),scores


def evaluate_one(match,name,regime='detected',prepared=False):
    artifact,manifest=frozen();destination=WORK/'final'/f'{match}-{regime}-{name}.json'
    identity=report_identity(match,regime,name)
    if destination.exists():
        previous=json.loads(destination.read_text())
        if previous['identity']!=identity:raise ValueError('existing final result has a different frozen identity')
        return f'{match} {name} {regime}: preserved frozen final result'
    if not prepared:prepare_one(match,regime)
    data=load_motion_cache(ROOT/'cache'/f'{match}-{regime}');case=load_case(match,name,regime)
    frames=case_frames(data,case);base=decisions(case['baseline']);pred,scores=predict(frames,base,artifact,case['x'])
    endpoint,matching=endpoint_predictions(frames,base,pred,artifact['policy']['max_gap_s'])
    last,_=endpoint_predictions(frames,base,pred,artifact['policy']['max_gap_s'],mode='last_owner')
    report=compare(data,frames,base,pred)
    result=dict(identity=identity,match=match,observation_regime=regime,mask_regime=name,motion=report,
        endpoint=compare(data,frames,base,endpoint),last_owner=compare(data,frames,base,last),matching=matching,
        native_observations=native_gap_statistics(data),geometry_vs_frozen=compare(data,frames,infer(frames),base),
        no_decoder=compare(data,frames,base,apply_temporal_policy(frames,base,scores,TemporalPolicy(**artifact['policy']))))
    if name=='natural':
        result['reference_boundary_sensitivity']={}
        for shift in (-3,3):
            gt=np.full(len(data.reference),3,dtype=np.uint8)
            for period in (1,2):
                at=np.flatnonzero(data.periods==period);source=at+shift
                ok=(source>=0)&(source<len(gt));at=at[ok];source=source[ok]
                ok=data.periods[source]==period;gt[at[ok]]=data.reference[source[ok]]
            result['reference_boundary_sensitivity'][str(shift/25)+'s']=dict(
                baseline=score_temporal(gt,codes(base),data.periods),selected=score_temporal(gt,codes(pred),data.periods),
                interpretation='nearest canonical sensitivity to one native 0.1s sample (0.12s); no prediction/tuning change')
    write_json(destination,result)
    return '{} {} {}: frozen spell {:.4f}->{:.4f}; X {:.2%}->{:.2%}'.format(match,name,regime,
        report['baseline']['metrics']['spell_f1_mean'],report['selected']['metrics']['spell_f1_mean'],
        report['baseline']['coverage']['undecided_fraction'],report['selected']['coverage']['undecided_fraction'])


def evaluate_test_match(match):
    prepare_one(match)
    return '\n'.join(evaluate_one(match,name,prepared=True) for name in ('natural','masked'))


def stress_frames(frames,name):
    result=[]
    for i,f in enumerate(frames):
        if name=='opponent_loss':
            result.append(replace(f,away_xy=(),away_ids=(),away_distance=None));continue
        if name=='identity_discontinuity':
            offset=10000 if (i//100)%2 else 0
            result.append(replace(f,home_ids=tuple(v+offset for v in f.home_ids),away_ids=tuple(v+offset for v in f.away_ids)));continue
        source=f
        if name=='ball_time_shift':
            at=i-3
            source=frames[at] if at>=0 and frames[at].period==f.period else None
        ball=(source.ball_x,source.ball_y) if source is not None and source.ball_observed else None
        if name=='false_ball' and i%100==0 and ball is not None:ball=(105.3-ball[0],68-ball[1])
        result.append(motion_frame(f.period,ball,f.home_xy,f.away_xy,f.home_ids,f.away_ids,
            geometry_valid=f.geometry_valid,ball_native_observation=False,ball_provenance='synthetic_stress'))
    return result


def stress_one(match):
    artifact,manifest=frozen();destination=WORK/'stresses'/f'{match}.json'
    if destination.exists():
        require_evidence(json.loads(destination.read_text()),report_identity(match))
        return f'{match}: preserved stresses'
    data=load_motion_cache(ROOT/'cache'/f'{match}-detected');result=dict(identity=report_identity(match),artifact_sha256=manifest['artifact_sha256'],match=match,cases={})
    for name in ('opponent_loss','identity_discontinuity','false_ball','ball_time_shift'):
        frames=stress_frames(data.frames(),name)
        base=infer_tactical(frames,FROZEN_MODEL['model'],Policy(**FROZEN_MODEL['policy']));pred,_=predict(frames,base,artifact)
        result['cases'][name]=compare(data,frames,base,pred)
        if name=='opponent_loss' and codes(base).tolist()!=codes(pred).tolist():raise ValueError('missing opponent guard failed')
    write_json(destination,result);return f'{match}: completed four predeclared input-mechanism stresses'


def regression_one(match):
    artifact,manifest=frozen();destination=WORK/'seen-dfl'/f'{match}.json'
    if destination.exists():
        require_evidence(json.loads(destination.read_text()),regression_identity(match))
        return f'{match}: preserved seen regression'
    root=CODE.parent/'external-reference';data=load_cache(root/'cache'/match)
    raw=list((root/'raw').glob('*'+match+'*.xml'))
    meta=next(p for p in raw if 'matchinformation' in p.name);tracking=next(p for p in raw if 'positions' in p.name.lower())
    frames=load_dfl_motion(meta,tracking,data);mask=contiguous_mask(data.periods,.3,1729+sum(map(ord,match)))
    result=dict(identity=regression_identity(match),artifact_sha256=manifest['artifact_sha256'],match=match,scope='explicitly seen development/selection data; no fresh D validation',cases={})
    for name,case in (('natural',frames),('masked',mask_motion_frames(frames,mask))):
        base=infer_tactical(case,FROZEN_MODEL['model'],Policy(**FROZEN_MODEL['policy']));pred,_=predict(case,base,artifact)
        # DFL has no SkillCorner reconciliation fields; use full provider reference directly.
        report=compare_temporal_dfl(data,case,base,pred)
        result['cases'][name]=report
    result['passes']=all(r['selected']['metrics']['spell_f1_mean']>=r['baseline']['metrics']['spell_f1_mean']
        and r['selected']['metrics']['macro_f1']>=r['baseline']['metrics']['macro_f1'] for r in result['cases'].values())
    write_json(destination,result);return f'{match}: seen DFL complete-target regression passes={result["passes"]}'


def compare_temporal_dfl(data,frames,base,pred):
    from gap_solver.temporal_metrics import compare_temporal
    report=compare_temporal(data.reference,codes(base),codes(pred),data.periods,frames)
    report['new_ha_during_provider_dead']=int(((data.reference==2)&(codes(base)==3)&(codes(pred)<2)).sum())
    return report


def summarize():
    artifact,manifest=frozen();matches=manifest['split']['test'];values={}
    for match in matches:
        for name in ('natural','masked'):
            value=json.loads((WORK/'final'/f'{match}-detected-{name}.json').read_text())
            require_evidence(value,report_identity(match,mask_regime=name))
            values[match,name]=value
    regression=[json.loads(path.read_text()) for path in (WORK/'seen-dfl').glob('*.json')]
    expected=set(sum(json.loads((CODE.parent/'external-reference/provenance.json').read_text())['split'].values(),[]))
    validate_receipts(regression,expected,regression_identity,{'natural','masked'})
    regression_passed=all(r['passes'] and all(v['selected']['metrics']['spell_f1_mean']>=v['baseline']['metrics']['spell_f1_mean']
        and v['selected']['metrics']['macro_f1']>=v['baseline']['metrics']['macro_f1'] for v in r['cases'].values()) for r in regression)
    stresses=[json.loads(path.read_text()) for path in (WORK/'stresses').glob('*.json')]
    validate_receipts(stresses,manifest['split']['validation'],report_identity,{'opponent_loss','identity_discontinuity','false_ball','ball_time_shift'})
    available=[]
    for match in manifest['split']['validation']:
        record=json.loads((WORK/'final'/f'{match}-available-natural.json').read_text());require_evidence(record,report_identity(match,'available'));available.append(record)
    natural=[values[m,'natural']['motion'] for m in matches];endpoint=[values[m,'natural']['endpoint'] for m in matches]
    masked=[values[m,'masked']['motion'] for m in matches];masked_endpoint=[values[m,'masked']['endpoint'] for m in matches]
    acceptance=final_acceptance(natural,endpoint,masked,masked_endpoint,artifact['validation_passed'],regression_passed)
    result=dict(schema_version=1,artifact_sha256=manifest['artifact_sha256'],validation_eligibility=artifact['eligibility'],
        acceptance=acceptance,local_inference_authorized=acceptance['passes'],matches=matches,seen_regression_passed=regression_passed,
        summary={name:dict(mean_spell_f1=float(np.mean([r[name]['metrics']['spell_f1_mean'] for r in natural])),
            mean_unknown_fraction=float(np.mean([r[name]['coverage']['undecided_fraction'] for r in natural]))) for name in ('baseline','selected')},
        completion=dict(test_match_regimes=len(values),seen_dfl_matches=len(regression),stress_matches=len(stresses),available_ablation_matches=len(available)),
        stress_results=[dict(match=r['match'],cases={name:dict(spell_f1=v['selected']['metrics']['spell_f1_mean'],newly_assigned=v['change']['newly_resolved_frames']) for name,v in r['cases'].items()}) for r in stresses],
        available_ablation=[dict(match=r['match'],unknown_fraction=r['motion']['selected']['coverage']['undecided_fraction'],spell_f1=r['motion']['selected']['metrics']['spell_f1_mean'],newly_assigned=r['motion']['change']['newly_resolved_frames']) for r in available],
        local_accuracy_measured=False,independent_live_dead_validation=False,default_promoted=False)
    write_json(WORK/'final-summary.json',result);print(json.dumps(result,indent=2),flush=True)


def build_jobs(stage,manifest):
    if stage=='test':return [(evaluate_test_match,(m,)) for m in manifest['split']['test']]
    elif stage=='available':return [(evaluate_one,(m,'natural','available')) for m in manifest['split']['validation']]
    elif stage=='stresses':return [(stress_one,(m,)) for m in manifest['split']['validation']]
    else:
        split=json.loads((CODE.parent/'external-reference/provenance.json').read_text())['split']
        return [(regression_one,(m,)) for m in sum(split.values(),[])]


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('stage',choices=['test','available','stresses','seen-dfl','summarize']);parser.add_argument('--workers',type=int,default=2);args=parser.parse_args()
    _,manifest=frozen()
    if args.stage=='summarize':summarize();return
    jobs=build_jobs(args.stage,manifest)
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        futures=[pool.submit(function,*args) for function,args in jobs]
        for future in as_completed(futures):print(future.result(),flush=True)


if __name__=='__main__':main()
