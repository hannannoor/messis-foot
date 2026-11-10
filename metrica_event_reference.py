"""Prospective sparse-event reference convention for public Metrica samples."""
from collections import defaultdict
from dataclasses import dataclass
from math import isfinite

KINDS={'PASS','CARRY','RECOVERY','SHOT','SET PIECE','BALL LOST','BALL OUT','FAULT RECEIVED','CHALLENGE','CARD'}
ACTIONS={'PASS','CARRY','RECOVERY','SHOT','BALL LOST','BALL OUT'}

@dataclass(frozen=True)
class Event:
    period:int
    start:int
    end:int
    team:str
    kind:str
    subtypes:tuple=()
    missing_end:bool=False


def _index(frame,time):
    frame=int(frame);time=float(time)
    if frame<0 or not isfinite(time) or frame!=round(time*25):raise ValueError('Event frame/time clock disagreement')
    return frame-1


def _event(period,start,end,team,kind,tokens):
    kind=str(kind).strip().upper();tokens=tuple(str(v).strip().upper() for v in tokens if str(v).strip())
    missing_end=end==-1 and start>=0 and kind=='SET PIECE'
    if missing_end:end=start
    if int(period) not in (1,2) or end<start or kind not in KINDS or team not in ('H','A',''):raise ValueError('Unsupported Metrica event mapping')
    return Event(int(period),start,end,team,kind,tokens,missing_end)


def normalize_csv(row):
    side={'HOME':'H','AWAY':'A'}.get(str(row['Team']).strip().upper(),'')
    return _event(row['Period'],_index(row['Start Frame'],row['Start Time [s]']),_index(row['End Frame'],row['End Time [s]']),side,row['Type'],str(row['Subtype']).split('-'))


def normalize_json(row,team_map):
    value=row.get('subtypes');subtypes=[]
    if isinstance(value,dict):subtypes=[value['name']]
    elif isinstance(value,list):subtypes=[v['name'] for v in value]
    elif value is not None:raise ValueError('Unsupported subtype format')
    return _event(row['period'],_index(row['start']['frame'],row['start']['time']),_index(row['end']['frame'],row['end']['time']),team_map.get((row.get('team') or {}).get('id'),''),row['type']['name'],subtypes)


def build_reference(events,periods):
    n=len(periods)
    if any(type(p) is not int or p not in (0,1,2) for p in periods):raise ValueError('Invalid reference periods')
    for e in events:
        if (e.period not in (1,2) or type(e.start) is not int or type(e.end) is not int or not -1<=e.start<=e.end
            or e.team not in ('H','A','') or e.kind not in KINDS):raise ValueError('Invalid normalized event')
    labels=['X']*n;i=0;used=set();clipped=conflicts=0
    while i<n:
        if not periods[i]:i+=1;continue
        first=i;period=periods[i]
        while i<n and periods[i]==period:i+=1
        stop=i;selected=[(j,e) for j,e in enumerate(events) if e.period==period and e.end>=first and e.start<stop]
        if not selected:continue
        used.update(j for j,e in selected)
        meaningful=[(j,e) for j,e in selected if e.kind!='CARD']
        if not meaningful:continue
        coverage_end=max(min(e.end,stop-1) for _,e in meaningful);points=defaultdict(list)
        for j,e in selected:
            used.add(j);clipped+=int(e.start<first or e.end>=stop)
            if e.kind=='CARD':continue
            start=max(first,e.start);end=min(stop-1,e.end)
            is_stop=(e.kind in ('BALL OUT','FAULT RECEIVED') or bool({'FAULT','GOAL'}.intersection(e.subtypes)))
            if e.kind in ACTIONS:points[start].append(('owner',e.team))
            if e.kind=='SET PIECE':points[start].append(('restart',e.team))
            if e.kind=='CHALLENGE' and not is_stop:
                if 'WON' in e.subtypes and 'LOST' in e.subtypes:raise ValueError('Conflicting challenge outcomes')
                if 'WON' in e.subtypes:team=e.team
                elif 'LOST' in e.subtypes:team={'H':'A','A':'H'}.get(e.team,'')
                else:team=''
                points[end].append(('owner',team))
            if is_stop:points[end].append(('stop','D'))
        owner='X';dead=False
        for at in range(first,coverage_end+1):
            point=points.get(at,())
            restarts=[team for kind,team in point if kind=='restart']
            stops=any(kind=='stop' for kind,team in point)
            owners=[team for kind,team in point if kind=='owner']
            if restarts:
                teams=set(restarts);owner=next(iter(teams)) if len(teams)==1 and '' not in teams else 'X';dead=False
                conflicts+=int(owner=='X')
            elif stops:owner='D';dead=True
            elif not dead and owners:
                teams=set(owners);owner=next(iter(teams)) if len(teams)==1 and '' not in teams else 'X'
                conflicts+=int(owner=='X')
            labels[at]=owner
    summary=dict(events=len(events),ignored_card_events=sum(e.kind=='CARD' for e in events),missing_end_events=sum(e.missing_end for e in events),outside_events=len(events)-len(used),clipped_events=clipped,conflict_frames=conflicts,
        known_frames=sum(v!='X' for v in labels),label_counts={v:labels.count(v) for v in 'HADX'})
    return tuple(labels),summary
