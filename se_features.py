"""Rich geometry features for the strong-emission model. Inputs: tracking frames only (no labels, tags, ids of
matches/providers). Uses past AND future context (offline task). All arrays float32 (n, F).
"""
from math import isfinite

import numpy as np

K = 16  # max players per team kept
CAP = 30.0
FPS = 25.0


def _arr(frames):
    n = len(frames)
    per = np.zeros(n, np.int8)
    val = np.zeros(n, bool)
    obs = np.zeros(n, bool)
    ball = np.full((n, 2), np.nan, np.float64)
    H = np.full((n, K, 2), np.nan, np.float64)
    A = np.full((n, K, 2), np.nan, np.float64)
    Hid = np.full((n, K), -1, np.int64)
    Aid = np.full((n, K), -1, np.int64)
    for i, f in enumerate(frames):
        per[i] = f.period
        val[i] = bool(getattr(f, 'geometry_valid', True))
        if f.ball_observed:
            obs[i] = True
            ball[i] = (f.ball_x, f.ball_y)
        for pts, ids, P, I in ((f.home_xy, f.home_ids, H, Hid), (f.away_xy, f.away_ids, A, Aid)):
            m = min(K, len(pts))
            if m:
                P[i, :m] = np.asarray(pts[:m], dtype=np.float64)
                if len(ids) >= m:
                    I[i, :m] = [(-1 if x is None else hash(x) & 0x7fffffffffff) for x in ids[:m]]
    obs &= per > 0
    return per, val, obs, ball, H, A, Hid, Aid


def _segments(per):
    """Segment id changing at period change."""
    change = np.ones(len(per), bool)
    change[1:] = per[1:] != per[:-1]
    return np.cumsum(change)


def _shift(x, k, fill=np.nan):
    out = np.full_like(x, fill, dtype=np.float64)
    if k > 0:
        out[k:] = x[:-k]
    elif k < 0:
        out[:k] = x[-k:]
    else:
        out[:] = x
    return out


def _speeds(P, I, seg, lag=5):
    """Per-player speed (m/s) matching ids between t-lag and t. Returns (n,K) with nan where unknown."""
    n = len(P)
    sp = np.full((n, K), np.nan)
    Pp = np.full_like(P, np.nan)
    Pp[lag:] = P[:-lag]
    Ip = np.full_like(I, -1)
    Ip[lag:] = I[:-lag]
    segp = np.full_like(seg, -1)
    segp[lag:] = seg[:-lag]
    same_seg = segp == seg
    # match each id at t to the same id at t-lag
    for k in range(K):
        idk = I[:, k]
        match = (Ip == idk[:, None]) & (idk[:, None] >= 0)
        has = match.any(1) & same_seg
        j = match.argmax(1)
        prev = Pp[np.arange(n), j]
        d = np.hypot(P[:, k, 0] - prev[:, 0], P[:, k, 1] - prev[:, 1]) * FPS / lag
        d = np.where(has & (d < 12), d, np.nan)
        sp[:, k] = d
    return sp


def _nanmean(x, axis):
    with np.errstate(invalid='ignore', divide='ignore'):
        c = np.isfinite(x).sum(axis)
        s = np.where(np.isfinite(x), x, 0).sum(axis)
        return np.where(c > 0, s / np.maximum(c, 1), np.nan), c


def _window_mean(x, w, seg, direction):
    """Masked mean of x over [t-w, t] (direction=-1) or [t, t+w] (+1) within segment; nan values ignored.
    Returns (mean or 0, support fraction)."""
    n = len(x)
    ok = np.isfinite(x)
    v = np.where(ok, x, 0.0)
    out = np.zeros(n)
    cnt = np.zeros(n)
    tot = np.zeros(n)
    for s in np.unique(seg):
        idx = np.flatnonzero(seg == s)
        a, b = idx[0], idx[-1] + 1
        cv = np.concatenate([[0], np.cumsum(v[a:b])])
        cc = np.concatenate([[0], np.cumsum(ok[a:b])])
        t = np.arange(b - a)
        if direction < 0:
            lo, hi = np.maximum(0, t - w), t + 1
        else:
            lo, hi = t, np.minimum(b - a, t + w + 1)
        out[a:b] = cv[hi] - cv[lo]
        cnt[a:b] = cc[hi] - cc[lo]
        tot[a:b] = hi - lo
    mean = np.where(cnt > 0, out / np.maximum(cnt, 1), 0.0)
    return mean, cnt / np.maximum(tot, 1)


def _event_ref(event_mask, value, seg, direction, cap_s=20.0):
    """For each t, value at the most recent (direction -1) / next (+1) event and time distance in s (capped)."""
    n = len(event_mask)
    idx = np.arange(n)
    if direction < 0:
        last = np.where(event_mask, idx, -1)
        last = np.maximum.accumulate(last)
        ok = (last >= 0)
        ok[ok] &= seg[last[ok]] == seg[ok]
        dt = np.where(ok, (idx - last) / FPS, cap_s)
        val = np.where(ok, value[np.clip(last, 0, n - 1)], 0.0)
    else:
        nxt = np.where(event_mask, idx, n)
        nxt = np.minimum.accumulate(nxt[::-1])[::-1]
        ok = nxt < n
        ok[ok] &= seg[nxt[ok]] == seg[ok]
        dt = np.where(ok, (nxt - idx) / FPS, cap_s)
        val = np.where(ok, value[np.clip(nxt, 0, n - 1)], 0.0)
    return val, np.minimum(dt, cap_s)


