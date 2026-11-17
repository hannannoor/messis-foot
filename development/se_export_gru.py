"""Export trained GRU state dicts to numpy arrays."""
import sys
import numpy as np, torch
dst = sys.argv[1]; out = {}; fixes = set()
for k, src in enumerate(sys.argv[2:]):
    ck = torch.load(src, map_location='cpu', weights_only=False)
    fixes.add(bool(ck.get('opts', {}).get('symfix')))
    for name, t in ck['state'].items():
        out[f'm{k}.{name}'] = t.numpy().astype(np.float32)
    out[f'm{k}.mu'] = np.asarray(ck['mu'], np.float32); out[f'm{k}.sd'] = np.asarray(ck['sd'], np.float32)
out['n_models'] = np.array(len(sys.argv) - 2)
if len(fixes) != 1:
    raise SystemExit('models disagree on the swap fix (opts "symfix")')
if fixes.pop():   # only written for round-10 models, so older exports stay byte-identical
    out['symfix'] = np.array(True)
np.savez_compressed(dst, **out)
print(sorted(k for k in out if k.startswith('m0.')))
