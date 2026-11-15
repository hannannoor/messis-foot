"""Append impulse-touch (v4) and contact-reliability (v5) features to every cached feature file. Idempotent."""
import sys
from multiprocessing import Pool
import numpy as np
import se_load, se_features

def job(path):
    z = dict(np.load(path))
    names = [str(s) for s in z['names']]
    todo = [(m, f) for m, f in (('itouch_last', se_features.impulse_features),
                                 ('itouch_last_rel', se_features.impulse_rel_features),
                                 ('tsH_cx', se_features.team_shape_features),
                                 ('tsH_line_p50', se_features.team_shape_ext_features)) if m not in names]
    if not todo:
        return path.name, 'skip'
    kind = path.parent.name
    if kind == 'provided':
        import se_provided
        frames = se_provided.frames()
    else:
        cid = path.stem
        frames, _ = se_load.load(cid)
        if kind == 'cases_deg' or kind.startswith(('cases_aug', 'cases_eval')):
            from se_degrade import degrade
            frames = degrade(frames, z['drop'])
    for _, fn in todo:
        Xe, ne = fn(frames)
        z['X'] = np.concatenate([z['X'], Xe], 1)
        names = names + list(ne)
    z['names'] = np.array(names)
    tmp = path.with_suffix('.tmp.npz')
    np.savez_compressed(tmp, **z)
    tmp.replace(path)
    return path.name, z['X'].shape

if __name__ == '__main__':
    P = se_load.PRIVATE
    paths = sorted((P / 'cases').glob('*.npz')) + sorted((P / 'cases_deg').glob('*.npz')) + sorted((P / 'cases_aug').glob('*.npz')) + [P / 'provided' / 'features.npz']
    for d in sorted(P.glob('cases_aug?*')):
        paths += sorted(d.glob('*.npz'))
    for d in sorted(P.glob('cases_eval*')):
        paths += sorted(d.glob('*.npz'))
    if '--only-new' in sys.argv:
        paths = [p for p in paths if p.parent.name in ('cases_aug2', 'cases_aug3')]
    if '--only' in sys.argv:
        keep = sys.argv[sys.argv.index('--only') + 1].split(',')
        paths = [p for p in paths if p.parent.name in keep]
    if '--only-eval' in sys.argv:
        paths = [p for p in paths if p.parent.name.startswith('cases_eval')]
    with Pool(8) as pool:
        for r in pool.imap_unordered(job, paths):
            print(*r, flush=True)
