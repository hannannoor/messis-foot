"""Input-only retained-owner block contrast; no training or reference access."""
from dataclasses import dataclass
from math import isfinite
import numpy as np

from ball_gap_policy import decode_ball_gap
from gap_solver.materialization_control import materialize_abstentions
from gap_solver.soft_sequence import sequence_usable
from gap_solver.tactical import feature_rows,PortableTree

MODES=('control','memory-ablated')
MODEL_SHA='363c45c70838b398cd87aee7474d7e281fd392f059a31b85712e312058aaab4d'


def _mode(mode):
    if mode not in MODES:raise ValueError('Unknown ablation mode')


def transform_row(row,mode):
    _mode(mode)
    try:values=tuple(row)
    except TypeError:raise ValueError('Invalid feature row') from None
    if len(values)!=18 or not all(isfinite(value) for value in values):raise ValueError('Invalid feature row')
    return values if mode=='control' else values[:15]+(0.,0.,10.)


def _matrix(matrix):
    try:
        with np.errstate(over='raise',invalid='raise'):values=np.array(matrix,dtype=np.float32,copy=True,order='C')
    except (TypeError,ValueError,FloatingPointError):raise ValueError('Invalid float32 feature matrix') from None
    if values.ndim!=2 or values.shape[1]!=18 or not np.isfinite(values).all():raise ValueError('Invalid feature dimensions/values')
    return values


def transform_matrix(matrix,mode):
    _mode(mode);values=_matrix(matrix)
    if mode=='memory-ablated':values[:,15:18]=(0.,0.,10.)
    return values


@dataclass(frozen=True)
class PreparedInputs:
    matrix: object
    periods: object
    observed: object
    usable: object

    def __post_init__(self):
        matrix=_matrix(self.matrix);n=len(matrix)
        periods=np.array(self.periods,copy=True);observed=np.array(self.observed,copy=True);usable=np.array(self.usable,copy=True)
        if not n or any(value.ndim!=1 or len(value)!=n for value in (periods,observed,usable)):
            raise ValueError('Input dimensions differ')
        if periods.dtype.kind not in 'ui' or not np.isin(periods,[0,1,2]).all() or observed.dtype!=bool or usable.dtype!=bool:
            raise ValueError('Invalid period/availability flags')
        for name,value in (('matrix',matrix),('periods',periods.astype(np.uint8)),('observed',observed),('usable',usable)):
            value.setflags(write=False);object.__setattr__(self,name,value)


@dataclass(frozen=True)
class Prediction:
    supports: object
    latent: tuple
    final: tuple
    policy_counts: dict


def prepare_inputs(frames):
    frames=list(frames)
    if not frames or any(f.dead_evidence or f.dead_source or f.tag_team or f.restart_hint for f in frames):
        raise ValueError('Nonempty geometry-only inputs required')
    return PreparedInputs(np.asarray(list(feature_rows(frames)),dtype=np.float32),
        np.asarray([f.period for f in frames],dtype=np.uint8),np.asarray([f.ball_observed for f in frames],dtype=bool),
        np.asarray([bool(sequence_usable(f)) for f in frames],dtype=bool))


def predict_supports(matrix,model):
    x=_matrix(matrix);PortableTree(model)
    nodes=np.zeros(len(x),dtype=np.int32)
    left=np.asarray(model['children_left']);right=np.asarray(model['children_right'])
    feature=np.asarray(model['feature']);threshold=np.asarray(model['threshold'],dtype=np.float64)
    while True:
        active=np.flatnonzero(left[nodes]!=-1)
        if not len(active):break
        at=nodes[active]
        nodes[active]=np.where(x[active,feature[at]]<=threshold[at],left[at],right[at])
    return np.asarray(model['probabilities'],dtype=np.float64)[nodes]


def infer_prepared(inputs,model,mode):
    if not isinstance(inputs,PreparedInputs):raise ValueError('Prepared input contract required')
    supports=predict_supports(transform_matrix(inputs.matrix,mode),model)
    periods=inputs.periods.tolist()
    latent,counts=decode_ball_gap(supports,periods,inputs.usable.tolist(),inputs.observed.tolist())
    supports.setflags(write=False)
    return Prediction(supports,tuple(latent),tuple(materialize_abstentions(latent,periods)),counts)
