"""Independent-provider features and phase reference; no reference-dependent inference filtering."""
from dataclasses import dataclass
from collections import Counter
import csv
import hashlib
import json
from math import isfinite
from pathlib import Path
import uuid

import numpy as np
from .motion import MotionFrame,motion_frame

_ADAPTER_SOURCES={name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
                  for name in ('skillcorner.py','motion.py')}


def _sha256(path):
    digest=hashlib.sha256()
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda:handle.read(4*1024*1024),b''):digest.update(chunk)
    return digest.hexdigest()


@dataclass
class MotionMatch:
    match_id: str
    records: list
    reference: object
    source_frames: object
    notes: dict
    native_ball_available: object=None
    native_periods: object=None
    native_reference: object=None

    def frames(self):return self.records

    @property
    def periods(self):return np.fromiter((f.period for f in self.records),dtype=np.uint8,count=len(self.records))


def _clock(value):
    parts=str(value).split(':')
    if len(parts)!=3:raise ValueError('tracking timestamp must be HH:MM:SS')
    h,m,s=map(float,parts)
    if not all(isfinite(x) and x>=0 for x in (h,m,s)) or m>=60 or s>=60:
        raise ValueError('invalid tracking clock')
    return h*3600+m*60+s


def _phase_clock(value):
    parts=str(value).split(':')
    if len(parts)==2:
        minute,second=map(float,parts)
        if not isfinite(minute) or not isfinite(second) or minute<0 or not 0<=second<60:raise ValueError('invalid phase clock')
        return minute*60+second
    return _clock(value)


def _position(value,detected_only):
    detected=value.get('is_detected')
    if detected is not None and type(detected) is not bool:
        raise ValueError('observation flag must be JSON boolean or null')
    x,y=value.get('x'),value.get('y')
    if x is None or y is None:return None
    if type(x) not in (int,float) or type(y) not in (int,float) or not isfinite(x) or not isfinite(y):
        raise ValueError('invalid external position')
    return (float(x),float(y)) if not detected_only or detected is True else None


