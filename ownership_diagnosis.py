"""Input-only reconstruction and reference-conditioned used-data diagnostics."""
from dataclasses import dataclass
import hashlib
from math import isclose
import struct
import numpy as np

from ball_gap_policy import decode_ball_gap
from gap_solver import official_metrics as official
from gap_solver.benchmark import evaluation_arrays
from gap_solver.materialization_control import materialize_abstentions
from gap_solver.soft_sequence import sequence_usable,soft_emissions
from gap_solver.tactical import feature_rows,PortableTree
from gap_solver.tactical_model import FROZEN_MODEL
from gap_solver.temporal_metrics import metric_periods
from cadence_metrics import diagnostic_metrics
from ownership_paths import path_tables,state_summary,patch_summary,ABS_TOL,REL_TOL

FAMILIES=('missed_D','false_D','ownership_swap')


@dataclass(frozen=True)
class InferenceTrace:
    emissions: tuple
    periods: tuple
    observed: tuple
    usable: tuple
    latent: tuple
    final: tuple
    raw_codes: tuple
    memory_owner: tuple
    memory_age: tuple
    segments: tuple
    policy_counts: dict


def _blocks(mask,periods):
    i=0
    while i<len(mask):
        if not mask[i] or not periods[i]:i+=1;continue
        first=i;period=periods[i]
        while i<len(mask) and mask[i] and periods[i]==period:i+=1
        yield first,i


def prepare_inference(frames):
    frames=list(frames)
    if not frames or any(f.dead_evidence or f.dead_source or f.tag_team or f.restart_hint for f in frames):
        raise ValueError('Nonempty geometry-only frames required')
    tree=PortableTree(FROZEN_MODEL['model']);supports=[];memory=[];ages=[]
    for row in feature_rows(frames):
        supports.append(tree.predict(row));memory.append(0 if row[15]>.5 else 1 if row[16]>.5 else 3);ages.append(row[17])
    periods=tuple(int(f.period) for f in frames)
    observed=tuple(bool(f.ball_observed) for f in frames);usable=tuple(bool(sequence_usable(f)) for f in frames)
    latent,counts=decode_ball_gap(supports,periods,usable,observed)
    emissions=soft_emissions(supports,[0.]*len(frames),0.)
    emissions=tuple(row if seen else (0.,0.,0.) for row,seen in zip(emissions,observed))
    segments=tuple((a,b) for a,b in _blocks(usable,periods) if any(observed[a:b]))
    raw=tuple(max(range(3),key=lambda k:row[k]) for row in supports)
    return InferenceTrace(emissions,periods,observed,usable,tuple(latent),
                          tuple(materialize_abstentions(latent,periods)),raw,tuple(memory),tuple(ages),segments,counts)


def _codes(labels):
    return np.asarray(['HADX'.index(label) for label in labels],dtype=np.uint8)


def _arrays(reference,prediction,periods):
    gt,pred,period=(np.asarray(v) for v in (reference,prediction,periods))
    if (any(v.ndim!=1 for v in (gt,pred,period)) or not len(gt) or len({len(gt),len(pred),len(period)})!=1
            or gt.dtype.kind not in 'ui' or pred.dtype.kind not in 'ui'
            or not np.isin(gt,[0,1,2,3]).all() or not np.isin(pred,[0,1,2,3]).all()
            or not np.isin(period,[0,1,2]).all()):
        raise ValueError('Invalid diagnostic dimensions/codes')
    return np.where(period>0,gt,3).astype(np.uint8),pred.astype(np.uint8),period


def _evaluation(reference,prediction,periods):
    gt,pred,period=_arrays(reference,prediction,periods)
    if not (gt<3).any():return np.empty(0,dtype=np.uint8),np.empty(0,dtype=np.uint8)
    return evaluation_arrays(gt,pred,metric_periods(gt,period))


