"""Deterministic numpy inference for the strong-emission model (no torch / scikit-learn at runtime).

Supports = geometric blend (equal weights) of two bidirectional-GRU heads and one gradient-boosted pair of heads
(ownership with home/away swap averaging, live/dead), then squared (power 2) and renormalised.
Models were fitted on external matches only (DFL, SkillCorner, WCSF); see docs/strong-emissions-results.md.
"""
from pathlib import Path

import numpy as np

from se_sym import swap_plan, swapped

MODEL_DIR = Path(__file__).resolve().parent / 'strong_model'
POWER = 2.0
WINDOW, CONTEXT = 6000, 1500


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
    logits = logits - logits.max(-1, keepdims=True)
    e = np.exp(logits)
    return e / e.sum(-1, keepdims=True)


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
    for a, b in _segments(period):
        for s in range(a, b, WINDOW):
            lo, hi = max(a, s - CONTEXT), min(b, s + WINDOW + CONTEXT)
            q = _net(p, k, np.ascontiguousarray(Z[:, lo:hi]))
            e = min(b, s + WINDOW)
            orig = q[0, s - lo:e - lo]
            swp = q[1, s - lo:e - lo][:, [1, 0, 2]]
            sup[s:e] = .5 * (orig + swp)
    return sup


# ----- blend --------------------------------------------------------------------------------------------------

def supports(X, names, period):
    gbm = np.load(MODEL_DIR / 'gbm.npz')
    gru = np.load(MODEL_DIR / 'gru.npz')
    if [str(s) for s in gbm['names']] != list(names):
        raise ValueError('Feature schema differs from the exported model')
    plan = swap_plan(list(names))
    X = np.asarray(X, np.float32)
    parts = [gru_supports(gru, k, X, period, plan) for k in range(int(gru['n_models']))]
    parts.append(gbm_supports(gbm, X, plan))
    lp = sum(np.log(np.clip(p, 1e-9, 1)) for p in parts) / len(parts)
    p = np.exp(lp - lp.max(1, keepdims=True))
    p /= p.sum(1, keepdims=True)
    p = np.clip(p, 1e-9, 1) ** POWER
    p /= p.sum(1, keepdims=True)
    p = np.clip(p, 1e-6, 1)
    return p / p.sum(1, keepdims=True)
