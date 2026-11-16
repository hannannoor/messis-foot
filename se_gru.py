"""Bidirectional GRU over per-frame features -> H/A/D supports. External data only.

    python se_gru.py <tag> cv|final ['{"hidden":128,"steps":3000}']
Loss: 3-class CE on rows labelled H/A/D in D-labelled providers (DFL/WCSF); on SkillCorner (no D labels) only
H-vs-A conditional likelihood. Home/away swap augmentation; swap test-time averaging.
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn

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
DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'


XDROP = ()   # feature-name prefixes to leave out (opts "xdrop"), for ablations
# Providers supervised for H-vs-A only. SkillCorner has no D labels. Metrica (round 10): its dead ball IS the missing
# ball, so D supervision there would teach an exact-edge shortcut that the provided match does not share.
HA_ONLY = ('skillcorner', 'metrica')


def load(cid):
    X, ref, per, names = load_path(PRIVATE / 'cases' / (cid + '.npz'))
    if cid.startswith('metrica'):   # round 10: ball-flag reference (se_metrica_ballref.py), not the event-derived one
        ref = np.load(PRIVATE / 'metrica_ballref' / (cid + '.npy')).astype(np.int64)
        if len(ref) != len(X):
            raise ValueError('Metrica ball-flag reference length differs from the case')
    return X, ref, per, names


KEEP_NAMES = None   # exact feature list (saved models), overrides XDROP when set


def load_path(path):
    z = np.load(path)
    names = [str(s) for s in z['names']]
    if KEEP_NAMES is not None:
        keep = [names.index(n) for n in KEEP_NAMES]
    else:
        keep = [i for i, n in enumerate(names) if not (XDROP and n.startswith(XDROP))]
    return (z['X'][:, keep].astype(np.float32), z['ref'].astype(np.int64), z['period'].astype(np.int64),
            [names[i] for i in keep])


def segments(period):
    out, i, n = [], 0, len(period)
    while i < n:
        j = i
        while j < n and period[j] == period[i]:
            j += 1
        if period[i] > 0:
            out.append((i, j))
        i = j
    return out


class Net(nn.Module):
    def __init__(self, d, h, layers=2, drop=.1, n_out=3):
        super().__init__()
        self.inp = nn.Sequential(nn.Linear(d, h), nn.GELU(), nn.Dropout(drop), nn.Linear(h, h), nn.GELU())
        self.gru = nn.GRU(h, h, num_layers=layers, batch_first=True, bidirectional=True, dropout=drop)
        self.out = nn.Sequential(nn.Dropout(drop), nn.Linear(2 * h, h), nn.GELU(), nn.Linear(h, n_out))

    def forward(self, x):
        y, _ = self.gru(self.inp(x))
        return self.out(y)


def spell_weights(ref, per, scale, cap):
    """Weight H/A frames by inverse spell length: clip(scale / len, 1, cap). Other frames 1."""
    w = np.ones(len(ref), np.float32)
    if not scale:
        return w
    i, n = 0, len(ref)
    while i < n:
        j = i + 1
        while j < n and ref[j] == ref[i] and per[j] == per[i]:
            j += 1
        if ref[i] < 2:
            w[i:j] = min(cap, max(1.0, scale / (j - i)))
        i = j
    return w


def boundary_target(ref, per, hasd, k=2):
    """1 within +-k frames of a possession boundary. D providers: any change among H/A/D labels. SkillCorner (no D):
    change of team between consecutive H/A-labelled frames (across X). Returns (target, valid mask)."""
    n = len(ref)
    ev = np.zeros(n, bool)
    if hasd:
        lab = ref < 3
        ch = np.zeros(n, bool)
        ch[1:] = lab[1:] & lab[:-1] & (ref[1:] != ref[:-1]) & (per[1:] == per[:-1])
        ev = ch
        valid = lab
    else:
        last, lastp = -1, -1
        for t in np.flatnonzero(ref < 2):
            if last >= 0 and ref[t] != last and per[t] == lastp:
                ev[t] = True
            last, lastp = ref[t], per[t]
        valid = ref < 2
    tgt = np.convolve(ev.astype(float), np.ones(2 * k + 1), 'same') > 0
    return tgt.astype(np.float32), valid


def loss_fn(logits, ref, dmask, wt=None, bt=None, bv=None, lam=0.0):
    """ref: 0 H,1 A,2 D,3 X. dmask: True where provider has D labels."""
    logp = torch.log_softmax(logits, -1)
    full = (ref < 3) & dmask
    own = (ref < 2) & ~dmask
    lab = ref.clamp(max=2)
    l1 = -logp.gather(-1, lab.unsqueeze(-1)).squeeze(-1)
    cond = logp[..., :2] - torch.logsumexp(logp[..., :2], -1, keepdim=True)
    l2 = -cond.gather(-1, lab.clamp(max=1).unsqueeze(-1)).squeeze(-1)
    if wt is None:
        wt = torch.ones_like(l1)
    tot = (l1 * full * wt).sum() + (l2 * own * wt).sum()
    main = tot / ((full + own) * wt).sum().clamp(min=1)
    if lam and bt is not None:
        bl = nn.functional.binary_cross_entropy_with_logits(logits[..., 3], bt, reduction='none',
                                                            pos_weight=torch.tensor(5.0, device=logits.device))
        main = main + lam * (bl * bv).sum() / bv.sum().clamp(min=1)
    return main


def train(cids, opts, plan, stats):
    mu, sd = stats
    data = []
    for cid in cids:
        X, ref, per, _ = load(cid)
        X = np.clip((X - mu) / sd, -6, 6).astype(np.float32)
        Xs = np.clip((swapped(load(cid)[0], plan) - mu) / sd, -6, 6).astype(np.float32)
        refs = np.where(ref == 0, 1, np.where(ref == 1, 0, ref))
        wt = spell_weights(ref, per, opts.get('short_scale', 0), opts.get('short_cap', 4.0))
        aug = None
        ap = PRIVATE / 'cases_aug' / (cid + '.npz')
        views = [q for q in (PRIVATE / v / (cid + '.npz') for v in opts.get('aug_views', ())) if q.exists()]
        if opts.get('aug') and views:
            aug = ('lazy', [load_path(v)[0] for v in views])   # raw; normalised + swapped per chunk (RAM)
        elif opts.get('aug') and ap.exists():
            Xa = load_path(ap)[0]
            aug = (np.clip((Xa - mu) / sd, -6, 6).astype(np.float32), np.clip((swapped(Xa, plan) - mu) / sd, -6, 6).astype(np.float32))
        bt, bv = boundary_target(ref, per, not cid.startswith(HA_ONLY))   # same under H/A swap
        data.append((X, Xs, ref, refs, segments(per), not cid.startswith(HA_ONLY), wt, aug, bt, bv))
    torch.manual_seed(opts.get('seed', 1729))
    rng = np.random.default_rng(opts.get('seed', 1729))
    lam = float(opts.get('bnd', 0.0))
    net = Net(data[0][0].shape[1], opts.get('hidden', 128), opts.get('layers', 2), opts.get('drop', .1),
              4 if lam else 3).to(DEVICE)
    steps = opts.get('steps', 3000)
    opt = torch.optim.AdamW(net.parameters(), lr=opts.get('lr', 1e-3), weight_decay=1e-2)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=opts.get('lr', 1e-3), total_steps=steps, pct_start=.1)
    L, B = opts.get('chunk', 1500), opts.get('batch', 24)
    net.train()
    t0 = time.time()
    for step in range(steps):
        xb, rb, db, wb, bb, vb = [], [], [], [], [], []
        for _ in range(B):
            X, Xs, ref, refs, segs, hasd, wt, aug, btt, bvv = data[rng.integers(len(data))]
            raw = None
            if aug is not None and rng.random() < opts.get('aug_p', .5):
                if isinstance(aug[0], str):
                    raw = aug[1][rng.integers(len(aug[1]))]
                else:
                    X, Xs = aug
            a, b = segs[rng.integers(len(segs))]
            s = rng.integers(a, max(a + 1, b - L))
            e = min(b, s + L)
            sw = rng.random() < .5
            if raw is not None:
                z = swapped(raw[s:e], plan) if sw else raw[s:e]
                x = np.clip((z - mu) / sd, -6, 6).astype(np.float32)
            else:
                x = (Xs if sw else X)[s:e]
            r = (refs if sw else ref)[s:e]
            ww = wt[s:e]
            b1, v1 = btt[s:e], bvv[s:e].astype(np.float32)
            if e - s < L:
                x = np.pad(x, ((0, L - (e - s)), (0, 0)))
                r = np.pad(r, (0, L - (e - s)), constant_values=3)
                ww = np.pad(ww, (0, L - (e - s)), constant_values=1)
                b1, v1 = np.pad(b1, (0, L - (e - s))), np.pad(v1, (0, L - (e - s)))
            xb.append(x); rb.append(r); db.append(hasd); wb.append(ww); bb.append(b1); vb.append(v1)
        xb = torch.from_numpy(np.stack(xb)).to(DEVICE)
        rb = torch.from_numpy(np.stack(rb)).to(DEVICE)
        dm = torch.tensor(db, device=DEVICE)[:, None].expand_as(rb)
        wtb = torch.from_numpy(np.stack(wb)).to(DEVICE)
        if lam:
            loss = loss_fn(net(xb), rb, dm, wtb, torch.from_numpy(np.stack(bb)).to(DEVICE),
                           torch.from_numpy(np.stack(vb)).to(DEVICE), lam)
        else:
            loss = loss_fn(net(xb), rb, dm, wtb)
        opt.zero_grad()
        loss.backward()
        nn.utils.clip_grad_norm_(net.parameters(), 1.0)
        opt.step()
        sched.step()
        if step % 500 == 0:
            print(f'  step {step} loss {loss.item():.4f} {time.time() - t0:.0f}s', flush=True)
    return net


@torch.no_grad()
def predict(net, cid, plan, stats, path=None):
    mu, sd = stats
    net.eval()
    X, ref, per, _ = load(cid) if path is None else load_path(path)
    sup = np.tile(np.array([[.45, .45, .1]]), (len(X), 1))
    bnd = np.zeros(len(X), np.float32)
    for sw in (False, True):
        Z = swapped(X, plan) if sw else X
        Z = np.clip((Z - mu) / sd, -6, 6).astype(np.float32)
        Z[:, sd < 1e-2] = 0.0  # constant in training (e.g. geometry-valid flag): neutral at inference
        for a, b in segments(per):
            p = np.zeros((b - a, 3), np.float32)
            pb = np.zeros(b - a, np.float32)
            W, C = 6000, 1500  # window, context on each side
            for s in range(a, b, W):
                lo, hi = max(a, s - C), min(b, s + W + C)
                o = net(torch.from_numpy(np.ascontiguousarray(Z[lo:hi]))[None].to(DEVICE))[0]
                q = torch.softmax(o[:, :3], -1).cpu().numpy()
                e = min(b, s + W)
                p[s - a:e - a] = q[s - lo:e - lo]
                if o.shape[-1] > 3:
                    pb[s - a:e - a] = torch.sigmoid(o[:, 3]).cpu().numpy()[s - lo:e - lo]
            if sw:
                p = p[:, [1, 0, 2]]
            sup[a:b] = p if not sw else .5 * (sup[a:b] + p)
            bnd[a:b] = pb if not sw else .5 * (bnd[a:b] + pb)
    LAST_BND[0] = bnd
    return sup


LAST_BND = [None]   # boundary probabilities of the last predict() call (models with a boundary head)


def run(tag, mode, opts):
    out = PRIVATE / 'preds' / tag
    out.mkdir(parents=True, exist_ok=True)
    (out / 'opts.json').write_text(json.dumps(dict(opts, mode=mode, model='gru')))
    global XDROP
    XDROP = tuple(opts.get('xdrop', ()))
    names = load(DEV[0])[3]
    plan = swap_plan(names)
    folds = [(tuple(c for c in DEV if c not in f), f) for f in FOLDS] if mode == 'cv' else [(DEV, HOLDOUT)] if mode == 'final' else [(ALL, ())]
    if mode == 'custom':   # round 9: train on ALL + opts["extra_train"], predict opts["test"] (e.g. Metrica leave-one-game-out)
        folds = [(ALL + tuple(opts.get('extra_train', ())), tuple(opts['test']))]
    for tr, te in folds:
        t = time.time()
        Xall = np.concatenate([load(c)[0][::10] for c in tr])
        mu, sd = Xall.mean(0), Xall.std(0) + 1e-3
        net = train(tr, opts, plan, (mu, sd))
        for cid in te:
            np.savez_compressed(out / (cid + '.npz'), sup=predict(net, cid, plan, (mu, sd)), bnd=LAST_BND[0])
            dp = PRIVATE / 'cases_deg' / (cid + '.npz')
            if dp.exists():
                (out / 'deg').mkdir(exist_ok=True)
                np.savez_compressed(out / 'deg' / (cid + '.npz'), sup=predict(net, None, plan, (mu, sd), dp), bnd=LAST_BND[0])
            for v in opts.get('eval_dirs', ()):   # extra evaluation views (investigation)
                vp = PRIVATE / v / (cid + '.npz')
                if vp.exists():
                    (out / v).mkdir(exist_ok=True)
                    np.savez_compressed(out / v / (cid + '.npz'), sup=predict(net, None, plan, (mu, sd), vp), bnd=LAST_BND[0])
        if mode == 'cv':   # keep fold models so new evaluation views need no retraining (se_predict.py)
            torch.save(dict(state=net.state_dict(), mu=mu, sd=sd, opts=opts, names=names, test=list(te),
                            hidden=opts.get('hidden', 128), layers=opts.get('layers', 2), n_out=4 if opts.get('bnd') else 3),
                       out / f'fold{FOLDS.index(te)}.pt')
        if mode in ('final', 'all'):
            prov = PRIVATE / 'provided' / 'features.npz'
            np.savez_compressed(out / 'provided.npz', sup=predict(net, None, plan, (mu, sd), prov), bnd=LAST_BND[0])
            torch.save(dict(state=net.state_dict(), mu=mu, sd=sd, opts=opts, names=names), out / 'model.pt')
        print('fold', te, round(time.time() - t, 1), flush=True)


if __name__ == '__main__':
    run(sys.argv[1], sys.argv[2], json.loads(sys.argv[3]) if len(sys.argv) > 3 else {})
