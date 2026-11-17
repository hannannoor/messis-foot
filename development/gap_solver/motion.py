"""Geometry records that retain player context when ball coordinates are unavailable."""
from dataclasses import dataclass,replace
from math import hypot
from typing import Optional
import xml.etree.ElementTree as ET

from .core import Frame
from .io import N_FRAMES,BLOCKS,_number


@dataclass(frozen=True)
class MotionFrame(Frame):
    home_xy: tuple=()
    away_xy: tuple=()
    home_ids: tuple=()
    away_ids: tuple=()
    geometry_valid: bool=True
    ball_native_observation: Optional[bool]=None
    ball_provenance: str='available_unverified'
    ball_interpolated: bool=False
    ball_sample_time_s: Optional[float]=None
    interpolated: bool=False
    native_frame: Optional[int]=None


def motion_frame(period,ball,home,away,home_ids=(),away_ids=(),**flags):
    home,away=tuple(home),tuple(away)
    bx,by=ball if ball is not None else (None,None)
    if ball is None:
        flags.update(ball_native_observation=False,ball_provenance='missing',ball_interpolated=False,ball_sample_time_s=None)
    def nearest(points):
        return min((hypot(x-bx,y-by) for x,y in points),default=None) if ball is not None else None
    return MotionFrame(period=period,ball_x=bx,ball_y=by,
        home_distance=nearest(home),away_distance=nearest(away),
        home_xy=home,away_xy=away,home_ids=tuple(home_ids),away_ids=tuple(away_ids),**flags)


def load_motion_atd(meta_path,raw_path,quality_path,n_frames=N_FRAMES,blocks=None):
    """Strict local parsing; no tags, labels, fixed D, or freshness assumptions."""
    from .tactical_cli import apply_geometry_quality
    metadata=ET.parse(meta_path).getroot()
    teams=list(metadata.iter('Team'))
    if len(teams)!=2 or len({t.get('id') for t in teams})!=2:
        raise ValueError('motion metadata requires two distinct teams')
    ids=[t.get('id') for t in teams]
    slots=[p.get('teamId') for p in metadata.iter('Player')]
    if not slots or any(side not in ids for side in slots):
        raise ValueError('invalid motion player membership')
    sides=[ids.index(side) for side in slots]
    periods=[0]*n_frames
    for period,first,last in BLOCKS if blocks is None else blocks:
        if period not in (1,2):raise ValueError('invalid motion period')
        for i in range(max(0,first),min(n_frames,last+1)):periods[i]=period
    frames=[]
    with open(raw_path,encoding='utf-8-sig') as handle:
        for i,line in enumerate(handle):
            parts=line.strip().split(':')
            if len(parts)!=3 or int(parts[0])!=i+1 or i>=n_frames:
                raise ValueError('motion ATD must retain contiguous original frame IDs')
            values=parts[1].split(';')
            if len(values)!=len(slots):raise ValueError('motion player slot count differs from metadata')
            points=[[],[]];members=[[],[]]
            for slot,(side,value) in enumerate(zip(sides,values)):
                xyz=value.split(',')
                if len(xyz)!=3:raise ValueError('motion player requires x,y,speed')
                x,y=_number(xyz[0]),_number(xyz[1])
                if x is not None and y is not None:
                    points[side].append((x*105.3,y*68.));members[side].append(slot)
            values=parts[2].split(',')
            if len(values)!=3:raise ValueError('motion ball requires x,y,speed')
            x,y=_number(values[0]),_number(values[1])
            ball=(x*105.3,y*68.) if x is not None and y is not None else None
            frames.append(motion_frame(periods[i],ball,*points,*members,native_frame=i,
                                       ball_sample_time_s=i/25 if ball is not None else None))
    if len(frames)!=n_frames:raise ValueError('motion tracking row count differs from expected source')
    _,valid=apply_geometry_quality(frames,quality_path)
    frames=[f if ok else replace(f,ball_x=None,ball_y=None,home_distance=None,away_distance=None,
             home_xy=(),away_xy=(),home_ids=(),away_ids=(),geometry_valid=False,
             ball_native_observation=False,ball_provenance='missing',ball_interpolated=False,ball_sample_time_s=None)
            for f,ok in zip(frames,valid)]
    return frames,tuple(t.findtext('Name') or '' for t in teams)
