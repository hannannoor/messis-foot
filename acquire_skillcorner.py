"""Acquire pinned licensed external inputs only, without inference or label-based selection."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
import json
from pathlib import Path
import re

from gap_solver.acquisition import acquire_asset


def main():
    code=Path(__file__).resolve().parent
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=code.parent/'independent-reference')
    parser.add_argument('--workers',type=int,default=3)
    args=parser.parse_args()
    if not 1<=args.workers<=8:parser.error('workers must be1..8')
    protocol=json.loads((code/'benchmark/skillcorner/protocol.json').read_text(encoding='utf-8'))
    revision=protocol['revision']
    if not re.fullmatch('[a-f0-9]{40}',revision) or not protocol['license'].startswith('MIT'):
        raise ValueError('Missing pinned revision/checked licence')
    args.root.mkdir(parents=True,exist_ok=True)
    provenance=args.root/'provenance.json'
    if provenance.exists() and json.loads(provenance.read_text())['source_revision']!=revision:
        raise ValueError('Existing external directory belongs to a different source revision')
    pointers={p['path']:p for p in protocol['tracking_lfs_objects']}
    entries=[]
    for item in protocol['files']:
        path=item['path']
        if path.endswith('_dynamic_events.csv'):continue
        if not re.fullmatch(r'data/matches/(\d+)/\1_(match\.json|tracking_extrapolated\.jsonl|phases_of_play\.csv)',path):
            raise ValueError('Invalid pinned asset path')
        target=args.root/'raw'/Path(path).relative_to('data/matches')
        if path in pointers:
            pointer=pointers[path]
            entries.append((path,'https://media.githubusercontent.com/media/SkillCorner/opendata/'+revision+'/'+path,
                            target,pointer['object_bytes'],pointer['object_sha256'],'sha256'))
        else:
            entries.append((path,'https://raw.githubusercontent.com/SkillCorner/opendata/'+revision+'/'+path,
                            target,item['repository_bytes'],item['git_blob_sha'],'git_blob_sha1'))
    for item in protocol['root_files']:
        entries.append((item['path'],'https://raw.githubusercontent.com/SkillCorner/opendata/'+revision+'/'+item['path'],
                       args.root/'source'/item['path'],item['repository_bytes'],item['git_blob_sha'],'git_blob_sha1'))
    def acquire(entry):
        path,url,target,size,digest,algorithm=entry
        result=acquire_asset(url,target,size,digest,algorithm)
        result.update(source_path=path,url=url,algorithm=algorithm)
        print(('Verified cached ' if result['cached'] else 'Acquired verified ')+path,flush=True)
        return result
    with ThreadPoolExecutor(max_workers=args.workers) as pool:results=list(pool.map(acquire,entries))
    record=dict(source_revision=revision,source=protocol['source'],license=protocol['license'],
                attribution=protocol['attribution'],split=protocol['split'],split_fixed_before_model_scores=True,
                acquired_at_utc=datetime.now(timezone.utc).isoformat(),files=results,
                model_scores_computed=False,unused_event_files_not_downloaded=True)
    temporary=provenance.with_suffix('.json.new')
    temporary.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');temporary.replace(provenance)
    print('Verified {} external source files; no model fitted/scored.'.format(len(results)),flush=True)


if __name__=='__main__':main()
