"""Short D breaks (council idea): where the ball's touch team flips but the decoded labels show no boundary
within +-k frames, insert a short D so the surrounding possession is split (team of the gap left unknown).
Optional: model change-probability gate tau, and conversion of predicted H/A spells shorter than m frames to D.
Pure post-process on final labels; no reference input.

    python se_dbreak.py <scoretag> <cfg>      # grid over (k, tau, m, width) on dev, printed
"""
import sys
from itertools import product

import numpy as np

import se_load

H, A, D, X = 0, 1, 2, 3


def touch_flips(Xf, names):
    i = names.index('last_touch')
    lt = Xf[:, i]
    prev = np.concatenate([[0.0], lt[:-1]])
    return np.flatnonzero((lt != 0) & (prev != 0) & (lt != prev))


def change_prob(sup, k):
    """P(team differs between windows before and after t), from conditional H share in +-k windows."""
    ph = sup[:, 0] / np.clip(sup[:, 0] + sup[:, 1], 1e-9, None)
    c = np.concatenate([[0.0], np.cumsum(ph)])
    n = len(ph)
    t = np.arange(n)
    lo, hi = np.maximum(0, t - k), np.minimum(n, t + k + 1)
    b = (c[t] - c[lo]) / np.maximum(t - lo, 1)
    a = (c[hi] - c[t + 1]) / np.maximum(hi - t - 1, 1)
    return b * (1 - a) + (1 - b) * a


def apply(final, flips, cp, period, k, tau, m, width):
    out = final.copy()
    n = len(out)
    if m:
        i = 0
        while i < n:
            j = i + 1
            while j < n and out[j] == out[i] and period[j] == period[i]:
                j += 1
            if out[i] in (H, A) and j - i < m:
                out[i:j] = D
            i = j
    bound = np.zeros(n + 1, int)
    change = np.zeros(n, bool)
    change[1:] = out[1:] != out[:-1]
    bound[1:] = np.cumsum(change)
    for t in flips:
        lo, hi = max(0, t - k), min(n - 1, t + k)
        if bound[hi + 1] - bound[lo + 1] > 0:
            continue  # a boundary already exists nearby
        if out[t] not in (H, A) or cp[t] < tau or period[t] == 0:
            continue
        out[t:t + width] = D
    return out


def main(tag, cfg):
    from memory_ablation_metrics import score_variant
    base, _, power = tag.partition('@')
    cids = [c for c in se_load.ALL if c not in se_load.HOLDOUT]
    grid = list(product((12, 25), (0.0, 0.3, 0.5), (0, 10), (2,)))
    res = {g: {} for g in grid}
    res0 = {}
    for cid in cids:
        z = np.load(se_load.PRIVATE / 'cases' / (cid + '.npz'))
        names = [str(s) for s in z['names']]
        sup = np.load(se_load.PRIVATE / 'preds' / base / (cid + '.npz'))['sup']
        final = np.load(se_load.PRIVATE / 'scores2' / tag / f'{cid}.{cfg}.final.npy')
        per, obs, ref = z['period'].astype(np.uint8), z['observed'].astype(bool), z['ref']
        flips = touch_flips(z['X'], names)
        res0[cid] = score_variant(ref, final, per, obs)['metrics']['spell_f1_mean']
        for g in grid:
            k, tau, m, w = g
            cp = change_prob(sup, k)
            out = apply(final, flips, cp, per, k, tau, m, w)
            res[g][cid] = score_variant(ref, out, per, obs)['metrics']['spell_f1_mean']

    def comp(d):
        by = {}
        for c, v in d.items():
            by.setdefault(se_load.provider(c), []).append(v)
        return {p: float(np.mean(v)) for p, v in by.items()}
    b = comp(res0)
    print('base', round(np.mean(list(b.values())), 4), {p: round(v, 4) for p, v in b.items()})
    for g in grid:
        c = comp(res[g])
        better = sum(res[g][x] > res0[x] for x in cids); worse = sum(res[g][x] < res0[x] for x in cids)
        print('k,tau,m,w', g, round(np.mean(list(c.values())), 4), {p: round(v - b[p], 4) for p, v in c.items()},
              f'better {better} worse {worse}', flush=True)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
