"""Strict IDSSE adapter for external evaluation. Target attributes never become features."""
from array import array
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np
from .core import Frame


@dataclass
class ExternalMatch:
    match_id: str
    periods: object
    source_frames: object
    ball_xy: object
    distances: object
    player_counts: object
    reference: object
    notes: dict

    def frames(self):
        def number(x):
            return float(x) if np.isfinite(x) else None
        return [Frame(period=int(p),ball_x=number(b[0]),ball_y=number(b[1]),
                      home_distance=number(d[0]),away_distance=number(d[1]))
                for p,b,d in zip(self.periods,self.ball_xy,self.distances)]


def _coordinate(value):
    if value is None or value.lower() in ('','nan','none'):
        return float('nan')
    result=float(value)
    if not np.isfinite(result):
        raise ValueError('nonfinite external coordinate')
    return result


def reference_code(status,possession):
    if status=='0':
        return 2
    if status=='1' and possession in ('1','2'):
        return int(possession)-1
    return 3


def load_external(metadata_path,tracking_path):
    metadata=ET.parse(metadata_path).getroot()
    general=metadata.find('.//General')
    if general is None:
        raise ValueError('external metadata lacks General record')
    home,away=general.get('HomeTeamId'),general.get('GuestTeamId')
    if not home or not away or home==away:
        raise ValueError('external metadata needs distinct home and away identities')
    match_id=general.get('MatchId','unknown')
    records=[]
    current=None
    pitch=None
    excluded=Counter()
    raw_states,raw_possessions=Counter(),Counter()
    previous_last={}
    sections={'firstHalf':1,'secondHalf':2}
    for event,element in ET.iterparse(tracking_path,events=('start','end')):
        tag=element.tag.rsplit('}',1)[-1]
        if event=='start' and tag=='FrameSet':
            section=element.get('GameSection')
            team=element.get('TeamId','')
            kind='ball' if team.lower()=='ball' else 'player' if team in (home,away) else None
            if section not in sections or kind is None:
                excluded[str(section)+':'+str(team)]+=1
                current=None
            else:
                source_match=element.get('MatchId')
                if source_match and match_id!='unknown' and source_match!=match_id:
                    raise ValueError('tracking match ID disagrees with external metadata')
                current=dict(period=sections[section],team=team,person=element.get('PersonId',team),kind=kind,
                             n=array('i'),x=array('f'),y=array('f'),target=array('B'),first_t=None,last_t=None)
        elif event=='end' and tag=='PitchSize':
            candidate=(float(element.get('X','0')),float(element.get('Y','0')))
            if not all(np.isfinite(v) and v>0 for v in candidate) or pitch is not None and candidate!=pitch:
                raise ValueError('invalid/inconsistent external pitch dimensions')
            pitch=candidate
            element.clear()
        elif event=='end' and tag=='Frame':
            if current is not None:
                n=int(element.get('N','-1'))
                if n<0 or current['n'] and n<=current['n'][-1]:
                    raise ValueError('external frame IDs must increase within each track')
                current['n'].append(n)
                current['x'].append(_coordinate(element.get('X')))
                current['y'].append(_coordinate(element.get('Y')))
                timestamp=element.get('T')
                if timestamp:
                    current['first_t']=current['first_t'] or timestamp
                    current['last_t']=timestamp
                if current['kind']=='ball':
                    status,possession=element.get('BallStatus',''),element.get('BallPossession','')
                    raw_states[status]+=1;raw_possessions[possession]+=1
                    current['target'].append(reference_code(status,possession))
            element.clear()
        elif event=='end' and tag=='FrameSet':
            if current is not None and current['n']:
                key=(current['period'],current['team'],current['person'])
                if key in previous_last and current['n'][0]<=previous_last[key]:
                    raise ValueError('external track reuses original frame IDs')
                previous_last[key]=current['n'][-1]
                if current['first_t'] and len(current['n'])>1:
                    duration=(datetime.fromisoformat(current['last_t'])-datetime.fromisoformat(current['first_t'])).total_seconds()
                    expected=(current['n'][-1]-current['n'][0])/25
                    if abs(duration-expected)>.01:
                        raise ValueError('external timestamps disagree with canonical 25 Hz frame grid')
                records.append(current)
            current=None
            element.clear()
    if pitch is None or not records or not any(r['kind']=='ball' for r in records):
        raise ValueError('external tracking lacks pitch dimensions or ball records')
    periods=[];numbers=[];balls=[];distances=[];counts=[];references=[]
    for period in sorted({r['period'] for r in records}):
        rows=[r for r in records if r['period']==period]
        first=min(r['n'][0] for r in rows);last=max(r['n'][-1] for r in rows)
        n=last-first+1
        if n>1000000:
            raise ValueError('unreasonable external period frame range')
        xy=np.full((n,2),np.nan,dtype=np.float32)
        target=np.full(n,3,dtype=np.uint8)
        ball_seen=np.zeros(n,dtype=bool)
        for r in rows:
            if r['kind']!='ball':
                continue
            indices=np.asarray(r['n'],dtype=np.int64)-first
            if ball_seen[indices].any():
                raise ValueError('duplicate external ball frame')
            ball_seen[indices]=True
            xy[indices,0]=(np.asarray(r['x'])/pitch[0]+.5)*105.3
            xy[indices,1]=(np.asarray(r['y'])/pitch[1]+.5)*68
            target[indices]=np.asarray(r['target'])
        minimum=np.full((n,2),np.inf,dtype=np.float32)
        visible=np.zeros((n,2),dtype=np.uint8)
        for r in rows:
            if r['kind']!='player':
                continue
            side=0 if r['team']==home else 1
            indices=np.asarray(r['n'],dtype=np.int64)-first
            px=(np.asarray(r['x'])/pitch[0]+.5)*105.3
            py=(np.asarray(r['y'])/pitch[1]+.5)*68
            seen=np.isfinite(px)&np.isfinite(py)
            visible[indices[seen],side]+=1
            observed=seen&np.isfinite(xy[indices]).all(axis=1)
            selected=indices[observed]
            d=np.hypot(px[observed]-xy[selected,0],py[observed]-xy[selected,1])
            minimum[selected,side]=np.minimum(minimum[selected,side],d)
        minimum[~np.isfinite(minimum)]=np.nan
        periods.append(np.full(n,period,dtype=np.uint8));numbers.append(np.arange(first,last+1,dtype=np.int32))
        balls.append(xy);distances.append(minimum);counts.append(visible);references.append(target)
    notes=dict(fps=25,canonical_pitch_m=[105.3,68],source_pitch_m=list(pitch),
               raw_status_counts=dict(raw_states),raw_possession_counts=dict(raw_possessions),
               excluded_track_sections=dict(excluded),reference_type='provider reference; not competition gold',
               label_features_excluded=['BallStatus','BallPossession','events','match/team identities'],
               unknown_reference_preserved=True)
    return ExternalMatch(match_id,np.concatenate(periods),np.concatenate(numbers),np.concatenate(balls),
                         np.concatenate(distances),np.concatenate(counts),np.concatenate(references),notes)


def save_cache(match,prefix):
    prefix=Path(prefix);prefix.parent.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(str(prefix)+'.features.npz',periods=match.periods,source_frames=match.source_frames,
                        ball_xy=match.ball_xy,distances=match.distances,player_counts=match.player_counts)
    np.savez_compressed(str(prefix)+'.reference.npz',periods=match.periods,source_frames=match.source_frames,reference=match.reference)
    Path(str(prefix)+'.metadata.json').write_text(json.dumps(dict(match_id=match.match_id,notes=match.notes),indent=2)+'\n',encoding='utf-8')


def load_cache(prefix):
    prefix=str(prefix)
    meta=json.loads(Path(prefix+'.metadata.json').read_text(encoding='utf-8'))
    with np.load(prefix+'.features.npz',allow_pickle=False) as features,np.load(prefix+'.reference.npz',allow_pickle=False) as reference:
        for key in ('periods','source_frames'):
            if not np.array_equal(features[key],reference[key]):
                raise ValueError('external feature/reference frame grids disagree')
        return ExternalMatch(meta['match_id'],features['periods'],features['source_frames'],features['ball_xy'],
                             features['distances'],features['player_counts'],reference['reference'],meta['notes'])
