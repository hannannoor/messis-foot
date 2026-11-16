"""Predict a new evaluation view with saved CV fold models (no retraining).

    python se_predict.py <tag> <view_dir> [<view_dir> ...]
GRU tags (fold*.pt) need the PyTorch env; GBM tags (fold*.pkl) need the scikit-learn env.
Writes preds/<tag>/<view_dir>/<cid>.npz for each fold's held-out matches that exist in the view.
"""
import pickle
import sys

import numpy as np

import se_load

P = se_load.PRIVATE


def gru(tag, views):
    import torch
    import se_gru
    for f in sorted((P / 'preds' / tag).glob('fold*.pt')):
        ck = torch.load(f, map_location='cpu', weights_only=False)
        opts = ck['opts']
        se_gru.XDROP = tuple(opts.get('xdrop', ()))
        se_gru.KEEP_NAMES = list(ck['names'])
        net = se_gru.Net(len(ck['names']), ck['hidden'], ck['layers'], opts.get('drop', .1), ck.get('n_out', 3)).to(se_gru.DEVICE)
        net.load_state_dict(ck['state'])
        plan = se_gru.swap_plan(ck['names'])
        for v in views:
            for cid in ck['test']:
                vp = P / v / (cid + '.npz')
                if vp.exists():
                    (P / 'preds' / tag / v).mkdir(parents=True, exist_ok=True)
                    sup = se_gru.predict(net, None, plan, (ck['mu'], ck['sd']), vp)
                    np.savez_compressed(P / 'preds' / tag / v / (cid + '.npz'), sup=sup, bnd=se_gru.LAST_BND[0])


def gbm(tag, views):
    from se_sym import swapped, swap_plan
    for f in sorted((P / 'preds' / tag).glob('fold*.pkl')):
        b = pickle.loads(f.read_bytes())
        models, keep = b['models'], b['keep']
        sp = swap_plan(b['names']) if b['sym'] else None
        for v in views:
            for cid in b['test']:
                vp = P / v / (cid + '.npz')
                if not vp.exists():
                    continue
                z = np.load(vp); vn = [str(n) for n in z['names']]
                X = z['X'][:, [vn.index(n) for n in b['names']]]
                ph = models['own'].predict_proba(X)[:, 1]
                if sp is not None:
                    ph = .5 * (ph + 1 - models['own'].predict_proba(swapped(X, sp))[:, 1])
                pd = models['live'].predict_proba(X)[:, 1]
                (P / 'preds' / tag / v).mkdir(parents=True, exist_ok=True)
                np.savez_compressed(P / 'preds' / tag / v / (cid + '.npz'),
                                    sup=np.column_stack(((1 - pd) * ph, (1 - pd) * (1 - ph), pd)))


if __name__ == '__main__':
    tag, views = sys.argv[1], sys.argv[2:]
    if list((P / 'preds' / tag).glob('fold*.pt')):
        gru(tag, views)
    elif list((P / 'preds' / tag).glob('fold*.pkl')):
        gbm(tag, views)
    else:
        raise SystemExit(f'no saved fold models for {tag}')
    print('predicted', tag, views)
