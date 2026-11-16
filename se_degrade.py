"""Degraded-ball evaluation view: drop the ball on D-labelled matches with SkillCorner-like gap statistics.

Gap/observed run lengths are sampled from SkillCorner DEV matches (never BAR-ATH). Deterministic per match.
    python se_degrade.py build [cid ...]   -> strong-emissions-reference/cases_deg/<cid>.npz (features, mask, release sup)
"""
from dataclasses import replace
import sys
import zlib

import numpy as np

import se_load

SC_DEV = [c for c in se_load.ALL if c.startswith('skillcorner') and c not in se_load.HOLDOUT]
DEG_CASES = [c for c in se_load.ALL if c.startswith('dfl') and c not in se_load.HOLDOUT]
TARGET_MISSING = 0.42


def _runs(observed, period):
    obs_runs, miss_runs = [], []
    i, n = 0, len(observed)
    while i < n:
        if period[i] == 0:
            i += 1
            continue
        j = i
        while j < n and observed[j] == observed[i] and period[j] == period[i]:
            j += 1
        (obs_runs if observed[i] else miss_runs).append(j - i)
        i = j
    return np.asarray(obs_runs), np.asarray(miss_runs)


def gap_stats():
    o, m = [], []
    for c in SC_DEV:
        z = np.load(se_load.PRIVATE / 'cases' / (c + '.npz'))
        a, b = _runs(z['observed'], z['period'])
        o.append(a); m.append(b)
    return np.concatenate(o), np.concatenate(m)


def make_mask(n, period, cid, target=None):
    """True = drop ball. Alternating observed/missing runs from SC empirical distributions, rescaled so the
    missing fraction on active rows is about TARGET_MISSING (or `target`)."""
    TARGET_MISSING = globals()['TARGET_MISSING'] if target is None else target
    obs_runs, miss_runs = gap_stats()
    rng = np.random.default_rng(zlib.crc32(cid.encode()))
    # scale observed runs so expected missing fraction hits the target
    em, eo = miss_runs.mean(), obs_runs.mean()
    scale = em * (1 - TARGET_MISSING) / (TARGET_MISSING * eo)
    drop = np.zeros(n, bool)
    t = 0
    observed = rng.random() < .5
    while t < n:
        L = int(max(1, round(rng.choice(obs_runs) * scale))) if observed else int(rng.choice(miss_runs))
        if not observed:
            drop[t:t + L] = True
        t += L
        observed = not observed
    drop &= np.asarray(period) > 0
    return drop


def transplant_mask(period, sc_cid):
    """True = drop ball, copied from a real SkillCorner dev match: per period, frame k of the DFL period gets the
    SkillCorner observed flag at frame k of the same period (wrapping if the DFL period is longer)."""
    z = np.load(se_load.PRIVATE / 'cases' / (sc_cid + '.npz'))
    sobs, sper = np.asarray(z['observed'], bool), np.asarray(z['period'])
    period = np.asarray(period)
    drop = np.zeros(len(period), bool)
    for p in np.unique(period[period > 0]):
        idx = np.flatnonzero(period == p)
        src = sobs[sper == p]
        if not len(src):
            src = sobs[sper > 0]
        drop[idx] = ~src[np.arange(len(idx)) % len(src)]
    return drop


# Player dropout (round 8): rounded aggregate rates only (see round-8 design). Per team, alternating present/missing
# runs; missing runs log-normal (median 4 s, p90 ~35 s); in a missing run k players are absent (k=1 most often),
# always the k most extreme along the pitch axis at that frame (camera edges).
P_MISS_TEAM = 0.36
K_DIST = {1: .58, 2: .15, 3: .07, 4: .08, 5: .06, 6: .06}


def player_k(n, period, seed):
    rng = np.random.default_rng(zlib.crc32(seed.encode()))
    mu, sig = np.log(100.0), 1.69
    lm = np.exp(mu + sig * sig / 2)
    lp = lm * (1 - P_MISS_TEAM) / P_MISS_TEAM
    k = np.zeros(n, np.int8)
    t, missing = 0, rng.random() < P_MISS_TEAM
    ks, ps = list(K_DIST), list(K_DIST.values())
    while t < n:
        if missing:
            L = int(min(3000, max(1, rng.lognormal(mu, sig))))
            k[t:t + L] = rng.choice(ks, p=ps)
        else:
            L = int(max(1, rng.exponential(lp)))
        t += L
        missing = not missing
    k[np.asarray(period) == 0] = 0
    return k


