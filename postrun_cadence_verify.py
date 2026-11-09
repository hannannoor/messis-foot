"""Additive post-review publication guard; the historical V2 sources stay frozen.

This attests current omitted-wrapper bytes and strict report consistency. It
does not retroactively prove every wrapper's historical execution-time state.
No external predictions/official scores are recomputed here.
"""
import hashlib
import json
from math import isfinite,isclose
from pathlib import Path
from statistics import fmean

import cadence_experiment as run
import cadence_receipts as schema
from cadence_protocol import CONTROL,CANDIDATE,VARIANTS,case_keys,digest,hash_files


OMITTED={
    'accuracy_experiment.py':'2eb9963993e4cc51aeb7841d624bacc20da50ee7610847c4b9c5941d0b2f150a',
    'accuracy_experiment_frozen.py':'cf0559d447c44cb2f059cea21cb96a9a6c70a4aad89ae9e0ced83d46580ca0f8',
    'accuracy_evidence.py':'2d3195ff0b42e973998c6a32d81e0f590e45ee97d69132fafb87881c096980c4',
    'ball_gap_candidate.py':'8f120af1c9d0c7219fd075ea2217612d7755798c94c9d815fe92d85b76e4a4f2',
}
IOU={'0.3','0.4','0.5','0.6','0.7'}
RESULT={'metrics','spell_counts','dead_metrics','boundary_metrics','supplementary','coverage'}
COUNT_NAMES={'true_D','false_D','missed_D','H_to_A','A_to_H','undecided','raw_distance_ties','matched_latency_denominator'}


def strict_json_loads(raw):
    def pairs(rows):
        result={}
        for key,value in rows:
            if key in result:raise ValueError('Duplicate JSON key')
            result[key]=value
        return result
    def constant(value):raise ValueError('Nonfinite JSON constant')
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=constant)


def _dictionary_keys(path,value):
    if not path:return schema.TOP
    if path==('input_sha256',):return set(value)
    if path==('variants',):return set(VARIANTS)
    if path==('feature_diagnostics',):return schema.FEATURES
    if path==('feature_diagnostics','time_basis'):return {'source','canonical_grid','invalid_source','none'}
    if path==('feature_diagnostics','pair_duration_bins'):return {'up_to_08','08_to_12','12_to_20','unavailable'}
    if path==('exchange_diagnostics',):return {CONTROL,CANDIDATE}
    if len(path)==2 and path[0]=='exchange_diagnostics' and path[1] in (CONTROL,CANDIDATE):return schema.EXCHANGE
    if len(path)<2 or path[0]!='variants' or path[1] not in VARIANTS:return None
    tail=path[2:]
    if not tail:return RESULT
    if tail==('metrics',):return schema.METRICS
    if tail==('coverage',):return schema.COVERAGE
    if tail==('spell_counts',):return IOU
    if len(tail)==2 and tail[0]=='spell_counts' and tail[1] in IOU:return schema.SCORES
    if tail==('dead_metrics',):return schema.DEAD
    if tail==('dead_metrics','dead_interval'):return {'n_gt','n_pred','per_iou','mean_f1'}
    if tail==('dead_metrics','dead_interval','per_iou'):return IOU
    if len(tail)==4 and tail[:3]==('dead_metrics','dead_interval','per_iou') and tail[3] in IOU:return schema.SCORES
    if tail==('boundary_metrics',):return {'12','25'}
    if len(tail)==2 and tail[0]=='boundary_metrics' and tail[1] in ('12','25'):return schema.BOUNDARY
    if tail==('supplementary',):return {'spell_duration','HA_boundaries','live_team'}
    if tail==('supplementary','live_team'):return {'known_live_rows','H_to_A','A_to_H','false_D','undecided'}
    if tail==('supplementary','HA_boundaries'):return {'12','25'}
    if len(tail)==3 and tail[:2]==('supplementary','HA_boundaries') and tail[2] in ('12','25'):return schema.HA_BOUNDARY
    if tail==('supplementary','spell_duration'):return {'short','medium','long','very_long'}
    if len(tail)>=3 and tail[:2]==('supplementary','spell_duration') and tail[2] in ('short','medium','long','very_long'):
        if len(tail)==3:return {'n_gt','per_iou'}
        if len(tail)==4 and tail[3]=='per_iou':return IOU
        if len(tail)==5 and tail[3]=='per_iou' and tail[4] in IOU:return {'n_matched','recall'}
    return None


