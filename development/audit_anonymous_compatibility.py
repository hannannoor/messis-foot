"""Predeclared seen-data stress of estimated correspondence; no fitting or selection."""
import argparse,json
from pathlib import Path
import numpy as np
from gap_solver.anonymous_motion import associate_anonymous
from gap_solver.candidate_cli import ROOT,predict_four
from gap_solver.input_contract import sha256
from gap_solver.temporal_protocol import load_temporal_frozen
from gap_solver.temporal import motion_feature_rows,MOTION_FEATURES
from gap_solver.temporal_metrics import compare_temporal
from gap_solver.skillcorner import load_motion_cache
from gap_solver.external import load_cache
from gap_solver.dfl_motion import load_dfl_motion


def aggregate_score(report):
    fields=('macro_f1','spell_f1_mean','spell_f1_at_headline','spell_iou_headline','accuracy','kappa',
        'n_gt_spells','n_pred_spells','spell_count_error','mean_spell_duration_s','gt_mean_spell_duration_s')
    coverage=('graded_frames','resolved_frames','undecided_frames','resolved_fraction','undecided_fraction','decided_correct_fraction')
    def selected(section,names):
        return {key:value for key,value in report['selected'][section].items() if key in names and (value is None or type(value) in (int,float))}
    return dict(metrics=selected('metrics',fields),coverage=selected('coverage',coverage))


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('cohort',choices=['skillcorner','dfl']);a=p.parse_args()
    freeze=ROOT/'reports/input-contract/comparison-freeze.json';frozen=json.loads(freeze.read_text())
    for name,expected in frozen['source_sha256'].items():
        if sha256(ROOT/name)!=expected:raise ValueError('Comparison source changed after freeze: '+name)
    match=frozen['stress_matches'][a.cohort][0];inputs={}
    if a.cohort=='skillcorner':
        prefix=ROOT.parent/'independent-reference/cache'/f'{match}-detected'
        data=load_motion_cache(prefix);frames=data.frames()
    else:
        base=ROOT.parent/'external-reference';prefix=base/'cache'/match;data=load_cache(prefix)
        paths=list((base/'raw').glob('*'+match+'*.xml'))
        meta=next(p for p in paths if 'matchinformation' in p.name);raw=next(p for p in paths if 'positions' in p.name)
        frames=load_dfl_motion(meta,raw,data);inputs.update(metadata=sha256(meta),tracking=sha256(raw))
    for suffix in ('.metadata.json','.features.npz','.reference.npz'):inputs[suffix]=sha256(str(prefix)+suffix)
    artifact,manifest=load_temporal_frozen(ROOT/'benchmark/skillcorner/frozen',ROOT)
    estimated,association=associate_anonymous(frames)
    original=predict_four(frames,artifact);adapted=predict_four(estimated,artifact)
    encode=lambda values:np.fromiter(('HADX'.index(x) for x in values),dtype=np.uint8,count=len(values))
    old=encode(original['incumbent'])
    if not np.array_equal(old,encode(adapted['incumbent'])):raise ValueError('Correspondence must not change incumbent geometry predictions')
    original_x=np.asarray(list(motion_feature_rows(frames)),dtype=np.float32)
    estimated_x=np.asarray(list(motion_feature_rows(estimated)),dtype=np.float32)
    indices=[i for i,name in enumerate(MOTION_FEATURES) if any(x in name for x in ('continuity','_vx','_vy','speed'))]
    result=dict(schema_version=1,cohort=a.cohort,match=match,fresh_holdout=False,previously_seen_development=True,
        fitting_or_selection_performed=False,full_dead_reference=a.cohort=='dfl',association=association,
        comparison_freeze_sha256=sha256(freeze),input_sha256=inputs,driver_sha256=sha256(__file__),
        baseline_predictions_identical=True,features={MOTION_FEATURES[i]:dict(mean_absolute_change=float(np.mean(np.abs(original_x[:,i]-estimated_x[:,i])))) for i in indices},policies={})
    for name in original:
        one=encode(original[name]);two=encode(adapted[name])
        def metrics(pred):
            report=compare_temporal(data.reference,old,pred,data.periods,frames)
            return aggregate_score(report)
        result['policies'][name]=dict(original_ids=metrics(one),estimated_correspondence=metrics(two),changed_frames=int((one!=two).sum()))
    out=ROOT/'reports/input-contract'/f'{a.cohort}-anonymous-compatibility.json'
    if out.exists():raise ValueError('Preserve existing stress result')
    out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
