"""Strong-emission release: geometry features -> GRU+GBM supports -> release decoder chain -> submission.csv.

    python strong_release.py --prefix <tactical prefix> --tags <tags.xml> --out <new dir>

Runtime: CPython 3.14 + numpy (inference only; models in strong_model/ were fitted on external data only).
Decoder chain unchanged from restart_release.py: decode -> gap rule -> decoder restart -> gap rule -> kickoff patch.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np

VERSION = '2026.11.14-strong-emissions'


def generate(prefix, tags, out, *, features_out=None):
    from gap_solver.tactical import feature_rows
    from kickoff_patch import kickoff_starts
    from live_dead_assembly import StreamSupportSet
    from recent_geometry_assembly import assemble_research
    from release_runtime import load_source, submission_bytes
    import se_features
    import strong_runtime
    out = Path(out)
    if out.exists() or out.is_symlink():
        raise FileExistsError('Output directory must not exist')
    prefix = str(prefix)
    frames, _ = load_source(*(Path(prefix + s) for s in ('_atd.xml', '_atd.txt', '_homography.csv')))
    frames = list(frames)
    f18 = np.asarray(list(feature_rows(frames)), dtype=np.float64)
    X, names, info = se_features.build(frames, f18)
    sup = strong_runtime.supports(X, names, info['period'])
    result = assemble_research(frames, StreamSupportSet('release', sup), kickoff_starts(tags))
    data = submission_bytes(result.final)
    model_sha = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(strong_runtime.MODEL_DIR.glob('*.npz'))}
    receipt = dict(version=VERSION, rows=len(result.final), csv_sha256=hashlib.sha256(data).hexdigest(),
                   supports_sha256=hashlib.sha256(np.ascontiguousarray(sup).tobytes()).hexdigest(),
                   model_sha256=model_sha, counts={k: result.final.count(k) for k in 'HADX'},
                   stoppage_gaps=len(result.stoppage_gaps), kickoff_changed=result.kickoff_changed)
    out.mkdir(parents=True, exist_ok=False)
    (out / 'submission.csv').write_bytes(data)
    (out / 'strong-release-receipt.json').write_text(json.dumps(receipt, sort_keys=True, indent=1, default=str) + '\n',
                                                     encoding='utf-8')
    if features_out:
        np.savez_compressed(features_out, sup=sup)
    return receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prefix', required=True)
    parser.add_argument('--tags', required=True, help='Automatic kickoff tags only')
    parser.add_argument('--out', required=True, help='New nonexistent output directory')
    args = parser.parse_args(argv)
    print(json.dumps(generate(args.prefix, args.tags, args.out), sort_keys=True, default=str))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
