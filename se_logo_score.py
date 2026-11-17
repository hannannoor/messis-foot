"""Round 10: score the Metrica leave-one-game-out, ownership-only, against the ball-flag reference.
    python se_logo_score.py [processes]      -> scores2/metrica_logo.json and a table
Two arms per held-out game, each one v8-recipe model set (2 GRUs + boosted trees, equal geometric blend, power 2)
decoded exactly like the release (switch cost 20, touch cost, boundary cost, 'gapko' stage):
  baseline  trained on the 18 external matches (preds/lgbasea, lgbaseb, lgbaseg)
  metrica   the same recipe plus the two OTHER Metrica games, supervised for ownership only (preds/lo<k>a, b, g)
An arm whose predictions are not there yet is skipped. Scores: see se_metrica_rescore.py ('ownership' is the evidence).
"""
import json
import sys
from multiprocessing import Pool

import numpy as np

import se_load
from se_metrica_rescore import ownership_only

GAMES = tuple('metrica-' + g for g in se_load.METRICA)
ARMS = {'baseline': lambda k: ('lgbasea', 'lgbaseb', 'lgbaseg'), 'metrica': lambda k: (f'lo{k}a', f'lo{k}b', f'lo{k}g'),
        # round 10 retrain recipe (state-dependent copies + swap fix), all external data, no Metrica in training
        'c10': lambda k: ('c10a', 'c10b', 'c10g')}


def set_supports(tags, cid):
    """One model set, as strong_runtime._set_logp + supports() with a single set. Returns (supports, boundary)."""
    parts, bnds = [], []
    for tag in tags:
        z = np.load(se_load.PRIVATE / 'preds' / tag / (cid + '.npz'))
        parts.append(np.asarray(z['sup'], np.float64))
        if 'bnd' in z.files and z['bnd'].ndim == 1 and len(z['bnd']) == len(z['sup']):
            bnds.append(np.asarray(z['bnd'], np.float64))
    lp = sum(np.log(np.clip(p, 1e-9, 1)) for p in parts) / len(parts)
    p = np.exp(lp - lp.max(1, keepdims=True))
    p /= p.sum(1, keepdims=True)
    p = np.clip(p, 1e-9, 1) ** 2.0
    p /= p.sum(1, keepdims=True)
    p = np.clip(p, 1e-6, 1)
    return p / p.sum(1, keepdims=True), (np.mean(bnds, 0) if bnds else None)


def one(cid):
    import strong_runtime as rt
    from memory_ablation_metrics import score_variant
    from se_assembly import assemble
    k = GAMES.index(cid) + 1
    frames, _ = se_load.load(cid)
    ref = np.load(se_load.PRIVATE / 'metrica_ballref' / (cid + '.npy'))
    per = np.asarray([f.period for f in frames], np.uint8)
    obs = np.asarray([f.ball_observed for f in frames], bool)
    z = np.load(se_load.PRIVATE / 'cases' / (cid + '.npz'))
    names = [str(s) for s in z['names']]
    X = z['X']
    out = {}
    for arm, tags_for in ARMS.items():
        tags = tags_for(k)
        if not all((se_load.PRIVATE / 'preds' / t / (cid + '.npz')).exists() for t in tags):
            continue
        sup, bnd = set_supports(tags, cid)
        st = assemble(frames, sup, (), missing_w=rt.MISSING_W, cost=rt.SWITCH_COST, cost_rows=rt.cost_rows(X, names, bnd))['gapko']
        lab = np.asarray(['HADX'.index(s) for s in st], np.uint8)
        np.save(se_load.PRIVATE / 'scores2' / f'metrica_logo_{arm}_{cid}.npy', lab)
        own = score_variant(ref, ownership_only(ref, lab), per, obs)
        full = score_variant(ref, lab, per, obs)
        live = ref < 2
        out[arm] = dict(ownership=own['metrics']['spell_f1_mean'], ball=full['metrics']['spell_f1_mean'],
                        short_recall=own['short_spells']['recall'], spells_gt=own['spells']['n_gt'], spells_pred=own['spells']['n_pred'],
                        team_accuracy=float((lab[live & (lab < 2)] == ref[live & (lab < 2)]).mean()),
                        dead_recall=full['dead']['recall'], dead_precision=full['dead']['precision'])
    return cid, out


if __name__ == '__main__':
    with Pool(int(sys.argv[1]) if len(sys.argv) > 1 else 3) as pool:
        res = dict(pool.map(one, GAMES))
    (se_load.PRIVATE / 'scores2' / 'metrica_logo.json').write_text(json.dumps(res, indent=1))
    for arm in ARMS:
        rows = [res[c].get(arm) for c in GAMES]
        if not all(rows):
            print(f'{arm:9s} predictions missing for {[c for c, r in zip(GAMES, rows) if not r]}')
            continue
        print(f'{arm:9s} ownership ' + ' '.join(f'{r["ownership"]:.4f}' for r in rows) + f'  mean {np.mean([r["ownership"] for r in rows]):.4f}'
              + ' | short ' + ' '.join(f'{r["short_recall"]:.2f}' for r in rows)
              + ' | spells gt/pred ' + ' '.join(f'{r["spells_gt"]}/{r["spells_pred"]}' for r in rows)
              + ' | team acc ' + ' '.join(f'{r["team_accuracy"]:.3f}' for r in rows)
              + ' | full ' + ' '.join(f'{r["ball"]:.4f}' for r in rows))
    for arm in ARMS:
        if arm != 'baseline' and all(arm in res[c] and 'baseline' in res[c] for c in GAMES):
            d = np.array([res[c][arm]['ownership'] - res[c]['baseline']['ownership'] for c in GAMES])
            print(f'{arm} - baseline (ownership): {d.mean():+.4f} +- {d.std(ddof=1) / np.sqrt(len(d)):.4f}  per game {d.round(4).tolist()}  up {int((d > 0).sum())}/3')
