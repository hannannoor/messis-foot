"""User-requested post-hoc combinations of gated and ungated external predictions."""
import argparse,json,shutil
from concurrent.futures import ProcessPoolExecutor,as_completed
from pathlib import Path
import numpy as np
from ablate_confidence import (CODE,ROOT,WORK,source_identity,raw_tree_decisions,temporal_variants)
from evaluate_temporal_final import frozen
from select_temporal_recovery import load_case,sha,write_json
from gap_solver.skillcorner import load_motion_cache
from gap_solver.external import load_cache
from gap_solver.dfl_motion import load_dfl_motion
from gap_solver.tactical import infer_tactical,Policy
from gap_solver.tactical_model import FROZEN_MODEL
from gap_solver.temporal import motion_feature_rows,decode_team_sequence
from gap_solver.temporal_development import codes,decisions,symmetric_scores
from gap_solver.temporal_metrics import compare_temporal
from gap_solver.temporal_protocol import require_evidence
from gap_solver.core import Frame
from gap_solver.confidence_ensemble import aggregate_decisions

DESTINATION=ROOT/'ensemble-ablation'
VARIANTS={'gated_plus_raw_HAD','head_agreement_on_X','supported_head_agreement_on_X'}


def outside_reference_counts(reference,periods,baseline,prediction):
    gt=np.asarray(reference);periods=np.asarray(periods);old=np.asarray(baseline);new=np.asarray(prediction)
    if gt.ndim!=1 or any(x.shape!=gt.shape for x in (periods,old,new)):raise ValueError('Outside-reference dimensions differ')
    if any(not np.isin(x,[0,1,2,3]).all() for x in (gt,old,new)) or not np.isin(periods,[0,1,2]).all():raise ValueError('Invalid outside-reference codes')
    outside=(gt==3)&(periods>0)&(old==3)
    return {label:int((outside&(new==code)).sum()) for code,label in enumerate('HAD')}


def identity(cohort,match,artifact_id):
    value=source_identity(cohort,match,artifact_id)
    value['source_sha256'].update(ensemble_driver=sha(Path(__file__)),ensemble_rules=sha(CODE/'gap_solver/confidence_ensemble.py'))
    return value


def check_receipt(report,expected,path):
    require_evidence(report,expected)
    if set(report.get('variants',{}))!=VARIANTS:raise ValueError('Incomplete ensemble comparison receipt')
    if any(set(v.get('unmeasured_new_outside_reference_by_label',{}))!=set('HAD') for v in report['variants'].values()):raise ValueError('Missing all-label outside-reference counts')
    if sha(path)!=report['prediction_sha256']:raise ValueError('Ensemble prediction cache changed')


