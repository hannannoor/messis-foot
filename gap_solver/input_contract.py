"""Strict channel-referenced EPTS ingestion. No labels or video are consumed."""
import csv
import hashlib
import math
import json
import stat
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

from .io import BLOCKS
from .motion import motion_frame


@dataclass(frozen=True)
class EPTSContract:
    sides: tuple
    rows: int
    speed_unit: str
    legacy_slot_order_matches: bool
    metadata_pitch: tuple
    legacy_team_order_matches: bool
    legacy_slot_roles_match: bool


def sha256(path):
    digest=hashlib.sha256()
    with open(path,'rb') as handle:
        for chunk in iter(lambda:handle.read(1024*1024),b''): digest.update(chunk)
    return digest.hexdigest()


def _unique(elements):
    result={}
    for e in elements:
        key=e.get('id')
        if not key or key in result: raise ValueError('Missing or duplicate EPTS identifier')
        result[key]=e
    return result


def read_epts_contract(path):
    root=ET.parse(path).getroot()
    if [float(e.text) for e in root.iter('FrameRate')]!=[25.]: raise ValueError('Expected declared 25Hz EPTS')
    teams=_unique(root.iter('Team'));roles={}
    aliases={'barcelona':'H','fcbarcelona':'H','athleticclub':'A','atleticclub':'A'}
    for key,t in teams.items():
        role=aliases.get(''.join(c for c in (t.findtext('Name') or '').lower() if c.isalnum()))
        if role is None or role in roles.values(): raise ValueError('Unresolved or ambiguous documented team role')
        roles[key]=role
    if set(roles.values())!={'H','A'}: raise ValueError('Expected two documented teams')
    players=_unique(root.iter('Player'));channels=_unique(root.iter('Channel'));pc=_unique(root.iter('PlayerChannel'))
    for p in players.values():
        if p.get('teamId') not in roles: raise ValueError('Unknown player team reference')
    kinds={};units={}
    for key,c in channels.items():
        name=c.findtext('Name');unit=c.findtext('Unit')
        kind={'position_x':'x','position_y':'y','speed_kph':'s','speed_mps':'s'}.get(name)
        if kind is None or kind in kinds.values(): raise ValueError('Unsupported or duplicate EPTS channel')
        if kind in 'xy' and unit!='normalized': raise ValueError('Coordinates must be declared normalized')
        if kind=='s' and (name,unit) not in (('speed_kph','kph'),('speed_mps','m/s')): raise ValueError('Unknown speed units')
        kinds[key]=kind;units[kind]=unit
    if set(kinds.values())!=set('xys'): raise ValueError('Incomplete channels')
    specs=list(root.iter('DataFormatSpecification'))
    if len(specs)!=1: raise ValueError('Exactly one data format specification required')
    spec=specs[0];parts=list(spec)
    if spec.get('separator')!=':' or spec.get('startFrame')!='1' or len(parts)!=3: raise ValueError('Unsupported source indexing/register layout')
    rows=int(spec.get('endFrame','0'))
    if rows<1 or parts[0].tag!='StringRegister' or parts[0].get('name')!='frameCount': raise ValueError('Invalid frame count register')
    if parts[1].tag!='SplitRegister' or parts[1].get('separator')!=';': raise ValueError('Invalid player split')
    order=[]
    for triple in parts[1]:
        if triple.tag!='SplitRegister' or triple.get('separator')!=',' or len(triple)!=3: raise ValueError('Invalid player triple')
        refs=[]
        for e in triple:
            if e.tag!='PlayerChannelRef' or e.get('playerChannelId') not in pc: raise ValueError('Broken player channel reference')
            refs.append(pc[e.get('playerChannelId')])
        ids={e.get('playerId') for e in refs}
        if len(ids)!=1 or next(iter(ids)) not in players or [kinds.get(e.get('channelId')) for e in refs]!=list('xys'):
            raise ValueError('Player triple must reference one player in x,y,s order')
        order.append(next(iter(ids)))
    ball=parts[2]
    if ball.tag!='SplitRegister' or ball.get('separator')!=',' or [kinds.get(e.get('channelId')) if e.tag=='BallChannelRef' else None for e in ball]!=list('xys'):
        raise ValueError('Invalid ball register')
    if len(order)!=len(players) or set(order)!=set(players): raise ValueError('Player registers must cover each slot once')
    field=list(root.iter('FieldSize'))
    if len(field)!=1: raise ValueError('Missing pitch dimensions')
    pitch=(float(field[0].findtext('Width')),float(field[0].findtext('Height')))
    if pitch!=(105.,68.): raise ValueError('Unexpected metadata pitch contract')
    sides=tuple(roles[players[p].get('teamId')] for p in order)
    if set(sides)!={'H','A'}:raise ValueError('Registered slots must include both teams')
    legacy=tuple('H' if p.get('teamId')==next(iter(teams)) else 'A' for p in players.values())
    return EPTSContract(sides,rows,units['s'],order==list(players),pitch,roles[next(iter(teams))]=='H',sides==legacy)


