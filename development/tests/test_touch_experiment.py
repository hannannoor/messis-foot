from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from gap_solver.motion import motion_frame
try:
    import touch_experiment as e
except ImportError:
    e=None

class TouchExperiment(unittest.TestCase):
    def setUp(self):self.assertIsNotNone(e,'touch_experiment missing')
    def test_fixed_split_and_grid(self):
        dev,confirm=e.split_matches()
        self.assertEqual(len(dev),6);self.assertEqual(len(confirm),7)
        self.assertIn('dfl-J03WN1',dev);self.assertIn('wcsf-used-match',confirm)
        self.assertEqual([x.split('-')[1] for x in dev if x.startswith('skillcorner')],['1874553','2007448','2010085','2013725','2016236'])
        self.assertEqual(len(e.GRID),12)
    def test_selection_eligibility_and_ties(self):
        controls={r:.4 for r in e.REGIMES}
        scores=[dict(config=c,means={r:.5 for r in e.REGIMES}) for c in e.GRID]
        self.assertEqual(e.select_config(scores,controls),dict(theta=5,beta=1,c_touch=32))
        for s in scores:s['means']['jitter']=.39
        self.assertIsNone(e.select_config(scores,controls))
    def test_jitter_is_deterministic_and_updates_distances(self):
        frames=[motion_frame(1,(1.,0.),((0.,0.),),((10.,0.),)),motion_frame(1,None,(),())]
        a=e.add_jitter(frames);b=e.add_jitter(frames)
        self.assertEqual(a,b);self.assertEqual(frames[0].ball_x,1.)
        self.assertNotEqual(a[0].home_distance,frames[0].home_distance)
        self.assertIsNone(a[1].ball_x)
    def test_equal_provider_weight(self):
        scores={'skillcorner-1':.8,'skillcorner-2':.6,'dfl-1':.3}
        self.assertAlmostEqual(e.provider_mean(scores),.5)
    def test_claims_are_exclusive(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()/'.tmp') as d:
            e.claim(Path(d),'development','x')
            with self.assertRaises(FileExistsError):e.claim(Path(d),'development','x')
            with self.assertRaises(ValueError):e.claim(Path(d),'development','../x')
    def test_decision_edges(self):
        means={r:dict(control=.4,candidate=.45) for r in e.REGIMES}
        self.assertEqual(e.classify(means,True,True),'Accept')
        means['natural']['candidate']=.42
        self.assertEqual(e.classify(means,True,True),'Inconclusive')
        self.assertEqual(e.classify(means,False,True),'Reject')
        means['natural']['candidate']=.4
        self.assertEqual(e.classify(means,True,True),'Reject')
    def test_safeguards(self):
        def score(recall=.5,n_pred=10,owners=True):
            return dict(dead=dict(recall=recall,n_gt=100,n_matched=round(recall*100)),predicted_on_known=dict(H=5,A=5 if owners else 0),spells=dict(n_gt=10,n_pred=n_pred))
        rows=[dict(case_id='dfl-x',regime=r,control=score(),candidate=score()) for r in e.REGIMES]
        self.assertTrue(e.safeguards(rows)['passed'])
        rows[0]['candidate']=score(recall=.47)
        self.assertFalse(e.safeguards(rows)['passed'])
        rows[0]['candidate']=score(n_pred=12)
        self.assertFalse(e.safeguards(rows)['passed'])
        rows[0]['candidate']=score(owners=False)
        self.assertFalse(e.safeguards(rows)['passed'])
    def test_budget_formula(self):
        self.assertEqual(e.LIMITS,dict(control=45,development=216,confirmation=21))

    def test_scoring_boundary_encodes_letters(self):
        import numpy as np
        frames=[motion_frame(1,(0.,0.),((0.,0.),),((10.,0.),)) for _ in range(12)]
        score=e.score(np.array([0]*4+[1]*4+[2]*4,dtype=np.uint8),list('HHHHAAAADDDD'),frames)
        self.assertEqual(score['metrics']['spell_f1_mean'],1.)
    def test_exact_inclusive_boundaries(self):
        means={r:dict(control=.46,candidate=.50) for r in e.REGIMES}
        self.assertEqual(e.classify(means,True,True),'Accept')
        def score(n):return dict(dead=dict(recall=.5,n_gt=100,n_matched=50),predicted_on_known=dict(H=5,A=5),spells=dict(n_gt=10,n_pred=n))
        rows=[dict(case_id='dfl-x',regime=r,control=score(9),candidate=score(11)) for r in e.REGIMES]
        self.assertTrue(e.safeguards(rows)['passed'])
    def test_means_reject_missing_duplicate_or_extra(self):
        rows=[dict(case_id='dfl-x',regime=r,control=dict(metrics=dict(spell_f1_mean=.5))) for r in e.REGIMES]
        self.assertEqual(e.means_for(rows,['dfl-x'],'control')['natural'],.5)
        for bad in (rows[:-1],rows+[rows[0]],rows+[dict(rows[0],case_id='dfl-y')]):
            with self.assertRaises(ValueError):e.means_for(bad,['dfl-x'],'control')
    def test_phase_seal_binds_receipts_summary_and_claims(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()/'.tmp') as directory:
            public=Path(directory)/'public';private=Path(directory)/'private'
            e.write_new(public/'freeze.json',dict(test=True))
            identity=dict(freeze_commit='a'*40,freeze_sha256=e.sha(public/'freeze.json'))
            e.write_new(public/'control/x.json',dict(identity,case_id='dfl-x'))
            e.write_new(public/'control-reproduction.json',dict(identity,passed=True))
            e.claim(private,'control','x')
            e.seal_phase(public,private,'control','control-reproduction.json',['x'],'a'*40,create=True)
            e.seal_phase(public,private,'control','control-reproduction.json',['x'],'a'*40)
            (public/'control-reproduction.json').write_text('{}')
            with self.assertRaises(ValueError):e.seal_phase(public,private,'control','control-reproduction.json',['x'],'a'*40)
    def test_mask_precedes_jitter(self):
        from unittest.mock import patch
        frames=[motion_frame(1,(float(i),0.),((0.,0.),),((10.,0.),)) for i in range(200)]
        seen=[]
        real=e.add_jitter
        def capture(source):seen.extend(source);return real(source)
        with patch.object(e,'add_jitter',side_effect=capture):outputs=list(e.regimes(frames))
        self.assertEqual(seen,outputs[1][1])
        self.assertTrue(any(not f.ball_observed for f in seen))
        self.assertEqual([f.ball_observed for f in outputs[2][1]],[f.ball_observed for f in seen])
    def test_terminal_development_reject_has_zero_confirmation(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()/'.tmp') as directory:
            e.development_reject(Path(directory),dict(selected=None,freeze_commit='a'*40,freeze_sha256='b'*64))
            decision=e.read(Path(directory)/'decision.json')
            self.assertEqual(decision['decision'],'Reject')
            self.assertEqual(decision['confirmation_scoring_calls'],0)

    def test_source_commit_must_contain_frozen_bytes(self):
        from unittest.mock import patch
        with patch.object(e,'source_hashes',return_value={'a.py':'a'*64}), patch.object(e,'committed_sources',return_value={'a.py':'b'*64}):
            with self.assertRaises(ValueError):e.source_identity('commit')
        with patch.object(e,'source_hashes',return_value={'a.py':'a'*64}), patch.object(e,'committed_sources',return_value={'a.py':'a'*64}):
            self.assertEqual(e.source_identity('commit'),{'a.py':'a'*64})
    def test_case_input_inventory_and_mutation(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()/'.tmp') as directory:
            path=Path(directory)/'source';path.write_bytes(b'original')
            frozen=dict(input_sha256={'case':{'source':e.sha(path)}})
            e.check_case_input('case',dict(files={'source':path}),frozen)
            path.write_bytes(b'changed')
            with self.assertRaises(ValueError):e.check_case_input('case',dict(files={'source':path}),frozen)
            with self.assertRaises(ValueError):e.check_case_input('case',dict(files={}),frozen)
