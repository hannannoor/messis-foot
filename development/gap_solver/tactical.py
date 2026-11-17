"""Portable geometry-only state inference, selected exclusively on external references."""
from collections import deque
from dataclasses import dataclass,replace
from itertools import zip_longest
from math import hypot,isfinite
import struct

from .core import Config,Decision,_blocks,_candidate,infer


FEATURE_NAMES=('ball_observed','home_observed','away_observed','home_distance','away_distance',
               'distance_margin','min_distance','ball_edge_x','ball_edge_y','ball_speed',
               'recent_speed','slow_ball_age','missing_ball_age','last_home_distance',
               'last_away_distance','last_control_home','last_control_away','last_control_age')


def feature_rows(frames):
    """No reference/status/tag inputs. Physical features and retained confirmed control only."""
    cfg=Config()
    previous_period=None
    previous_ball=None
    speeds=deque(maxlen=12)
    last_ball=last_control=None
    last_side=candidate=''
    run=0
    last_h=last_a=30.
    slow=0.
    for i,f in enumerate(frames):
        if f.period not in (0,1,2):
            raise ValueError('invalid tactical period')
        if f.period!=previous_period or f.period==0:
            previous_ball=None;speeds.clear();last_ball=last_control=None
            last_side=candidate='';run=0;last_h=last_a=30.;slow=0.
        previous_period=f.period
        h_ok=f.home_distance is not None and isfinite(f.home_distance) and f.home_distance>=0
        a_ok=f.away_distance is not None and isfinite(f.away_distance) and f.away_distance>=0
        h=min(30.,f.home_distance) if h_ok else 30.
        a=min(30.,f.away_distance) if a_ok else 30.
        observed=f.ball_observed and f.period!=0
        speed=0.
        if observed:
            if previous_ball is not None:
                speed=min(50.,hypot(f.ball_x-previous_ball[0],f.ball_y-previous_ball[1])*25)
                slow=min(10.,slow+.04) if speed<=.5 else 0.
            else:
                slow=0.
            previous_ball=(f.ball_x,f.ball_y)
            last_ball=i;last_h=h;last_a=a
        else:
            previous_ball=None;slow=0.
        speeds.append(speed)
        side=_candidate(f,cfg) if f.period else ''
        if side and side==candidate:
            run+=1
        else:
            candidate=side;run=1 if side else 0
        if run>=6:
            last_side=side;last_control=i
        row=(float(observed),float(h_ok),float(a_ok),h,a,a-h,min(h,a),
             abs(f.ball_x-52.65)/52.65 if observed else 0.,abs(f.ball_y-34)/34 if observed else 0.,
             speed,sum(speeds)/len(speeds),slow,min(10.,(i-last_ball)/25) if last_ball is not None else 10.,
             last_h,last_a,float(last_side=='H'),float(last_side=='A'),
             min(10.,(i-last_control)/25) if last_control is not None else 10.)
        yield row


@dataclass(frozen=True)
class Policy:
    confidence: float=.9
    minimum_run_frames: int=6
    max_gap_s: float=2.
    bridge_s: float=2.

    def validate(self):
        if (not isfinite(self.confidence) or not 0<self.confidence<=1
                or type(self.minimum_run_frames) is not int or self.minimum_run_frames<1
                or any(not isfinite(x) or x<0 for x in (self.max_gap_s,self.bridge_s))):
            raise ValueError('invalid tactical policy')