def run_one(cohort,match):
    artifact,manifest=frozen();expected=identity(cohort,match,manifest['artifact_sha256'])
    destination=DESTINATION/f'{cohort}-{match}.json';prediction_path=DESTINATION/f'{cohort}-{match}.npz'
    if destination.exists():check_receipt(json.loads(destination.read_text()),expected,prediction_path);return f'{cohort} {match}: preserved ensemble comparison'
    if cohort=='skillcorner':
        data=load_motion_cache(ROOT/'cache'/f'{match}-detected');frames=data.frames();case=load_case(match,'natural')
        baseline=decisions(case['baseline']);x=case['x']
    else:
        root=CODE.parent/'external-reference';data=load_cache(root/'cache'/str(match));raw=list((root/'raw').glob('*'+str(match)+'*.xml'))
        frames=load_dfl_motion(next(p for p in raw if 'matchinformation' in p.name),next(p for p in raw if 'positions' in p.name),data)
        baseline=infer_tactical(frames,FROZEN_MODEL['model'],Policy(**FROZEN_MODEL['policy']))
        x=np.asarray(list(motion_feature_rows(frames)),dtype=np.float32)
    scores=symmetric_scores(artifact['model'],x);scores[codes(baseline)!=3]=0.
    posterior=decode_team_sequence(scores,frames,baseline,artifact['transition_cost']*artifact['policy']['switch_multiplier'])
    supported,direct=temporal_variants(frames,baseline,posterior,artifact['policy']);raw=raw_tree_decisions(frames)
    variants=aggregate_decisions(frames,baseline,direct,raw,supported)
    result=dict(schema_version=1,identity=expected,cohort=cohort,match=match,post_hoc=True,fresh_holdout=False,
        local_inference_performed=False,agreement_is_calibrated_confidence=False,variants={})
    for name,pred in variants.items():
        report=compare_temporal(data.reference,codes(baseline),codes(pred),data.periods,frames)
        report['unmeasured_new_outside_reference_by_label']=outside_reference_counts(data.reference,data.periods,codes(baseline),codes(pred))
        result['variants'][name]=report
    DESTINATION.mkdir(parents=True,exist_ok=True);temporary=Path(str(prediction_path)+'.new')
    with temporary.open('wb') as handle:np.savez_compressed(handle,baseline=codes(baseline),temporal=codes(direct),raw=codes(raw),supported=codes(supported),**{name:codes(pred) for name,pred in variants.items()})
    temporary.replace(prediction_path);result['prediction_sha256']=sha(prediction_path);write_json(destination,result)
    return cohort+' '+str(match)+': '+', '.join('{} X={:.1%},spell={:.4f}'.format(name,r['selected']['coverage']['undecided_fraction'],r['selected']['metrics']['spell_f1_mean']) for name,r in result['variants'].items())


def refresh_receipts(previous_driver_sha,previous_rules_sha):
    """Recompute missing counts from verified saved decisions; never fit or repredict.

    Re-execute the strengthened aggregation rule on every cached row and require
    exact equality with every saved output. Retain the original prediction-code
    identity rather than representing it as a new model run.
    """
    if any(not isinstance(v,str) or len(v)!=64 or any(c not in '0123456789abcdef' for c in v) for v in (previous_driver_sha,previous_rules_sha)):
        raise ValueError('Explicit previous source SHA256 values are required')
    _,manifest=frozen();pending=[]
    for path in sorted(DESTINATION.glob('*.json')):
        if path.name=='summary.json':continue
        report=json.loads(path.read_text());current=identity(report['cohort'],report['match'],manifest['artifact_sha256'])
        previous=json.loads(json.dumps(current));previous['source_sha256'].update(ensemble_driver=previous_driver_sha,ensemble_rules=previous_rules_sha)
        require_evidence(report,previous)
        if set(report.get('variants',{}))!=VARIANTS:raise ValueError('Cannot refresh incomplete comparisons')
        prediction_path=path.with_suffix('.npz')
        if sha(prediction_path)!=report['prediction_sha256']:raise ValueError('Original saved predictions changed')
        with np.load(prediction_path,allow_pickle=False) as archive:arrays={key:archive[key] for key in archive.files}
        prefix=(ROOT/'cache'/f'{report["match"]}-detected') if report['cohort']=='skillcorner' else CODE.parent/'external-reference/cache'/str(report['match'])
        with np.load(str(prefix)+'.reference.npz',allow_pickle=False) as archive:gt=archive['reference'];periods=archive['periods']
        frames=[Frame(period=int(p)) for p in periods]
        recomputed=aggregate_decisions(frames,decisions(arrays['baseline']),decisions(arrays['temporal']),decisions(arrays['raw']),decisions(arrays['supported']))
        for name,pred in recomputed.items():
            if not np.array_equal(codes(pred),arrays[name]):raise ValueError('Changed rule affects cached predictions; full rerun required')
            report['variants'][name]['unmeasured_new_outside_reference_by_label']=outside_reference_counts(gt,periods,arrays['baseline'],arrays[name])
        report.update(prediction_origin_identity=report['identity'],identity=current,
            receipt_refresh=dict(previous_receipt_sha256=sha(path),all_cached_predictions_recomputed_equal=True,model_rep_run=False))
        pending.append((path,report))
    backup=DESTINATION.parent/(DESTINATION.name+'-pre-review')
    if backup.exists():raise ValueError('Review archive already exists; preserve it and inspect before retry')
    backup.mkdir()
    for path,report in pending:shutil.copyfile(path,backup/path.name)
    for path,report in pending:write_json(path,report)
    print(f'Refreshed{len(pending)} receipts from exact verified cached decisions; no model rerun or metric change.',flush=True)


