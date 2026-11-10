from pathlib import Path
import tempfile,unittest
from unittest.mock import patch
try:
    import gap_liveness_experiment as x
except ImportError:
    x=None

class GapProtocol(unittest.TestCase):
    def setUp(self):self.assertIsNotNone(x,'gap_liveness_experiment missing')
    def test_inclusive_harm_edges_and_mask_not_gating(self):
        baseline={r:{p:.55 for p in ('skillcorner','dfl','wcsf')} for r in x.REGIMES}
        candidate={r:dict(v) for r,v in baseline.items()}
        candidate['natural']={p:.545 for p in baseline['natural']}
        candidate['mask30-seed1729']={p:0. for p in baseline['natural']}
        self.assertTrue(x.harm_gate(baseline,candidate)['passed'])
        candidate['natural']['dfl']=.539999
        self.assertFalse(x.harm_gate(baseline,candidate)['passed'])
    def test_primary_loss_beyond_edge_rejects(self):
        a={r:{p:.5 for p in ('skillcorner','dfl','wcsf')} for r in x.REGIMES}
        b={r:{p:.494999 for p in a[r]} for r in x.REGIMES}
        result=x.harm_gate(a,b)
        self.assertFalse(result['primary_pass']);self.assertTrue(all(result['provider_pass'].values()))
    def test_exact_inventory_excludes_overlap(self):
        ids=[('skillcorner-a','skillcorner','fit-disjoint'),('dfl-a','dfl','fit-disjoint'),('wcsf-a','wcsf','fit-disjoint'),('dfl-overlap','dfl','fitting-overlap')]
        records=[dict(case_id=cid,regime=r,control=dict(metrics=dict(spell_f1_mean=.5 if role=='fit-disjoint' else 0.))) for cid,p,role in ids for r in x.REGIMES]
        self.assertEqual(x.provider_scores(records,'control',ids)['natural']['dfl'],.5)
        for bad in (records[:-1],records+[records[0]]):
            with self.assertRaises(ValueError):x.provider_scores(bad,'control',ids)
    def test_claims_and_phase_entry_are_exclusive(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()/'.tmp') as directory:
            x.claim(Path(directory),'control','dfl-x-natural')
            with self.assertRaises(FileExistsError):x.claim(Path(directory),'control','dfl-x-natural')
            with self.assertRaises(ValueError):x.claim(Path(directory),'control','../escape')
    def test_scoring_encodes_letters(self):
        import numpy as np
        from gap_solver.motion import motion_frame
        frames=[motion_frame(1,(0,0),((0,0),),((10,0),)) for _ in range(6)]
        result=x.score(np.array([0,0,1,1,2,2],dtype=np.uint8),list('HHAADD'),frames)
        self.assertEqual(result['metrics']['spell_f1_mean'],1.)
    def test_git_blob_hash_matches_known_content(self):
        import hashlib
        content=b'example\n'
        self.assertEqual(x.blob_hash(content),hashlib.sha1(b'blob 8\0example\n').hexdigest())
    def test_input_binding_detects_mutation(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()/'.tmp') as directory:
            p=Path(directory)/'input';p.write_bytes(b'original')
            binding=dict(files={'one':p});expected={'one':x.sha(p)}
            x.check_input(binding,expected)
            p.write_bytes(b'changed')
            with self.assertRaises(ValueError):x.check_input(binding,expected)
    def test_private_control_label_hash_required(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()/'.tmp') as directory:
            p=Path(directory)/'labels';p.write_bytes(b'HAD')
            self.assertEqual(x.load_control_labels(p,x.sha(p),3),('H','A','D'))
            with self.assertRaises(ValueError):x.load_control_labels(p,'0'*64,3)
            with self.assertRaises(ValueError):x.load_control_labels(p,x.sha(p),2)
    def test_phase_seal_tamper_fails(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()/'.tmp') as directory:
            root=Path(directory);public=root/'public';private=root/'private'
            x.write_new(public/'freeze.json',{'test':True})
            identity=dict(freeze_commit='a'*40,freeze_sha256=x.sha(public/'freeze.json'))
            x.write_new(public/'control/key.json',identity);x.write_new(public/'control-result.json',identity)
            x.claim(private,'control','key')
            x.seal_phase(public,private,'control','control-result.json',['key'],'a'*40,create=True)
            (public/'control/key.json').write_text('{}')
            with self.assertRaises(ValueError):x.seal_phase(public,private,'control','control-result.json',['key'],'a'*40)
    def test_budget_fixed_no_grid(self):self.assertEqual(x.LIMITS,dict(control=30,rule=30))

    def test_provider_only_limit_can_fail_while_primary_passes(self):
        a={r:{p:.55 for p in ('skillcorner','dfl','wcsf')} for r in x.REGIMES}
        b={r:dict(v) for r,v in a.items()};b['natural']['dfl']=.54
        self.assertTrue(x.harm_gate(a,b)['passed'])
        b['natural']['dfl']=.539999
        result=x.harm_gate(a,b)
        self.assertTrue(result['primary_pass']);self.assertFalse(result['provider_pass']['dfl'])
    def test_freeze_and_map_identity_cannot_be_rebound(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()/'.tmp') as directory:
            public=Path(directory)/'public';private=Path(directory)/'private'
            x.write_new(public/'freeze.json',dict(source_commit='a'*40))
            x.write_new(private/'input-map.json',dict(example='path'))
            x.bind_freeze_identity(public,private,'a'*40)
            x.verify_freeze_identity(public,private,x.read(public/'freeze.json'))
            (private/'input-map.json').write_text('{}')
            with self.assertRaises(ValueError):x.verify_freeze_identity(public,private,x.read(public/'freeze.json'))
            (public/'freeze.json').write_text('{"source_commit":"b"}')
            with self.assertRaises(ValueError):x.verify_freeze_identity(public,private,x.read(public/'freeze.json'))
    def test_cache_sidecars_must_share_actual_prefix(self):
        root=Path('C:/synthetic-cache')
        files={'features':root/'one.features.npz','metadata':root/'one.metadata.json','reference':root/'one.reference.npz'}
        x.check_binding_layout('dfl-synthetic',dict(files=files))
        files['features']=root/'other.features.npz'
        with self.assertRaises(ValueError):x.check_binding_layout('dfl-synthetic',dict(files=files))
    def test_committed_documents_are_bound(self):
        import hashlib
        with patch.object(x.subprocess,'check_output',return_value=b'original'):
            with self.assertRaises(ValueError):x.check_committed_documents('commit',{'doc.md':'0'*64})
            x.check_committed_documents('commit',{'doc.md':hashlib.sha256(b'original').hexdigest()})
    def test_completed_provisional_receipt_survives_following_error(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()/'.tmp') as directory:
            private=Path(directory)
            result=dict(completed_score=.5)
            x.store_provisional(private,'control','case-natural',result)
            try:raise ValueError('synthetic later failure')
            except ValueError:pass
            self.assertEqual(x.read(private/'provisional/control/case-natural.json'),result)
            with self.assertRaises(FileExistsError):x.store_provisional(private,'control','case-natural',result)
    def label_fixture(self,private,matches):
        rows=[]
        for cid,provider,role in matches:
            for regime in x.REGIMES:
                key=cid+'-'+regime;path=private/'control-labels'/(key+'.labels');path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b'HHHHHH')
                rows.append(dict(case_id=cid,provider=provider,role=role,regime=regime,labels_sha256=x.sha(path),control=dict(support=dict(frames=6))))
        return rows
    def test_missing_last_label_stops_rule_before_any_claim(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()/'.tmp') as directory:
            private=Path(directory)/'private';public=Path(directory)/'public';rows=self.label_fixture(private,x.MATCHES)
            last=rows[-1];(private/'control-labels'/(last['case_id']+'-'+last['regime']+'.labels')).unlink()
            frozen=dict(input_sha256={cid:{} for cid,_,_ in x.MATCHES});bindings={cid:dict(files={}) for cid,_,_ in x.MATCHES}
            with patch.object(x,'PRIVATE',private),patch.object(x,'PUBLIC',public),patch.object(x,'checked',return_value=(frozen,bindings,'a'*40)),patch.object(x,'verify_control',return_value=rows),patch('memory_ablation_run.load_evaluation',side_effect=AssertionError('data load must not happen')):
                with self.assertRaises(ValueError):x.rule()
            self.assertFalse((private/'rule-entry.json').exists());self.assertFalse((private/'claims/rule').exists())
    def test_synthetic_rule_stage_seals_exact_paired_cases(self):
        import numpy as np
        from gap_solver.motion import motion_frame
        matches=tuple((p+'-synthetic',p,'fit-disjoint') for p in ('skillcorner','dfl','wcsf'))
        frames=[motion_frame(1,(0,0),((0,0),),((10,0),)) for _ in range(6)]
        baseline=x.score(np.zeros(6,dtype=np.uint8),tuple('HHHHHH'),frames)
        with tempfile.TemporaryDirectory(dir=Path.cwd()/'.tmp') as directory:
            private=Path(directory)/'private';public=Path(directory)/'public';rows=self.label_fixture(private,matches)
            for row in rows:row['control']=baseline
            x.write_new(public/'freeze.json',{'synthetic':True})
            frozen=dict(input_sha256={cid:{} for cid,_,_ in matches});bindings={cid:dict(files={}) for cid,_,_ in matches}
            case=dict(frames=frames,reference=lambda:np.zeros(6,dtype=np.uint8))
            with patch.object(x,'MATCHES',matches),patch.object(x,'PRIVATE',private),patch.object(x,'PUBLIC',public),patch.object(x,'checked',return_value=(frozen,bindings,'a'*40)),patch.object(x,'verify_control',return_value=rows),patch('memory_ablation_run.load_evaluation',return_value=case):
                result=x.rule()
                self.assertTrue(result['gate']['passed']);self.assertEqual(result['scoring_calls'],6)
                self.assertEqual(len(list((private/'claims/rule').glob('*.json'))),6)
                self.assertTrue((private/'rule-seal.json').is_file())