class PortableTree:
    def __init__(self,model):
        if tuple(model.get('feature_names',()))!=FEATURE_NAMES:
            raise ValueError('exported tree feature schema differs from portable geometry features')
        names=('children_left','children_right','feature','threshold','probabilities')
        if any(name not in model for name in names):
            raise ValueError('incomplete exported tree')
        n=len(model['feature'])
        if not n or n>4095 or any(len(model[name])!=n for name in names):
            raise ValueError('invalid exported tree dimensions')
        reachable={0}
        for i in range(n):
            left,right=model['children_left'][i],model['children_right'][i]
            probabilities=model['probabilities'][i]
            if (len(probabilities)!=3 or any(not isfinite(p) or not 0<=p<=1 for p in probabilities)
                    or abs(sum(probabilities)-1)>1e-6 or not isfinite(model['threshold'][i])):
                raise ValueError('invalid exported leaf support')
            if left==right==-1:
                continue
            if (type(left) is not int or type(right) is not int or not i<left<n or not i<right<n
                    or left==right or not 0<=model['feature'][i]<len(FEATURE_NAMES)):
                raise ValueError('invalid/cyclic exported tree')
            if i in reachable:
                reachable.update((left,right))
        if len(reachable)!=n:
            raise ValueError('unreachable exported tree nodes')
        self.model=model

    def predict(self,row):
        if len(row)!=len(FEATURE_NAMES) or any(not isfinite(x) for x in row):
            raise ValueError('invalid portable feature row')
        node=0
        while self.model['children_left'][node]!=-1:
            key=self.model['feature'][node]
            # sklearn trees compare float32 inputs against stored float64 thresholds.
            value=struct.unpack('<f',struct.pack('<f',row[key]))[0]
            node=(self.model['children_left'][node] if value<=self.model['threshold'][node]
                  else self.model['children_right'][node])
        return self.model['probabilities'][node]


def apply_policy(frames,feature_probability_pairs,policy,baseline=None):
    policy.validate()
    if any(f.dead_evidence and f.dead_source=='published_pre_kickoff' for f in frames):
        raise ValueError('published pre-kickoff D shortcut is excluded from the new tactical route')
    # Automatic challenge-only tags are not part of this external geometry benchmark.
    geometry=[replace(f,tag_team='',restart_hint=False) for f in frames]
    baseline=infer(geometry) if baseline is None else baseline
    if len(baseline)!=len(frames):
        raise ValueError('tactical baseline dimensions differ')
    raw=[]
    sentinel=object()
    for f,pair in zip_longest(geometry,feature_probability_pairs,fillvalue=sentinel):
        if f is sentinel or pair is sentinel:
            raise ValueError('tactical feature/probability frame counts differ')
        row,probabilities=pair
        if len(row)!=len(FEATURE_NAMES) or len(probabilities)!=3 or any(not isfinite(p) or p<0 for p in probabilities):
            raise ValueError('invalid external state predictions')
        winner=max(range(3),key=lambda k:probabilities[k])
        label='HAD'[winner] if probabilities[winner]>=policy.confidence and f.period else 'X'
        if label=='D' and (not f.ball_observed or not row[1] or not row[2]):
            label='X'
        elif label in ('H','A'):
            if f.ball_observed:
                if not row[1] or not row[2]:
                    label='X'
            elif not (row[15 if label=='H' else 16] and row[17]<=policy.max_gap_s+1e-9):
                label='X'
        raw.append(label)
    result=list(baseline)
    for low,high in _blocks(geometry):
        first=low
        while first<high:
            stop=first+1
            while stop<high and raw[stop]==raw[first]:
                stop+=1
            label=raw[first]
            if label!='X' and stop-first>=policy.minimum_run_frames:
                for i in range(first,stop):
                    if geometry[i].dead_evidence:
                        continue
                    if label=='D' or baseline[i].label=='X':
                        reason=('external_model_dead' if label=='D' else 'external_model_control'
                                if geometry[i].ball_observed else 'external_model_retained_owner')
                        result[i]=Decision(label,reason,'external_model')
            first=stop
        anchors=list(result)
        i=low
        while i<high:
            if anchors[i].label!='X':
                i+=1;continue
            first=i
            while i<high and anchors[i].label=='X':
                i+=1
            stop=i
            if first==low or stop==high or (stop-first)/25>policy.bridge_s:
                continue
            owner=anchors[first-1].label
            if owner not in ('H','A') or anchors[stop].label!=owner:
                continue
            if any(raw[j] not in ('X',owner) or geometry[j].dead_evidence
                   or _candidate(geometry[j],Config()) not in ('',owner) for j in range(first,stop)):
                continue
            plausible=True
            for a,b in zip(geometry[first-1:stop],geometry[first:stop+1]):
                if a.ball_observed and b.ball_observed and hypot(a.ball_x-b.ball_x,a.ball_y-b.ball_y)*25>35:
                    plausible=False;break
            if plausible:
                for j in range(first,stop):
                    result[j]=Decision(owner,'bounded_same_owner_interval','inferred_heuristic')
    return result


def infer_tactical(frames,model,policy=Policy()):
    tree=PortableTree(model)
    return apply_policy(frames,((row,tree.predict(row)) for row in feature_rows(frames)),policy)
