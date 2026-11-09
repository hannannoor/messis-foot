"""Exclusive, hash-bound replay of five already-used possession cases.

Only aggregate receipts leave the private generation. Verification is read-only.
"""
import argparse
import ast
from datetime import datetime,timezone
import hashlib
import json
from math import isfinite,isclose
from pathlib import Path
import platform
import re
import sqlite3
import subprocess
import sys
import numpy as np

from accuracy_evidence import assert_public_report
from gap_solver.input_contract import reject_linked_ancestors
from gap_solver.tactical_model import FROZEN_MODEL
from ownership_diagnosis import prepare_inference,analyze_case,check_parity,FAMILIES

ROOT=Path(__file__).resolve().parent
CASE_IDS=('skillcorner-1874553','skillcorner-1886347','dfl-J03WOH','dfl-J03WOY','wcsf-used-match')
ENTRIES=('ownership_paths.py','ownership_diagnosis.py','ownership_run.py')
VARIANTS=('baseline_metric','supported_liveness_repair','supported_ownership_repair')
MODEL='363c45c70838b398cd87aee7474d7e281fd392f059a31b85712e312058aaab4d'
PROTECTED={
 'competition_release.py':'e8d35e15be9524270bed82352791dc2849087b49b4c2b59c191023954b19eddb',
 'docs/superpowers/specs/2026-11-08-ownership-path-diagnosis-design.md':'bddff762f6539b5d0966cd467ea39417f254bf3f1511ced8146f199e072122c9',
 'docs/superpowers/plans/2026-11-08-ownership-path-diagnosis.md':'54e3465bba5bb822b4e6f478b484c3caf52f6f780900a3c8c42960c720fcd65a'}
PILOT_SHA='a3895724e6e744f47ab130df50e67dcad85011361127857a2f484a5dbb2fa3a8'
WCSF_SHA={
 'geometry.sqlite':'951f4e6d91c0706654181874e116932db345f16094108ba8dfcc1fd4264ce6c3',
 'reference.sqlite':'39465638737add82029468a4d292a71317f702e05dbc4fdd6bd58100171fb398',
 'predictions/canonical-index.npy':'f2beb04bea227e45e9d45ff01fadebf6d8a9cf150cba59d9479f47fe818cb68b',
 'predictions/w0-c32-neutral-missing.npy':'f95290360906c060b206ae9a492b19edd273f126cb85cc38e649b7f9aaa28ec9'}


