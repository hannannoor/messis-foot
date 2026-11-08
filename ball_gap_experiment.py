"""Single predeclared external ball-gap experiment; only bounded aggregates leave caches."""
import argparse,json
from concurrent.futures import ProcessPoolExecutor,as_completed
from pathlib import Path
import numpy as np
import accuracy_experiment as original
from accuracy_evidence import assert_public_report,boundary_summary,portable_require_files,canonical_map,canonical_key,RAW_LOAD_CASE
from gap_solver.accuracy_protocol import SPLITS,digest,hash_files
from gap_solver.temporal_selection import contiguous_mask
from gap_solver.soft_sequence import soft_emissions,decode_soft
from gap_solver.materialization_control import materialize_abstentions
from ball_gap_policy import decode_ball_gap,POLICY_ID

ROOT=Path(__file__).resolve().parent
REPORTS=ROOT/'reports/ball-gap'
BASELINE='w0-c32'
VARIANTS=(BASELINE,POLICY_ID,'agreement-plus-carry')
DESIGN_SHA='35990be277f4d7a64c5509355b066674e6f92c1287ad3c2cfaf8204f8434abb0'
ORIGINAL_EXPERIMENT='e7031f709506cb1c0631a716dc60b290cc22c9320a49a4c12daa9bdd5bffd001'


def sha256(path):return hash_files({'file':Path(path)})['file']


def store_identical(path,value):
    assert_public_report(value);path=Path(path)
    if path.exists():
        if json.loads(path.read_text())!=value:raise ValueError('Existing evidence differs; refusing rewrite: '+path.name)
        return
    path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_name(path.name+'.new')
    with temporary.open('x',encoding='utf-8') as handle:handle.write(json.dumps(value,indent=2,allow_nan=False)+'\n')
    temporary.replace(path)


def seal_reports(paths,destination):
    paths=list(paths)
    if len({p.name for p in paths})!=len(paths):raise ValueError('Duplicate receipt names')
    store_identical(destination,dict(report_sha256={p.name:sha256(p) for p in paths}))


def verify_report_seal(paths,seal):
    expected=json.loads(Path(seal).read_text())['report_sha256']
    portable_require_files(expected,{p.name:p for p in paths})
    return expected


def load_availability(feature_path,expected_sha,periods,cohort,regime):
    if cohort not in ('dfl','skillcorner') or regime not in ('natural','masked'):raise ValueError('Unknown availability case')
    if sha256(feature_path)!=expected_sha:raise ValueError('Availability feature source changed')
    with np.load(feature_path,allow_pickle=False) as archive:
        if not np.array_equal(archive['periods'],periods):raise ValueError('Availability/score period grids differ')
        ball=archive['ball_xy' if cohort=='dfl' else 'ball']
    if ball.shape!=(len(periods),2):raise ValueError('Invalid ball availability dimensions')
    observed=np.isfinite(ball).all(axis=1)
    if regime=='masked':observed &= ~contiguous_mask(periods,.3,1729)
    return observed


def dead_metrics(gt,pred,periods):
    gt=np.asarray(gt);pred=np.asarray(pred)
    if pred.shape!=gt.shape or pred.ndim!=1 or not np.isin(pred,[0,1,2,3]).all():raise ValueError('Invalid dead-metric prediction')
    mapped=original.engine.metric_periods(gt,periods)
    known=gt<3;live=gt<2;dead=gt==2;said_dead=known&(pred==2)
    tp=int((dead&(pred==2)).sum());fp=int((live&(pred==2)).sum());fn=int((dead&(pred!=2)).sum())
    n_live=int(live.sum());n_dead=int(dead.sum());n_said=int(said_dead.sum())
    a,b=original.engine.evaluation_arrays(gt,pred,mapped);official=original.engine.official
    runs=official.valid_runs(a);filled=official.fill_abstentions(b,runs)
    actual=[s for s in official.segments(a,runs) if s[2]==2]
    estimated=[s for s in official.segments(filled,runs) if s[2]==2]
    overlaps=official.spell_overlaps(actual,estimated);scores={};f1s=[]
    for threshold in official.SPELL_IOUS:
        matched,spurious,missed=official.match_spells(overlaps,len(actual),len(estimated),threshold)
        den=2*matched+spurious+missed;f1=2*matched/den if den else None
        scores[str(threshold)]=dict(n_matched=matched,n_spurious=spurious,n_missed=missed,
            precision=matched/(matched+spurious) if matched+spurious else None,
            recall=matched/(matched+missed) if matched+missed else None,f1=f1)
        f1s.append(f1)
    return dict(n_live=n_live,n_dead=n_dead,n_pred_D_on_known=n_said,true_D=tp,false_D=fp,missed_D=fn,
        false_D_fraction=fp/n_live if n_live else None,missed_D_fraction=fn/n_dead if n_dead else None,
        precision=tp/n_said if n_said else None,recall=tp/n_dead if n_dead else None,
        dead_interval=dict(n_gt=len(actual),n_pred=len(estimated),per_iou=scores,mean_f1=None if any(v is None for v in f1s) else float(np.mean(f1s))))


