"""Provided match: build features exactly like the external cases (inference only; no GT, no video).

    python se_provided.py extract   -> strong-emissions-reference/provided/features.npz + aggregate shift report
    python se_provided.py submit <predtag> <power> <outdir>  -> submission.csv through the release decoder chain
"""
import json
import sys
from pathlib import Path

import numpy as np

import se_features
import se_load

DATA = Path.home() / 'Desktop' / 'more than a hack data' / 'tactical cam'
PREFIX = str(DATA / 'BAR-ATH_tactical')
OUT = se_load.PRIVATE / 'provided'


def frames():
    from release_runtime import load_source
    fr, _ = load_source(*(Path(PREFIX + s) for s in ('_atd.xml', '_atd.txt', '_homography.csv')))
    return list(fr)


def extract():
    from gap_solver.tactical import feature_rows
    OUT.mkdir(parents=True, exist_ok=True)
    fr = frames()
    f18 = np.asarray(list(feature_rows(fr)), dtype=np.float64)
    X, names, info = se_features.build(fr, f18)
    np.savez_compressed(OUT / 'features.npz', X=X, names=np.array(names), period=info['period'],
                        observed=info['observed'], ref=np.full(len(X), 3, np.uint8))
    # aggregate shift report vs external dev matches (means on active rows)
    act = info['period'] > 0
    ext = []
    for cid in se_load.ALL:
        if cid in se_load.HOLDOUT:
            continue
        z = np.load(se_load.PRIVATE / 'cases' / (cid + '.npz'))
        ext.append(z['X'][z['period'] > 0][::20])
    E = np.concatenate(ext)
    mu, sd = E.mean(0), E.std(0) + 1e-6
    z = (X[act].mean(0) - mu) / sd
    order = np.argsort(-np.abs(z))[:20]
    report = dict(rows=len(X), active=int(act.sum()), ball_observed_frac=float(info['observed'][act].mean()),
                  largest_shifts={names[i]: round(float(z[i]), 2) for i in order})
    (OUT / 'shift.json').write_text(json.dumps(report, indent=1))
    print(json.dumps(report, indent=1))


def submit(tag, power, outdir):
    from kickoff_patch import kickoff_starts
    from live_dead_assembly import StreamSupportSet
    from recent_geometry_assembly import assemble_research
    from release_runtime import submission_bytes
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=False)
    sup = np.load(se_load.PRIVATE / 'preds' / tag / 'provided.npz')['sup']
    sup = np.clip(sup, 1e-9, 1) ** float(power)
    sup = np.clip(sup / sup.sum(1, keepdims=True), 1e-6, 1)
    sup = sup / sup.sum(1, keepdims=True)
    fr = frames()
    starts = kickoff_starts(PREFIX + '_smart_tagging.xml')
    asm = assemble_research(fr, StreamSupportSet('release', sup), starts)
    data = submission_bytes(asm.final)
    (outdir / 'submission.csv').write_bytes(data)
    counts = {k: asm.final.count(k) for k in 'HADX'}
    (outdir / 'receipt.json').write_text(json.dumps(dict(tag=tag, power=power, rows=len(asm.final), counts=counts,
                                                         kickoff_changed=asm.kickoff_changed), default=str, indent=1))
    print(counts)


if __name__ == '__main__':
    if sys.argv[1] == 'extract':
        extract()
    else:
        submit(*sys.argv[2:5])
