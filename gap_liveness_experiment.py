"""Prospective one-shot gap-rule external harm check; no challenge data here."""
import argparse
from collections import defaultdict
from datetime import datetime,timezone
import hashlib,json
from math import fsum,isclose,ulp
from pathlib import Path
import platform,re,subprocess,sys

from touch_experiment import canonical,write_new,read,score,seal_phase
from memory_ablation_metrics import MATCHES

BASE='a5d5aa3c7da86837ec0f0a750f8e1996b66e639a'
ROOT=Path(__file__).resolve().parent
PUBLIC=ROOT/'reports/gap-liveness'
PRIVATE=ROOT.parent/'gap-liveness-private/2026-11-10'
REGIMES=('natural','mask30-seed1729')
LIMITS=dict(control=30,rule=30)
SPECS=('docs/superpowers/specs/2026-11-10-gap-liveness-design.md','docs/superpowers/specs/2026-11-10-observed-touch-design.md','docs/superpowers/plans/2026-11-10-gap-liveness-addenda.md')


def sha(path):
    with Path(path).open('rb') as handle:return hashlib.file_digest(handle,'sha256').hexdigest()


def blob_hash(data):return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()


def tree(commit):
    data=subprocess.check_output(['git','ls-tree','-rz',commit],cwd=ROOT)
    result={}
    for entry in data.split(b'\0'):
        if not entry:continue
        meta,name=entry.split(b'\t',1);mode,kind,digest=meta.decode().split()
        if kind!='blob' or mode!='100644':raise ValueError('Unsupported preserved Git object')
        result[name.decode()]=digest
    return result


def preservation():
    recorded=tree(BASE);changed=[]
    for name,digest in recorded.items():
        path=ROOT/name
        if not path.is_file() or blob_hash(path.read_bytes())!=digest:changed.append(name)
    return dict(base=BASE,files=len(recorded),unchanged=not changed,changed_paths=changed)


def source_hashes(commit):
    recorded=tree(commit);result={}
    for name,digest in recorded.items():
        if not name.endswith('.py'):continue
        data=(ROOT/name).read_bytes()
        if blob_hash(data)!=digest:raise ValueError('Uncommitted source bytes')
        result[name]=hashlib.sha256(data).hexdigest()
    return result


def check_input(binding,expected):
    if set(binding['files'])!=set(expected) or {k:sha(v) for k,v in binding['files'].items()}!=expected:
        raise ValueError('Frozen input identity differs')


def check_binding_layout(cid,binding):
    if cid=='wcsf-used-match':return
    paths=list(binding['files'].values())
    features=[Path(p) for p in paths if str(p).endswith('.features.npz')]
    if len(features)!=1:raise ValueError('Exactly one cache feature prefix required')
    prefix=str(features[0])[:-len('.features.npz')]
    for suffix in ('.metadata.json','.features.npz','.reference.npz'):
        expected=Path(prefix+suffix)
        actual=[Path(p) for p in paths if str(p).endswith(suffix)]
        if actual!=[expected]:raise ValueError('Cache sidecar path differs from consumed sibling')


def bind_freeze_identity(public,private,source_commit):
    write_new(Path(private)/'freeze-identity.json',dict(freeze_sha256=sha(Path(public)/'freeze.json'),
        input_map_sha256=sha(Path(private)/'input-map.json'),source_commit=source_commit))


def verify_freeze_identity(public,private,frozen):
    identity=read(Path(private)/'freeze-identity.json')
    expected=dict(freeze_sha256=sha(Path(public)/'freeze.json'),input_map_sha256=sha(Path(private)/'input-map.json'),source_commit=frozen['source_commit'])
    if identity!=expected:raise ValueError('Original freeze/map identity changed')


def check_committed_documents(commit,expected):
    for name,digest in expected.items():
        data=subprocess.check_output(['git','show',commit+':'+name],cwd=ROOT)
        if hashlib.sha256(data).hexdigest()!=digest:raise ValueError('Document bytes absent from source commit')


