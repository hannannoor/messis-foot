import base64
import copy
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from contextlib import redirect_stderr,redirect_stdout
from unittest.mock import patch

import memory_ablation_protocol as p
import memory_ablation_run as runner
import memory_ablation_metrics as metrics
from test_memory_ablation_protocol import fixture
import test_memory_ablation_metrics as metric_fixture
from test_memory_ablation_metrics import codes


def replace(path,value):path.write_bytes(p.canonical(value))


class ReviewRegressions(unittest.TestCase):
    def test_production_registry_is_shared_across_distinct_workspace_parents(self):
        with tempfile.TemporaryDirectory() as tmp:
            a=runner.AblationSession('a',root=Path(tmp)/'first/code')
            b=runner.AblationSession('b',root=Path(tmp)/'second/code')
            self.assertEqual(a.budget,b.budget)

    def test_nonzero_strict_gain_edge_and_missing_support_overall_precedence(self):
        rows=metric_fixture.MemoryMetrics().receipts()
        for row in rows:
            row['variants']['control']['metrics']['spell_f1_mean']=.5
            row['variants']['memory-ablated']['metrics']['spell_f1_mean']=.500001
        self.assertEqual(metrics.summarize_cases(rows)['checks']['natural_primary_gain']['status'],'fail')

    def test_missing_required_support_dominates_other_gate_failures(self):
        rows=metric_fixture.MemoryMetrics().receipts()
        next(r for r in rows if r['cohort']=='dfl')['variants']['memory-ablated']['dead']['precision']=None
        rows[0]['variants']['memory-ablated']['metrics']['spell_f1_mean']=.1
        result=metrics.summarize_cases(rows)
        self.assertEqual(result['decision'],'unresolved')
        self.assertEqual(result['checks']['fit_disjoint_case_spell_loss']['status'],'fail')

    def test_supplied_rates_and_strata_must_reconcile_to_confusion(self):
        valid=metrics.score_variant(codes('HHDDAA'),codes('HHHHAA'),[1]*6,[True,False]*3)
        changes=[('rate',lambda x:x.update(known_live_false_D_rate=.1)),
            ('accuracy',lambda x:x['metrics'].update(accuracy=.1)),
            ('macro',lambda x:x['metrics'].update(official_macro_f1=.1))]
        changes += [(key,lambda x,k=key:x['strata']['ball_observed'].__setitem__(k,x['strata']['ball_observed'][k]+1))
            for key in ('correct','ownership_swaps','false_D','missed_D')]
        p.validate_score(valid)
        for name,change in changes:
            with self.subTest(name=name):
                bad=copy.deepcopy(valid);change(bad)
                with self.assertRaises(ValueError):p.validate_score(bad)

    def test_lifecycle_artifacts_reject_anchored_extra_fields_and_wrong_seal_digest(self):
        with fixture() as (root,_,__,___):
            s=runner.AblationSession('review',root=root);s.freeze();s.fit();s.seal()
            for name,anchor_name,field,check in (
                ('freeze.json','freeze-anchor.json','freeze_sha256',s._frozen),
                ('fit.json','fit-anchor.json','fit_sha256',s._fit_status),
                ('seal.json','seal-anchor.json','seal_sha256',s._sealed)):
                path=s.public/name;anchor=s.private/anchor_name
                saved=path.read_bytes();saved_anchor=anchor.read_bytes()
                with self.subTest(name=name):
                    value=p.read(path);value['additional_sha256']={'x=4.2,y=1.0':'a'*64}
                    value['limitations']=['arbitrary per-frame content'];replace(path,value)
                    a=p.read(anchor);a[field]=p.sha(path);replace(anchor,a)
                    with self.assertRaises(ValueError):check()
                path.write_bytes(saved);anchor.write_bytes(saved_anchor)
            path=s.public/'freeze.json';anchor_path=s.private/'freeze-anchor.json';saved=path.read_bytes();saved_anchor=anchor_path.read_bytes()
            value=p.read(path);value['protocol']['automatic_promotion']=0;replace(path,value)
            a=p.read(anchor_path);a['freeze_sha256']=p.sha(path);replace(anchor_path,a)
            with self.assertRaises(ValueError):s._frozen()
            path.write_bytes(saved);anchor_path.write_bytes(saved_anchor)
            seal=p.read(s.public/'seal.json');seal['model_sha256']['memory-ablated']='a'*64
            replace(s.public/'seal.json',seal);replace(s.private/'seal-anchor.json',dict(seal_sha256=p.sha(s.public/'seal.json')))
            with self.assertRaises(ValueError):s._sealed()

    def test_failed_cli_verify_does_not_write_to_its_subject(self):
        with fixture() as (root,_,__,___):
            s=runner.AblationSession('readonly',root=root);s.freeze()
            before={str(f.relative_to(s.private)):f.read_bytes() for f in s.private.rglob('*') if f.is_file()}
            with patch.object(runner,'AblationSession',return_value=s),patch.object(s,'verify',side_effect=ValueError('synthetic failure')), \
                patch('sys.argv',['run','verify','--run-id','readonly']),redirect_stderr(io.StringIO()),redirect_stdout(io.StringIO()):
                self.assertEqual(runner.main(),1)
            after={str(f.relative_to(s.private)):f.read_bytes() for f in s.private.rglob('*') if f.is_file()}
            self.assertEqual(after,before)

    def test_record_integrity_detects_binary_change_with_unchanged_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);dist=root/'fake.dist-info';dist.mkdir();binary=root/'fake.pyd';binary.write_bytes(b'original')
            digest=base64.urlsafe_b64encode(hashlib.sha256(binary.read_bytes()).digest()).decode().rstrip('=')
            record=dist/'RECORD';record.write_text('fake.pyd,sha256='+digest+',8\nfake.dist-info/RECORD,,\n')
            identity=p.record_identity(record,root);self.assertEqual(identity['hashed_files'],1)
            binary.write_bytes(b'modified')
            with self.assertRaises(ValueError):p.record_identity(record,root)

    def test_historical_audit_binds_git_sources_without_scientific_entries(self):
        with fixture() as (root,_,sources,___):
            s=runner.AblationSession('historic',root=root);s.freeze();s.fit();s.seal();s.evaluate();s.summarize()
            expected=p.read(s.public/'freeze.json')['source_sha256'];next(iter(sources.values())).write_bytes(b'# retrospective correction\n')
            with self.assertRaises(ValueError):s.verify()
            with patch.object(p,'historical_sources',return_value=expected,create=True), \
                 patch.object(runner,'prepare_inputs',side_effect=AssertionError('audit prepared')), \
                 patch.object(runner,'infer_prepared',side_effect=AssertionError('audit inferred')), \
                 patch.object(runner,'score_variant',side_effect=AssertionError('audit scored')):
                self.assertEqual(s.verify(source_commit='a'*40)['scorings'],60)


    def test_retirement_certificate_rejects_extra_public_fields(self):
        with fixture() as (root,_,__,___):
            s=runner.AblationSession('old',root=root);s.freeze()
            p.store_exact(s.private/'fit-request.incomplete',dict(utc=p.utc()))
            for name in ('execution-error-fit-worker.log','execution-error-fit.log'):(s.private/name).write_text('synthetic failure')
            s.retire_preflight('successor')
            path=s.public/'preflight-status.json';value=p.read(path);value['limitations']=['unowned content'];replace(path,value)
            replace(s.private/'retired-preflight.json',dict(status_sha256=p.sha(path)))
            link=p.read(s.budget/'preflight-successor.json');link['status_sha256']=p.sha(path);replace(s.budget/'preflight-successor.json',link)
            with self.assertRaises(ValueError):runner.AblationSession('successor',root=root).freeze()

    def test_base_interpreter_library_must_match_recorded_provenance(self):
        provenance=dict(interpreter_sha256='a'*64,dll_sha256='b'*64)
        runtime=dict(binary_identity=dict(base_executable_sha256='a'*64,interpreter_library_sha256='c'*64))
        with self.assertRaises(ValueError):p.validate_training_binaries(runtime,provenance)

    def test_historical_source_hashes_are_checked_against_git_objects(self):
        import subprocess
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);path=root/'source.py';path.write_bytes(b'# original\n')
            def git(*args):return subprocess.check_output(['git',*args],cwd=root,stderr=subprocess.DEVNULL,text=True).strip()
            git('init');git('add','source.py');git('-c','user.name=Synthetic','-c','user.email=synthetic@example.invalid','commit','-m','synthetic')
            commit=git('rev-parse','HEAD');expected={'source.py':hashlib.sha256(path.read_bytes()).hexdigest()};path.write_bytes(b'# current correction\n')
            self.assertEqual(p.historical_sources(root,commit,expected),expected)
            with self.assertRaises(ValueError):p.historical_sources(root,commit,{'source.py':'0'*64})


if __name__=='__main__':unittest.main()
