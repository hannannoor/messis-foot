"""Motion-only reconstruction for explicitly seen DFL regression data, never fresh testing."""
from array import array
import xml.etree.ElementTree as ET
import numpy as np
from .motion import motion_frame


def load_dfl_motion(metadata_path,tracking_path,base):
    general=ET.parse(metadata_path).getroot().find('.//General')
    home,away=general.get('HomeTeamId'),general.get('GuestTeamId')
    if not home or not away or home==away:raise ValueError('invalid DFL team identities')
    pitch=base.notes['source_pitch_m'];tracks=[];current=None;sections={'firstHalf':1,'secondHalf':2}
    for event,element in ET.iterparse(tracking_path,events=('start','end')):
        tag=element.tag.rsplit('}',1)[-1]
        if event=='start' and tag=='FrameSet':
            team=element.get('TeamId');period=sections.get(element.get('GameSection'))
            current=dict(side=int(team==away),period=period,person=element.get('PersonId'),n=array('i'),x=array('f'),y=array('f')) if team in (home,away) and period else None
        elif event=='end' and tag=='Frame':
            if current is not None:
                current['n'].append(int(element.get('N')))
                for axis in ('x','y'):
                    raw=element.get(axis.upper());current[axis].append(float(raw) if raw and raw.lower() not in ('nan','none') else float('nan'))
            element.clear()
        elif event=='end' and tag=='FrameSet':
            if current is not None and current['n']:tracks.append(current)
            current=None;element.clear()
    identities=[sorted({r['person'] for r in tracks if r['side']==side}) for side in (0,1)]
    if any(None in ids or len(ids)>64 for ids in identities):raise ValueError('unsupported DFL player identities')
    xy=[np.full((len(base.periods),len(ids),2),np.nan,dtype=np.float32) for ids in identities]
    seen=set()
    for row in tracks:
        at=np.flatnonzero(base.periods==row['period']);numbers=base.source_frames[at]
        native=np.asarray(row['n']);indices=np.searchsorted(numbers,native)
        if (indices>=len(numbers)).any() or not np.array_equal(numbers[indices],native):raise ValueError('DFL player grid differs from frozen baseline')
        if len(native)>1 and (np.diff(native)<=0).any():raise ValueError('DFL track indices do not increase')
        side=row['side'];person=identities[side].index(row['person']);selected=at[indices]
        key=(side,person,row['period'])
        if key in seen and np.isfinite(xy[side][selected,person]).any():raise ValueError('overlapping DFL player tracks')
        seen.add(key)
        xy[side][selected,person,0]=(np.asarray(row['x'])/pitch[0]+.5)*105.3
        xy[side][selected,person,1]=(np.asarray(row['y'])/pitch[1]+.5)*68
    result=[]
    for i,(period,ball) in enumerate(zip(base.periods,base.ball_xy)):
        points=[];ids=[]
        for side in (0,1):
            selected=np.flatnonzero(np.isfinite(xy[side][i]).all(axis=1))
            points.append(tuple(map(tuple,xy[side][i,selected])));ids.append(tuple(map(int,selected)))
        result.append(motion_frame(int(period),tuple(ball) if np.isfinite(ball).all() else None,*points,*ids,
            ball_native_observation=None,ball_provenance='available_freshness_unverified'))
    return result