def case_keys(stage):
    if stage not in SPLITS:raise ValueError('Unknown stage')
    return {(c,str(m),r) for c,ids in SPLITS[stage].items() for m in ids for r in ('natural','masked')}


def _mean(rows,variant,section,field):
    values=[r['variants'][variant][section][field] for r in rows]
    if not values or any(v is None for v in values):return None
    if any(not isinstance(v,(int,float)) or not np.isfinite(v) for v in values):raise ValueError('Invalid metric mean')
    return float(np.mean(values))


def assess(reports,stage):
    keys=[(r['cohort'],str(r['match']),r['regime']) for r in reports]
    if len(keys)!=len(set(keys)) or set(keys)!=case_keys(stage) or any(r['stage']!=stage for r in reports):raise ValueError('Incomplete or duplicate stage membership')
    def provider(regime,cohort,variant,section,field):
        return _mean([r for r in reports if r['regime']==regime and r['cohort']==cohort],variant,section,field)
    def balanced(regime,variant,field):
        values=[provider(regime,c,variant,'metrics',field) for c in SPLITS[stage]]
        return None if any(v is None for v in values) else float(np.mean(values))
    def compare(new,old,strict=False,less=False):
        if new is None or old is None:return False
        return bool(new<old if less else new>old if strict else new>=old)
    checks={}
    for metric in ('spell_f1_mean','accuracy'):
        checks['natural_'+metric+'_preserved']=compare(balanced('natural',POLICY_ID,metric),balanced('natural',BASELINE,metric))
    checks['masked_skillcorner_accuracy_improved']=compare(provider('masked','skillcorner',POLICY_ID,'metrics','accuracy'),provider('masked','skillcorner',BASELINE,'metrics','accuracy'),strict=True)
    checks['masked_skillcorner_false_D_reduced']=compare(provider('masked','skillcorner',POLICY_ID,'dead_metrics','false_D_fraction'),provider('masked','skillcorner',BASELINE,'dead_metrics','false_D_fraction'),less=True)
    checks['masked_spell_f1_mean_preserved']=compare(balanced('masked',POLICY_ID,'spell_f1_mean'),balanced('masked',BASELINE,'spell_f1_mean'))
    for regime in ('natural','masked'):
        checks[regime+'_dfl_D_recall_preserved']=compare(provider(regime,'dfl',POLICY_ID,'dead_metrics','recall'),provider(regime,'dfl',BASELINE,'dead_metrics','recall'))
    return dict(stage=stage,checks=checks,eligible=all(checks.values()),fresh_holdout=False,target_accuracy_measured=False)


def protocol():
    return dict(policy_id=POLICY_ID,baseline=BASELINE,motion_weight=0.,switch_cost=32.,floor=1e-6,
        missing_emission='equal H/A/D log scores, zero triple',unsupported_segment='latent X then separate unchanged carry',
        splits=SPLITS,mask=dict(rate=.3,seed=1729,definition='unchanged contiguous_mask'),
        acceptance='all seven assess checks, separately validation and regression; no tolerances or reselection',
        fresh_holdout=False,head_fitting_performed=False,target_data_used=False)


def source_paths():return {n:ROOT/n for n in ('ball_gap_policy.py','ball_gap_experiment.py')}


def archive_paths():
    return {p.name:p for stage in SPLITS for c,ids in SPLITS[stage].items() for m in ids for r in ('natural','masked') for p in original.engine.case_paths(c,m,r)}


def verify_old():
    original.source_check();core=original.GUARD.core();selected=original.GUARD.verified_selection(core)
    original.GUARD.verified_summary_inputs(core)
    if digest(core)!=ORIGINAL_EXPERIMENT or (selected['selected_id'],selected['weight'],selected['switch_cost'])!=(BASELINE,0.,32.):raise ValueError('Wrong original experimental baseline')
    return core,selected


