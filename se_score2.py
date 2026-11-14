"""Score configurable assembly variants on dev (or given) cases, every stage.
    python se_score2.py <predtag@power> <cfg> [<cfg> ...] [--cases a,b]   cfg = w<missing_w>c<cost>, e.g. w0c32
Writes scores2/<tag>/<cid>.json  {cfg: {stage: f1}}"""
import json, sys, time, re
from multiprocessing import Pool
import numpy as np
import se_load

def parse(cfg):
    m = re.fullmatch(r'w([\d.]+)(h?)c([\d.]+)(?:d([\d.]+))?', cfg)
    return float(m.group(1)), float(m.group(3)), (float(m.group(4)) if m.group(4) else None), ('ha' if m.group(2) else 'all')

DEG = False


def sup_for(tag, cid):
    base, _, power = tag.partition('@')
    case = np.load(se_load.PRIVATE / ('cases_deg' if DEG else 'cases') / (cid + '.npz'))
    sub = (base + '/deg') if DEG else base
    sup = case['release_sup'] if base == 'release' else np.load(se_load.PRIVATE / 'preds' / sub / (cid + '.npz'))['sup']
    if power:
        sup = np.clip(sup, 1e-9, 1) ** float(power); sup = sup / sup.sum(1, keepdims=True)
    sup = np.clip(np.asarray(sup, np.float64), 1e-6, 1); return sup / sup.sum(1, keepdims=True), case

def _init(deg):
    global DEG
    DEG = deg


def one(args):
    tag, cid, cfgs = args
    from memory_ablation_metrics import score_variant
    from se_assembly import assemble
    sup, case = sup_for(tag, cid)
    if DEG:
        from se_degrade import load_deg
        frames, ref = load_deg(cid)
    else:
        frames, ref = se_load.load(cid)
    per = np.asarray([f.period for f in frames], np.uint8); obs = np.asarray([f.ball_observed for f in frames], bool)
    out = {}
    for cfg in cfgs:
        w, c, d, mode = parse(cfg)
        st = assemble(frames, sup, (), missing_w=w, cost=c, cost_d=d, mode=mode)
        d0 = se_load.PRIVATE / 'scores2' / (tag + ('_deg' if DEG else '')); d0.mkdir(parents=True, exist_ok=True)
        np.save(d0 / f'{cid}.{cfg}.final.npy', np.asarray(['HADX'.index(s) for s in st['final']], np.uint8))
        np.save(d0 / f'{cid}.{cfg}.nogap.npy', np.asarray(['HADX'.index(s) for s in st['nogap']], np.uint8))
        out[cfg] = {k: score_variant(ref, np.asarray(['HADX'.index(s) for s in v], np.uint8), per, obs)['metrics']['spell_f1_mean'] for k, v in st.items()}
    d = se_load.PRIVATE / 'scores2' / (tag + ('_deg' if DEG else '')); d.mkdir(parents=True, exist_ok=True)
    prev = json.loads((d / (cid + '.json')).read_text()) if (d / (cid + '.json')).exists() else {}
    prev.update(out); (d / (cid + '.json')).write_text(json.dumps(prev))
    return cid, out

if __name__ == '__main__':
    args = sys.argv[1:]; cases = None
    if '--cases' in args:
        i = args.index('--cases'); cases = args[i + 1].split(','); del args[i:i + 2]
    if '--deg' in args:
        args.remove('--deg'); DEG = True
    tag, cfgs = args[0], args[1:]
    cids = cases or [c for c in se_load.ALL if c not in se_load.HOLDOUT]
    if DEG and not cases:
        cids = [c for c in cids if c.startswith('dfl')]
    with Pool(len(cids), initializer=_init, initargs=(DEG,)) as pool:
        res = dict(pool.map(one, [(tag, c, cfgs) for c in cids]))
    for cfg in cfgs:
        for stage in ('control', 'final', 'nogap'):
            by = {}
            for c in cids: by.setdefault(se_load.provider(c), []).append(res[c][cfg][stage])
            m = {k: round(float(np.mean(v)), 4) for k, v in by.items()}
            print(tag, cfg, stage.ljust(9), round(float(np.mean(list(m.values()))), 4), m, flush=True)
