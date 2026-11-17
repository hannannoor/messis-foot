"""Observed-only touch amendment; archived experiment remains unchanged."""
from math import isfinite
from touch_physics import detect_touches
from touch_evidence import prepare_evidence
from touch_decoder import validate_rows,decode_variable
from gap_solver.materialization_control import materialize_abstentions
from release_runtime import ReleasePrediction


def detect_observed_touches(frames,theta):
    return [event for event in detect_touches(frames,theta) if event.kind=='kink']


def observed_evidence_rows(rows,periods,usable,observed,events,beta,c_touch):
    n=len(periods);costs=[(32.,)*3 for _ in range(n)]
    validate_rows(rows,periods,usable,costs)
    if len(observed)!=n or any(type(v) is not bool for v in observed):raise ValueError('Explicit observation flags required')
    if any(not isinstance(v,(int,float)) or not isfinite(v) or v<0 for v in (beta,c_touch)):raise ValueError('Invalid touch parameters')
    previous=-1;by_frame={}
    for event in events:
        at=event.frame_index
        if (type(at) is not int or not previous<at<n or not periods[at] or not observed[at]
            or event.team not in ('H','A','') or event.kind!='kink'):raise ValueError('Invalid observed touch')
        previous=at;by_frame[at]=event
    result=[];owner='';start=-1;previous_period=None
    for i,(row,period,ok,seen) in enumerate(zip(rows,periods,usable,observed)):
        if period!=previous_period or not period or not seen:owner=''
        previous_period=period
        if i in by_frame:
            owner=by_frame[i].team;start=i
            if owner:
                cost=list(costs[i]);cost['HAD'.index(owner)]=c_touch;costs[i]=tuple(cost)
        if owner and i-start>=250:owner=''
        values=list(row) if seen else [0.,0.,0.]
        if owner and ok and period:values['HAD'.index(owner)]+=beta
        if not all(isfinite(v) for v in values):raise ValueError('Touch evidence overflow')
        result.append(tuple(values))
    return result,costs


def predict_observed_touch(frames,theta,beta,c_touch,events=None):
    detected=detect_observed_touches(frames,theta)
    events=detected if events is None else events
    base,_,periods,usable,counts=prepare_evidence(frames,[],0,32)
    rows,costs=observed_evidence_rows(base,periods,usable,[f.ball_observed for f in frames],events,beta,c_touch)
    latent=decode_variable(rows,periods,usable,costs)
    labels=materialize_abstentions(latent,periods)
    counts=dict(counts,materialized_rows=sum(a!=b for a,b in zip(latent,labels)),
        latent_unknown_active=sum(bool(p) and label=='X' for p,label in zip(periods,latent)))
    return ReleasePrediction(tuple(latent),tuple(labels),counts)
