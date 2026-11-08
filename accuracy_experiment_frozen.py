"""Frozen, external-only soft H/A/D experiment. Per-frame caches stay local."""
import argparse,json
from concurrent.futures import ProcessPoolExecutor,as_completed
from pathlib import Path
import numpy as np

from gap_solver.accuracy_protocol import PARAMETERS,SPLITS,CONTROLS,digest,hash_files,require_files,assert_aggregate,select_validation
from gap_solver.anonymous_motion import associate_anonymous
from gap_solver.core import Decision
from gap_solver.candidate_cli import ROOT
from gap_solver.tactical import Policy,infer_tactical,PortableTree,feature_rows
from gap_solver.tactical_model import FROZEN_MODEL
from gap_solver.temporal import motion_feature_rows,decode_team_sequence,mask_motion_frames
from gap_solver.temporal_development import symmetric_scores
from gap_solver.temporal_selection import contiguous_mask
from gap_solver.temporal_protocol import load_temporal_frozen
from gap_solver.soft_sequence import soft_emissions,decode_soft,sequence_usable
from gap_solver.confidence_ensemble import aggregate_decisions
from gap_solver.materialization_control import materialize_abstentions
from gap_solver.skillcorner import load_motion_cache
from gap_solver.external import load_cache
from gap_solver.dfl_motion import load_dfl_motion
from gap_solver.temporal_metrics import metric_periods
from gap_solver.benchmark import evaluate_external,evaluation_arrays,compare_external
from gap_solver import official_metrics as official

WORK=ROOT.parent/'accuracy-reference'
REPORTS=ROOT/'reports/accuracy-first'


def encode(values):return np.fromiter(('HADX'.index(x) for x in values),dtype=np.uint8,count=len(values))


def score_heads(frames,artifact):
    if any(f.dead_evidence or f.tag_team or f.restart_hint for f in frames):raise ValueError('Geometry-only head inputs required')
    x=np.asarray(list(feature_rows(frames)),dtype=np.float32);model=FROZEN_MODEL['model'];PortableTree(model)
    nodes=np.zeros(len(x),dtype=np.int32);left=np.asarray(model['children_left']);right=np.asarray(model['children_right'])
    feature=np.asarray(model['feature']);threshold=np.asarray(model['threshold'])
    while True:
        active=np.flatnonzero(left[nodes]!=-1)
        if not len(active):break
        at=nodes[active];nodes[active]=np.where(x[active,feature[at]]<=threshold[at],left[at],right[at])
    supports=np.asarray(model['probabilities'],dtype=np.float64)[nodes]
    motion=np.asarray(list(motion_feature_rows(frames)),dtype=np.float32)
    return supports,symmetric_scores(artifact['model'],motion)


def four_from_scores(frames,supports,scores,artifact):
    baseline=infer_tactical(frames,FROZEN_MODEL['model'],Policy(**FROZEN_MODEL['policy']))
    masked=[float(z) if d.label=='X' and f.period and f.geometry_valid else 0. for f,d,z in zip(frames,baseline,scores)]
    posterior=decode_team_sequence(masked,frames,baseline,artifact['transition_cost']*artifact['policy']['switch_multiplier'])
    temporal=[Decision('A' if z>0 else 'H') if f.period and f.geometry_valid and b.label=='X' else b for f,b,z in zip(frames,baseline,posterior)]
    raw=[Decision('HAD'[int(np.argmax(p))]) if f.period else Decision() for f,p in zip(frames,supports)]
    agreement=aggregate_decisions(frames,baseline,temporal,raw,temporal)['head_agreement_on_X']
    baseline=[d.label for d in baseline];agreement=[d.label for d in agreement];periods=[f.period for f in frames]
    return dict(incumbent=baseline,carry=materialize_abstentions(baseline,periods),agreement=agreement,
        **{'agreement-plus-carry':materialize_abstentions(agreement,periods)})


