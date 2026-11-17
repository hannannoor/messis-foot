"""Strict canonical geometry adapters for the three pinned public Metrica samples."""
import csv,json
from itertools import zip_longest
from math import isfinite
from pathlib import Path
import xml.etree.ElementTree as ET
from gap_solver.motion import motion_frame
from metrica_event_reference import normalize_csv,normalize_json


def _number(value):
    if value.strip().lower() in ('','nan'):return None
    result=float(value)
    if not isfinite(result):raise ValueError('Nonfinite sample coordinate')
    return result


def _point(values):
    if len(values)!=2:raise ValueError('Expected x/y pair')
    x,y=map(_number,values)
    return None if x is None or y is None else (x*105.3,y*68.)


def _csv_side(path,side):
    with Path(path).open(newline='',encoding='utf-8-sig') as handle:
        reader=csv.reader(handle);roles,numbers,names=(next(reader) for _ in range(3));width=len(names)
        if (names[:3]!=['Period','Frame','Time [s]'] or width<7 or (width-5)%2 or len(roles)!=width or len(numbers)!=width or names[-2].strip()!='Ball'):
            raise ValueError('Unsupported sample CSV schema')
        slots=list(range(3,width-2,2));ids=[numbers[j].strip() for j in slots]
        if any(not value for value in ids) or len(set(ids))!=len(ids) or any(roles[j].strip().upper()!=side.upper() for j in slots):raise ValueError('Invalid sample team/identity header')
        count=0
        for row in reader:
            count+=1
            if len(row)!=width:raise ValueError('Sample CSV row width changed')
            period,frame,time=int(row[0]),int(row[1]),float(row[2])
            if period not in (1,2) or frame!=count or not isfinite(time) or abs(time-frame/25)>1e-6:raise ValueError('Sample CSV clock/index mismatch')
            points=[];members=[]
            for j,identifier in zip(slots,ids):
                point=_point(row[j:j+2])
                if point is not None:points.append(point);members.append(identifier)
            yield frame,period,time,_point(row[-2:]),tuple(points),tuple(members)


def load_csv_tracking(home,away):
    frames=[];sentinel=object()
    for h,a in zip_longest(_csv_side(home,'Home'),_csv_side(away,'Away'),fillvalue=sentinel):
        if h is sentinel or a is sentinel or h[:3]!=a[:3]:raise ValueError('Sample team clocks differ')
        if h[3] is not None and a[3] is not None and h[3]!=a[3]:raise ValueError('Duplicate ball streams disagree')
        ball=h[3] if a[3] is not None else None
        frames.append(motion_frame(h[1],ball,h[4],a[4],h[5],a[5],native_frame=h[0]-1,ball_sample_time_s=h[2] if ball is not None else None,
            ball_native_observation=ball is not None,ball_provenance='public_corrected_sample'))
    if not frames:raise ValueError('Empty sample tracking')
    return frames


