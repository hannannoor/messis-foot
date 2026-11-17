"""Round 11: what do the stoppages v9 misses look like? SkillCorner (external), event-derived dead-ball labels.

    python se_dead_diag.py [procs]     -> scores2/dead_diag.json + table (aggregate counts only)

For every active frame: reference (live / dead, and the stoppage kind from the provider's events), v9's label (release
decoder + gap rule, models that never trained on the match), and simple tracking cues:
  seen      ball observed
  still     ball observed and moving < 0.5 m/s (over 0.4 s)
  out       ball observed outside the pitch lines (> 0.5 m)
  edge      ball observed within 2 m of a touchline or goal line
  spot      ball observed within 1.5 m of a corner, a penalty spot or the centre spot
Counts are reported for missed dead frames (dead in the reference, H/A from v9) and for live frames (false-alarm
base rate of each cue).
"""
import json
import sys
from math import hypot
from multiprocessing import Pool

import numpy as np

import se_load
import se_sc_dead as sd

L, W = 105.3, 68.0   # pitch used by the adapters (0..L, 0..W)
SPOTS = ((0, 0), (0, W), (L, 0), (L, W), (11, W / 2), (L - 11, W / 2), (L / 2, W / 2))


def cues(frames):
    n = len(frames)
    seen = np.array([f.ball_observed for f in frames])
    bx = np.array([f.ball_x if f.ball_observed else np.nan for f in frames], float)
    by = np.array([f.ball_y if f.ball_observed else np.nan for f in frames], float)
    k = 10   # 0.4 s
    sp = np.full(n, np.nan)
    sp[k:] = np.hypot(bx[k:] - bx[:-k], by[k:] - by[:-k]) / (k / 25)
    still = seen & (sp < .5)
    out = seen & ((bx < -.5) | (bx > L + .5) | (by < -.5) | (by > W + .5))
    edge = seen & ~out & ((bx < 2) | (bx > L - 2) | (by < 2) | (by > W - 2))
    spot = seen & np.any([np.hypot(bx - x, by - y) < 1.5 for x, y in SPOTS], axis=0)
    return dict(seen=seen, still=still, out=out, edge=edge, spot=spot), (np.nanmin(bx), np.nanmax(bx), np.nanmin(by), np.nanmax(by))


def kinds(cid, n):
    src, _, per = sd.source_frames(cid)
    kind = np.full(n, '', object)
    for a, b, k in sd.stoppages(cid.split('-', 1)[1]):
        kind[(src >= a) & (src < b)] = k.replace('_for', '').replace('_against', '')
    return kind


def one(cid):
    import gap_liveness as gl
    import strong_runtime as rt
    from se_assembly import assemble
    frames, _ = se_load.load(cid)
    ref = np.load(sd.OUT / (cid + '.npy'))
    per = np.asarray([f.period for f in frames])
    z = np.load(se_load.PRIVATE / 'cases' / (cid + '.npz'))
    names = [str(s) for s in z['names']]
    tag, btags = sd.model_tags(cid)
    sup = np.load(se_load.PRIVATE / 'preds' / tag / (cid + '.npz'))['sup']
    sup = np.clip(sup, 1e-9, 1) ** 2.0
    sup = np.clip(sup / sup.sum(1, keepdims=True), 1e-6, 1)
    sup /= sup.sum(1, keepdims=True)
    bnd = np.mean([np.load(se_load.PRIVATE / 'preds' / t / (cid + '.npz'))['bnd'] for t in btags], 0)
    lab = np.array(['HADX'.index(s) for s in assemble(frames, sup, (), missing_w=rt.MISSING_W, cost=rt.SWITCH_COST,
                                                       cost_rows=rt.cost_rows(z['X'], names, bnd))['gapko']])
    c, rng = cues(frames)
    kind = kinds(cid, len(frames))
    act = per > 0
    missed = act & (ref == 2) & (lab < 2)
    hit = act & (ref == 2) & (lab == 2)
    live = act & (ref < 2)
    out = dict(range=[round(float(v), 1) for v in rng], n_dead=int((act & (ref == 2)).sum()), n_missed=int(missed.sum()),
               n_hit=int(hit.sum()), n_live=int(live.sum()))
    for name, m in c.items():
        out['missed_' + name] = int((missed & m).sum())
        out['live_' + name] = int((live & m).sum())
        out['hit_' + name] = int((hit & m).sum())
    for k in set(kind[act & (ref == 2)]):
        out['missed_kind_' + k] = int((missed & (kind == k)).sum())
        out['dead_kind_' + k] = int((act & (ref == 2) & (kind == k)).sum())
    return cid, out


if __name__ == '__main__':
    cids = list(sd.DEV_SC + sd.NEW_SC)
    with Pool(int(sys.argv[1]) if len(sys.argv) > 1 else 2) as pool:
        res = dict(pool.map(one, cids))
    (se_load.PRIVATE / 'scores2' / 'dead_diag.json').write_text(json.dumps(res, indent=1))
    tot = {}
    for r in res.values():
        for k, v in r.items():
            if k != 'range':
                tot[k] = tot.get(k, 0) + v
    print('coordinate ranges (x min/max, y min/max):', [r['range'] for r in list(res.values())[:3]])
    nd, nm, nh, nl = tot['n_dead'], tot['n_missed'], tot['n_hit'], tot['n_live']
    print(f'dead frames {nd}, missed by v9 {nm} ({nm / nd:.0%}), live frames {nl}')
    print(f'{"cue":6s} {"missed dead":>12s} {"caught dead":>12s} {"live (false-alarm base)":>24s}')
    for name in ('seen', 'still', 'out', 'edge', 'spot'):
        print(f'{name:6s} {tot["missed_" + name] / nm:12.1%} {tot["hit_" + name] / nh:12.1%} {tot["live_" + name] / nl:24.1%}')
    print('missed share by stoppage kind:')
    for k in sorted(x[len('dead_kind_'):] for x in tot if x.startswith('dead_kind_')):
        print(f'  {k or "(none)":14s} dead {tot["dead_kind_" + k]:7d}  missed {tot.get("missed_kind_" + k, 0) / tot["dead_kind_" + k]:5.0%}')