def freeze():
    core,selected=verify_old()
    design=ROOT/'docs/superpowers/specs/2026-11-07-ball-gap-evidence-design.md'
    if sha256(design)!=DESIGN_SHA:raise ValueError('Approved design changed')
    value=dict(schema_version=1,base_commit='b43327c101a8e33cadd5cf4f8a892910bad24c42',protocol=protocol(),
        approved_design_sha256=DESIGN_SHA,original_experiment_sha256=digest(core),original_selection_sha256=digest(selected),
        source_sha256=hash_files(source_paths()),original_archive_sha256=hash_files(archive_paths()),
        input_sha256=core['input_sha256'],original_verification_sha256=sha256(original.engine.REPORTS/'verification-source.json'))
    store_identical(REPORTS/'comparison-freeze.json',value)
    print('Frozen one candidate: '+digest(value),flush=True)


def load_freeze():
    value=json.loads((REPORTS/'comparison-freeze.json').read_text());original.source_check();core=original.GUARD.core()
    portable_require_files(value['source_sha256'],source_paths());portable_require_files(value['original_archive_sha256'],archive_paths())
    if value['protocol']!=protocol() or value['approved_design_sha256']!=DESIGN_SHA or value['original_experiment_sha256']!=digest(core) or value['input_sha256']!=core['input_sha256'] or value['original_verification_sha256']!=sha256(original.engine.REPORTS/'verification-source.json'):
        raise ValueError('Frozen protocol or original evidence identity changed')
    if value['original_selection_sha256']!=digest(json.loads((original.engine.REPORTS/'selection.json').read_text())):raise ValueError('Original selection changed')
    return value,core


def output_path(stage,cohort,match,regime):return REPORTS/stage/f'{cohort}-{match}-{regime}.json'


def stage_paths(stage):return sorted(output_path(stage,c,m,r) for c,m,r in case_keys(stage))


def expected_identity(frozen,stage,cohort,match,regime):
    value=dict(experiment_sha256=digest(frozen),stage=stage,cohort=cohort,match=str(match),regime=regime)
    if stage=='regression':value['validation_disposition_sha256']=sha256(REPORTS/'validation-disposition.json')
    return value


def sealed_stage(stage,frozen):
    paths=stage_paths(stage);verify_report_seal(paths,REPORTS/(stage+'-seal.json'));rows=[]
    for p in paths:
        r=json.loads(p.read_text());assert_public_report(r)
        if r['identity']!=expected_identity(frozen,stage,r['cohort'],r['match'],r['regime']) or set(r['variants'])!=set(VARIANTS):raise ValueError('Scored receipt binding or variants changed')
        rows.append(r)
    assess(rows,stage)
    return rows


def disposition_value(frozen):
    rows=sealed_stage('validation',frozen)
    return dict(experiment_sha256=digest(frozen),assessment=assess(rows,'validation'),validation_seal_sha256=sha256(REPORTS/'validation-seal.json'))


def verified_disposition(frozen):
    value=disposition_value(frozen)
    if json.loads((REPORTS/'validation-disposition.json').read_text())!=value:raise ValueError('Validation disposition changed')
    return value


def score_one(stage,cohort,match):
    frozen,core=load_freeze()
    if stage=='regression':verified_disposition(frozen)
    for regime in ('natural','masked'):
        arrays,record=RAW_LOAD_CASE(cohort,match,regime,core);gt,periods=original.engine.reference(cohort,match)
        if not np.array_equal(periods,arrays['periods']):raise ValueError('Reference/score grids differ')
        paths=original.engine.input_paths(cohort,match);logical,feature=next((k,p) for k,p in paths.items() if str(p).endswith('.features.npz'))
        observed=load_availability(feature,canonical_map(core['input_sha256'][f'{cohort}-{match}'])[canonical_key(logical)],periods,cohort,regime)
        usable=arrays['usable'].tolist();latent,counts=decode_ball_gap(arrays['supports'],periods,usable,observed.tolist())
        candidate=original.engine.encode(materialize_abstentions(latent,periods))
        old_latent=decode_soft(soft_emissions(arrays['supports'],arrays['motion_scores'],0.),periods,usable,32.)
        baseline=original.engine.encode(materialize_abstentions(old_latent,periods))
        old=json.loads((original.engine.REPORTS/stage/f'{cohort}-{match}-{regime}.json').read_text())
        variants={}
        for name,pred in ((BASELINE,baseline),(POLICY_ID,candidate),('agreement-plus-carry',arrays['agreement-plus-carry'])):
            metrics=original.aggregate_metrics(gt,pred,periods,arrays['incumbent'])
            if name!=POLICY_ID and metrics!=old['variants'][name]:raise ValueError('Original comparator failed exact replay')
            strata={}
            for scope,mask in (('ball_available',observed),('ball_missing',~observed)):
                cm=np.zeros((4,4),dtype=np.int64);scored=(gt<3)&mask&(periods>0)
                np.add.at(cm,(gt[scored],pred[scored]),1)
                strata[scope]=dict(known_frames=int(scored.sum()),confusion=cm.tolist())
            variants[name]=dict(**metrics,dead_metrics=dead_metrics(gt,pred,periods),boundary_metrics=boundary_summary(gt,pred,periods),input_strata=strata)
        counts.update(latent_unknown_active=int(sum(p>0 and v=='X' for p,v in zip(periods,latent))),
            materialized_active=int(sum(p>0 and 'HADX'[v]!=l for p,v,l in zip(periods,candidate,latent))))
        value=dict(schema_version=1,identity=expected_identity(frozen,stage,cohort,match,regime),stage=stage,cohort=cohort,match=match,regime=regime,
            fresh_holdout=False,target_data_used=False,head_fitting_performed=False,variants=variants,policy_diagnostics=counts,
            score_archive_sha256=record['archive_sha256']['scores'],feature_sha256=sha256(feature))
        store_identical(output_path(stage,cohort,match,regime),value)
    return f'{stage} {cohort}-{match}: natural and masked complete'


