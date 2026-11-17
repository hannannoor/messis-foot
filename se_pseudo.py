"""Round 11: self-training. Turn a match's own decoded labels into a pseudo-labelled training case.

    python se_pseudo.py <name> <case .npz> <labels: .npy of 0 H,1 A,2 D,3 X  or  submission .csv> [margin]
        -> strong-emissions-reference/cases/pl-<name>.npz   (features of the case, ref = pseudo-labels)

The labels come from our own pipeline's output on that match; no person decides any of them. Cases named 'pl-*' are
supervised for ownership only (se_gru.HA_ONLY), so only the H and A pseudo-labels are used. `margin` (frames, default 0)
blanks the pseudo-labels within that distance of a change of label, where the decoder is least reliable.
Prints aggregate counts only.
"""
import sys

import numpy as np

import se_load


def read_labels(path):
    if str(path).endswith('.npy'):
        return np.load(path).astype(np.uint8)
    with open(path, newline='') as f:
        rows = f.read().split('\n')
    if rows[0].strip() != 'frame,label':
        raise ValueError('unexpected CSV header')
    return np.asarray(['HADX'.index(r.strip().split(',')[1]) for r in rows[1:] if r.strip()], np.uint8)


def build(name, case_path, label_path, margin=0):
    z = np.load(case_path)
    lab = read_labels(label_path)
    if len(lab) != len(z['X']):
        raise ValueError(f'labels {len(lab)} rows, case {len(z["X"])} rows')
    ref = lab.copy()
    if margin:
        ch = np.flatnonzero(lab[1:] != lab[:-1]) + 1
        near = np.zeros(len(lab), bool)
        for c in ch:
            near[max(0, c - margin):c + margin] = True
        ref[near] = 3
    ref[np.asarray(z['period']) <= 0] = 3
    out = se_load.PRIVATE / 'cases' / ('pl-' + name + '.npz')
    np.savez_compressed(out, X=z['X'], names=z['names'], period=z['period'], observed=z['observed'], ref=ref)
    counts = {k: int((ref == i).sum()) for i, k in enumerate('HADX')}
    print(out.name, 'rows', len(ref), counts, 'margin', margin)


if __name__ == '__main__':
    build(sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]) if len(sys.argv) > 4 else 0)
