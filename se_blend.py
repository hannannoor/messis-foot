"""Geometric blend of prediction tags: python se_blend.py <out> <tagA>:<w> <tagB>:<w> ..."""
import sys
import numpy as np
import se_load

out, parts = sys.argv[1], [(a.split(':')[0], float(a.split(':')[1])) for a in sys.argv[2:]]
d = se_load.PRIVATE / 'preds' / out
d.mkdir(parents=True, exist_ok=True)
common = set.intersection(*[{p.stem for p in (se_load.PRIVATE / 'preds' / t).glob('*.npz')} for t, _ in parts])
for cid in sorted(common):
    lp = sum(w * np.log(np.clip(np.load(se_load.PRIVATE / 'preds' / t / (cid + '.npz'))['sup'], 1e-9, 1)) for t, w in parts)
    lp /= sum(w for _, w in parts)
    p = np.exp(lp - lp.max(1, keepdims=True)); p /= p.sum(1, keepdims=True)
    np.savez_compressed(d / (cid + '.npz'), sup=p)
print(out, len(common))
