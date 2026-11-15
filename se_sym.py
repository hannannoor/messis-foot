"""Home/away swap for symmetric augmentation (pure numpy)."""
import numpy as np


def swap_plan(names):
    """(perm, sign, one_minus) such that X_swapped = X[:, perm] * sign (+ 1 - x for one_minus cols)."""
    idx = {n: i for i, n in enumerate(names)}
    perm = list(range(len(names)))
    sign = np.ones(len(names))
    onem = np.zeros(len(names), bool)
    pairs = [('f18_1', 'f18_2'), ('f18_3', 'f18_4'), ('f18_13', 'f18_14'), ('f18_15', 'f18_16'), ('nH', 'nA'),
             ('h_spread', 'a_spread'), ('spd_H', 'spd_A'), ('spd_nearH', 'spd_nearA'), ('close_h1', 'close_a1')]
    pairs += [(f'dH{k}', f'dA{k}') for k in range(3)]
    pairs += [(f'nH{r}', f'nA{r}') for r in ('2', '5', '10')]
    for a, b in pairs:
        if a in idx and b in idx:
            perm[idx[a]], perm[idx[b]] = idx[b], idx[a]
    if 'ball_minus_hcx' in idx and 'ball_minus_acx' in idx:
        perm[idx['ball_minus_hcx']], perm[idx['ball_minus_acx']] = idx['ball_minus_acx'], idx['ball_minus_hcx']
        sign[idx['ball_minus_hcx']] = sign[idx['ball_minus_acx']] = -1
    for w in ('p12', 'f12', 'p25', 'f25'):
        a, b = f'itouchH_{w}', f'itouchA_{w}'
        if a in idx and b in idx:
            perm[idx[a]], perm[idx[b]] = idx[b], idx[a]
    for n, i in idx.items():
        if n.startswith('tsH_') and 'tsA_' + n[4:] in idx:
            perm[i], perm[idx['tsA_' + n[4:]]] = idx['tsA_' + n[4:]], i
    for n in ('itouch_last', 'itouch_next', 'rtouch_last', 'rtouch_next'):
        if n in idx:
            sign[idx[n]] = -1
    for n, i in idx.items():
        if n.startswith(('itouch', 'rtouch', 'tsH_', 'tsA_')):
            continue
        base = n.split('_p')[0].split('_f')[0]
        if n.endswith('_sup'):
            continue
        if n in ('f18_5', 'margin', 'margin_tanh', 'last_touch', 'next_touch', 'last_ctl', 'next_ctl', 'ball_rx',
                 'bvx_home') or base in ('margin', 'touch', 'bvx'):
            sign[i] = -1
        if base == 'nearH':
            onem[i] = True
    return np.asarray(perm), sign, onem


def swapped(X, plan):
    perm, sign, onem = plan
    Y = X[:, perm] * sign.astype(np.float32)
    Y[:, onem] = np.where(Y[:, onem] != 0, 1 - Y[:, onem], 0)
    return Y


