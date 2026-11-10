from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager,ExitStack
import copy
import hashlib
import io
import ast
import os
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from contextlib import redirect_stderr
import numpy as np

from gap_solver.motion import motion_frame
from gap_solver.tactical import FEATURE_NAMES
from gap_solver.tactical_model import FROZEN_MODEL
from memory_ablation_training import TrainingData,semantic_digest,model_digest,ControlMismatch
from memory_ablation_metrics import MATCHES,REGIMES,MODES
try:
    import memory_ablation_protocol as protocol
    import memory_ablation_run as runner
except ImportError:
    protocol=runner=None

ROOT=Path(__file__).resolve().parents[1]


@contextmanager
def fixture():
    with tempfile.TemporaryDirectory() as tmp,ExitStack() as stack:
        root=Path(tmp)/'code';root.mkdir()
        release=json.loads((ROOT/'release/manifest.json').read_text(encoding='utf-8'))
        names=set(release['sources'])|{'competition_release.py',*protocol.PROTECTED}
        for name in names:
            target=root/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
        sources={name:root/name for name in protocol.ENTRIES}
        for path in sources.values():path.write_bytes(b'# synthetic source identity\n')
        bindings=dict(training={},evaluation={})
        for category,ids in (('training',('J03WOH','J03WOY','J03WPY','J03WMX')),('evaluation',tuple(c[0] for c in MATCHES))):
            for cid in ids:
                path=root/(category+'-'+cid+'.bin');path.write_bytes(('synthetic '+category+cid).encode())
                bindings[category][cid]=dict(files={category+'/'+cid:path},expected={category+'/'+cid:hashlib.sha256(path.read_bytes()).hexdigest()},parity={regime:None for regime in REGIMES})
        runtime=protocol.runtime_info(training=True)
        env=dict(training=runtime,scoring=protocol.runtime_info(),training_python=str(Path(__import__('sys').executable)),
                 scoring_python=str(Path(__import__('sys').executable)),lock_sha256='a'*64,provenance_sha256='b'*64)
        data=TrainingData(np.zeros((6,18),dtype=np.float32),np.asarray([0,1,2]*2,dtype=np.uint8),np.full(6,1/6),np.column_stack([np.zeros(6),np.zeros(6),np.arange(6)]).astype(np.int64),())
        candidate=dict(feature_names=list(FEATURE_NAMES),children_left=[-1],children_right=[-1],feature=[-2],threshold=[-2.],probabilities=[[.4,.3,.3]])
        def fitted(data,on_fit_entry,expected_control_sha=None):
            result={}
            for mode,model in (('control',FROZEN_MODEL['model']),('memory-ablated',candidate)):
                on_fit_entry(mode)
                result[mode]=dict(mode=mode,model=copy.deepcopy(model),model_sha256=model_digest(model),portable_all_rows_match=True,rows=6,
                    class_support=dict(H=2,A=2,D=2),training_sha256={k:semantic_digest(getattr(data,k)) for k in ('matrix','target','weights','row_identity')},
                    parameters=dict(max_depth=4,min_samples_leaf=125,random_state=1729))
                result[mode]['training_sha256']['fitted_matrix']=semantic_digest(data.matrix)
            return result
        def load(cid,binding):
            frames=[motion_frame(1,None,[(1.,1.)]*3,[(70.,1.)]*3) for _ in range(5)]
            return dict(frames=frames,reference=lambda:np.full(5,2,dtype=np.uint8),validate=lambda prediction:None,reference_loaded_by_adapter=True)
        stack.enter_context(patch.object(protocol,'source_paths',return_value=sources))
        stack.enter_context(patch.object(protocol,'input_bindings',return_value=bindings))
        stack.enter_context(patch.object(protocol,'environments',return_value=env))
        stack.enter_context(patch.object(runner,'load_training',return_value=data))
        stack.enter_context(patch.object(runner,'fit_pair',side_effect=fitted))
        stack.enter_context(patch.object(runner,'load_evaluation',side_effect=load))
        stack.enter_context(patch.object(runner,'run_training_worker',side_effect=lambda session:session._fit_worker()))
        yield root,bindings,sources,env


