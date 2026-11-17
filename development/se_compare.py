"""Compare scored tags on dev matches: per case and provider-weighted composite."""
import json, sys
import numpy as np
import se_load

def read(tag):
    d = se_load.PRIVATE / 'scores' / tag
    return {p.stem: json.loads(p.read_text()) for p in d.glob('*.json')}

def comp(rows, cids):
    by = {}
    for c in cids:
        if c in rows: by.setdefault(se_load.provider(c), []).append(rows[c]['f1'])
    m = {p: np.mean(v) for p, v in by.items()}
    return np.mean(list(m.values())), m

HOLD = '--holdout' in sys.argv
tags = [a for a in sys.argv[1:] if a != '--holdout']
data = {t: read(t) for t in ['release'] + tags}
cids = sorted(c for c in data[tags[-1]] if (c in se_load.HOLDOUT) == HOLD)
print('case'.ljust(22), *[t[:12].rjust(12) for t in data], ' npred')
for c in cids:
    print(c.ljust(22), *[f"{data[t][c]['f1']:.4f}".rjust(12) if c in data[t] else ' '*12 for t in data],
          ' ', *[data[t][c]['n_pred'] for t in data if c in data[t]], data['release'][c]['n_gt'])
oos = [c for c in cids if c not in se_load.RELEASE_TRAIN]
if HOLD:
    print('NOTE: holdout composite = mean over providers (dfl, skillcorner, wcsf) of per-case means')
for name, cs in (('dev-all', cids), ('dev-oos', oos)):
    print(name.ljust(22), *[f"{comp(data[t], cs)[0]:.4f}".rjust(12) for t in data], {t: {k: round(v,4) for k,v in comp(data[t], cs)[1].items()} for t in data})