def preflight_control_labels(records,private):
    exact_records(records)
    expected={r['case_id']+'-'+r['regime']+'.labels' for r in records}
    folder=Path(private)/'control-labels'
    if not folder.is_dir() or {p.name for p in folder.iterdir()}!=expected:raise ValueError('Private control label inventory differs')
    for row in records:
        load_control_labels(folder/(row['case_id']+'-'+row['regime']+'.labels'),row['labels_sha256'],row['control']['support']['frames'])


def store_provisional(private,phase,key,row):
    if phase not in LIMITS or not re.fullmatch('[A-Za-z0-9-]+',key):raise ValueError('Invalid provisional key')
    write_new(Path(private)/'provisional'/phase/(key+'.json'),row)


def verify_provisionals(private,phase,records):
    expected={r['case_id']+'-'+r['regime']+'.json' for r in records}
    folder=Path(private)/'provisional'/phase
    if not folder.is_dir() or {p.name for p in folder.iterdir()}!=expected:raise ValueError('Provisional receipt inventory differs')
    for row in records:
        if read(folder/(row['case_id']+'-'+row['regime']+'.json'))!=row:raise ValueError('Completed aggregate changed')


def claim(directory,phase,key):
    if phase not in LIMITS or not re.fullmatch('[A-Za-z0-9-]+',key):raise ValueError('Invalid gap claim')
    folder=Path(directory)/'claims'/phase;folder.mkdir(parents=True,exist_ok=True)
    if len(list(folder.iterdir()))>=LIMITS[phase]:raise ValueError('Gap budget exhausted')
    write_new(folder/(key+'.json'),dict(key=key,utc=datetime.now(timezone.utc).isoformat()))


def keys():return sorted(cid+'-'+regime for cid,_,_ in MATCHES for regime in REGIMES)


def exact_records(records,matches=None):
    matches=MATCHES if matches is None else matches
    expected={(cid,r) for cid,_,_ in matches for r in REGIMES}
    actual=[(r['case_id'],r['regime']) for r in records]
    if len(actual)!=len(expected) or set(actual)!=expected:raise ValueError('Exact paired case inventory required')


def provider_scores(records,variant,matches=None):
    matches=MATCHES if matches is None else matches
    exact_records(records,matches);roles={cid:(cohort,role) for cid,cohort,role in matches};out={}
    for regime in REGIMES:
        groups=defaultdict(list)
        for row in records:
            cid=row['case_id'];cohort,role=roles[cid]
            if row['regime']==regime and role=='fit-disjoint':groups[cohort].append(row[variant]['metrics']['spell_f1_mean'])
        if set(groups)!={'skillcorner','dfl','wcsf'}:raise ValueError('All primary providers required')
        out[regime]={p:fsum(v)/len(v) for p,v in groups.items()}
    return out


def primary(provider_means):return {r:fsum(values.values())/len(values) for r,values in provider_means.items()}


def within_loss(candidate,control,limit):
    boundary=control-limit
    return candidate>=boundary or isclose(candidate,boundary,rel_tol=0,abs_tol=4*max(ulp(candidate),ulp(control),ulp(boundary)))


def harm_gate(control,candidate):
    a,b=primary(control)['natural'],primary(candidate)['natural']
    per_provider={p:within_loss(candidate['natural'][p],control['natural'][p],.01) for p in ('skillcorner','dfl','wcsf')}
    main=within_loss(b,a,.005)
    return dict(passed=main and all(per_provider.values()),primary_pass=main,provider_pass=per_provider,
        natural_primary_delta=b-a,natural_provider_deltas={p:candidate['natural'][p]-control['natural'][p] for p in per_provider},
        masked_is_descriptive_only=True)


def load_control_labels(path,expected,n):
    if sha(path)!=expected:raise ValueError('Stored control labels changed')
    value=Path(path).read_bytes()
    if len(value)!=n or any(v not in b'HADX' for v in value):raise ValueError('Invalid stored control labels')
    return tuple(value.decode('ascii'))


def runtime():
    import numpy,pandas
    return dict(python=platform.python_version(),numpy=numpy.__version__,pandas=pandas.__version__,executable_sha256=sha(sys.executable))