def aggregate_metrics(reference,prediction,periods,incumbent):
    gt=np.asarray(reference);pred=np.asarray(prediction);base=np.asarray(incumbent)
    mapped=metric_periods(gt,periods);report=evaluate_external(gt,pred,mapped);m=report['metrics']
    names=('spell_f1_mean','macro_f1','accuracy','kappa','alive_dead_f1','n_gt_spells','n_pred_spells','spell_count_error','mean_spell_duration_s','gt_mean_spell_duration_s')
    values={k:m[k] for k in names if k in m}
    values['confusion']=np.asarray(m['confusion']).tolist()
    a,b=evaluation_arrays(gt,pred,mapped);runs=official.valid_runs(a);filled=official.fill_abstentions(b,runs)
    actual=official.possession_spells(a,runs);estimated=official.possession_spells(filled,runs)
    def overlaps(one,others):
        first,stop,label=one
        return sum(label==other[2] and min(stop,other[1])>max(first,other[0]) for other in others)
    result=dict(metrics=values,coverage=report['coverage'],spell_counts=m['spell_f1'],
        overlap_diagnostics=dict(reference_spells_split=int(sum(overlaps(s,estimated)>1 for s in actual)),predicted_spells_merging=int(sum(overlaps(s,actual)>1 for s in estimated))),
        changes=compare_external(gt,base,pred,mapped),
        unmeasured_emitted_by_label={label:int(((gt==3)&(pred==i)&(np.asarray(periods)>0)).sum()) for i,label in enumerate('HAD')})
    assert_aggregate(result);return result


def write_report(path,value):
    assert_aggregate(value);path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_name(path.name+'.new');temporary.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n',encoding='utf-8');temporary.replace(path)


def source_paths():
    paths={p.relative_to(ROOT).as_posix():p for p in (ROOT/'gap_solver').glob('*.py')}
    paths['accuracy_experiment.py']=Path(__file__)
    return paths


def input_paths(cohort,match):
    prefix=ROOT.parent/('external-reference/cache/'+str(match) if cohort=='dfl' else 'independent-reference/cache/'+str(match)+'-detected')
    paths={str(prefix.relative_to(ROOT.parent))+suffix:Path(str(prefix)+suffix) for suffix in ('.metadata.json','.features.npz','.reference.npz')}
    if cohort=='dfl':
        paths.update({p.relative_to(ROOT.parent).as_posix():p for p in (ROOT.parent/'external-reference/raw').glob('*'+str(match)+'*.xml') if 'matchinformation' in p.name or 'positions' in p.name})
    return paths


def freeze():
    path=REPORTS/'comparison-freeze.json'
    if path.exists():load_freeze();return
    artifact,manifest=load_temporal_frozen(ROOT/'benchmark/skillcorner/frozen',ROOT)
    inputs={}
    for cohorts in SPLITS.values():
        for cohort,ids in cohorts.items():
            for match in ids:inputs[f'{cohort}-{match}']=hash_files(input_paths(cohort,match))
    value=dict(schema_version=1,base_commit='9bd11dc847f71973782ea268045609f6a8c6bffd',split=SPLITS,
        settings=[dict(id=name,weight=w,switch_cost=c) for name,w,c in PARAMETERS],mask=dict(rate=.3,seed=1729,definition='frozen contiguous_mask'),
        source_sha256=hash_files(source_paths()),input_sha256=inputs,temporal_artifact_sha256=manifest['artifact_sha256'],
        tactical_artifact_sha256=FROZEN_MODEL['artifact_sha256'],fresh_holdout=False,head_fitting_performed=False,
        selection='natural only; equal providers then matches; spellF1, macroF1, lower weight, lower switch cost')
    write_report(path,value);print('Frozen16 settings and13 seen external matches: '+digest(value),flush=True)


def load_freeze():
    value=json.loads((REPORTS/'comparison-freeze.json').read_text());require_files(value['source_sha256'],source_paths())
    if value['split']!=SPLITS or value['settings']!=[dict(id=n,weight=w,switch_cost=c) for n,w,c in PARAMETERS]:raise ValueError('Frozen protocol changed')
    return value


def case_paths(cohort,match,regime):
    prefix=WORK/'cases'/f'{cohort}-{match}-{regime}'
    return prefix.with_suffix('.npz'),prefix.with_suffix('.json')


def identity(frozen,cohort,match,regime):return dict(experiment_sha256=digest(frozen),cohort=cohort,match=match,regime=regime)


def load_case(cohort,match,regime,frozen):
    path,metadata=case_paths(cohort,match,regime);record=json.loads(metadata.read_text())
    if record['identity']!=identity(frozen,cohort,match,regime):raise ValueError('Stale score cache identity')
    require_files(record['archive_sha256'],{'scores':path})
    require_files(frozen['input_sha256'][f'{cohort}-{match}'],input_paths(cohort,match))
    with np.load(path,allow_pickle=False) as archive:arrays={k:archive[k] for k in archive.files}
    return arrays,record