def _walk(value,path=()):
    if isinstance(value,dict):
        keys=_dictionary_keys(path,value)
        if keys is None or set(value)!=set(keys):raise ValueError('Unexpected container/fields at scalar report boundary')
        for key,member in value.items():_walk(member,path+(key,))
        return
    if isinstance(value,list):
        if len(path)!=4 or path[:1]!=('variants',) or path[2:]!=('metrics','confusion'):
            raise ValueError('Only the declared confusion matrix may be an array')
        if len(value)!=3 or any(not isinstance(row,list) or len(row)!=4 or any(type(x) is not int or x<0 for x in row) for row in value):
            raise ValueError('Invalid bounded confusion')
        return
    if len(path)==1:return # Exact metadata values are checked below.
    if path[0]=='input_sha256':
        if not isinstance(value,str) or len(value)!=64 or any(c not in '0123456789abcdef' for c in value):raise ValueError('Invalid input digest')
        return
    if path[0]=='exchange_diagnostics' and path[-1]=='path_uniqueness_measured':
        if value is not False:raise ValueError('Path uniqueness was not measured')
        return
    name=path[-1]
    is_count=(path[0] in ('feature_diagnostics','exchange_diagnostics') or name.startswith('n_') or name.endswith('_rows') or name in COUNT_NAMES)
    if is_count:
        if type(value) is not int or value<0:raise ValueError('Expected a nonnegative integer scalar')
    elif value is not None and (type(value) not in (int,float) or not isfinite(value)):
        raise ValueError('Expected a finite numeric scalar or defined null')


def _same(actual,expected):
    if expected is None:
        if actual is not None:raise ValueError('Undefined metric must be null')
    elif type(actual) not in (int,float) or not isfinite(actual) or not isclose(actual,expected,rel_tol=1e-12,abs_tol=1e-12):
        raise ValueError('Metric disagrees with its support/counts')


def _ratio(numerator,denominator,nullable=False):return numerator/denominator if denominator else None if nullable else 0.


def _scores(row,ng,npred,nullable=False):
    m=row['n_matched'];sp=row['n_spurious'];miss=row['n_missed']
    if m+miss!=ng or m+sp!=npred:raise ValueError('Event/spell count reconciliation failed')
    _same(row['precision'],_ratio(m,npred,nullable));_same(row['recall'],_ratio(m,ng,nullable))
    _same(row['f1'],_ratio(2*m,ng+npred,nullable))


def _boundary(row,legacy):
    _scores(row,row['n_gt'],row['n_pred'])
    if row['n_ambiguous']>row['n_gt']:raise ValueError('Ambiguous events exceed true support')
    names=('mean_latency','median_latency','mean_abs_latency','p90_abs_latency') if legacy else ('mean_latency','mean_abs_latency')
    for name in names:
        frames=row[name+'_frames']
        if not row['n_matched']:_same(frames,None)
        elif type(frames) not in (int,float) or not isfinite(frames) or ('abs' in name and frames<0):raise ValueError('Invalid matched latency')
        if legacy:_same(row[name+'_seconds'],None if frames is None else frames/25)
    if not legacy and row['matched_latency_denominator']!=row['n_matched']:raise ValueError('Latency denominator mismatch')
    if row['n_matched'] and row['mean_abs_latency_frames']+1e-12<abs(row['mean_latency_frames']):raise ValueError('Impossible signed/absolute latency means')


