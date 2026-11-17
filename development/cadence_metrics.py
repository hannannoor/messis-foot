"""Post-inference aggregate diagnostics and prospective continuation checks."""
from math import isfinite
from statistics import fmean
import numpy as np

from cadence_protocol import CONTROL,CANDIDATE,MATCHES,VARIANTS,case_keys
from accuracy_evidence import assert_public_report
from gap_solver import official_metrics as official
from gap_solver.temporal_metrics import metric_periods
from gap_solver.benchmark import evaluation_arrays


BINS=('short','medium','long','very_long')


def _duration_bin(length):
    return 'short' if length<=25 else 'medium' if length<=75 else 'long' if length<=250 else 'very_long'


def diagnostic_metrics(reference,prediction,periods,sidecars):
    gt,pred,period=[np.asarray(v) for v in (reference,prediction,periods)]
    if any(v.ndim!=1 for v in (gt,pred,period)) or len({len(gt),len(pred),len(period)})!=1:
        raise ValueError('Diagnostic arrays must have matching one-dimensional shapes')
    if not np.isin(gt,[0,1,2,3]).all() or not np.isin(pred,[0,1,2,3]).all() or not np.isin(period,[0,1,2]).all():
        raise ValueError('Invalid diagnostic codes')
    active=period>0
    gt=np.where(active,gt,3).astype(np.uint8)
    if (gt<3).any():
        mapped=metric_periods(gt,period)
        a,b=evaluation_arrays(gt,pred,mapped)
    else:
        a=np.empty(0,dtype=np.uint8);b=np.empty(0,dtype=np.uint8)
    runs=official.valid_runs(a);filled=official.fill_abstentions(b,runs)
    actual=official.possession_spells(a,runs);estimated=official.possession_spells(filled,runs)
    overlaps=official.spell_overlaps(actual,estimated)
    durations={name:dict(n_gt=0,per_iou={str(t):dict(n_matched=0,recall=None) for t in official.SPELL_IOUS}) for name in BINS}
    for first,stop,_ in actual:durations[_duration_bin(stop-first)]['n_gt']+=1
    for threshold in official.SPELL_IOUS:
        flags=official.matched_gt_flags(overlaps,len(actual),threshold)
        for flag,(first,stop,_) in zip(flags,actual):
            durations[_duration_bin(stop-first)]['per_iou'][str(threshold)]['n_matched']+=int(flag)
        for row in durations.values():
            row['per_iou'][str(threshold)]['recall']=row['per_iou'][str(threshold)]['n_matched']/row['n_gt'] if row['n_gt'] else None
    boundaries={}
    for tolerance in (12,25):
        counts=dict(n_gt=0,n_pred=0,n_matched=0,n_missed=0,n_spurious=0,n_ambiguous=0);latencies=[]
        for run in runs:
            true=[t for t in official.transitions(a,[run]) if t[1] in (0,1) and t[2] in (0,1)]
            guessed=[t for t in official.transitions(filled,[run]) if t[1] in (0,1) and t[2] in (0,1)]
            row=official.transition_scores(true,guessed,tolerance,typed='pair')
            for name in counts:counts[name]+=row[name]
            latencies.extend(p[0]-g[0] for g,p in row['pairs'])
        tp=counts['n_matched'];ng=counts['n_gt'];npred=counts['n_pred']
        counts.update(precision=tp/npred if npred else 0.,recall=tp/ng if ng else 0.,
            f1=2*tp/(ng+npred) if ng+npred else 0.,
            mean_latency_frames=fmean(latencies) if latencies else None,
            mean_abs_latency_frames=fmean(abs(x) for x in latencies) if latencies else None,
            matched_latency_denominator=len(latencies))
        boundaries[str(tolerance)]=counts
    observation=dict(active_rows=int(active.sum()),observed_ball_rows=0,velocity_available_rows=0,
        velocity_unavailable_rows=int(active.sum()),repaired_rows=0,rolling_window_changed_rows=0,
        time_basis={name:0 for name in ('source','canonical_grid','invalid_source','none')},
        pair_duration_bins={name:0 for name in ('up_to_08','08_to_12','12_to_20','unavailable')})
    if sidecars:
        if len(sidecars)!=len(gt):raise ValueError('Sidecar dimensions differ')
        for row,is_active in zip(sidecars,active):
            if not is_active:continue
            observation['observed_ball_rows']+=int(row.legacy[0]>0)
            observation['velocity_available_rows']+=int(row.velocity_valid)
            observation['repaired_rows']+=int(row.repaired)
            observation['rolling_window_changed_rows']+=int(row.legacy[10]!=row.candidate[10])
            observation['time_basis'][row.time_basis]+=1
            dt=row.pair_dt_s
            name='unavailable' if dt is None else 'up_to_08' if dt<=.08+1e-9 else '08_to_12' if dt<=.12+1e-9 else '12_to_20'
            observation['pair_duration_bins'][name]+=1
        observation['velocity_unavailable_rows']-=observation['velocity_available_rows']
    live=gt<2
    result=dict(spell_duration=durations,HA_boundaries=boundaries,observation=observation,
        live_team=dict(known_live_rows=int(live.sum()),H_to_A=int(((gt==0)&(pred==1)).sum()),
            A_to_H=int(((gt==1)&(pred==0)).sum()),false_D=int((live&(pred==2)).sum()),
            undecided=int((live&(pred==3)).sum())))
    assert_public_report(result)
    return result


