"""Finite three-state offline evidence; no reference or incumbent anchor input."""
from math import isfinite,log
from .temporal import _points


def sequence_usable(frame):
    if frame.period not in (1,2) or not frame.geometry_valid:return False
    observed=frame.ball_observed and all(x is not None and isfinite(x) and x>=0 for x in (frame.home_distance,frame.away_distance))
    return observed or len(_points(frame,'home'))>=3 and len(_points(frame,'away'))>=3


def soft_emissions(supports,motion_scores,weight):
    if not isfinite(weight) or weight<0 or len(supports)!=len(motion_scores):raise ValueError('Invalid soft emission dimensions/weight')
    result=[]
    for p,z in zip(supports,motion_scores):
        if len(p)!=3 or any(not isfinite(x) or not 0<=x<=1 for x in p) or abs(sum(p)-1)>1e-6 or not isfinite(z):raise ValueError('Invalid soft head scores')
        adjustment=weight*z/2
        row=(log(max(p[0],1e-6))-adjustment,log(max(p[1],1e-6))+adjustment,log(max(p[2],1e-6)))
        if not all(isfinite(x) for x in row):raise ValueError('Soft emission overflow')
        result.append(row)
    return result


def decode_soft(emissions,periods,usable,switch_cost):
    n=len(periods)
    if len(emissions)!=n or len(usable)!=n or not isfinite(switch_cost) or switch_cost<0:raise ValueError('Invalid soft decoder dimensions/cost')
    if any(p not in (0,1,2) for p in periods) or any(len(r)!=3 or not all(isfinite(x) for x in r) for r in emissions):raise ValueError('Invalid soft decoder states/emissions')
    result=['X']*n;back=[bytearray(n) for _ in range(3)];i=0
    while i<n:
        if not periods[i] or not usable[i]:i+=1;continue
        first=i;period=periods[i];previous=(0.,0.,0.)
        while i<n and periods[i]==period and usable[i]:
            row=emissions[i];values=[]
            for state in range(3):
                a=previous[0]-(switch_cost if state!=0 else 0.)
                b=previous[1]-(switch_cost if state!=1 else 0.)
                c=previous[2]-(switch_cost if state!=2 else 0.)
                chosen=0 if a>=b and a>=c else (1 if b>=c else 2)
                back[state][i]=chosen;values.append((a,b,c)[chosen]+row[state])
            normal=max(values);previous=tuple(v-normal for v in values)
            if not all(isfinite(v) for v in previous):raise ValueError('Soft decoder overflow')
            i+=1
        a,b,c=previous;state=0 if a>=b and a>=c else (1 if b>=c else 2)
        for j in range(i-1,first-1,-1):result[j]='HAD'[state];state=back[state][j]
    return result
