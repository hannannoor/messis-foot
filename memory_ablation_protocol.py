"""Fixed identities, public schemas and exclusive budgets for memory ablation."""
import ast
from datetime import datetime,timezone
import hashlib
import importlib.metadata
import json
from math import isclose,isfinite
from pathlib import Path
import platform
import re
import sqlite3
import subprocess
import sys
import numpy as np

from accuracy_evidence import assert_public_report
from gap_solver.input_contract import reject_linked_ancestors
from gap_solver.tactical import FEATURE_NAMES,PortableTree
import ownership_run as legacy
from memory_ablation import MODEL_SHA
from memory_ablation_training import TRAIN_MATCHES,model_digest,semantic_digest
from memory_ablation_metrics import MATCHES,REGIMES,MODES

ROOT=Path(__file__).resolve().parent
BASE='b5878dd19ae3313803329f32482c2d500246ab39'
EXPERIMENT='control-memory-2026-11-09'
ENTRIES=('memory_ablation.py','memory_ablation_training.py','memory_ablation_metrics.py','memory_ablation_protocol.py','memory_ablation_run.py')
PROTECTED={**legacy.PROTECTED,
 'docs/superpowers/specs/2026-11-09-control-memory-ablation-design.md':'7fd441b06233cd705556fcc9a53173c0a56b29762a980ea5a59875c93275fd00',
 'docs/superpowers/plans/2026-11-09-control-memory-ablation.md':'d71f17ce5d2883d1cf6b54c1f777b6f660a60288fb437c753b03a0abf21a1c94'}