def score_stage(stage,workers):
    frozen,_=load_freeze();verify_old()
    if stage=='regression':verified_disposition(frozen)
    seal=REPORTS/(stage+'-seal.json')
    if seal.exists():sealed_stage(stage,frozen);print(stage+' sealed receipts verified',flush=True);return
    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures=[pool.submit(score_one,stage,c,m) for c,ids in SPLITS[stage].items() for m in ids]
        for future in as_completed(futures):print(future.result(),flush=True)
    paths=stage_paths(stage);actual=set((REPORTS/stage).glob('*.json'))
    if actual!=set(paths):raise ValueError('Unexpected scored receipts')
    seal_reports(paths,seal);sealed_stage(stage,frozen)


def summary_value(frozen):
    validation=verified_disposition(frozen);regression=sealed_stage('regression',frozen);groups={}
    for stage,rows in (('validation',sealed_stage('validation',frozen)),('regression',regression)):
        groups[stage]={}
        for regime in ('natural','masked'):
            groups[stage][regime]={}
            for cohort in ('dfl','skillcorner'):
                cases=[r for r in rows if r['regime']==regime and r['cohort']==cohort];variants={}
                for name in VARIANTS:
                    scalar={m:_mean(cases,name,'metrics',m) for m in ('accuracy','spell_f1_mean','macro_f1')}
                    scalar.update({m:_mean(cases,name,'dead_metrics',m) for m in ('false_D_fraction','recall','precision')})
                    scalar['pooled_counts']={m:sum(r['variants'][name]['dead_metrics'][m] for r in cases) for m in ('n_live','n_dead','true_D','false_D','missed_D')}
                    scalar['dead_interval_f1_mean']=None if cohort=='skillcorner' else float(np.mean([r['variants'][name]['dead_metrics']['dead_interval']['mean_f1'] for r in cases]))
                    variants[name]=scalar
                groups[stage][regime][cohort]=variants
    assessment=assess(regression,'regression');eligible=validation['assessment']['eligible'] and assessment['eligible']
    return dict(schema_version=1,experiment_sha256=digest(frozen),validation_disposition_sha256=sha256(REPORTS/'validation-disposition.json'),
        regression_seal_sha256=sha256(REPORTS/'regression-seal.json'),validation=validation['assessment'],regression=assessment,
        eligible=eligible,disposition='experimental_opt_in_eligible' if eligible else 'rejected_keep_w0-c32',
        provider_means=groups,fresh_holdout=False,target_accuracy_measured=False,parameter_reselection_performed=False)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('stage',choices=['freeze','validate','decide','regress','summarize','verify']);p.add_argument('--workers',type=int,default=2);args=p.parse_args()
    if args.workers<1 or args.workers>2:p.error('Use one or two workers')
    if args.stage=='freeze':freeze();return
    frozen,_=load_freeze()
    if args.stage in ('validate','regress'):score_stage('validation' if args.stage=='validate' else 'regression',args.workers)
    elif args.stage=='decide':
        value=disposition_value(frozen);store_identical(REPORTS/'validation-disposition.json',value);print(json.dumps(value['assessment'],indent=2))
    elif args.stage=='summarize':
        value=summary_value(frozen);store_identical(REPORTS/'summary.json',value);print(json.dumps({k:value[k] for k in ('disposition','validation','regression')},indent=2))
    else:
        verify_old();value=summary_value(frozen)
        if json.loads((REPORTS/'summary.json').read_text())!=value:raise ValueError('Summary differs from sealed evidence')
        print('Original evidence, new source/input/archive bindings, stage receipts, dispositions and summary verified')

if __name__=='__main__':main()
