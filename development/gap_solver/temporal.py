"""Portable player-motion evidence and offline team-state inference, without reference inputs."""
from dataclasses import dataclass,replace
from math import exp,hypot,isfinite,log,log1p
import struct

from .core import Decision,_blocks,infer


MOTION_FEATURES=('ball_available','home_count','away_count','home_cx','home_cy','away_cx','away_cy',
    'home_width','home_length','away_width','away_length','home_vx','home_vy','away_vx','away_vy',
    'home_speed','away_speed','home_continuity','away_continuity','home_distance','away_distance',
    'last_owner','next_owner','last_anchor_available','next_anchor_available','last_anchor_age','next_anchor_age',
    'gap_progress','gap_duration','last_ball_x','last_ball_y','next_ball_x','next_ball_y',
    'home_path_distance','away_path_distance','home_near_path','away_near_path','home_count_delta','away_count_delta')
_INDEX={name:i for i,name in enumerate(MOTION_FEATURES)}


def _clip(value,low=-1.,high=1.):return max(low,min(high,value))


def _quantile(values,q):
    values=sorted(values)
    if not values:return 0.
    at=q*(len(values)-1);low=int(at);high=min(len(values)-1,low+1)
    return values[low]+(values[high]-values[low])*(at-low)


def _points(frame,side):
    points=getattr(frame,side+'_xy',());ids=getattr(frame,side+'_ids',())
    if ids and len(ids)!=len(points):raise ValueError('motion identity/position dimensions disagree')
    ids=ids or tuple(range(len(points)))
    if len(set(ids))!=len(ids):raise ValueError('duplicate motion track identity')
    return {person:(float(x),float(y)) for person,(x,y) in zip(ids,points)
            if isfinite(x) and isfinite(y) and -10<=x<=115.3 and -10<=y<=78}


def anchor_context(frames):
    clean=[replace(f,tag_team='',restart_hint=False,dead_evidence=False,dead_source='') for f in frames]
    geometry=infer(clean);n=len(frames);left=[-1]*n;right=[-1]*n;owners=[0]*n
    for i,(f,d) in enumerate(zip(clean,geometry)):
        if (f.ball_observed and getattr(f,'geometry_valid',True) and d.label in ('H','A')
                and len(_points(f,'home'))>=3 and len(_points(f,'away'))>=3):owners[i]=-1 if d.label=='H' else 1
    for first,stop in _blocks(clean):
        last=-1
        for i in range(first,stop):
            if owners[i]:last=i
            left[i]=last
        following=-1
        for i in range(stop-1,first-1,-1):
            if owners[i]:following=i
            right[i]=following
    return left,right,owners


def motion_feature_rows(frames):
    left,right,owners=anchor_context(frames)
    previous=[{},{}];previous_period=0
    for i,f in enumerate(frames):
        if not f.period or f.period!=previous_period or not getattr(f,'geometry_valid',True):previous=[{},{}]
        previous_period=f.period
        teams=[_points(f,side) if getattr(f,'geometry_valid',True) else {} for side in ('home','away')]
        summaries=[]
        for points,prior in zip(teams,previous):
            xy=list(points.values());xs=[p[0] for p in xy];ys=[p[1] for p in xy]
            common=[person for person in points if person in prior]
            vx=[(points[p][0]-prior[p][0])*25 for p in common];vy=[(points[p][1]-prior[p][1])*25 for p in common]
            speeds=[hypot(a,b) for a,b in zip(vx,vy)]
            summaries.append(dict(count=min(len(xy),11)/11,cx=_clip((_quantile(xs,.5)-52.65)/52.65) if xy else 0.,
                cy=_clip((_quantile(ys,.5)-34)/34) if xy else 0.,
                width=(_quantile(ys,.9)-_quantile(ys,.1))/68 if xy else 0.,
                length=(_quantile(xs,.9)-_quantile(xs,.1))/105.3 if xy else 0.,
                vx=_clip(_quantile(vx,.5)/15),vy=_clip(_quantile(vy,.5)/15),
                speed=_clip(_quantile(speeds,.5)/20,0,1),
                continuity=len(common)/max(len(points),len(prior),1),
                count_delta=_clip((len(points)-len(prior))/11)))
        a,b=left[i],right[i];last=frames[a] if a>=0 else None;following=frames[b] if b>=0 else None
        progress=(i-a)/(b-a) if a>=0 and b>a else .5
        if f.ball_observed:path=(f.ball_x,f.ball_y)
        elif last is not None and following is not None:
            path=(last.ball_x+(following.ball_x-last.ball_x)*progress,last.ball_y+(following.ball_y-last.ball_y)*progress)
        else:path=None
        distances=[];near=[]
        for points in teams:
            values=[hypot(x-path[0],y-path[1]) for x,y in points.values()] if path is not None else []
            distances.append(min(min(values,default=30.),30.)/30)
            near.append(sum(d<=5 for d in values)/max(len(values),1))
        def ball_coord(anchor,axis):
            if anchor is None:return 0.
            return _clip(((anchor.ball_x if axis==0 else anchor.ball_y)-(52.65 if axis==0 else 34))/(52.65 if axis==0 else 34))
        h,away=summaries
        row=(float(f.ball_observed),h['count'],away['count'],h['cx'],h['cy'],away['cx'],away['cy'],
            h['width'],h['length'],away['width'],away['length'],h['vx'],h['vy'],away['vx'],away['vy'],
            h['speed'],away['speed'],h['continuity'],away['continuity'],
            min(f.home_distance,30.)/30 if f.home_distance is not None else 1.,
            min(f.away_distance,30.)/30 if f.away_distance is not None else 1.,
            float(owners[a]) if a>=0 else 0.,float(owners[b]) if b>=0 else 0.,float(a>=0),float(b>=0),
            min((i-a)/25,30.)/30 if a>=0 else 1.,min((b-i)/25,30.)/30 if b>=0 else 1.,progress,
            min(max(b-a-1,0)/25,120.)/120 if a>=0 and b>=0 else 1.,
            ball_coord(last,0),ball_coord(last,1),ball_coord(following,0),ball_coord(following,1),
            *distances,*near,h['count_delta'],away['count_delta'])
        if len(row)!=len(MOTION_FEATURES) or not all(isfinite(x) for x in row):raise ValueError('nonfinite motion feature')
        yield row
        previous=teams if f.period and getattr(f,'geometry_valid',True) else [{},{}]