def canonical(value):return (json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
def digest(value):return hashlib.sha256(canonical(value)).hexdigest()
def sha(path):return legacy._sha(path)
def read(path):
    reject_linked_ancestors(path)
    return json.loads(Path(path).read_text(encoding='utf-8'))
def utc():return datetime.now(timezone.utc).isoformat()


def write_new(path,value):
    reject_linked_ancestors(path)
    with Path(path).open('xb') as handle:handle.write(canonical(value))


def store_exact(path,value):
    write_new(path,value)
    if Path(path).read_bytes()!=canonical(value):raise ValueError('Persisted canonical bytes differ')


def hashes(paths):return {key:sha(path) for key,path in sorted(paths.items())}


def runtime_info(training=False):
    packages={}
    for name in ('numpy','pandas')+(('scipy','scikit-learn','joblib','threadpoolctl') if training else ()):
        try:packages[name]=importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:packages[name]=None
    return dict(python=platform.python_version(),platform=platform.platform(),sqlite=sqlite3.sqlite_version,
        executable_sha256=sha(sys.executable),packages=packages,
        threads={key:__import__('os').environ.get(key) for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS')})


def thread_environment():
    env=__import__('os').environ.copy()
    for key in ('PYTHONHOME','PYTHONPATH','PYTHONEXECUTABLE','__PYVENV_LAUNCHER__'):env.pop(key,None)
    env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1')
    return env


def environments(root,scoring_python=None,scoring_threads=None):
    root=Path(root);python=root/'.superpowers/memory-ablation/venv/Scripts/python.exe'
    if not python.is_file():raise ValueError('Pinned local training environment missing')
    code='import json,memory_ablation_protocol as p;print(json.dumps(p.runtime_info(training=True)))'
    trained=json.loads(subprocess.check_output([str(python),'-c',code],cwd=root,env=thread_environment(),text=True))
    pins={'numpy':'1.26.4','pandas':'2.2.2','scipy':'1.13.1','scikit-learn':'1.5.1'}
    if not trained['python'].startswith('3.12.') or any(trained['packages'][key]!=value for key,value in pins.items()):
        raise ValueError('Historical training dependency pins differ')
    provenance=root/'.superpowers/memory-ablation/environment-provenance.json'
    prov=read(provenance)
    if prov['requirements_lock_sha256']!=sha(root/'requirements-memory-ablation.lock'):raise ValueError('Environment lock changed')
    scoring_python=Path(scoring_python or sys.executable).resolve()
    scoring_env=__import__('os').environ.copy()
    for key in ('PYTHONHOME','PYTHONPATH','PYTHONEXECUTABLE','__PYVENV_LAUNCHER__'):scoring_env.pop(key,None)
    if scoring_threads is not None:
        for key,value in scoring_threads.items():
            if key not in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):raise ValueError('Unexpected scoring thread setting')
            if value is None:scoring_env.pop(key,None)
            else:scoring_env[key]=value
    score_code='import json,memory_ablation_protocol as p;print(json.dumps(p.runtime_info()))'
    scoring=json.loads(subprocess.check_output([str(scoring_python),'-c',score_code],cwd=root,env=scoring_env,text=True))
    return dict(training=trained,scoring=scoring,training_python=str(python.resolve()),
        scoring_python=str(scoring_python),lock_sha256=sha(root/'requirements-memory-ablation.lock'),provenance_sha256=sha(provenance))


def public_environment(value):return {key:v for key,v in value.items() if not key.endswith('_python')}


def trusted_json(root,name):
    original=subprocess.check_output(['git','show',BASE+':'+name],cwd=root)
    if hashlib.sha256(original).hexdigest()!=sha(Path(root)/name):raise ValueError('Historical receipt changed before freeze')
    return json.loads(original)


def source_paths(root):
    root=Path(root);pending=[root/name for name in ENTRIES];found={}
    while pending:
        path=pending.pop();name=path.relative_to(root).as_posix()
        if name in found:continue
        if not path.is_file():raise ValueError('Missing source entry')
        found[name]=path;package=name.split('/')[:-1]
        for node in ast.walk(ast.parse(path.read_text(encoding='utf-8-sig'))):
            names=[]
            if isinstance(node,ast.Import):names=[a.name.split('.') for a in node.names]
            elif isinstance(node,ast.ImportFrom):
                base=(package[:len(package)-node.level+1] if node.level else [])+(node.module.split('.') if node.module else [])
                names=[base]+[base+[a.name] for a in node.names if a.name!='*']
            for parts in names:
                for size in range(1,len(parts)+1):
                    stem=root.joinpath(*parts[:size])
                    for candidate in (stem.with_suffix('.py'),stem/'__init__.py'):
                        if candidate.is_file():pending.append(candidate)
    extras=tuple(PROTECTED)+('requirements-training.txt','requirements-memory-ablation.lock','benchmark/provenance.json',
        'docs/superpowers/specs/2026-11-09-memory-ablation-preflight-recovery.md',
        'docs/superpowers/specs/2026-11-09-memory-ablation-cache-frame-amendment.md',
        'reports/ball-gap/comparison-freeze.json','reports/ownership-path/2026-11-09-natural-v2/freeze.json',
        'reports/wcsf-transfer-v2/acquisition.json','reports/wcsf-transfer-v2/geometry.json','reports/wcsf-transfer-v2/predictions-seal.json','reports/wcsf-transfer-v2/results.json')
    for name in extras:
        if not (root/name).is_file():raise ValueError('Required protocol source missing')
        found[name]=root/name
    for cid,cohort,role in MATCHES:
        for regime in REGIMES:
            if cid=='wcsf-used-match':continue
            suffix='natural' if regime=='natural' else 'masked'
            if role=='fitting-overlap' or cid in ('skillcorner-1874553','skillcorner-1886347'):
                name=('reports/ownership-path/2026-11-09-natural-v2/'+cid+'.json' if regime=='natural'
                    else 'reports/cadence-v2/cases/'+cid+'-'+regime+'.json')
            else:name='reports/ball-gap/regression/'+cid+'-'+suffix+'.json'
            trusted_json(root,name);found[name]=root/name
    return found


def _prior_hashes(files,old):
    result={}
    for key,path in files.items():
        suffix=next((s for s in ('.metadata.json','.features.npz','.reference.npz') if str(path).endswith(s)),None)
        choices=[value for name,value in old.items() if (name.endswith(suffix) if suffix else name.replace('\\','/').split('/')[-1]==path.name)]
        if len(choices)!=1:raise ValueError('Ambiguous historical input identity')
        result[key]=choices[0]
    return result


def _parity_from_variant(row):
    return dict(metrics={key:row['metrics'][key] for key in ('spell_f1_mean','accuracy')},
        n_gt=row['metrics']['n_gt_spells'],n_pred=row['metrics']['n_pred_spells'],
        per_iou={t:{k:v[k] for k in ('n_matched','n_missed','n_spurious','f1')} for t,v in row['spell_counts'].items()})


def cached_evaluation_files(workspace,cid,prior):
    cohort,match=cid.split('-',1)
    if cohort not in ('skillcorner','dfl'):raise ValueError('Unknown cached provider')
    directory=Path(workspace)/('independent-reference' if cohort=='skillcorner' else 'external-reference')
    prefix=directory/'cache'/(match+'-detected' if cohort=='skillcorner' else match)
    files={cid+'/'+s:Path(str(prefix)+s) for s in ('.metadata.json','.features.npz','.reference.npz')}
    if cohort=='dfl':
        names=[key.replace('\\','/').split('/')[-1] for key in prior if key.endswith('.xml')]
        if len(names)!=2 or len(set(names))!=2 or sum('matchinformation' in name for name in names)!=1 or sum('positions_raw_observed' in name for name in names)!=1 or any('DFL-MAT-'+match not in name for name in names):
            raise ValueError('Exact retained DFL metadata/positions names required')
        files.update({cid+'/'+name:directory/'raw'/name for name in names})
    return files


def training_files(workspace,match,records):
    prefix=Path(workspace)/'external-reference/cache'/match
    files={'training/'+match+'/'+s:Path(str(prefix)+s) for s in ('.metadata.json','.features.npz','.reference.npz')}
    metadata=read(Path(str(prefix)+'.metadata.json'));notes=metadata['notes']
    if metadata['match_id']!='DFL-MAT-'+match or notes.get('fps')!=25 or notes.get('label_features_excluded')!=['BallStatus','BallPossession','events','match/team identities'] or notes.get('unknown_reference_preserved') is not True:
        raise ValueError('Training cache provenance contract differs')
    chosen=[record for record in records if 'DFL-MAT-'+match in record['name'] and ('matchinformation' in record['name'] or 'positions_raw_observed' in record['name'])]
    if len(chosen)!=2:raise ValueError('Expected exact pinned training source pair')
    for record in chosen:
        name=record['name']
        if Path(name).name!=name:raise ValueError('Unsafe training provenance filename')
        source=Path(workspace)/'external-reference/raw'/name;reject_linked_ancestors(source)
        md5=hashlib.md5()
        with source.open('rb') as handle:
            for block in iter(lambda:handle.read(1024*1024),b''):md5.update(block)
        if source.stat().st_size!=record['size'] or md5.hexdigest()!=record['md5']:raise ValueError('Training raw source differs from retained provenance')
        files['training/'+match+'/'+name]=source
    return files


def input_bindings(root):
    root=Path(root);workspace=root.parent
    older=trusted_json(root,'reports/ball-gap/comparison-freeze.json')['input_sha256']
    pilot=trusted_json(root,'reports/ownership-path/2026-11-09-natural-v2/freeze.json')['input_sha256']
    result=dict(training={},evaluation={})
    provenance=trusted_json(root,'benchmark/provenance.json')
    for match in TRAIN_MATCHES:
        files=training_files(workspace,match,provenance['files'])
        result['training'][match]=dict(files=files,expected=hashes(files))
    for cid,cohort,role in MATCHES:
        parity={};files={}
        if cohort=='wcsf':
            base=workspace/'wcsf-reference/wcsf-2026-11-09-2'
            files={cid+'/'+name:base/name for name in legacy.WCSF_SHA};expected={cid+'/'+k:v for k,v in legacy.WCSF_SHA.items()}
            old=trusted_json(root,'reports/wcsf-transfer-v2/results.json')['match']['w0-c32-neutral-missing']
            parity['natural']=dict(metrics={key:old['metrics'][key] for key in ('spell_f1_mean','accuracy')},n_gt=old['spells']['n_gt'],n_pred=old['spells']['n_pred'],
                per_iou={t:{k:v[k] for k in ('n_matched','n_missed','n_spurious','f1')} for t,v in old['spells']['per_iou'].items()})
            parity[REGIMES[1]]=None
        else:
            prior=pilot.get(cid,older.get(cid,{}));files=cached_evaluation_files(workspace,cid,prior)
            expected=_prior_hashes(files,prior)
            for regime in REGIMES:
                diagnostic=cid in pilot
                name=('reports/ownership-path/2026-11-09-natural-v2/'+cid+'.json' if regime=='natural' else 'reports/cadence-v2/cases/'+cid+'-'+regime+'.json') if diagnostic else 'reports/ball-gap/regression/'+cid+('-natural.json' if regime=='natural' else '-masked.json')
                old=trusted_json(root,name)
                if diagnostic and regime=='natural':
                    b=old['diagnostic']['baseline'];parity[regime]=dict(metrics={key:b['metrics'][key] for key in ('spell_f1_mean','accuracy')},n_gt=b['spells']['n_gt'],n_pred=b['spells']['n_pred'],
                        per_iou={t:{k:v[k] for k in ('n_matched','n_missed','n_spurious','f1')} for t,v in b['spells']['per_iou'].items()})
                else:parity[regime]=_parity_from_variant(old['variants']['frozen-control' if diagnostic else 'w0-c32-neutral-missing'])
        result['evaluation'][cid]=dict(files=files,expected=expected,parity=parity)
    return result


def protocol():
    return dict(experiment=EXPERIMENT,model_sha256=MODEL_SHA,neutral_home=0.,neutral_away=0.,neutral_age=10.,
        max_fits=2,max_inferences=60,max_scorings=60,mask_rate=.3,mask_seed=1729,training_seed=1729,
        tree_depth=4,minimum_leaf=125,switch_cost=32.,motion_weight=0.,floor=1e-6,
        cases={cid:dict(cohort=p,role=role) for cid,p,role in MATCHES},regimes={r:True for r in REGIMES},
        primary_gain_threshold=1e-6,maximum_spell_loss=.01,maximum_D_loss=.01,maximum_short_recall_loss=.02,
        short_length_frames=25,short_support_threshold=20,comparison_slack=1e-6,fresh_holdout=False,automatic_promotion=False)


def validate_model(value,mode):
    schema=dict(mode=(mode,),model_sha256='hash',portable_all_rows_match=(True,),rows='count',class_support={k:'count' for k in 'HAD'},
        training_sha256={k:'hash' for k in ('matrix','target','weights','row_identity','fitted_matrix')},
        parameters=dict(max_depth=(4,),min_samples_leaf=(125,),random_state=(1729,)))
    if not isinstance(value,dict) or 'model' not in value:raise ValueError('Missing portable model')
    metadata={key:v for key,v in value.items() if key!='model'};legacy._shape(metadata,schema);assert_public_report(metadata)
    model=value['model'];required={'feature_names','children_left','children_right','feature','threshold','probabilities'}
    if not isinstance(model,dict) or set(model)!=required or model['feature_names']!=list(FEATURE_NAMES):raise ValueError('Unknown portable model schema')
    n=len(model['children_left'])
    if not 1<=n<=31 or any(type(x) is not int for key in ('children_left','children_right','feature') for x in model[key]):raise ValueError('Invalid bounded tree')
    PortableTree(model)
    if model_digest(model)!=value['model_sha256'] or sum(value['class_support'].values())!=value['rows']:raise ValueError('Model identity/support differs')
    if mode=='control' and value['model_sha256']!=MODEL_SHA:raise ValueError('Reconstructed control digest differs')
    if mode=='memory-ablated' and set(model['feature'])&{15,16,17}:raise ValueError('Ablation split on retained-owner feature')
    return value


SCORE_SCHEMA=dict(schema_version=(1,),support={k:'count' for k in ('frames','known','unknown','H','A','D')},
    predicted_on_known={k:'count' for k in 'HADX'},metrics=legacy.METRICS,spells=legacy.SPELL_SCHEMA,confusion='confusion',
    dead=dict(n_gt='count',n_pred='count',n_matched='count',precision='nullable',recall='nullable'),known_live_false_D_rate='nullable',
    short_spells=dict(n_gt='count',n_matched='count',recall='nullable'),all_state_boundaries={str(t):legacy.BOUNDARY for t in (12,25)},
    HA_boundaries={str(t):legacy.BOUNDARY for t in (12,25)},strata={name:{key:'count' for key in ('known','correct','ownership_swaps','false_D','missed_D')} for name in ('ball_observed','ball_missing')})


def validate_score(value):
    legacy._shape(value,SCORE_SCHEMA);assert_public_report(value)
    s=value['support'];cm=value['confusion']
    if sum(s[k] for k in 'HAD')!=s['known'] or s['known']+s['unknown']!=s['frames'] or [sum(row) for row in cm]!=[s[k] for k in ('H','A','D','unknown')]:raise ValueError('Score support differs')
    if value['predicted_on_known']!={name:sum(cm[i][j] for i in range(3)) for j,name in enumerate('HADX')}:raise ValueError('Prediction support differs')
    legacy._spell_counts(value['spells'],s['known'])
    if not legacy._close(value['metrics']['spell_f1_mean'],value['spells']['mean_f1']):raise ValueError('Spell metric differs')
    for row in (value['short_spells'],):
        if row['n_matched']>row['n_gt'] or not legacy._close(row['recall'],row['n_matched']/row['n_gt'] if row['n_gt'] else None):raise ValueError('Short-spell support differs')
    dead=value['dead']
    if (dead['n_gt'],dead['n_pred'],dead['n_matched'])!=(s['D'],value['predicted_on_known']['D'],cm[2][2]):raise ValueError('D support differs')
    for key,denom in (('precision',dead['n_pred']),('recall',dead['n_gt'])):
        if not legacy._close(dead[key],dead['n_matched']/denom if denom else None):raise ValueError('D ratio differs')
    if sum(row['known'] for row in value['strata'].values())!=s['known']:raise ValueError('Observation support differs')
    for row in list(value['HA_boundaries'].values())+list(value['all_state_boundaries'].values()):
        if row['n_matched']+row['n_missed']!=row['n_gt'] or row['n_matched']+row['n_spurious']!=row['n_pred'] or row['matched_latency_denominator']!=row['n_matched']:raise ValueError('Boundary counts differ')
    return value


def validate_case(value,expected_inputs):
    ids=tuple(cid for cid,_,_ in MATCHES)
    schema=dict(schema_version=(1,),case_id=ids,cohort=('skillcorner','dfl','wcsf'),role=('fit-disjoint','fitting-overlap'),regime=REGIMES,
        freeze_sha256='hash',seal_sha256='hash',input_sha256={k:'hash' for k in expected_inputs},input_semantic_sha256='hash',input_container_sha256='hash',
        prediction_container_sha256={m:'hash' for m in MODES},prediction_semantic_sha256={m:'hash' for m in MODES},
        variants={m:SCORE_SCHEMA for m in MODES},baseline_parity=('passed','not_previously_scored'))
    legacy._shape(value,schema);assert_public_report(value)
    if value['input_sha256']!=expected_inputs:raise ValueError('Trusted case input keys/hash values differ')
    expected=next((p,role) for cid,p,role in MATCHES if cid==value['case_id'])
    if (value['cohort'],value['role'])!=expected:raise ValueError('Case role/provider differs')
    for row in value['variants'].values():validate_score(row)
    if value['variants']['control']['support']!=value['variants']['memory-ablated']['support']:raise ValueError('Variant references differ')
    return value


def check_baseline(score,expected):
    if expected is None:return 'not_previously_scored'
    for key,value in expected['metrics'].items():
        if not isclose(score['metrics'][key],value,abs_tol=1e-6,rel_tol=1e-10):raise ValueError('Historical baseline metric parity failed')
    spells=score['spells']
    if (spells['n_gt'],spells['n_pred'])!=(expected['n_gt'],expected['n_pred']) or set(spells['per_iou'])!=set(expected['per_iou']):raise ValueError('Historical spell support differs')
    for threshold,row in expected['per_iou'].items():
        for key,value in row.items():
            measured=spells['per_iou'][threshold][key]
            if not (isclose(measured,value,abs_tol=1e-6,rel_tol=1e-10) if key=='f1' else measured==value):raise ValueError('Historical IoU parity failed')
    return 'passed'


def array_identity(arrays):return digest({key:semantic_digest(value) for key,value in sorted(arrays.items())})


def safe_run_id(run_id):
    reserved={'CON','PRN','AUX','NUL',*('COM'+str(i) for i in range(1,10)),*('LPT'+str(i) for i in range(1,10))}
    if not isinstance(run_id,str) or not re.fullmatch('[a-z0-9][a-z0-9-]{0,63}',run_id) or run_id.upper() in reserved:raise ValueError('Unsafe run ID')
    return run_id
