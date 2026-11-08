"""Exact bounded report schema; per-frame inference objects never pass this boundary."""
from math import isfinite

from cadence_protocol import VARIANTS,CONTROL,CANDIDATE,case_keys,digest,hash_files
from accuracy_evidence import assert_public_report


METRICS={'spell_f1_mean','macro_f1','accuracy','alive_dead_f1','n_gt_spells','n_pred_spells','confusion'}
SCORES={'precision','recall','f1','n_matched','n_spurious','n_missed'}
COUNTS={'n_gt','n_pred','n_matched','n_missed','n_spurious','n_ambiguous'}
BOUNDARY=COUNTS|{'precision','recall','f1'}|{name+unit for name in ('mean_latency','median_latency','mean_abs_latency','p90_abs_latency') for unit in ('_frames','_seconds')}
HA_BOUNDARY=COUNTS|{'precision','recall','f1','mean_latency_frames','mean_abs_latency_frames','matched_latency_denominator'}
DEAD={'n_live','n_dead','n_pred_D_on_known','true_D','false_D','missed_D','false_D_fraction','missed_D_fraction','precision','recall','dead_interval'}
COVERAGE={'active_rows','latent_X_rows','materialized_rows','neutral_rows','unsupported_rows','raw_distance_ties','wholly_unknown_period_D_rows'}
EXCHANGE={'known_live_rows','changed_after_exchange','changed_with_original_raw_HA_tie','changed_without_original_raw_HA_tie','changed_on_ball_missing','path_uniqueness_measured'}
FEATURES={'active_rows','observed_ball_rows','velocity_available_rows','velocity_unavailable_rows','repaired_rows','rolling_window_changed_rows','time_basis','pair_duration_bins'}
TOP={'schema_version','experiment_sha256','cohort','match','regime','fresh_holdout','target_data_used','head_fitting_performed','input_sha256','variants','feature_diagnostics','exchange_diagnostics'}


def _keys(value,expected):
    if not isinstance(value,dict) or set(value)!=set(expected):raise ValueError('Unexpected or missing report fields')


def _numbers(value):
    if isinstance(value,dict):
        for member in value.values():_numbers(member)
    elif isinstance(value,list):
        for member in value:_numbers(member)
    elif value is not None and (isinstance(value,bool) or not isinstance(value,(int,float)) or not isfinite(value)):
        raise ValueError('Metric leaves must be finite numbers or null')


def _counts(value):
    if any(type(v) is not int or v<0 for v in value.values()):raise ValueError('Counts must be nonnegative integers')