def prepare_one(cohort,match):
    frozen=load_freeze();require_files(frozen['input_sha256'][f'{cohort}-{match}'],input_paths(cohort,match))
    if all(case_paths(cohort,match,r)[1].exists() for r in ('natural','masked')):
        for regime in ('natural','masked'):load_case(cohort,match,regime,frozen)
        return f'{cohort}-{match}: verified existing score caches'
    artifact,_=load_temporal_frozen(ROOT/'benchmark/skillcorner/frozen',ROOT)
    if cohort=='skillcorner':data=load_motion_cache(ROOT.parent/'independent-reference/cache'/f'{match}-detected');frames=data.frames()
    else:
        data=load_cache(ROOT.parent/'external-reference/cache'/str(match));paths=list(input_paths(cohort,match).values())
        frames=load_dfl_motion(next(p for p in paths if 'matchinformation' in p.name),next(p for p in paths if 'positions' in p.name),data)
    frames,association=associate_anonymous(frames);periods=np.asarray([f.period for f in frames],dtype=np.uint8)
    mask=contiguous_mask(periods,.3,1729)
    for regime,records in [('natural',frames),('masked',mask_motion_frames(frames,mask))]:
        supports,scores=score_heads(records,artifact);controls=four_from_scores(records,supports,scores,artifact)
        path,metadata=case_paths(cohort,match,regime);path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('wb') as handle:np.savez_compressed(handle,supports=supports,motion_scores=scores,periods=periods,
            usable=np.asarray([sequence_usable(f) for f in records],dtype=bool),**{k:encode(v) for k,v in controls.items()})
        write_report(metadata,dict(identity=identity(frozen,cohort,match,regime),archive_sha256=hash_files({'scores':path}),association=association,rows=len(periods)))
    return f'{cohort}-{match}: prepared both input-only regimes'


def reference(cohort,match):
    prefix=ROOT.parent/('external-reference/cache/'+str(match) if cohort=='dfl' else 'independent-reference/cache/'+str(match)+'-detected')
    with np.load(str(prefix)+'.reference.npz',allow_pickle=False) as archive:return archive['reference'].copy(),archive['periods'].copy()


def score_one(stage,cohort,match):
    frozen=load_freeze();settings=PARAMETERS
    selected=None
    if stage=='regression':
        selected=json.loads((REPORTS/'selection.json').read_text())
        if selected['experiment_sha256']!=digest(frozen):raise ValueError('Selected artifact source changed')
        settings=[(selected['selected_id'],selected['weight'],selected['switch_cost'])]
    for regime in ('natural','masked'):
        destination=REPORTS/stage/f'{cohort}-{match}-{regime}.json';arrays,record=load_case(cohort,match,regime,frozen)
        expected=identity(frozen,cohort,match,regime)|dict(stage=stage,score_archive_sha256=record['archive_sha256']['scores'],settings=[name for name,_,_ in settings])
        if selected is not None:expected['selection_sha256']=digest(selected)
        if destination.exists():
            if json.loads(destination.read_text())['identity']!=expected:raise ValueError('Stale scored receipt')
            continue
        gt,periods=reference(cohort,match)
        if not np.array_equal(periods,arrays['periods']):raise ValueError('Score/reference grids differ')
        variants={name:aggregate_metrics(gt,arrays[name],periods,arrays['incumbent']) for name in CONTROLS}
        latent={}
        for name,w,c in settings:
            labels=decode_soft(soft_emissions(arrays['supports'],arrays['motion_scores'],w),periods,arrays['usable'],c)
            latent[name]=dict(unknown_active=int(sum(p>0 and label=='X' for p,label in zip(periods,labels))))
            carried=materialize_abstentions(labels,periods);variants[name]=aggregate_metrics(gt,encode(carried),periods,arrays['incumbent'])
        write_report(destination,dict(schema_version=1,identity=expected,stage=stage,cohort=cohort,match=match,regime=regime,
            fresh_holdout=False,head_fitting_performed=False,target_data_used=False,variants=variants,latent_diagnostics=latent))
    return f'{stage} {cohort}-{match}: both regimes complete'


