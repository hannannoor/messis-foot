"""Cache independent features/references; never open model scores or fit a policy."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path

from gap_solver.skillcorner import load_skillcorner,save_motion_cache,load_motion_cache


def prepare(job):
    root,match,regime=job;root=Path(root);folder=root/'raw'/str(match)
    prefix=root/'cache'/(str(match)+'-'+regime)
    if all(Path(str(prefix)+suffix).exists() for suffix in ('.features.npz','.reference.npz','.metadata.json')):
        try:
            data=load_motion_cache(prefix)
            return dict(match=match,canonical_frames=len(data.frames()),cached=True)
        except ValueError as error:
            if 'different adapter' not in str(error):raise
    data=load_skillcorner(folder/(str(match)+'_match.json'),folder/(str(match)+'_tracking_extrapolated.jsonl'),
                         folder/(str(match)+'_phases_of_play.csv'),detected_only=regime=='detected')
    save_motion_cache(data,prefix)
    return dict(match=match,canonical_frames=len(data.frames()),cached=False)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parent.parent/'independent-reference')
    parser.add_argument('--split',choices=['all','development','calibration','validation','test'],default='all')
    parser.add_argument('--regime',choices=['detected','available'],default='detected')
    parser.add_argument('--workers',type=int,default=2)
    args=parser.parse_args()
    if not 1<=args.workers<=4:parser.error('workers must be1..4')
    protocol=json.loads((args.root/'provenance.json').read_text(encoding='utf-8'))
    ids=[m for name,matches in protocol['split'].items() if args.split in ('all',name) for m in matches]
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        for record in pool.map(prepare,[(str(args.root),match,args.regime) for match in ids]):
            print('Cached source {}: {} canonical frames ({})'.format(record['match'],record['canonical_frames'],args.regime),flush=True)


if __name__=='__main__':main()
