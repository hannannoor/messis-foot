"""Score supports through the unchanged release decoder chain with the official spell metric.

    python se_score.py <tag> [cid ...]     # reads strong-emissions-reference/preds/<tag>/<cid>.npz (key 'sup')
    tag 'release' uses the frozen release supports stored in the case file.
"""
import json
import sys
import time
from multiprocessing import Pool

import numpy as np

import se_load


def score_one(args):
    tag, cid = args
    from live_dead_assembly import assemble_stream
    from memory_ablation_metrics import score_variant
    t = time.time()
    case = np.load(se_load.PRIVATE / 'cases' / (cid + '.npz'))
    if tag == 'release':
        sup = case['release_sup']
    else:
        base, _, power = tag.partition('@')
        sup = np.load(se_load.PRIVATE / 'preds' / base / (cid + '.npz'))['sup']
        if power:
            sup = np.clip(sup, 1e-9, 1) ** float(power)
            sup = sup / sup.sum(1, keepdims=True)
    frames, ref = se_load.load(cid)
    if not np.array_equal(ref, case['ref']):
        raise ValueError('reference drift ' + cid)
    sup = np.clip(np.asarray(sup, np.float64), 1e-6, 1)
    sup = sup / sup.sum(1, keepdims=True)
    asm = assemble_stream(frames, 'release', sup)
    final = np.asarray(['HADX'.index(s) for s in asm.final], np.uint8)
    periods = np.asarray([f.period for f in frames], np.uint8)
    observed = np.asarray([f.ball_observed for f in frames], bool)
    s = score_variant(ref, final, periods, observed)
    out = dict(cid=cid, tag=tag, f1=s['metrics']['spell_f1_mean'], n_gt=s['spells']['n_gt'],
               n_pred=s['spells']['n_pred'], d_prec=s['dead']['precision'], d_rec=s['dead']['recall'],
               acc=s['metrics'].get('accuracy'), secs=round(time.time() - t, 1))
    d = se_load.PRIVATE / 'scores' / tag
    d.mkdir(parents=True, exist_ok=True)
    np.save(d / (cid + '.final.npy'), final)
    (d / (cid + '.json')).write_text(json.dumps(out))
    return out


def composite(rows, cids):
    """Provider-weighted mean (each provider's mean over the given cases, then mean over providers)."""
    by = {}
    for c in cids:
        if c in rows:
            by.setdefault(se_load.provider(c), []).append(rows[c])
    means = {p: float(np.mean(v)) for p, v in by.items()}
    return float(np.mean(list(means.values()))) if means else None, means


def main(argv):
    tag = argv[0]
    cids = argv[1:]
    if not cids:
        if tag == 'release':
            cids = list(se_load.ALL)
        else:
            cids = sorted(p.stem for p in (se_load.PRIVATE / 'preds' / tag.partition('@')[0]).glob('*.npz')
                          if p.stem not in se_load.HOLDOUT)
    with Pool(min(13, len(cids))) as pool:
        res = pool.map(score_one, [(tag, c) for c in cids])
    for r in sorted(res, key=lambda r: r['cid']):
        print(json.dumps(r))


if __name__ == '__main__':
    main(sys.argv[1:])