def external_regimes(frames):
    from gap_solver.temporal_selection import contiguous_mask
    from gap_solver.temporal import mask_motion_frames
    yield 'natural',frames
    yield REGIMES[1],mask_motion_frames(frames,contiguous_mask([f.period for f in frames],.3,1729))


def freeze():
    import memory_ablation_protocol as p
    if PRIVATE.exists() or (PUBLIC/'freeze.json').exists():raise FileExistsError('New gap experiment already exists')
    kept=preservation()
    if not kept['unchanged']:raise ValueError('Historical archive changed')
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    sources=source_hashes(head);bindings=p.input_bindings(ROOT)['evaluation']
    for cid,b in bindings.items():
        check_binding_layout(cid,b);check_input(b,b['expected'])
    value=dict(schema_version=1,experiment='gap-liveness-2026-11-10',base=BASE,source_commit=head,
        source_sha256=sources,document_sha256={name:sha(ROOT/name) for name in SPECS},runtime=runtime(),
        input_sha256={cid:b['expected'] for cid,b in bindings.items()},regimes=REGIMES,limits=LIMITS,
        cases={cid:dict(provider=p,role=role) for cid,p,role in MATCHES},
        parameters=dict(long_gap_strictly_over=75,speed_baseline=25,sample_step=5,discard_speed_at_least=12,minimum_players=10,restart_speed_max=.5,restart_frames_max=250),
        gates=dict(natural_primary_max_loss=.005,natural_provider_max_loss=.01,masked_gates=False),
        expected_control=dict(natural=.551816,**{REGIMES[1]:.469149}),
        preservation=kept,created_utc=datetime.now(timezone.utc).isoformat(),fresh_holdout=False,
        automatic_promotion=False,metrica_and_challenge_dependent_on_external_pass=True,
        probe_json_verified=False,written_aggregates_authorized=True,scaling_test_cap_eligibility_preserved=True)
    PRIVATE.mkdir(parents=True)
    write_new(PRIVATE/'input-map.json',{cid:{k:str(v) for k,v in b['files'].items()} for cid,b in bindings.items()})
    write_new(PUBLIC/'freeze.json',value)
    bind_freeze_identity(PUBLIC,PRIVATE,head)
    return dict(status='frozen_before_scoring_commit_required',cases=15,limits=LIMITS,preserved_files=kept['files'])


def checked(allow_additive_sources=False):
    value=read(PUBLIC/'freeze.json')
    verify_freeze_identity(PUBLIC,PRIVATE,value)
    committed=subprocess.check_output(['git','show','HEAD:reports/gap-liveness/freeze.json'],cwd=ROOT)
    if committed!=(PUBLIC/'freeze.json').read_bytes():raise ValueError('Freeze not committed')
    freeze_commit=subprocess.check_output(['git','log','-1','--format=%H','--','reports/gap-liveness/freeze.json'],cwd=ROOT,text=True).strip()
    if source_hashes(freeze_commit)!=value['source_sha256'] or source_hashes(value['source_commit'])!=value['source_sha256']:raise ValueError('Frozen source identity differs')
    if subprocess.run(['git','merge-base','--is-ancestor',value['source_commit'],freeze_commit],cwd=ROOT,capture_output=True).returncode:raise ValueError('Source revision is not an ancestor of the freeze')
    current=set(subprocess.check_output(['git','ls-files','*.py'],cwd=ROOT,text=True).splitlines())
    untracked=subprocess.check_output(['git','ls-files','--others','--exclude-standard','*.py'],cwd=ROOT,text=True).splitlines()
    if untracked or not set(value['source_sha256'])<=current or not allow_additive_sources and current!=set(value['source_sha256']):raise ValueError('Scientific source inventory changed')
    check_committed_documents(value['source_commit'],value['document_sha256'])
    kept=preservation()
    if not kept['unchanged']:raise ValueError('Historical archive changed before phase entry')
    if runtime()!=value['runtime'] or {name:sha(ROOT/name) for name in SPECS}!=value['document_sha256']:
        raise ValueError('Frozen runtime/documents differ')
    if value['limits']!=LIMITS or value['regimes']!=list(REGIMES):raise ValueError('Frozen protocol differs')
    mapping=read(PRIVATE/'input-map.json')
    if set(mapping)!=set(value['cases']):raise ValueError('Input case inventory differs')
    bindings={cid:dict(files={k:Path(v) for k,v in b.items()}) for cid,b in mapping.items()}
    for cid,b in bindings.items():
        check_binding_layout(cid,b);check_input(b,value['input_sha256'][cid])
    return value,bindings,freeze_commit


