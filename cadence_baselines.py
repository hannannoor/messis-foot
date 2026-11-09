"""Nearest-player controls with disclosed external period/tie adaptations.

Smoothing algorithm: Metrica Sports, MIT, 2026-2027; pinned upstream
f8f2629ff1e0985f81d7e59d8413678514ee1530/starter/baseline.py.
See licenses/official-baseline-MIT.txt. No challenge assets are used.
"""
from math import isfinite
from numbers import Integral
import numpy as np

from gap_solver.soft_sequence import sequence_usable
from gap_solver.materialization_control import materialize_abstentions


WINDOWS=(0,25,50,125)
MODES=('official-convention','matched-input')


def _nearest(frames):
    result=[];ties=0
    for f in frames:
        if not f.ball_observed:
            result.append(-1);continue
        nearest=[]
        for points in (f.home_xy,f.away_xy):
            values=[(x-f.ball_x)**2+(y-f.ball_y)**2 for x,y in points if isfinite(x) and isfinite(y)]
            nearest.append(min(values) if values else float('inf'))
        home,away=nearest
        if home==away==float('inf'):result.append(-1)
        else:
            result.append(0 if home<=away else 1)
            ties+=int(f.period in (1,2) and home==away)
    return result,ties


def nearest_codes(frames):
    return _nearest(frames)[0]


def smooth_votes(codes,half_width):
    if isinstance(half_width,bool) or not isinstance(half_width,Integral) or half_width<0:
        raise ValueError('Half width must be a nonnegative integer')
    a=np.asarray(codes)
    if a.ndim!=1 or not np.isin(a,(-1,0,1)).all():raise ValueError('Invalid vote codes')
    if half_width==0:return np.where(a==0,'H',np.where(a==1,'A','D')).tolist()
    h=np.concatenate(([0],np.cumsum(a==0)));v=np.concatenate(([0],np.cumsum(a==1)))
    at=np.arange(len(a));lo=np.maximum(0,at-half_width);hi=np.minimum(len(a),at+half_width+1)
    home=h[hi]-h[lo];away=v[hi]-v[lo]
    return np.where(home+away==0,'D',np.where(home>=away,'H','A')).tolist()


def _from_codes(frames,codes,usable,ties,half_width,mode):
    if mode not in MODES or isinstance(half_width,bool) or half_width not in WINDOWS:
        raise ValueError('Only the two frozen families and four frozen windows are permitted')
    periods=[f.period for f in frames]
    if any(p not in (0,1,2) for p in periods):raise ValueError('Invalid input periods')
    latent=['X']*len(frames);i=0
    while i<len(frames):
        if not periods[i] or (mode=='matched-input' and not usable[i]):i+=1;continue
        first=i;p=periods[i]
        while i<len(frames) and periods[i]==p and (mode=='official-convention' or usable[i]):i+=1
        labels=smooth_votes(codes[first:i],half_width)
        if mode=='matched-input':labels=['X' if x=='D' else x for x in labels]
        latent[first:i]=labels
    final=list(latent) if mode=='official-convention' else materialize_abstentions(latent,periods)
    return dict(latent=latent,final=final,raw_distance_ties=ties)


def baseline_predictions(frames,half_width,mode):
    codes,ties=_nearest(frames)
    usable=[sequence_usable(f) for f in frames]
    return _from_codes(frames,codes,usable,ties,half_width,mode)


def baseline_family_predictions(frames):
    codes,ties=_nearest(frames)
    usable=[sequence_usable(f) for f in frames]
    return {f'{mode}-w{width}':_from_codes(frames,codes,usable,ties,width,mode)
            for mode in MODES for width in WINDOWS}
