"""Fixed development pilot and fail-closed local evidence identities."""
import json
from pathlib import Path

from gap_solver.accuracy_protocol import digest,hash_files
from gap_solver.input_contract import write_new_report
from accuracy_evidence import assert_public_report


BASE_COMMIT='cee674190775e9356745f461ba1561e9f2a46f7e'
CONTROL='frozen-control'
CANDIDATE='bounded-reacquisition-speed-v1'
MATCHES=(('skillcorner','1874553'),('skillcorner','1886347'),('dfl','J03WOH'),('dfl','J03WOY'))
REGIMES=('natural','retain-2','retain-3','retain-5','mask30-seed1729')
VARIANTS=(CONTROL,CANDIDATE)+tuple(f'{mode}-w{w}' for mode in ('official-convention','matched-input') for w in (0,25,50,125))


def case_keys():return tuple((c,m,r) for c,m in MATCHES for r in REGIMES)


def protocol():
    return dict(schema_version=1,base_commit=BASE_COMMIT,max_gap_s=.20,max_pair_rows=5,
        speed_cap_m_s=50.,recent_window_rows=12,time_bound_tolerance_s=1e-9,
        switch_cost=32.,motion_weight=0.,floor=1e-6,mask_rate=.30,mask_seed=1729,
        max_cases=20,max_aggregate_scorings=200,
        cases=[dict(cohort=c,match=m,regime=r) for c,m,r in case_keys()],
        variants={name:dict(kind='fixed') for name in VARIANTS},
        duration_bins=dict(short='<=25',medium='26..75',long='76..250',very_long='>250'),
        gate='seven exact aggregate checks plus per-match review; no qualification/promotion',
        fresh_holdout=False,head_fitting_performed=False,target_data_used=False)


def validate_protocol(value):
    if value!=protocol():raise ValueError('Frozen cadence protocol differs; no parameter reselection')
    assert_public_report(value)


def make_freeze(sources,inputs):
    value=dict(schema_version=1,base_commit=BASE_COMMIT,protocol=protocol(),
        source_sha256=hash_files(sources),input_sha256=hash_files(inputs))
    assert_public_report(value)
    return value


def validate_freeze(value,sources,inputs):
    if set(value)!={'schema_version','base_commit','protocol','source_sha256','input_sha256'}:
        raise ValueError('Unexpected or missing freeze fields')
    validate_protocol(value['protocol'])
    if value['schema_version']!=1 or value['base_commit']!=BASE_COMMIT:
        raise ValueError('Wrong freeze release/schema')
    if value['source_sha256']!=hash_files(sources) or value['input_sha256']!=hash_files(inputs):
        raise ValueError('Consumed source/input identity changed')
    assert_public_report(value)


def write_new(path,value,inputs):
    assert_public_report(value)
    write_new_report(Path(path),value,inputs)