def validate_receipt(value,frozen,input_paths):
    _keys(value,TOP)
    if value['schema_version']!=1 or value['experiment_sha256']!=digest(frozen):raise ValueError('Receipt experiment identity changed')
    if (value['cohort'],value['match'],value['regime']) not in case_keys():raise ValueError('Unexpected case')
    if any(value[k] is not False for k in ('fresh_holdout','target_data_used','head_fitting_performed')):raise ValueError('Incorrect experiment scope flags')
    actual=hash_files(input_paths)
    if value['input_sha256']!=actual or any(frozen['input_sha256'].get(k)!=v for k,v in actual.items()):
        raise ValueError('Receipt consumed input identity changed')
    _keys(value['variants'],VARIANTS)
    for result in value['variants'].values():
        _keys(result,{'metrics','spell_counts','dead_metrics','boundary_metrics','supplementary','coverage'})
        _keys(result['metrics'],METRICS)
        _keys(result['spell_counts'],{'0.3','0.4','0.5','0.6','0.7'})
        for row in result['spell_counts'].values():_keys(row,SCORES)
        dead=result['dead_metrics'];_keys(dead,DEAD)
        _keys(dead['dead_interval'],{'n_gt','n_pred','per_iou','mean_f1'})
        _keys(dead['dead_interval']['per_iou'],{'0.3','0.4','0.5','0.6','0.7'})
        for row in dead['dead_interval']['per_iou'].values():_keys(row,SCORES)
        _keys(result['boundary_metrics'],{'12','25'})
        for row in result['boundary_metrics'].values():_keys(row,BOUNDARY)
        extra=result['supplementary'];_keys(extra,{'spell_duration','HA_boundaries','live_team'})
        _keys(extra['spell_duration'],{'short','medium','long','very_long'})
        for row in extra['spell_duration'].values():
            _keys(row,{'n_gt','per_iou'});_keys(row['per_iou'],{'0.3','0.4','0.5','0.6','0.7'})
            for item in row['per_iou'].values():_keys(item,{'n_matched','recall'})
        _keys(extra['HA_boundaries'],{'12','25'})
        for row in extra['HA_boundaries'].values():_keys(row,HA_BOUNDARY)
        _keys(extra['live_team'],{'known_live_rows','H_to_A','A_to_H','false_D','undecided'})
        _keys(result['coverage'],COVERAGE);_counts(result['coverage'])
        _numbers(result)
        cm=result['metrics']['confusion']
        if not isinstance(cm,list) or len(cm)!=3 or any(not isinstance(r,list) or len(r)!=4 or any(type(n) is not int or n<0 for n in r) for r in cm):
            raise ValueError('Invalid 3x4 confusion counts')
        if sum(map(sum,cm[:2]))!=dead['n_live'] or sum(cm[2])!=dead['n_dead']:
            raise ValueError('Confusion/support reconciliation failed')
        if cm[0][2]+cm[1][2]!=dead['false_D'] or cm[2][2]!=dead['true_D']:
            raise ValueError('Confusion/dead-count reconciliation failed')
        if sum(r['n_gt'] for r in extra['spell_duration'].values())!=result['metrics']['n_gt_spells']:
            raise ValueError('Duration support reconciliation failed')
    feature=value['feature_diagnostics'];_keys(feature,FEATURES)
    _keys(feature['time_basis'],{'source','canonical_grid','invalid_source','none'})
    _keys(feature['pair_duration_bins'],{'up_to_08','08_to_12','12_to_20','unavailable'})
    _counts({k:v for k,v in feature.items() if not isinstance(v,dict)})
    _counts(feature['time_basis']);_counts(feature['pair_duration_bins'])
    if feature['velocity_available_rows']+feature['velocity_unavailable_rows']!=feature['active_rows']:
        raise ValueError('Velocity support reconciliation failed')
    if sum(feature['time_basis'].values())!=feature['active_rows'] or sum(feature['pair_duration_bins'].values())!=feature['active_rows']:
        raise ValueError('Feature strata reconciliation failed')
    _keys(value['exchange_diagnostics'],{CONTROL,CANDIDATE})
    for row in value['exchange_diagnostics'].values():
        _keys(row,EXCHANGE)
        if row['path_uniqueness_measured'] is not False:raise ValueError('Path uniqueness has not been measured')
        _counts({k:v for k,v in row.items() if k!='path_uniqueness_measured'})
        if row['changed_with_original_raw_HA_tie']+row['changed_without_original_raw_HA_tie']!=row['changed_after_exchange'] or row['changed_after_exchange']>row['known_live_rows']:
            raise ValueError('Exchange count reconciliation failed')
    assert_public_report(value)


def receipt_variant(aggregate,dead,boundary,extra,coverage):
    metrics={k:aggregate['metrics'][k] for k in METRICS}
    confusion=metrics['confusion']
    if len(confusion)==4:
        if any(confusion[3]):raise ValueError('Official confusion unexpectedly scores excluded truth')
        metrics['confusion']=confusion[:3]
    return dict(metrics=metrics,spell_counts={str(k):v for k,v in aggregate['spell_counts'].items()},
        dead_metrics=dead,boundary_metrics=boundary,
        supplementary={k:extra[k] for k in ('spell_duration','HA_boundaries','live_team')},coverage=coverage)
