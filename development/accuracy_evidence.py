"""Strict verification added around the exact preserved scoring engine."""
import json,re
from pathlib import Path,PureWindowsPath
import numpy as np
import accuracy_experiment_frozen as engine
from gap_solver.accuracy_protocol import PARAMETERS,SPLITS,CONTROLS,digest,hash_files,select_validation
from gap_solver.temporal_protocol import load_temporal_frozen
from gap_solver.tactical_model import FROZEN_MODEL

RAW_LOAD_FREEZE=engine.load_freeze
RAW_PREPARE=engine.prepare_one
RAW_SCORE=engine.score_one
RAW_SELECT=engine.select
RAW_SUMMARIZE=engine.summarize
RAW_LOAD_CASE=engine.load_case


def canonical_key(key):
    key=str(key)
    if PureWindowsPath(key).drive or key.startswith(('/','\\')):raise ValueError('Identity key must be relative')
    parts=key.replace('\\','/').split('/')
    if any(p in ('','..','.') for p in parts):raise ValueError('Unsafe logical identity key')
    return '/'.join(parts)


def canonical_map(value):
    result={}
    for key,member in value.items():
        name=canonical_key(key)
        if name in result:raise ValueError('Colliding portable identity keys')
        result[name]=member
    return result


def portable_require_files(expected,paths):
    if canonical_map(expected)!=canonical_map(hash_files(paths)):raise ValueError('Consumed source/input/model/archive identity changed')


def assert_public_report(value,key='',hash_context=False):
    """Allow bounded aggregate shapes; reject event/coordinate/label sequences."""
    hashed=hash_context or key.endswith('_sha256') and isinstance(value,dict)
    if hashed:
        if isinstance(value,dict):
            for member in value.values():assert_public_report(member,hash_context=True)
        elif not isinstance(value,str) or not re.fullmatch('[0-9a-f]{64}',value):raise ValueError('Invalid hash-only identity map')
        return
    if isinstance(value,dict):
        forbidden={'transitions','pairs','missed','spurious','prediction','predictions','reference','home_xy','away_xy','ball_xy','ball_x','ball_y','source_frames','timestamps','labels','frame','timestamp','label'}
        if set(value)&forbidden:raise ValueError('Per-frame/event content in public report')
        if 'frames' in value and type(value['frames']) is not int:raise ValueError('Frame sequence in public report')
        for name,member in value.items():assert_public_report(member,name)
    elif isinstance(value,(list,tuple)):
        if key in ('confusion','confusion_reference_rows_HAD_prediction_columns_HADX'):
            sizes=(3,4) if key=='confusion' else (3,)
            if len(value) not in sizes or any(not isinstance(row,(list,tuple)) or len(row)!=4 or any(type(n) is not int or n<0 for n in row) for row in value):raise ValueError('Invalid bounded aggregate confusion')
        elif key in ('settings','ranking','cases','matches','sources'):
            if len(value)>100:raise ValueError('Oversized aggregate case/setting list')
            if key=='settings' and all(isinstance(v,str) for v in value):
                if len(value)!=len(set(value)) or not set(value)<={n for n,_,_ in PARAMETERS}:raise ValueError('Invalid setting ID list')
            else:
                if any(not isinstance(v,dict) for v in value):raise ValueError('Aggregate list must contain named records')
                for member in value:assert_public_report(member)
        elif key in ('dfl','skillcorner'):
            allowed={str(m) for groups in SPLITS.values() for m in groups[key]}
            if len(value)!=len(set(map(str,value))) or not set(map(str,value))<=allowed:raise ValueError('Invalid declared match IDs')
        elif key=='limitations' and len(value)<=12 and all(isinstance(v,str) for v in value):pass
        else:raise ValueError('Unapproved array shape in public report: '+key)
    elif isinstance(value,float) and not np.isfinite(value):raise ValueError('Nonfinite public metric')
    elif value is not None and not isinstance(value,(str,int,float,bool)):raise ValueError('Unsupported public value')


class EvidenceGuard:
    def core(self):
        value=RAW_LOAD_FREEZE()
        _,manifest=load_temporal_frozen(engine.ROOT/'benchmark/skillcorner/frozen',engine.ROOT)
        if manifest['artifact_sha256']!=value['temporal_artifact_sha256'] or FROZEN_MODEL['artifact_sha256']!=value['tactical_artifact_sha256']:
            raise ValueError('Frozen head model changed under old experiment identity')
        return value

    def case(self,core,cohort,match,regime,check_inputs=True):
        if check_inputs:portable_require_files(core['input_sha256'][f'{cohort}-{match}'],engine.input_paths(cohort,match))
        archive,metadata=engine.case_paths(cohort,match,regime);record=json.loads(metadata.read_text())
        if record['identity']!=engine.identity(core,cohort,match,regime):raise ValueError('Case identity changed')
        portable_require_files(record['archive_sha256'],{'scores':archive})
        return record

    def verified_receipts(self,stage,core,selected=None):
        rows=engine.receipts(stage);seen=set()
        settings=[n for n,_,_ in PARAMETERS] if stage=='validation' else [selected['selected_id']]
        for r in rows:
            pair=(r['cohort'],str(r['match']));record=self.case(core,r['cohort'],r['match'],r['regime'],pair not in seen);seen.add(pair)
            expected=engine.identity(core,r['cohort'],r['match'],r['regime'])|dict(stage=stage,score_archive_sha256=record['archive_sha256']['scores'],settings=settings)
            if selected is not None:expected['selection_sha256']=digest(selected)
            if r['identity']!=expected or r['stage']!=stage or set(r['variants'])!=set(CONTROLS)|set(settings):raise ValueError('Scored receipt/model/cache binding changed')
            assert_public_report(r)
        return rows

    def verified_selection(self,core=None):
        core=self.core() if core is None else core;rows=self.verified_receipts('validation',core)
        expected=select_validation([r for r in rows if r['regime']=='natural'])
        expected.update(experiment_sha256=digest(core),fresh_holdout=False,
            validation_receipt_sha256=hash_files({p.name:p for p in (engine.REPORTS/'validation').glob('*.json')}))
        actual=json.loads((engine.REPORTS/'selection.json').read_text())
        if actual!=expected:raise ValueError('Selected parameters/decision do not match frozen validation receipts')
        return actual

    def verified_summary_inputs(self,core=None):
        core=self.core() if core is None else core;selected=self.verified_selection(core)
        return self.verified_receipts('regression',core,selected)


def boundary_summary(reference,prediction,periods):
    mapped=engine.metric_periods(reference,periods);a,b=engine.evaluation_arrays(reference,prediction,mapped)
    runs=engine.official.valid_runs(a);filled=engine.official.fill_abstentions(b,runs)
    actual=engine.official.transitions(a,runs);estimated=engine.official.transitions(filled,runs);result={}
    for tolerance in engine.official.TAUS:
        row=engine.official.transition_scores(actual,estimated,tolerance)
        keep={k:row[k] for k in ('precision','recall','f1','n_gt','n_pred','n_matched','n_missed','n_spurious','n_ambiguous')}
        for name in ('mean_latency','median_latency','mean_abs_latency','p90_abs_latency'):
            keep[name+'_frames']=row[name];keep[name+'_seconds']=None if row[name] is None else row[name]/25.
        result[str(tolerance)]=keep
    assert_public_report(result);return result


# Only logical relative-name comparison changes. The preserved engine's bytes,
# inference functions, settings, mask definition and original receipts stay fixed.
engine.require_files=portable_require_files
