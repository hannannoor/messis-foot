"""Public-only evidence checks and additive verification of the historical run.

This guard was added after scoring. It never infers/rescores or rewrites v2 evidence.
"""
from datetime import datetime,timedelta,timezone
from pathlib import Path,PurePosixPath
import hashlib
import json
import re

from wcsf_report import read_json,parse_json,keys,count,validate_report,METHODS

HISTORICAL_FREEZE='cca43bd48da128247fea378fc8e8d3cc5455969ace0f93de377e9458259fc4aa'
HISTORICAL_RESULT='16297acd3e3d176f06ad105575f89d3ecf3818e9ee874a02bafde2cf70c8694d'
HISTORICAL_COMMIT='2abd83b3a719ae041671194000b4fa3c20ffcfd4'


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def sha256(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def _hash(value):
    if type(value) is not str or not re.fullmatch('[0-9a-f]{64}',value):raise ValueError('Invalid hash identity')


def read_events(path):
    with Path(path).open(encoding='utf-8') as f:lines=f.read().splitlines()
    if len(lines)>32 or any(not s.strip() for s in lines):raise ValueError('Unexpected event-log length/blank line')
    return [parse_json(s) for s in lines]


def _time(value):
    if type(value) is not str:raise ValueError('Invalid event timestamp')
    try:t=datetime.fromisoformat(value)
    except ValueError:raise ValueError('Invalid event timestamp') from None
    if t.tzinfo is None or t.utcoffset()!=timedelta(0):raise ValueError('Event timestamp must be UTC')
    return t


def load_attempts(path,freeze_sha256,*,complete=False):
    p=Path(path);events=read_events(p) if p.exists() else []
    expected=[(stage,m) for stage in ('infer','score') for m in METHODS]
    if len(events)>6 or complete and len(events)!=6:raise ValueError('Unexpected method-attempt count')
    times=[]
    for row,(stage,method) in zip(events,expected):
        keys(row,('event','timestamp_utc','stage','method','freeze_sha256'))
        if row['event']!='method_attempt' or row['stage']!=stage or row['method']!=method or row['freeze_sha256']!=freeze_sha256:
            raise ValueError('Unexpected attempt event/order/protocol')
        times.append(_time(row['timestamp_utc']))
    if times!=sorted(times):raise ValueError('Attempt timestamps out of order')
    return events


def validate_logs(access_path,attempt_path,freeze_sha256,first_access,*,legacy=False):
    from wcsf_source import REV
    events=read_events(access_path)
    names=('machine_reference_access','predictions_sealed','reference_summary_and_outcomes_opened')
    if len(events)!=3 or tuple(e.get('event') for e in events)!=names:raise ValueError('Unexpected access event/order')
    a,b,c=events
    keys(a,('event','timestamp_utc','source_periods','protocol_hash','source_commit','actor','purpose'))
    keys(b,('event','timestamp_utc','protocol_hash','methods'))
    keys(c,('event','timestamp_utc','protocol_hash','permanently_used'))
    if any(e['protocol_hash']!=freeze_sha256 for e in events):raise ValueError('Access protocol differs')
    if type(a['source_periods']) is not int or a['source_periods']!=2 or a['source_commit']!=REV or a['actor']!='local_adapter' or a['purpose']!='quarantined_ingestion':raise ValueError('Machine reference-access identity differs')
    if type(b['methods']) is not int or b['methods']!=3 or c['permanently_used'] is not True:raise ValueError('Outcome access declaration differs')
    if a['timestamp_utc']!=first_access:raise ValueError('First machine access differs from acquisition')
    times=[_time(e['timestamp_utc']) for e in events]
    if times!=sorted(times):raise ValueError('Access timestamps out of order')
    attempts=load_attempts(attempt_path,freeze_sha256,complete=True)
    ts=[_time(e['timestamp_utc']) for e in attempts]
    if not times[0]<=ts[0]<=ts[2]<=times[1]:raise ValueError('Inference/reference access order differs')
    if legacy:
        # V2's first score timestamp is a stage-entry claim, not exact method entry.
        if not times[1]<=ts[3]<=times[2]<=ts[4]:raise ValueError('Historical scoring access order differs')
    elif not times[2]<=ts[3]:raise ValueError('Method entered before reference loading event')
    return dict(access_sha256=sha256(access_path),attempts_sha256=sha256(attempt_path),access_events=3,inference_attempts=3,scoring_attempts=3,
                attempt_timestamp_semantics='legacy first-score stage entry' if legacy else 'method entry')


def verify_public(public):
    public=Path(public);freeze=read_json(public/'freeze.json');fd=digest(freeze)
    keys(freeze,('schema_version','base_commit','methods','generation','assets','source_sha256','environment','contract'))
    if type(freeze['schema_version']) is not int or freeze['schema_version']!=1 or freeze['methods']!=list(METHODS):raise ValueError('Invalid frozen method identity')
    sources=freeze['source_sha256']
    if type(sources) is not dict or not 9<=len(sources)<=1000:raise ValueError('Invalid bounded source inventory')
    for name,h in sources.items():
        p=PurePosixPath(name)
        if p.is_absolute() or '..' in p.parts or '\\' in name or ':' in name:raise ValueError('Unsafe source identity')
        _hash(h)
    acq=read_json(public/'acquisition.json');geo=read_json(public/'geometry.json');pred=read_json(public/'predictions-seal.json')
    seal=read_json(public/'score-seal.json');verification=read_json(public/'verification.json');result=read_json(public/'results.json')
    keys(acq,('schema_version','freeze_sha256','input_sha256','source_rows','identical_geometry_duplicates','first_machine_reference_access_utc'))
    keys(acq['input_sha256'],('archive_1','archive_2','geometry_store','reference_store'))
    for h in acq['input_sha256'].values():_hash(h)
    count(acq['source_rows']);count(acq['identical_geometry_duplicates']);_time(acq['first_machine_reference_access_utc'])
    keys(geo,('schema_version','freeze_sha256','acquisition_sha256','decision','quality'))
    keys(geo['decision'],('selected','eligible','candidate_counts','failure'))
    if geo['decision']['selected'] not in ('absolute-x','absolute-xy','offset-x','offset-xy') or geo['decision']['failure'] is not None:raise ValueError('No passing geometry contract')
    keys(pred,('schema_version','freeze_sha256','geometry_sha256','private_sha256','rows'))
    keys(pred['private_sha256'],(*METHODS,'index','endpoints','provenance'))
    for h in pred['private_sha256'].values():_hash(h)
    keys(seal,('schema_version','freeze_sha256','predictions_seal_sha256','results_sha256','attempts_sha256',
               *(['access_sha256'] if 'post-review' in freeze['contract'] else [])))
    keys(verification,('schema_version','status','verified','freeze_sha256','geometry_sha256','completed_method_comparisons','inference_attempts','scoring_attempts','results_sha256'))
    for row in (acq,geo,pred,seal,verification):
        if type(row['schema_version']) is not int or row['schema_version']!=1 or row['freeze_sha256']!=fd:raise ValueError('Public freeze binding differs')
    for key,path,row in (('acquisition_sha256','acquisition.json',geo),('geometry_sha256','geometry.json',pred),
                         ('predictions_seal_sha256','predictions-seal.json',seal),('results_sha256','results.json',seal),
                         ('geometry_sha256','geometry.json',verification),('results_sha256','results.json',verification)):
        if row[key]!=sha256(public/path):raise ValueError('Public receipt hash chain differs')
    _hash(seal['attempts_sha256'])
    if 'access_sha256' in seal:_hash(seal['access_sha256'])
    validate_report(result)
    if type(pred['rows']) is not int or pred['rows']!=result['match'][METHODS[0]]['support']['frames']:raise ValueError('Prediction/evaluation rows differ')
    if verification['status']!='completed' or verification['verified'] is not True or any(type(verification[k]) is not int or verification[k]!=3 for k in ('completed_method_comparisons','inference_attempts','scoring_attempts')):raise ValueError('Incomplete comparison receipt')
    return dict(public_numeric_and_hash_chain_verified=True,private_inputs_verified=False,environment_match_required=False,
                source_authenticity_independently_verified=False,declared_method_comparisons=3,freeze_sha256=fd,results_sha256=sha256(public/'results.json'))


def verify_historical_local(root):
    root=Path(root);public=root/'reports/wcsf-transfer-v2';private=root.parent/'wcsf-reference/wcsf-2026-11-09-2'
    snapshot=root/'.superpowers/sdd/2026-11-09-wcsf-transfer/frozen-v2-sources'
    result=verify_public(public);freeze=read_json(public/'freeze.json')
    if digest(freeze)!=HISTORICAL_FREEZE or sha256(public/'results.json')!=HISTORICAL_RESULT:raise ValueError('Unexpected historical comparison identity')
    for name,h in freeze['source_sha256'].items():
        if sha256(snapshot/name)!=h:raise ValueError('Historical source snapshot differs')
    acq=read_json(public/'acquisition.json');pred=read_json(public/'predictions-seal.json');seal=read_json(public/'score-seal.json')
    inputs=dict(archive_1=private/'positions_FIRST_HALF.csv.zip',archive_2=private/'positions_SECOND_HALF.csv.zip',geometry_store=private/'geometry.sqlite',reference_store=private/'reference.sqlite')
    outputs={**{m:private/'predictions'/(m+'.npy') for m in METHODS},'index':private/'predictions/canonical-index.npy','endpoints':private/'predictions/endpoints.npy','provenance':private/'predictions/observation-provenance.npy'}
    if acq['input_sha256']!={n:sha256(p) for n,p in inputs.items()} or pred['private_sha256']!={n:sha256(p) for n,p in outputs.items()}:raise ValueError('Historical private artifact differs')
    logs=validate_logs(private/'access.jsonl',private/'attempts.jsonl',HISTORICAL_FREEZE,acq['first_machine_reference_access_utc'],legacy=True)
    if logs['attempts_sha256']!=seal['attempts_sha256']:raise ValueError('Historical attempt seal differs')
    return dict(schema_version=1,stage='post_run_guard_attestation',historical_source_commit=HISTORICAL_COMMIT,
                historical_freeze_sha256=HISTORICAL_FREEZE,results_sha256=HISTORICAL_RESULT,
                historical_sources_verified=len(freeze['source_sha256']),private_input_hashes_verified=4,private_output_hashes_verified=6,
                logs=logs,scientific_rescoring_performed=False,
                guards_added_after_scoring=True,guard_source_sha256={n:sha256(root/n) for n in ('wcsf_postrun_verify.py','wcsf_report.py','wcsf_audit.py')})


def main():
    import argparse
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('mode',choices=('public','local'));parser.add_argument('--write-attestation',action='store_true')
    args=parser.parse_args();root=Path(__file__).resolve().parent
    try:
        result=verify_public(root/'reports/wcsf-transfer-v2') if args.mode=='public' else verify_historical_local(root)
        if args.write_attestation:
            if args.mode!='local':raise ValueError('Only local verification can attest private artifacts')
            p=root/'reports/wcsf-transfer-v2/post-review-attestation.json'
            if p.exists():
                if read_json(p)!=result:raise ValueError('Preserve prior attestation')
            else:
                with p.open('x',encoding='utf-8') as f:f.write(json.dumps(result,indent=2,allow_nan=False)+'\n')
        print(json.dumps(result,allow_nan=False));return 0
    except (ValueError,OSError,KeyError,TypeError) as error:
        print(json.dumps(dict(status='failed',error_type=type(error).__name__)));return 1


if __name__=='__main__':raise SystemExit(main())