def receipts(stage):
    expected={(cohort,str(match),regime) for cohort,ids in SPLITS[stage].items() for match in ids for regime in ('natural','masked')}
    rows=[json.loads(p.read_text()) for p in (REPORTS/stage).glob('*.json')]
    keys=[(r['cohort'],str(r['match']),r['regime']) for r in rows]
    if len(keys)!=len(set(keys)) or set(keys)!=expected:raise ValueError('Incomplete/duplicate external receipts')
    return rows


def select():
    frozen=load_freeze();rows=receipts('validation')
    if any(r['identity']['experiment_sha256']!=digest(frozen) for r in rows):raise ValueError('Validation receipt source changed')
    result=select_validation([r for r in rows if r['regime']=='natural'])
    result.update(experiment_sha256=digest(frozen),fresh_holdout=False,validation_receipt_sha256=hash_files({p.name:p for p in (REPORTS/'validation').glob('*.json')}))
    path=REPORTS/'selection.json'
    if path.exists() and json.loads(path.read_text())!=result:raise ValueError('Preserve frozen selection')
    write_report(path,result);print(json.dumps({k:result[k] for k in ('selected_id','score','baseline_score','validation_improved')},indent=2),flush=True)


def summarize():
    frozen=load_freeze();selected=json.loads((REPORTS/'selection.json').read_text());rows=receipts('regression');name=selected['selected_id']
    require_files(selected['validation_receipt_sha256'],{p.name:p for p in (REPORTS/'validation').glob('*.json')})
    summaries={}
    for regime in ('natural','masked'):
        groups={}
        for cohort in SPLITS['regression']:
            cases=[r for r in rows if r['cohort']==cohort and r['regime']==regime]
            if any(r['identity'].get('selection_sha256')!=digest(selected) or r['identity']['experiment_sha256']!=digest(frozen) for r in cases):raise ValueError('Regression source/selection changed')
            values={}
            for variant in (*CONTROLS,name):
                metrics={m:float(np.mean([r['variants'][variant]['metrics'][m] for r in cases])) for m in ('spell_f1_mean','macro_f1','accuracy')}
                metrics['corrections']=sum(r['variants'][variant]['changes']['already_decided_corrections'] for r in cases)
                metrics['regressions']=sum(r['variants'][variant]['changes']['already_decided_regressions'] for r in cases)
                values[variant]=metrics
            groups[cohort]=values
        primary={variant:float(np.mean([v[variant]['spell_f1_mean'] for v in groups.values()])) for variant in (*CONTROLS,name)}
        summaries[regime]=dict(cohorts=groups,provider_balanced_spell_f1=primary,primary_change=primary[name]-primary['agreement-plus-carry'])
    improved=selected['validation_improved'] and summaries['natural']['primary_change']>0
    result=dict(schema_version=1,selected_id=name,experimental=True,fresh_holdout=False,target_accuracy_measured=False,
        validation_improved=selected['validation_improved'],seen_regression_improved=summaries['natural']['primary_change']>0,
        disposition='experimental_opt_in_eligible' if improved else 'rejected_keep_existing_candidate',regimes=summaries,
        experiment_sha256=digest(frozen),selection_sha256=digest(selected),regression_receipt_sha256=hash_files({p.name:p for p in (REPORTS/'regression').glob('*.json')}))
    write_report(REPORTS/'summary.json',result);print(json.dumps(result,indent=2),flush=True)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('stage',choices=['freeze','prepare','validate','select','regress','summarize']);p.add_argument('--workers',type=int,default=2);a=p.parse_args()
    if a.stage=='freeze':freeze();return
    if a.stage=='select':select();return
    if a.stage=='summarize':summarize();return
    stages=('validation','regression') if a.stage=='prepare' else (('validation',) if a.stage=='validate' else ('regression',))
    jobs=[(stage,cohort,match) for stage in stages for cohort,ids in SPLITS[stage].items() for match in ids]
    with ProcessPoolExecutor(max_workers=a.workers) as pool:
        futures=[pool.submit(prepare_one,cohort,match) if a.stage=='prepare' else pool.submit(score_one,stage,cohort,match) for stage,cohort,match in jobs]
        for future in as_completed(futures):print(future.result(),flush=True)

if __name__=='__main__':main()
