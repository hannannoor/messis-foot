"""Round 11: predict extra matches with a model trained in 'final' or 'all' mode (preds/<tag>/model.pt or models.pkl).

    python se_predict_final.py <tag> <cid> [<cid> ...]     -> preds/<tag>/<cid>.npz  (sup, and bnd for GRUs)
Used to score the ten added SkillCorner matches with models that never trained on them.
"""
import pickle
import sys

import numpy as np

import se_load

P = se_load.PRIVATE


def gru(tag, cids):
    import torch
    import se_gru
    from se_sym import swap_plan
    ck = torch.load(P / 'preds' / tag / 'model.pt', map_location='cpu', weights_only=False)
    o = ck['opts']
    se_gru.KEEP_NAMES = list(ck['names'])
    net = se_gru.Net(len(ck['names']), o.get('hidden', 128), o.get('layers', 2), o.get('drop', .1),
                     4 if o.get('bnd') else 3).to(se_gru.DEVICE)
    net.load_state_dict(ck['state'])
    plan = swap_plan(list(ck['names']), fix=bool(o.get('symfix')))
    for cid in cids:
        sup = se_gru.predict(net, None, plan, (ck['mu'], ck['sd']), P / 'cases' / (cid + '.npz'))
        np.savez_compressed(P / 'preds' / tag / (cid + '.npz'), sup=sup, bnd=se_gru.LAST_BND[0])
        print(tag, cid, flush=True)


def gbm(tag, cids):
    import se_train
    from se_sym import swap_plan, swapped
    blob = pickle.loads((P / 'preds' / tag / 'models.pkl').read_bytes())
    m = blob['models']
    plan = swap_plan(list(blob['names']), fix=bool(blob.get('symfix')))
    for cid in cids:
        z = np.load(P / 'cases' / (cid + '.npz'))
        names = [str(s) for s in z['names']]
        X = z['X'][:, [names.index(n) for n in blob['names']]]
        ph = .5 * (m['own'].predict_proba(X)[:, 1] + 1 - m['own'].predict_proba(swapped(X, plan))[:, 1])
        pd = m['live'].predict_proba(X)[:, 1]
        np.savez_compressed(P / 'preds' / tag / (cid + '.npz'), sup=np.column_stack(((1 - pd) * ph, (1 - pd) * (1 - ph), pd)))
        print(tag, cid, flush=True)


if __name__ == '__main__':
    tag, cids = sys.argv[1], sys.argv[2:]
    (gru if (P / 'preds' / tag / 'model.pt').exists() else gbm)(tag, cids)