def build(frames, frozen18=None):
    """Return (X float32 (n,F), names)."""
    per, val, obs, ball, H, A, Hid, Aid = _arr(frames)
    n = len(per)
    seg = _segments(per)
    cols, names = [], []

    def add(name, x):
        x = np.asarray(x, np.float64)
        x = np.where(np.isfinite(x), x, 0.0)
        cols.append(x.astype(np.float32))
        names.append(name)

    if frozen18 is not None:
        for j in range(18):
            add(f'f18_{j}', frozen18[:, j])

    nH = np.isfinite(H[:, :, 0]).sum(1)
    nA = np.isfinite(A[:, :, 0]).sum(1)
    add('nH', nH)
    add('nA', nA)
    add('obs', obs)
    add('valid', val)

    # attack orientation: home attacks +x if home centroid x < away centroid x
    hcx, _ = _nanmean(H[:, :, 0], 1)
    acx, _ = _nanmean(A[:, :, 0], 1)
    hcy, _ = _nanmean(H[:, :, 1], 1)
    acy, _ = _nanmean(A[:, :, 1], 1)
    sgn = np.sign(np.nan_to_num(acx - hcx))
    # smooth orientation per segment by majority (orientation is constant within a half)
    for s in np.unique(seg):
        m = seg == s
        tot = sgn[m].sum()
        sgn[m] = 1.0 if tot >= 0 else -1.0
    allx = np.concatenate([H[:, :, 0], A[:, :, 0]], 1)
    ally = np.concatenate([H[:, :, 1], A[:, :, 1]], 1)
    cx, _ = _nanmean(allx, 1)
    cy, _ = _nanmean(ally, 1)
    add('team_gap_x', sgn * (acx - hcx))
    add('h_spread', np.nanstd(np.where(np.isfinite(H[:, :, 0]), H[:, :, 0], np.nan), 1) if True else 0)
    add('a_spread', np.nanstd(np.where(np.isfinite(A[:, :, 0]), A[:, :, 0], np.nan), 1))
    add('all_spread_y', np.nanstd(ally, 1))

    # ball geometry
    bx, by = ball[:, 0], ball[:, 1]
    dH = np.hypot(H[:, :, 0] - bx[:, None], H[:, :, 1] - by[:, None])
    dA = np.hypot(A[:, :, 0] - bx[:, None], A[:, :, 1] - by[:, None])
    dHs = np.sort(np.where(np.isfinite(dH), dH, np.inf), 1)
    dAs = np.sort(np.where(np.isfinite(dA), dA, np.inf), 1)
    for k in range(3):
        add(f'dH{k}', np.where(obs, np.minimum(CAP, dHs[:, k]), CAP))
        add(f'dA{k}', np.where(obs, np.minimum(CAP, dAs[:, k]), CAP))
    h1 = np.where(obs, np.minimum(CAP, dHs[:, 0]), np.nan)
    a1 = np.where(obs, np.minimum(CAP, dAs[:, 0]), np.nan)
    margin = a1 - h1  # >0 home closer
    add('margin', margin)
    add('margin_tanh', np.tanh(margin / 2))
    for r in (2.0, 5.0, 10.0):
        add(f'nH{r:g}', np.where(obs, (dH < r).sum(1), 0))
        add(f'nA{r:g}', np.where(obs, (dA < r).sum(1), 0))
    add('ball_rx', np.where(obs, sgn * (bx - cx), 0))
    add('ball_ry', np.where(obs, by - cy, 0))
    add('ball_absx', np.where(obs, np.abs(bx - cx), 0))
    # ball relative to each team's centroid in home-attack frame
    add('ball_minus_hcx', np.where(obs, sgn * (bx - hcx), 0))
    add('ball_minus_acx', np.where(obs, sgn * (bx - acx), 0))

    # ball velocity (central difference over 2 frames, same segment, both observed)
    def lagged(x, k):
        return _shift(x, k)
    seg_f = seg.astype(np.float64)
    vx = (lagged(bx, -2) - lagged(bx, 2)) / (4 / FPS)
    vy = (lagged(by, -2) - lagged(by, 2)) / (4 / FPS)
    okv = (lagged(seg_f, -2) == seg_f) & (lagged(seg_f, 2) == seg_f)
    vx = np.where(okv & np.isfinite(vx), vx, np.nan)
    vy = np.where(okv & np.isfinite(vy), vy, np.nan)
    bsp = np.minimum(40, np.hypot(vx, vy))
    add('bvx_home', sgn * np.clip(vx, -40, 40))
    add('bvy', np.clip(vy, -40, 40))
    add('bspeed', bsp)
    add('bspeed_known', np.isfinite(bsp))
    acc = np.abs(lagged(bsp, -3) - lagged(bsp, 3))
    add('bacc', np.minimum(acc, 40))

    # closing rates of nearest distances (sorted-distance change over 5 frames)
    for nm, d in (('h1', h1), ('a1', a1)):
        dd = (d - lagged(d, 5)) * FPS / 5
        add(f'close_{nm}', np.clip(dd, -20, 20))

    # player speeds
    spH = _speeds(H, Hid, seg)
    spA = _speeds(A, Aid, seg)
    mH, _ = _nanmean(spH, 1)
    mA, _ = _nanmean(spA, 1)
    allsp = np.concatenate([spH, spA], 1)
    mAll, cAll = _nanmean(allsp, 1)
    add('spd_H', mH)
    add('spd_A', mA)
    add('spd_all', mAll)
    add('spd_n', cAll)
    with np.errstate(invalid='ignore'):
        add('spd_max', np.nanmax(np.where(np.isfinite(allsp), allsp, -1), 1))
        add('frac_fast', np.where(cAll > 0, (allsp > 3).sum(1) / np.maximum(cAll, 1), 0))
        add('frac_still', np.where(cAll > 0, (allsp < 1).sum(1) / np.maximum(cAll, 1), 0))
    # nearest player's speed per team
    jH = np.argmin(np.where(np.isfinite(dH), dH, np.inf), 1)
    jA = np.argmin(np.where(np.isfinite(dA), dA, np.inf), 1)
    add('spd_nearH', np.where(obs, spH[np.arange(n), jH], np.nan))
    add('spd_nearA', np.where(obs, spA[np.arange(n), jA], np.nan))

    # touches: ball within 1.5 m of nearest player and that team clearly closer
    touch_h = obs & (h1 <= 1.5) & (np.nan_to_num(margin, nan=0) >= 0.5)
    touch_a = obs & (a1 <= 1.5) & (np.nan_to_num(margin, nan=0) <= -0.5)
    touch = touch_h | touch_a
    tv = np.where(touch_h, 1.0, np.where(touch_a, -1.0, 0.0))
    lv, ldt = _event_ref(touch, tv, seg, -1)
    nv, ndt = _event_ref(touch, tv, seg, +1)
    add('last_touch', lv)
    add('last_touch_dt', ldt)
    add('next_touch', nv)
    add('next_touch_dt', ndt)
    add('touch_agree', lv * nv)
    # looser control: within 3m, margin >= 1
    ctl_h = obs & (h1 <= 3) & (np.nan_to_num(margin, nan=0) >= 1)
    ctl_a = obs & (a1 <= 3) & (np.nan_to_num(margin, nan=0) <= -1)
    cv = np.where(ctl_h, 1.0, np.where(ctl_a, -1.0, 0.0))
    lv2, ldt2 = _event_ref(ctl_h | ctl_a, cv, seg, -1)
    nv2, ndt2 = _event_ref(ctl_h | ctl_a, cv, seg, +1)
    add('last_ctl', lv2)
    add('last_ctl_dt', ldt2)
    add('next_ctl', nv2)
    add('next_ctl_dt', ndt2)

    # missing-ball timing
    one = np.ones(n)
    _, lo_dt = _event_ref(obs, one, seg, -1, cap_s=30)
    _, no_dt = _event_ref(obs, one, seg, +1, cap_s=30)
    add('since_obs', lo_dt)
    add('until_obs', no_dt)
    add('gap_len', np.minimum(30, lo_dt + no_dt))

    # context windows
    signals = dict(margin=np.tanh(margin / 2), bspeed=bsp, spd_all=mAll, frac_fast=np.where(cAll > 0, (allsp > 3).sum(1) / np.maximum(cAll, 1), np.nan),
                   obs=obs.astype(float), touch=tv, nearH=np.where(obs, (h1 < a1).astype(float), np.nan),
                   bvx=sgn * np.clip(vx, -40, 40))
    for nm, x in signals.items():
        for w in (12, 50, 125, 375):
            for d in (-1, 1):
                m, sup = _window_mean(x, w, seg, d)
                add(f'{nm}_{"p" if d < 0 else "f"}{w}', m)
                if nm in ('margin', 'bspeed'):
                    add(f'{nm}_{"p" if d < 0 else "f"}{w}_sup', sup)

    # position within period
    pos = np.zeros(n)
    for s in np.unique(seg):
        idx = np.flatnonzero(seg == s)
        pos[idx] = np.minimum(np.arange(len(idx)), len(idx) - 1 - np.arange(len(idx))) / FPS
    add('edge_dist_s', np.minimum(pos, 600))
    add('period', per)

    X = np.stack(cols, 1)
    return X, tuple(names), dict(period=per, observed=obs, valid=val, sign=sgn)


def swap_names(names):
    """Index permutation and sign flips that swap home/away roles (for symmetric augmentation)."""
    return None