def _bytes(value):return (json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
def _digest(value):return hashlib.sha256(_bytes(value)).hexdigest()
def _read(path):return json.loads(Path(path).read_text(encoding='utf-8'))


def _sha(path):
    reject_linked_ancestors(path)
    h=hashlib.sha256()
    with Path(path).open('rb') as handle:
        for block in iter(lambda:handle.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def _write_new(path,value):
    reject_linked_ancestors(path)
    with Path(path).open('xb') as handle:handle.write(_bytes(value))


def _hashes(paths):return {name:_sha(path) for name,path in sorted(paths.items())}
def _utc():return datetime.now(timezone.utc).isoformat()


def _environment():
    import pandas as pd
    return dict(python=platform.python_version(),numpy=np.__version__,pandas=pd.__version__,sqlite=sqlite3.sqlite_version,platform=platform.platform())


def _release_components(root):
    tree=ast.parse((root/'competition_release.py').read_text(encoding='utf-8'))
    manifest=next(ast.literal_eval(node.value) for node in tree.body if isinstance(node,ast.Assign)
        and any(isinstance(name,ast.Name) and name.id=='MANIFEST' for name in node.targets))
    if manifest['model_sha256']!=MODEL or _hashes({name:root/name for name in manifest['sources']})!=manifest['sources']:
        raise ValueError('Executed release component differs from pinned artifact')


def _sources(root):
    """Resolve local import closure, including lazy adapter imports and packages."""
    root=Path(root);found={};pending=[root/name for name in ENTRIES]
    while pending:
        path=pending.pop()
        if not path.is_file():raise ValueError('Missing source entry')
        logical=path.relative_to(root).as_posix()
        if logical in found:continue
        found[logical]=path
        package=logical.split('/')[:-1]
        for node in ast.walk(ast.parse(path.read_text(encoding='utf-8-sig'))):
            names=[]
            if isinstance(node,ast.Import):names=[alias.name.split('.') for alias in node.names]
            elif isinstance(node,ast.ImportFrom):
                base=(package[:len(package)-node.level+1] if node.level else [])+(node.module.split('.') if node.module else [])
                names=[base]+[base+[alias.name] for alias in node.names if alias.name!='*']
            for parts in names:
                for size in range(1,len(parts)+1):
                    stem=root.joinpath(*parts[:size])
                    for candidate in (stem.with_suffix('.py'),stem/'__init__.py'):
                        if candidate.is_file() and candidate.relative_to(root).as_posix() not in found:pending.append(candidate)
    for name in tuple(PROTECTED)+('benchmark/frozen/tactical-selected.json','benchmark/ball-gap/selected.json','release/manifest.json',
            'docs/superpowers/specs/2026-11-09-all-state-path-diagnosis-addendum.md',
            'docs/superpowers/plans/2026-11-09-all-state-path-diagnosis.md',
            'benchmark/frozen/freeze-manifest.json','reports/wcsf-transfer-v2/acquisition.json',
            'reports/wcsf-transfer-v2/geometry.json','reports/wcsf-transfer-v2/predictions-seal.json',
            'reports/wcsf-transfer-v2/results.json'):
        if not (root/name).is_file():raise ValueError('Required protocol identity missing')
        found[name]=root/name
    return found


def _git_commit(root):
    return subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()


def _bindings(root):
    root=Path(root);pilot=root.parent/'next-phase-notes/ownership-council/development-diagnosis.json'
    if _sha(pilot)!=PILOT_SHA:raise ValueError('Prior pilot identity changed')
    cases=_read(pilot)['cases'];result={}
    for old in cases:
        cohort=old['cohort'];match=str(old['match']);cid=cohort+'-'+match
        if cid not in CASE_IDS or cid in result or old['regime']!='natural':raise ValueError('Prior cohort changed')
        directory=root.parent/('independent-reference' if cohort=='skillcorner' else 'external-reference')
        prefix=directory/'cache'/(match+'-detected' if cohort=='skillcorner' else match)
        files={cid+'/'+name:Path(str(prefix)+name) if name.startswith('.') else directory/'raw'/name
               for name in old['input_sha256']}
        parity={k:old['strata']['all_known_live'][k] for k in ('frames','wrong_team','raw_correct_final_wrong','raw_wrong_final_correct')}
        files[cid+'/prior-pilot']=pilot
        result[cid]=dict(cohort=cohort,files=files,
            expected={**{cid+'/'+k:v for k,v in old['input_sha256'].items()},cid+'/prior-pilot':PILOT_SHA},parity={'pilot':parity})
    directory=root.parent/'wcsf-reference/wcsf-2026-11-09-2';cid=CASE_IDS[-1]
    if _sha(root/'reports/wcsf-transfer-v2/results.json')!='16297acd3e3d176f06ad105575f89d3ecf3818e9ee874a02bafde2cf70c8694d':
        raise ValueError('Prior WCSF result changed')
    prior=_read(root/'reports/wcsf-transfer-v2/results.json')['match']['w0-c32-neutral-missing']['spells']
    result[cid]=dict(cohort='wcsf',files={cid+'/'+name:directory/name for name in WCSF_SHA},
        expected={cid+'/'+k:v for k,v in WCSF_SHA.items()},parity={'wcsf':dict(frames=143431,known=143165,
            n_gt=411,n_pred=490,n_matched=233,n_missed=178,n_spurious=257,mean_f1=prior['mean_f1'],
            per_iou={t:{k:row[k] for k in ('n_matched','n_missed','n_spurious','f1')} for t,row in prior['per_iou'].items()})})
    return result


def _load_case(case_id,binding):
    if case_id!=CASE_IDS[-1]:
        from cadence_experiment import load_case
        cohort,match=case_id.split('-',1);data=load_case(cohort,match)
        # Assert that the old adapter used precisely the frozen inventory.
        actual={str(p.resolve()) for p in data.input_paths.values()}
        expected={str(p.resolve()) for k,p in binding['files'].items() if not k.endswith('/prior-pilot')}
        if actual!=expected:raise ValueError('Adapter consumed unexpected files')
        return dict(frames=data.frames,reference=lambda:data.reference,validate=lambda trace:None,reference_loaded_by_adapter=True)
    from wcsf_geometry import canonical_input,GeometryDecision
    from wcsf_reference import reference_codes
    files=binding['files'];get=lambda name:files[case_id+'/'+name]
    decision=GeometryDecision('absolute-xy',57374,{'absolute-x':233,'absolute-xy':57374,'offset-x':0,'offset-xy':0},None)
    data=canonical_input(get('geometry.sqlite'),decision)
    index=np.load(get('predictions/canonical-index.npy'),allow_pickle=False)
    if not np.array_equal(np.asarray(data.index),index):raise ValueError('Original WCSF index parity failed')
    def validate(trace):
        sealed=np.load(get('predictions/w0-c32-neutral-missing.npy'),allow_pickle=False)
        actual=np.asarray(['HADX'.index(s) for s in trace.final],dtype=np.uint8)
        if not np.array_equal(actual,sealed):raise ValueError('Original WCSF prediction parity failed')
    return dict(frames=data.frames,reference=lambda:reference_codes(get('reference.sqlite'),data.index),
                validate=validate,reference_loaded_by_adapter=False)


# Owned recursive schema: unknown keys and all unapproved array shapes fail.
def _shape(value,schema):
    if isinstance(schema,dict):
        if not isinstance(value,dict) or set(value)!=set(schema):raise ValueError('Unexpected aggregate keys')
        for key,sub in schema.items():_shape(value[key],sub)
        return
    if schema=='count':ok=type(value) is int and value>=0
    elif schema=='integer':ok=type(value) is int
    elif schema=='number':ok=type(value) in (int,float) and isfinite(value)
    elif schema=='nullable':ok=value is None or type(value) in (int,float) and isfinite(value)
    elif schema=='hash':ok=isinstance(value,str) and re.fullmatch('[0-9a-f]{64}',value)
    elif schema=='bool':ok=type(value) is bool
    elif schema=='confusion':
        ok=isinstance(value,list) and len(value)==4 and all(isinstance(row,list) and len(row)==4 and all(type(x) is int and x>=0 for x in row) for row in value)
    elif isinstance(schema,tuple):ok=value in schema and type(value) is type(schema[0])
    else:raise ValueError('Unknown schema')
    if not ok:raise ValueError('Invalid aggregate scalar or shape')


COUNT3={k:'count' for k in ('no_same_team_overlap','below_threshold_overlap','qualifying_consumed')}
IOU_SCHEMA=dict(n_matched='count',n_missed='count',n_spurious='count',f1='nullable',unmatched_gt=COUNT3,unmatched_pred=COUNT3)
SPELL_SCHEMA=dict(n_gt='count',n_pred='count',split_reference_spells='count',merge_prediction_spells='count',
    per_iou={str(t):IOU_SCHEMA for t in (.3,.4,.5,.6,.7)},mean_f1='nullable')
METRICS={k:'nullable' for k in ('accuracy','official_macro_f1','spell_f1_mean')}
STATS=dict(n='count',total='number',minimum='nullable',maximum='nullable',positive='count',negative='count',near_zero='count')
FAMILY=dict(frames='count',episodes='count',objective_classes={k:dict(episodes='count',frames='count') for k in
    ('wrong_emission_preference','switch_penalty_blocks_reference','numerical_tie','mixed_or_nonlocal')},
    margins={k:STATS for k in ('prefix_before','local','future','full','emission_margin','switch_margin')},
    local_reference_favoring_frames='count',local_wrong_favoring_frames='count',future_reversal_frames='count',numerical_tie_frames='count',
    patch_emission_gain='number',patch_additional_switches='integer',patch_objective_gain='number',
    duration=dict(median_s='nullable',p90_s='nullable',max_s='nullable',frames_in_episodes_at_least2s='count'))
BOUNDARY={**{k:'count' for k in ('n_gt','n_pred','n_matched','n_missed','n_spurious','n_ambiguous','matched_latency_denominator')},
    **{k:'nullable' for k in ('precision','recall','f1','mean_latency_frames','mean_abs_latency_frames')}}
QUERY=dict(frames='count',numerical_tie_frames='count',margins={k:STATS for k in ('prefix_before','local','future','full','emission_margin','switch_margin')})
DIAGNOSTIC=dict(schema_version=(2,),support={k:'count' for k in ('frames','known','unknown','H','A','D')},
    input_segments='count',input_path_sha256='hash',exact_recurrence_ties='count',supported_error_frames='count',
    carried_known_frames='count',carried_error_frames='count',families={k:FAMILY for k in FAMILIES},
    agreement={k:QUERY for k in 'HAD'},legacy_HA_queries={**QUERY,'selected_D_frames':'count'},
    baseline=dict(metrics=METRICS,spells=SPELL_SCHEMA,confusion='confusion'),
    counterfactuals={k:dict(diagnostic_only=(True,),changed_rows='count',spell_f1_delta='nullable',metrics=METRICS,spells=SPELL_SCHEMA) for k in VARIANTS[1:]},
    pilot_parity={k:'count' for k in ('frames','wrong_team','raw_correct_final_wrong','raw_wrong_final_correct')},
    HA_boundaries={str(t):BOUNDARY for t in (12,25)},all_state_boundaries={str(t):BOUNDARY for t in (12,25)},
    policy_counts={k:'count' for k in ('neutral_active_usable_rows','unsupported_segments','unsupported_active_rows')},
    strata={k:{**{field:'count' for field in ('frames','known_live_frames','supported_errors','carried_errors','ownership_swaps',
        'usable_frames','unusable_frames','memory_evaluable_ownership_swaps','ownership_swaps_with_opposed_memory')},
        'reference_state_support':{state:'count' for state in 'HAD'},
        'family_emission_evidence':{name:{field:'count' for field in ('frames','local_reference_favoring','local_wrong_favoring','local_near_zero')} for name in FAMILIES}}
        for k in ('all_known','ball_observed','ball_missing','near_boundary_2s','near_annotation_edge_2s','observed_interior_beyond2s')})


def _close(a,b):
    if a is None or b is None:return a is b
    return isclose(a,b,abs_tol=1e-12,rel_tol=1e-10)


def _spell_counts(spells,known):
    scores=[]
    for row in spells['per_iou'].values():
        tp,fp,fn=(row[k] for k in ('n_matched','n_spurious','n_missed'))
        if tp+fn!=spells['n_gt'] or tp+fp!=spells['n_pred']:raise ValueError('Spell counts do not reconcile')
        if sum(row['unmatched_gt'].values())!=fn or sum(row['unmatched_pred'].values())!=fp:raise ValueError('Unmatched partitions differ')
        score=(2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0.) if known else None
        if not _close(row['f1'],score):raise ValueError('Spell F1 differs')
        if score is not None:scores.append(score)
    if not _close(spells['mean_f1'],sum(scores)/len(scores) if scores else None):raise ValueError('Mean spell F1 differs')


def validate_case_report(value,expected_input_sha256):
    if not isinstance(value,dict):raise ValueError('Case receipt must be a dictionary')
    expected=dict(schema_version=(1,),case_id=CASE_IDS,freeze_sha256='hash',input_sha256={k:'hash' for k in expected_input_sha256},
        trace_container_sha256='hash',trace_semantic_sha256='hash',diagnostic=DIAGNOSTIC,parity_passed=(True,),
        evaluation_counts={k:(1,) for k in VARIANTS})
    _shape(value,expected);assert_public_report(value)
    if value['input_sha256']!=expected_input_sha256:raise ValueError('Input identity differs from trusted case binding')
    d=value['diagnostic'];s=d['support'];cm=d['baseline']['confusion']
    if s['known']+s['unknown']!=s['frames'] or s['H']+s['A']+s['D']!=s['known']:raise ValueError('Support counts differ')
    if [sum(row) for row in cm]!=[s[k] for k in ('H','A','D','unknown')]:raise ValueError('Confusion support differs')
    errors=sum(sum(row)-row[i] for i,row in enumerate(cm[:3]))
    if d['supported_error_frames']+d['carried_error_frames']!=errors:raise ValueError('Error attribution differs')
    if sum(row['frames'] for row in d['families'].values())!=d['supported_error_frames']:raise ValueError('Families differ')
    for row in d['families'].values():
        if sum(c['episodes'] for c in row['objective_classes'].values())!=row['episodes'] or sum(c['frames'] for c in row['objective_classes'].values())!=row['frames']:raise ValueError('Episode totals differ')
        for stat in row['margins'].values():
            if stat['n']!=row['frames'] or stat['positive']+stat['negative']+stat['near_zero']!=stat['n']:raise ValueError('Margin support differs')
    _spell_counts(d['baseline']['spells'],s['known'])
    for name,row in d['counterfactuals'].items():
        _spell_counts(row['spells'],s['known'])
        old=d['baseline']['spells']['mean_f1'];new=row['spells']['mean_f1']
        if not _close(row['spell_f1_delta'],new-old if old is not None else None):raise ValueError('Counterfactual delta differs')
        changed=sum(d['families'][k]['frames'] for k in (('missed_D','false_D') if name==VARIANTS[1] else ('ownership_swap',)))
        if row['changed_rows']!=changed:raise ValueError('Repair eligibility differs')
    for query in list(d['agreement'].values())+[d['legacy_HA_queries']]:
        if query['numerical_tie_frames']>query['frames']:raise ValueError('Query tie support differs')
        for stat in query['margins'].values():
            if stat['n']!=query['frames'] or stat['positive']+stat['negative']+stat['near_zero']!=stat['n']:raise ValueError('Query support differs')
    for row in d['strata'].values():
        if row['usable_frames']+row['unusable_frames']!=row['frames'] or sum(row['reference_state_support'].values())!=row['frames']:raise ValueError('Stratum support differs')
        if row['ownership_swaps_with_opposed_memory']>row['memory_evaluable_ownership_swaps'] or row['memory_evaluable_ownership_swaps']>row['ownership_swaps']:raise ValueError('Swap-memory support differs')
        for family in row['family_emission_evidence'].values():
            if family['local_reference_favoring']+family['local_wrong_favoring']+family['local_near_zero']!=family['frames']:raise ValueError('Stratum emission signs differ')
        if sum(f['frames'] for f in row['family_emission_evidence'].values())!=row['supported_errors']:raise ValueError('Stratum families differ')
    for row in list(d['HA_boundaries'].values())+list(d['all_state_boundaries'].values()):
        if row['n_matched']+row['n_missed']!=row['n_gt'] or row['n_matched']+row['n_spurious']!=row['n_pred'] or row['matched_latency_denominator']!=row['n_matched']:raise ValueError('Boundary counts differ')
    return value


def _trace_arrays(trace):
    code=lambda labels:np.asarray(['HADX'.index(s) for s in labels],dtype=np.uint8)
    return dict(emissions=np.asarray(trace.emissions,dtype='<f8'),periods=np.asarray(trace.periods,dtype=np.uint8),
        observed=np.asarray(trace.observed,dtype=np.uint8),usable=np.asarray(trace.usable,dtype=np.uint8),
        latent=code(trace.latent),final=code(trace.final),raw_codes=np.asarray(trace.raw_codes,dtype=np.uint8),
        memory_owner=np.asarray(trace.memory_owner,dtype=np.uint8),memory_age=np.asarray(trace.memory_age,dtype='<f8'),
        segments=np.asarray(trace.segments,dtype='<i8').reshape(-1,2))


def _semantic(arrays):
    h=hashlib.sha256(b'ownership-trace-v1\n')
    for key,value in sorted(arrays.items()):
        h.update(_bytes(dict(name=key,dtype=value.dtype.str,shape=list(value.shape))))
        h.update(value.tobytes(order='C'))
    return h.hexdigest()


class DiagnosisSession:
    def __init__(self,run_id,root=ROOT):
        if not isinstance(run_id,str) or not re.fullmatch('[a-z0-9][a-z0-9-]{0,63}',run_id) or run_id.upper() in {'CON','PRN','AUX','NUL',*('COM'+str(n) for n in range(1,10)),*('LPT'+str(n) for n in range(1,10))}:
            raise ValueError('Unsafe run ID')
        self.root=Path(root).resolve();self.run_id=run_id
        self.public=self.root/'reports/ownership-path'/run_id
        self.private=self.root.parent/'ownership-reference'/run_id
        reject_linked_ancestors(self.public);reject_linked_ancestors(self.private)

    def _current(self):
        model_bytes=json.dumps(FROZEN_MODEL['model'],sort_keys=True,separators=(',',':'),allow_nan=False).encode()
        if hashlib.sha256(model_bytes).hexdigest()!=MODEL:raise ValueError('Frozen model changed')
        if _hashes({k:self.root/k for k in PROTECTED})!=PROTECTED:raise ValueError('Released artifact or approved design changed')
        _release_components(self.root)
        sources=_sources(self.root)
        if not set(ENTRIES)<=set(sources):raise ValueError('Incomplete source inventory')
        bindings=_bindings(self.root)
        if set(bindings)!=set(CASE_IDS):raise ValueError('Exact five-case cohort required')
        for cid,b in bindings.items():
            if not b['files'] or _hashes(b['files'])!=b['expected']:raise ValueError('Prior input hashes changed')
        return sources,bindings

    def freeze(self):
        sources,bindings=self._current()
        self.private.parent.mkdir(parents=True,exist_ok=True);self.private.mkdir()
        _write_new(self.private/'.incomplete',dict(stage='freeze',utc=_utc()))
        self.public.mkdir(parents=True,exist_ok=False)
        value=dict(schema_version=1,run_id=self.run_id,created_utc=_utc(),source_git_commit=_git_commit(self.root),
            model_sha256=MODEL,source_sha256=_hashes(sources),input_sha256={cid:b['expected'] for cid,b in bindings.items()},
            case_contracts={cid:b['parity'] for cid,b in bindings.items()},
            protocol=dict(selected_id='w0-c32-neutral-missing',switch_cost=32,dead_weight=0,emission_floor=1e-6,
                state_order='H/A/D',regime='natural',fresh_holdout=False,target_data_used=False,head_fitting_performed=False,
                inference_entries=5,baseline_evaluations=5,reference_only_repair_evaluations=10,carry_eligible=False),
            environment=_environment())
        assert_public_report(value);_write_new(self.public/'freeze.json',value)
        _write_new(self.private/'freeze-anchor.json',dict(freeze_sha256=_sha(self.public/'freeze.json')))
        _write_new(self.private/'input-map.json',{cid:{k:str(p.resolve()) for k,p in b['files'].items()} for cid,b in bindings.items()})
        (self.private/'.incomplete').unlink()
        return dict(freeze_sha256=_sha(self.public/'freeze.json'),cases=5)

    def _frozen(self):
        if (self.private/'.incomplete').exists():raise ValueError('Incomplete freeze')
        freeze=_read(self.public/'freeze.json');anchor=_read(self.private/'freeze-anchor.json')
        if anchor!={'freeze_sha256':_sha(self.public/'freeze.json')}:raise ValueError('Freeze anchor changed')
        if freeze['environment']!=_environment():raise ValueError('Frozen runtime environment changed')
        sources,bindings=self._current()
        if freeze['source_sha256']!=_hashes(sources) or freeze['input_sha256']!={cid:b['expected'] for cid,b in bindings.items()} or freeze['case_contracts']!={cid:b['parity'] for cid,b in bindings.items()} or freeze['model_sha256']!=MODEL or freeze['run_id']!=self.run_id:
            raise ValueError('Frozen binding changed')
        return freeze,bindings,anchor['freeze_sha256']

    def _event(self,case_id,event,**extra):
        path=self.private/'access.jsonl'
        with path.open('ab') as handle:handle.write(_bytes(dict(case_id=case_id,event=event,utc=_utc(),**extra)))

    def run_cases(self):
        freeze,bindings,identity=self._frozen()
        cases=self.private/'cases';cases.mkdir(exist_ok=True)
        if any(cases.iterdir()):raise ValueError('Preserve prior or incomplete case attempts; use a new run ID')
        for cid in CASE_IDS:
            directory=cases/cid;directory.mkdir();_write_new(directory/'.incomplete',dict(utc=_utc()))
            self._event(cid,'adapter_entry',reference_container_may_be_parsed=cid!=CASE_IDS[-1])
            loaded=_load_case(cid,bindings[cid])
            self._event(cid,'adapter_return',reference_loaded_by_adapter=loaded['reference_loaded_by_adapter'])
            self._event(cid,'inference_entry');trace=prepare_inference(loaded['frames']);loaded['validate'](trace)
            arrays=_trace_arrays(trace)
            with (directory/'input-trace.npz').open('xb') as handle:np.savez_compressed(handle,**arrays)
            self._event(cid,'reference_codes_entry',already_parsed_by_adapter=loaded['reference_loaded_by_adapter'])
            reference=loaded['reference']()
            diagnostic=analyze_case(trace,reference,expected_parity=bindings[cid]['parity'],
                on_evaluation=lambda name:self._event(cid,'evaluation_entry',variant=name))
            self._frozen()
            receipt=dict(schema_version=1,case_id=cid,freeze_sha256=identity,input_sha256=bindings[cid]['expected'],
                trace_container_sha256=_sha(directory/'input-trace.npz'),trace_semantic_sha256=_semantic(arrays),
                diagnostic=diagnostic,parity_passed=True,evaluation_counts={name:1 for name in VARIANTS})
            validate_case_report(receipt,bindings[cid]['expected'])
            target=self.public/(cid+'.json');_write_new(target,receipt)
            if target.read_bytes()!=_bytes(receipt):raise ValueError('Persisted receipt differs')
            _write_new(directory/'complete.json',dict(report_sha256=_sha(target)))
            self._event(cid,'complete');(directory/'.incomplete').unlink()
            del loaded,trace,reference,arrays,diagnostic
        return dict(cases=5,inference_entries=5,evaluated_arrays=15)

    def _receipts(self):
        freeze,bindings,identity=self._frozen();rows={}
        cases=self.private/'cases'
        if not cases.is_dir() or {p.name for p in cases.iterdir()}!=set(CASE_IDS):raise ValueError('Incomplete or extra case attempts')
        for cid in CASE_IDS:
            directory=cases/cid
            if {p.name for p in directory.iterdir()}!={'input-trace.npz','complete.json'}:raise ValueError('Incomplete case generation')
            path=self.public/(cid+'.json');value=validate_case_report(_read(path),bindings[cid]['expected'])
            if value['case_id']!=cid or value['freeze_sha256']!=identity or value['input_sha256']!=bindings[cid]['expected'] or _read(directory/'complete.json')!={'report_sha256':_sha(path)}:raise ValueError('Case identity differs')
            if value['trace_container_sha256']!=_sha(directory/'input-trace.npz'):raise ValueError('Trace container changed')
            with np.load(directory/'input-trace.npz',allow_pickle=False) as trace:
                if value['trace_semantic_sha256']!=_semantic({k:trace[k] for k in trace.files}):raise ValueError('Trace content changed')
            d=value['diagnostic'];check_parity(d['baseline'],d['pilot_parity'],d['support'],bindings[cid]['parity'])
            rows[cid]=value
        return rows

    def _summary(self,rows):
        def group(ids):
            cases={cid:dict(known=rows[cid]['diagnostic']['support']['known'],
                spell_f1=rows[cid]['diagnostic']['baseline']['spells']['mean_f1'],
                family_frames={k:v['frames'] for k,v in rows[cid]['diagnostic']['families'].items()},
                repair_spell_f1_deltas={k:v['spell_f1_delta'] for k,v in rows[cid]['diagnostic']['counterfactuals'].items()}) for cid in ids}
            return dict(cases=cases,n_cases=len(ids),known=sum(v['known'] for v in cases.values()),fresh_holdout=False)
        value=dict(schema_version=1,freeze_sha256=_sha(self.public/'freeze.json'),case_receipt_sha256={cid:_sha(self.public/(cid+'.json')) for cid in CASE_IDS},
            original_four=group(CASE_IDS[:4]),used_wcsf_separate=group(CASE_IDS[4:]),
            method_counts=dict(inference_entries=5,baseline_evaluations=5,reference_only_repair_evaluations=10),
            limitations=['Used development evidence; cases and frames are not independent fresh samples.',
                'Reference-only signed repairs are diagnostic, not feasible predictors or additive loss fractions.',
                'Cache adapters parse reference containers before inference; pure inference and path tables receive no reference.'])
        assert_public_report(value);return value

    def summarize(self):
        rows=self._receipts();value=self._summary(rows)
        _write_new(self.public/'summary.json',value);return dict(cases=5)

    def verify(self):
        expected={'freeze.json','summary.json',*(cid+'.json' for cid in CASE_IDS)}
        if not self.public.is_dir() or {p.name for p in self.public.iterdir()}!=expected:raise ValueError('Unexpected public inventory')
        rows=self._receipts()
        if (self.public/'summary.json').read_bytes()!=_bytes(self._summary(rows)):raise ValueError('Summary bytes differ')
        events=[json.loads(line) for line in (self.private/'access.jsonl').read_text().splitlines()]
        expected=[]
        for cid in CASE_IDS:
            expected.extend((cid,name,variant) for name,variant in [('adapter_entry',None),('adapter_return',None),('inference_entry',None),('reference_codes_entry',None),
                *((('evaluation_entry',variant) for variant in VARIANTS)),('complete',None)])
        if [(e['case_id'],e['event'],e.get('variant')) for e in events]!=expected:raise ValueError('Attempt/evaluation chronology differs')
        return dict(cases=5,inference_entries=5,evaluated_arrays=15,freeze_sha256=_sha(self.public/'freeze.json'))


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('command',choices=('freeze','run','summarize','verify'));parser.add_argument('--run-id',required=True)
    args=parser.parse_args();session=DiagnosisSession(args.run_id)
    result=getattr(session,'run_cases' if args.command=='run' else args.command)()
    print(json.dumps(result,sort_keys=True))


if __name__=='__main__':main()
