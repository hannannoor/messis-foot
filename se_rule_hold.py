"""Round 11: one confirmation look at the locked holdout for the ball-out rule (outgapt1). Dev-only models (HB8)."""
from multiprocessing import Pool
import numpy as np
import se_load, se_sc_dead as sd
import se_rule_dead as r


def hold(cid):
    import strong_runtime as rt
    from memory_ablation_metrics import score_variant
    from se_assembly import assemble
    frames, ref = se_load.load(cid)
    if cid.startswith('skillcorner'):
        ref = np.load(sd.OUT / (cid + '.npy'))
    per = np.asarray([f.period for f in frames], np.uint8); obs = np.asarray([f.ball_observed for f in frames], bool)
    z = np.load(se_load.PRIVATE / 'cases' / (cid + '.npz')); names = [str(s) for s in z['names']]
    sup = np.load(se_load.PRIVATE / 'preds' / 'HB8' / (cid + '.npz'))['sup']
    sup = np.clip(sup, 1e-9, 1) ** 2.0; sup = np.clip(sup / sup.sum(1, keepdims=True), 1e-6, 1); sup /= sup.sum(1, keepdims=True)
    bnd = np.mean([np.load(se_load.PRIVATE / 'preds' / t / (cid + '.npz'))['bnd'] for t in ('H_r8ba', 'H_r8bb')], 0)
    base = np.array(['HADX'.index(s) for s in assemble(frames, sup, (), missing_w=rt.MISSING_W, cost=rt.SWITCH_COST,
                                                        cost_rows=rt.cost_rows(z['X'], names, bnd))['gapko']], np.uint8)
    lab = r.apply_rule('outgapt1', base, frames)
    return cid, score_variant(ref, base, per, obs)['metrics']['spell_f1_mean'], score_variant(ref, lab, per, obs)['metrics']['spell_f1_mean']


if __name__ == '__main__':
    with Pool(4) as p:
        for cid, a, b in p.map(hold, ('dfl-J03WN1', 'skillcorner-2013725', 'skillcorner-2016236', 'skillcorner-2017461')):
            print(f'holdout {cid:22s} v9 {a:.4f}  outgapt1 {b:.4f}  change {b - a:+.4f}', flush=True)
