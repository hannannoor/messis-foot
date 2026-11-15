"""Noise-aware comparison of prediction tags across evaluation views (investigation, dev only).

    python se_noise.py <cfg> <tagA> <tagB> [<tagC> ...]     (a tag may be tag#cfg, tag@power#cfg to override)
For each view (clean, deg, cases_evalg1/2, cases_evalr1/2) prints each tag's provider-weighted mean and, for every
tag against the first, the paired per-match mean difference +- 1 SE and how many matches improved.
Reads scores2/<tag>[_<view>]/<cid>.json written by se_score2.py.
"""
import json
import sys

import numpy as np

import se_load

VIEWS = [('clean', ''), ('deg', '_deg'), ('evalg1', '_cases_evalg1'), ('evalg2', '_cases_evalg2'),
         ('evalr1', '_cases_evalr1'), ('evalr2', '_cases_evalr2')]


def per_match(tag, suf, cfg):
    d = se_load.PRIVATE / 'scores2' / (tag + suf)
    out = {}
    for f in d.glob('*.json'):
        j = json.loads(f.read_text())
        if cfg in j:
            out[f.stem] = j[cfg]['nogap']
    return out


def weighted(scores):
    by = {}
    for c, v in scores.items():
        by.setdefault(se_load.provider(c), []).append(v)
    return float(np.mean([np.mean(v) for v in by.values()])) if by else float('nan')


if __name__ == '__main__':
    cfg, tags = sys.argv[1], sys.argv[2:]
    for view, suf in VIEWS:
        def get(t):
            name, _, c = t.partition('#')
            return per_match(name if '@' in name else name + '@2', suf, c or cfg)
        s = {t: get(t) for t in tags}
        if not all(s.values()):
            continue
        common = sorted(set.intersection(*[set(v) for v in s.values()]))
        line = [f'{view:7s} n={len(common):2d}'] + [f'{t}={weighted({c: s[t][c] for c in common}):.4f}' for t in tags]
        print('  '.join(line))
        base = tags[0]
        for t in tags[1:]:
            d = np.array([s[t][c] - s[base][c] for c in common])
            print(f'          {t}-{base}: {d.mean():+.4f} +- {d.std(ddof=1) / np.sqrt(len(d)):.4f}  up {int((d > 0).sum())}/{len(d)}')
