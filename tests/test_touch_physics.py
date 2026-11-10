from dataclasses import replace
import random
import unittest
from gap_solver.motion import motion_frame
try:
    import touch_physics as p
except ImportError:
    p=None


def track(n=80,kink=None,near=True,contest=False):
    points=[(i*.4,0) if kink is None or i<=kink else (kink*.4,(i-kink)*.4) for i in range(n)]
    return [motion_frame(1,b,((b[0]+(.6 if contest else .5),b[1]),) if near else ((1000,1000),),
        ((b[0]-.6,b[1]),) if contest else ((2000,2000),)) for b in points]

class TouchPhysics(unittest.TestCase):
    def setUp(self): self.assertIsNotNone(p,'touch_physics missing')
    def test_straight(self): self.assertEqual(p.detect_touches(track(),3),[])
    def test_deceleration(self):
        frames=[motion_frame(1,(i*.4-i*i*.0005,0),((0,0),),((100,100),)) for i in range(80)]
        self.assertEqual(p.detect_touches(frames,3),[])
    def test_home_kink(self):
        events=p.detect_touches(track(kink=40),3)
        self.assertEqual(len(events),1);self.assertEqual(events[0].team,'H')
        self.assertLessEqual(abs(events[0].frame_index-40),2)
        self.assertEqual(events[0].kind,'kink')
    def test_remote_kink_discarded(self): self.assertEqual(p.detect_touches(track(kink=40,near=False),3),[])
    def test_contested(self):
        events=p.detect_touches(track(kink=40,contest=True),3)
        self.assertEqual(len(events),1);self.assertEqual(events[0].team,'')
    def test_declared_jitter_gate(self):
        rng=random.Random(1729);frames=[]
        for i in range(500):
            b=(i*.4+rng.gauss(0,.05),rng.gauss(0,.05))
            frames.append(motion_frame(1,b,((b[0]+1,b[1]),),((1000,1000),)))
        for theta in (3,5): self.assertEqual(p.detect_touches(frames,theta),[])
    def test_reacquisition(self):
        frames=track()
        frames[20:30]=[motion_frame(1,None,((0,0),),((0,0),)) for _ in range(10)]
        self.assertEqual(p.detect_touches(frames,3),[])
        for i in range(30,80):
            b=(i*.4,10)
            frames[i]=motion_frame(1,b,((1000,1000),),((b[0]+.5,b[1]),))
        events=p.detect_touches(frames,3)
        self.assertEqual([(e.frame_index,e.team,e.kind) for e in events],[(30,'A','reacquire')])
    def test_period_reset_and_zero(self):
        frames=track(kink=40)
        self.assertEqual(p.detect_touches([replace(f,period=0) for f in frames],3),[])
        frames=[replace(f,period=1 if i<=40 else 2) for i,f in enumerate(frames)]
        self.assertEqual(p.detect_touches(frames,3),[])
    def test_mirror(self):
        frames=track(kink=40)
        mirror=[replace(f,home_xy=f.away_xy,away_xy=f.home_xy) for f in frames]
        a=p.detect_touches(frames,3);b=p.detect_touches(mirror,3)
        self.assertEqual([(e.frame_index,e.kind) for e in a],[(e.frame_index,e.kind) for e in b])
        self.assertEqual([e.team for e in b],['A'])
    def test_invalid_inputs(self):
        for f in (replace(track()[0],period=3),replace(track()[0],ball_x=float('nan')),
                  replace(track()[0],home_xy=((1,float('inf')),)),replace(track()[0],ball_y=None)):
            with self.assertRaises(ValueError):p.detect_touches([f],3)
        for theta in (-1,float('nan'),float('inf')):
            with self.assertRaises(ValueError):p.detect_touches(track(),theta)

    def test_provider_float32_coordinates(self):
        import numpy as np
        frames=[replace(f,ball_x=np.float32(f.ball_x),ball_y=np.float32(f.ball_y),
            home_xy=tuple(tuple(np.float32(v) for v in point) for point in f.home_xy),
            away_xy=tuple(tuple(np.float32(v) for v in point) for point in f.away_xy)) for f in track(kink=40)]
        events=p.detect_touches(frames,3)
        self.assertEqual(len(events),1);self.assertEqual(events[0].team,'H')