def _number(value):
    if value.strip().lower() in ('','nan'): return None
    try: result=float(value)
    except ValueError: raise ValueError('Malformed ATD numeric value') from None
    if not math.isfinite(result): raise ValueError('Nonfinite ATD value other than missing NaN')
    return result


def iter_records(contract,path,blocks=None):
    """Yield canonical metres; speed is validated but deliberately unused."""
    blocks=BLOCKS if blocks is None else blocks
    count=0
    with open(path,encoding='utf-8-sig') as handle:
        for i,line in enumerate(handle):
            parts=line.strip().split(':')
            if len(parts)!=3 or parts[0]!=str(i+1) or i>=contract.rows: raise ValueError('Noncontiguous original ATD indices')
            slots=parts[1].split(';')
            if len(slots)!=len(contract.sides): raise ValueError('Wrong ATD slot count')
            def point(text):
                xyz=text.split(',')
                if len(xyz)!=3: raise ValueError('Wrong ATD triple size')
                x,y,s=map(_number,xyz)
                if (x is None)!=(y is None): raise ValueError('Partial XY observation')
                return None if x is None else (x*105.3,y*68.)
            home=[];away=[]
            for side,text in zip(contract.sides,slots):
                xy=point(text)
                if xy is not None: (home if side=='H' else away).append(xy)
            ball=point(parts[2]);period=next((p for p,a,b in blocks if a<=i<=b),0)
            yield motion_frame(period,ball,home,away,native_frame=i,ball_sample_time_s=i/25 if ball is not None else None)
            count+=1
    if count!=contract.rows: raise ValueError('ATD row count differs from metadata')


def quality_mask(path,rows):
    """Preserve incumbent engineering gate; it is not ATD observation validation."""
    required=['frame','valid','reprojection_error']+['h'+str(a)+str(b) for a in range(3) for b in range(3)]
    mask=[]
    with open(path,newline='',encoding='utf-8-sig') as handle:
        reader=csv.reader(handle);header=next(reader,[])
        if len(header)!=len(set(header)) or not set(required)<=set(header):raise ValueError('Invalid homography header')
        for i,values in enumerate(reader):
            if len(values)!=len(header):raise ValueError('Invalid homography row width')
            row=dict(zip(header,values))
            if row['frame']!=str(i) or i>=rows:raise ValueError('Noncontiguous original homography indices')
            if row['valid'] not in ('0','1'):raise ValueError('Invalid homography flag')
            matrix=[_number(row[k]) for k in required[3:]];error=_number(row['reprojection_error'])
            accepted=row['valid']=='1' and all(v is not None for v in matrix)
            if accepted:
                a,b,c,d,e,f,g,h,j=matrix;scale=max(abs(v) for v in matrix)
                determinant=a*(e*j-f*h)-b*(d*j-f*g)+c*(d*h-e*g)
                accepted=scale>0 and abs(determinant)>1e-12*scale**3
            mask.append(accepted and error is not None and 0<=error<=3.)
    if len(mask)!=rows:raise ValueError('Homography row count differs from metadata')
    return mask


