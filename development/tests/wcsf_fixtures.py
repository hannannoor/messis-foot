"""Synthetic anonymous geometry and ZIPs; never external match assets."""
from pathlib import Path
import csv
import io
import zipfile
from contextlib import contextmanager
import hashlib
from unittest.mock import patch

HEADERS = ('x','y','group_id','timestamp_ms','x_ball','y_ball','player_id','AliveFlag','PossessionFlag')


def rows(n=101, hypothesis='absolute-x', period=1):
    result=[]
    for i in range(n):
        ball=(10+i*.03, 4+i*.01)
        for team in (1,2):
            for j in range(3):
                # Source players are in their own negative-goal frame.
                x=-20+j*4+i*.02; y=-8+j*6+i*.005
                bx,by=ball
                if team==2:
                    bx=-bx
                    if hypothesis.endswith('-xy'):by=-by
                if hypothesis.startswith('offset-'):bx-=x;by-=y
                result.append(dict(zip(HEADERS,(x,y,team,i*100,bx,by,team*100+j,1,1))))
    return result


def csv_zip(path, records, delimiter=',', bom=False, member='positions.csv'):
    text=io.StringIO();writer=csv.DictWriter(text,HEADERS,delimiter=delimiter)
    writer.writeheader();writer.writerows(records)
    data=text.getvalue().encode('utf-8-sig' if bom else 'utf-8')
    with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED) as z:z.writestr(member,data)
    return Path(path)


def source_paths(folder, first=None, second=None):
    from wcsf_source import SourcePaths
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    archives=(csv_zip(folder/'first.zip',rows() if first is None else first),
              csv_zip(folder/'second.zip',rows() if second is None else second))
    return SourcePaths(archives,folder/'geometry.sqlite',folder/'reference.sqlite',folder/'access.jsonl')


@contextmanager
def scored_session(folder):
    import wcsf_source
    from wcsf_audit import AuditSession
    folder=Path(folder);assets=[];responses={}
    for name,_,_ in wcsf_source.ASSETS:
        p=csv_zip(folder/name,rows());b=p.read_bytes()
        assets.append((name,hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest(),len(b)));responses[name]=b
    session=AuditSession(Path(__file__).resolve().parents[1],folder/'reports',folder/'private')
    with patch('wcsf_source.ASSETS',tuple(assets)):
        session.freeze()
        with patch('wcsf_source.urllib.request.urlopen',side_effect=lambda req,**kw:io.BytesIO(responses[req.full_url.rsplit('/',1)[1]])):
            session.acquire()
        session.qualify();session.infer();session.score();session.verify()
        yield session
