"""Deterministic numpy inference for the strong-emission model (no torch / scikit-learn at runtime).

Each model set = geometric blend (equal weights) of two bidirectional-GRU heads and one gradient-boosted pair of
heads (ownership with home/away swap averaging, live/dead). v5 blends two sets geometrically (v4 set 0.3 on 171
features, v6 set 0.7 on 241 features incl. team-shape, trained with 3 ball-dropout views), then squares (power 2) and renormalises.
Models were fitted on external matches only (DFL, SkillCorner, WCSF); see docs/strong-emissions-results.md.
"""
from pathlib import Path

import numpy as np

from se_sym import swap_plan, swapped

MODEL_DIR = Path(__file__).resolve().parent / 'strong_model'
POWER = 2.0
MISSING_W = 1.0   # log-evidence weight on missing-ball rows (release: 0)
SWITCH_COST = 20.0  # decoder switch cost (release: 32)
GAP_RULE = 'gapko'  # v9: gap rule on the main decode, then kickoff patch (False = v3-v8 'nogap'; True = full release chain)
WINDOW, CONTEXT = 6000, 1500
SETS = (('gru.npz', 'gbm.npz', 0.15), ('gru8.npz', 'gbm8.npz', 0.85))   # (GRU file, GBM file, set weight)
TOUCH_COST, TOUCH_K = 10.0, 6   # v5: switch cost within +-TOUCH_K frames of an impulse contact
BND_LO = 8.0   # v8: switch cost falls towards 8 where the GRUs' boundary channel fires


def cost_rows(X, names, bnd=None):
    """Per-frame switch cost: TOUCH_COST near impulse contacts (itouch_last_dt == 0), SWITCH_COST elsewhere; with
    BND_LO set and boundary probabilities b given, also SWITCH_COST - (SWITCH_COST - BND_LO) * max_{+-2} b (minimum)."""
    names = list(names)
    t = (np.asarray(X)[:, names.index('itouch_last_dt')] == 0) & (np.asarray(X)[:, names.index('itouch_last')] != 0)
    near = np.convolve(t.astype(float), np.ones(2 * TOUCH_K + 1), 'same') > 0
    c = np.where(near, TOUCH_COST, SWITCH_COST)
    if BND_LO is not None and bnd is not None:
        b = np.maximum.reduce([np.roll(bnd, k) for k in range(-2, 3)])
        c = np.minimum(c, SWITCH_COST - (SWITCH_COST - BND_LO) * np.clip(b, 0, 1))
    return c


# ----- gradient-boosted heads ---------------------------------------------------------------------------------

def gbm_proba(m, head, X):
    X = np.asarray(X, np.float64)
    feat, thr = m[f'{head}_feature'], m[f'{head}_threshold']
    left, right, leaf = m[f'{head}_left'], m[f'{head}_right'], m[f'{head}_leaf']
    val, mleft = m[f'{head}_value'], m[f'{head}_missing_left']
    raw = np.full(len(X), float(m[f'{head}_baseline'][0]))
    rows = np.arange(len(X))
    for root in m[f'{head}_roots']:
        node = np.full(len(X), root, np.int64)
        while True:
            active = ~leaf[node]
            if not active.any():
                break
            n = node[active]
            x = X[rows[active], feat[n]]
            go_left = np.where(np.isnan(x), mleft[n], x <= thr[n])
            node[active] = np.where(go_left, left[n], right[n])
        raw += val[node]
    return 1.0 / (1.0 + np.exp(-raw))


def gbm_supports(m, X, plan):
    ph = gbm_proba(m, 'own', X)
    ph = .5 * (ph + 1 - gbm_proba(m, 'own', swapped(X, plan)))
    pd = gbm_proba(m, 'live', X)
    return np.column_stack(((1 - pd) * ph, (1 - pd) * (1 - ph), pd))


# ----- bidirectional GRU ---------------------------------------------------------------------------------------

def _erf(x):
    # Abramowitz & Stegun 7.1.26 (|error| < 1.5e-7)
    s = np.sign(x)
    a = np.abs(x)
    t = 1.0 / (1.0 + 0.3275911 * a)
    y = 1.0 - (((((1.061405429 * t - 1.453152027) * t) + 1.421413741) * t - 0.284496736) * t + 0.254829592) * t * np.exp(-a * a)
    return s * y


def _gelu(x):
    return 0.5 * x * (1.0 + _erf(x / np.sqrt(2.0)))


def _sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


def _gru_dir(xs, w_ih, w_hh, b_ih, b_hh, reverse):
    """xs: (B, T, D) -> (B, T, H). PyTorch gate order r, z, n."""
    B, T, _ = xs.shape
    H = w_hh.shape[1]
    gi = xs @ w_ih.T + b_ih  # (B, T, 3H)
    h = np.zeros((B, H), np.float32)
    out = np.empty((B, T, H), np.float32)
    order = range(T - 1, -1, -1) if reverse else range(T)
    w_hh_t = np.ascontiguousarray(w_hh.T)
    for t in order:
        gh = h @ w_hh_t + b_hh
        g = gi[:, t]
        r = _sigmoid(g[:, :H] + gh[:, :H])
        z = _sigmoid(g[:, H:2 * H] + gh[:, H:2 * H])
        n = np.tanh(g[:, 2 * H:] + r * gh[:, 2 * H:])
        h = (1 - z) * n + z * h
        out[:, t] = h
    return out


