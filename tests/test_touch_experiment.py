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
            return dict(dead=dict(recall=recall),predicted_on_known=dict(H=5,A=5 if owners else 0),spells=dict(n_gt=10,n_pred=n_pred))
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