def strict_validate_receipt(value):
    _walk(value)
    if type(value['schema_version']) is not int or value['schema_version']!=1:raise ValueError('Invalid receipt schema')
    if (value['cohort'],value['match'],value['regime']) not in case_keys():raise ValueError('Undeclared case')
    if not isinstance(value['experiment_sha256'],str) or len(value['experiment_sha256'])!=64:raise ValueError('Invalid experiment digest')
    if any(value[name] is not False for name in ('fresh_holdout','target_data_used','head_fitting_performed')):raise ValueError('Incorrect experiment scope')
    for result in value['variants'].values():
        metrics=result['metrics'];cm=metrics['confusion'];dead=result['dead_metrics'];total=sum(map(sum,cm))
        if total<=0:raise ValueError('No scored support')
        live=sum(map(sum,cm[:2]));nd=sum(cm[2]);td=cm[2][2];fd=cm[0][2]+cm[1][2];miss=nd-td;said=td+fd
        for name,expected in (('n_live',live),('n_dead',nd),('true_D',td),('false_D',fd),('missed_D',miss),('n_pred_D_on_known',said)):
            _same(dead[name],expected)
        for name,expected in (('precision',_ratio(td,said,True)),('recall',_ratio(td,nd,True)),('false_D_fraction',_ratio(fd,live,True)),('missed_D_fraction',_ratio(miss,nd,True))):
            _same(dead[name],expected)
        _same(metrics['accuracy'],sum(cm[i][i] for i in range(3))/total)
        _same(metrics['macro_f1'],fmean(_ratio(2*cm[i][i],sum(cm[i])+sum(r[i] for r in cm)) for i in range(3)))
        tp=sum(sum(row[:2]) for row in cm[:2]);fp=sum(cm[2][:2]);fn=sum(sum(row[2:]) for row in cm[:2])
        _same(metrics['alive_dead_f1'],_ratio(2*tp,2*tp+fp+fn))
        for row in result['spell_counts'].values():_scores(row,metrics['n_gt_spells'],metrics['n_pred_spells'])
        _same(metrics['spell_f1_mean'],fmean(row['f1'] for row in result['spell_counts'].values()))
        intervals=dead['dead_interval']
        for row in intervals['per_iou'].values():_scores(row,intervals['n_gt'],intervals['n_pred'],True)
        f1s=[row['f1'] for row in intervals['per_iou'].values()]
        _same(intervals['mean_f1'],None if any(x is None for x in f1s) else fmean(f1s))
        for row in result['boundary_metrics'].values():_boundary(row,True)
        extra=result['supplementary']
        for row in extra['HA_boundaries'].values():_boundary(row,False)
        for row in extra['spell_duration'].values():
            for score in row['per_iou'].values():
                if score['n_matched']>row['n_gt']:raise ValueError('Duration matches exceed support')
                _same(score['recall'],_ratio(score['n_matched'],row['n_gt'],True))
        if sum(r['n_gt'] for r in extra['spell_duration'].values())!=metrics['n_gt_spells']:raise ValueError('Duration count mismatch')
        for name,expected in (('known_live_rows',live),('H_to_A',cm[0][1]),('A_to_H',cm[1][0]),('false_D',fd),('undecided',cm[0][3]+cm[1][3])):
            _same(extra['live_team'][name],expected)
        coverage=result['coverage']
        if coverage['active_rows']<total or not 0<=coverage['materialized_rows']<=coverage['latent_X_rows']<=coverage['active_rows']:
            raise ValueError('Invalid materialization support')
    feature=value['feature_diagnostics']
    if feature['velocity_available_rows']+feature['velocity_unavailable_rows']!=feature['active_rows'] or feature['velocity_available_rows']>feature['observed_ball_rows'] or feature['repaired_rows']>feature['velocity_available_rows']:
        raise ValueError('Invalid velocity availability support')
    if sum(feature['time_basis'].values())!=feature['active_rows'] or sum(feature['pair_duration_bins'].values())!=feature['active_rows']:
        raise ValueError('Feature strata mismatch')


def attest_omitted_sources(root):
    root=Path(root);actual={}
    for name,expected in OMITTED.items():
        path=root/name
        if not path.is_file():raise ValueError('Omitted scoring wrapper unavailable')
        actual[name]=hashlib.sha256(path.read_bytes()).hexdigest()
        if actual[name]!=expected:raise ValueError('Omitted scoring wrapper differs from base Git bytes')
    return actual


def verify():
    omitted=attest_omitted_sources(run.ROOT)
    folder=run.REPORTS
    frozen=strict_json_loads((folder/'comparison-freeze.json').read_bytes())
    rows=[]
    for c,m,r in case_keys():
        path=folder/'cases'/run.case_filename(c,m,r)
        value=strict_json_loads(path.read_bytes());strict_validate_receipt(value)
        run.validate_receipt(value,frozen,run.case_input_paths(c,m));rows.append(value)
    for name in ('summary.json','case-seal.json','verification.json'):strict_json_loads((folder/name).read_bytes())
    run.verify() # Hash/identity and summary replay only; no arrays/predictions rescored.
    own={name:run.ROOT/name for name in ('postrun_cadence_verify.py','tests/test_review_cadence_evidence.py')}
    value=dict(schema_version=1,experiment_sha256=digest(frozen),timing='post-run independent-review hardening',
        original_v2_explicit_source_inventory_complete=False,listed_historical_sources_verified=True,
        omitted_current_wrapper_sha256=omitted,omitted_current_wrappers_match_base=True,
        historical_wrapper_execution_state_proven=False,verification_source_sha256=hash_files(own),
        strict_cases_verified=20,variant_numeric_reports_verified=200,duplicate_json_keys_rejected=True,
        extra_external_scoring_performed=False,new_holdout=False,target_data_used=False,
        endpoint_provenance_distinguished=False,native_freshness_validated=False,
        limitations=['Four original executed wrappers were omitted from the explicit prospective V2 map; their current bytes match the pinned base.',
            'Post-run matching is not proof of every historical transient execution state.',
            'Use this strict publication verifier; the original V2 validator remains frozen historical source.',
            'Timing-basis marginals do not identify endpoint interpolation, native freshness, or valid source-pair counts.',
            'Only supplementary.HA_boundaries is run-local and pair-typed; legacy boundary_metrics is unchanged.',
            'Whole-period fallback subtype can undercount interrupted same-number blocks; ordinary materialization count is valid.'])
    run._store_identical(folder/'post-review-attestation.json',value,run.all_input_paths().values())
    print('Post-review guard passed: 20 strict receipts / 200 numeric reports; four current wrapper identities attested')
    return value


if __name__=='__main__':verify()
