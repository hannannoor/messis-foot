"""Train ownership + liveness heads (HistGradientBoosting) and write supports per held-out match.

    python se_train.py <tag> cv        # grouped 4-fold over DEV matches -> preds/<tag>/<dev cid>.npz
    python se_train.py <tag> final     # train on all DEV, predict HOLDOUT (+ dev in-sample, flagged)
Options via env-free JSON in argv[3] (optional): {"drop": [...prefixes], "iter": 300, "step": 4}
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier

from se_sym import swap_plan, swapped

PRIVATE = Path(__file__).resolve().parent.parent / 'strong-emissions-reference'
SC = ('1874553', '1886347', '2007448', '2007721', '2010085', '2011166', '2013725', '2015213', '2016236', '2017461')
DFL = ('J03WMX', 'J03WN1', 'J03WOH', 'J03WOY', 'J03WPY', 'J03WQQ', 'J03WR9')
ALL = tuple('skillcorner-' + m for m in SC) + tuple('dfl-' + m for m in DFL) + ('wcsf-used-match',)
HOLDOUT = ('wcsf-used-match', 'dfl-J03WN1', 'skillcorner-2013725', 'skillcorner-2016236', 'skillcorner-2017461')
DEV = tuple(c for c in ALL if c not in HOLDOUT)
FOLDS = (('dfl-J03WR9', 'dfl-J03WMX', 'skillcorner-1874553', 'skillcorner-2007448'),
         ('dfl-J03WOH', 'dfl-J03WQQ', 'skillcorner-1886347', 'skillcorner-2010085'),
         ('dfl-J03WOY', 'skillcorner-2007721', 'skillcorner-2011166'),
         ('dfl-J03WPY', 'skillcorner-2015213'))
assert sorted(sum(FOLDS, ())) == sorted(DEV)


def load(cid, keep):
    z = np.load(PRIVATE / 'cases' / (cid + '.npz'))
    X = z['X'][:, keep]
    return X, z['ref'], z['period'], z['observed']


def columns(opts):
    names = [str(s) for s in np.load(PRIVATE / 'cases' / (DEV[0] + '.npz'))['names']]
    drop = tuple(opts.get('drop', ()))
    keep_only = tuple(opts.get('only', ()))
    keep = [i for i, n in enumerate(names) if not n.startswith(drop or ('\0',))
            and (not keep_only or n.startswith(keep_only))]
    return keep, [names[i] for i in keep]


def rows(cids, keep, step, head):
    Xs, ys, ws = [], [], []
    for cid in cids:
        X, ref, per, obs = load(cid, keep)
        if head == 'own':
            m = (ref < 2) & (per > 0)
        else:
            if cid.startswith('skillcorner'):
                continue
            m = (ref < 3) & (per > 0)
        idx = np.flatnonzero(m)[::step]
        y = (ref[idx] == 0) if head == 'own' else (ref[idx] == 2)
        Xs.append(X[idx]); ys.append(y); ws.append(np.full(len(idx), 1.0 / max(1, len(idx))))
    return np.concatenate(Xs), np.concatenate(ys), np.concatenate(ws) * 1e5


def fit(X, y, w, opts):
    clf = HistGradientBoostingClassifier(max_iter=opts.get('iter', 300), learning_rate=opts.get('lr', .08),
                                         max_leaf_nodes=opts.get('leaves', 63), min_samples_leaf=opts.get('minleaf', 200),
                                         l2_regularization=1.0, max_bins=255, early_stopping=False, random_state=1729)
    clf.fit(X, y, sample_weight=w)
    return clf


def predict(models, cid, keep, plan=None):
    X, ref, per, obs = load(cid, keep)
    ph = models['own'].predict_proba(X)[:, 1]
    if plan is not None:
        ph = .5 * (ph + 1 - models['own'].predict_proba(swapped(X, plan))[:, 1])
    pd = models['live'].predict_proba(X)[:, 1]
    sup = np.column_stack(((1 - pd) * ph, (1 - pd) * (1 - ph), pd))
    return sup


def run(tag, mode, opts):
    keep, names = columns(opts)
    step = opts.get('step', 4)
    out = PRIVATE / 'preds' / tag
    out.mkdir(parents=True, exist_ok=True)
    (out / 'opts.json').write_text(json.dumps(dict(opts, mode=mode, n_features=len(keep))))
    folds = [(tuple(c for c in DEV if c not in f), f) for f in FOLDS] if mode == 'cv' else [(DEV, HOLDOUT)] if mode == 'final' else [(ALL, ())]
    for train, test in folds:
        t = time.time()
        sp = swap_plan(names) if opts.get('sym') else None
        models = {}
        for h in ('own', 'live'):
            X, y, w = rows(train, keep, step, h)
            if h == 'own' and sp is not None:
                X, y, w = np.concatenate([X, swapped(X, sp)]), np.concatenate([y, ~y]), np.concatenate([w, w])
            models[h] = fit(X, y, w, opts)
        for cid in test:
            np.savez_compressed(out / (cid + '.npz'), sup=predict(models, cid, keep, sp))
        if mode in ('final', 'all'):
            X, _, _, _ = (lambda z: (z['X'][:, keep], 0, 0, 0))(np.load(PRIVATE / 'provided' / 'features.npz'))
            ph = models['own'].predict_proba(X)[:, 1]
            if sp is not None:
                ph = .5 * (ph + 1 - models['own'].predict_proba(swapped(X, sp))[:, 1])
            pdd = models['live'].predict_proba(X)[:, 1]
            np.savez_compressed(out / 'provided.npz', sup=np.column_stack(((1 - pdd) * ph, (1 - pdd) * (1 - ph), pdd)))
            import pickle
            (out / 'models.pkl').write_bytes(pickle.dumps(dict(models=models, names=names)))
        print('fold', test, round(time.time() - t, 1), flush=True)


if __name__ == '__main__':
    run(sys.argv[1], sys.argv[2], json.loads(sys.argv[3]) if len(sys.argv) > 3 else {})
