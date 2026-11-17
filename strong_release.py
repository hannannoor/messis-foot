"""Strong-emission release: geometry features -> GRU+GBM supports -> release decoder chain -> submission.csv.

    python strong_release.py --prefix <tactical prefix> --tags <tags.xml> --out <new dir>

Runtime: CPython 3.14 + numpy (inference only; models in strong_model/ were fitted on external data only).
Decoder: 3-state Viterbi over model supports (evidence kept on missing-ball rows, switch cost 20, 10 within
+-6 frames of an impulse contact, down towards 8 where the GRU boundary channel fires) -> label-free gap rule
(gap_liveness.py: a ball gap over 3 s with below-typical player speed becomes dead ball) -> automatic kickoff patch.
This is the 'gapko' stage of se_assembly.py, selected by strong_runtime.GAP_RULE (v9; v3-v8 used 'nogap').
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / 'development'))   # all modules live in development/

import numpy as np

VERSION = '2026.11.17-strong-emissions-v10-candidate'


def generate(prefix, tags, out, *, features_out=None):
    from gap_solver.tactical import feature_rows
    from kickoff_patch import kickoff_starts
    from se_assembly import assemble
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
    for fn in (se_features.impulse_features, se_features.impulse_rel_features, se_features.team_shape_features,
               se_features.restart_features):
        Xe, ne = fn(frames)
        X, names = np.concatenate([X, Xe], 1), tuple(names) + tuple(ne)
    sup = strong_runtime.supports(X, names, info['period'])
    stages = assemble(frames, sup, kickoff_starts(tags), missing_w=strong_runtime.MISSING_W,
                      cost=strong_runtime.SWITCH_COST, cost_rows=strong_runtime.cost_rows(X, names, strong_runtime.boundary()))
    g = strong_runtime.GAP_RULE
    final = list(stages[g if isinstance(g, str) else ('final' if g else 'nogap')])
    if getattr(strong_runtime, 'BALL_OUT_RULE', False):   # v10 candidate
        from ball_out_rule import apply_ball_out
        final = apply_ball_out(frames, final)
    data = submission_bytes(final)
    model_sha = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(strong_runtime.MODEL_DIR.glob('*.npz'))}
    receipt = dict(version=VERSION, rows=len(final), csv_sha256=hashlib.sha256(data).hexdigest(),
                   supports_sha256=hashlib.sha256(np.ascontiguousarray(sup).tobytes()).hexdigest(),
                   model_sha256=model_sha, counts={k: final.count(k) for k in 'HADX'},
                   missing_w=strong_runtime.MISSING_W, switch_cost=strong_runtime.SWITCH_COST,
                   gap_rule=strong_runtime.GAP_RULE, touch_cost=strong_runtime.TOUCH_COST,
                   touch_k=strong_runtime.TOUCH_K, sets=[list(x) for x in strong_runtime.SETS], bnd_lo=strong_runtime.BND_LO,
                   ball_out_rule=getattr(strong_runtime, 'BALL_OUT_RULE', False))
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