def _epts_metadata(path):
    root=ET.parse(path).getroot()
    if [float(e.text) for e in root.iter('FrameRate')]!=[25.]:raise ValueError('Sample EPTS must declare25Hz')
    fields=list(root.iter('FieldSize'))
    if len(fields)!=1 or (float(fields[0].findtext('Width')),float(fields[0].findtext('Height')))!=(105.,68.):raise ValueError('Unexpected sample pitch')
    teams=[e.get('id') for e in root.iter('Team')]
    if len(teams)!=2 or len(set(teams))!=2:raise ValueError('Expected two sample teams')
    mapping=dict(zip(teams,'HA'));players={}
    for e in root.iter('Player'):
        identifier=e.get('id')
        if not identifier or identifier in players or e.get('teamId') not in mapping:raise ValueError('Invalid EPTS player metadata')
        players[identifier]=mapping[e.get('teamId')]
    channels={}
    for e in root.iter('Channel'):
        axis={'position_x':'x','position_y':'y'}.get(e.findtext('Name'))
        if axis is None or e.findtext('Unit')!='normalized' or e.get('id') in channels:raise ValueError('Unsupported EPTS channel')
        channels[e.get('id')]=axis
    if set(channels.values())!={'x','y'}:raise ValueError('Incomplete sample channels')
    pc={}
    for e in root.iter('PlayerChannel'):
        key=e.get('id');person=e.get('playerId');axis=channels.get(e.get('channelId'))
        if not key or key in pc or person not in players or axis is None:raise ValueError('Invalid player channel reference')
        pc[key]=(person,axis)
    periods={}
    for e in root.iter('ProviderParameter'):
        name=e.findtext('Name');value=e.findtext('Value')
        if name in ('first_half_start','first_half_end','second_half_start','second_half_end'):
            if name in periods:raise ValueError('Duplicate period metadata')
            periods[name]=int(value)
        elif name in ('first_extra_half_start','second_extra_half_start') and value and value.strip():raise ValueError('Extra sample periods unsupported')
    bounds=[]
    for period,prefix in ((1,'first'),(2,'second')):
        first,last=periods[prefix+'_half_start'],periods[prefix+'_half_end']
        if not 1<=first<=last:raise ValueError('Invalid period range')
        bounds.append((period,first,last))
    if bounds[0][2]>=bounds[1][1]:raise ValueError('Overlapping period ranges')
    specs=[];previous=0
    for spec in root.iter('DataFormatSpecification'):
        first,last=int(spec.get('startFrame')),int(spec.get('endFrame'));parts=list(spec)
        if first!=previous+1 or last<first or spec.get('separator')!=':' or len(parts)!=3 or parts[0].tag!='StringRegister' or parts[0].get('name')!='frameCount':raise ValueError('Invalid EPTS format ranges')
        if parts[1].get('separator')!=';' or parts[2].get('separator')!=',':raise ValueError('Unsupported sample separators')
        slots=[]
        for pair in parts[1]:
            if pair.get('separator')!=',' or len(pair)!=2:raise ValueError('Unsupported player coordinate layout')
            refs=[pc.get(e.get('playerChannelId')) if e.tag=='PlayerChannelRef' else None for e in pair]
            if any(v is None for v in refs) or refs[0][0]!=refs[1][0] or [v[1] for v in refs]!=['x','y']:raise ValueError('Broken x/y identity reference')
            identifier=refs[0][0];slots.append((players[identifier],identifier))
        if len({pid for side,pid in slots})!=len(slots):raise ValueError('Duplicate sample player slot')
        if [channels.get(e.get('channelId')) if e.tag=='BallChannelRef' else None for e in parts[2]]!=['x','y']:raise ValueError('Broken sample ball channel')
        specs.append((first,last,tuple(slots)));previous=last
    if not specs or previous!=bounds[-1][2]:raise ValueError('Incomplete sample format coverage')
    return mapping,bounds,specs


def load_epts_tracking(metadata,tracking):
    mapping,bounds,specs=_epts_metadata(metadata);frames=[];at=0
    with Path(tracking).open(encoding='utf-8-sig') as handle:
        for count,line in enumerate(handle,1):
            parts=line.strip().split(':')
            if len(parts)!=3 or int(parts[0])!=count:raise ValueError('Sample EPTS index mismatch')
            while at<len(specs) and count>specs[at][1]:at+=1
            if at==len(specs) or count<specs[at][0]:raise ValueError('Sample frame outside declared layout')
            slots=specs[at][2];values=parts[1].split(';')
            if len(values)!=len(slots):raise ValueError('Sample EPTS slot count mismatch')
            points=[[],[]];ids=[[],[]]
            for value,(side,identifier) in zip(values,slots):
                point=_point(value.split(','))
                if point is not None:
                    j='HA'.index(side);points[j].append(point);ids[j].append(identifier)
            period=next((p for p,first,last in bounds if first<=count<=last),0)
            ball=_point(parts[2].split(','))
            frames.append(motion_frame(period,ball,*points,*ids,native_frame=count-1,ball_sample_time_s=count/25 if ball is not None else None,
                ball_native_observation=ball is not None,ball_provenance='public_corrected_sample'))
    if len(frames)!=specs[-1][1]:raise ValueError('Incomplete sample tracking file')
    return frames,mapping


def load_game(directory,game):
    root=Path(directory)/'data'/game
    if game in ('Sample_Game_1','Sample_Game_2'):
        return load_csv_tracking(root/(game+'_RawTrackingData_Home_Team.csv'),root/(game+'_RawTrackingData_Away_Team.csv')),{'Home':'H','Away':'A'}
    if game=='Sample_Game_3':return load_epts_tracking(root/(game+'_metadata.xml'),root/(game+'_tracking.txt'))
    raise ValueError('Undeclared sample game')


def load_events(directory,game,team_map):
    root=Path(directory)/'data'/game
    if game in ('Sample_Game_1','Sample_Game_2'):
        with (root/(game+'_RawEventsData.csv')).open(newline='',encoding='utf-8-sig') as handle:return [normalize_csv(row) for row in csv.DictReader(handle)]
    if game=='Sample_Game_3':return [normalize_json(row,team_map) for row in json.loads((root/(game+'_events.json')).read_text(encoding='utf-8'))['data']]
    raise ValueError('Undeclared event source')
