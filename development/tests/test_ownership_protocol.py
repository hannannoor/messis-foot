from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager,ExitStack
import copy
import ast
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
import numpy as np

from gap_solver.motion import motion_frame
import ownership_diagnosis as analysis
try:
    import ownership_run as runner
except ImportError:
    runner=None

ROOT=Path(__file__).resolve().parents[1]


@contextmanager
def fixture():
    with tempfile.TemporaryDirectory() as directory,ExitStack() as stack:
        root=Path(directory)/'code';root.mkdir()
        for name in ('competition_release.py','docs/superpowers/specs/2026-11-08-ownership-path-diagnosis-design.md',
                     'docs/superpowers/plans/2026-11-08-ownership-path-diagnosis.md',
                     *json.loads((ROOT/'release/manifest.json').read_text())['sources']):
            target=root/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
        sources={name:root/name for name in ('ownership_paths.py','ownership_diagnosis.py','ownership_run.py')}
        for path in sources.values():path.write_text('# controlled synthetic source identity\n')
        bindings={}
        for case_id in runner.CASE_IDS:
            path=root/(case_id+'.bin');path.write_bytes(('synthetic '+case_id).encode())
            parity=({'pilot':dict(frames=5 if case_id.startswith('skillcorner') else 0,wrong_team=0,
                     raw_correct_final_wrong=0,raw_wrong_final_correct=0)} if case_id!='wcsf-used-match' else
                     {'wcsf':dict(frames=5,known=5,n_gt=0,n_pred=0,n_matched=0,n_missed=0,n_spurious=0)})
            bindings[case_id]=dict(cohort=case_id.split('-')[0],files={case_id+'/fixture':path},
                                  expected={case_id+'/fixture':hashlib.sha256(path.read_bytes()).hexdigest()},parity=parity)
        def load(case_id,binding):
            frames=[motion_frame(1,None,[(1.,1.),(2.,2.),(3.,3.)],[(70.,1.),(71.,2.),(72.,3.)]) for _ in range(5)]
            ref=np.full(5,0 if case_id.startswith('skillcorner') else 2,dtype=np.uint8)
            return dict(frames=frames,reference=lambda:ref,validate=lambda trace:None,
                        reference_loaded_by_adapter=case_id!='wcsf-used-match')
        stack.enter_context(patch.object(runner,'_sources',return_value=sources))
        stack.enter_context(patch.object(runner,'_bindings',return_value=bindings))
        stack.enter_context(patch.object(runner,'_git_commit',return_value='a'*40))
        stack.enter_context(patch.object(runner,'_load_case',side_effect=load))
        yield root,bindings,sources