def reject_linked_ancestors(path):
    """lstat reparse flags work on Windows before Path.is_junction existed."""
    path=Path(path)
    for part in (path,*path.parents):
        try:info=part.lstat()
        except FileNotFoundError:continue
        if stat.S_ISLNK(info.st_mode) or getattr(info,'st_file_attributes',0)&getattr(stat,'FILE_ATTRIBUTE_REPARSE_POINT',1024):
            raise ValueError('Output path must not traverse links or reparse points')


def protect_report_path(path,inputs):
    path=Path(path);reject_linked_ancestors(path)
    for source in map(Path,inputs):
        if path.resolve()==source.resolve() or path.exists() and source.exists() and path.samefile(source):raise ValueError('Report cannot replace input alias')
    if path.exists():raise FileExistsError('Use a new aggregate report path')


def write_new_report(path,value,inputs):
    path=Path(path);protect_report_path(path,inputs);path.parent.mkdir(parents=True,exist_ok=True)
    protect_report_path(path,inputs)
    with path.open('x',encoding='utf-8') as handle:json.dump(value,handle,indent=2,allow_nan=False);handle.write('\n')


def audit_source(meta,raw,quality,scope):
    if scope not in ('tactical','broadcast'): raise ValueError('Unknown source scope')
    c=read_epts_contract(meta);mask=quality_mask(quality,c.rows)
    counts=dict(ball_available=0,player_points=0,players_without_ball=0,repeated_adjacent_ball_xy=0,repeated_adjacent_player_xy=0,outside_normalized_pitch_points=0,active_rows=0)
    previous_ball=None;previous_points=set()
    for f in iter_records(c,raw,blocks=() if scope=='broadcast' else None):
        ball=(f.ball_x,f.ball_y) if f.ball_observed else None
        points={(side,x,y) for side,pts in [('H',f.home_xy),('A',f.away_xy)] for x,y in pts}
        counts['ball_available']+=ball is not None;counts['player_points']+=len(f.home_xy)+len(f.away_xy)
        counts['players_without_ball']+=ball is None and bool(points)
        counts['repeated_adjacent_ball_xy']+=ball is not None and ball==previous_ball
        counts['repeated_adjacent_player_xy']+=len(points & previous_points)
        counts['outside_normalized_pitch_points']+=sum(not (0<=x<=105.3 and 0<=y<=68) for _,x,y in points)
        counts['active_rows']+=bool(f.period);previous_ball=ball;previous_points=points
    return dict(schema_version=1,scope=scope,rows=c.rows,slots=len(c.sides),fps=25,source_start_index=1,output_start_index=0,
        metadata_pitch_m=list(c.metadata_pitch),canonical_pitch_m=[105.3,68.],coordinates='normalized_to_canonical_metres',
        declared_speed_unit=c.speed_unit,documented_speed_unit='m/s',speed_unit_conflict=c.speed_unit!='m/s',source_speed_used=False,
        role_mapping='documented team names resolved through channel references',legacy_slot_order_matches=c.legacy_slot_order_matches,
        legacy_team_order_matches=c.legacy_team_order_matches,legacy_slot_roles_match=c.legacy_slot_roles_match,
        player_identity_available=False,freshness_verified=False,repetition_proves_staleness=False,
        homography_accepted=sum(mask),homography_rejected=len(mask)-sum(mask),homography_max_error=3.,
        homography_scope='pitch-to-pixel transform quality; not independent pitch-observation validation',
        broadcast_clock_aligned=False,input_sha256={n:sha256(p) for n,p in [('metadata',meta),('tracking',raw),('homography',quality)]},**counts)
