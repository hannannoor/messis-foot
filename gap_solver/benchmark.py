"""External provider-reference evaluation with unchanged official metric functions."""
import numpy as np
from . import official_metrics


def _validate(reference,prediction,periods):
    arrays=[np.asarray(x) for x in (reference,prediction,periods)]
    if any(a.ndim!=1 for a in arrays) or not len(arrays[0]) or len({len(a) for a in arrays})!=1:
        raise ValueError('external metric inputs need nonempty matching one-dimensional arrays')
    gt,pred,period=arrays
    if not np.isin(gt,[0,1,2,3]).all() or not np.isin(pred,[0,1,2,3]).all() or not np.isin(period,[1,2]).all():
        raise ValueError('invalid external reference, prediction or period code')
    if not (gt<3).any():
        raise ValueError('external reference has no scored support')
    chunks=period[np.r_[True,period[1:]!=period[:-1]]]
    if len(set(chunks.tolist()))!=len(chunks):
        raise ValueError('external periods cannot reappear after a reset')
    return gt.astype(np.uint8),pred.astype(np.uint8),period.astype(np.uint8)


def evaluation_arrays(reference,prediction,periods):
    gt,pred,period=_validate(reference,prediction,periods)
    starts=np.r_[0,np.flatnonzero(period[1:]!=period[:-1])+1,len(period)]
    a=[];b=[]
    separator=np.full(max(official_metrics.TAUS)+1,3,dtype=np.uint8)
    for index,(first,stop) in enumerate(zip(starts,starts[1:])):
        if index:
            a.append(separator);b.append(separator)
        a.append(gt[first:stop]);b.append(pred[first:stop])
    return np.concatenate(a),np.concatenate(b)


def evaluate_external(reference,prediction,periods):
    gt,pred,period=_validate(reference,prediction,periods)
    scored=gt<3
    a,b=evaluation_arrays(gt,pred,period)
    result=official_metrics.evaluate(a,b,bootstrap_n=0)
    n=int(scored.sum());x=int(((pred==3)&scored).sum())
    decided=scored&(pred<3)
    return dict(reference_type='external provider reference; not challenge accuracy',metrics=result,
                coverage=dict(original_frames=len(gt),graded_frames=n,undecided_frames=x,undecided_fraction=x/n,
                              decided_correct_fraction=float((gt[decided]==pred[decided]).mean()) if decided.any() else None),
                evaluation_only_separator_frames=len(a)-len(gt))


def compare_external(reference,before,after,periods):
    gt,old,period=_validate(reference,before,periods)
    _,new,_=_validate(reference,after,periods)
    scored=gt<3
    assigned=scored&(old==3)&(new<3)
    support=int(assigned.sum())
    labels={}
    for code,name in enumerate('HAD'):
        mask=assigned&(new==code)
        count=int(mask.sum())
        labels[name]=dict(frames=count,correct_fraction=float((gt[mask]==new[mask]).mean()) if count else None)
    padded_gt,padded_old=evaluation_arrays(gt,old,period)
    _,padded_new=evaluation_arrays(gt,new,period)
    runs=official_metrics.valid_runs(padded_gt)
    expanded_old=official_metrics.fill_abstentions(padded_old,runs)
    expanded_new=official_metrics.fill_abstentions(padded_new,runs)
    starts=assigned&np.r_[True,(~assigned[:-1])|(period[1:]!=period[:-1])]
    changed_decided=scored&(old<3)&(new!=old)
    return dict(newly_resolved_frames=support,newly_resolved_intervals=int(starts.sum()),
                newly_resolved_correct_fraction=float((gt[assigned]==new[assigned]).mean()) if support else None,
                newly_resolved_by_label=labels,
                raw_label_changes=int((scored&(old!=new)).sum()),
                changed_already_decided_frames=int(changed_decided.sum()),
                already_decided_corrections=int((changed_decided&(old!=gt)&(new==gt)).sum()),
                already_decided_regressions=int((changed_decided&(old==gt)&(new!=gt)).sum()),
                reversions_to_undecided=int((scored&(old<3)&(new==3)).sum()),
                scorer_expanded_label_changes=int(((padded_gt<3)&(expanded_old!=expanded_new)).sum()),
                reference_type='external provider reference; not challenge accuracy')