class OwnershipProtocol(unittest.TestCase):
    def setUp(self):self.assertIsNotNone(runner,'Bounded diagnostic protocol is missing')

    def test_dependency_closure_and_protocol_inventory(self):
        sources=runner._sources(ROOT)
        required={'ownership_paths.py','ownership_diagnosis.py','ownership_run.py',
            'gap_solver/skillcorner.py','gap_solver/external.py','gap_solver/dfl_motion.py',
            'gap_solver/official_metrics.py','wcsf_geometry.py','wcsf_reference.py',
            'benchmark/ball-gap/selected.json','release/manifest.json',
            'docs/superpowers/specs/2026-11-09-all-state-path-diagnosis-addendum.md',
            'docs/superpowers/plans/2026-11-09-all-state-path-diagnosis.md'}
        self.assertTrue(required<=set(sources),required-set(sources))
        for name in runner.ENTRIES:ast.parse((ROOT/name).read_text(),feature_version=(3,9))

    def test_complete_synthetic_flow_and_read_only_verification(self):
        with fixture() as (root,_,__):
            session=runner.DiagnosisSession('synthetic-flow',root=root)
            session.freeze();session.run_cases();session.summarize()
            with patch.object(runner,'prepare_inference',side_effect=AssertionError('verification inferred')), \
                 patch.object(runner,'analyze_case',side_effect=AssertionError('verification evaluated')):
                result=session.verify()
            self.assertEqual(result['cases'],5)
            self.assertEqual(result['inference_entries'],5)
            self.assertEqual(result['evaluated_arrays'],15)

    def test_input_source_and_freeze_mutations_fail(self):
        for kind in ('input','source','freeze'):
            with fixture() as (root,bindings,sources),self.subTest(kind=kind):
                session=runner.DiagnosisSession('mutation',root=root);session.freeze()
                if kind=='input':next(iter(bindings.values()))['files'][next(iter(next(iter(bindings.values()))['files']))].write_bytes(b'changed')
                elif kind=='source':sources['ownership_paths.py'].write_bytes(b'changed')
                else:
                    path=session.public/'freeze.json';value=json.loads(path.read_text());value['model_sha256']='0'*64;path.write_text(json.dumps(value))
                with self.assertRaises(ValueError):session.run_cases()

    def test_exact_case_membership_and_missing_source_are_enforced(self):
        with fixture() as (root,bindings,sources):
            bad=dict(bindings);bad.pop(runner.CASE_IDS[0])
            with patch.object(runner,'_bindings',return_value=bad),self.assertRaises(ValueError):
                runner.DiagnosisSession('missing-case',root=root).freeze()
            bad_sources=dict(sources);bad_sources.pop('ownership_paths.py')
            with patch.object(runner,'_sources',return_value=bad_sources),self.assertRaises(ValueError):
                runner.DiagnosisSession('missing-source',root=root).freeze()

    def test_ids_and_existing_generations_are_protected(self):
        with fixture() as (root,_,__):
            for run_id in ('','../escape','bad/name','CON','space name'):
                with self.assertRaises(ValueError):runner.DiagnosisSession(run_id,root=root)
            session=runner.DiagnosisSession('preserve',root=root);session.freeze()
            before=(session.public/'freeze.json').read_bytes()
            with self.assertRaises(FileExistsError):session.freeze()
            self.assertEqual((session.public/'freeze.json').read_bytes(),before)

    def test_concurrent_freeze_has_one_winner(self):
        with fixture() as (root,_,__):
            def worker(_):
                try:runner.DiagnosisSession('race',root=root).freeze();return True
                except FileExistsError:return False
            with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(worker,range(2)))
            self.assertEqual(sum(results),1)

    def test_interrupted_case_and_corrupt_persistence_stay_incomplete(self):
        for kind in ('loader','receipt'):
            with fixture() as (root,_,__),self.subTest(kind=kind):
                session=runner.DiagnosisSession('interrupted',root=root);session.freeze()
                if kind=='loader':context=patch.object(runner,'_load_case',side_effect=OSError('synthetic failure'))
                else:
                    original=runner._write_new
                    def corrupt(path,value):
                        value=copy.deepcopy(value)
                        if path.parent==session.public and path.name==runner.CASE_IDS[0]+'.json':value['freeze_sha256']='0'*64
                        original(path,value)
                    context=patch.object(runner,'_write_new',side_effect=corrupt)
                with context,self.assertRaises((ValueError,OSError)):session.run_cases()
                self.assertTrue((session.private/'cases'/runner.CASE_IDS[0]/'.incomplete').exists())
                with self.assertRaises((ValueError,FileExistsError)):session.run_cases()
                with self.assertRaises(ValueError):session.verify()

    def test_egress_schema_rejects_extra_events_and_receipt_tampering(self):
        with fixture() as (root,_,__):
            session=runner.DiagnosisSession('egress',root=root);session.freeze();session.run_cases();session.summarize()
            path=session.public/(runner.CASE_IDS[0]+'.json');good=json.loads(path.read_text())
            for mutate in ('new_event_key','new_nested_array'):
                bad=copy.deepcopy(good)
                if mutate=='new_event_key':bad['diagnostic']['harmless_notes']=[{'start':3,'owner':'H'}]
                else:bad['diagnostic']['families']['false_D']['margins']['full']['total']=[1,2]
                with self.assertRaises(ValueError):runner.validate_case_report(bad,good['input_sha256'])
            extra=session.public/'extra.json';extra.write_text('{}')
            with self.assertRaises(ValueError):session.verify()
            extra.unlink();path.write_text(json.dumps(dict(good,freeze_sha256='0'*64)))
            with self.assertRaises(ValueError):session.verify()

    def test_summary_shadow_arrays_and_boolean_counts_are_rejected(self):
        for kind in ('shadow','boolean'):
            with fixture() as (root,_,__),self.subTest(kind=kind):
                session=runner.DiagnosisSession('summary-egress',root=root)
                session.freeze();session.run_cases();session.summarize()
                path=session.public/'summary.json';original=path.read_text()
                if kind=='shadow':path.write_text('{"schema_version":[{"start":1,"owner":"H"}],'+original[1:])
                else:
                    value=json.loads(original);value['schema_version']=True;path.write_text(json.dumps(value))
                with self.assertRaises(ValueError):session.verify()

    def test_case_hash_keys_and_prefreeze_release_runtime_drift(self):
        with fixture() as (root,_,__):
            session=runner.DiagnosisSession('hash-keys',root=root);session.freeze();session.run_cases();session.summarize()
            good=json.loads((session.public/(runner.CASE_IDS[0]+'.json')).read_text())
            runner.validate_case_report(good,good['input_sha256'])
            bad=copy.deepcopy(good);bad['input_sha256']['private/home-coordinate/12.1/44.3']='a'*64
            with self.assertRaises(ValueError):runner.validate_case_report(bad,good['input_sha256'])
            with patch.object(runner.platform,'python_version',return_value='different-runtime'),self.assertRaises(ValueError):session.verify()
        with fixture() as (root,_,__):
            (root/'gap_solver/tactical.py').write_text('# persistent pre-freeze edit\n')
            with self.assertRaises(ValueError):runner.DiagnosisSession('component-drift',root=root).freeze()

    def test_baseline_parity_precedes_path_queries_and_repairs(self):
        frames=[motion_frame(1,None,[(1.,1.)]*3,[(70.,1.)]*3) for _ in range(5)]
        trace=analysis.prepare_inference(frames);reference=np.full(5,2,dtype=np.uint8);entries=[]
        expected={'wcsf':dict(frames=5,known=5,n_gt=99,n_pred=0,n_matched=0,n_missed=0,n_spurious=0)}
        with self.assertRaises(ValueError):
            analysis.analyze_case(trace,reference,expected_parity=expected,on_evaluation=entries.append)
        self.assertEqual(entries,['baseline_metric'])


if __name__=='__main__':unittest.main()