def spell_diagnosis(reference,prediction,periods):
    a,b=_evaluation(reference,prediction,periods)
    runs=official.valid_runs(a);filled=official.fill_abstentions(b,runs)
    actual=official.possession_spells(a,runs);estimated=official.possession_spells(filled,runs)
    overlaps=official.spell_overlaps(actual,estimated)
    by_gt=[[] for _ in actual];by_pred=[[] for _ in estimated]
    for iou,g,p in overlaps:by_gt[g].append((iou,p));by_pred[p].append((iou,g))
    table={};scores=[]
    def partition(neighbors,matched,threshold):
        result=dict(no_same_team_overlap=0,below_threshold_overlap=0,qualifying_consumed=0)
        for i,choices in enumerate(neighbors):
            if i in matched:continue
            key='no_same_team_overlap' if not choices else 'below_threshold_overlap' if max(v for v,_ in choices)<threshold else 'qualifying_consumed'
            result[key]+=1
        return result
    for threshold in official.SPELL_IOUS:
        mg=set();mp=set()
        for iou,g,p in overlaps:
            if iou<threshold:break
            if g not in mg and p not in mp:mg.add(g);mp.add(p)
        tp,fp,fn=official.match_spells(overlaps,len(actual),len(estimated),threshold)
        if (tp,fp,fn)!=(len(mg),len(estimated)-len(mp),len(actual)-len(mg)):
            raise ValueError('Official spell matching differs')
        score=(2.*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0.) if len(a) else None
        if score is not None:scores.append(score)
        table[str(threshold)]=dict(n_matched=tp,n_spurious=fp,n_missed=fn,f1=score,
            unmatched_gt=partition(by_gt,mg,threshold),unmatched_pred=partition(by_pred,mp,threshold))
    return dict(n_gt=len(actual),n_pred=len(estimated),split_reference_spells=sum(len(row)>1 for row in by_gt),
                merge_prediction_spells=sum(len(row)>1 for row in by_pred),
                per_iou=table,mean_f1=sum(scores)/len(scores) if scores else None)


def diagnostic_repairs(trace,reference):
    gt,pred,_=_arrays(reference,_codes(trace.final),trace.periods)
    latent=_codes(trace.latent);eligible=(gt<3)&(latent<3)&(pred!=gt)
    liveness=eligible&((gt==2)|(pred==2));ownership=eligible&(gt<2)&(pred<2)
    result={}
    for name,mask in (('supported_liveness_repair',liveness),('supported_ownership_repair',ownership)):
        repaired=pred.copy();repaired[mask]=gt[mask]
        result[name]=tuple('HADX'[int(value)] for value in repaired)
    return result


def _family(reference,prediction):
    return 'missed_D' if reference==2 else 'false_D' if prediction==2 else 'ownership_swap'


def _new_stats():return dict(n=0,total=0.,minimum=None,maximum=None,positive=0,negative=0,near_zero=0)


def _add_stat(stat,value):
    stat['n']+=1;stat['total']+=float(value)
    stat['minimum']=float(value) if stat['minimum'] is None else min(stat['minimum'],float(value))
    stat['maximum']=float(value) if stat['maximum'] is None else max(stat['maximum'],float(value))
    stat['positive']+=int(value>ABS_TOL);stat['negative']+=int(value < -ABS_TOL);stat['near_zero']+=int(abs(value)<=ABS_TOL)


def _baseline(gt,pred,periods):
    cm=official.confusion(gt,pred);known=int((gt<3).sum())
    spells=spell_diagnosis(gt,pred,periods)
    metrics=dict(accuracy=float(official.accuracy(cm[:3])) if known else None,
                 official_macro_f1=float(official.macro_f1(cm[:3])) if known else None,spell_f1_mean=spells['mean_f1'])
    return dict(metrics=metrics,spells=spells,confusion=cm.tolist())


