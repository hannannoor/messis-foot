"""Protect ingestion isolation, archive identities and typed source structure."""
import hashlib
from contextlib import closing
import io
import json
from pathlib import Path
import sqlite3
import struct
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from wcsf_fixtures import csv_zip,rows,source_paths


class SourceTests(unittest.TestCase):
    def setUp(self):
        try:import wcsf_source
        except ImportError:self.fail('Missing planned safe source ingestion')
        self.api=wcsf_source
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)

    def test_pinned_bytes_and_blob(self):
        p=csv_zip(self.root/'a.zip',rows(1));b=p.read_bytes()
        h=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
        self.assertEqual(self.api.validate_archive(p,h,len(b)),'positions.csv')
        for digest,size in [('0'*40,len(b)),(h,len(b)+1)]:
            with self.assertRaises(ValueError):self.api.validate_archive(p,digest,size)

    def test_rejects_zip_traversal_symlink_duplicate_and_ratio(self):
        for kind in ('../escape.csv','C:/escape.csv','/absolute.csv','symlink','duplicate','ratio','extra'):
            p=self.root/(str(len(kind))+kind.replace('/','_').replace(':','_')+'.zip')
            with zipfile.ZipFile(p,'w',zipfile.ZIP_DEFLATED) as z:
                if kind=='symlink':
                    member=zipfile.ZipInfo('positions.csv');member.create_system=3;member.external_attr=(0o120777<<16);z.writestr(member,'target')
                elif kind=='duplicate':z.writestr('a.csv','x');z.writestr('b.csv','x')
                elif kind=='ratio':z.writestr('positions.csv','x'*100000)
                elif kind=='extra':z.writestr('positions.csv','x');z.writestr('other.txt','x')
                else:z.writestr(kind,'x')
            b=p.read_bytes();h=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
            with self.subTest(kind=kind),self.assertRaises(ValueError):self.api.validate_archive(p,h,len(b))

    def test_existing_generation_never_overwritten(self):
        p=self.root/'existing';p.mkdir();(p/'keep').write_text('original')
        with self.assertRaises((ValueError,FileExistsError)):self.api.acquire(p)
        self.assertEqual((p/'keep').read_text(),'original')

    def test_small_matching_appledouble_sidecar_and_impostors(self):
        cases=[('valid','__MACOSX/._positions.csv',b'\x00\x05\x16\x07'+b'\x00'*159,True),
               ('bad_magic','__MACOSX/._positions.csv',b'fake metadata',False),
               ('wrong_name','__MACOSX/._other.csv',b'\x00\x05\x16\x07',False),
               ('too_large','__MACOSX/._positions.csv',b'\x00\x05\x16\x07'+bytes(range(256))*20,False)]
        for name,member,metadata,allowed in cases:
            p=self.root/(name+'.zip')
            with zipfile.ZipFile(p,'w') as z:z.writestr('positions.csv','x,y\n1,2\n');z.writestr(member,metadata)
            b=p.read_bytes();h=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
            if allowed:
                try:member_name=self.api.validate_archive(p,h,len(b))
                except ValueError:self.fail('A matching bounded AppleDouble sidecar must not become a second data CSV')
                self.assertEqual(member_name,'positions.csv')
            else:
                with self.subTest(name=name),self.assertRaises(ValueError):self.api.validate_archive(p,h,len(b))

    def test_encrypted_and_declared_oversize_members_rejected(self):
        for kind in ('encrypted','oversize'):
            p=csv_zip(self.root/(kind+'.zip'),rows(1));b=bytearray(p.read_bytes());central=b.index(b'PK\x01\x02')
            if kind=='encrypted':
                struct.pack_into('<H',b,central+8,1);struct.pack_into('<H',b,6,1)
            else:struct.pack_into('<I',b,central+24,2000000001)
            p.write_bytes(b);h=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
            with self.assertRaises(ValueError):self.api.validate_archive(p,h,len(b))

    def test_public_download_has_no_credentials_and_wrong_bytes_stop(self):
        class Response(io.BytesIO):
            pass
        requests=[]
        def open_public(request,**kwargs):requests.append(request);return Response(b'bad source bytes')
        with patch('wcsf_source.urllib.request.urlopen',side_effect=open_public):
            with self.assertRaises(ValueError):self.api.acquire(self.root/'new')
        self.assertEqual(len(requests),1)
        self.assertEqual(requests[0].full_url,'https://raw.githubusercontent.com/MatKempeGroningen/WCSF_SolutionRoom/1c9ba798f98a9fffb16081a5d3965774d4e5662c/positions_FIRST_HALF.csv.zip')
        self.assertNotIn('authorization',{k.lower() for k in requests[0].headers})

    def test_delimiter_and_bom_unique_headers(self):
        for i,delimiter in enumerate((',',';','\t')):
            folder=self.root/str(i);paths=source_paths(folder)
            csv_zip(paths.archives[0],rows(2),delimiter,bom=True)
            self.api.ingest(paths)
            with closing(sqlite3.connect(paths.geometry_db)) as db:self.assertEqual(db.execute('select count(*) from geometry where period=1').fetchone()[0],12)
        p=self.root/'badheader';paths=source_paths(p)
        with zipfile.ZipFile(paths.archives[0],'w') as z:z.writestr('a.csv','x,x\n1,2\n')
        with self.assertRaises(ValueError):self.api.ingest(paths)

    def test_only_geometry_columns_reach_geometry_store(self):
        paths=source_paths(self.root/'normal');self.api.ingest(paths)
        with closing(sqlite3.connect(paths.geometry_db)) as db:
            names={r[1] for r in db.execute('pragma table_info(geometry)')}
        self.assertEqual(names,{'period','t','team','player','x','y','bx','by'})
        events=[json.loads(line) for line in paths.access_log.read_text().splitlines()]
        self.assertEqual(events[0]['event'],'machine_reference_access')
        self.assertFalse(any('AliveFlag' in line for line in paths.access_log.read_text().splitlines()))

    def test_required_ids_clocks_and_conflicting_geometry_duplicates(self):
        bads=[dict(timestamp_ms=-100),dict(group_id=3),dict(player_id='invalid'),dict(timestamp_ms=101),dict(timestamp_ms=86400100)]
        for i,bad in enumerate(bads):
            data=rows(3);data[6].update(bad);paths=source_paths(self.root/str(i),first=data)
            with self.subTest(bad=bad),self.assertRaises(ValueError):self.api.ingest(paths)
        data=rows(2);data.append(dict(data[0],x=123.));paths=source_paths(self.root/'conflict',first=data)
        with self.assertRaises(ValueError):self.api.ingest(paths)

    def test_identical_geometry_duplicates_preserve_conflicting_reference_rows(self):
        data=rows(2);data.append(dict(data[0],PossessionFlag=2));paths=source_paths(self.root/'duplicates',first=data)
        self.api.ingest(paths)
        with closing(sqlite3.connect(paths.geometry_db)) as db:self.assertEqual(db.execute('select count(*) from geometry where period=1').fetchone()[0],12)
        with closing(sqlite3.connect(paths.reference_db)) as db:
            self.assertEqual(db.execute('select count(*) from annotations where period=1').fetchone()[0],13)

    def test_ingestion_releases_database_handles(self):
        paths=source_paths(self.root/'handles');self.api.ingest(paths)
        paths.geometry_db.rename(self.root/'renamed.sqlite')
        paths.reference_db.rename(self.root/'renamed-reference.sqlite')

    def test_ids_keep_team_and_clock_span_cap(self):
        data=rows(2);data[0]['player_id']=200;paths=source_paths(self.root/'team',first=data)
        with self.assertRaises(ValueError):self.api.ingest(paths)
        data=rows(2)
        for r in data[6:]:r['timestamp_ms']=5400100
        paths=source_paths(self.root/'span',first=data)
        with self.assertRaises(ValueError):self.api.ingest(paths)


if __name__=='__main__':unittest.main()