def _net(p, k, x):
    """x: (B, T, D) float32 -> softmax (B, T, 3)."""
    g = lambda name: p[f'm{k}.{name}']
    y = _gelu(x @ g('inp.0.weight').T + g('inp.0.bias'))
    y = _gelu(y @ g('inp.3.weight').T + g('inp.3.bias'))
    layer = 0
    while f'm{k}.gru.weight_ih_l{layer}' in p:
        f = _gru_dir(y, g(f'gru.weight_ih_l{layer}'), g(f'gru.weight_hh_l{layer}'), g(f'gru.bias_ih_l{layer}'),
                     g(f'gru.bias_hh_l{layer}'), False)
        b = _gru_dir(y, g(f'gru.weight_ih_l{layer}_reverse'), g(f'gru.weight_hh_l{layer}_reverse'),
                     g(f'gru.bias_ih_l{layer}_reverse'), g(f'gru.bias_hh_l{layer}_reverse'), True)
        y = np.concatenate([f, b], -1)
        layer += 1
    y = _gelu(y @ g('out.1.weight').T + g('out.1.bias'))
    logits = y @ g('out.3.weight').T + g('out.3.bias')
    bnd = _sigmoid(logits[..., 3]) if logits.shape[-1] > 3 else None
    logits = logits[..., :3]
    logits = logits - logits.max(-1, keepdims=True)
    e = np.exp(logits)
    LAST_BND[0] = bnd
    return e / e.sum(-1, keepdims=True)


LAST_BND = [None]


def _segments(period):
    out, i, n = [], 0, len(period)
    while i < n:
        j = i
        while j < n and period[j] == period[i]:
            j += 1
        if period[i] > 0:
            out.append((i, j))
        i = j
    return out


def gru_supports(p, k, X, period, plan):
    mu, sd = p[f'm{k}.mu'], p[f'm{k}.sd']
    const = sd < 1e-2

    def norm(Z):
        Z = np.clip((Z - mu) / sd, -6, 6).astype(np.float32)
        Z[:, const] = 0.0
        return Z

    Z = np.stack([norm(X), norm(swapped(X, plan))])  # batch: original, swapped
    sup = np.tile(np.array([[.45, .45, .1]]), (len(X), 1))
    bnd = np.zeros(len(X))
    for a, b in _segments(period):
        for s in range(a, b, WINDOW):
            lo, hi = max(a, s - CONTEXT), min(b, s + WINDOW + CONTEXT)
            q = _net(p, k, np.ascontiguousarray(Z[:, lo:hi]))
            e = min(b, s + WINDOW)
            orig = q[0, s - lo:e - lo]
            swp = q[1, s - lo:e - lo][:, [1, 0, 2]]
            sup[s:e] = .5 * (orig + swp)
            if LAST_BND[0] is not None:
                bnd[s:e] = .5 * (LAST_BND[0][0, s - lo:e - lo] + LAST_BND[0][1, s - lo:e - lo])
    GRU_BND.append(bnd if LAST_BND[0] is not None else None)
    return sup


GRU_BND = []


# ----- blend --------------------------------------------------------------------------------------------------

def _set_logp(gru_file, gbm_file, X, names, period):
    gbm = np.load(MODEL_DIR / gbm_file)
    gru = np.load(MODEL_DIR / gru_file)
    want = [str(s) for s in gbm['names']]
    have = list(names)
    missing = [n for n in want if n not in have]
    if missing:
        raise ValueError('Feature schema lacks model columns: ' + ', '.join(missing[:5]))
    Xs = np.asarray(X, np.float32)[:, [have.index(n) for n in want]]
    plan = swap_plan(want)
    parts = [gru_supports(gru, k, Xs, period, plan) for k in range(int(gru['n_models']))]
    parts.append(gbm_supports(gbm, Xs, plan))
    lp = sum(np.log(np.clip(p, 1e-9, 1)) for p in parts) / len(parts)
    p = np.exp(lp - lp.max(1, keepdims=True))
    return np.log(np.clip(p / p.sum(1, keepdims=True), 1e-9, 1))


def boundary():
    """Mean boundary probability over the GRUs (of the last supports() call) that have a boundary channel."""
    bs = [b for b in GRU_BND if b is not None]
    return np.mean(bs, 0) if bs else None


def supports(X, names, period):
    GRU_BND.clear()
    lp = sum(w * _set_logp(a, b, X, names, period) for a, b, w in SETS) / sum(w for _, _, w in SETS)
    p = np.exp(lp - lp.max(1, keepdims=True))
    p /= p.sum(1, keepdims=True)
    p = np.clip(p, 1e-9, 1) ** POWER
    p /= p.sum(1, keepdims=True)
    p = np.clip(p, 1e-6, 1)
    return p / p.sum(1, keepdims=True)