def control_summary(records,frozen,commit):
    providers=provider_scores(records,'control');means=primary(providers)
    return dict(freeze_commit=commit,freeze_sha256=sha(PUBLIC/'freeze.json'),providers=providers,primary=means,
        expected=frozen['expected_control'],passed=all(round(means[r],6)==frozen['expected_control'][r] for r in REGIMES),scoring_calls=len(records))


def verify_control(frozen,commit):
    records=seal_phase(PUBLIC,PRIVATE,'control','control-reproduction.json',keys(),commit)
    actual=control_summary(records,frozen,commit)
    if read(PUBLIC/'control-reproduction.json')!=actual or not actual['passed']:raise ValueError('Control reproduction not proven')
    exact_records(records)
    verify_provisionals(PRIVATE,'control',records)
    return records


def controls():
    frozen,bindings,commit=checked()
    from memory_ablation_run import load_evaluation
    from release_runtime import predict_selected
    write_new(PRIVATE/'control-entry.json',dict(freeze_commit=commit))
    records=[]
    for cid,provider,role in MATCHES:
        check_input(bindings[cid],frozen['input_sha256'][cid]);case=load_evaluation(cid,bindings[cid]);pending=[]
        for regime,frames in external_regimes(case['frames']):
            key=cid+'-'+regime;claim(PRIVATE,'control',key)
            labels=predict_selected(frames).labels;result=score(case['reference'](),labels,frames)
            data=''.join(labels).encode('ascii')
            private=PRIVATE/'control-labels'/(key+'.labels');private.parent.mkdir(parents=True,exist_ok=True)
            row=dict(case_id=cid,provider=provider,role=role,regime=regime,control=result,labels_sha256=hashlib.sha256(data).hexdigest(),
                freeze_commit=commit,freeze_sha256=sha(PUBLIC/'freeze.json'))
            store_provisional(PRIVATE,'control',key,row)
            prior=read(ROOT/'reports/touch-evidence/control'/(key+'.json'))['control']
            if result!=prior:raise ValueError('Historical control count/metric parity failed')
            with private.open('xb') as handle:handle.write(data)
            records.append(row);pending.append((key,row))
            print(json.dumps(dict(stage='control',completed=len(records),maximum=30,case_id=cid,regime=regime)),flush=True)
        check_input(bindings[cid],frozen['input_sha256'][cid])
        for key,row in pending:write_new(PUBLIC/'control'/(key+'.json'),row)
    verify_provisionals(PRIVATE,'control',records)
    summary=control_summary(records,frozen,commit);write_new(PUBLIC/'control-reproduction.json',summary)
    seal_phase(PUBLIC,PRIVATE,'control','control-reproduction.json',keys(),commit,create=True)
    if not summary['passed']:raise ValueError('Control reproduction failed')
    return summary


def rule_summary(records,commit):
    a=provider_scores(records,'control');b=provider_scores(records,'candidate');gate=harm_gate(a,b)
    counts=[]
    for regime in REGIMES:
        for provider in ('skillcorner','dfl','wcsf'):
            for role in ('fit-disjoint','fitting-overlap'):
                group=[r['gap'] for r in records if r['regime']==regime and r['provider']==provider and r['role']==role]
                if not group:continue
                counts.append(dict(provider=provider,role=role,regime=regime,matches=len(group),
                    **{k:sum(r[k] for r in group) for k in ('long_gaps','stoppage_gaps','long_gap_frames','stoppage_gap_frames','restart_extension_frames','frames_relabelled')}))
    return dict(freeze_commit=commit,freeze_sha256=sha(PUBLIC/'freeze.json'),control_providers=a,candidate_providers=b,
        control_primary=primary(a),candidate_primary=primary(b),gate=gate,provider_gap_counts=counts,
        decision='Pass external harm gate' if gate['passed'] else 'Reject gap rule',scoring_calls=len(records),
        fresh_holdout=False,automatic_promotion=False,challenge_generation_performed=False)