class MemoryProtocol(unittest.TestCase):
    def setUp(self):self.assertIsNotNone(runner,'Bounded memory experiment runner is missing')

    def test_DFL_raw_names_come_from_the_retained_manifest_not_a_fixed_competition(self):
        raw=('DFL_02_01_matchinformation_DFL-COM-000001_DFL-MAT-J03WN1.xml',
             'DFL_04_03_positions_raw_observed_DFL-COM-000001_DFL-MAT-J03WN1.xml')
        prior={**{'external-reference\\cache\\J03WN1'+s:'a'*64 for s in ('.metadata.json','.features.npz','.reference.npz')},
               **{'external-reference/raw/'+name:'b'*64 for name in raw}}
        files=protocol.cached_evaluation_files(Path('synthetic-workspace'),'dfl-J03WN1',prior)
        self.assertEqual({path.name for path in files.values() if path.suffix=='.xml'},set(raw))
        self.assertEqual(len(protocol._prior_hashes(files,prior)),5)

    def test_training_sources_match_pinned_provenance_without_opening_arrays(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace=Path(tmp);cache=workspace/'external-reference/cache';raw=workspace/'external-reference/raw'
            cache.mkdir(parents=True);raw.mkdir(parents=True)
            prefix=cache/'J03WOH'
            Path(str(prefix)+'.metadata.json').write_text(json.dumps(dict(match_id='DFL-MAT-J03WOH',notes=dict(fps=25,
                label_features_excluded=['BallStatus','BallPossession','events','match/team identities'],unknown_reference_preserved=True))))
            for suffix in ('.features.npz','.reference.npz'):Path(str(prefix)+suffix).write_bytes(b'synthetic unopened container')
            records=[]
            for name in ('DFL_02_01_matchinformation_DFL-COM-000002_DFL-MAT-J03WOH.xml','DFL_04_03_positions_raw_observed_DFL-COM-000002_DFL-MAT-J03WOH.xml'):
                (raw/name).write_bytes(b'synthetic-source');records.append(dict(name=name,size=16,md5=hashlib.md5(b'synthetic-source').hexdigest()))
            files=protocol.training_files(workspace,'J03WOH',records)
            self.assertEqual(len(files),5)
            (raw/records[0]['name']).write_bytes(b'changed')
            with self.assertRaises(ValueError):protocol.training_files(workspace,'J03WOH',records)

    def test_full_synthetic_lifecycle_and_read_only_verify(self):
        with fixture() as (root,_,__,___):
            s=runner.AblationSession('synthetic',root=root);s.freeze();s.fit();s.seal();s.evaluate();s.summarize()
            with patch.object(runner,'prepare_inputs',side_effect=AssertionError('verify prepared')), \
                 patch.object(runner,'fit_pair',side_effect=AssertionError('verify fitted')), \
                 patch.object(runner,'infer_prepared',side_effect=AssertionError('verify inferred')), \
                 patch.object(runner,'score_variant',side_effect=AssertionError('verify scored')):
                result=s.verify()
            self.assertEqual((result['fits'],result['inference_entries'],result['scorings']),(2,60,60))

    def test_global_run_ownership_and_duplicate_stages_do_not_reset_budget(self):
        with fixture() as (root,_,__,___):
            s=runner.AblationSession('original',root=root);s.freeze();s.fit()
            for other in (runner.AblationSession('new-run',root=root),runner.AblationSession('other-checkout',root=root.parent/'code2')):
                with self.assertRaises((FileExistsError,ValueError)):other.freeze()
            with self.assertRaises((ValueError,FileExistsError)):s.fit()
            s.seal();s.evaluate()
            with self.assertRaises((ValueError,FileExistsError)):s.evaluate()

    def test_concurrent_freeze_has_one_winner(self):
        with fixture() as (root,_,__,___):
            def worker(i):
                try:runner.AblationSession('race'+str(i),root=root).freeze();return True
                except (FileExistsError,ValueError):return False
            with ThreadPoolExecutor(max_workers=2) as pool:result=list(pool.map(worker,range(2)))
            self.assertEqual(sum(result),1)

    def test_frozen_inputs_sources_runtime_and_masks_reject_drift(self):
        for kind in ('input','source','environment','freeze'):
            with fixture() as (root,bindings,sources,env),self.subTest(kind=kind):
                s=runner.AblationSession('drift',root=root);s.freeze()
                if kind=='input':next(iter(bindings['training'].values()))['files'][next(iter(next(iter(bindings['training'].values()))['files']))].write_bytes(b'changed')
                elif kind=='source':next(iter(sources.values())).write_bytes(b'changed')
                elif kind=='environment':env['scoring']['python']='changed'
                else:
                    p=s.public/'freeze.json';v=json.loads(p.read_text());v['protocol']['mask_seed']=3;p.write_text(json.dumps(v))
                with self.assertRaises(ValueError):s.fit()

    def test_source_case_inventory_and_prefreeze_release_component_drift_fail(self):
        for kind in ('source','case','release'):
            with fixture() as (root,bindings,sources,env),self.subTest(kind=kind):
                if kind=='source':sources.pop(protocol.ENTRIES[0])
                elif kind=='case':bindings['evaluation'].pop(MATCHES[0][0])
                else:(root/'gap_solver/tactical.py').write_bytes(b'edited')
                with self.assertRaises(ValueError):runner.AblationSession('invalid',root=root).freeze()

    def test_interrupted_fit_and_scoring_preserve_claims_and_cannot_resume(self):
        for kind in ('fit','score'):
            with fixture() as (root,_,__,___),self.subTest(kind=kind):
                s=runner.AblationSession('interrupted',root=root);s.freeze()
                if kind=='fit':
                    def broken(data,callback,**kwargs):callback('control');raise RuntimeError('synthetic interrupted fit')
                    with patch.object(runner,'fit_pair',side_effect=broken),self.assertRaises(RuntimeError):s.fit()
                    with self.assertRaises((ValueError,FileExistsError)):s.fit()
                else:
                    s.fit();s.seal()
                    with patch.object(runner,'score_variant',side_effect=RuntimeError('synthetic interrupted score')),self.assertRaises(RuntimeError):s.evaluate()
                    with self.assertRaises((ValueError,FileExistsError)):s.evaluate()
                with self.assertRaises(ValueError):s.verify()

    def test_stopped_control_reconstruction_is_honest_and_never_enters_candidate(self):
        with fixture() as (root,_,__,___):
            s=runner.AblationSession('stopped',root=root);s.freeze()
            def mismatch(data,callback,**kwargs):
                callback('control')
                model=dict(feature_names=list(FEATURE_NAMES),children_left=[-1],children_right=[-1],feature=[-2],threshold=[-2.],probabilities=[[.4,.3,.3]])
                raise ControlMismatch(model,dict(mode='control',model_sha256=model_digest(model)))
            with patch.object(runner,'fit_pair',side_effect=mismatch):result=s.fit()
            self.assertEqual(result['status'],'stopped_control_mismatch')
            with self.assertRaises(ValueError):s.seal()
            with self.assertRaises(ValueError):s.evaluate()
            s.summarize();verified=s.verify()
            self.assertEqual((verified['fits'],verified['inference_entries'],verified['scorings']),(1,0,0))

    def test_models_case_egress_and_summary_bytes_reject_extra_keys_and_arrays(self):
        with fixture() as (root,bindings,__,___):
            s=runner.AblationSession('egress',root=root);s.freeze();s.fit();s.seal();s.evaluate();s.summarize()
            path=s.public/(MATCHES[0][0]+'--natural.json');good=json.loads(path.read_text())
            bad=copy.deepcopy(good);bad['input_sha256']['private/coordinates/1/2']='a'*64
            with self.assertRaises(ValueError):protocol.validate_case(bad,bindings['evaluation'][MATCHES[0][0]]['expected'])
            bad=copy.deepcopy(good);bad['variants']['control']['notes']=[dict(start=1,owner='H')]
            with self.assertRaises(ValueError):protocol.validate_case(bad,good['input_sha256'])
            model=json.loads((s.public/'models/memory-ablated.json').read_text());model['model']['secret']=[1,2]
            with self.assertRaises(ValueError):protocol.validate_model(model,'memory-ablated')
            p=s.public/'summary.json';original=p.read_bytes();p.write_bytes(b'{"schema_version":[1,2],'+original[1:])
            with self.assertRaises(ValueError):s.verify()
            p.write_bytes(original);extra=s.public/'extra.json';extra.write_text('{}')
            with self.assertRaises(ValueError):s.verify()

    def test_persisted_case_and_model_corruption_do_not_clear_incomplete(self):
        for kind in ('case','model'):
            with fixture() as (root,_,__,___),self.subTest(kind=kind):
                s=runner.AblationSession('persistence',root=root);s.freeze();write=protocol.write_new
                def corrupt(path,value):
                    value=copy.deepcopy(value)
                    if kind=='model' and path.name=='control.json':value['model_sha256']='0'*64
                    if kind=='case' and path.name.endswith('--natural.json'):value['freeze_sha256']='0'*64
                    write(path,value)
                if kind=='model':
                    with patch.object(protocol,'write_new',side_effect=corrupt),self.assertRaises(ValueError):s.fit()
                    with self.assertRaises(ValueError):s.seal()
                else:
                    s.fit();s.seal()
                    with patch.object(protocol,'write_new',side_effect=corrupt),self.assertRaises(ValueError):s.evaluate()
                    with self.assertRaises(ValueError):s.verify()

    def test_cli_failure_retains_private_details_without_stderr_disclosure(self):
        with fixture() as (root,_,__,___):
            s=runner.AblationSession('cli-failure',root=root);s.freeze();stderr=io.StringIO()
            with patch.object(runner,'AblationSession',return_value=s), \
                 patch.object(runner,'run_training_worker',side_effect=RuntimeError('synthetic-private-token')), \
                 patch.object(__import__('sys'),'argv',['memory_ablation_run.py','fit','--run-id','cli-failure']),redirect_stderr(stderr):
                self.assertEqual(runner.main(),1)
            self.assertNotIn('synthetic-private-token',stderr.getvalue());self.assertNotIn('Traceback',stderr.getvalue())
            details=list(s.private.glob('execution-error-*.log'))
            self.assertEqual(len(details),1)
            self.assertIn('synthetic-private-token',details[0].read_text(encoding='utf-8'))
            with self.assertRaises((ValueError,FileExistsError)):s.fit()

    def test_owned_reads_and_private_roots_reject_linked_ancestors(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);target=base/'target';target.mkdir();(target/'value.json').write_text('{"synthetic":1}')
            def linked_directory(link,destination):
                if os.name=='nt':
                    result=subprocess.run(['cmd','/c','mklink','/J',str(link),str(destination)],capture_output=True)
                    if result.returncode:self.skipTest('Native Windows junction creation unavailable')
                else:os.symlink(destination,link,target_is_directory=True)
            link=base/'linked';linked_directory(link,target)
            with self.assertRaises(ValueError):protocol.read(link/'value.json')
            root=base/'code';root.mkdir();outside=base/'outside';outside.mkdir()
            linked_directory(base/'memory-ablation-reference',outside)
            with self.assertRaises(ValueError):runner.AblationSession('linked-root',root=root)

    def test_actual_dependency_inventory_and_python39_grammar(self):
        paths=protocol.source_paths(ROOT)
        required=set(protocol.ENTRIES)|{'gap_solver/tactical.py','gap_solver/selection.py','gap_solver/external.py',
            'gap_solver/skillcorner.py','gap_solver/dfl_motion.py','wcsf_geometry.py','wcsf_reference.py','requirements-memory-ablation.lock'}
        self.assertTrue(required<=set(paths),required-set(paths))
        for name in protocol.ENTRIES:ast.parse((ROOT/name).read_text(encoding='utf-8'),feature_version=(3,9))

    def test_training_worker_observes_the_fixed_scoring_interpreter(self):
        training_python=ROOT/'.superpowers/memory-ablation/venv/Scripts/python.exe'
        if not training_python.is_file():self.skipTest('Provision the approved pinned training environment')
        scoring=str(Path('C:/Python314/python.exe'))
        if not Path(scoring).is_file():self.skipTest('This reference Windows runtime is unavailable')
        threads=protocol.runtime_info()['threads']
        code=('import json,memory_ablation_protocol as p;v=p.environments(p.ROOT,scoring_python='+repr(scoring)+
            ',scoring_threads='+repr(threads)+');print(json.dumps({k:v[k]["python"] for k in ("training","scoring")}))')
        result=subprocess.run([str(training_python),'-c',code],cwd=ROOT,env=protocol.thread_environment(),capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(json.loads(result.stdout),dict(training='3.12.13',scoring='3.14.5'))

    def test_zero_entry_preflight_retirement_preserves_owner_and_shared_budget(self):
        with fixture() as (root,_,__,___):
            old=runner.AblationSession('preflight-failed',root=root);old.freeze();original_owner=(old.budget/'experiment-owner.json').read_bytes()
            with self.assertRaises(ValueError):old.retire_preflight('successor')
            protocol.store_exact(old.private/'fit-request.incomplete',dict(utc=protocol.utc()))
            for name in ('execution-error-fit-worker.log','execution-error-fit.log'):(old.private/name).write_text('synthetic terminated worker preflight')
            old.retire_preflight('successor')
            self.assertEqual((old.budget/'experiment-owner.json').read_bytes(),original_owner)
            self.assertTrue((old.private/'fit-request.incomplete').exists())
            self.assertTrue((old.public/'preflight-status.json').is_file())
            new=runner.AblationSession('successor',root=root);new.freeze();new.fit();new.seal();new.evaluate();new.summarize()
            verified=new.verify();self.assertEqual((verified['fits'],verified['scorings']),(2,60))
            with self.assertRaises((ValueError,FileExistsError)):new.retire_preflight('third')
            with self.assertRaises((ValueError,FileExistsError)):runner.AblationSession('third',root=root).freeze()

    def test_preflight_retirement_refuses_any_consumed_scientific_entry(self):
        with fixture() as (root,_,__,___):
            s=runner.AblationSession('consumed',root=root);s.freeze()
            for name in ('execution-error-fit-worker.log','execution-error-fit.log'):(s.private/name).write_text('synthetic failure')
            s._claim('fit','control')
            with self.assertRaises(ValueError):s.retire_preflight('new-run')


if __name__=='__main__':unittest.main()
