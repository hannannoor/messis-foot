"""Post-hoc diagnostic requested by user; opened external cohorts are NOT fresh holdouts."""
import argparse,json
from concurrent.futures import ProcessPoolExecutor,as_completed
from pathlib import Path
import numpy as np
from gap_solver.core import Decision
from gap_solver.temporal import TemporalPolicy,apply_temporal_policy,motion_feature_rows
from gap_solver.temporal_development import codes,decisions
from gap_solver.temporal_metrics import compare_temporal
from gap_solver.tactical import PortableTree,feature_rows,infer_tactical,Policy
from gap_solver.tactical_model import FROZEN_MODEL
from gap_solver.skillcorner import load_motion_cache
from gap_solver.external import load_cache
from gap_solver.dfl_motion import load_dfl_motion
from gap_solver.temporal_protocol import evidence_identity,require_evidence
from select_temporal_recovery import CODE,ROOT,WORK,load_case,write_json,sha
from evaluate_temporal_final import frozen,predict,regression_identity

DESTINATION=ROOT/'confidence-ablation'


def temporal_variants(frames,baseline,posterior,policy):
    if len(frames)!=len(posterior) or len(frames)!=len(baseline) or not np.isfinite(posterior).all():raise ValueError('Invalid ablation dimensions/scores')
    # Saturating only the posterior sign bypasses confidence in the unchanged
    # policy function while preserving its support/anchor/quality/gap guards.
    signs=[50. if z>0 else -50. for z in posterior]
    off=apply_temporal_policy(frames,baseline,signs,TemporalPolicy(**policy))
    direct=[Decision('A' if z>0 else 'H','diagnostic_argmax','unsupported_estimate') if b.label=='X' and f.period else b
            for f,b,z in zip(frames,baseline,posterior)]
    return off,direct


def raw_tree_decisions(frames,model=None):
    tree=PortableTree(FROZEN_MODEL['model'] if model is None else model)
    result=[]
    for frame,row in zip(frames,feature_rows(frames)):
        probabilities=tree.predict(row)
        result.append(Decision('HAD'[max(range(3),key=lambda i:probabilities[i])],'diagnostic_raw_tree','unsupported_estimate') if frame.period else Decision('X'))
    return result


def source_identity(cohort,match,artifact_id):
    names=('temporal.py','temporal_development.py','temporal_metrics.py','tactical.py','tactical_model.py','core.py',
        'benchmark.py','official_metrics.py','motion.py','skillcorner.py','external.py','dfl_motion.py')
    sources={name:CODE/'gap_solver'/name for name in names};sources['ablate_confidence.py']=Path(__file__)
    inputs={'frozen_artifact':WORK/'frozen/temporal-selected.json'}
    if cohort=='skillcorner':
        for suffix in ('.metadata.json','.features.npz','.reference.npz'):
            inputs['source_cache'+suffix]=ROOT/'cache'/(str(match)+'-detected'+suffix)
        inputs['case_metadata']=WORK/'cases'/f'{match}-detected.json'
        inputs['natural_feature_case']=WORK/'cases'/f'{match}-detected-natural.npz'
    else:
        dfl=CODE.parent/'external-reference'
        inputs.update({str(p.relative_to(dfl)):p for p in (dfl/'raw').glob('*'+str(match)+'*.xml') if 'positions' in p.name or 'matchinformation' in p.name})
        inputs.update({f'cache/{match}'+suffix:dfl/'cache'/(str(match)+suffix) for suffix in ('.features.npz','.reference.npz','.metadata.json')})
    result=evidence_identity(sources,inputs,artifact_id);result.update(cohort=cohort,match=match);return result