def load_skillcorner(metadata_path,tracking_path,phases_path,detected_only=True):
    meta=json.loads(Path(metadata_path).read_text(encoding='utf-8-sig'))
    home,away=meta['home_team']['id'],meta['away_team']['id']
    if home==away:raise ValueError('external teams must be distinct')
    length,width=float(meta['pitch_length']),float(meta['pitch_width'])
    if not all(isfinite(x) and x>0 for x in (length,width)):raise ValueError('invalid external pitch')
    membership={}
    for player in meta['players']:
        person,team=player['id'],player['team_id']
        if person in membership or team not in (home,away):raise ValueError('invalid external roster membership')
        membership[person]=0 if team==home else 1
    def normalize(point):return ((point[0]/length+.5)*105.3,(point[1]/width+.5)*68.)
    native=[];previous=-1;origins={};groups=Counter();raw_periods=Counter();native_observed=0
    with open(tracking_path,encoding='utf-8-sig') as handle:
        for line in handle:
            row=json.loads(line)
            number=row['frame']
            if type(number) is not int or not previous<number<=1000000:
                raise ValueError('native frame IDs must increase without duplication')
            while len(native)<number:native.append(None)
            source_period=row.get('period');raw_periods[str(source_period)]+=1
            period=source_period if source_period in (1,2) else 0
            if period:
                time=_clock(row.get('timestamp'))
                origins.setdefault(period,time-number/10)
                if abs(time-(origins[period]+number/10))>.011:
                    raise ValueError('native tracking clock disagrees with 10 Hz indices')
            ball=_position(row.get('ball_data') or {},detected_only)
            players=[{},{}];seen=set()
            for player in row.get('player_data') or []:
                person=player.get('player_id')
                if person not in membership or person in seen:
                    raise ValueError('unknown/duplicate tracked player identity')
                seen.add(person)
                point=_position(player,detected_only)
                if point is not None:players[membership[person]][person]=normalize(point)
            groups[str((row.get('possession') or {}).get('group'))]+=1
            native_observed+=ball is not None
            native.append(dict(period=period,ball=normalize(ball) if ball is not None else None,
                               players=players,detected=(row.get('ball_data') or {}).get('is_detected') is True))
            previous=number
    if not native:raise ValueError('external tracking is empty')
    n=len(native);native_ref=np.full(n,3,dtype=np.uint8);annotated=np.zeros(n,dtype=bool);conflict=np.zeros(n,dtype=bool)
    period_conflict=np.zeros(n,dtype=bool);requested=np.zeros(n,dtype=bool);reconciliation=Counter()
    with open(phases_path,newline='',encoding='utf-8-sig') as handle:
        for row in csv.DictReader(handle):
            first,stop,period=int(row['frame_start']),int(row['frame_end']),int(row['period'])
            if first<0 or stop<first:raise ValueError('invalid phase interval')
            reconciliation['intervals_total']+=1
            if period not in (1,2):
                reconciliation['unsupported_period_intervals']+=1
                continue
            reconciliation['requested_native_frames']+=stop-first
            reconciliation['out_of_range_native_frames']+=max(0,stop-max(first,n))
            clock_bad=False
            if all(row.get(key) not in (None,'') for key in ('time_start','time_end','duration')):
                reconciliation['clock_checked_intervals']+=1
                try:
                    start_t,stop_t=_phase_clock(row['time_start']),_phase_clock(row['time_end'])
                    duration=float(row['duration'])
                    clock_bad=(period not in origins or not isfinite(duration)
                         or abs(start_t-(origins.get(period,0)+first/10))>.011
                         or abs(stop_t-(origins.get(period,0)+stop/10))>.011
                         or abs(duration-(stop-first)/10)>.011)
                except (TypeError,ValueError):clock_bad=True
                if clock_bad:reconciliation['clock_disagreement_intervals']+=1
            else:reconciliation['clock_unverified_intervals']+=1
            try:team=int(row['team_in_possession_id'])
            except (TypeError,ValueError):team=None
            code=0 if team==home else 1 if team==away else 3
            if code==3:reconciliation['invalid_team_intervals']+=1
            for i in range(first,min(stop,n)):
                requested[i]=True
                if native[i] is None:
                    reconciliation['missing_native_rows']+=1
                    continue
                if clock_bad:
                    conflict[i]=True;native_ref[i]=3
                    continue
                if native[i]['period']!=period:
                    period_conflict[i]=True;conflict[i]=True;native_ref[i]=3
                    continue
                if annotated[i] and native_ref[i]!=code:conflict[i]=True
                annotated[i]=True;native_ref[i]=3 if conflict[i] else code
    count=(n*5+1)//2
    records=[];reference=np.full(count,3,dtype=np.uint8);mapping=np.arange(count,dtype=np.float64)*.4
    empty=dict(period=0,ball=None,players=[{},{}],detected=False)
    def value_at(k):return native[k] if 0<=k<n and native[k] is not None else empty
    for k in range(count):
        index=(k*2)//5;fraction=(k*2%5)/5
        left=value_at(index);right=value_at(index+1);period=left['period']
        compatible=period!=0 and right['period']==period
        def interpolate(a,b):return tuple(x+(y-x)*fraction for x,y in zip(a,b))
        ball=(left['ball'] if fraction==0 else interpolate(left['ball'],right['ball'])
              if compatible and left['ball'] is not None and right['ball'] is not None else None)
        ball_interpolated=bool(fraction and ball is not None)
        provenance=('native_detected' if left['detected'] else 'provider_extrapolated') if ball is not None and not fraction else (
            'interpolated_detected' if left['detected'] and right['detected'] else 'interpolated_available') if ball is not None else 'missing'
        native_detection=bool(ball is not None and not fraction and left['detected'])
        sample_time=index/10 if ball is not None and not fraction else None
        players=[{},{}];player_interpolated=False
        for side in (0,1):
            if fraction==0:players[side]=dict(left['players'][side])
            elif compatible:
                players[side]={person:interpolate(point,right['players'][side][person])
                               for person,point in left['players'][side].items() if person in right['players'][side]}
                player_interpolated=player_interpolated or bool(players[side])
        # Isolated native samples may sit halfway between 25 Hz ticks. Retain one
        # at the following tick (<=.02 s), without filling the missing interval.
        nearest=(index*5+1)//2
        snap=k==nearest
        if snap and period:
            if ball is None and left['ball'] is not None:
                ball=left['ball'];ball_interpolated=False;native_detection=left['detected'];sample_time=index/10
                provenance='snapped_detected' if left['detected'] else 'provider_extrapolated'
            for side in (0,1):
                for person,point in left['players'][side].items():players[side].setdefault(person,point)
        members=[tuple(sorted(x)) for x in players]
        records.append(motion_frame(period,ball,
            tuple(players[0][p] for p in members[0]),tuple(players[1][p] for p in members[1]),*members,
            native_frame=index,ball_native_observation=native_detection,ball_provenance=provenance,
            ball_interpolated=ball_interpolated,ball_sample_time_s=sample_time,
            interpolated=bool(ball_interpolated or player_interpolated)))
        if period:reference[k]=native_ref[index]
    notes=dict(fps=25,native_fps=10,native_grid_rows=n,canonical_rows=count,
        native_numeric_positions_used=native_observed,raw_tracking_possession_groups=dict(groups),raw_period_counts=dict(raw_periods),
        position_regime='detected_only' if detected_only else 'available_including_extrapolation',
        reference_type='provider phase reference; known in-play H/A only; missing phases are unknown, not D',
        unknown_reference_preserved=True,reference_fields_excluded_from_features=True,
        resampling='linear only across consecutive available native samples within period; isolated samples snapped <=.02s',
        phase_interval='left closed, right open; native frame IDs',canonical_pitch_m=[105.3,68.])
    notes['phase_period_conflict_native_frames']=int(period_conflict.sum())
    reconciliation['requested_unique_native_frames']=int(requested.sum())
    reconciliation['assigned_known_reference_native_frames']=int((native_ref<2).sum())
    reconciliation['conflicting_native_frames']=int(conflict.sum())
    reconciliation['retained_reference_fraction']=float((native_ref<2).sum()/requested.sum()) if requested.any() else 0.
    notes['phase_reconciliation']=dict(reconciliation)
    notes['input_sha256']={Path(p).name:_sha256(p) for p in (metadata_path,tracking_path,phases_path)}
    notes['ball_sample_time_definition']='source-frame elapsed seconds, not match clock; absent for synthetic blends'
    return MotionMatch(str(meta['id']),records,reference,mapping,notes,
        np.asarray([r is not None and r['ball'] is not None for r in native],dtype=bool),
        np.asarray([r['period'] if r is not None else 0 for r in native],dtype=np.uint8),native_ref)


