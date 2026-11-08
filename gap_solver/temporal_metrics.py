"""Gap-aware external diagnostics; provider reference holes never become inference inputs."""
from collections import Counter
import numpy as np

from . import official_metrics as official
from .benchmark import evaluate_external,compare_external
from .core import infer


def _codes(values):
    array=np.asarray(values)
    if array.ndim!=1 or not np.isin(array,[0,1,2,3]).all():raise ValueError('invalid temporal label code')
    return array.astype(np.uint8)


def metric_periods(reference,periods):
    gt=np.asarray(reference);period=np.asarray(periods)
    if gt.ndim!=1 or period.ndim!=1 or len(gt)!=len(period) or not len(gt):
        raise ValueError('temporal reference/period dimensions disagree')
    if not np.isin(period,[0,1,2]).all() or not np.isin(gt,[0,1,2,3]).all():
        raise ValueError('invalid temporal reference/period code')
    if ((period==0)&(gt!=3)).any():raise ValueError('reference cannot label structurally unknown periods')
    active=np.flatnonzero(period)
    if not len(active):raise ValueError('no structurally supported period')
    # Preserve original unknown rows. Only supply a bookkeeping period to the
    # unchanged scorer; GT X still splits every unknown region into valid runs.
    result=period.copy();current=period[active[0]]
    for i,value in enumerate(period):
        if value:current=value
        else:result[i]=current
    return result.astype(np.uint8)


def score_temporal(reference,prediction,periods):
    gt=_codes(reference);pred=_codes(prediction)
    mapped=metric_periods(gt,periods)
    report=evaluate_external(gt,pred,mapped)
    report['scope']=dict(canonical_frames=len(gt),structural_period_frames=int((np.asarray(periods)>0).sum()),
        unknown_annotation_frames_within_period=int(((np.asarray(periods)>0)&(gt==3)).sum()),
        reference_contract='known in-play provider team reference; outside annotation remains unknown')
    confusion=np.asarray(report['metrics']['confusion'])
    values=[]
    for code in (0,1):
        tp=int(confusion[code,code]);denominator=int(confusion[code].sum()+confusion[:,code].sum())
        values.append(2*tp/denominator if denominator else 0.)
    report['known_team_macro_f1']=float(np.mean(values))
    runs=official.valid_runs(gt)
    filled=official.fill_abstentions(pred,runs)
    transitions=official.transitions(filled,runs)
    switches=sum(a<2 and b<2 for _,a,b in transitions)
    minutes=int((gt<2).sum())/25/60
    report['predicted_team_switches_per_known_live_minute']=switches/minutes if minutes else None
    return report


def missing_intervals(frames):
    result=[];i=0
    while i<len(frames):
        if not frames[i].period or frames[i].ball_observed:i+=1;continue
        first=i;period=frames[i].period
        while i<len(frames) and frames[i].period==period and not frames[i].ball_observed:i+=1
        result.append((first,i))
    return result


def duration_bucket(seconds):
    return next((name for upper,name in ((.2,'<=0.2s'),(.6,'0.2-0.6s'),(2,'0.6-2s'),(5,'2-5s'),(10,'5-10s'))
                 if seconds<=upper),'over10s')


def native_gap_statistics(data):
    available=np.asarray(data.native_ball_available,dtype=bool);periods=np.asarray(data.native_periods)
    if available.ndim!=1 or periods.shape!=available.shape:raise ValueError('native availability arrays disagree')
    missing=(~available)&(periods>0);intervals=0;buckets=Counter();i=0
    fps=float(data.notes['native_fps'])
    while i<len(missing):
        if not missing[i]:i+=1;continue
        first=i;period=periods[i]
        while i<len(missing) and missing[i] and periods[i]==period:i+=1
        intervals+=1;buckets[duration_bucket((i-first)/fps)]+=i-first
    return dict(native_fps=fps,native_rows=len(available),missing_native_frames=int(missing.sum()),
                missing_native_intervals=intervals,missing_native_seconds=float(missing.sum()/fps),
                missing_native_frames_by_duration=dict(buckets))