def summarize():
    _,manifest=frozen();expected={'skillcorner':set(manifest['split']['test']),'dfl':set(sum(json.loads((CODE.parent/'external-reference/provenance.json').read_text())['split'].values(),[]))}
    reports=[json.loads(p.read_text()) for p in DESTINATION.glob('*.json') if p.name!='summary.json']
    if len(reports)!=sum(map(len,expected.values())):raise ValueError('Missing/extra ensemble match receipts')
    for cohort,ids in expected.items():
        if {r['match'] for r in reports if r['cohort']==cohort}!=ids:raise ValueError('Ensemble cohort membership differs')
    for r in reports:check_receipt(r,identity(r['cohort'],r['match'],manifest['artifact_sha256']),DESTINATION/f'{r["cohort"]}-{r["match"]}.npz')
    result=dict(schema_version=1,post_hoc=True,fresh_holdout=False,artifact_sha256=manifest['artifact_sha256'],local_inference_performed=False,cohorts={})
    for cohort in expected:
        matches=[r for r in reports if r['cohort']==cohort];values={}
        for name in matches[0]['variants']:
            rs=[r['variants'][name] for r in matches];labels={}
            for label in 'HAD':
                n=sum(r['change']['newly_resolved_by_label'][label]['frames'] for r in rs)
                correct=sum(r['change']['newly_resolved_by_label'][label]['frames']*(r['change']['newly_resolved_by_label'][label]['correct_fraction'] or 0) for r in rs)
                labels[label]=dict(frames=n,correct_fraction=correct/n if n else None)
            outside={label:sum(r['unmeasured_new_outside_reference_by_label'][label] for r in rs) for label in 'HAD'}
            values[name]=dict(matches=len(rs),mean_unknown_fraction=float(np.mean([r['selected']['coverage']['undecided_fraction'] for r in rs])),
                mean_frame_accuracy=float(np.mean([r['selected']['metrics']['accuracy'] for r in rs])),
                mean_spell_f1=float(np.mean([r['selected']['metrics']['spell_f1_mean'] for r in rs])),
                mean_spell_change=float(np.mean([r['selected']['metrics']['spell_f1_mean']-r['baseline']['metrics']['spell_f1_mean'] for r in rs])),
                new_by_label=labels,unmeasured_new_outside_reference=sum(outside.values()),unmeasured_new_outside_reference_by_label=outside,
                already_decided_changes=sum(r['change']['changed_already_decided_frames'] for r in rs))
        result['cohorts'][cohort]=values
    write_json(DESTINATION/'summary.json',result);print(json.dumps(result,indent=2),flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('stage',choices=['run','summarize','refresh']);parser.add_argument('--workers',type=int,default=2)
    parser.add_argument('--previous-driver-sha');parser.add_argument('--previous-rules-sha');args=parser.parse_args()
    if args.stage=='summarize':summarize();return
    if args.stage=='refresh':refresh_receipts(args.previous_driver_sha,args.previous_rules_sha);return
    _,manifest=frozen();dfl=sum(json.loads((CODE.parent/'external-reference/provenance.json').read_text())['split'].values(),[])
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        futures=[pool.submit(run_one,cohort,m) for cohort,matches in [('skillcorner',manifest['split']['test']),('dfl',dfl)] for m in matches]
        for future in as_completed(futures):print(future.result(),flush=True)


if __name__=='__main__':main()
