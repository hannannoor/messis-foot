"""One frozen WCSF transfer audit; inference has no reference argument."""
import numpy as np
from dataclasses import asdict
from pathlib import Path
import hashlib
import json
import platform
import sqlite3
import sys
from gap_solver.tactical import PortableTree,feature_rows
from gap_solver.tactical_model import FROZEN_MODEL
from gap_solver.soft_sequence import sequence_usable
from gap_solver.materialization_control import materialize_abstentions
from ball_gap_policy import decode_ball_gap
from cadence_baselines import baseline_predictions

METHODS=('w0-c32-neutral-missing','official-convention-w50','matched-input-w50')


def infer_fixed(frames,*,on_method=None):
    if any(f.dead_evidence or f.tag_team or f.restart_hint for f in frames):
        raise ValueError('Geometry-only fixed-head inputs required')
    if on_method:on_method(METHODS[0])
    tree=PortableTree(FROZEN_MODEL['model'])
    supports=[tree.predict(r) for r in feature_rows(frames)]
    periods=[f.period for f in frames]
    labels,_=decode_ball_gap(supports,periods,[bool(sequence_usable(f)) for f in frames],
                             [bool(f.ball_observed) for f in frames])
    encode=lambda values:np.asarray(['HADX'.index(s) for s in values],dtype=np.uint8)
    result={METHODS[0]:encode(materialize_abstentions(labels,periods))}
    for mode in ('official-convention','matched-input'):
        if on_method:on_method(mode+'-w50')
        result[mode+'-w50']=encode(baseline_predictions(frames,50,mode)['final'])
    return result


def _score_cell(gt,pred,periods):
    from gap_solver import official_metrics as official
    from gap_solver.benchmark import evaluation_arrays
    from cadence_metrics import diagnostic_metrics
    from wcsf_report import prf,mean_defined,IOUS
    cm=official.confusion(gt,pred);known=int((gt<3).sum())
    support=dict(frames=len(gt),known=known,unknown=len(gt)-known,
                 **{name:int((gt==k).sum()) for k,name in enumerate('HAD')})
    support.update({name+'_seconds':support[name]/25 for name in 'HAD'})
    rates=[]
    for k in range(3):
        tp=int(cm[k,k]);fp=int(cm[:3,k].sum())-tp;fn=int(cm[k].sum())-tp
        rates.append(prf(tp,fp,fn)['f1'])
    if known:a,b=evaluation_arrays(gt,pred,periods)
    else:a=np.empty(0,dtype=np.uint8);b=np.empty(0,dtype=np.uint8)
    runs=official.valid_runs(a);filled=official.fill_abstentions(b,runs)
    spell=official.spell_scores(a,filled,runs)
    def intervals(actual,estimated):
        overlap=official.spell_overlaps(actual,estimated);table={}
        for threshold in official.SPELL_IOUS:
            table[str(threshold)]=prf(*official.match_spells(overlap,len(actual),len(estimated),threshold))
        return dict(n_gt=len(actual),n_pred=len(estimated),per_iou=table,mean_f1=mean_defined(v['f1'] for v in table.values()))
    table={str(k):prf(*(r[n] for n in ('n_matched','n_spurious','n_missed'))) for k,r in spell['per_iou'].items()}
    spells=dict(n_gt=spell['n_gt'],n_pred=spell['n_pred'],per_iou=table,mean_f1=mean_defined(v['f1'] for v in table.values()))
    dead=intervals([s for s in official.segments(a,runs) if s[2]==2],
                   [s for s in official.segments(filled,runs) if s[2]==2])
    extras=diagnostic_metrics(gt,pred,periods,[])
    boundaries=extras['HA_boundaries']
    for row in boundaries.values():
        values=prf(row['n_matched'],row['n_spurious'],row['n_missed'])
        for key in ('precision','recall','f1'):row[key]=values[key]
    metrics=dict(accuracy=float(official.accuracy(cm[:3])) if known else None,
                 official_macro_f1=float(official.macro_f1(cm[:3])) if known else None,
                 supported_macro_f1=mean_defined(rates),spell_f1_mean=spells['mean_f1'])
    return dict(support=support,metrics=metrics,confusion=cm.tolist(),spells=spells,
        dead=dict(frame=prf(int(cm[2,2]),int(cm[:2,2].sum()),int(cm[2].sum()-cm[2,2])),intervals=dead),
        duration=extras['spell_duration'],HA_boundaries=boundaries)


