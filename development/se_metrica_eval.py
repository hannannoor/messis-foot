"""Round 9: score release configurations (exact numpy runtime + release decoder) on Metrica sample games.
    python se_metrica_eval.py            -> scores/metrica_eval.json and a table
No fitting, no tuning: every configuration is a frozen release (all-data models never saw these games)."""
import json
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np

import se_load

ARCH = se_load.PRIVATE / 'model_archive'
CONFIGS = {   # name: (SETS, BND_LO)
    'v2': ((('gru_v2.npz', 'gbm_v2.npz', 1.0),), None),   # pre-dropout models; decoded with the v2 chain (gap rule)
    'v4': ((('gru.npz', 'gbm.npz', 1.0),), None),
    'v5': ((('gru.npz', 'gbm.npz', 0.3), ('gru5.npz', 'gbm5.npz', 0.7)), None),
    'v6': ((('gru.npz', 'gbm.npz', 0.3), ('gru6.npz', 'gbm6.npz', 0.7)), None),
    'v8': ((('gru.npz', 'gbm.npz', 0.15), ('gru8.npz', 'gbm8.npz', 0.85)), 8.0),
}
GAMES = tuple('metrica-' + g for g in se_load.METRICA)


def one(args):
    name, cid = args
    import strong_runtime as rt
    from se_assembly import assemble
    from memory_ablation_metrics import score_variant
    rt.MODEL_DIR = ARCH
    rt.SETS, rt.BND_LO = CONFIGS[name] if name != 'release' else (None, None)
    z = np.load(se_load.PRIVATE / 'cases' / (cid + '.npz'))
    names = [str(s) for s in z['names']]
    frames, ref = se_load.load(cid)
    per = np.asarray([f.period for f in frames], np.uint8)
    obs = np.asarray([f.ball_observed for f in frames], bool)
    if name == 'release':   # old frozen tree + release chain (gap rule, cost 32, missing rows neutral)
        st = assemble(frames, z['release_sup'], (), missing_w=0.0, cost=32.0)['final']
    else:
        sup = rt.supports(z['X'], names, z['period'])
        if name == 'v2':
            st = assemble(frames, sup, (), missing_w=1.0, cost=20.0)['final']
        else:
            st = assemble(frames, sup, (), missing_w=rt.MISSING_W, cost=rt.SWITCH_COST,
                          cost_rows=rt.cost_rows(z['X'], names, rt.boundary()))['nogap']
    lab = np.asarray(['HADX'.index(s) for s in st], np.uint8)
    np.save(se_load.PRIVATE / 'scores2' / f'metrica_{name}_{cid}.npy', lab)
    m = score_variant(ref, lab, per, obs)['metrics']
    if name != 'release':   # stage ablation: same supports, with and without the gap rule
        np.savez_compressed(se_load.PRIVATE / 'scores2' / f'metrica_sup_{name}_{cid}.npz', sup=sup,
                            bnd=rt.boundary() if rt.boundary() is not None else np.zeros(0))
        both = assemble(frames, sup, (), missing_w=rt.MISSING_W if name != 'v2' else 1.0, cost=rt.SWITCH_COST,
                        cost_rows=None if name == 'v2' else rt.cost_rows(z['X'], names, rt.boundary()))
        for k in ('final', 'nogap'):
            l2 = np.asarray(['HADX'.index(s) for s in both[k]], np.uint8)
            print(name, cid, k, round(score_variant(ref, l2, per, obs)['metrics']['spell_f1_mean'], 4), flush=True)
    return name, cid, m['spell_f1_mean']


if __name__ == '__main__':
    only = sys.argv[2].split(',') if len(sys.argv) > 2 else ['release'] + list(CONFIGS)
    jobs = [(n, c) for n in only for c in GAMES]
    with Pool(int(sys.argv[1]) if len(sys.argv) > 1 else 4) as pool:
        res = pool.map(one, jobs)
    out = {}
    for n, c, f in res:
        out.setdefault(n, {})[c] = f
    f = se_load.PRIVATE / 'scores2' / 'metrica_eval.json'
    prev = json.loads(f.read_text()) if f.exists() else {}
    prev.update(out); f.write_text(json.dumps(prev, indent=1))
    for n, v in out.items():
        print(n.ljust(8), ' '.join(f'{v[c]:.4f}' for c in GAMES), ' mean', round(float(np.mean(list(v.values()))), 4))