def save_motion_cache(match,prefix):
    prefix=Path(prefix);prefix.parent.mkdir(parents=True,exist_ok=True)
    frames=match.frames();n=len(frames)
    generation=uuid.uuid4().hex
    identity=dict(match_id=match.match_id,position_regime=match.notes['position_regime'],
                  input_sha256=match.notes.get('input_sha256',{}),adapter_sources=_ADAPTER_SOURCES)
    identity_digest=hashlib.sha256(json.dumps(identity,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    shared=dict(generation_id=np.asarray(generation),input_identity=np.asarray(identity_digest),
                match_id=np.asarray(match.match_id),position_regime=np.asarray(match.notes['position_regime']))
    arrays=dict(periods=match.periods,source_frames=np.asarray(match.source_frames,dtype=np.float64),
        ball=np.asarray([(f.ball_x if f.ball_x is not None else np.nan,f.ball_y if f.ball_y is not None else np.nan) for f in frames]),
        flags=np.asarray([(f.geometry_valid,2 if f.ball_native_observation is None else f.ball_native_observation,
                           f.interpolated,f.ball_interpolated) for f in frames],dtype=np.uint8),
        ball_provenance=np.asarray([f.ball_provenance for f in frames]),
        ball_sample_time=np.asarray([f.ball_sample_time_s if f.ball_sample_time_s is not None else np.nan for f in frames]),
        native_frame=np.asarray([f.native_frame if f.native_frame is not None else -1 for f in frames],dtype=np.int32),**shared)
    if match.native_ball_available is not None:
        arrays.update(native_ball_available=match.native_ball_available,native_periods=match.native_periods)
    for side in ('home','away'):
        maximum=max((len(getattr(f,side+'_xy')) for f in frames),default=0)
        xy=np.full((n,maximum,2),np.nan,dtype=np.float64);ids=np.full((n,maximum),-1,dtype=np.int64)
        counts=np.zeros(n,dtype=np.uint8)
        for i,f in enumerate(frames):
            points=getattr(f,side+'_xy');members=getattr(f,side+'_ids');counts[i]=len(points)
            if points:xy[i,:len(points)]=points;ids[i,:len(points)]=members
        arrays[side+'_xy']=xy;arrays[side+'_ids']=ids;arrays[side+'_count']=counts
    def publish_npz(suffix,values):
        target=Path(str(prefix)+suffix);temporary=Path(str(target)+'.new')
        with temporary.open('wb') as handle:np.savez_compressed(handle,**values)
        temporary.replace(target)
    publish_npz('.features.npz',arrays)
    targets=dict(reference=match.reference,periods=match.periods,source_frames=match.source_frames,**shared)
    if match.native_reference is not None:targets['native_reference']=match.native_reference
    publish_npz('.reference.npz',targets)
    array_hashes={suffix:_sha256(str(prefix)+suffix) for suffix in ('.features.npz','.reference.npz')}
    target=Path(str(prefix)+'.metadata.json');temporary=Path(str(target)+'.new')
    temporary.write_text(json.dumps(dict(schema_version=2,match_id=match.match_id,notes=match.notes,
        adapter_sources=_ADAPTER_SOURCES,generation_id=generation,input_identity=identity_digest,
        position_regime=match.notes['position_regime'],array_sha256=array_hashes),indent=2)+'\n',encoding='utf-8')
    temporary.replace(target)


def load_motion_cache(prefix):
    prefix=str(prefix);metadata=json.loads(Path(prefix+'.metadata.json').read_text(encoding='utf-8'))
    if metadata.get('adapter_sources')!=_ADAPTER_SOURCES:raise ValueError('Motion cache was built by a different adapter; rebuild from verified raw sources')
    if metadata.get('schema_version')!=2 or metadata['position_regime']!=metadata['notes']['position_regime']:
        raise ValueError('Motion cache provenance schema/regime disagree')
    for suffix in ('.features.npz','.reference.npz'):
        if _sha256(prefix+suffix)!=metadata['array_sha256'][suffix]:raise ValueError('Motion cache generation content changed')
    with np.load(prefix+'.features.npz',allow_pickle=False) as feature_archive,np.load(prefix+'.reference.npz',allow_pickle=False) as reference_archive:
        features={key:feature_archive[key] for key in feature_archive.files}
        target={key:reference_archive[key] for key in reference_archive.files}
        for field in ('generation_id','input_identity','match_id','position_regime'):
            if any(str(a[field].item())!=str(metadata[field]) for a in (features,target)):
                raise ValueError('Motion cache generation identities disagree')
        if any(not np.array_equal(features[k],target[k]) for k in ('periods','source_frames')):
            raise ValueError('motion feature/reference cache indices disagree')
        records=[]
        for i,period in enumerate(features['periods']):
            players=[];members=[]
            for side in ('home','away'):
                count=int(features[side+'_count'][i]);players.append(tuple(map(tuple,features[side+'_xy'][i,:count])))
                members.append(tuple(map(int,features[side+'_ids'][i,:count])))
            ball=tuple(features['ball'][i]) if np.isfinite(features['ball'][i]).all() else None
            flags=features['flags'][i];native=int(features['native_frame'][i]);sample_time=float(features['ball_sample_time'][i])
            records.append(motion_frame(int(period),ball,*players,*members,geometry_valid=bool(flags[0]),
                ball_native_observation=None if flags[1]==2 else bool(flags[1]),interpolated=bool(flags[2]),
                ball_interpolated=bool(flags[3]),ball_provenance=str(features['ball_provenance'][i]),
                ball_sample_time_s=sample_time if isfinite(sample_time) else None,native_frame=native if native>=0 else None))
        return MotionMatch(metadata['match_id'],records,target['reference'].copy(),features['source_frames'].copy(),metadata['notes'],
            features['native_ball_available'].copy() if 'native_ball_available' in features else None,
            features['native_periods'].copy() if 'native_periods' in features else None,
            target['native_reference'].copy() if 'native_reference' in target else None)