def swap_feature_row(row):
    values=list(row)
    for name,index in _INDEX.items():
        if name.startswith('home_'):values[index]=row[_INDEX['away_'+name[5:]]]
        elif name.startswith('away_'):values[index]=row[_INDEX['home_'+name[5:]]]
    for name in ('last_owner','next_owner'):values[_INDEX[name]]=-row[_INDEX[name]]
    return tuple(values)


def reflect_feature_row(row):
    values=list(row)
    for name in ('home_cx','home_cy','away_cx','away_cy','home_vx','home_vy','away_vx','away_vy',
                 'last_ball_x','last_ball_y','next_ball_x','next_ball_y'):values[_INDEX[name]]=-row[_INDEX[name]]
    return tuple(values)


def mask_motion_frames(frames,mask):
    if len(frames)!=len(mask):raise ValueError('motion mask dimensions disagree')
    return [replace(f,ball_x=None,ball_y=None,home_distance=None,away_distance=None,
             ball_native_observation=False,ball_provenance='missing',ball_interpolated=False,ball_sample_time_s=None)
            if remove else f for f,remove in zip(frames,mask)]


class PortableBoosted:
    def __init__(self,model):
        if tuple(model.get('feature_names',()))!=MOTION_FEATURES:raise ValueError('portable motion feature schema differs')
        self.model=model
        if not isfinite(model.get('initial_log_odds',float('nan'))) or not 0<model.get('learning_rate',0)<=1:
            raise ValueError('invalid portable ensemble scale')
        trees=model.get('trees',[])
        if not trees or len(trees)>1000:raise ValueError('invalid portable ensemble dimensions')
        for tree in trees:
            n=len(tree.get('feature',[]))
            if not n or n>4095 or any(len(tree.get(k,[]))!=n for k in ('children_left','children_right','threshold','value')):
                raise ValueError('invalid regression tree dimensions')
            reached={0}
            for i in range(n):
                a,b=tree['children_left'][i],tree['children_right'][i]
                if not isfinite(tree['threshold'][i]) or not isfinite(tree['value'][i]):raise ValueError('invalid regression tree value')
                if a==b==-1:continue
                if type(a) is not int or type(b) is not int or not i<a<n or not i<b<n or a==b or not 0<=tree['feature'][i]<len(MOTION_FEATURES):
                    raise ValueError('invalid/cyclic regression tree')
                if i in reached:reached.update((a,b))
            if len(reached)!=n:raise ValueError('unreachable regression tree')

    def score(self,row):
        if len(row)!=len(MOTION_FEATURES) or not all(isfinite(v) for v in row):raise ValueError('invalid motion feature row')
        values=struct.unpack('<'+'f'*len(row),struct.pack('<'+'f'*len(row),*row))
        score=self.model['initial_log_odds'];rate=self.model['learning_rate']
        for tree in self.model['trees']:
            node=0
            while tree['children_left'][node]!=-1:
                node=tree['children_left'][node] if values[tree['feature'][node]]<=tree['threshold'][node] else tree['children_right'][node]
            score+=rate*tree['value'][node]
        return score

    def symmetric_score(self,row):return (self.score(row)-self.score(swap_feature_row(row)))/2


