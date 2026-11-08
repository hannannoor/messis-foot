"""Read-only external development diagnosis; no fitting or prediction-source edits.

All arrays stay in process memory. Only bounded named aggregates are written.
"""
from pathlib import Path
import json,sys
from dataclasses import replace
import numpy as np

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
CODE=ROOT/'ball-gap-work'
sys.path.insert(0,str(CODE))
from ball_gap_candidate import selected_artifact
from ball_gap_policy import decode_ball_gap
from gap_solver.materialization_control import materialize_abstentions
from gap_solver.skillcorner import load_motion_cache
from gap_solver.external import load_cache
from gap_solver.dfl_motion import load_dfl_motion
from gap_solver.tactical import feature_rows,PortableTree
from gap_solver.tactical_model import FROZEN_MODEL
from gap_solver.soft_sequence import sequence_usable
from gap_solver.core import _candidate,Config
from gap_solver.accuracy_protocol import hash_files,digest
from accuracy_evidence import assert_public_report

CASES=(('skillcorner',1874553),('skillcorner',1886347),('dfl','J03WOH'),('dfl','J03WOY'))
PROTOCOL=dict(scope='previously examined external development only; natural inputs',
    cases={f'{c}-{m}':'development' for c,m in CASES},boundary_near_frames=50,annotation_edge_frames=50,
    episode_long_frames=50,clear_geometry='unchanged core candidate: within2m and distance margin at least0.75m',
    counterfactual='consistent team-identity exchange, fixed predictor; diagnostic only',
    inference_edits=False,head_fitting=False,target_data_used=False,fresh_holdout=False)


def write(path,value):
    assert_public_report(value)
    if path.exists():raise ValueError('Preserve existing diagnosis evidence; use an explicit new run')
    path.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def blocks(mask,periods):
    i=0
    while i<len(mask):
        if not mask[i] or not periods[i]:i+=1;continue
        first=i;p=periods[i]
        while i<len(mask) and mask[i] and periods[i]==p:i+=1
        yield first,i


def episodes(mask,periods):
    lengths=np.asarray([b-a for a,b in blocks(mask,periods)],dtype=np.int64)
    return dict(n_episodes=len(lengths),frames=int(lengths.sum()),median_s=float(np.median(lengths)/25) if len(lengths) else None,
        p90_s=float(np.quantile(lengths,.9)/25) if len(lengths) else None,max_s=float(lengths.max()/25) if len(lengths) else None,
        frames_in_episodes_at_least2s=int(lengths[lengths>=50].sum()))


def scores(frames):
    x=np.asarray(list(feature_rows(frames)),dtype=np.float32);model=FROZEN_MODEL['model'];PortableTree(model)
    nodes=np.zeros(len(x),dtype=np.int32);left=np.asarray(model['children_left']);right=np.asarray(model['children_right'])
    feature=np.asarray(model['feature']);threshold=np.asarray(model['threshold'])
    while True:
        active=np.flatnonzero(left[nodes]!=-1)
        if not len(active):break
        at=nodes[active];nodes[active]=np.where(x[active,feature[at]]<=threshold[at],left[at],right[at])
    support=np.asarray(model['probabilities'],dtype=np.float64)[nodes]
    tree=PortableTree(model)
    for i in range(0,len(x),257):assert tuple(support[i])==tuple(tree.predict(x[i]))
    return x,nodes,support


