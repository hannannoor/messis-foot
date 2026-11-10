"""Deterministic geometry-only touch detection on canonical 25 Hz tracks."""
from dataclasses import dataclass
from math import hypot,isfinite

FPS=25
WINDOW=5
RADIUS=2.5
MARGIN=.5

@dataclass(frozen=True,order=True)
class TouchEvent:
    frame_index:int
    team:str
    kind:str


def validate_frames(frames):
    for frame in frames:
        if type(frame.period) is not int or frame.period not in (0,1,2):raise ValueError('Invalid period')
        ball=(frame.ball_x,frame.ball_y)
        if any(x is not None and (not isinstance(x,(float,int)) or not isfinite(x)) for x in ball):
            raise ValueError('Nonfinite ball coordinates')
        if (ball[0] is None)!=(ball[1] is None):raise ValueError('Partial ball coordinate')
        for points in (frame.home_xy,frame.away_xy):
            if any(len(point)!=2 or not all(isinstance(x,(float,int)) and isfinite(x) for x in point) for point in points):
                raise ValueError('Invalid player coordinates')


def attributed_team(frame):
    distances=[min((hypot(x-frame.ball_x,y-frame.ball_y) for x,y in points),default=float('inf'))
               for points in (frame.home_xy,frame.away_xy)]
    h,a=distances
    if min(h,a)>RADIUS:return None
    return ('H' if h<a else 'A') if abs(h-a)>=MARGIN else ''


def detect_touches(frames,theta):
    if not isinstance(theta,(int,float)) or not isfinite(theta) or theta<0:raise ValueError('Invalid theta')
    validate_frames(frames)
    events=[];n=len(frames);i=0;previous_run=None;last_period=None
    while i<n:
        f=frames[i]
        if f.period!=last_period or not f.period:previous_run=None
        last_period=f.period
        if not f.period or not f.ball_observed:
            i+=1;continue
        first=i;period=f.period
        while i<n and frames[i].period==period and frames[i].ball_observed:i+=1
        stop=i
        def velocity(a,b):return ((frames[b].ball_x-frames[a].ball_x)*FPS/(b-a),
                                  (frames[b].ball_y-frames[a].ball_y)*FPS/(b-a))
        if previous_run is not None:
            old_first,old_stop=previous_run;last=old_stop-1
            if first>old_stop and old_stop-old_first>=WINDOW+1:
                vx,vy=velocity(last-WINDOW,last);seconds=(first-last)/FPS
                error=hypot(f.ball_x-frames[last].ball_x-vx*seconds,f.ball_y-frames[last].ball_y-vy*seconds)
                team=attributed_team(f)
                if error>theta*seconds and team is not None:events.append(TouchEvent(first,team,'reacquire'))
        surprises={}
        for t in range(first+WINDOW,stop-WINDOW):
            before=velocity(t-WINDOW,t);after=velocity(t,t+WINDOW)
            surprises[t]=hypot(after[0]-before[0],after[1]-before[1])
        for t,surprise in surprises.items():
            if surprise<theta:continue
            neighborhood=range(max(first+WINDOW,t-WINDOW),min(stop-WINDOW,t+WINDOW+1))
            peak=max(neighborhood,key=lambda j:(surprises[j],-j))
            if peak!=t:continue
            team=attributed_team(frames[t])
            if team is not None:events.append(TouchEvent(t,team,'kink'))
        previous_run=(first,stop)
    return events