@dataclass(frozen=True)
class TemporalPolicy:
    confidence: float=.95
    max_gap_s: float=5.
    minimum_players: int=3
    switch_multiplier: float=1.

    def validate(self):
        if (not .5<self.confidence<=1 or not isfinite(self.max_gap_s) or self.max_gap_s<0
                or type(self.minimum_players) is not int or self.minimum_players<1
                or not isfinite(self.switch_multiplier) or self.switch_multiplier<=0):
            raise ValueError('invalid temporal policy')


def _logadd(a,b):
    maximum=max(a,b)
    return maximum+log(exp(a-maximum)+exp(b-maximum)) if isfinite(maximum) else maximum


def decode_team_sequence(scores,frames,baseline,switch_cost):
    n=len(frames)
    if len(scores)!=n or len(baseline)!=n or not isfinite(switch_cost) or switch_cost<0 or not all(isfinite(z) for z in scores):
        raise ValueError('invalid temporal decoder inputs')
    posterior=[0.]*n;i=0
    def usable(k):return frames[k].period and getattr(frames[k],'geometry_valid',True) and baseline[k].label!='D'
    while i<n:
        if not usable(i):i+=1;continue
        first=i;period=frames[i].period
        while i<n and usable(i) and frames[i].period==period:i+=1
        stop=i;emissions=[]
        for k in range(first,stop):
            label=baseline[k].label
            if label=='H':emissions.append((0.,-float('inf')))
            elif label=='A':emissions.append((-float('inf'),0.))
            else:
                z=_clip(scores[k],-50,50);emissions.append((-log1p(exp(z)),-log1p(exp(-z))))
        forward=[];a=b=0.
        for e0,e1 in emissions:
            x=e0+_logadd(a,b-switch_cost);y=e1+_logadd(b,a-switch_cost)
            normal=max(x,y);a,b=x-normal,y-normal;forward.append((a,b))
        a=b=0.
        for j in range(stop-first-1,-1,-1):
            f0,f1=forward[j];posterior[first+j]=_clip((f1+b)-(f0+a),-50,50)
            e0,e1=emissions[j]
            x=_logadd(e0+a,e1+b-switch_cost);y=_logadd(e1+b,e0+a-switch_cost)
            normal=max(x,y);a,b=x-normal,y-normal
    return posterior


def apply_temporal_policy(frames,baseline,posterior,policy,context=None):
    policy.validate();n=len(frames)
    if len(baseline)!=n or len(posterior)!=n:raise ValueError('temporal policy dimensions disagree')
    left,right,_=anchor_context(frames) if context is None else context
    barriers=[0]
    for f,d in zip(frames,baseline):barriers.append(barriers[-1]+int(not f.period or not getattr(f,'geometry_valid',True) or d.label=='D'))
    result=list(baseline)
    for i,(f,d,z) in enumerate(zip(frames,baseline,posterior)):
        if d.label!='X' or not f.period or not getattr(f,'geometry_valid',True):continue
        if len(_points(f,'home'))<policy.minimum_players or len(_points(f,'away'))<policy.minimum_players:continue
        a,b=left[i],right[i]
        if a<0 or b<0 or max(b-a-1,0)/25>policy.max_gap_s or barriers[b+1]!=barriers[a]:continue
        if not isfinite(z):raise ValueError('nonfinite temporal posterior')
        p=1/(1+exp(-_clip(z,-50,50)))
        if max(p,1-p)<policy.confidence:continue
        result[i]=Decision('A' if p>.5 else 'H','temporal_player_motion','external_temporal_experiment')
    return result


def infer_temporal(frames,artifact,baseline=None):
    if any(f.dead_evidence for f in frames):raise ValueError('geometry-only temporal inference cannot consume dead labels')
    if baseline is None:
        from .tactical import infer_tactical,Policy
        from .tactical_model import FROZEN_MODEL
        baseline=infer_tactical(frames,FROZEN_MODEL['model'],Policy(**FROZEN_MODEL['policy']))
    policy=TemporalPolicy(**artifact['policy']);policy.validate()
    temperature=float(artifact['temperature'])
    if not isfinite(temperature) or temperature<=0:raise ValueError('invalid temporal score scale')
    tree=PortableBoosted(artifact['model'])
    scores=[tree.symmetric_score(row) if d.label=='X' else 0. for row,d in zip(motion_feature_rows(frames),baseline)]
    posterior=decode_team_sequence(scores,frames,baseline,float(artifact['transition_cost'])*policy.switch_multiplier)
    return apply_temporal_policy(frames,baseline,[z/temperature for z in posterior],policy)
