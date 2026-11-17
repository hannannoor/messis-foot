"""Pinned public WCSF acquisition; streaming geometry/reference isolation."""
from dataclasses import dataclass
from contextlib import closing
from datetime import datetime,timezone
from decimal import Decimal,InvalidOperation
from pathlib import Path,PurePosixPath,PureWindowsPath
import csv
import hashlib
import io
import json
import math
import shutil
import sqlite3
import urllib.request
import zipfile

REV='1c9ba798f98a9fffb16081a5d3965774d4e5662c'
ASSETS=(('positions_FIRST_HALF.csv.zip','d7de2a38f5650150684b1008aa7f4fd28b85d777',22704565),
        ('positions_SECOND_HALF.csv.zip','66fc3ee2966aaf3392d4a327ba3f49385e9c7032',23746663))
GEOMETRY=('x','y','group_id','timestamp_ms','x_ball','y_ball','player_id')
REQUIRED=GEOMETRY+('AliveFlag','PossessionFlag')


@dataclass(frozen=True)
class SourcePaths:
    archives:tuple
    geometry_db:Path
    reference_db:Path
    access_log:Path
    protocol_sha256:str=''


def event(path,name,**counts):
    with Path(path).open('a',encoding='utf-8') as f:
        f.write(json.dumps(dict(event=name,timestamp_utc=datetime.now(timezone.utc).isoformat(),**counts),allow_nan=False)+'\n')


def _csv_member(path):
    with zipfile.ZipFile(path) as z:
        infos=z.infolist();names=[i.filename for i in infos]
        if len(names)!=len(set(names)):raise ValueError('Duplicate ZIP member')
        if sum(i.file_size for i in infos)>2000000000:raise ValueError('ZIP size limit exceeded')
        files=[];metadata=[]
        for info in infos:
            p=PurePosixPath(info.filename.replace('\\','/'))
            if p.is_absolute() or PureWindowsPath(info.filename).drive or '..' in p.parts:
                raise ValueError('Unsafe ZIP path')
            if info.flag_bits&1 or (info.external_attr>>16)&0o170000==0o120000:
                raise ValueError('Encrypted/linked ZIP member')
            if info.file_size/max(1,info.compress_size)>200:raise ValueError('ZIP ratio limit exceeded')
            if info.is_dir():continue
            if p.parts[0]=='__MACOSX' and p.name.startswith('._'):
                metadata.append(info);continue
            if p.suffix.lower()!='.csv':raise ValueError('Unexpected ZIP member type')
            files.append(info.filename)
        if len(files)!=1:raise ValueError('Expected one CSV member')
        if len(metadata)>1:raise ValueError('Unexpected metadata sidecar count')
        basename=PurePosixPath(files[0].replace('\\','/')).name
        for info in metadata:
            if info.filename!=f'__MACOSX/._{basename}' or not 4<=info.file_size<=4096:
                raise ValueError('Unexpected metadata sidecar identity/size')
            with z.open(info) as f:
                if f.read(4)!=b'\x00\x05\x16\x07':raise ValueError('Unexpected metadata header')
        return files[0]


def validate_archive(path,expected_blob,expected_bytes):
    path=Path(path)
    if path.stat().st_size!=expected_bytes:raise ValueError('Archive byte identity mismatch')
    h=hashlib.sha1(b'blob '+str(expected_bytes).encode()+b'\0')
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    if h.hexdigest()!=expected_blob:raise ValueError('Archive Git blob mismatch')
    return _csv_member(path)


def acquire(generation):
    from gap_solver.input_contract import reject_linked_ancestors
    generation=Path(generation);reject_linked_ancestors(generation)
    if generation.exists():raise FileExistsError('Preserve existing private generation')
    ancestor=generation.parent
    while not ancestor.exists():ancestor=ancestor.parent
    if shutil.disk_usage(ancestor).free<3000000000:raise ValueError('Insufficient disk headroom')
    generation.parent.mkdir(parents=True,exist_ok=True);generation.mkdir()
    paths=[]
    for name,blob,size in ASSETS:
        path=generation/name
        url=f'https://raw.githubusercontent.com/MatKempeGroningen/WCSF_SolutionRoom/{REV}/{name}'
        request=urllib.request.Request(url,headers={'User-Agent':'MESSIs-FOOT-licensed-WCSF-audit'})
        with urllib.request.urlopen(request,timeout=40) as response,path.open('xb') as f:
            total=0
            for block in iter(lambda:response.read(1024*1024),b''):
                total+=len(block)
                if total>size:raise ValueError('Archive transfer exceeds pinned bytes')
                f.write(block)
        validate_archive(path,blob,size);paths.append(path)
    return tuple(paths)