def drop_players(frames, kH, kA, centre_x=52.5):
    from math import hypot
    out = []
    for f, a, b in zip(frames, kH, kA):
        if a or b:
            def keep(xy, ids, k):
                if not k or not len(xy):
                    return tuple(xy), tuple(ids)
                order = sorted(range(len(xy)), key=lambda i: -abs(float(xy[i][0]) - centre_x))
                gone = set(order[:min(int(k), len(xy))])
                return (tuple(v for i, v in enumerate(xy) if i not in gone),
                        tuple(v for i, v in enumerate(ids) if i not in gone) if len(ids) == len(xy) else tuple(ids))
            hxy, hid = keep(f.home_xy, f.home_ids, a)
            axy, aid = keep(f.away_xy, f.away_ids, b)
            hd, ad = f.home_distance, f.away_distance
            if f.ball_x is not None and f.ball_y is not None:
                hd = min((hypot(float(x) - float(f.ball_x), float(y) - float(f.ball_y)) for x, y in hxy), default=None)
                ad = min((hypot(float(x) - float(f.ball_x), float(y) - float(f.ball_y)) for x, y in axy), default=None)
            f = replace(f, home_xy=hxy, home_ids=hid, away_xy=axy, away_ids=aid, home_distance=hd, away_distance=ad)
        out.append(f)
    return out


def degrade(frames, drop):
    out = []
    for f, d in zip(frames, drop):
        if d and f.ball_observed:
            f = replace(f, ball_x=None, ball_y=None, home_distance=None, away_distance=None,
                        ball_native_observation=False, ball_provenance='missing', ball_interpolated=False,
                        ball_sample_time_s=None)
        out.append(f)
    return out


def load_deg(cid):
    frames, ref = se_load.load(cid)
    drop = np.load(se_load.PRIVATE / 'cases_deg' / (cid + '.npz'))['drop']
    return degrade(frames, drop), ref


def build(cids, kind='deg'):
    from gap_solver.tactical import feature_rows
    from memory_ablation import predict_supports
    import live_dead_protocol as lp
    import se_features
    model = lp.load_frozen_model()
    out = se_load.PRIVATE / ('cases_' + kind)
    out.mkdir(parents=True, exist_ok=True)
    for cid in cids:
        frames, ref = se_load.load(cid)
        per = np.asarray([f.period for f in frames])
        if kind.startswith('evalr'):   # real SkillCorner gap layout, rotated over SC dev matches
            k = DEG_CASES.index(cid) + (0 if kind == 'evalr1' else 3)
            drop = transplant_mask(per, sorted(SC_DEV)[k % len(SC_DEV)])
        elif kind == 'augsc':   # SkillCorner training copy: extra ~25% removal on top of its natural ball loss
            drop = make_mask(len(frames), per, cid + '#' + kind, target=0.25)
        else:
            drop = make_mask(len(frames), per, cid if kind == 'deg' else cid + '#' + kind)
        frames = degrade(frames, drop)
        extra = {}
        PSRC = {'evalp': 'cases_deg', 'evalrp': 'cases_evalr1', 'augp': 'cases_aug', 'augp2': 'cases_aug2', 'augp3': 'cases_aug3'}
        if kind in PSRC:   # ball loss (from an existing view) + player dropout; training kinds use their own seeds
            src = PSRC[kind]
            drop = np.load(se_load.PRIVATE / src / (cid + '.npz'))['drop']
            frames, _ = se_load.load(cid)
            frames = degrade(frames, drop)
            extra = dict(kH=player_k(len(frames), per, cid + '#' + kind + 'H'), kA=player_k(len(frames), per, cid + '#' + kind + 'A'))
            frames = drop_players(frames, extra['kH'], extra['kA'])
        f18 = np.asarray(list(feature_rows(frames)), dtype=np.float64)
        sup = np.asarray(predict_supports(f18, model), dtype=np.float64)
        X, names, info = se_features.build(frames, f18)
        np.savez_compressed(out / (cid + '.npz'), X=X, names=np.array(names), ref=ref, period=info['period'],
                            observed=info['observed'], release_sup=sup, drop=drop, **extra)
        act = per > 0
        print(cid, 'missing frac on active', round(float((~info['observed'])[act].mean()), 3), flush=True)


if __name__ == '__main__':
    kind = sys.argv[1].replace('build', '') or 'deg'
    build(sys.argv[2:] or DEG_CASES, kind)