def analyze_case(trace,reference,*,expected_parity=None,on_evaluation=None):
    gt,pred,periods=_arrays(reference,_codes(trace.final),trace.periods)
    n=len(gt)
    if any(len(value)!=n for value in (trace.emissions,trace.observed,trace.usable,trace.latent,trace.raw_codes,trace.memory_owner,trace.memory_age)):
        raise ValueError('Trace dimensions differ')
    latent=_codes(trace.latent);known=gt<3;live=gt<2;observed=np.asarray(trace.observed);usable=np.asarray(trace.usable)
    error=known&(pred!=gt);supported=known&(latent<3);carried=known&(latent==3)
    if np.any((latent<3)&(latent!=pred)):
        raise ValueError('Supported labels changed during materialization')
    memory=np.asarray(trace.memory_owner);raw=np.asarray(trace.raw_codes)
    measured=live&observed&usable
    pilot=dict(frames=int(live.sum()),wrong_team=int((live&(pred<2)&(pred!=gt)).sum()),
               raw_correct_final_wrong=int((measured&(raw==gt)&(pred!=gt)).sum()),
               raw_wrong_final_correct=int((measured&(raw!=gt)&(pred==gt)).sum()))
    if on_evaluation:on_evaluation('baseline_metric')
    baseline=_baseline(gt,pred,periods)
    if expected_parity is not None:
        if set(expected_parity)=={'pilot'}:
            actual=pilot
        elif set(expected_parity)=={'wcsf'}:
            spells=baseline['spells'];half=spells['per_iou']['0.5']
            actual=dict(frames=n,known=int(known.sum()),n_gt=spells['n_gt'],n_pred=spells['n_pred'],
                        **{key:half[key] for key in ('n_matched','n_missed','n_spurious')})
        else:raise ValueError('Unknown baseline parity contract')
        if actual!=next(iter(expected_parity.values())):raise ValueError('Prior baseline parity failed')
    families={name:dict(frames=0,episodes=0,objective_classes={key:dict(episodes=0,frames=0) for key in
                    ('wrong_emission_preference','switch_penalty_blocks_reference','numerical_tie','mixed_or_nonlocal')},
                    margins={key:_new_stats() for key in ('prefix_before','local','future','full','emission_margin','switch_margin')},
                    local_reference_favoring_frames=0,local_wrong_favoring_frames=0,future_reversal_frames=0,
                    patch_emission_gain=0.,patch_additional_switches=0,patch_objective_gain=0.) for name in FAMILIES}
    lengths={name:[] for name in FAMILIES};agreement={name:dict(frames=0,full_margin=_new_stats()) for name in 'HAD'}
    fingerprint=hashlib.sha256(b'ownership-input-paths-v1\n');exact_ties=0;checked=0
    for first,stop in trace.segments:
        table=path_tables(trace.emissions[first:stop]);selected=trace.latent[first:stop]
        if table.labels!=selected:raise ValueError('Instrument labels differ from frozen decoder')
        original=sum(row['HAD'.index(label)] for row,label in zip(table.emissions,selected))-32*sum(a!=b for a,b in zip(selected,selected[1:]))
        if not isclose(original,table.score,abs_tol=ABS_TOL,rel_tol=REL_TOL):raise ValueError('Instrument objective differs')
        fingerprint.update(struct.pack('<qq',first,stop));fingerprint.update(''.join(table.labels).encode('ascii'))
        for rows in (table.forward,table.backward):
            for row in rows:fingerprint.update(struct.pack('<ddd',*row))
        exact_ties+=table.exact_ties;checked+=stop-first
        for index in range(first,stop):
            if not known[index]:continue
            r=int(gt[index]);p=int(latent[index]);at=index-first
            if r==p:
                other=1-r if r<2 else max((0,1),key=lambda k:table.forward[at][k]+table.backward[at][k])
                query=state_summary(table,at,r,other);row=agreement['HAD'[r]]
                row['frames']+=1;_add_stat(row['full_margin'],query['full']);continue
            query=state_summary(table,at,r,p)
            if query['full'] < -(ABS_TOL+REL_TOL*max(abs(query['reference_score']),abs(query['comparison_score']))):
                raise ValueError('Selected state is not a constrained optimum')
            row=families[_family(r,p)];row['frames']+=1
            for key,stat in row['margins'].items():_add_stat(stat,query[key])
            row['local_reference_favoring_frames']+=int(query['local'] < -ABS_TOL)
            row['local_wrong_favoring_frames']+=int(query['local']>ABS_TOL)
            row['future_reversal_frames']+=int(query['prefix'] < -ABS_TOL and query['full']>ABS_TOL)
        i=first
        while i<stop:
            if not known[i] or latent[i]==gt[i]:i+=1;continue
            start=i;r=int(gt[i]);p=int(latent[i]);i+=1
            while i<stop and known[i] and gt[i]==r and latent[i]==p:i+=1
            patch=patch_summary(table.emissions,table.labels,start-first,i-first,r)
            if patch['objective_gain']>ABS_TOL+REL_TOL*abs(table.score):raise ValueError('Reference patch improves the optimum')
            row=families[_family(r,p)];row['episodes']+=1;lengths[_family(r,p)].append(i-start)
            category=('numerical_tie' if abs(patch['objective_gain'])<=ABS_TOL else
                      'wrong_emission_preference' if patch['emission_gain'] < -ABS_TOL else
                      'switch_penalty_blocks_reference' if patch['emission_gain']>ABS_TOL and patch['additional_switches']>0 else 'mixed_or_nonlocal')
            row['objective_classes'][category]['episodes']+=1;row['objective_classes'][category]['frames']+=i-start
            row['patch_emission_gain']+=patch['emission_gain'];row['patch_additional_switches']+=patch['additional_switches'];row['patch_objective_gain']+=patch['objective_gain']
    if checked!=int((latent<3).sum()):raise ValueError('Supported segment coverage differs')
    for name,row in families.items():
        values=lengths[name]
        row['duration']=dict(median_s=float(np.median(values)/25) if values else None,
            p90_s=float(np.quantile(values,.9)/25) if values else None,max_s=max(values)/25 if values else None,
            frames_in_episodes_at_least2s=sum(value for value in values if value>=50))
        if sum(value['frames'] for value in row['objective_classes'].values())!=row['frames']:raise ValueError('Episode/frame counts differ')
    near=np.zeros(n,dtype=bool);edges=np.zeros(n,dtype=bool)
    for a,b in _blocks(known,periods):
        edges[a:min(b,a+50)]=True;edges[max(a,b-50):b]=True
        for index in np.flatnonzero(gt[a+1:b]!=gt[a:b-1])+a+1:near[max(a,index-50):min(b,index+51)]=True
    def stratum(mask):
        at=known&mask;wrong=at&error
        return dict(frames=int(at.sum()),known_live_frames=int((at&live).sum()),supported_errors=int((wrong&supported).sum()),
                    carried_errors=int((wrong&carried).sum()),ownership_swaps=int((at&live&(pred<2)&(pred!=gt)).sum()),
                    wrong_with_opposed_memory=int((wrong&(memory<2)&(memory!=gt)).sum()))
    counterfactuals={}
    for name,labels in diagnostic_repairs(trace,gt).items():
        if on_evaluation:on_evaluation(name)
        estimate=_codes(labels);evaluated=_baseline(gt,estimate,periods)
        old=baseline['spells']['mean_f1'];new=evaluated['spells']['mean_f1']
        counterfactuals[name]=dict(diagnostic_only=True,changed_rows=int((estimate!=pred).sum()),
            spell_f1_delta=new-old if old is not None and new is not None else None,
            metrics=evaluated['metrics'],spells=evaluated['spells'])
    return dict(schema_version=1,support=dict(frames=n,known=int(known.sum()),unknown=n-int(known.sum()),
                   **{name:int((gt==k).sum()) for k,name in enumerate('HAD')}),
        input_segments=len(trace.segments),input_path_sha256=fingerprint.hexdigest(),exact_recurrence_ties=exact_ties,
        supported_error_frames=int((error&supported).sum()),carried_known_frames=int(carried.sum()),carried_error_frames=int((error&carried).sum()),
        families=families,agreement=agreement,baseline=baseline,counterfactuals=counterfactuals,pilot_parity=pilot,
        HA_boundaries=diagnostic_metrics(gt,pred,periods,[])['HA_boundaries'],policy_counts=trace.policy_counts,
        strata=dict(all_known=stratum(np.ones(n,dtype=bool)),ball_observed=stratum(observed),ball_missing=stratum(~observed),
                    near_boundary_2s=stratum(near),near_annotation_edge_2s=stratum(edges),
                    observed_interior_beyond2s=stratum(observed&~near&~edges)))
