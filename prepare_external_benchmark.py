"""Prepare external caches; label data stays separate from input arrays."""
import concurrent.futures
import json
from pathlib import Path
from gap_solver.external import load_external,save_cache

ROOT=Path(__file__).resolve().parent.parent/'external-reference'


def prepare(match):
    raw=ROOT/'raw'
    metadata=list(raw.glob('*matchinformation*DFL-MAT-'+match+'.xml'))
    tracking=list(raw.glob('*positions*DFL-MAT-'+match+'.xml'))
    if len(metadata)!=1 or len(tracking)!=1:
        raise ValueError('Missing/ambiguous external source files for '+match)
    prefix=ROOT/'cache'/match
    if Path(str(prefix)+'.metadata.json').exists():
        return match,'cached'
    result=load_external(metadata[0],tracking[0])
    save_cache(result,prefix)
    return match,len(result.periods)


if __name__=='__main__':
    provenance=json.loads((ROOT/'provenance.json').read_text(encoding='utf-8'))
    matches=[m for names in provenance['split'].values() for m in names]
    with concurrent.futures.ProcessPoolExecutor(max_workers=2) as executor:
        for match,size in executor.map(prepare,matches):
            print('Prepared external match {}: {}'.format(match,size),flush=True)
