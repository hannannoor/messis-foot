"""Round 11: label-free ball-position dead-ball rules applied after the v9 decoder (gap rule), external data only.

    python se_rule_dead.py [procs]      -> scores2/rule_dead.json + table

Rules (pitch 0..105.3 x 0..68 m, as every adapter and the provided match use):
  out<m>      ball observed more than <m> metres outside a touchline or goal line -> D
  outgap<m>   as out<m>, and D continues through the ball gap that directly follows (ball went out, then vanished)
  still<s>    ball observed and moving under 0.3 m/s for at least <s> seconds -> D
Matches and references (models never trained on the match):
  DFL dev (6) and SkillCorner dev (7): v8-recipe CV folds (B8); SkillCorner added (10) and WCSF: dev-only models (HB8).
  DFL and WCSF are scored against their tracking-derived references; SkillCorner against the event-derived stoppage
  reference (sc_deadref/).
Pass rule, fixed before the run: a rule is kept only if WCSF and the DFL mean each change by no less than -0.002 and
the SkillCorner mean gain is at least 2 SE. The locked holdout is then used once to confirm the kept rule.
"""
import json
import sys
from multiprocessing import Pool

import numpy as np

import se_load
import se_sc_dead as sd

L, W = 105.3, 68.0
DFL_DEV = tuple(c for c in se_load.ALL if c.startswith('dfl') and c not in se_load.HOLDOUT)
RULES = ('v9', 'out0.5', 'out1', 'outgap0.5', 'outgap1', 'still2', 'still4', 'outgapt0.5', 'outgapt1')


def tags(cid):
    if cid in DFL_DEV or cid in sd.DEV_SC:
        return 'B8', ('r8ba', 'r8bb')
    return 'HB8', ('H_r8ba', 'H_r8bb')


def apply_rule(rule, lab, frames):
    lab = lab.copy()
    seen = np.array([f.ball_observed for f in frames])
    bx = np.array([f.ball_x if f.ball_observed else np.nan for f in frames], float)
    by = np.array([f.ball_y if f.ball_observed else np.nan for f in frames], float)
    per = np.array([f.period for f in frames])
    act = per > 0
    if rule.startswith('out'):
        m = float(rule.lstrip('outgap'))
        out = seen & act & ((bx < -m) | (bx > L + m) | (by < -m) | (by > W + m))
        if rule.startswith('outgapt'):   # restart taken from outside the line (throw-in): release D 0.4 s before re-entry
            n = len(out)
            i = 0
            while i < n:
                if not out[i]:
                    i += 1
                    continue
                j = i
                while j < n and out[j]:
                    j += 1
                if j < n and seen[j] and per[j] == per[i]:
                    out[max(i, j - 10):j] = False
                i = j
            rule = 'outgap' + rule[7:]
        lab[out] = 2
        if rule.startswith('outgap'):   # (also the trimmed variants)
            n = len(lab)
            for i in np.flatnonzero(out):
                j = i + 1
                if j < n and not seen[j] and per[j] == per[i]:
                    while j < n and not seen[j] and per[j] == per[i]:
                        lab[j] = 2
                        j += 1
    elif rule.startswith('still'):
        s = float(rule[5:])
        k = 10
        sp = np.full(len(lab), np.inf)
        sp[k:] = np.hypot(bx[k:] - bx[:-k], by[k:] - by[:-k]) / (k / 25)
        still = seen & act & (sp < .3)
        i, n, need = 0, len(lab), int(s * 25)
        while i < n:
            if not still[i]:
                i += 1
                continue
            j = i
            while j < n and still[j]:
                j += 1
            if j - i >= need:
                lab[max(0, i - k):j] = 2
            i = j
    return lab


def one(cid):
    import strong_runtime as rt
    from memory_ablation_metrics import score_variant
    from se_assembly import assemble
    frames, ref = se_load.load(cid)
    if cid.startswith('skillcorner'):
        ref = np.load(sd.OUT / (cid + '.npy'))
    per = np.asarray([f.period for f in frames], np.uint8)
    obs = np.asarray([f.ball_observed for f in frames], bool)
    z = np.load(se_load.PRIVATE / 'cases' / (cid + '.npz'))
    names = [str(s) for s in z['names']]
    tag, btags = tags(cid)
    sup = np.load(se_load.PRIVATE / 'preds' / tag / (cid + '.npz'))['sup']
    sup = np.clip(sup, 1e-9, 1) ** 2.0
    sup = np.clip(sup / sup.sum(1, keepdims=True), 1e-6, 1)
    sup /= sup.sum(1, keepdims=True)
    bnd = np.mean([np.load(se_load.PRIVATE / 'preds' / t / (cid + '.npz'))['bnd'] for t in btags], 0)
    base = np.array(['HADX'.index(s) for s in assemble(frames, sup, (), missing_w=rt.MISSING_W, cost=rt.SWITCH_COST,
                                                        cost_rows=rt.cost_rows(z['X'], names, bnd))['gapko']], np.uint8)
    out = {}
    for rule in RULES:
        lab = base if rule == 'v9' else apply_rule(rule, base, frames)
        r = score_variant(ref, lab, per, obs)
        out[rule] = dict(full=r['metrics']['spell_f1_mean'], dead_recall=r['dead']['recall'], dead_precision=r['dead']['precision'],
                         changed=int((lab != base).sum()))
    return cid, out


if __name__ == '__main__':
    cids = list(DFL_DEV) + ['wcsf-used-match'] + list(sd.DEV_SC + sd.NEW_SC)
    with Pool(int(sys.argv[1]) if len(sys.argv) > 1 else 3) as pool:
        res = dict(pool.map(one, cids))
    (se_load.PRIVATE / 'scores2' / 'rule_dead.json').write_text(json.dumps(res, indent=1))
    groups = {'DFL dev (6)': list(DFL_DEV), 'WCSF': ['wcsf-used-match'], 'SkillCorner (17)': list(sd.DEV_SC + sd.NEW_SC)}
    for rule in [r for r in RULES[1:] if len(sys.argv) < 3 or r in sys.argv[2].split(',')]:
        print(rule)
        for g, cs in groups.items():
            d = np.array([res[c][rule]['full'] - res[c]['v9']['full'] for c in cs])
            se = d.std(ddof=1) / np.sqrt(len(d)) if len(d) > 1 else float('nan')
            print(f'   {g:17s} v9 {np.mean([res[c]["v9"]["full"] for c in cs]):.4f}  change {d.mean():+.4f} +- {se:.4f}  up {int((d > 0).sum())}/{len(d)}'
                  f'  dead R {np.mean([res[c]["v9"]["dead_recall"] for c in cs]):.3f}->{np.mean([res[c][rule]["dead_recall"] for c in cs]):.3f}'
                  f'  P {np.mean([res[c]["v9"]["dead_precision"] for c in cs]):.3f}->{np.mean([res[c][rule]["dead_precision"] for c in cs]):.3f}'
                  f'  frames changed {sum(res[c][rule]["changed"] for c in cs)}')