def score_fixed(gt,periods,methods,*,on_method=None):
    from wcsf_report import METRICS,validate_report
    gt=np.asarray(gt);periods=np.asarray(periods)
    if type(methods) is not dict or set(methods)!=set(METHODS):raise ValueError('Only the three frozen methods allowed')
    if gt.ndim!=1 or periods.shape!=gt.shape or not len(gt) or gt.dtype.kind not in 'ui' or periods.dtype.kind not in 'ui':
        raise ValueError('Invalid reference/period structure')
    if not np.isin(gt,[0,1,2,3]).all() or not np.isin(periods,[1,2]).all():raise ValueError('Invalid reference/period codes')
    chunks=periods[np.r_[True,periods[1:]!=periods[:-1]]]
    if len(set(chunks.tolist()))!=len(chunks):raise ValueError('Periods cannot reappear')
    result=dict(schema_version=1,full_state_complete=bool(all((gt==k).any() for k in range(3))),match={},halves={'1':{},'2':{}},deltas={})
    for method in METHODS:
        if on_method:on_method(method)
        pred=np.asarray(methods[method])
        if pred.shape!=gt.shape or pred.dtype.kind not in 'ui' or not np.isin(pred,[0,1,2,3]).all():raise ValueError('Invalid frozen prediction')
        result['match'][method]=_score_cell(gt,pred,periods)
        for p in (1,2):
            take=periods==p;result['halves'][str(p)][method]=_score_cell(gt[take],pred[take],periods[take])
    for method in METHODS[1:]:
        result['deltas'][method]={}
        for name in METRICS:
            a=result['match'][method]['metrics'][name];b=result['match'][METHODS[0]]['metrics'][name]
            result['deltas'][method][name]=None if a is None or b is None else a-b
    validate_report(result)
    return result


def sha256(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def source_paths(root):
    root=Path(root);excluded={'.tmp','.superpowers','.git','.venv','__pycache__'}
    paths={p.relative_to(root).as_posix():p for p in root.rglob('*.py') if not excluded.intersection(p.relative_to(root).parts)}
    for directory in ('benchmark/frozen','benchmark/skillcorner/frozen'):
        paths.update({p.relative_to(root).as_posix():p for p in (root/directory).glob('*.json')})
    for name in ('docs/superpowers/specs/2026-11-09-wcsf-transfer-design.md',
                 'docs/superpowers/plans/2026-11-09-wcsf-transfer.md',
                 'docs/superpowers/specs/2026-11-09-wcsf-container-amendment.md',
                 'docs/reference-qualification/source-qualification.json',
                 'docs/reference-qualification/evaluation-protocol.md'):
        paths[name]=root/name
    required={'accuracy_experiment.py','accuracy_experiment_frozen.py','accuracy_evidence.py','ball_gap_candidate.py',
              'wcsf_source.py','wcsf_geometry.py','wcsf_reference.py','wcsf_audit.py','wcsf_report.py'}
    if not required<=paths.keys() or any(not p.is_file() for p in paths.values()):raise ValueError('Incomplete prospective source inventory')
    return dict(sorted(paths.items()))


def write_new(path,value):
    from gap_solver.input_contract import reject_linked_ancestors
    from wcsf_report import read_json
    path=Path(path);reject_linked_ancestors(path)
    if path.exists():
        if digest(read_json(path))!=digest(value):raise ValueError('Preserve conflicting receipt generation')
        return
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8') as f:f.write(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n')


