"""Extract features/labels/release supports per external match into strong-emissions-reference/cases/<cid>.npz."""
import sys
import time

import numpy as np

import se_load
import se_features


def main(cids):
    from gap_solver.tactical import feature_rows
    from memory_ablation import predict_supports
    import live_dead_protocol as lp
    model = lp.load_frozen_model()
    out = se_load.PRIVATE / 'cases'
    out.mkdir(parents=True, exist_ok=True)
    for cid in cids:
        path = out / (cid + '.npz')
        if path.exists():
            print('skip', cid, flush=True)
            continue
        t = time.time()
        frames, ref = se_load.load(cid)
        f18 = np.asarray(list(feature_rows(frames)), dtype=np.float64)
        sup = np.asarray(predict_supports(f18, model), dtype=np.float64)
        X, names, info = se_features.build(frames, f18)
        np.savez_compressed(path, X=X, names=np.array(names), ref=ref, period=info['period'],
                            observed=info['observed'], release_sup=sup)
        print(cid, X.shape, round(time.time() - t, 1), flush=True)


if __name__ == '__main__':
    main(sys.argv[1:] or se_load.ALL)
