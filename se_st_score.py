"""Round 11: score the self-training check. Paired, per target match, decoded exactly like the release.
    python se_st_score.py [suffixes, default a] [processes]      -> scores2/selftrain_<suffixes>.json and a table
Arms (model tags; suffix a/b = GRU seeds, g = boosted trees; one equal-weight set, power 2):
  base  trained without the target:   Metrica lgbase<s>, WCSF H_r8b<s> / H_g8p
  self  the same recipe plus the target's own decoded labels as ownership-only pseudo-labels: st<k><s>, stw<s>
Scores: 'ownership' (dead-ball calls taken out; the evidence on Metrica) and 'full'.
"""
import json
import sys
from multiprocessing import Pool

import numpy as np

import se_load
from se_logo_score import set_supports
from se_metrica_rescore import ownership_only

METRICA = tuple('metrica-' + g for g in se_load.METRICA)
WCSF = 'wcsf-used-match'
SUFFIX = 'a'


def tags(cid, arm):
    out = []
    for s in SUFFIX:
        if cid == WCSF:
            out.append(('stw' + s) if arm == 'self' else ('H_g8p' if s == 'g' else 'H_r8b' + s))
        else:
            out.append((f'st{METRICA.index(cid) + 1}{s}') if arm == 'self' else 'lgbase' + s)
    return tuple(out)


def one(args):
    cid, suffix = args
    global SUFFIX
    SUFFIX = suffix
    import strong_runtime as rt
    from memory_ablation_metrics import score_variant
    from se_assembly import assemble
    frames, ref = se_load.load(cid)
    if cid in METRICA:
        ref = np.load(se_load.PRIVATE / 'metrica_ballref' / (cid + '.npy'))
    per = np.asarray([f.period for f in frames], np.uint8)
    obs = np.asarray([f.ball_observed for f in frames], bool)
    z = np.load(se_load.PRIVATE / 'cases' / (cid + '.npz'))
    names = [str(s) for s in z['names']]
    X = z['X']
    out = {}
    for arm in ('base', 'self'):
        sup, bnd = set_supports(tags(cid, arm), cid)
        st = assemble(frames, sup, (), missing_w=rt.MISSING_W, cost=rt.SWITCH_COST, cost_rows=rt.cost_rows(X, names, bnd))['gapko']
        lab = np.asarray(['HADX'.index(s) for s in st], np.uint8)
        np.save(se_load.PRIVATE / 'scores2' / f'selftrain_{suffix}_{arm}_{cid}.npy', lab)
        own = score_variant(ref, ownership_only(ref, lab), per, obs)
        full = score_variant(ref, lab, per, obs)
        live = (ref < 2) & (lab < 2)
        out[arm] = dict(ownership=own['metrics']['spell_f1_mean'], full=full['metrics']['spell_f1_mean'],
                        short_recall=own['short_spells']['recall'], spells_gt=own['spells']['n_gt'],
                        spells_pred=own['spells']['n_pred'], team_accuracy=float((lab[live] == ref[live]).mean()))
    return cid, out


if __name__ == '__main__':
    suffix = sys.argv[1] if len(sys.argv) > 1 else 'a'
    SUFFIX = suffix
    cids = [c for c in METRICA + (WCSF,)
            if all((se_load.PRIVATE / 'preds' / t / (c + '.npz')).exists() for arm in ('base', 'self') for t in tags(c, arm))]
    with Pool(int(sys.argv[2]) if len(sys.argv) > 2 else 2) as pool:
        res = dict(pool.map(one, [(c, suffix) for c in cids]))
    (se_load.PRIVATE / 'scores2' / f'selftrain_{suffix}.json').write_text(json.dumps(res, indent=1))
    for key in ('ownership', 'full', 'team_accuracy', 'short_recall'):
        d = np.array([res[c]['self'][key] - res[c]['base'][key] for c in cids])
        print(f'{key:13s} base ' + ' '.join(f'{res[c]["base"][key]:.4f}' for c in cids)
              + ' | self ' + ' '.join(f'{res[c]["self"][key]:.4f}' for c in cids)
              + f' | diff {d.mean():+.4f} +- {d.std(ddof=1) / np.sqrt(len(d)) if len(d) > 1 else float("nan"):.4f}  up {int((d > 0).sum())}/{len(d)}')
    print('targets', cids)
    print('spells gt/pred base', [(res[c]['base']['spells_gt'], res[c]['base']['spells_pred']) for c in cids],
          'self', [res[c]['self']['spells_pred'] for c in cids])
