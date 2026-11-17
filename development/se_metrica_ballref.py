"""Round 10: save the ball-flag reference of each Metrica sample game for training and scoring.
    python se_metrica_ballref.py     -> strong-emissions-reference/metrica_ballref/<cid>.npy  (0 H, 1 A, 2 D, 3 X)
External public data only (metrica_ball_reference.py)."""
import numpy as np

import se_load

if __name__ == '__main__':
    out = se_load.PRIVATE / 'metrica_ballref'
    out.mkdir(parents=True, exist_ok=True)
    for game in se_load.METRICA:
        cid = 'metrica-' + game
        frames, ref = se_load.load(cid, reference='ball')
        case = np.load(se_load.PRIVATE / 'cases' / (cid + '.npz'))
        if len(ref) != len(case['period']) or not np.array_equal(case['period'], [f.period for f in frames]):
            raise ValueError('Reference does not line up with the saved case: ' + cid)
        np.save(out / (cid + '.npy'), ref)
        print(cid, {k: int((ref == i).sum()) for i, k in enumerate('HADX')}, flush=True)
