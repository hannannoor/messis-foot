"""Append impulse-touch features to every cached feature file (clean, deg, aug, provided). Idempotent."""
import sys
from multiprocessing import Pool
import numpy as np
import se_load, se_features

def job(path):
    z = dict(np.load(path))
    names = [str(s) for s in z['names']]
    if 'itouch_last' in names:
        return path.name, 'skip'
    kind = path.parent.name
    if kind == 'provided':
        import se_provided
        frames = se_provided.frames()
    else:
        cid = path.stem
        frames, _ = se_load.load(cid)
        if kind in ('cases_deg', 'cases_aug'):
            from se_degrade import degrade
            frames = degrade(frames, z['drop'])
    Xe, ne = se_features.impulse_features(frames)
    z['X'] = np.concatenate([z['X'], Xe], 1)
    z['names'] = np.array(names + list(ne))
    tmp = path.with_suffix('.tmp.npz')
    np.savez_compressed(tmp, **z)
    tmp.replace(path)
    return path.name, z['X'].shape

if __name__ == '__main__':
    P = se_load.PRIVATE
    paths = sorted((P / 'cases').glob('*.npz')) + sorted((P / 'cases_deg').glob('*.npz')) + sorted((P / 'cases_aug').glob('*.npz')) + [P / 'provided' / 'features.npz']
    with Pool(8) as pool:
        for r in pool.imap_unordered(job, paths):
            print(*r, flush=True)
