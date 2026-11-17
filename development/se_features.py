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


IMPULSE_THR = 4.0   # m/s velocity change over +-2 frames (fixed a priori, physical)
TOUCH_R = 2.0       # m, player radius for a contact


def _impulse_core(frames):
    """Contact detection shared by impulse_features and impulse_rel_features."""
    per, val, obs, ball, H, A, Hid, Aid = _arr(frames)
    n = len(per)
    seg = _segments(per)
    # smooth ball over 5 frames inside observed runs of the same segment
    bx = np.where(obs, ball[:, 0], np.nan)
    by = np.where(obs, ball[:, 1], np.nan)
    def smooth(x):
        out = np.full(n, np.nan)
        for k in range(-2, 3):
            s = _shift(x, k)
            s = np.where(_shift(seg.astype(float), k) == seg, s, np.nan)
            out = np.where(k == -2, s, out + s) if False else out
        stack = np.stack([np.where(_shift(seg.astype(float), k) == seg, _shift(x, k), np.nan) for k in range(-2, 3)])
        return np.nanmean(stack, 0) if True else out
    with np.errstate(all='ignore'):
        sx, sy = smooth(bx), smooth(by)
        vx = (sx - _shift(sx, 1)) * FPS
        vy = (sy - _shift(sy, 1)) * FPS
        dvx = _shift(vx, -2) - _shift(vx, 2)
        dvy = _shift(vy, -2) - _shift(vy, 2)
        imp = np.hypot(dvx, dvy)
    imp = np.where(np.isfinite(imp), np.minimum(imp, 40.0), 0.0)
    # nearest player distances per team
    dH = np.hypot(H[:, :, 0] - ball[:, None, 0], H[:, :, 1] - ball[:, None, 1])
    dA = np.hypot(A[:, :, 0] - ball[:, None, 0], A[:, :, 1] - ball[:, None, 1])
    h1 = np.where(obs, np.nanmin(np.where(np.isfinite(dH), dH, np.inf), 1), np.inf)
    a1 = np.where(obs, np.nanmin(np.where(np.isfinite(dA), dA, np.inf), 1), np.inf)
    # local maxima within +-3 frames above threshold, with a player within TOUCH_R
    peak = imp >= IMPULSE_THR
    for k in (1, 2, 3):
        peak &= imp >= np.nan_to_num(_shift(imp, k), nan=0)
        peak &= imp > np.nan_to_num(_shift(imp, -k), nan=0)
    near = np.minimum(h1, a1) <= TOUCH_R
    touch = peak & near & obs
    team = np.where(h1 < a1, 1.0, -1.0)
    conf = np.clip(np.abs(np.where(np.isfinite(a1 - h1), a1 - h1, 0)), 0, 5) / 5 * np.minimum(imp, 20) / 20
    tv = np.where(touch, team, 0.0)
    return dict(touch=touch, team=team, conf=conf, tv=tv, imp=imp, seg=seg, obs=obs)


def impulse_features(frames):
    """Contact ('impulse touch') features: ball-velocity impulse peaks with a player within TOUCH_R."""
    k = _impulse_core(frames)
    touch, team, conf, tv, imp, seg = k['touch'], k['team'], k['conf'], k['tv'], k['imp'], k['seg']
    cols, names = [], []

    def add(name, x):
        x = np.asarray(x, np.float64)
        cols.append(np.where(np.isfinite(x), x, 0.0).astype(np.float32)); names.append(name)

    lv, ldt = _event_ref(touch, tv, seg, -1)
    nv, ndt = _event_ref(touch, tv, seg, +1)
    lc, _ = _event_ref(touch, conf, seg, -1)
    nc, _ = _event_ref(touch, conf, seg, +1)
    add('itouch_last', lv); add('itouch_last_dt', ldt); add('itouch_last_conf', lc)
    add('itouch_next', nv); add('itouch_next_dt', ndt); add('itouch_next_conf', nc)
    add('itouch_flip', (lv * nv < 0).astype(float))
    add('impulse', imp)
    for w in (12, 25):
        for d in (-1, 1):
            mh, _ = _window_mean(np.where(touch & (team > 0), 1.0, 0.0), w, seg, d)
            ma, _ = _window_mean(np.where(touch & (team < 0), 1.0, 0.0), w, seg, d)
            add(f'itouchH_{"p" if d < 0 else "f"}{w}', mh * (w + 1))
            add(f'itouchA_{"p" if d < 0 else "f"}{w}', ma * (w + 1))
    return np.stack(cols, 1), tuple(names)


REL_HALF = 5   # frames: smoothing (+-2) plus the +-2 velocity difference plus 1 for the frame difference


