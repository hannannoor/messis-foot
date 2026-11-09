"""Prespecified aggregate scores and gates; no model or parameter selection."""
from math import fsum,isfinite
import numpy as np

from cadence_metrics import diagnostic_metrics
from ownership_diagnosis import _arrays,_evaluation,_baseline,_all_state_boundaries
from gap_solver import official_metrics as official

SC=('1874553','1886347','2007448','2007721','2010085','2011166','2013725','2015213','2016236','2017461')
MATCHES=tuple(('skillcorner-'+m,'skillcorner','fit-disjoint') for m in SC)+(
    ('dfl-J03WR9','dfl','fit-disjoint'),('dfl-J03WN1','dfl','fit-disjoint'),('wcsf-used-match','wcsf','fit-disjoint'),
    ('dfl-J03WOH','dfl','fitting-overlap'),('dfl-J03WOY','dfl','fitting-overlap'))
REGIMES=('natural','mask30-seed1729')
MODES=('control','memory-ablated')
PROVIDERS=('skillcorner','dfl','wcsf')
EPS=1e-6


def score_variant(reference,prediction,periods,observed):
    gt,pred,period=_arrays(reference,prediction,periods);seen=np.asarray(observed)
    if seen.dtype!=bool or seen.shape!=gt.shape:raise ValueError('Explicit observed flags required')
    known=gt<3;live=gt<2;baseline=_baseline(gt,pred,period)
    a,b=_evaluation(gt,pred,period);runs=official.valid_runs(a);filled=official.fill_abstentions(b,runs)
    actual=official.possession_spells(a,runs);estimated=official.possession_spells(filled,runs)
    flags=official.matched_gt_flags(official.spell_overlaps(actual,estimated),len(actual),.5)
    short=[bool(stop-first<=25) for first,stop,_ in actual]
    ns=sum(short);matched=sum(bool(flag) and is_short for flag,is_short in zip(flags,short))
    nd=int((gt==2).sum());pd=int((known&(pred==2)).sum());tp=int(((gt==2)&(pred==2)).sum())
    def stratum(mask):
        at=known&mask
        return dict(known=int(at.sum()),correct=int((at&(gt==pred)).sum()),
            ownership_swaps=int((at&live&(pred<2)&(gt!=pred)).sum()),
            false_D=int((at&live&(pred==2)).sum()),missed_D=int((at&(gt==2)&(pred!=2)).sum()))
    return dict(schema_version=1,support=dict(frames=len(gt),known=int(known.sum()),unknown=int((~known).sum()),
                    **{name:int((gt==k).sum()) for k,name in enumerate('HAD')}),
        predicted_on_known={name:int((known&(pred==k)).sum()) for k,name in enumerate('HADX')},
        metrics=baseline['metrics'],spells=baseline['spells'],confusion=baseline['confusion'],
        dead=dict(n_gt=nd,n_pred=pd,n_matched=tp,precision=tp/pd if pd else None,recall=tp/nd if nd else None),
        known_live_false_D_rate=int((live&(pred==2)).sum())/int(live.sum()) if live.any() else None,
        short_spells=dict(n_gt=ns,n_matched=matched,recall=matched/ns if ns else None),
        all_state_boundaries=_all_state_boundaries(gt,pred,period),HA_boundaries=diagnostic_metrics(gt,pred,period,[])['HA_boundaries'],
        strata=dict(ball_observed=stratum(seen),ball_missing=stratum(~seen)))


def _number(value):
    if value is None:return None
    if type(value) not in (int,float) or not isfinite(value) or not 0<=value<=1:raise ValueError('Invalid bounded metric')
    return float(value)


def _mean(values):
    values=[_number(v) for v in values]
    return fsum(values)/len(values) if values and all(v is not None for v in values) else None


def _delta(candidate,control):
    candidate=_number(candidate);control=_number(control)
    return candidate-control if candidate is not None and control is not None else None


