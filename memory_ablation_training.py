"""Exact historical training recipe, with one matched retained-owner ablation."""
from dataclasses import dataclass
import hashlib
import json
import numpy as np

from gap_solver.selection import ball_mask,mask_frames,export_tree
from memory_ablation import transform_matrix,predict_supports,MODEL_SHA,MODES
from gap_solver.tactical import feature_rows

TRAIN_MATCHES=('J03WOH','J03WOY','J03WPY','J03WMX')


def model_digest(model):
    return hashlib.sha256(json.dumps(model,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def semantic_digest(values):
    value=np.ascontiguousarray(values)
    if value.dtype.byteorder=='>':value=value.astype(value.dtype.newbyteorder('<'))
    header=json.dumps(dict(dtype=value.dtype.str,shape=list(value.shape)),sort_keys=True,separators=(',',':')).encode()
    return hashlib.sha256(header+b'\n'+value.tobytes()).hexdigest()


@dataclass(frozen=True)
class TrainingData:
    matrix: object
    target: object
    weights: object
    row_identity: object
    group_counts: tuple

    def __post_init__(self):
        matrix=transform_matrix(self.matrix,'control');target=np.array(self.target,copy=True)
        weights=np.array(self.weights,dtype=np.float64,copy=True);identity=np.array(self.row_identity,copy=True)
        n=len(matrix)
        if not n or target.shape!=(n,) or target.dtype.kind not in 'ui' or not np.isin(target,[0,1,2]).all():
            raise ValueError('Invalid fitting targets')
        if weights.shape!=(n,) or not np.isfinite(weights).all() or np.any(weights<=0):raise ValueError('Invalid fitting weights')
        if identity.shape!=(n,3) or identity.dtype.kind not in 'ui':raise ValueError('Invalid private row identities')
        for name,value in (('matrix',matrix),('target',target.astype(np.uint8)),('weights',weights),('row_identity',identity.astype(np.int64))):
            value.setflags(write=False);object.__setattr__(self,name,value)
        object.__setattr__(self,'group_counts',tuple(dict(value) for value in self.group_counts))


def prepare_training(groups):
    groups=list(groups)
    if tuple(group['match'] for group in groups)!=TRAIN_MATCHES:raise ValueError('Exact historical training order required')
    matrices=[];targets=[];weights=[];identities=[];counts=[]
    for group_index,group in enumerate(groups):
        frames=list(group['frames']);target=np.asarray(group['reference']);periods=np.asarray(group['periods'])
        if target.shape!=(len(frames),) or periods.shape!=target.shape or target.dtype.kind not in 'ui' or not np.isin(target,[0,1,2,3]).all():
            raise ValueError('Invalid training reference dimensions/codes')
        if not np.array_equal(periods,[frame.period for frame in frames]) or not np.isin(periods,[1,2]).all():
            raise ValueError('Training period structure differs')
        if any(f.dead_evidence or f.dead_source or f.tag_team or f.restart_hint for f in frames):raise ValueError('Geometry-only training frames required')
        take=(np.arange(len(frames))%5==0)&(target<3);selected=np.flatnonzero(take)
        if not len(selected):raise ValueError('Training group has no selected known rows')
        for regime,rate in enumerate((0.,.3)):
            inputs=frames if rate==0 else mask_frames(frames,ball_mask(periods,rate,1729+group_index))
            matrix=transform_matrix(list(feature_rows(inputs)),'control')
            matrices.append(matrix[take]);targets.append(target[take])
            weights.append(np.full(len(selected),1./len(selected),dtype=np.float64))
            identities.append(np.column_stack((np.full(len(selected),group_index),np.full(len(selected),regime),selected)))
            counts.append(dict(match=group['match'],regime='natural' if regime==0 else 'mask30',rows=len(selected)))
    return TrainingData(np.concatenate(matrices),np.concatenate(targets),np.concatenate(weights),np.concatenate(identities),tuple(counts))


class ControlMismatch(ValueError):
    def __init__(self,model,receipt):
        super().__init__('Historical control reconstruction failed; candidate not fitted')
        self.model=model;self.receipt=receipt


def fit_pair(data,on_fit_entry,expected_control_sha=MODEL_SHA):
    from sklearn.tree import DecisionTreeClassifier
    if not isinstance(data,TrainingData) or not callable(on_fit_entry):raise ValueError('Training contract and entry callback required')
    original={name:semantic_digest(getattr(data,name)) for name in ('matrix','target','weights','row_identity')}
    results={}
    for mode in MODES:
        matrix=transform_matrix(data.matrix,mode)
        if matrix[:,:15].tobytes()!=data.matrix[:,:15].tobytes():raise ValueError('Ablation changed unrelated features')
        classifier=DecisionTreeClassifier(max_depth=4,min_samples_leaf=125,random_state=1729)
        on_fit_entry(mode)
        classifier.fit(matrix,data.target,sample_weight=data.weights)
        model=export_tree(classifier);digest=model_digest(model)
        portable=predict_supports(matrix,model);expected=classifier.predict_proba(matrix)
        if not np.allclose(portable,expected,atol=1e-12,rtol=0):raise ValueError('Portable model differs from fitted supports')
        receipt=dict(mode=mode,model_sha256=digest,portable_all_rows_match=True,rows=len(matrix),
            class_support={name:int((data.target==k).sum()) for k,name in enumerate('HAD')},
            training_sha256={**original,'fitted_matrix':semantic_digest(matrix)},
            parameters=dict(max_depth=4,min_samples_leaf=125,random_state=1729))
        if mode=='control' and digest!=expected_control_sha:raise ControlMismatch(model,receipt)
        if mode=='memory-ablated' and set(model['feature'])&{15,16,17}:raise ValueError('Candidate split on neutralized feature')
        results[mode]=dict(model=model,**receipt)
    if original!={name:semantic_digest(getattr(data,name)) for name in original}:raise ValueError('Fitting mutated source data')
    return results