def impulse_rel_features(frames):
    """Contact reliability: a contact is reliable when the ball is observed (same segment) on every frame of
    [t-REL_HALF, t+REL_HALF], so smoothing/differencing never straddles an observation edge."""
    k = _impulse_core(frames)
    touch, tv, seg, obs = k['touch'], k['tv'], k['seg'], k['obs']
    full = obs.copy()
    for d in range(-REL_HALF, REL_HALF + 1):
        if d:
            full &= (np.nan_to_num(_shift(obs.astype(float), d), nan=0) > 0) & (_shift(seg.astype(float), d) == seg)
    rel = touch & full
    cols, names = [], []

    def add(name, x):
        x = np.asarray(x, np.float64)
        cols.append(np.where(np.isfinite(x), x, 0.0).astype(np.float32)); names.append(name)

    r = np.where(touch, full.astype(float), 0.0)
    lr, _ = _event_ref(touch, r, seg, -1)
    nr, _ = _event_ref(touch, r, seg, +1)
    add('itouch_last_rel', lr); add('itouch_next_rel', nr)
    lv, ldt = _event_ref(rel, tv, seg, -1)
    nv, ndt = _event_ref(rel, tv, seg, +1)
    add('rtouch_last', lv); add('rtouch_last_dt', ldt); add('rtouch_next', nv); add('rtouch_next_dt', ndt)
    return np.stack(cols, 1), tuple(names)


def _vel_x(P, I, seg, lag=5):
    """Per-player x velocity (m/s), ids matched between t-lag and t; nan where unknown."""
    n = len(P)
    vx = np.full((n, K), np.nan)
    Pp = np.full_like(P, np.nan); Pp[lag:] = P[:-lag]
    Ip = np.full_like(I, -1); Ip[lag:] = I[:-lag]
    segp = np.full_like(seg, -1); segp[lag:] = seg[:-lag]
    same = segp == seg
    for k in range(K):
        idk = I[:, k]
        match = (Ip == idk[:, None]) & (idk[:, None] >= 0)
        has = match.any(1) & same
        prev = Pp[np.arange(n), match.argmax(1)]
        v = (P[:, k, 0] - prev[:, 0]) * FPS / lag
        vx[:, k] = np.where(has & (np.abs(v) < 12), v, np.nan)
    return vx


def team_shape_features(frames, ext=False):
    """Player-only ownership cues for long ball gaps, each team in its own attacking frame (H/A paired):
    centroid depth and forward velocity, length/width, forward runners, defensive-line depth, marking tightness."""
    per, val, obs, ball, H, A, Hid, Aid = _arr(frames)
    n = len(per)
    seg = _segments(per)
    hcx, _ = _nanmean(H[:, :, 0], 1)
    acx, _ = _nanmean(A[:, :, 0], 1)
    sgn = np.sign(np.nan_to_num(acx - hcx))
    mid = np.zeros(n)
    for s in np.unique(seg):
        m = seg == s
        sgn[m] = 1.0 if sgn[m].sum() >= 0 else -1.0
        mid[m] = np.nanmedian(np.concatenate([hcx[m], acx[m]])) if np.isfinite(hcx[m]).any() else 0.0
    cols, names = [], []

    def add(name, x):
        x = np.asarray(x, np.float64)
        cols.append(np.where(np.isfinite(x), x, 0.0).astype(np.float32)); names.append(name)

    sig = {}
    with np.errstate(all='ignore'):
        for T, P, I, O, d in (('H', H, Hid, A, sgn), ('A', A, Aid, H, -sgn)):
            xs = d[:, None] * (P[:, :, 0] - mid[:, None])          # own attacking frame, + = towards opponent goal
            ok = np.isfinite(xs)
            cxa, _ = _nanmean(xs, 1)
            vx = d[:, None] * _vel_x(P, I, seg)
            vxm, _ = _nanmean(vx, 1)
            srt = np.sort(np.where(ok, xs, np.inf), 1)
            line = np.where(ok.sum(1) >= 3, srt[:, 1], np.nan)        # deepest outfield player (skip keeper)
            top = np.where(ok, xs, -np.inf).max(1)
            length = np.where(ok.sum(1) >= 3, top - line, np.nan)
            ys = np.where(ok, P[:, :, 1], np.nan)
            width = np.nanmax(ys, 1) - np.nanmin(ys, 1)
            fwd = np.where(np.isfinite(vx), vx > 3.0, False).sum(1)
            back = np.where(np.isfinite(vx), vx < -3.0, False).sum(1)
            dd = np.hypot(P[:, :, None, 0] - O[:, None, :, 0], P[:, :, None, 1] - O[:, None, :, 1])
            near_opp = np.nanmin(np.where(np.isfinite(dd), dd, np.inf), 2)
            mark, _ = _nanmean(np.where(np.isfinite(near_opp) & ok, np.minimum(near_opp, 30), np.nan), 1)
            for nm, x in (('cx', cxa), ('vx', vxm), ('line', line), ('len', length), ('wid', width),
                          ('fwd', fwd), ('back', back), ('mark', mark)):
                add(f'ts{T}_{nm}', x); sig[(T, nm)] = x
    if ext:   # round 6: longer memory (+-30 s) and shape-extent windows; returned alone
        cols, names = [], []
        plan = [(nm, (50, 125, 375, 750)) for nm in ('line', 'len', 'wid')] +                [(nm, (750,)) for nm in ('vx', 'fwd', 'cx', 'mark')]
    else:
        plan = [(nm, (50, 125, 375)) for nm in ('vx', 'fwd', 'cx', 'mark')]
    for nm, ws in plan:
        for T in ('H', 'A'):
            for w in ws:
                for dr in (-1, 1):
                    m, _ = _window_mean(sig[(T, nm)], w, seg, dr)
                    add(f'ts{T}_{nm}_{"p" if dr < 0 else "f"}{w}', m)
    return np.stack(cols, 1), tuple(names)


