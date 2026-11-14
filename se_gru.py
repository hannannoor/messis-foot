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


def load(cid):
    z = np.load(PRIVATE / 'cases' / (cid + '.npz'))
    return z['X'].astype(np.float32), z['ref'].astype(np.int64), z['period'].astype(np.int64), [str(s) for s in z['names']]


def load_path(path):
    z = np.load(path)
    return z['X'].astype(np.float32), z['ref'].astype(np.int64), z['period'].astype(np.int64), [str(s) for s in z['names']]


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
    def __init__(self, d, h, layers=2, drop=.1):
        super().__init__()
        self.inp = nn.Sequential(nn.Linear(d, h), nn.GELU(), nn.Dropout(drop), nn.Linear(h, h), nn.GELU())
        self.gru = nn.GRU(h, h, num_layers=layers, batch_first=True, bidirectional=True, dropout=drop)
        self.out = nn.Sequential(nn.Dropout(drop), nn.Linear(2 * h, h), nn.GELU(), nn.Linear(h, 3))

    def forward(self, x):
        y, _ = self.gru(self.inp(x))
        return self.out(y)


def loss_fn(logits, ref, dmask):
    """ref: 0 H,1 A,2 D,3 X. dmask: True where provider has D labels."""
    logp = torch.log_softmax(logits, -1)
    full = (ref < 3) & dmask
    own = (ref < 2) & ~dmask
    lab = ref.clamp(max=2)
    l1 = -logp.gather(-1, lab.unsqueeze(-1)).squeeze(-1)
    cond = logp[..., :2] - torch.logsumexp(logp[..., :2], -1, keepdim=True)
    l2 = -cond.gather(-1, lab.clamp(max=1).unsqueeze(-1)).squeeze(-1)
    tot = (l1 * full).sum() + (l2 * own).sum()
    return tot / (full.sum() + own.sum()).clamp(min=1)


def train(cids, opts, plan, stats):
    mu, sd = stats
    data = []
    for cid in cids:
        X, ref, per, _ = load(cid)
        X = np.clip((X - mu) / sd, -6, 6).astype(np.float32)
        Xs = np.clip((swapped(load(cid)[0], plan) - mu) / sd, -6, 6).astype(np.float32)
        refs = np.where(ref == 0, 1, np.where(ref == 1, 0, ref))
        data.append((X, Xs, ref, refs, segments(per), not cid.startswith('skillcorner')))
    torch.manual_seed(opts.get('seed', 1729))
    rng = np.random.default_rng(opts.get('seed', 1729))
    net = Net(data[0][0].shape[1], opts.get('hidden', 128), opts.get('layers', 2), opts.get('drop', .1)).to(DEVICE)
    steps = opts.get('steps', 3000)
    opt = torch.optim.AdamW(net.parameters(), lr=opts.get('lr', 1e-3), weight_decay=1e-2)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=opts.get('lr', 1e-3), total_steps=steps, pct_start=.1)
    L, B = opts.get('chunk', 1500), opts.get('batch', 24)
    net.train()
    t0 = time.time()
    for step in range(steps):
        xb, rb, db = [], [], []
        for _ in range(B):
            X, Xs, ref, refs, segs, hasd = data[rng.integers(len(data))]
            a, b = segs[rng.integers(len(segs))]
            s = rng.integers(a, max(a + 1, b - L))
            e = min(b, s + L)
            sw = rng.random() < .5
            x = (Xs if sw else X)[s:e]
            r = (refs if sw else ref)[s:e]
            if e - s < L:
                x = np.pad(x, ((0, L - (e - s)), (0, 0)))
                r = np.pad(r, (0, L - (e - s)), constant_values=3)
            xb.append(x); rb.append(r); db.append(hasd)
        xb = torch.from_numpy(np.stack(xb)).to(DEVICE)
        rb = torch.from_numpy(np.stack(rb)).to(DEVICE)
        dm = torch.tensor(db, device=DEVICE)[:, None].expand_as(rb)
        loss = loss_fn(net(xb), rb, dm)
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
    for sw in (False, True):
        Z = swapped(X, plan) if sw else X
        Z = np.clip((Z - mu) / sd, -6, 6).astype(np.float32)
        Z[:, sd < 1e-2] = 0.0  # constant in training (e.g. geometry-valid flag): neutral at inference
        for a, b in segments(per):
            p = np.zeros((b - a, 3), np.float32)
            W, C = 6000, 1500  # window, context on each side
            for s in range(a, b, W):
                lo, hi = max(a, s - C), min(b, s + W + C)
                q = torch.softmax(net(torch.from_numpy(np.ascontiguousarray(Z[lo:hi]))[None].to(DEVICE)), -1)[0]
                q = q.cpu().numpy()
                e = min(b, s + W)
                p[s - a:e - a] = q[s - lo:e - lo]
            if sw:
                p = p[:, [1, 0, 2]]
            sup[a:b] = p if not sw else .5 * (sup[a:b] + p)
    return sup


def run(tag, mode, opts):
    out = PRIVATE / 'preds' / tag
    out.mkdir(parents=True, exist_ok=True)
    (out / 'opts.json').write_text(json.dumps(dict(opts, mode=mode, model='gru')))
    names = load(DEV[0])[3]
    plan = swap_plan(names)
    folds = [(tuple(c for c in DEV if c not in f), f) for f in FOLDS] if mode == 'cv' else [(DEV, HOLDOUT)] if mode == 'final' else [(ALL, ())]
    for tr, te in folds:
        t = time.time()
        Xall = np.concatenate([load(c)[0][::10] for c in tr])
        mu, sd = Xall.mean(0), Xall.std(0) + 1e-3
        net = train(tr, opts, plan, (mu, sd))
        for cid in te:
            np.savez_compressed(out / (cid + '.npz'), sup=predict(net, cid, plan, (mu, sd)))
        if mode in ('final', 'all'):
            prov = PRIVATE / 'provided' / 'features.npz'
            np.savez_compressed(out / 'provided.npz', sup=predict(net, None, plan, (mu, sd), prov))
            torch.save(dict(state=net.state_dict(), mu=mu, sd=sd, opts=opts, names=names), out / 'model.pt')
        print('fold', te, round(time.time() - t, 1), flush=True)


if __name__ == '__main__':
    run(sys.argv[1], sys.argv[2], json.loads(sys.argv[3]) if len(sys.argv) > 3 else {})
