"""Geometry-only global reconstruction and explicit 10-to-25 Hz transform."""
from contextlib import closing
from dataclasses import dataclass
from itertools import groupby
from math import hypot,isfinite
from pathlib import Path
from statistics import median
import sqlite3

from gap_solver.motion import motion_frame

HYPOTHESES=('absolute-x','absolute-xy','offset-x','offset-xy')


@dataclass(frozen=True)
class GeometryDecision:
    selected:str|None
    eligible:int
    candidate_counts:dict
    failure:str|None


@dataclass
class CanonicalInput:
    frames:list
    index:list
    quality:dict
    endpoints:list


def _connect(path):
    return closing(sqlite3.connect(Path(path).resolve().as_uri()+'?mode=ro',uri=True))


def _clock_bounds(db):
    with _connect(db) as con:
        bounds=con.execute('select period,min(t),max(t),count(distinct t) from geometry group by period order by period').fetchall()
        if [r[0] for r in bounds]!=[1,2]:raise ValueError('Both source periods required')
        for period,first,last,count in bounds:
            if first<0 or last>86400000 or last-first>5400000:raise ValueError('Source clock extent exceeds contract')
            for (t,) in con.execute('select distinct t from geometry where period=?',(period,)):
                if type(t) is not int or (t-first)%100:raise ValueError('Source cadence differs from 100 ms lattice')
    return bounds


def _native(db):
    with _connect(db) as con:
        cursor=con.execute('select period,t,team,player,x,y,bx,by from geometry order by period,t,team,player')
        for key,group in groupby(cursor,key=lambda r:(r[0],r[1])):yield key,list(group)


def _finite(*values):
    return all(x is not None and isfinite(x) for x in values)


def _eligible(rows):
    for team in (1,2):
        members=[r for r in rows if r[2]==team]
        if sum(_finite(r[4],r[5]) for r in members)<3:return False
        if sum(_finite(*r[4:8]) for r in members)<2:return False
    return True


def _reflect(x,y,team,hypothesis):
    return (-x,-y if hypothesis.endswith('-xy') else y) if team==2 else (x,y)


def _reconstruct(rows,hypothesis):
    points=[];supports={1:0,2:0}
    for _,_,team,player,x,y,bx,by in rows:
        if not _finite(x,y,bx,by):continue
        if hypothesis.startswith('offset-'):bx+=x;by+=y
        points.append(_reflect(bx,by,team,hypothesis));supports[team]+=1
    if min(supports.values())<2:return None
    if max(p[0] for p in points)-min(p[0] for p in points)>.25:return None
    if max(p[1] for p in points)-min(p[1] for p in points)>.25:return None
    for i,p in enumerate(points):
        if any(hypot(p[0]-q[0],p[1]-q[1])>.25 for q in points[i+1:]):return None
    return median(p[0] for p in points),median(p[1] for p in points)


def qualify(geometry_db):
    _clock_bounds(geometry_db)
    eligible=0;counts=dict.fromkeys(HYPOTHESES,0)
    for _,rows in _native(geometry_db):
        if not _eligible(rows):continue
        eligible+=1
        for h in HYPOTHESES:counts[h]+=int(_reconstruct(rows,h) is not None)
    passing=[h for h in HYPOTHESES if eligible>=100 and 100*counts[h]>=99*eligible]
    if len(passing)!=1:
        return GeometryDecision(None,eligible,counts,'insufficient_eligible_timestamps' if eligible<100 else 'ambiguous_or_unresolved_coordinates')
    return GeometryDecision(passing[0],eligible,counts,None)


def _canonical(x,y):
    return x*105.3/105+52.65,y+34.


def _native_sample(rows,hypothesis):
    players={1:{},2:{}}
    for _,_,team,player,x,y,_,_ in rows:
        if _finite(x,y):players[team][player]=_canonical(*_reflect(x,y,team,hypothesis))
    ball=_reconstruct(rows,hypothesis)
    return players,None if ball is None else _canonical(*ball)


def canonical_input(geometry_db,decision):
    if decision.selected not in HYPOTHESES or decision.failure is not None:
        raise ValueError('Passing geometry decision required')
    if qualify(geometry_db)!=decision:raise ValueError('Geometry decision/source mismatch')
    bounds=_clock_bounds(geometry_db)
    samples={1:{},2:{}}
    for (p,t),rows in _native(geometry_db):samples[p][t]=_native_sample(rows,decision.selected)
    frames=[];index=[];endpoints=[]
    quality=dict(canonical_rows=0,native_source_frames=sum(len(s) for s in samples.values()),
                 native_grid_rows=0,interpolated_geometry_rows=0,unusable_geometry_rows=0,
                 native_ball_rows=0,interpolated_ball_rows=0,missing_ball_rows=0)
    for period,first,last,_ in bounds:
        native=samples[period]
        for t in range(first,last+1,40):
            exact=t in native;left=first+(t-first)//100*100;right=left+100
            valid=exact or left in native and right in native
            if exact:
                players,ball=native[t];ends=(t,t);quality['native_grid_rows']+=1
            elif valid:
                a,ab=native[left];b,bb=native[right];weight=(t-left)/100
                players={team:{pid:tuple(a[team][pid][j]+weight*(b[team][pid][j]-a[team][pid][j]) for j in (0,1))
                               for pid in sorted(a[team].keys()&b[team].keys())} for team in (1,2)}
                ball=None if ab is None or bb is None else tuple(ab[j]+weight*(bb[j]-ab[j]) for j in (0,1))
                ends=(left,right);quality['interpolated_geometry_rows']+=1
            else:
                players={1:{},2:{}};ball=None;ends=(None,None);quality['unusable_geometry_rows']+=1
            ids=[tuple(sorted(players[team])) for team in (1,2)]
            points=[tuple(players[team][pid] for pid in ids[team-1]) for team in (1,2)]
            f=motion_frame(period,ball,*points,*ids,geometry_valid=bool(valid),
                ball_native_observation=bool(exact and ball is not None),
                ball_provenance='wcsf_preprocessed_10hz' if exact else 'wcsf_interpolated_25hz',
                ball_interpolated=bool(not exact and valid and ball is not None),
                ball_sample_time_s=t/1000 if ball is not None else None,
                interpolated=bool(not exact and valid),native_frame=(t-first)//100 if exact else None)
            frames.append(f);index.append((period,t));endpoints.append(ends)
            quality['canonical_rows']+=1
            quality['missing_ball_rows']+=int(ball is None)
            quality['native_ball_rows']+=int(exact and ball is not None)
            quality['interpolated_ball_rows']+=int(not exact and ball is not None)
    return CanonicalInput(frames,index,quality,endpoints)
