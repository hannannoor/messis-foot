"""Acquire the predeclared CC-BY-4.0 external reference, with immutable checksums."""
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import time
import urllib.request

root=Path(__file__).resolve().parent.parent/'external-reference'
manifest=json.loads((root/'figshare-manifest.json').read_text(encoding='utf-8'))
if manifest['license']['url'].rstrip('/')!='https://creativecommons.org/licenses/by/4.0':
    raise ValueError('Unexpected external dataset licence; refusing acquisition')
raw=root/'raw'
raw.mkdir(parents=True,exist_ok=True)
split={'development':['J03WOH','J03WOY','J03WPY','J03WMX'],
       'validation':['J03WQQ'],'test':['J03WR9','J03WN1']}
ids={match for matches in split.values() for match in matches}
files=[f for f in manifest['files'] if any('DFL-MAT-'+match+'.xml' in f['name'] for match in ids)]
if len(files)!=21:
    raise ValueError('Expected three source files for each of seven external matches')

def md5(path):
    digest=hashlib.md5()
    with path.open('rb') as handle:
        for chunk in iter(lambda:handle.read(8*1024*1024),b''):
            digest.update(chunk)
    return digest.hexdigest()

def acquire(record):
    destination=raw/record['name']
    expected=record.get('computed_md5') or record.get('supplied_md5')
    if destination.exists() and destination.stat().st_size==record['size'] and md5(destination)==expected:
        print('Verified cached '+record['name'],flush=True)
        return dict(name=record['name'],md5=expected,size=record['size'],source_url=record['download_url'])
    partial=destination.with_suffix('.xml.partial')
    for attempt in range(3):
        try:
            offset=partial.stat().st_size if partial.exists() else 0
            request=urllib.request.Request(record['download_url'],headers={'Range':'bytes={}-'.format(offset)} if offset else {})
            with urllib.request.urlopen(request,timeout=90) as response:
                append=offset>0 and response.status==206
                with partial.open('ab' if append else 'wb') as output:
                    while True:
                        chunk=response.read(4*1024*1024)
                        if not chunk:
                            break
                        output.write(chunk)
            if partial.stat().st_size!=record['size'] or md5(partial)!=expected:
                raise ValueError('External source size/checksum mismatch: '+record['name'])
            os.replace(partial,destination)
            print('Downloaded and verified '+record['name'],flush=True)
            return dict(name=record['name'],md5=expected,size=record['size'],source_url=record['download_url'])
        except Exception:
            if attempt==2:
                raise
            time.sleep(2)

with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
    acquired=list(executor.map(acquire,files))
provenance=dict(dataset_title=manifest['title'],doi=manifest['doi'],license=manifest['license'],
                attribution='Bassek, Rein, Weber et al., Scientific Data 12, 195 (2025), doi:10.1038/s41597-025-04505-y; DFL / Sportec Solutions.',
                split=split,split_fixed_before_scores=True,reference_type='external provider labels, not competition gold',files=acquired)
(root/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n',encoding='utf-8')
print('Completed checksum-verified external acquisition; declared split saved.',flush=True)
