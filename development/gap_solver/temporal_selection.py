"""External-only fitting helpers; sklearn is consumed by the developer, never runtime inference."""
from math import log
import numpy as np
from .temporal import MOTION_FEATURES


def export_boosted(classifier):
    if list(classifier.classes_)!=[0,1] or classifier.estimators_.shape[1]!=1:
        raise ValueError('portable model requires explicit binary H/A classes')
    prior=classifier.init_.class_prior_
    if len(prior)!=2 or min(prior)<=0:raise ValueError('unsupported ensemble initial estimator')
    trees=[]
    for estimator in classifier.estimators_[:,0]:
        tree=estimator.tree_
        trees.append(dict(children_left=tree.children_left.tolist(),children_right=tree.children_right.tolist(),
                          feature=tree.feature.tolist(),threshold=tree.threshold.tolist(),value=tree.value[:,0,0].tolist()))
    return dict(feature_names=list(MOTION_FEATURES),learning_rate=float(classifier.learning_rate),
                initial_log_odds=log(float(prior[1])/float(prior[0])),trees=trees)


def fit_temperature(scores,target,weights=None):
    z=np.asarray(scores,dtype=np.float64);y=np.asarray(target)
    if z.ndim!=1 or y.shape!=z.shape or not len(z) or not np.isfinite(z).all() or not np.isin(y,[0,1]).all():
        raise ValueError('invalid external calibration data')
    w=np.ones(len(z)) if weights is None else np.asarray(weights,dtype=np.float64)
    if w.shape!=z.shape or not np.isfinite(w).all() or (w<0).any() or w.sum()<=0:raise ValueError('invalid calibration weights')
    w=w/w.sum();low=0.;high=20.
    for _ in range(70):
        beta=(low+high)/2
        p=1/(1+np.exp(-np.clip(z*beta,-50,50)))
        gradient=float(np.dot(w,z*(p-y)))
        if gradient>0:high=beta
        else:low=beta
    return 1/max((low+high)/2,.001)


def contiguous_mask(periods,rate,seed):
    periods=np.asarray(periods)
    if periods.ndim!=1 or not np.isin(periods,[0,1,2]).all() or not 0<=rate<=1:raise ValueError('invalid contiguous mask protocol')
    rng=np.random.RandomState(seed);active=np.flatnonzero(periods>0);target=round(len(active)*rate)
    mask=np.zeros(len(periods),dtype=bool);remaining=target;attempts=0
    while remaining and attempts<max(100,len(active)*10):
        first=int(rng.choice(active));length=int(rng.choice([5,15,50,125,250]));stop=first
        while stop<len(periods) and periods[stop]==periods[first] and stop-first<length:stop+=1
        selected=np.flatnonzero(~mask[first:stop])+first
        selected=selected[:remaining];mask[selected]=True;remaining-=len(selected);attempts+=1
    if remaining:
        selected=rng.choice(np.flatnonzero((periods>0)&~mask),remaining,replace=False);mask[selected]=True
    return mask


def validation_gate(reports,endpoints,masked_reports=None,masked_endpoints=None):
    if len(reports)!=len(endpoints) or len(reports)<2:raise ValueError('validation gate requires paired independent matches')
    checks={}
    checks['source_quality']=all(r.get('source_quality_gate_passed') is True for r in reports)
    checks['coverage_gain']=float(np.mean([r['baseline']['coverage']['undecided_fraction']-r['selected']['coverage']['undecided_fraction'] for r in reports]))>=.05
    checks['team_spell_no_match_decline']=all(r['selected']['metrics']['spell_f1_mean']>=r['baseline']['metrics']['spell_f1_mean'] for r in reports)
    checks['mean_spell_advantage_over_endpoint']=float(np.mean([r['selected']['metrics']['spell_f1_mean']-e['selected']['metrics']['spell_f1_mean'] for r,e in zip(reports,endpoints)]))>0
    checks['natural_hidden_nonregression']=all(r['hidden_opponents']['reference_short_spells']==0 or
        r['hidden_opponents']['selected_hits']>=r['hidden_opponents']['baseline_hits'] for r in reports)
    label_details={}
    for name in ('H','A'):
        total=sum(r['change']['newly_resolved_by_label'][name]['frames'] for r in reports)
        correct=sum(r['change']['newly_resolved_by_label'][name]['frames']*(r['change']['newly_resolved_by_label'][name]['correct_fraction'] or 0.) for r in reports)
        missing_total=sum(r['gap_strata']['per_label'][name]['frames'] for r in reports)
        missing_correct=sum(r['gap_strata']['per_label'][name]['correct'] for r in reports)
        gaps=sum(r['gap_strata']['per_label'][name]['gaps'] for r in reports)
        checks[name+'_new_agreement']=total>=100 and correct/total>=.9
        checks[name+'_missing_gap_agreement']=missing_total>=100 and gaps>=10 and missing_correct/missing_total>=.9
        label_details[name]=dict(frames=total,correct_fraction=correct/total if total else None,
            missing_frames=missing_total,missing_correct_fraction=missing_correct/missing_total if missing_total else None,gaps=gaps)
    def hidden_support(values):return sum(r['hidden_opponents']['reference_short_spells'] for r in values)
    use=reports;against=endpoints;scope='natural'
    if hidden_support(reports)<20 and masked_reports is not None:
        use=masked_reports;against=masked_endpoints;scope='masked'
    support=hidden_support(use)
    hits=sum(r['hidden_opponents']['selected_hits'] for r in use)
    other_hits=sum(r['hidden_opponents']['selected_hits'] for r in against)
    false=sum(r['hidden_opponents']['selected_false_opposing_spells'] for r in use)
    other_false=sum(r['hidden_opponents']['selected_false_opposing_spells'] for r in against)
    checks['hidden_support']=support>=20 and sum(r['hidden_opponents']['reference_short_spells']>0 for r in use)>=2
    checks['positive_hidden_recovery']=hits>other_hits
    checks['hidden_nonregression_against_baseline']=all(r['hidden_opponents']['selected_hits']>=r['hidden_opponents']['baseline_hits'] for r in use)
    checks['bounded_false_opposing_spells']=false-other_false<=hits-other_hits
    return dict(passes=all(checks.values()),checks=checks,labels=label_details,
                hidden_scope=scope,hidden_reference_spells=support,hidden_hits=hits,endpoint_hits=other_hits,
                natural_hidden_claim_supported=scope=='natural' and checks['hidden_support'] and checks['positive_hidden_recovery'])