def _metric(row,name,section,field):
    value=row['variants'][name][section][field]
    if value is None:return None
    if isinstance(value,bool) or not isinstance(value,(int,float,np.integer,np.floating)) or not isfinite(value) or not 0<=value<=1:
        raise ValueError('Invalid bounded acceptance metric')
    return float(value)


def assess_continuation(receipts):
    keys=[(r['cohort'],str(r['match']),r['regime']) for r in receipts]
    if len(keys)!=20 or len(set(keys))!=20 or set(keys)!=set(case_keys()):
        raise ValueError('Continuation requires all twenty exact cases')
    if any(set(r['variants'])!=set(VARIANTS) for r in receipts):raise ValueError('Incomplete variant inventory')
    for row in receipts:
        for name in (CONTROL,CANDIDATE):
            for field in ('accuracy','spell_f1_mean'):_metric(row,name,'metrics',field)
            _metric(row,name,'dead_metrics','recall')
            dead=row['variants'][name]['dead_metrics']
            if any(type(dead[k]) is not int or dead[k]<0 for k in ('n_live','n_dead','false_D')) or dead['false_D']>dead['n_live']:
                raise ValueError('Invalid dead/live support counts')
    def rows_for(cohort,match,regime):
        return [r for r in receipts if r['cohort']==cohort and str(r['match'])==match and
                (r['regime'].startswith('retain-') if regime=='cadence' else r['regime']==regime)]
    def optional_mean(values):
        values=list(values)
        return None if not values or any(v is None for v in values) else fmean(values)
    def value(row,name,kind):
        if kind=='recall':
            return _metric(row,name,'dead_metrics','recall') if row['variants'][name]['dead_metrics']['n_dead']>0 else None
        if kind=='false_D_rate':
            d=row['variants'][name]['dead_metrics'];return d['false_D']/d['n_live'] if d['n_live'] else None
        return _metric(row,name,'metrics',kind)
    def match_mean(cohort,match,regime,name,kind):
        return optional_mean(value(r,name,kind) for r in rows_for(cohort,match,regime))
    def provider_mean(cohort,regime,name,kind):
        return optional_mean(match_mean(c,m,regime,name,kind) for c,m in MATCHES if c==cohort)
    def balanced(regime,name,kind):
        return optional_mean(provider_mean(c,regime,name,kind) for c in ('dfl','skillcorner'))
    comparisons={
        'natural_spell_preserved':('natural','spell_f1_mean','balanced','preserve'),
        'natural_accuracy_preserved':('natural','accuracy','balanced','preserve'),
        'natural_dfl_D_recall_preserved':('natural','recall','dfl','preserve'),
        'cadence_spell_improved':('cadence','spell_f1_mean','balanced','improve'),
        'cadence_false_D_reduced':('cadence','false_D_rate','balanced','reduce'),
        'masked_spell_preserved':('mask30-seed1729','spell_f1_mean','balanced','preserve'),
        'masked_dfl_D_recall_preserved':('mask30-seed1729','recall','dfl','preserve'),
    }
    checks={};values={}
    for key,(regime,kind,scope,operation) in comparisons.items():
        def mean(name):return balanced(regime,name,kind) if scope=='balanced' else provider_mean('dfl',regime,name,kind)
        old,new=mean(CONTROL),mean(CANDIDATE)
        checks[key]=bool(old is not None and new is not None and (new>=old if operation=='preserve' else new>old if operation=='improve' else new<old))
        values[key]=dict(control=old,candidate=new,delta=None if old is None or new is None else new-old)
    losses=[]
    for cohort,match in MATCHES:
        for regime in ('natural','cadence'):
            old=match_mean(cohort,match,regime,CONTROL,'spell_f1_mean');new=match_mean(cohort,match,regime,CANDIDATE,'spell_f1_mean')
            if old is not None and new is not None and new<old:
                losses.append(dict(cohort=cohort,match=match,regime=regime,metric='spell_f1_mean',delta=new-old))
        if cohort=='dfl':
            for row in [r for r in receipts if r['cohort']==cohort and str(r['match'])==match]:
                old,new=value(row,CONTROL,'recall'),value(row,CANDIDATE,'recall')
                if old is not None and new is not None and new<old:
                    losses.append(dict(cohort=cohort,match=match,regime=row['regime'],metric='D_recall',delta=new-old))
    result=dict(checks=checks,values=values,aggregate_gate_passed=all(checks.values()),
        per_match_review_required=bool(losses),automatic_continuation_allowed=all(checks.values()) and not losses,
        cases=losses,fresh_holdout=False,target_accuracy_measured=False)
    assert_public_report(result)
    return result
