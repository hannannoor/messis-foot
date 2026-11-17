"""Post-freeze explanatory diagnostics; never fits or selects a model."""
from dataclasses import replace
import json
from pathlib import Path
import numpy as np
from gap_solver.external import load_cache
from gap_solver.frozen_protocol import load_frozen
from gap_solver.core import infer
from gap_solver.tactical import Policy,infer_tactical
from gap_solver.selection import ball_mask
from gap_solver.benchmark import evaluate_external,compare_external

CODE=Path(__file__).resolve().parent
ROOT=CODE.parent/'external-reference'


def codes(decisions):
    return np.asarray(['HADX'.index(d.label) for d in decisions],dtype=np.uint8)


def describe(mask,reference,before,after):
    selected=mask&(reference<3)
    n=int(selected.sum())
    return dict(frames=n,baseline_x=int((selected&(before==3)).sum()),selected_x=int((selected&(after==3)).sum()),
                baseline_raw_correct_fraction=float((before[selected]==reference[selected]).mean()) if n else None,
                selected_raw_correct_fraction=float((after[selected]==reference[selected]).mean()) if n else None)


def main():
    artifact,manifest=load_frozen(ROOT,CODE/'gap_solver')
    diagnostics=dict(model_id=manifest['artifact_sha256'],used_for_model_selection=False,
                     definitions='External provider-state boundaries; flight/stationary groupings are observable proxies, not independently annotated physical events.',
                     validation={})
    for match in manifest['split']['validation']:
        data=load_cache(ROOT/'cache'/match);frames=data.frames()
        old=codes(infer(frames));new=codes(infer_tactical(frames,artifact['model'],Policy(**artifact['policy'])))
        observed=np.isfinite(data.ball_xy).all(axis=1)
        speed=np.full(len(frames),np.nan)
        same=(data.periods[1:]==data.periods[:-1])&observed[1:]&observed[:-1]
        indices=np.flatnonzero(same)+1
        speed[indices]=np.hypot(*(data.ball_xy[indices]-data.ball_xy[indices-1]).T)*25
        available=np.isfinite(data.distances).all(axis=1)
        nearby=available&(np.min(np.where(np.isfinite(data.distances),data.distances,np.inf),axis=1)<=2)
        groups={
            'numeric_ball_position_missing':~observed,
            'ball_far_from_both_teams_proxy':observed&available&(data.distances[:,0]>2)&(data.distances[:,1]>2),
            'slow_nearby_ball_proxy':observed&nearby&(speed<=.5)}
        boundary_counts={}
        for kind in ('team_handover','inactive_to_active_restart','active_to_inactive_stoppage'):
            mask=np.zeros(len(frames),dtype=bool);count=0
            for i in range(1,len(frames)):
                a,b=int(data.reference[i-1]),int(data.reference[i])
                if data.periods[i]!=data.periods[i-1] or a==b or a==3 or b==3:
                    continue
                actual=('inactive_to_active_restart' if a==2 else 'active_to_inactive_stoppage' if b==2 else 'team_handover')
                if actual==kind:
                    count+=1
                    first=max(0,i-25);stop=min(len(frames),i+26)
                    local=np.arange(first,stop)
                    mask[local[data.periods[local]==data.periods[i]]]=True
            groups[kind+'_one_second_window']=mask;boundary_counts[kind]=count
        result={name:describe(mask,data.reference,old,new) for name,mask in groups.items()}
        result['reference_boundary_counts']=boundary_counts
        result['stationary_reference_dead_assigned_team_before']=int((groups['slow_nearby_ball_proxy']&(data.reference==2)&(old<2)).sum())
        result['stationary_reference_dead_assigned_team_after']=int((groups['slow_nearby_ball_proxy']&(data.reference==2)&(new<2)).sum())
        diagnostics['validation'][match]=result
    (ROOT/'reports'/'boundary-and-observation-diagnostics.json').write_text(json.dumps(diagnostics,indent=2)+'\n',encoding='utf-8')
    stress=dict(model_id=manifest['artifact_sha256'],post_freeze_diagnostic=True,used_for_selection=False,matches={})
    for index,match in enumerate(manifest['split']['test']):
        data=load_cache(ROOT/'cache'/match);original=data.frames()
        cases={}
        before=codes(infer(original));after=codes(infer_tactical(original,artifact['model'],Policy(**artifact['policy'])))
        active_reference=data.reference.copy();active_reference[active_reference==2]=3
        cases['reference_active_only_diagnostic']=dict(
            baseline=evaluate_external(active_reference,before,data.periods),
            selected=evaluate_external(active_reference,after,data.periods),
            note='Reference-active conditional score excludes inactive spans only for scoring; inputs and frozen predictions are unchanged. Post-hoc diagnostic, not selection.')
        mask=ball_mask(data.periods,.3,4729+index)
        for side in ('home','away'):
            frames=[replace(f,**{side+'_distance':None}) if hidden else f for f,hidden in zip(original,mask)]
            old=codes(infer(frames));new=codes(infer_tactical(frames,artifact['model'],Policy(**artifact['policy'])))
            cases[side+'_distance_dropout_30pct']=dict(
                baseline=evaluate_external(data.reference,old,data.periods),
                selected=evaluate_external(data.reference,new,data.periods),
                change=compare_external(data.reference,old,new,data.periods),
                note='Synthetic entire-team nearest-distance unavailable; not a simulation of every partial-player tracking error.')
        stress['matches'][match]=cases
        print('Completed frozen boundary/observation diagnostics for '+match,flush=True)
    (ROOT/'reports'/'team-occlusion-stress.json').write_text(json.dumps(stress,indent=2)+'\n',encoding='utf-8')
    for match,cases in stress['matches'].items():
        for name,case in cases.items():
            print('{} {} spell {:.4f}->{:.4f}'.format(match,name,case['baseline']['metrics']['spell_f1_mean'],case['selected']['metrics']['spell_f1_mean']),flush=True)


if __name__=='__main__':
    main()