def team_shape_ext_features(frames):
    return team_shape_features(frames, ext=True)


def restart_features(frames):
    """Round 8: player-only dead-ball / restart cues (pitch 105 x 68 m). Stillness, touchline and corner occupancy,
    penalty-box and six-yard crowding, kickoff shape (each team in its own half, someone at the centre spot) and
    windows. Team-symmetric quantities only, so no home/away swap pairing is needed except per-team stillness."""
    per, val, obs, ball, H, A, Hid, Aid = _arr(frames)
    n = len(per)
    seg = _segments(per)
    allP = np.concatenate([H, A], 1)
    x, y = allP[..., 0], allP[..., 1]
    ok = np.isfinite(x)
    cols, names = [], []

    def add(name, v):
        v = np.asarray(v, np.float64)
        cols.append(np.where(np.isfinite(v), v, 0.0).astype(np.float32)); names.append(name)

    with np.errstate(all='ignore'):
        spH, spA = _speeds(H, Hid, seg), _speeds(A, Aid, seg)
        sp = np.concatenate([spH, spA], 1)
        still = lambda s: np.nanmean(np.where(np.isfinite(s), s < 1.0, np.nan), 1)
        stH, stA, stAll = still(spH), still(spA), still(sp)
        msp = np.nanmean(sp, 1)
        touch_y = np.minimum(y, 68 - y)
        n_touch = (ok & (touch_y < 2.5)).sum(1)
        cx = np.minimum(x, 105 - x)
        n_corner = (ok & (cx < 4) & (touch_y < 4)).sum(1)
        n_goalline = (ok & (cx < 2.5)).sum(1)
        inbox = ok & (cx < 16.5) & (y > 13.85) & (y < 54.15)
        n_box = np.maximum(inbox & (x < 52.5), False).sum(1), (inbox & (x >= 52.5)).sum(1)
        box_max = np.maximum(n_box[0], n_box[1])
        six = ok & (cx < 5.5) & (y > 24.84) & (y < 43.16)
        n_six = six.sum(1)
        centre = np.hypot(x - 52.5, y - 34.0)
        near_centre = np.nanmin(np.where(ok, centre, np.inf), 1)
        hcx, _ = _nanmean(H[:, :, 0], 1)
        acx, _ = _nanmean(A[:, :, 0], 1)
        sgn = np.sign(np.nan_to_num(acx - hcx))
        for s_ in np.unique(seg):
            m = seg == s_
            sgn[m] = 1.0 if sgn[m].sum() >= 0 else -1.0
        own_h = np.nanmean(np.where(np.isfinite(H[:, :, 0]), sgn[:, None] * (H[:, :, 0] - 52.5) <= 1.0, np.nan), 1)
        own_a = np.nanmean(np.where(np.isfinite(A[:, :, 0]), sgn[:, None] * (A[:, :, 0] - 52.5) >= -1.0, np.nan), 1)
        kickoff = np.minimum(own_h, own_a) * (near_centre < 3)
        dmsp = msp - _shift(msp, 25)
    sig = dict(still_all=stAll, mean_spd=msp, n_touch=n_touch, n_corner=n_corner, n_goalline=n_goalline,
               box_max=box_max, n_six=n_six, near_centre=np.minimum(near_centre, 40), kickoff=kickoff, dspd1=dmsp)
    for k_, v in sig.items():
        add('rs_' + k_, v)
    add('rsH_still', stH); add('rsA_still', stA)
    for k_ in ('still_all', 'mean_spd', 'n_touch', 'box_max', 'kickoff', 'n_corner'):
        for w in (50, 125):
            for d in (-1, 1):
                m, _ = _window_mean(sig[k_], w, seg, d)
                add(f'rs_{k_}_{"p" if d < 0 else "f"}{w}', m)
    # time since / until the whole field was mostly still (>= 60% players under 1 m/s)
    ev = np.nan_to_num(stAll) >= 0.6
    _, ldt = _event_ref(ev, ev.astype(float), seg, -1)
    _, ndt = _event_ref(ev, ev.astype(float), seg, +1)
    add('rs_since_still', ldt); add('rs_until_still', ndt)
    return np.stack(cols, 1), tuple(names)
