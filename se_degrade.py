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
        f18 = np.asarray(list(feature_rows(frames)), dtype=np.float64)
        sup = np.asarray(predict_supports(f18, model), dtype=np.float64)
        X, names, info = se_features.build(frames, f18)
        np.savez_compressed(out / (cid + '.npz'), X=X, names=np.array(names), ref=ref, period=info['period'],
                            observed=info['observed'], release_sup=sup, drop=drop)
        act = per > 0
        print(cid, 'missing frac on active', round(float((~info['observed'])[act].mean()), 3), flush=True)


if __name__ == '__main__':
    kind = sys.argv[1].replace('build', '') or 'deg'
    build(sys.argv[2:] or DEG_CASES, kind)
