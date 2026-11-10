from pathlib import Path
import tempfile,unittest,hashlib
try:
    import metrica_gap_check as m
except ImportError:m=None

class MetricaCheck(unittest.TestCase):
    def setUp(self):self.assertIsNotNone(m,'metrica_gap_check missing')
    def records(self):return [dict(game=g,control=dict(metrics=dict(spell_f1_mean=.5)),candidate=dict(metrics=dict(spell_f1_mean=.5)),gap={}) for g in m.GAMES]
    def test_mean_gate_and_exact_inventory(self):
        rows=self.records();self.assertTrue(m.decide(rows)['passed'])
        rows[0]['candidate']['metrics']['spell_f1_mean']=.49
        self.assertFalse(m.decide(rows)['passed'])
        for bad in (rows[:-1],rows+[rows[0]]):
            with self.assertRaises(ValueError):m.decide(bad)
    def test_source_blob_identity_and_missing_file(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()/'.tmp') as d:
            root=Path(d);data=b'public sample';(root/'source').write_bytes(data)
            asset=dict(path='source',bytes=len(data),git_blob_sha1=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest())
            m.verify_asset(root,asset)
            (root/'source').write_bytes(b'changed')
            with self.assertRaises(ValueError):m.verify_asset(root,asset)
    def test_claim_budget_is_per_variant_and_exclusive(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()/'.tmp') as d:
            root=Path(d);m.claim(root,'control',m.GAMES[0]);m.claim(root,'rule',m.GAMES[0])
            with self.assertRaises(FileExistsError):m.claim(root,'control',m.GAMES[0])
            with self.assertRaises(ValueError):m.claim(root,'control','unknown-game')
    def test_provisional_receipt_cannot_be_overwritten(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()/'.tmp') as d:
            root=Path(d);m.provisional(root,'control',m.GAMES[0],{'score':.5})
            with self.assertRaises(FileExistsError):m.provisional(root,'control',m.GAMES[0],{'score':.6})

    def test_negative_one_ulp_mean_is_rejected(self):
        import math
        rows=self.records()
        for row in rows:row['candidate']['metrics']['spell_f1_mean']=math.nextafter(.5,0.)
        self.assertFalse(m.decide(rows)['passed'])
    def test_invalid_returned_aggregate_retained_before_validation(self):
        import math
        with tempfile.TemporaryDirectory(dir=Path.cwd()/'.tmp') as d:
            private=Path(d)
            def invalid(*args):return {'metrics':{'spell_f1_mean':float('nan')}}
            def validate(value):raise ValueError('synthetic validation failure')
            with self.assertRaises(ValueError):m.score_retained(private,'control',m.GAMES[0],[],[],[],{},compute=invalid,validate=validate)
            value=m.read(private/'provisional/control'/(m.GAMES[0]+'.json'))
            self.assertTrue(math.isnan(value['score']['metrics']['spell_f1_mean']))
    def test_qualification_binding_requires_exact_source_and_records(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory(dir=Path.cwd()/'.tmp') as d:
            root=Path(d);qualification=root/'q.json';binding=root/'b.json';source=root/'metrica_event_reference.py';source.write_text('old');(root/'metrica_sample_adapter.py').write_text('adapter')
            m.write_new(qualification,dict(no_predictions_or_scores=True,records=[dict(game=g,model_inference_calls=0,scoring_calls=0,reference_sha256='a'*64) for g in m.GAMES]))
            m.write_new(binding,dict(qualification_sha256=m.gap.sha(qualification),source_sha256={'metrica_event_reference.py':m.gap.sha(source),'metrica_sample_adapter.py':m.gap.sha(root/'metrica_sample_adapter.py')},model_inference_calls=0,scoring_calls=0))
            with patch.object(m,'ROOT',root),patch.object(m,'QUALIFICATION',qualification),patch.object(m,'BINDING',binding,create=True):
                m.verify_qualification()
                source.write_text('new')
                with self.assertRaises(ValueError):m.verify_qualification()
    def test_public_case_contains_counts_and_hashes_not_metrics(self):
        import numpy as np
        from gap_solver.motion import motion_frame
        frames=[motion_frame(1,(0,0),((0,0),),((10,0),)) for _ in range(6)]
        score=m.gap.score(np.array([0,0,1,1,2,2],dtype=np.uint8),tuple('HHAADD'),frames)
        row=dict(freeze_commit='a'*40,freeze_sha256='b'*64,game=m.GAMES[0],control=score,candidate=score,
            gap=dict(long_gaps=0,stoppage_gaps=0,reference_speed_mps=1.2),reference=dict(known_frames=6,label_counts=dict(H=2,A=2,D=2,X=0)),labels_sha256=dict(control='c'*64,rule='c'*64),reference_sha256='d'*64)
        public=m.public_case(row,'e'*64)
        def check(value):
            if isinstance(value,dict):
                self.assertFalse(set(value)&{'metrics','accuracy','precision','recall','mean_f1','f1'})
                for v in value.values():check(v)
            elif isinstance(value,list):
                for v in value:check(v)
            else:self.assertNotIsInstance(value,float)
        check(public)
    def test_full_summary_reconstruction_checks_metadata(self):
        rows=self.records();commit='a'*40
        from unittest.mock import patch
        with patch.object(m.gap,'sha',return_value='b'*64):
            value=m.make_summary(rows,commit)
            m.verify_summary(value,rows,commit)
            value['scoring_calls']=5
            with self.assertRaises(ValueError):m.verify_summary(value,rows,commit)
    def test_observation_period_counts_checked_before_prediction(self):
        from gap_solver.motion import motion_frame
        frames=[motion_frame(1,(0,0),(),()),motion_frame(2,None,(),())]
        expected=dict(frames=2,period_counts={'0':0,'1':1,'2':1},ball_observed=1)
        m.check_qualified_grid(frames,expected)
        expected['ball_observed']=2
        with self.assertRaises(ValueError):m.check_qualified_grid(frames,expected)

    def test_new_scientific_python_inventory_is_rejected(self):
        from unittest.mock import patch
        frozen=dict(source_sha256={'one.py':'a'*64})
        with patch.object(m.subprocess,'check_output',side_effect=['one.py\nshadow.py\n','']):
            with self.assertRaises(ValueError):m.verify_source_inventory(frozen)
        with patch.object(m.subprocess,'check_output',side_effect=['one.py\n','untracked.py\n']):
            with self.assertRaises(ValueError):m.verify_source_inventory(frozen)

    def test_retained_scorer_encodes_predictor_letters(self):
        import numpy as np
        from gap_solver.motion import motion_frame
        frames=[motion_frame(1,(0,0),((0,0),),((10,0),)) for _ in range(6)]
        with tempfile.TemporaryDirectory(dir=Path.cwd()/'.tmp') as d:
            value=m.score_retained(Path(d),'control',m.GAMES[0],np.array([0,0,1,1,2,2],dtype=np.uint8),tuple('HHAADD'),frames,{})
            self.assertEqual(value['metrics']['spell_f1_mean'],1.)
