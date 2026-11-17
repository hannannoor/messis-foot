"""Own-decoder scoring straight from cached arrays (no frame loading).
    python se_fast.py <predtag> cost:power[:dbias] ...
"""
import json, sys, time
from multiprocessing import Pool
import numpy as np
import se_load
from se_decode import decode

def one(args):
    tag, cid, cfgs = args
    from memory_ablation_metrics import score_variant
    z = np.load(se_load.PRIVATE / 'cases' / (cid + '.npz'))
    sup = z['release_sup'] if tag == 'release' else np.load(se_load.PRIVATE / 'preds' / tag / (cid + '.npz'))['sup']
    res = {}
    for cfg in cfgs:
        c, p, *b = map(float, cfg.split(':'))
        fin = decode(sup, z['period'], c, p, b[0] if b else 0.)
        s = score_variant(z['ref'], fin, z['period'].astype(np.uint8), z['observed'].astype(bool))
        res[cfg] = s['metrics']['spell_f1_mean']
    return cid, res

if __name__ == '__main__':
    tag, cfgs = sys.argv[1], sys.argv[2:]
    cids = [c for c in se_load.ALL if c not in se_load.HOLDOUT]
    with Pool(13) as pool:
        out = dict(pool.map(one, [(tag, c, cfgs) for c in cids]))
    for cfg in cfgs:
        by = {}
        for c in cids: by.setdefault(se_load.provider(c), []).append(out[c][cfg])
        m = {k: round(float(np.mean(v)), 4) for k, v in by.items()}
        print(tag, cfg, round(float(np.mean(list(m.values()))), 4), m, flush=True)
    d = se_load.PRIVATE / 'fast'; d.mkdir(exist_ok=True)
    (d / f'{tag}.json').write_text(json.dumps(out))
