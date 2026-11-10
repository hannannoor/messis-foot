import ast
from dataclasses import replace
import hashlib
from pathlib import Path
import random
import tempfile
import unittest
from gap_solver.motion import motion_frame
from gap_solver.soft_sequence import decode_soft
from release_runtime import predict_selected,load_source
from release_fixtures import release_fixture
from touch_physics import TouchEvent
try:
    from touch_decoder import decode_variable
    from touch_evidence import evidence_rows,predict_touch
except ImportError:
    decode_variable=evidence_rows=predict_touch=None

class TouchEvidence(unittest.TestCase):
    def setUp(self):self.assertIsNotNone(decode_variable,'touch decoder missing')
    def test_random_decoder_parity(self):
        rng=random.Random(1729)
        for _ in range(250):
            n=rng.randrange(0,101);rows=[tuple(rng.choice((0.,-1.,-2.,-13.8)) for _ in range(3)) for _ in range(n)]
            periods=[rng.choice((0,1,1,1,2,2)) for _ in range(n)];usable=[rng.random()<.8 for _ in range(n)]
            self.assertEqual(decode_variable(rows,periods,usable,[(32.,)*3]*n),decode_soft(rows,periods,usable,32))
    def test_release_fixture_full_parity(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()/'.tmp') as directory:
            for case in ('positive','invalid','unsupported'):
                paths=release_fixture(Path(directory)/case,case)
                frames,_=load_source(*paths,scope='synthetic');control=predict_selected(frames)
                self.assertEqual(predict_touch(frames,3,4,8,events=[]),control)
                self.assertEqual(predict_touch(frames,3,0,32),control)
    def test_bonus_placement(self):
        n=300;events=[TouchEvent(1,'H','kink'),TouchEvent(5,'','kink'),TouchEvent(7,'A','reacquire')]
        rows,costs=evidence_rows([(0.,)*3]*n,[1]*n,[True]*n,events,2,8)
        self.assertEqual(rows[0],(0.,)*3);self.assertEqual(rows[1],(2.,0.,0.))
        self.assertEqual(rows[4],(2.,0.,0.));self.assertEqual(rows[5],(0.,)*3)
        self.assertEqual(rows[7],(0.,2.,0.));self.assertEqual(rows[256],(0.,2.,0.))
        self.assertEqual(rows[257],(0.,)*3)
        self.assertEqual(costs[1],(8.,32.,32.));self.assertEqual(costs[2],(32.,)*3)
    def test_bonus_period_and_unusable(self):
        rows,_=evidence_rows([(0.,)*3]*8,[1]*4+[2]*4,[True,True,False,True]+[True]*4,[TouchEvent(1,'H','kink')],2,8)
        self.assertEqual(rows[2],(0.,)*3);self.assertEqual(rows[3],(2.,0.,0.));self.assertEqual(rows[4],(0.,)*3)
    def test_mechanism(self):
        rows=[(0.,-.5,-10.)]*20+[(-.2,0.,-10.)]*20+[(0.,-.5,-10.)]*20
        periods=[1]*60;usable=[True]*60;events=[TouchEvent(20,'A','kink'),TouchEvent(40,'H','kink')]
        candidate,costs=evidence_rows(rows,periods,usable,events,2,8)
        self.assertEqual(decode_soft(rows,periods,usable,32),['H']*60)
        self.assertEqual(decode_variable(candidate,periods,usable,costs),['H']*20+['A']*20+['H']*20)
    def test_missing_frames_keep_bonus(self):
        frames=[motion_frame(1,(i*.01,0),((0,0),(0,1),(0,2)),((20,0),(20,1),(20,2))) for i in range(20)]
        frames[7]=motion_frame(1,None,((0,0),(0,1),(0,2)),((20,0),(20,1),(20,2)))
        from touch_evidence import prepare_evidence
        rows,costs,periods,usable,counts=prepare_evidence(frames,[TouchEvent(5,'A','kink')],2,8)
        self.assertEqual(rows[7],(0.,2.,0.));self.assertTrue(usable[7])
    def test_all_missing_segment_excluded(self):
        frames=[motion_frame(1,None,((0,0),(0,1),(0,2)),((20,0),(20,1),(20,2))) for _ in range(20)]
        self.assertEqual(predict_touch(frames,3,4,8,events=[]),predict_selected(frames))
    def test_invalid_parameters_and_rows(self):
        for value in (-1,float('nan'),float('inf')):
            for beta,cost in ((value,8),(2,value)):
                with self.assertRaises(ValueError):evidence_rows([(0.,)*3],[1],[True],[],beta,cost)
            with self.assertRaises(ValueError):decode_variable([(0.,)*3],[1],[True],[(value,32.,32.)])
        with self.assertRaises(ValueError):decode_variable([(float('inf'),0.,0.)],[1],[True],[(32.,)*3])
    def test_invalid_events(self):
        for event in (TouchEvent(1,'Z','kink'),TouchEvent(1,'H','bad'),TouchEvent(-1,'H','kink')):
            with self.assertRaises(ValueError):evidence_rows([(0.,)*3]*3,[1]*3,[True]*3,[event],2,8)
        with self.assertRaises(ValueError):evidence_rows([(0.,)*3]*3,[1]*3,[True]*3,[TouchEvent(1,'H','kink')]*2,2,8)
    def test_determinism(self):
        frames=[motion_frame(1,(i*.4,0),((i*.4+.5,0),),((1000,1000),)) for i in range(60)]
        digest=lambda:hashlib.sha256(''.join(predict_touch(frames,3,2,8).labels).encode()).hexdigest()
        self.assertEqual(digest(),digest())
    def test_inference_import_isolation(self):
        for name in ('touch_physics.py','touch_evidence.py','touch_decoder.py'):
            tree=ast.parse(Path(name).read_text(encoding='utf-8-sig'))
            names=[node.module or '' for node in ast.walk(tree) if isinstance(node,ast.ImportFrom)]
            names += [a.name for node in ast.walk(tree) if isinstance(node,ast.Import) for a in node.names]
            self.assertFalse(any(any(x in name for x in ('numpy','pandas','reference','metrics','ownership','memory_ablation')) for name in names))
    def test_release_preserved(self):
        self.assertEqual(hashlib.sha256(Path('competition_release.py').read_bytes()).hexdigest(),
            'e8d35e15be9524270bed82352791dc2849087b49b4c2b59c191023954b19eddb')
