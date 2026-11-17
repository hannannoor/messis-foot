"""Noise-aware comparison of prediction tags across evaluation views (investigation, dev only).

    python se_noise.py <cfg> <tagA> <tagB> [<tagC> ...] [--stage gapko|nogap|final]
    (a tag may be tag#cfg, tag@power#cfg to override; the default stage is the submitted decoder, 'gapko')
For each view (clean, deg, cases_evalg1/2, cases_evalr1/2) prints each tag's provider-weighted mean and, for every
tag against the first, the paired per-match mean difference +- 1 SE and how many matches improved.
Reads scores2/<tag>[_<view>]/<cid>.json written by se_score2.py.
"""
import json
import sys

import numpy as np

import se_load

VIEWS = [('clean', ''), ('deg', '_deg'), ('evalg1', '_cases_evalg1'), ('evalg2', '_cases_evalg2'),
         ('evalr1', '_cases_evalr1'), ('evalr2', '_cases_evalr2'), ('evalp', '_cases_evalp'), ('evalrp', '_cases_evalrp'),
         ('sde1', '_cases_sde1'), ('sde2', '_cases_sde2'), ('sde3', '_cases_sde3')]
# The deg/eval* views remove the ball at random with respect to play (round 10 audit): BAR-ATH loses it in about 150
# long blocks instead, so they penalise the submitted gap rule and are kept for history only. The sde* views are the
# round 10 state-dependent ones (se_degrade.state_loss): same generator, ball vanishing sooner, ball vanishing later.
LEGACY = {'deg', 'evalg1', 'evalg2', 'evalr1', 'evalr2', 'evalp', 'evalrp'}
STAGE = 'gapko'   # decoder stage scored: 'gapko' is the v9 submission ('nogap' = v3-v8); override with --stage


def per_match(tag, suf, cfg):
    d = se_load.PRIVATE / 'scores2' / (tag + suf)
    out = {}
    for f in d.glob('*.json'):
        j = json.loads(f.read_text())
        if cfg in j and STAGE in j[cfg]:   # files scored before v9 have no 'gapko' stage: rescore with se_score2.py
            out[f.stem] = j[cfg][STAGE]
    return out


def weighted(scores):
    by = {}
    for c, v in scores.items():
        by.setdefault(se_load.provider(c), []).append(v)
    return float(np.mean([np.mean(v) for v in by.values()])) if by else float('nan')


if __name__ == '__main__':
    args = sys.argv[1:]
    if '--stage' in args:
        i = args.index('--stage'); STAGE = args[i + 1]; del args[i:i + 2]
    cfg, tags = args[0], args[1:]
    print(f'stage {STAGE}')
    for view, suf in VIEWS:
        def get(t):
            name, _, c = t.partition('#')
            return per_match(name if '@' in name else name + '@2', suf, c or cfg)
        s = {t: get(t) for t in tags}
        if not all(s.values()):
            continue
        common = sorted(set.intersection(*[set(v) for v in s.values()]))
        line = [f'{view:7s}{" (legacy random loss)" if view in LEGACY else ""} n={len(common):2d}'] + [f'{t}={weighted({c: s[t][c] for c in common}):.4f}' for t in tags]
        print('  '.join(line))
        base = tags[0]
        for t in tags[1:]:
            d = np.array([s[t][c] - s[base][c] for c in common])
            print(f'          {t}-{base}: {d.mean():+.4f} +- {d.std(ddof=1) / np.sqrt(len(d)):.4f}  up {int((d > 0).sum())}/{len(d)}')