def diagnose(cohort,match):
    prefix=ROOT/('independent-reference/cache/'+str(match)+'-detected' if cohort=='skillcorner' else 'external-reference/cache/'+str(match))
    inputs={suffix:Path(str(prefix)+suffix) for suffix in ('.metadata.json','.features.npz','.reference.npz')}
    if cohort=='skillcorner':
        data=load_motion_cache(prefix);frames=data.frames();gt=data.reference;periods=data.periods
    else:
        data=load_cache(prefix)
        files={p.name:p for p in (ROOT/'external-reference/raw').glob('*'+str(match)+'*.xml') if 'matchinformation' in p.name or 'positions' in p.name}
        if len(files)!=2:raise ValueError('Expected exact DFL source pair')
        inputs.update(files);frames=load_dfl_motion(next(p for p in files.values() if 'matchinformation' in p.name),next(p for p in files.values() if 'positions' in p.name),data)
        gt=data.reference;periods=data.periods
    before=hash_files(inputs);x,nodes,support=scores(frames)
    observed=np.asarray([f.ball_observed for f in frames],dtype=bool);usable=np.asarray([sequence_usable(f) for f in frames],dtype=bool)
    labels,diag=decode_ball_gap(support,periods,usable.tolist(),observed.tolist());final=materialize_abstentions(labels,periods)
    pred=np.fromiter(('HADX'.index(v) for v in final),dtype=np.uint8);raw=support.argmax(axis=1)
    live=(gt<2)&(periods>0);swap=live&(pred<2)&(pred!=gt);raw_evaluable=observed&usable
    near=np.zeros(len(gt),bool);edge=np.zeros(len(gt),bool)
    for a,b in blocks(gt<3,periods):
        edge[a:min(b,a+50)]=True;edge[max(a,b-50):b]=True
        boundaries=np.flatnonzero(gt[a+1:b]!=gt[a:b-1])+a+1
        for at in boundaries:near[max(a,at-50):min(b,at+51)]=True
    interior=~near&~edge
    geometry=np.asarray([{'H':0,'A':1}.get(_candidate(f,Config()),3) if f.geometry_valid else 3 for f in frames],dtype=np.uint8)
    memory=np.where(x[:,15]>.5,0,np.where(x[:,16]>.5,1,3))
    def stats(mask):
        at=live&mask;wrong=swap&at;measured=at&raw_evaluable
        return dict(frames=int(at.sum()),H_reference_frames=int((at&(gt==0)).sum()),A_reference_frames=int((at&(gt==1)).sum()),
            H_to_A=int((at&(gt==0)&(pred==1)).sum()),A_to_H=int((at&(gt==1)&(pred==0)).sum()),
            wrong_team=int(wrong.sum()),wrong_team_fraction=float(wrong.sum()/at.sum()) if at.any() else None,
            false_D=int((at&(pred==2)).sum()),raw_evaluable_frames=int(measured.sum()),
            raw_correct_final_wrong=int((measured&(raw==gt)&(pred!=gt)).sum()),
            raw_wrong_final_correct=int((measured&(raw!=gt)&(pred==gt)).sum()),
            raw_wrong_team=int((measured&(raw<2)&(raw!=gt)).sum()),
            wrong_team_with_geometry_agreeing_gt=int((wrong&(geometry==gt)).sum()),
            wrong_team_with_memory_agreeing_gt=int((wrong&(memory==gt)).sum()),
            wrong_team_with_memory_opposite_gt=int((wrong&(memory<2)&(memory!=gt)).sum()))
    strata={
        'all_known_live':stats(np.ones(len(gt),bool)),
        'ball_available':stats(observed),'ball_missing':stats(~observed),
        'near_known_state_boundary_2s':stats(near),'near_annotation_edge_2s':stats(edge),
        'reference_interior_beyond2s':stats(interior),
        'observed_interior_beyond2s':stats(observed&interior),
        'clear_geometry_agrees_gt':stats(geometry==gt),
        'observed_interior_geometry_agrees_gt':stats(observed&interior&(geometry==gt)),
        'memory_available_age_at_most_1_54s':stats((memory<2)&(x[:,17]<=1.54)),
        'memory_available_age_above_1_54s':stats((memory<2)&(x[:,17]>1.54)),
        'period1':stats(periods==1),'period2':stats(periods==2)}
    leaves={str(int(node)):stats((nodes==node)&observed) for node in np.unique(nodes)}
    # Metamorphic diagnostic: labels/IDs transform with team point sets; coordinates and clock do not.
    exchanged=[replace(f,home_distance=f.away_distance,away_distance=f.home_distance,
        home_xy=f.away_xy,away_xy=f.home_xy,home_ids=f.away_ids,away_ids=f.home_ids) for f in frames]
    sx,snodes,ssupport=scores(exchanged);susable=[sequence_usable(f) for f in exchanged]
    slabels,_=decode_ball_gap(ssupport,periods,susable,observed.tolist())
    spred=np.fromiter(('HADX'.index(v) for v in materialize_abstentions(slabels,periods)),dtype=np.uint8)
    back=np.asarray([1,0,2,3],dtype=np.uint8)[spred];sraw=np.asarray([1,0,2,3],dtype=np.uint8)[ssupport.argmax(axis=1)]
    symmetry=dict(known_live_frames=int(live.sum()),raw_observed_disagreements=int((live&observed&(raw!=sraw)).sum()),
        final_disagreements=int((live&(pred!=back)).sum()),original_correct_exchanged_wrong=int((live&(pred==gt)&(back!=gt)).sum()),
        original_wrong_exchanged_correct=int((live&(pred!=gt)&(back==gt)).sum()),
        original_HA_swaps=int(swap.sum()),exchanged_HA_swaps=int((live&(back<2)&(back!=gt)).sum()))
    result=dict(cohort=cohort,match=match,regime='natural',reference_type='seen external provider labels; not independent control truth',
        structural_frames=len(frames),input_sha256=before,policy_diagnostics=diag,strata=strata,
        swap_episodes=episodes(swap,periods),interior_swap_episodes=episodes(swap&interior,periods),
        observed_leaf_counts=leaves,team_exchange=symmetry)
    assert hash_files(inputs)==before,'Consumed input changed during diagnosis'
    assert_public_report(result)
    print(json.dumps({'cohort':cohort,'match':match,'all':strata['all_known_live'],'interior':strata['observed_interior_beyond2s'],'symmetry':symmetry}),flush=True)
    return result


def main():
    artifact,_=selected_artifact();source=hash_files({'diagnostic_script':Path(__file__)})
    write(HERE/'diagnosis-protocol.json',dict(protocol=PROTOCOL,source_sha256=source,baseline_release_sha256=digest(artifact)))
    results=[diagnose(c,m) for c,m in CASES]
    selected_artifact();assert hash_files({'diagnostic_script':Path(__file__)})==source
    write(HERE/'development-diagnosis.json',dict(protocol_sha256=digest(PROTOCOL),source_sha256=source,baseline_release_sha256=digest(artifact),
        no_inference_source_edit=True,no_head_fitting=True,no_target_data=True,fresh_holdout=False,cases=results))
    print('Four natural development cases complete; only aggregate diagnostics saved',flush=True)

if __name__=='__main__':main()
