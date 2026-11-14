"""Live/dead sequence experiment: replace the frozen D-versus-live allocation on supported visible-ball rows.

With frozen supports (h, a, d) and a dead score q on an integration row (temporally eligible, ball observed, valid
geometry, active period): q is clipped to [1e-6, 1 - 1e-6], r = h / (h + a) (or .5 when h + a == 0) and the row
becomes ((1 - q) r, (1 - q)(1 - r), q).  Every other row is copied bit for bit.  No weight is fitted and q is not
multiplied into the old D score.  The supports then run through the unchanged emission-supplied release assembly
(decode, gap rule, decoder restart, gap rule, empty kickoff starts).  Reference labels are never read here.
"""
import numpy as np

from gap_solver.tactical import feature_rows
from memory_ablation import predict_supports
from recent_geometry_assembly import SupportSet, assemble_research
from recent_geometry_features import geometry_valid

STREAMS = ('release', 'instant', 'temporal')
CLIP = 1e-6


class StreamSupportSet(SupportSet):
    def __post_init__(self):
        if self.method not in STREAMS:
            raise ValueError('Unknown stream')
        values = np.array(self.supports, dtype=np.float64, copy=True)
        if values.ndim != 2 or values.shape[1] != 3 or not np.isfinite(values).all():
            raise ValueError('Supports must be a finite (n, 3) array')
        values.setflags(write=False)
        object.__setattr__(self, 'supports', values)


def frozen_supports(frames, frozen_model):
    matrix = np.asarray(list(feature_rows(list(frames))), dtype=np.float32)
    return np.asarray(predict_supports(matrix, frozen_model), dtype=np.float64)


def denominator_mask(frames):
    return np.fromiter((f.period in (1, 2) and geometry_valid(f) and f.ball_observed for f in frames), dtype=bool)


def integration_mask(frames, eligible):
    frames = list(frames)
    eligible = np.asarray(eligible, dtype=bool)
    if eligible.shape != (len(frames),):
        raise ValueError('Eligibility/frame dimensions differ')
    return denominator_mask(frames) & eligible


def integrate(frozen, q, mask):
    frozen = np.asarray(frozen, dtype=np.float64)
    q = np.asarray(q, dtype=np.float64)
    mask = np.asarray(mask, dtype=bool)
    n = len(frozen)
    if frozen.shape != (n, 3) or q.shape != (n,) or mask.shape != (n,):
        raise ValueError('Integration dimensions differ')
    if not np.isfinite(frozen).all() or not np.isfinite(q[mask]).all():
        raise ValueError('Non-finite integration inputs')
    out = frozen.copy()
    if mask.any():
        h, a = frozen[mask, 0], frozen[mask, 1]
        live = h + a
        r = np.where(live > 0, h / np.where(live > 0, live, 1.), .5)
        dead = np.clip(q[mask], CLIP, 1 - CLIP)
        out[mask] = np.column_stack(((1 - dead) * r, (1 - dead) * (1 - r), dead))
    return out


def assemble_stream(frames, stream, supports):
    return assemble_research(list(frames), StreamSupportSet(stream, supports))


def require_same_gaps(assemblies):
    gaps = {name: tuple(a.stoppage_gaps) for name, a in assemblies.items()}
    if len(set(gaps.values())) != 1:
        raise ValueError('Gap-rule stoppage intervals differ between streams')
