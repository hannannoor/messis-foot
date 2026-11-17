"""Touch evidence layered on the unchanged frozen tactical head."""
from math import isfinite
from gap_solver.soft_sequence import soft_emissions,sequence_usable
from gap_solver.materialization_control import materialize_abstentions
from gap_solver.tactical import PortableTree,feature_rows
from gap_solver.tactical_model import FROZEN_MODEL
from release_runtime import ReleasePrediction
from touch_decoder import decode_variable,validate_rows
from touch_physics import detect_touches,validate_frames


def evidence_rows(rows,periods,usable,events,beta,c_touch):
    if any(not isinstance(v,(float,int)) or not isfinite(v) or v<0 for v in (beta,c_touch)):
        raise ValueError('Invalid evidence parameters')
    n=len(periods);costs=[(32.,)*3 for _ in range(n)]
    validate_rows(rows,periods,usable,costs)
    previous=-1;by_frame={}
    for event in events:
        at=event.frame_index
        if (type(at) is not int or not previous<at<n or event.team not in ('H','A','')
            or event.kind not in ('kink','reacquire') or not periods[at]):raise ValueError('Invalid touch event')
        previous=at;by_frame[at]=event
    result=[];owner='';start=-1;previous_period=None
    for i,(row,period,ok) in enumerate(zip(rows,periods,usable)):
        if period!=previous_period or not period:owner=''
        previous_period=period
        if i in by_frame:
            owner=by_frame[i].team;start=i
            if owner:
                cost=list(costs[i]);cost['HAD'.index(owner)]=c_touch;costs[i]=tuple(cost)
        if owner and i-start>=250:owner=''
        row=list(row)
        if owner and ok and period:row['HAD'.index(owner)]+=beta
        if not all(isfinite(v) for v in row):raise ValueError('Evidence overflow')
        result.append(tuple(row))
    return result,costs


def prepare_evidence(frames,events,beta,c_touch):
    validate_frames(frames)
    if any(f.tag_team or f.restart_hint or f.dead_evidence or f.dead_source for f in frames):
        raise ValueError('Touch inference accepts geometry without label hints')
    tree=PortableTree(FROZEN_MODEL['model'])
    supports=[tree.predict(row) for row in feature_rows(frames)]
    periods=[f.period for f in frames];usable=[sequence_usable(f) for f in frames]
    observed=[f.ball_observed for f in frames]
    rows=soft_emissions(supports,[0.]*len(frames),0.)
    rows=[row if seen else (0.,)*3 for row,seen in zip(rows,observed)]
    effective=list(usable);segments=unsupported=0;i=0;n=len(frames)
    while i<n:
        if not periods[i] or not usable[i]:i+=1;continue
        first=i;period=periods[i]
        while i<n and periods[i]==period and usable[i]:i+=1
        if not any(observed[first:i]):
            segments+=1;unsupported+=i-first;effective[first:i]=[False]*(i-first)
    rows,costs=evidence_rows(rows,periods,effective,events,beta,c_touch)
    counts=dict(neutral_active_usable_rows=sum(bool(p and u and not o) for p,u,o in zip(periods,usable,observed)),
        unsupported_segments=segments,unsupported_active_rows=unsupported)
    return rows,costs,periods,effective,counts


def predict_touch(frames,theta,beta,c_touch,events=None):
    detected=detect_touches(frames,theta)
    events=detected if events is None else events
    rows,costs,periods,usable,counts=prepare_evidence(frames,events,beta,c_touch)
    latent=decode_variable(rows,periods,usable,costs)
    labels=materialize_abstentions(latent,periods)
    counts=dict(counts,materialized_rows=sum(a!=b for a,b in zip(latent,labels)),
        latent_unknown_active=sum(bool(p) and label=='X' for p,label in zip(periods,latent)))
    return ReleasePrediction(tuple(latent),tuple(labels),counts)