def run_one(cohort,match):
    from gap_solver.temporal_development import symmetric_scores
    from gap_solver.temporal import decode_team_sequence
    artifact,manifest=frozen();identity=source_identity(cohort,match,manifest['artifact_sha256'])
    destination=DESTINATION/f'{cohort}-{match}.json'
    if destination.exists():require_evidence(json.loads(destination.read_text()),identity);return f'{cohort} {match}: preserved diagnostic result'
    if cohort=='skillcorner':
        data=load_motion_cache(ROOT/'cache'/f'{match}-detected');frames=data.frames();case=load_case(match,'natural')
        baseline=decisions(case['baseline']);x=case['x']
    else:
        root=CODE.parent/'external-reference';data=load_cache(root/'cache'/str(match));raw=list((root/'raw').glob('*'+str(match)+'*.xml'))
        meta=next(p for p in raw if 'matchinformation' in p.name);tracking=next(p for p in raw if 'positions' in p.name)
        frames=load_dfl_motion(meta,tracking,data);baseline=infer_tactical(frames,FROZEN_MODEL['model'],Policy(**FROZEN_MODEL['policy']))
        x=np.asarray(list(motion_feature_rows(frames)),dtype=np.float32)
    scores=symmetric_scores(artifact['model'],x);scores[codes(baseline)!=3]=0.
    posterior=decode_team_sequence(scores,frames,baseline,artifact['transition_cost']*artifact['policy']['switch_multiplier'])
    off,direct=temporal_variants(frames,baseline,posterior,artifact['policy'])
    choices={'confidence_off_same_support':off,'temporal_argmax_all_X':direct,'raw_HAD_tree_argmax':raw_tree_decisions(frames)}
    result=dict(schema_version=1,identity=identity,cohort=cohort,match=match,post_hoc=True,fresh_holdout=False,
        training_or_retuning_performed=False,local_inference_performed=False,variants={},
        scope='Known-play H/A only' if cohort=='skillcorner' else 'Seen provider full H/A/D; inactive-coordinate shortcut remains',
        ties='H for exactly tied temporal logit; first H/A/D maximum for raw tree',
        warning='Direct temporal mode fills baseline X even without players/anchors; it cannot infer D or establish correctness outside reference.')
    old=codes(baseline)
    for name,decided in choices.items():
        report=compare_temporal(data.reference,old,codes(decided),data.periods,frames)
        report['new_ha_during_provider_dead']=int(((data.reference==2)&(old==3)&(codes(decided)<2)).sum())
        result['variants'][name]=report
    write_json(destination,result)
    return cohort+' '+str(match)+': '+', '.join('{} X={:.1%},spell={:.4f},new={}'.format(name,r['selected']['coverage']['undecided_fraction'],r['selected']['metrics']['spell_f1_mean'],r['change']['newly_resolved_frames']) for name,r in result['variants'].items())


def summarize():
    _,manifest=frozen();expected={'skillcorner':set(manifest['split']['test']),
        'dfl':set(sum(json.loads((CODE.parent/'external-reference/provenance.json').read_text())['split'].values(),[]))}
    reports=[json.loads(p.read_text()) for p in DESTINATION.glob('*.json') if p.name!='summary.json']
    if len(reports)!=sum(map(len,expected.values())):raise ValueError('Missing/extra ablation matches')
    for cohort,ids in expected.items():
        if {r['match'] for r in reports if r['cohort']==cohort}!=ids:raise ValueError('Ablation cohort membership differs')
    result=dict(schema_version=1,post_hoc=True,fresh_holdout=False,artifact_sha256=manifest['artifact_sha256'],local_inference_performed=False,cohorts={})
    for report in reports:require_evidence(report,source_identity(report['cohort'],report['match'],manifest['artifact_sha256']))
    for cohort in expected:
        matches=[r for r in reports if r['cohort']==cohort];variants={}
        for name in matches[0]['variants']:
            rs=[r['variants'][name] for r in matches];new=sum(r['change']['newly_resolved_frames'] for r in rs)
            by_label={}
            for label in 'HAD':
                count=sum(r['change']['newly_resolved_by_label'][label]['frames'] for r in rs)
                correct=sum(r['change']['newly_resolved_by_label'][label]['frames']*(r['change']['newly_resolved_by_label'][label]['correct_fraction'] or 0) for r in rs)
                by_label[label]=dict(frames=count,correct_fraction=correct/count if count else None)
            variants[name]=dict(matches=len(rs),mean_spell_f1=float(np.mean([r['selected']['metrics']['spell_f1_mean'] for r in rs])),
                mean_spell_change=float(np.mean([r['selected']['metrics']['spell_f1_mean']-r['baseline']['metrics']['spell_f1_mean'] for r in rs])),
                mean_unknown_fraction=float(np.mean([r['selected']['coverage']['undecided_fraction'] for r in rs])),new_frames=new,new_by_label=by_label,
                changed_already_decided=sum(r['change']['changed_already_decided_frames'] for r in rs),
                already_decided_regressions=sum(r['change']['already_decided_regressions'] for r in rs),
                already_decided_corrections=sum(r['change']['already_decided_corrections'] for r in rs),
                unmeasured_new_outside_reference=sum(r['unmeasured_new_ha_outside_reference'] for r in rs),
                new_ha_during_provider_dead=sum(r['new_ha_during_provider_dead'] for r in rs),
                hidden_truth=sum(r['hidden_opponents']['reference_short_spells'] for r in rs),hidden_hits=sum(r['hidden_opponents']['selected_hits'] for r in rs))
        result['cohorts'][cohort]=variants
    write_json(DESTINATION/'summary.json',result);print(json.dumps(result,indent=2),flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('stage',choices=['run','summarize']);parser.add_argument('--workers',type=int,default=2);args=parser.parse_args()
    if args.stage=='summarize':summarize();return
    _,manifest=frozen();dfl=sum(json.loads((CODE.parent/'external-reference/provenance.json').read_text())['split'].values(),[])
    jobs=[('skillcorner',m) for m in manifest['split']['test']]+[('dfl',m) for m in dfl]
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        for future in as_completed([pool.submit(run_one,*job) for job in jobs]):print(future.result(),flush=True)


if __name__=='__main__':main()