def rule():
    frozen,bindings,commit=checked();controls=verify_control(frozen,commit)
    preflight_control_labels(controls,PRIVATE)
    lookup={(r['case_id'],r['regime']):r for r in controls}
    from memory_ablation_run import load_evaluation
    from gap_liveness import apply_gap_rule
    write_new(PRIVATE/'rule-entry.json',dict(freeze_commit=commit));records=[]
    for cid,provider,role in MATCHES:
        check_input(bindings[cid],frozen['input_sha256'][cid]);case=load_evaluation(cid,bindings[cid]);pending=[]
        for regime,frames in external_regimes(case['frames']):
            key=cid+'-'+regime;control=lookup[(cid,regime)]
            labels=load_control_labels(PRIVATE/'control-labels'/(key+'.labels'),control['labels_sha256'],len(frames))
            claim(PRIVATE,'rule',key);prediction=apply_gap_rule(frames,labels)
            result=score(case['reference'](),prediction.labels,frames)
            row=dict(case_id=cid,provider=provider,role=role,regime=regime,control=control['control'],candidate=result,
                gap=prediction.summary,labels_sha256=hashlib.sha256(''.join(prediction.labels).encode()).hexdigest(),
                freeze_commit=commit,freeze_sha256=sha(PUBLIC/'freeze.json'))
            store_provisional(PRIVATE,'rule',key,row)
            records.append(row);pending.append((key,row))
            print(json.dumps(dict(stage='rule',completed=len(records),maximum=30,case_id=cid,regime=regime)),flush=True)
        check_input(bindings[cid],frozen['input_sha256'][cid])
        for key,row in pending:write_new(PUBLIC/'rule'/(key+'.json'),row)
    verify_provisionals(PRIVATE,'rule',records)
    summary=rule_summary(records,commit);write_new(PUBLIC/'external-results.json',summary)
    seal_phase(PUBLIC,PRIVATE,'rule','external-results.json',keys(),commit,create=True)
    return summary


def audit():
    frozen,bindings,commit=checked(allow_additive_sources=True);controls=verify_control(frozen,commit)
    preflight_control_labels(controls,PRIVATE)
    records=seal_phase(PUBLIC,PRIVATE,'rule','external-results.json',keys(),commit)
    verify_provisionals(PRIVATE,'rule',records)
    summary=rule_summary(records,commit)
    if summary!=read(PUBLIC/'external-results.json'):raise ValueError('Rule summary mismatch')
    lookup={(r['case_id'],r['regime']):r for r in controls}
    for row in records:
        baseline=lookup[(row['case_id'],row['regime'])]
        if row['control']!=baseline['control']:raise ValueError('Paired control changed')
        load_control_labels(PRIVATE/'control-labels'/(row['case_id']+'-'+row['regime']+'.labels'),baseline['labels_sha256'],row['control']['support']['frames'])
    counts={p:len(list((PRIVATE/'claims'/p).glob('*.json'))) for p in LIMITS}
    if counts!=LIMITS:raise ValueError('Claim counts differ')
    kept=preservation()
    if not kept['unchanged']:raise ValueError('Historical source archive changed')
    return dict(verified=True,decision=summary['decision'],freeze_commit=commit,claims=counts,preservation=kept,extra_inference_or_scoring_calls=0)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('stage',choices=('freeze','control','rule','audit'));args=parser.parse_args()
    actions=dict(freeze=freeze,control=controls,rule=rule,audit=audit)
    try:result=actions[args.stage]()
    except Exception as error:
        PRIVATE.mkdir(parents=True,exist_ok=True)
        import traceback
        filename=args.stage+'-failure-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')+'.log'
        with (PRIVATE/filename).open('x',encoding='utf-8') as handle:traceback.print_exc(file=handle)
        raise SystemExit('Gap stage stopped: '+type(error).__name__+'; private failure retained, no retry or budget reset.') from None
    print(json.dumps(result,sort_keys=True,allow_nan=False),flush=True)

if __name__=='__main__':main()
