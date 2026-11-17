"""Deterministic adjacent point correspondence, never verified player identities."""
from dataclasses import replace
from math import isfinite

MAX_STEP_M=20./25.  # Predeclared engineering bound; no target-data calibration.


def associate_anonymous(frames):
    result=[];previous={'home':(), 'away':()};next_id=0;last_period=0;matched=0;created=0
    def nearest(distances):
        if not distances:return None
        ordered=sorted(enumerate(distances),key=lambda z:z[1])
        if ordered[0][1]>MAX_STEP_M**2:return None
        if len(ordered)>1 and abs(ordered[0][1]-ordered[1][1])<=1e-12:return None
        return ordered[0][0]
    for f in frames:
        valid=f.period in (1,2) and f.geometry_valid
        if not valid or f.period!=last_period:previous={'home':(), 'away':()}
        changes={}
        for side in ('home','away'):
            points=sorted(getattr(f,side+'_xy')) if valid else []
            if any(len(p)!=2 or not all(isfinite(x) for x in p) for p in points):raise ValueError('Invalid anonymous point')
            old=previous[side];distances=[[(x-a)**2+(y-b)**2 for _,(a,b) in old] for x,y in points]
            toward_old=[nearest(row) for row in distances]
            toward_new=[nearest([row[j] for row in distances]) for j in range(len(old))]
            ids=[]
            for i,j in enumerate(toward_old):
                if j is not None and toward_new[j]==i:identifier=old[j][0];matched+=1
                else:identifier=next_id;next_id+=1;created+=1
                ids.append(identifier)
            changes[side+'_xy']=tuple(points);changes[side+'_ids']=tuple(ids)
            previous[side]=tuple(zip(ids,points))
        if not valid:
            changes.update(ball_x=None,ball_y=None,home_distance=None,away_distance=None,
                ball_native_observation=False,ball_provenance='missing',ball_sample_time_s=None)
        result.append(replace(f,**changes));last_period=f.period
    return result,dict(method='mutual_unique_nearest_adjacent_team_points',max_step_m=MAX_STEP_M,
        matches=matched,new_correspondences=created,player_identity_verified=False,
        ambiguity_policy='new correspondence; no tie breaking by slot',freshness_verified=False)
