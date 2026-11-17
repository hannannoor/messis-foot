"""Round 11: missed dead frames with the ball NOT visible (SkillCorner): how long is their ball gap, and how fast are
players moving there compared with the match's typical speed (the gap rule's test)? Aggregate counts only."""
import json, sys
from multiprocessing import Pool
import numpy as np
import se_load, se_sc_dead as sd
from se_dead_diag import one as _unused  # noqa: F401  (same imports)


def one(cid):
    import gap_liveness as gl
    import strong_runtime as rt
    from se_assembly import assemble
    from statistics import median
    frames, _ = se_load.load(cid)
    ref = np.load(sd.OUT / (cid + '.npy'))
    per = np.asarray([f.period for f in frames])
    z = np.load(se_load.PRIVATE / 'cases' / (cid + '.npz'))
    names = [str(s) for s in z['names']]
    tag, btags = sd.model_tags(cid)
    sup = np.load(se_load.PRIVATE / 'preds' / tag / (cid + '.npz'))['sup']
    sup = np.clip(sup, 1e-9, 1) ** 2.0; sup = np.clip(sup / sup.sum(1, keepdims=True), 1e-6, 1); sup /= sup.sum(1, keepdims=True)
    bnd = np.mean([np.load(se_load.PRIVATE / 'preds' / t / (cid + '.npz'))['bnd'] for t in btags], 0)
    lab = np.array(['HADX'.index(s) for s in assemble(frames, sup, (), missing_w=rt.MISSING_W, cost=rt.SWITCH_COST,
                                                       cost_rows=rt.cost_rows(z['X'], names, bnd))['gapko']])
    seen = np.array([f.ball_observed for f in frames])
    runlen = np.zeros(len(frames), int)
    i = 0
    while i < len(frames):
        if seen[i] or per[i] == 0:
            i += 1; continue
        j = i
        while j < len(frames) and not seen[j] and per[j] == per[i]:
            j += 1
        runlen[i:j] = j - i; i = j
    stats = gl.player_speed_statistics(frames)
    sp = np.array([np.nan if v is None else v for v in stats])
    # spread the 1-in-5 samples to neighbours
    idx = np.flatnonzero(~np.isnan(sp)); fill = np.interp(np.arange(len(sp)), idx, sp[idx]) if len(idx) else sp
    inside = runlen > gl.LONG_GAP
    refspeed = float(np.nanmedian(np.where(inside | (per == 0), np.nan, sp)))
    act = per > 0
    m = act & (ref == 2) & (lab < 2) & ~seen
    bins = [(1, 25), (26, 75), (76, 250), (251, 750), (751, 10 ** 9)]
    out = {f'len_{a}_{b}': int((m & (runlen >= a) & (runlen <= b)).sum()) for a, b in bins}
    rel = fill / refspeed
    for lo, hi in ((0, .75), (.75, 1.0), (1.0, 1.5), (1.5, 99)):
        out[f'speed_{lo}_{hi}'] = int((m & (rel >= lo) & (rel < hi)).sum())
    live_unseen = act & (ref < 2) & ~seen
    for a, b in bins:
        out[f'live_len_{a}_{b}'] = int((live_unseen & (runlen >= a) & (runlen <= b)).sum())
    out['n'] = int(m.sum())
    return cid, out


if __name__ == '__main__':
    with Pool(2) as pool:
        res = dict(pool.map(one, list(sd.DEV_SC + sd.NEW_SC)))
    tot = {}
    for r in res.values():
        for k, v in r.items():
            tot[k] = tot.get(k, 0) + v
    n = tot['n']
    print('missed dead frames with ball not visible:', n)
    for k in [k for k in tot if k.startswith('len_')]:
        print(f'  gap {k[4:]:>12s} frames: missed {tot[k] / n:5.1%}   live unseen {tot["live_" + k]:8d}')
    for k in [k for k in tot if k.startswith('speed_')]:
        print(f'  player speed / match typical {k[6:]:>10s}: {tot[k] / n:5.1%}')