def hidden_opponent_scores(reference,before,after,frames):
    gt=np.asarray(reference,dtype=np.uint8);runs=official.valid_runs(gt)
    all_truth=official.possession_spells(gt,runs)
    anchors=infer(frames)
    predicted=[official.possession_spells(_codes(p),runs)
               for p in (before,after)]
    short=[];all_opponents=[];opposing_predictions=[{},{}];same_endpoint_gaps=0
    for first,stop in missing_intervals(frames):
        if first==0 or stop==len(frames) or frames[first-1].period!=frames[first].period or frames[stop].period!=frames[first].period:continue
        owner=anchors[first-1].label
        if owner not in ('H','A') or anchors[stop].label!=owner:continue
        code='HA'.index(owner)
        if gt[first-1]!=code or gt[stop]!=code:continue
        same_endpoint_gaps+=1
        for spell in all_truth:
            a,b,label=spell
            if label==1-code and first<=a<b<=stop:
                all_opponents.append(spell)
                if .2<=(b-a)/25<=2.:short.append(spell)
        for j,spells in enumerate(predicted):
            for index,spell in enumerate(spells):
                a,b,label=spell
                if label==1-code and a<stop and b>first:opposing_predictions[j][index]=spell
    short=list(dict.fromkeys(short));all_opponents=list(dict.fromkeys(all_opponents))
    result=dict(reference_short_spells=len(short),same_team_endpoint_gaps=same_endpoint_gaps,mechanism_uses_raw_spans=True,
                short_definition='0.2-2s, wholly inside missing-ball interval; both credible endpoints are opposite team; IoU>=0.5')
    for name,spells in zip(('baseline','selected'),opposing_predictions):
        candidates=list(spells.values())
        matches=official.match_spells(official.spell_overlaps(short,candidates),len(short),len(candidates),.5)
        _,false,_=official.match_spells(official.spell_overlaps(all_opponents,candidates),len(all_opponents),len(candidates),.5)
        result[name+'_hits']=matches[0]
        result[name+'_recall']=matches[0]/len(short) if short else None
        result[name+'_false_opposing_spells']=false
    return result


def gap_strata(frames,reference,before,after):
    gt=np.asarray(reference);old=np.asarray(before);new=np.asarray(after);buckets={}
    gap_agreement=[];labels={name:dict(frames=0,correct=0,gaps=0) for name in ('H','A')}
    for first,stop in missing_intervals(frames):
        bucket=duration_bucket((stop-first)/25)
        record=buckets.setdefault(bucket,dict(intervals=0,frames=0,known_reference_frames=0,
            newly_assigned_frames=0,newly_assigned_correct=0,native_ball_samples=0))
        record['intervals']+=1;record['frames']+=stop-first
        known=gt[first:stop]<3;assigned=known&(old[first:stop]==3)&(new[first:stop]<2)
        correct=assigned&(gt[first:stop]==new[first:stop])
        record['known_reference_frames']+=int(known.sum())
        record['newly_assigned_frames']+=int(assigned.sum());record['newly_assigned_correct']+=int(correct.sum())
        record['native_ball_samples']+=sum(getattr(f,'ball_native_observation',False) is True for f in frames[first:stop])
        for code,name in enumerate(('H','A')):
            selected=assigned&(new[first:stop]==code)
            labels[name]['frames']+=int(selected.sum());labels[name]['correct']+=int((selected&(gt[first:stop]==code)).sum())
            labels[name]['gaps']+=int(selected.any())
        if assigned.any():gap_agreement.append(float(correct.sum()/assigned.sum()))
    return dict(by_duration=buckets,newly_assigned_gap_macro_agreement=float(np.mean(gap_agreement)) if gap_agreement else None,
                newly_assigned_gaps=len(gap_agreement),per_label=labels)


def compare_temporal(reference,before,after,periods,frames):
    gt=_codes(reference);old=_codes(before);new=_codes(after)
    if len(frames)!=len(gt):raise ValueError('temporal frame/reference dimensions disagree')
    mapped=metric_periods(gt,periods)
    change=compare_external(gt,old,new,mapped)
    unmeasured=(np.asarray(periods)>0)&(gt==3)&(old==3)&(new<2)
    return dict(baseline=score_temporal(gt,old,periods),selected=score_temporal(gt,new,periods),change=change,
        hidden_opponents=hidden_opponent_scores(gt,old,new,frames),gap_strata=gap_strata(frames,gt,old,new),
        unmeasured_new_ha_outside_reference=int(unmeasured.sum()),
        warning='Known-reference team agreement only; assignments outside support have unmeasured correctness.')
