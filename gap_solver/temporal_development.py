"""External experiment helpers. Reference labels are absent from feature/inference APIs."""
import numpy as np
from .core import Decision
from .tactical import infer_tactical,Policy
from .tactical_model import FROZEN_MODEL
from .temporal import (MOTION_FEATURES,motion_feature_rows,mask_motion_frames,anchor_context,
    swap_feature_row,reflect_feature_row,apply_temporal_policy,TemporalPolicy)
from .temporal_selection import contiguous_mask


def codes(decisions):return np.fromiter(('HADX'.index(d.label) for d in decisions),dtype=np.uint8,count=len(decisions))
def decisions(values):return [Decision('HADX'[int(v)]) for v in values]


def feature_cases(frames,seed):
    result={}
    periods=np.asarray([f.period for f in frames])
    mask=contiguous_mask(periods,.3,seed)
    for name,case in (('natural',frames),('masked',mask_motion_frames(frames,mask))):
        result[name]=dict(x=np.asarray(list(motion_feature_rows(case)),dtype=np.float32),
            baseline=codes(infer_tactical(case,FROZEN_MODEL['model'],Policy(**FROZEN_MODEL['policy']))),
            mask=np.zeros(len(frames),dtype=bool) if name=='natural' else mask)
    return result


def training_sample(x,reference,baseline,offset=0,stride=5):
    x=np.asarray(x,dtype=np.float32);gt=np.asarray(reference);old=np.asarray(baseline)
    if x.shape!=(len(gt),len(MOTION_FEATURES)) or old.shape!=gt.shape:raise ValueError('external training dimensions disagree')
    rows=np.flatnonzero((gt<2)&(old==3)&((np.arange(len(gt))-offset)%stride==0))
    if not len(rows):raise ValueError('empty external training case')
    values=x[rows];target=gt[rows].astype(np.uint8)
    swapped=np.asarray([swap_feature_row(r) for r in values],dtype=np.float32)
    reflected=np.asarray([reflect_feature_row(r) for r in values],dtype=np.float32)
    both=np.asarray([reflect_feature_row(r) for r in swapped],dtype=np.float32)
    return np.concatenate((values,swapped,reflected,both)),np.concatenate((target,1-target,target,1-target)),np.full(4*len(rows),1/(4*len(rows)))


def ensemble_scores(model,x):
    """Vectorized portable-tree evaluation, using the exact runtime float32 input."""
    x=np.asarray(x,dtype=np.float32)
    if x.ndim!=2 or x.shape[1]!=len(MOTION_FEATURES) or not np.isfinite(x).all():raise ValueError('invalid ensemble input')
    result=np.full(len(x),model['initial_log_odds'],dtype=np.float64)
    for tree in model['trees']:
        nodes=np.zeros(len(x),dtype=np.int32)
        left=np.asarray(tree['children_left']);right=np.asarray(tree['children_right'])
        feature=np.asarray(tree['feature']);threshold=np.asarray(tree['threshold']);value=np.asarray(tree['value'])
        while True:
            active=np.flatnonzero(left[nodes]!=-1)
            if not len(active):break
            at=nodes[active]
            nodes[active]=np.where(x[active,feature[at]]<=threshold[at],left[at],right[at])
        result+=model['learning_rate']*value[nodes]
    return result


def symmetric_scores(model,x):
    swapped=np.asarray([swap_feature_row(row) for row in x],dtype=np.float32)
    return (ensemble_scores(model,x)-ensemble_scores(model,swapped))/2


def endpoint_predictions(frames,baseline,proposal,max_gap_s,mode='two_sided'):
    """Choose only from input evidence; match proposal's added-frame count without GT.

    Rank eligible frames by shorter anchor gap then nearest observed endpoint. The
    comparator may use different rows from the model; report reference coverage too.
    """
    n=len(frames);context=anchor_context(frames);left,right,owners=context
    eligible=apply_temporal_policy(frames,baseline,[-50.]*n,
        TemporalPolicy(confidence=.9,max_gap_s=max_gap_s),context)
    wanted=sum(b.label=='X' and p.label in ('H','A') for b,p in zip(baseline,proposal))
    candidates=[i for i,(a,b) in enumerate(zip(baseline,eligible)) if a.label=='X' and b.label!='X']
    candidates.sort(key=lambda i:(right[i]-left[i],min(i-left[i],right[i]-i),i))
    if len(candidates)<wanted:raise ValueError('comparator cannot match candidate input coverage')
    result=list(baseline)
    for i in candidates[:wanted]:
        a,b=left[i],right[i]
        owner=owners[a] if mode=='last_owner' or i-a<=b-i else owners[b]
        result[i]=Decision('H' if owner<0 else 'A','endpoint_comparator','external_comparison')
    return result,dict(matched_added_count=wanted,eligible_input_frames=len(candidates),
        matching='same total added input-frame count; reference labels never used for ranking')
