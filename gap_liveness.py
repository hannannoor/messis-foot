"""Fixed label-free gap liveness; pure standard-library geometry functions."""
from dataclasses import dataclass
from math import hypot,isfinite
from numbers import Real
from statistics import median

FPS=25
SAMPLE_STEP=5
LONG_GAP=75
SPEED_CAP=12
MIN_PLAYERS=10
RESTART_SPEED=.5
MAX_EXTENSION=250

@dataclass(frozen=True)
class GapApplication:
    labels:tuple
    summary:dict
    stoppage_gaps:tuple
    extensions:tuple


def _players(frame):
    result={}
    for side in ('home','away'):
        points=getattr(frame,side+'_xy');ids=getattr(frame,side+'_ids')
        if any(len(point)!=2 or not all(isinstance(v,Real) and isfinite(v) for v in point) for point in points):
            raise ValueError('Invalid player coordinates')
        if not ids:continue
        if len(ids)!=len(points):raise ValueError('Player identity dimensions differ')
        for identifier,point in zip(ids,points):
            try:key=(side,identifier);duplicate=key in result
            except TypeError:raise ValueError('Invalid player identity') from None
            if identifier is None or duplicate:raise ValueError('Missing/duplicate player identity')
            result[key]=point
    return result


def _validate(frames):
    for frame in frames:
        if type(frame.period) is not int or frame.period not in (0,1,2):raise ValueError('Invalid period')
        coordinates=(frame.ball_x,frame.ball_y)
        if ((coordinates[0] is None)!=(coordinates[1] is None)
            or any(v is not None and (not isinstance(v,Real) or not isfinite(v)) for v in coordinates)):
            raise ValueError('Invalid ball coordinates')
        _players(frame)


def player_speed_statistics(frames):
    _validate(frames)
    result=[None]*len(frames);start=0;previous_period=None
    for i,frame in enumerate(frames):
        if frame.period!=previous_period:start=i
        previous_period=frame.period
        if not frame.period or i%SAMPLE_STEP or i-FPS<start:continue
        before=frames[i-FPS]
        if not frame.geometry_valid or not before.geometry_valid:continue
        current=_players(frame);old=_players(before);speeds=[]
        for key,(x,y) in current.items():
            if key not in old:continue
            a,b=old[key];speed=hypot(float(x)-float(a),float(y)-float(b))
            if isfinite(speed) and speed<SPEED_CAP:speeds.append(speed)
        if len(speeds)>=MIN_PLAYERS:result[i]=float(median(speeds))
    return tuple(result)


def long_gaps(frames):
    gaps=[];i=0
    while i<len(frames):
        frame=frames[i]
        if frame.period not in (1,2) or frame.ball_observed:i+=1;continue
        first=i;period=frame.period
        while i<len(frames) and frames[i].period==period and not frames[i].ball_observed:i+=1
        if i-first>LONG_GAP:gaps.append((first,i))
    return tuple(gaps)


def apply_gap_rule(frames,control_labels):
    if len(frames)!=len(control_labels) or any(v not in ('H','A','D','X') for v in control_labels):
        raise ValueError('Invalid control labels/dimensions')
    statistics=player_speed_statistics(frames);gaps=long_gaps(frames)
    inside=bytearray(len(frames))
    for first,stop in gaps:inside[first:stop]=b'\1'*(stop-first)
    reference_values=[v for i,v in enumerate(statistics) if frames[i].period and not inside[i] and v is not None]
    reference=float(median(reference_values)) if reference_values else None
    result=list(control_labels);stoppages=[];extensions=[]
    for first,stop in gaps:
        values=[v for v in statistics[first:stop] if v is not None]
        if reference is None or not values or not median(values)<reference:continue
        stoppages.append((first,stop));result[first:stop]=['D']*(stop-first)
        previous=first-1
        if previous<0 or frames[previous].period!=frames[first].period or not frames[previous].ball_observed:continue
        at=stop
        while at<len(frames) and at-stop<MAX_EXTENSION:
            frame=frames[at]
            if frame.period!=frames[first].period or not frame.ball_observed:break
            speed=hypot(float(frame.ball_x)-float(frames[previous].ball_x),float(frame.ball_y)-float(frames[previous].ball_y))*FPS
            if not isfinite(speed) or speed>RESTART_SPEED:break
            result[at]='D';previous=at;at+=1
        if at>stop:extensions.append((stop,at))
    summary=dict(long_gaps=len(gaps),stoppage_gaps=len(stoppages),live_or_unclassified_gaps=len(gaps)-len(stoppages),
        long_gap_frames=sum(b-a for a,b in gaps),stoppage_gap_frames=sum(b-a for a,b in stoppages),
        restart_extension_frames=sum(b-a for a,b in extensions),frames_relabelled=sum(a!=b for a,b in zip(control_labels,result)),
        reference_speed_mps=reference,defined_speed_samples=sum(v is not None for v in statistics))
    return GapApplication(tuple(result),summary,tuple(stoppages),tuple(extensions))
