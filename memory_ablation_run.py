"""Sequential bounded memory-ablation lifecycle; private arrays never published."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import numpy as np

import memory_ablation_protocol as p
from memory_ablation import prepare_inputs,infer_prepared
from memory_ablation_training import prepare_training,fit_pair,ControlMismatch,TRAIN_MATCHES,semantic_digest
from memory_ablation_metrics import MATCHES,REGIMES,MODES,score_variant,summarize_cases
from gap_solver.temporal_selection import contiguous_mask
from gap_solver.temporal import mask_motion_frames


def load_training(bindings):
    from gap_solver.external import load_cache
    groups=[]
    for match in TRAIN_MATCHES:
        files=bindings['training'][match]['files'];features=next(path for path in files.values() if str(path).endswith('.features.npz'))
        data=load_cache(Path(str(features)[:-len('.features.npz')]))
        if data.match_id!='DFL-MAT-'+match:raise ValueError('Training cache match identity differs')
        groups.append(dict(match=match,frames=data.frames(),reference=data.reference,periods=data.periods))
    return prepare_training(groups)


def load_evaluation(cid,binding):
    if cid=='wcsf-used-match':return p.legacy._load_case(cid,binding)
    from gap_solver.skillcorner import load_motion_cache
    from gap_solver.external import load_cache
    from gap_solver.dfl_motion import load_dfl_motion
    cohort,match=cid.split('-',1);files=binding['files']
    features=next(path for path in files.values() if str(path).endswith('.features.npz'))
    prefix=Path(str(features)[:-len('.features.npz')])
    if cohort=='skillcorner':data=load_motion_cache(prefix);frames=data.frames()
    else:
        data=load_cache(prefix);meta=next(path for path in files.values() if 'matchinformation' in path.name)
        positions=next(path for path in files.values() if 'positions' in path.name.lower());frames=load_dfl_motion(meta,positions,data)
    if str(data.match_id)!=(match if cohort=='skillcorner' else 'DFL-MAT-'+match):raise ValueError('Evaluation match identity differs')
    return dict(frames=frames,reference=lambda:data.reference,validate=lambda prediction:None,reference_loaded_by_adapter=True)


def run_training_worker(session):
    freeze,_,_=session._frozen();environment=p.read(session.private/'environment-map.json')
    result=subprocess.run([environment['training_python'],str(session.root/'memory_ablation_run.py'),'fit','--run-id',session.run_id,'--training-worker'],
        cwd=session.root,env=p.thread_environment(),capture_output=True,text=True)
    with (session.private/'training-worker.stdout.log').open('x',encoding='utf-8') as handle:handle.write(result.stdout)
    with (session.private/'training-worker.stderr.log').open('x',encoding='utf-8') as handle:handle.write(result.stderr)
    if result.returncode:raise ValueError('Pinned training worker stopped; private logs retained')
    return json.loads(result.stdout)


def _encoded(labels):return np.asarray(['HADX'.index(s) for s in labels],dtype=np.uint8)


def _save_arrays(path,arrays):
    p.reject_linked_ancestors(path)
    with path.open('xb') as handle:np.savez_compressed(handle,**arrays)


class AblationSession:
    def __init__(self,run_id,root=p.ROOT):
        self.run_id=p.safe_run_id(run_id);self.root=Path(root).resolve()
        self.budget=self.root.parent/'memory-ablation-reference'/p.EXPERIMENT
        self.private=self.budget/'runs'/run_id;self.public=self.root/'reports/memory-ablation'/run_id
        for path in (self.budget,self.private,self.public):p.reject_linked_ancestors(path)

    def _current(self):
        if p.hashes({name:self.root/name for name in p.PROTECTED})!=p.PROTECTED:raise ValueError('Protected release/design changed')
        p.legacy._release_components(self.root)
        sources=p.source_paths(self.root)
        if not set(p.ENTRIES)<=set(sources):raise ValueError('Incomplete ablation source inventory')
        bindings=p.input_bindings(self.root)
        if set(bindings)!= {'training','evaluation'} or tuple(bindings['training'])!=TRAIN_MATCHES or set(bindings['evaluation'])!={cid for cid,_,_ in MATCHES}:
            raise ValueError('Training/evaluation cohort changed')
        for group in bindings.values():
            for binding in group.values():
                if not binding['files'] or p.hashes(binding['files'])!=binding['expected']:raise ValueError('Frozen input identity differs')
        existing=self.private/'environment-map.json'
        if existing.is_file():
            recorded=p.read(existing)
            env=p.environments(self.root,scoring_python=recorded['scoring_python'],scoring_threads=recorded['scoring']['threads'])
        else:env=p.environments(self.root)
        return sources,bindings,env

    def _event(self,event,**fields):
        with (self.private/'access.jsonl').open('ab') as handle:handle.write(p.canonical(dict(event=event,utc=p.utc(),**fields)))

    def _owner_path(self):
        successor=self.budget/('generation-owner--'+self.run_id+'.json')
        return successor if successor.is_file() else self.budget/'experiment-owner.json'

    def _continuation(self,require_empty=False):
        link_path=self.budget/'preflight-successor.json'
        if not link_path.is_file():raise FileExistsError('Experiment owner already exists')
        link=p.read(link_path);original=p.read(self.budget/'experiment-owner.json')
        if original!=dict(run_id=link['prior_run_id'],experiment=p.EXPERIMENT,root=str(self.root)) or link['successor_run_id']!=self.run_id or link['owner_sha256']!=p.sha(self.budget/'experiment-owner.json'):
            raise ValueError('Preflight successor ownership differs')
        prior=self.budget/'runs'/link['prior_run_id'];public=self.root/'reports/memory-ablation'/link['prior_run_id']
        if p.read(prior/'retired-preflight.json')!=dict(status_sha256=p.sha(public/'preflight-status.json')) or link['status_sha256']!=p.sha(public/'preflight-status.json'):
            raise ValueError('Preflight retirement certificate changed')
        status=p.read(public/'preflight-status.json')
        if status['freeze_sha256']!=p.sha(public/'freeze.json') or (status['fits'],status['inference_entries'],status['scorings'])!=(0,0,0) or status['successor_run_id']!=self.run_id:
            raise ValueError('Preflight retirement identity differs')
        if status['error_log_sha256']!=p.hashes({name:prior/name for name in ('execution-error-fit-worker.log','execution-error-fit.log')}):raise ValueError('Preflight failure evidence changed')
        if require_empty and any((self.budget/'claims').iterdir()):raise ValueError('Scientific attempts cannot be retired/reset')
        return p.sha(link_path)

    def _expected_owner(self):
        value=dict(run_id=self.run_id,experiment=p.EXPERIMENT,root=str(self.root))
        if self._owner_path().name!='experiment-owner.json':value['preflight_certificate_sha256']=self._continuation()
        return value

    def retire_preflight(self,successor_run_id):
        p.safe_run_id(successor_run_id)
        if successor_run_id==self.run_id:raise ValueError('A successor requires a new generation')
        original=p.read(self.budget/'experiment-owner.json')
        if original!=dict(run_id=self.run_id,experiment=p.EXPERIMENT,root=str(self.root)) or (self.budget/'preflight-successor.json').exists():raise ValueError('Only the original empty preflight may be retired once')
        anchor=p.read(self.private/'freeze-anchor.json')
        if anchor!=dict(freeze_sha256=p.sha(self.public/'freeze.json'),owner_sha256=p.sha(self.budget/'experiment-owner.json'),environment_map_sha256=p.sha(self.private/'environment-map.json')):raise ValueError('Original preflight anchor differs')
        if any((self.budget/'claims').iterdir()):raise ValueError('A scientific claim prevents preflight retirement')
        if {path.name for path in self.public.iterdir()}!={'freeze.json'}:raise ValueError('Preflight has result artifacts')
        allowed={'environment-map.json','input-map.json','freeze-anchor.json','access.jsonl','fit-request.incomplete',
            'execution-error-fit-worker.log','execution-error-fit.log','training-worker.stdout.log','training-worker.stderr.log'}
        if not {path.name for path in self.private.iterdir()}<=allowed or not (self.private/'fit-request.incomplete').is_file():raise ValueError('Preflight contains prepared or incomplete scientific work')
        events=[json.loads(line) for line in (self.private/'access.jsonl').read_text(encoding='utf-8').splitlines()]
        if [event['event'] for event in events]!=['frozen']:raise ValueError('Training/evaluation acquisition already entered')
        errors={name:self.private/name for name in ('execution-error-fit-worker.log','execution-error-fit.log')}
        if not all(path.is_file() for path in errors.values()):raise ValueError('Completed worker/parent failure evidence required')
        value=dict(schema_version=1,status='retired_before_scientific_entry',prior_run_id=self.run_id,successor_run_id=successor_run_id,
            fits=0,inference_entries=0,scorings=0,freeze_sha256=p.sha(self.public/'freeze.json'),owner_sha256=p.sha(self.budget/'experiment-owner.json'),
            error_log_sha256=p.hashes(errors),created_utc=p.utc())
        p.assert_public_report(value);p.store_exact(self.public/'preflight-status.json',value)
        p.store_exact(self.private/'retired-preflight.json',dict(status_sha256=p.sha(self.public/'preflight-status.json')))
        p.store_exact(self.budget/'preflight-successor.json',dict(prior_run_id=self.run_id,successor_run_id=successor_run_id,
            owner_sha256=p.sha(self.budget/'experiment-owner.json'),status_sha256=p.sha(self.public/'preflight-status.json')))
        return dict(status=value['status'],fits=0,inference_entries=0,scorings=0,successor_run_id=successor_run_id)

    def freeze(self):
        successor=(self.budget/'experiment-owner.json').exists()
        certificate=self._continuation(require_empty=True) if successor else None
        sources,bindings,env=self._current()
        self.budget.mkdir(parents=True,exist_ok=True)
        owner=dict(run_id=self.run_id,experiment=p.EXPERIMENT,root=str(self.root))
        if successor:owner['preflight_certificate_sha256']=certificate
        owner_path=self.budget/('generation-owner--'+self.run_id+'.json') if successor else self.budget/'experiment-owner.json'
        p.store_exact(owner_path,owner)
        self.private.mkdir(parents=True,exist_ok=False);p.store_exact(self.private/'freeze.incomplete',dict(utc=p.utc()))
        self.public.mkdir(parents=True,exist_ok=False)
        value=dict(schema_version=1,run_id=self.run_id,created_utc=p.utc(),protocol=p.protocol(),source_sha256=p.hashes(sources),
            input_sha256={category:{cid:binding['expected'] for cid,binding in group.items()} for category,group in bindings.items()},
            baseline_contracts={cid:b['parity'] for cid,b in bindings['evaluation'].items()},environment=p.public_environment(env))
        p.assert_public_report(value);p.store_exact(self.public/'freeze.json',value)
        p.store_exact(self.private/'environment-map.json',env)
        p.store_exact(self.private/'input-map.json',{category:{cid:{key:str(path.resolve()) for key,path in b['files'].items()} for cid,b in group.items()} for category,group in bindings.items()})
        p.store_exact(self.private/'freeze-anchor.json',dict(freeze_sha256=p.sha(self.public/'freeze.json'),owner_sha256=p.sha(owner_path),environment_map_sha256=p.sha(self.private/'environment-map.json')))
        (self.budget/'claims').mkdir(exist_ok=successor);self._event('frozen');(self.private/'freeze.incomplete').unlink()
        return dict(status='frozen',cases=30,max_fits=2,max_scorings=60,freeze_sha256=p.sha(self.public/'freeze.json'))

    def _frozen(self):
        if (self.private/'freeze.incomplete').exists() or not (self.private/'freeze-anchor.json').is_file():raise ValueError('Missing/incomplete generation freeze')
        anchor=p.read(self.private/'freeze-anchor.json')
        if anchor!=dict(freeze_sha256=p.sha(self.public/'freeze.json'),owner_sha256=p.sha(self._owner_path()),environment_map_sha256=p.sha(self.private/'environment-map.json')):
            raise ValueError('Private freeze/owner anchor differs')
        owner=p.read(self._owner_path())
        if owner!=self._expected_owner():raise ValueError('Global experiment owner differs')
        freeze=p.read(self.public/'freeze.json');sources,bindings,env=self._current()
        if freeze['protocol']!=p.protocol() or freeze['source_sha256']!=p.hashes(sources) or freeze['environment']!=p.public_environment(env) or freeze['run_id']!=self.run_id:
            raise ValueError('Source/protocol/runtime freeze changed')
        if freeze['input_sha256']!={c:{cid:b['expected'] for cid,b in group.items()} for c,group in bindings.items()} or freeze['baseline_contracts']!={cid:b['parity'] for cid,b in bindings['evaluation'].items()}:
            raise ValueError('Frozen input or baseline contracts changed')
        return freeze,bindings,anchor['freeze_sha256']

    def _runtime(self,freeze,training=False):
        if p.runtime_info(training=training)!=freeze['environment']['training' if training else 'scoring']:raise ValueError('Executing runtime differs from freeze')

    def _claim(self,kind,identity):
        if kind=='fit':
            if identity not in MODES:raise ValueError('Unknown fitting mode')
            prior={path.name for path in (self.budget/'claims').glob('fit--*.json')}
            if len(prior)>=2 or identity=='memory-ablated' and 'fit--control.json' not in prior:raise ValueError('Fitting order/budget exhausted')
        else:
            allowed={cid+'--'+regime+'--'+mode for cid,_,_ in MATCHES for regime in REGIMES for mode in MODES}
            if kind not in ('inference','scoring') or identity not in allowed:raise ValueError('Unknown evaluation claim')
            if len(list((self.budget/'claims').glob(kind+'--*.json')))>=60:raise ValueError('Evaluation budget exhausted')
        p.store_exact(self.budget/'claims'/(kind+'--'+identity+'.json'),dict(run_id=self.run_id,kind=kind,identity=identity,utc=p.utc()))
        self._event(kind+'_entry',identity=identity)

    def fit(self):
        self._frozen()
        if (self.private/'fit.incomplete').exists() or (self.private/'fit-request.incomplete').exists() or (self.public/'fit.json').exists() or list((self.budget/'claims').glob('fit--*.json')):
            raise ValueError('Preserve consumed/interrupted fitting attempts')
        p.store_exact(self.private/'fit-request.incomplete',dict(utc=p.utc()))
        result=run_training_worker(self)
        (self.private/'fit-request.incomplete').unlink()
        return result

    def _fit_worker(self):
        freeze,bindings,identity=self._frozen();self._runtime(freeze,training=True)
        if (self.private/'fit.incomplete').exists() or (self.public/'fit.json').exists() or list((self.budget/'claims').glob('fit--*.json')):raise ValueError('Fitting attempts already claimed')
        p.store_exact(self.private/'fit.incomplete',dict(utc=p.utc()))
        self._event('training_reference_cache_entry',reference_container_parsed=True)
        data=load_training(bindings)
        arrays={key:getattr(data,key) for key in ('matrix','target','weights','row_identity')}
        _save_arrays(self.private/'training-data.npz',arrays);training_identity=p.array_identity(arrays)
        try:models=fit_pair(data,lambda mode:self._claim('fit',mode))
        except ControlMismatch as error:
            p.store_exact(self.private/'failed-control-model.json',error.model)
            value=dict(schema_version=1,status='stopped_control_mismatch',freeze_sha256=identity,fits=1,training_semantic_sha256=training_identity,
                control_model_sha256=error.receipt['model_sha256'],expected_control_sha256=p.MODEL_SHA)
            p.assert_public_report(value);p.store_exact(self.public/'fit.json',value)
            p.store_exact(self.private/'fit-anchor.json',dict(fit_sha256=p.sha(self.public/'fit.json')));self._event('fit_stopped')
            return dict(status=value['status'],fits=1)
        directory=self.public/'models';directory.mkdir()
        for mode in MODES:
            p.validate_model(models[mode],mode);p.store_exact(directory/(mode+'.json'),models[mode])
        value=dict(schema_version=1,status='complete',freeze_sha256=identity,fits=2,training_semantic_sha256=training_identity,
            model_artifact_sha256={mode:p.sha(directory/(mode+'.json')) for mode in MODES})
        p.assert_public_report(value);p.store_exact(self.public/'fit.json',value)
        p.store_exact(self.private/'fit-anchor.json',dict(fit_sha256=p.sha(self.public/'fit.json')))
        self._event('fit_complete');(self.private/'fit.incomplete').unlink()
        return dict(status='complete',fits=2)

    def _fit_status(self):
        if not (self.public/'fit.json').is_file() or not (self.private/'fit-anchor.json').is_file():raise ValueError('No completed fitting receipt')
        if p.read(self.private/'fit-anchor.json')!=dict(fit_sha256=p.sha(self.public/'fit.json')):raise ValueError('Fitting anchor changed')
        value=p.read(self.public/'fit.json')
        if value['freeze_sha256']!=p.sha(self.public/'freeze.json'):raise ValueError('Fitting freeze identity differs')
        return value

    def _models(self):
        value=self._fit_status()
        if value['status']!='complete' or (self.private/'fit.incomplete').exists():raise ValueError('Paired models not completed')
        models={mode:p.validate_model(p.read(self.public/'models'/(mode+'.json')),mode) for mode in MODES}
        if value['model_artifact_sha256']!={mode:p.sha(self.public/'models'/(mode+'.json')) for mode in MODES}:raise ValueError('Model artifacts changed')
        return models

    def seal(self):
        self._frozen();models=self._models()
        value=dict(schema_version=1,freeze_sha256=p.sha(self.public/'freeze.json'),fit_sha256=p.sha(self.public/'fit.json'),
            model_artifact_sha256={mode:p.sha(self.public/'models'/(mode+'.json')) for mode in MODES},model_sha256={mode:models[mode]['model_sha256'] for mode in MODES},created_utc=p.utc())
        p.assert_public_report(value);p.store_exact(self.public/'seal.json',value)
        p.store_exact(self.private/'seal-anchor.json',dict(seal_sha256=p.sha(self.public/'seal.json')));self._event('sealed')
        return dict(status='sealed',seal_sha256=p.sha(self.public/'seal.json'))

    def _sealed(self):
        if not (self.public/'seal.json').is_file() or not (self.private/'seal-anchor.json').is_file():raise ValueError('Model seal missing')
        if p.read(self.private/'seal-anchor.json')!=dict(seal_sha256=p.sha(self.public/'seal.json')):raise ValueError('Model seal changed')
        seal=p.read(self.public/'seal.json');models=self._models()
        if seal['freeze_sha256']!=p.sha(self.public/'freeze.json') or seal['fit_sha256']!=p.sha(self.public/'fit.json') or seal['model_artifact_sha256']!={mode:p.sha(self.public/'models'/(mode+'.json')) for mode in MODES}:raise ValueError('Sealed identities changed')
        return models,p.sha(self.public/'seal.json')

    def evaluate(self):
        freeze,bindings,identity=self._frozen();self._runtime(freeze);models,seal=self._sealed()
        cases=self.private/'cases'
        if cases.exists() or list((self.budget/'claims').glob('inference--*.json')) or list((self.budget/'claims').glob('scoring--*.json')):raise ValueError('Preserve prior/interrupted evaluations')
        cases.mkdir()
        for cid,cohort,role in MATCHES:
            binding=bindings['evaluation'][cid]
            self._event('evaluation_adapter_entry',case_id=cid,reference_container_may_be_parsed=cohort!='wcsf')
            loaded=load_evaluation(cid,binding);original=list(loaded['frames']);periods=np.asarray([f.period for f in original],dtype=np.uint8)
            for regime in REGIMES:
                name=cid+'--'+regime;directory=cases/name;directory.mkdir();p.store_exact(directory/'.incomplete',dict(utc=p.utc()))
                self._event('case_entry',case_id=cid,regime=regime,reference_loaded_by_adapter=loaded['reference_loaded_by_adapter'])
                mask=np.zeros(len(original),dtype=bool) if regime=='natural' else contiguous_mask(periods,.3,1729)
                inputs=prepare_inputs(original if regime=='natural' else mask_motion_frames(original,mask))
                input_arrays={key:getattr(inputs,key) for key in ('matrix','periods','observed','usable')};input_arrays['mask']=mask
                _save_arrays(directory/'inputs.npz',input_arrays)
                variants={};containers={};semantics={};reference=None;baseline_status=None
                for mode in MODES:
                    key=name+'--'+mode;self._claim('inference',key)
                    prediction=infer_prepared(inputs,models[mode]['model'],mode)
                    if mode=='control' and regime=='natural':loaded['validate'](prediction)
                    arrays=dict(supports=prediction.supports,latent=_encoded(prediction.latent),final=_encoded(prediction.final))
                    _save_arrays(directory/(mode+'.npz'),arrays);containers[mode]=p.sha(directory/(mode+'.npz'));semantics[mode]=p.array_identity(arrays)
                    if reference is None:
                        self._event('reference_codes_entry',case_id=cid,regime=regime,already_parsed_by_adapter=loaded['reference_loaded_by_adapter'])
                        reference=loaded['reference']()
                    self._claim('scoring',key)
                    variants[mode]=score_variant(reference,arrays['final'],inputs.periods,inputs.observed)
                    p.validate_score(variants[mode])
                    if mode=='control':baseline_status=p.check_baseline(variants[mode],binding['parity'][regime])
                if p.hashes(binding['files'])!=binding['expected'] or p.hashes({key:self.root/key for key in freeze['source_sha256']})!=freeze['source_sha256']:raise ValueError('Input/source changed during case')
                value=dict(schema_version=1,case_id=cid,cohort=cohort,role=role,regime=regime,freeze_sha256=identity,seal_sha256=seal,input_sha256=binding['expected'],
                    input_semantic_sha256=p.array_identity(input_arrays),input_container_sha256=p.sha(directory/'inputs.npz'),prediction_container_sha256=containers,prediction_semantic_sha256=semantics,
                    variants=variants,baseline_parity=baseline_status)
                p.validate_case(value,binding['expected']);p.store_exact(self.public/(name+'.json'),value)
                p.store_exact(directory/'complete.json',dict(receipt_sha256=p.sha(self.public/(name+'.json'))))
                self._event('case_complete',case_id=cid,regime=regime);(directory/'.incomplete').unlink()
            del loaded,original
        return dict(status='complete',inference_entries=60,scorings=60)

    def _array_check(self,path,container,semantic):
        if p.sha(path)!=container:raise ValueError('Private container hash changed')
        with np.load(path,allow_pickle=False) as arrays:
            if p.array_identity({key:arrays[key] for key in arrays.files})!=semantic:raise ValueError('Private semantic arrays changed')

    def _receipts(self):
        freeze,bindings,identity=self._frozen();_,seal=self._sealed();cases=self.private/'cases'
        expected={cid+'--'+regime for cid,_,_ in MATCHES for regime in REGIMES}
        if not cases.is_dir() or {path.name for path in cases.iterdir()}!=expected:raise ValueError('Missing/extra case generations')
        rows=[]
        for cid,_,_ in MATCHES:
            binding=bindings['evaluation'][cid]
            for regime in REGIMES:
                name=cid+'--'+regime;directory=cases/name;path=self.public/(name+'.json')
                if {f.name for f in directory.iterdir()}!={'inputs.npz','control.npz','memory-ablated.npz','complete.json'}:raise ValueError('Incomplete/unexpected private case')
                value=p.validate_case(p.read(path),binding['expected'])
                if (value['case_id'],value['regime'],value['freeze_sha256'],value['seal_sha256'])!=(cid,regime,identity,seal) or p.read(directory/'complete.json')!=dict(receipt_sha256=p.sha(path)):raise ValueError('Case receipt identity differs')
                self._array_check(directory/'inputs.npz',value['input_container_sha256'],value['input_semantic_sha256'])
                for mode in MODES:self._array_check(directory/(mode+'.npz'),value['prediction_container_sha256'][mode],value['prediction_semantic_sha256'][mode])
                if p.check_baseline(value['variants']['control'],binding['parity'][regime])!=value['baseline_parity']:raise ValueError('Baseline parity record changed')
                rows.append(value)
        return rows

    def _summary(self):
        fit=self._fit_status()
        if fit['status']=='stopped_control_mismatch':
            return dict(schema_version=1,status=fit['status'],freeze_sha256=p.sha(self.public/'freeze.json'),fit_sha256=p.sha(self.public/'fit.json'),fits=1,inference_entries=0,scorings=0)
        rows=self._receipts();value=summarize_cases(rows)
        value.update(freeze_sha256=p.sha(self.public/'freeze.json'),seal_sha256=p.sha(self.public/'seal.json'),
            case_receipt_sha256={row['case_id']+'/'+row['regime']:p.sha(self.public/(row['case_id']+'--'+row['regime']+'.json')) for row in rows})
        p.assert_public_report(value);return value

    def summarize(self):
        self._frozen();value=self._summary();p.assert_public_report(value);p.store_exact(self.public/'summary.json',value)
        return {key:value[key] for key in ('status','decision') if key in value}

    def verify(self):
        self._frozen();fit=self._fit_status();stopped=fit['status']=='stopped_control_mismatch'
        expected={'freeze.json','fit.json','summary.json'}
        if not stopped:expected|={'seal.json','models',*(cid+'--'+regime+'.json' for cid,_,_ in MATCHES for regime in REGIMES)}
        if {path.name for path in self.public.iterdir()}!=expected:raise ValueError('Unexpected public inventory')
        if (self.public/'summary.json').read_bytes()!=p.canonical(self._summary()):raise ValueError('Canonical summary differs')
        fits={'fit--control.json'} if stopped else {'fit--'+mode+'.json' for mode in MODES}
        claims=set(fits)
        if not stopped:claims|={kind+'--'+cid+'--'+regime+'--'+mode+'.json' for kind in ('inference','scoring') for cid,_,_ in MATCHES for regime in REGIMES for mode in MODES}
        if {path.name for path in (self.budget/'claims').iterdir()}!=claims:raise ValueError('Global attempt inventory differs')
        for name in claims:
            claim=p.read(self.budget/'claims'/name);kind,identity=name[:-5].split('--',1)
            if claim['run_id']!=self.run_id or claim['kind']!=kind or claim['identity']!=identity:raise ValueError('Attempt ownership differs')
        events=[json.loads(line) for line in (self.private/'access.jsonl').read_text(encoding='utf-8').splitlines()]
        entries=[(event['event'],event.get('identity')) for event in events if event['event'].endswith('_entry') and 'identity' in event]
        want=[('fit_entry','control')]
        if not stopped:
            want.append(('fit_entry','memory-ablated'))
            for cid,_,_ in MATCHES:
                for regime in REGIMES:
                    for mode in MODES:
                        identity=cid+'--'+regime+'--'+mode;want.extend([('inference_entry',identity),('scoring_entry',identity)])
        if entries!=want:raise ValueError('Computation entry chronology differs')
        if stopped:
            if not (self.private/'fit.incomplete').exists() or (self.private/'cases').exists():raise ValueError('Stopped reconstruction claims completion')
            failed=p.read(self.private/'failed-control-model.json')
            if p.model_digest(failed)!=fit['control_model_sha256'] or fit['control_model_sha256']==p.MODEL_SHA:raise ValueError('Stopped control identity differs')
        else:
            if {path.name for path in (self.public/'models').iterdir()}!={m+'.json' for m in MODES}:raise ValueError('Unexpected model inventory')
            if (self.private/'fit.incomplete').exists():raise ValueError('Incomplete fit')
        if (self.private/'fit-request.incomplete').exists():raise ValueError('Incomplete fitting request')
        with np.load(self.private/'training-data.npz',allow_pickle=False) as data:
            if p.array_identity({key:data[key] for key in data.files})!=fit['training_semantic_sha256']:raise ValueError('Training semantic identity changed')
        return dict(status=fit['status'],fits=1 if stopped else 2,inference_entries=0 if stopped else 60,scorings=0 if stopped else 60,freeze_sha256=p.sha(self.public/'freeze.json'))


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('command',choices=('freeze','fit','seal','evaluate','summarize','verify','retire-preflight'));parser.add_argument('--run-id',required=True)
    parser.add_argument('--successor-run-id')
    parser.add_argument('--training-worker',action='store_true',help=argparse.SUPPRESS)
    args=parser.parse_args();session=AblationSession(args.run_id)
    try:
        if args.training_worker and args.command!='fit':raise ValueError('Invalid training worker command')
        if args.command=='retire-preflight':
            if not args.successor_run_id:raise ValueError('Successor ID required')
            result=session.retire_preflight(args.successor_run_id)
        else:result=session._fit_worker() if args.training_worker else getattr(session,args.command)()
        print(json.dumps(result,sort_keys=True));return 0
    except Exception:
        if session.private.is_dir():
            import traceback
            error_path=session.private/('execution-error-'+args.command+('-worker' if args.training_worker else '')+'.log')
            try:
                p.reject_linked_ancestors(error_path)
                with error_path.open('x',encoding='utf-8') as handle:handle.write(traceback.format_exc())
            except (OSError,ValueError):pass
        print('Memory ablation stopped; preserve this generation and inspect private execution logs.',file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