def _integer(value,low,high):
    try:
        n=Decimal(value.strip())
        if not n.is_finite() or n!=n.to_integral_value() or not low<=n<=high:raise ValueError()
        return int(n)
    except (InvalidOperation,AttributeError,ValueError):raise ValueError('Invalid source key/clock') from None


def _coordinate(value):
    if value is None or not value.strip():return None
    try:v=float(value)
    except ValueError:raise ValueError('Invalid coordinate encoding') from None
    return v if math.isfinite(v) else None


def ingest(paths):
    from gap_solver.input_contract import reject_linked_ancestors
    for p in (paths.geometry_db,paths.reference_db,paths.access_log):
        reject_linked_ancestors(p)
        if Path(p).exists():raise FileExistsError('Preserve source-store generation')
    if len(paths.archives)!=2:raise ValueError('Exactly two archive periods required')
    # Exclusive placeholders prevent SQLite from opening an existing generation.
    for p in (paths.geometry_db,paths.reference_db):Path(p).open('xb').close()
    event(paths.access_log,'machine_reference_access',source_periods=2,protocol_hash=paths.protocol_sha256 or None,
          source_commit=REV,actor='local_adapter',purpose='quarantined_ingestion')
    count=duplicates=0;membership={}
    with closing(sqlite3.connect(paths.geometry_db)) as geo,closing(sqlite3.connect(paths.reference_db)) as ref:
        geo.execute('create table geometry (period integer,t integer,team integer,player integer,x real,y real,bx real,by real,primary key(period,t,team,player))')
        ref.execute('create table annotations (period integer,ordinal integer,t integer,team integer,player integer,alive text,owner text,primary key(period,ordinal))')
        ref.execute('create index annotation_times on annotations(period,t)')
        for period,path in enumerate(paths.archives,1):
            member=_csv_member(path);ordinal=0
            with zipfile.ZipFile(path) as z,z.open(member) as raw,io.TextIOWrapper(raw,encoding='utf-8-sig',newline='') as text:
                header=text.readline();options=[]
                for delimiter in (',',';','\t'):
                    names=[n.strip() for n in next(csv.reader([header],delimiter=delimiter))]
                    if set(REQUIRED)<=set(names) and len(names)==len(set(names)):options.append((delimiter,names))
                if len(options)!=1:raise ValueError('Ambiguous or missing CSV headers')
                delimiter,names=options[0];reader=csv.DictReader(text,fieldnames=names,delimiter=delimiter)
                for row in reader:
                    if None in row or any(row.get(k) is None for k in REQUIRED):raise ValueError('Malformed CSV row shape')
                    ordinal+=1;t=_integer(row['timestamp_ms'],0,86400000);team=_integer(row['group_id'],1,2)
                    player=_integer(row['player_id'],0,2**63-1)
                    if player in membership and membership[player]!=team:raise ValueError('Anonymous player changed team')
                    membership[player]=team
                    values=tuple(_coordinate(row[k]) for k in ('x','y','x_ball','y_ball'))
                    key=(period,t,team,player)
                    old=geo.execute('select x,y,bx,by from geometry where period=? and t=? and team=? and player=?',key).fetchone()
                    if old is not None:
                        if tuple(old)!=values:raise ValueError('Conflicting duplicate geometry')
                        duplicates+=1
                    else:geo.execute('insert into geometry values (?,?,?,?,?,?,?,?)',key+values)
                    ref.execute('insert into annotations values (?,?,?,?,?,?,?)',(period,ordinal,t,team,player,row['AliveFlag'].strip(),row['PossessionFlag'].strip()))
                    count+=1
                    if count%10000==0:geo.commit();ref.commit()
            times=[r[0] for r in geo.execute('select distinct t from geometry where period=? order by t',(period,))]
            if not times or times[-1]-times[0]>5400000 or any((t-times[0])%100 for t in times):
                raise ValueError('Invalid source cadence/extent')
        geo.commit();ref.commit()
    return dict(source_rows=count,identical_geometry_duplicates=duplicates)