def _check(values,non_applicable=0):
    failed=sum(value is False for value in values);unsupported=sum(value is None for value in values)
    status='fail' if failed else 'unresolved' if unsupported else 'pass' if values else 'non_applicable'
    return dict(status=status,assessed=len(values)-unsupported,failures=failed,unsupported=unsupported,non_applicable=non_applicable)


def summarize_cases(case_receipts):
    rows=list(case_receipts);expected={(cid,regime):(provider,role) for cid,provider,role in MATCHES for regime in REGIMES};seen={}
    for row in rows:
        key=(row['case_id'],row['regime'])
        if key in seen or key not in expected or (row['cohort'],row['role'])!=expected[key] or set(row['variants'])!=set(MODES):
            raise ValueError('Duplicate/unknown case, role or variant')
        seen[key]=row
    if set(seen)!=set(expected):raise ValueError('Exact thirty paired cases required')
    provider_means={};primary={};case_deltas={}
    for regime in REGIMES:
        provider_means[regime]={mode:{provider:_mean([row['variants'][mode]['metrics']['spell_f1_mean']
            for row in rows if row['regime']==regime and row['cohort']==provider and row['role']=='fit-disjoint'])
            for provider in PROVIDERS} for mode in MODES}
        primary[regime]={mode:_mean(provider_means[regime][mode].values()) for mode in MODES}
        primary[regime]['delta']=_delta(primary[regime]['memory-ablated'],primary[regime]['control'])
    values={name:[] for name in ('fit_disjoint_case_spell_loss','D_safeguards','skillcorner_false_D','short_spell_safeguard','owner_presence')}
    short_na=0;owner_na=0
    for row in rows:
        control=row['variants']['control'];candidate=row['variants']['memory-ablated']
        delta=_delta(candidate['metrics']['spell_f1_mean'],control['metrics']['spell_f1_mean'])
        case_deltas[row['case_id']+'/'+row['regime']]=delta
        if row['role']=='fit-disjoint':values['fit_disjoint_case_spell_loss'].append(None if delta is None else delta>=-.01-EPS)
        if row['cohort']=='skillcorner':
            delta_dead=_delta(candidate['known_live_false_D_rate'],control['known_live_false_D_rate'])
            values['skillcorner_false_D'].append(None if delta_dead is None else delta_dead<=.01+EPS)
        else:
            for metric in ('precision','recall'):
                delta_dead=_delta(candidate['dead'][metric],control['dead'][metric])
                values['D_safeguards'].append(None if delta_dead is None else delta_dead>=-.01-EPS)
        old=control['short_spells'];new=candidate['short_spells']
        if old['n_gt']!=new['n_gt']:raise ValueError('Reference short-spell support changed')
        if old['n_gt']==0:short_na+=1
        elif old['n_gt']<20:values['short_spell_safeguard'].append(new['n_matched']>=old['n_matched'])
        else:
            change=_delta(new['recall'],old['recall']);values['short_spell_safeguard'].append(None if change is None else change>=-.02-EPS)
        if control['support']['H'] and control['support']['A']:
            values['owner_presence'].append(candidate['predicted_on_known']['H']>0 and candidate['predicted_on_known']['A']>0)
        else:owner_na+=1
    gain=primary['natural']['delta'];masked=primary[REGIMES[1]]['delta']
    changes=[_delta(provider_means['natural']['memory-ablated'][p],provider_means['natural']['control'][p]) for p in PROVIDERS]
    checks=dict(natural_primary_gain=_check([None if gain is None else gain>EPS]),
        natural_provider_nonregression=_check([None if d is None else d>=-EPS for d in changes]),
        masked_primary_nonregression=_check([None if masked is None else masked>=-EPS]))
    for name,entries in values.items():checks[name]=_check(entries,short_na if name=='short_spell_safeguard' else owner_na if name=='owner_presence' else 0)
    decision='fail' if any(c['status']=='fail' for c in checks.values()) else 'unresolved' if any(c['status']=='unresolved' for c in checks.values()) else 'pass'
    return dict(schema_version=1,case_count=30,primary_matches=13,provider_means=provider_means,primary=primary,
        checks=checks,decision=decision,case_deltas=case_deltas,fresh_holdout=False,automatic_promotion=False)
