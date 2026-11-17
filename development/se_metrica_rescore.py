"""Round 10: rescore the saved round-9 Metrica predictions against the ball-flag reference.
    python se_metrica_rescore.py [processes]      -> scores2/metrica_rescore.json and a table
No inference and no fitting: saved label arrays (release, v2, v4-v8) and saved v8 supports (decoded with the v9
'gapko' stage). Three scores per release and game:
  event      official spell F1 against the round-9 event-derived reference (must reproduce round 9)
  ball       official spell F1 against the ball-flag reference. Dead ball there IS the ball flag, so any
             missing-ball rule is right by construction: not evidence about dead-ball detection.
  ownership  ball-flag reference with dead-ball calls taken out: the prediction takes the reference's D frames, and
             abstains (X, forward-filled by the scorer) wherever it said D on a reference-live frame.
"""
import json
import sys
from multiprocessing import Pool

import numpy as np

import se_load

SAVED = ('release', 'v2', 'v4', 'v5', 'v6', 'v8')
GAMES = tuple('metrica-' + g for g in se_load.METRICA)


def ownership_only(ref, lab):
    out = lab.copy()
    out[(ref < 2) & (lab == 2)] = 3
    out[ref == 2] = 2
    return out


def one(cid):
    import strong_runtime as rt
    from memory_ablation_metrics import score_variant
    from se_assembly import assemble
    frames, ref_event = se_load.load(cid)
    _, ref_ball = se_load.load(cid, reference='ball')
    per = np.asarray([f.period for f in frames], np.uint8)
    obs = np.asarray([f.ball_observed for f in frames], bool)
    scores2 = se_load.PRIVATE / 'scores2'
    labels = {name: np.load(scores2 / f'metrica_{name}_{cid}.npy') for name in SAVED}
    z = np.load(se_load.PRIVATE / 'cases' / (cid + '.npz'))
    names = [str(s) for s in z['names']]
    s8 = np.load(scores2 / f'metrica_sup_v8_{cid}.npz')
    stages = assemble(frames, s8['sup'], (), missing_w=rt.MISSING_W, cost=rt.SWITCH_COST,
                      cost_rows=rt.cost_rows(z['X'], names, s8['bnd'] if len(s8['bnd']) else None))
    code = lambda st: np.asarray(['HADX'.index(s) for s in st], np.uint8)
    if not np.array_equal(code(stages['nogap']), labels['v8']):
        raise ValueError('Saved v8 labels are not reproduced from the saved v8 supports')
    labels['v9'] = code(stages['gapko'])
    out = {}
    for name, lab in labels.items():
        full = score_variant(ref_ball, lab, per, obs)
        own = score_variant(ref_ball, ownership_only(ref_ball, lab), per, obs)
        out[name] = dict(event=score_variant(ref_event, lab, per, obs)['metrics']['spell_f1_mean'],
                         ball=full['metrics']['spell_f1_mean'], ownership=own['metrics']['spell_f1_mean'],
                         dead_precision=full['dead']['precision'], dead_recall=full['dead']['recall'],
                         ownership_short_recall=own['short_spells']['recall'],
                         ownership_spells=dict(gt=own['spells']['n_gt'], pred=own['spells']['n_pred']))
    act = per > 0
    counts = lambda r: {k: int((r[act] == i).sum()) for i, k in enumerate('HADX')}
    return cid, dict(scores=out, reference=dict(event=counts(ref_event), ball=counts(ref_ball),
                                                frames_changed=int((ref_event[act] != ref_ball[act]).sum())))


if __name__ == '__main__':
    with Pool(int(sys.argv[1]) if len(sys.argv) > 1 else 3) as pool:
        res = dict(pool.map(one, GAMES))
    (se_load.PRIVATE / 'scores2' / 'metrica_rescore.json').write_text(json.dumps(res, indent=1))
    for cid in GAMES:
        print(cid, 'reference labels', res[cid]['reference'])
    for key in ('event', 'ball', 'ownership'):
        print(f'\n{key}')
        for name in SAVED + ('v9',):
            v = [res[c]['scores'][name][key] for c in GAMES]
            print(f'  {name:8s}', ' '.join(f'{x:.4f}' for x in v), ' mean', round(float(np.mean(v)), 4))
    print('\ndead-ball precision / recall against the ball flag, and ownership short-possession recall (<=1 s)')
    for name in SAVED + ('v9',):
        row = [res[c]['scores'][name] for c in GAMES]
        print(f'  {name:8s}', ' '.join(f'{r["dead_precision"]:.3f}/{r["dead_recall"]:.3f}' for r in row),
              ' short', ' '.join(f'{r["ownership_short_recall"]:.2f}' for r in row),
              ' spells gt/pred', ' '.join(f'{r["ownership_spells"]["gt"]}/{r["ownership_spells"]["pred"]}' for r in row))