class AuditSession:
    def __init__(self,root,public,private):
        from gap_solver.input_contract import reject_linked_ancestors
        self.root=Path(root);self.public=Path(public);self.private=Path(private)
        reject_linked_ancestors(self.public);reject_linked_ancestors(self.private)

    @property
    def paths(self):
        import wcsf_source as source
        frozen=self._freeze()
        return source.SourcePaths(tuple(self.private/a[0] for a in source.ASSETS),self.private/'geometry.sqlite',
            self.private/'reference.sqlite',self.private/'access.jsonl',digest(frozen))

    def _expected_freeze(self):
        import pandas as pd
        import wcsf_source as source
        return dict(schema_version=1,base_commit='61a90e331d1e025a00ab3e84e5b5827be654d9a8',
            methods=list(METHODS),generation=self.private.name,
            assets={str(i):dict(name=n,git_blob=b,bytes=s) for i,(n,b,s) in enumerate(source.ASSETS,1)},
            source_sha256={n:sha256(p) for n,p in source_paths(self.root).items()},
            environment=dict(python=sys.version,numpy=np.__version__,pandas=pd.__version__,sqlite=sqlite3.sqlite_version,system=platform.system()),
            contract='2026-11-09-wcsf-transfer-design + container-amendment v2; fixed descriptive three-method audit')

    def freeze(self):
        value=self._expected_freeze();write_new(self.public/'freeze.json',value);return value

    def _freeze(self):
        from wcsf_report import read_json
        p=self.public/'freeze.json'
        if not p.exists():raise ValueError('Prospective freeze required')
        value=read_json(p)
        if digest(value)!=digest(self._expected_freeze()):raise ValueError('Frozen source/protocol/environment changed')
        return value

    def _inputs(self):
        p=self.paths
        return {'archive_1':p.archives[0],'archive_2':p.archives[1],
                'geometry_store':p.geometry_db,'reference_store':p.reference_db}

    def _acquisition(self):
        from wcsf_report import read_json,keys,count
        frozen=self._freeze();value=read_json(self.public/'acquisition.json')
        keys(value,('schema_version','freeze_sha256','input_sha256','source_rows','identical_geometry_duplicates','first_machine_reference_access_utc'))
        if type(value['schema_version']) is not int or value['schema_version']!=1:raise ValueError('Invalid acquisition schema')
        count(value['source_rows']);count(value['identical_geometry_duplicates'])
        if value['freeze_sha256']!=digest(frozen) or value['input_sha256']!={n:sha256(p) for n,p in self._inputs().items()}:
            raise ValueError('Acquired input identity changed')
        return value

    def acquire(self):
        import wcsf_source as source
        from wcsf_report import read_json
        frozen=self._freeze()
        if (self.public/'acquisition.json').exists():return self._acquisition()
        if self.private.exists():raise ValueError('Preserve incomplete acquisition generation')
        archives=source.acquire(self.private)
        if archives!=self.paths.archives:raise ValueError('Unexpected acquired archive roles')
        counts=source.ingest(self.paths)
        first=json.loads(self.paths.access_log.read_text(encoding='utf-8').splitlines()[0])
        value=dict(schema_version=1,freeze_sha256=digest(frozen),
            input_sha256={n:sha256(p) for n,p in self._inputs().items()},**counts,
            first_machine_reference_access_utc=first['timestamp_utc'])
        write_new(self.public/'acquisition.json',value);return value

    def geometry(self):
        from wcsf_report import read_json,keys
        self._acquisition();value=read_json(self.public/'geometry.json')
        keys(value,('schema_version','freeze_sha256','acquisition_sha256','decision','quality'))
        keys(value['decision'],('selected','eligible','candidate_counts','failure'))
        if value['freeze_sha256']!=digest(self._freeze()) or value['acquisition_sha256']!=sha256(self.public/'acquisition.json'):
            raise ValueError('Geometry receipt identity changed')
        return value

    def qualify(self):
        from wcsf_geometry import qualify,canonical_input
        self._acquisition();decision=qualify(self.paths.geometry_db)
        quality=None if decision.selected is None else canonical_input(self.paths.geometry_db,decision).quality
        value=dict(schema_version=1,freeze_sha256=digest(self._freeze()),acquisition_sha256=sha256(self.public/'acquisition.json'),
                   decision=asdict(decision),quality=quality)
        write_new(self.public/'geometry.json',value);return value

    def attempts(self):
        p=self.private/'attempts.jsonl'
        return [] if not p.exists() else [json.loads(s) for s in p.read_text(encoding='utf-8').splitlines()]

    def _attempt(self,stage,method):
        from wcsf_source import event
        event(self.private/'attempts.jsonl','method_attempt',stage=stage,method=method,freeze_sha256=digest(self._freeze()))

    def _prediction_paths(self):
        folder=self.private/'predictions'
        return {**{m:folder/(m+'.npy') for m in METHODS},
                'index':folder/'canonical-index.npy','endpoints':folder/'endpoints.npy','provenance':folder/'observation-provenance.npy'}

    def _predictions(self):
        from wcsf_report import read_json,keys
        geometry=self.geometry()
        if geometry['decision']['selected'] is None:raise ValueError('Structural qualification failed; no model calls allowed')
        if not (self.public/'predictions-seal.json').exists():raise ValueError('Complete prediction seal required before scoring')
        value=read_json(self.public/'predictions-seal.json')
        keys(value,('schema_version','freeze_sha256','geometry_sha256','private_sha256','rows'))
        if value['freeze_sha256']!=digest(self._freeze()) or value['geometry_sha256']!=sha256(self.public/'geometry.json'):
            raise ValueError('Prediction binding changed')
        files=self._prediction_paths()
        if set((self.private/'predictions').iterdir())!=set(files.values()):raise ValueError('Unexpected private prediction files')
        if value['private_sha256']!={n:sha256(p) for n,p in files.items()}:raise ValueError('Prediction/index identity changed')
        if [a['method'] for a in self.attempts() if a['stage']=='infer']!=list(METHODS):raise ValueError('Unexpected inference attempts')
        return value

    def infer(self):
        from wcsf_geometry import GeometryDecision,canonical_input
        from wcsf_source import event
        value=self.geometry();decision=GeometryDecision(**value['decision'])
        if decision.selected is None:raise ValueError('Structural qualification failed; no model calls allowed')
        if (self.public/'predictions-seal.json').exists():return self._predictions()
        folder=self.private/'predictions'
        if folder.exists():raise ValueError('Preserve incomplete prediction generation')
        data=canonical_input(self.paths.geometry_db,decision)
        if data.quality!=value['quality']:raise ValueError('Canonical quality differs from seal')
        folder.mkdir()
        self._attempt('infer',METHODS[0])
        result=infer_fixed(data.frames,on_method=lambda m:self._attempt('infer',m) if m!=METHODS[0] else None)
        files=self._prediction_paths()
        arrays={**result,'index':np.asarray(data.index,dtype=np.int64),
                'endpoints':np.asarray([[(-1 if v is None else v) for v in pair] for pair in data.endpoints],dtype=np.int64),
                'provenance':np.asarray([[bool(f.ball_native_observation),bool(f.ball_interpolated)] for f in data.frames],dtype=np.uint8)}
        for name,path in files.items():
            with path.open('xb') as f:np.save(f,arrays[name],allow_pickle=False)
        seal=dict(schema_version=1,freeze_sha256=digest(self._freeze()),geometry_sha256=sha256(self.public/'geometry.json'),
                  private_sha256={n:sha256(p) for n,p in files.items()},rows=len(data.frames))
        write_new(self.public/'predictions-seal.json',seal)
        event(self.paths.access_log,'predictions_sealed',protocol_hash=digest(self._freeze()),methods=3)
        return seal

    def score(self):
        from wcsf_reference import reference_codes
        from wcsf_report import read_json
        from wcsf_source import event
        self._predictions()
        if (self.public/'results.json').exists():self._results();return read_json(self.public/'results.json')
        started=self.private/'score-started.json'
        if started.exists():raise ValueError('Preserve incomplete scoring attempt; no automatic retry')
        write_new(started,dict(freeze_sha256=digest(self._freeze())))
        self._attempt('score',METHODS[0])
        event(self.paths.access_log,'reference_summary_and_outcomes_opened',protocol_hash=digest(self._freeze()),permanently_used=True)
        index_array=np.load(self._prediction_paths()['index'],allow_pickle=False)
        index=[(int(p),int(t)) for p,t in index_array]
        reference=reference_codes(self.paths.reference_db,index)
        methods={m:np.load(self._prediction_paths()[m],allow_pickle=False) for m in METHODS}
        report=score_fixed(reference,index_array[:,0].astype(np.uint8),methods,
                           on_method=lambda m:self._attempt('score',m) if m!=METHODS[0] else None)
        write_new(self.public/'results.json',report)
        write_new(self.public/'score-seal.json',dict(schema_version=1,freeze_sha256=digest(self._freeze()),
            predictions_seal_sha256=sha256(self.public/'predictions-seal.json'),results_sha256=sha256(self.public/'results.json'),
            attempts_sha256=sha256(self.private/'attempts.jsonl')))
        return report

    def _results(self):
        from wcsf_report import read_json,keys,validate_report
        self._predictions();seal=read_json(self.public/'score-seal.json')
        keys(seal,('schema_version','freeze_sha256','predictions_seal_sha256','results_sha256','attempts_sha256'))
        expected=dict(schema_version=1,freeze_sha256=digest(self._freeze()),
            predictions_seal_sha256=sha256(self.public/'predictions-seal.json'),results_sha256=sha256(self.public/'results.json'),
            attempts_sha256=sha256(self.private/'attempts.jsonl'))
        if seal!=expected:raise ValueError('Scientific result/attempt identity changed')
        if [a['method'] for a in self.attempts() if a['stage']=='score']!=list(METHODS):raise ValueError('Unexpected scoring attempts')
        validate_report(read_json(self.public/'results.json'))
        events=[json.loads(s)['event'] for s in self.paths.access_log.read_text(encoding='utf-8').splitlines()]
        if events.count('predictions_sealed')!=1 or events.count('reference_summary_and_outcomes_opened')!=1 or events.index('predictions_sealed')>events.index('reference_summary_and_outcomes_opened'):
            raise ValueError('Reference/outcome opening order differs')
        return seal

    def verify(self):
        from wcsf_geometry import qualify
        value=self.geometry()
        if asdict(qualify(self.paths.geometry_db))!=value['decision']:raise ValueError('Geometry decision does not reproduce')
        if value['decision']['selected'] is None:
            if self.attempts() or (self.public/'results.json').exists():raise ValueError('Model calls on failed geometry')
            status='structural_failure';score_count=0
        else:self._results();status='completed';score_count=3
        result=dict(schema_version=1,status=status,verified=True,freeze_sha256=digest(self._freeze()),
                    geometry_sha256=sha256(self.public/'geometry.json'),completed_method_comparisons=score_count,
                    inference_attempts=sum(a['stage']=='infer' for a in self.attempts()),
                    scoring_attempts=sum(a['stage']=='score' for a in self.attempts()),
                    results_sha256=sha256(self.public/'results.json') if score_count else None)
        write_new(self.public/'verification.json',result);return result


def main():
    import argparse
    root=Path(__file__).resolve().parent
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('stage',choices=('freeze','acquire','qualify','infer','score','verify'))
    args=parser.parse_args();session=AuditSession(root,root/'reports/wcsf-transfer-v2',root.parent/'wcsf-reference/wcsf-2026-11-09-2')
    try:
        result=getattr(session,args.stage)()
        summary=dict(stage=args.stage,status='ok')
        if args.stage=='freeze':summary['sources']=len(result['source_sha256'])
        if args.stage=='qualify':summary.update(decision=result['decision'],quality=result['quality'])
        if args.stage=='verify':summary=result
        print(json.dumps(summary,allow_nan=False))
    except Exception as error:
        print(json.dumps(dict(stage=args.stage,status='failed',error_type=type(error).__name__)))
        return 1
    return 0


if __name__=='__main__':raise SystemExit(main())
