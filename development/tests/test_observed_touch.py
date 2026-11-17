from pathlib import Path
from dataclasses import replace
import struct,tempfile,unittest
from gap_solver.motion import motion_frame
from release_runtime import load_source,predict_selected
from release_fixtures import release_fixture
from touch_physics import TouchEvent
from test_touch_physics import track
try:
    import observed_touch as o
except ImportError:
    o=None

class ObservedTouch(unittest.TestCase):
    def setUp(self):self.assertIsNotNone(o,'observed_touch missing')
    def test_reappearance_does_not_emit_and_later_kink_does(self):
        frames=track(n=100,kink=60)
        for i in range(30,40):frames[i]=motion_frame(1,None,(),())
        for i in range(40,100):
            f=frames[i];frames[i]=replace(f,ball_y=f.ball_y+10,home_xy=tuple((x,y+10) for x,y in f.home_xy))
        events=o.detect_observed_touches(frames,3)
        self.assertTrue(all(e.kind=='kink' and e.frame_index!=40 for e in events))
        self.assertEqual([(e.frame_index,e.team) for e in events],[(60,'H')])
    def test_missing_bonus_is_neutral_and_does_not_resume(self):
        periods=[1]*30;seen=[True]*30;seen[12:16]=[False]*4
        rows,costs=o.observed_evidence_rows([(0.,)*3]*30,periods,[True]*30,seen,[TouchEvent(5,'H','kink'),TouchEvent(23,'A','kink')],2,8)
        self.assertEqual(rows[11],(2.,0.,0.))
        self.assertEqual(rows[12:23],[(0.,)*3]*11)
        self.assertEqual(rows[23],(0.,2.,0.));self.assertEqual(costs[5],(8.,32.,32.))
    def test_every_touch_followed_by_gap_missing_bytes_match_control(self):
        n=80;seen=[True]*n
        for i in (12,35,60):seen[i:i+5]=[False]*5
        events=[TouchEvent(i,'H' if j%2==0 else 'A','kink') for j,i in enumerate((5,28,53))]
        base=[(-1.,-2.,-3.) if seen[i] else (0.,)*3 for i in range(n)]
        rows,_=o.observed_evidence_rows(base,[1]*n,[True]*n,seen,events,4,8)
        for i in range(n):
            if not seen[i]:self.assertEqual(struct.pack('<ddd',*rows[i]),struct.pack('<ddd',*base[i]))
    def test_contested_and_period_reset_and_expiry(self):
        rows,_=o.observed_evidence_rows([(0.,)*3]*300,[1]*290+[2]*10,[True]*300,[True]*300,
            [TouchEvent(1,'H','kink'),TouchEvent(5,'','kink'),TouchEvent(7,'A','kink')],2,32)
        self.assertEqual(rows[5],(0.,)*3);self.assertEqual(rows[256],(0.,2.,0.));self.assertEqual(rows[257],(0.,)*3)
        self.assertEqual(rows[290],(0.,)*3)
    def test_fixture_parity_no_events_or_disabled(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()/'.tmp') as directory:
            for case in ('positive','invalid','unsupported'):
                frames,_=load_source(*release_fixture(Path(directory)/case,case),scope='synthetic')
                expected=predict_selected(frames)
                self.assertEqual(o.predict_observed_touch(frames,3,4,8,events=[]),expected)
                self.assertEqual(o.predict_observed_touch(frames,3,0,32),expected)
    def test_invalid_events_flags_or_parameters(self):
        for events in ([TouchEvent(5,'A','reacquire')],[TouchEvent(5,'H','kink')]*2):
            with self.assertRaises(ValueError):o.observed_evidence_rows([(0.,)*3]*20,[1]*20,[True]*20,[True]*20,events,2,8)
        seen=[True]*20;seen[5]=False
        with self.assertRaises(ValueError):o.observed_evidence_rows([(0.,)*3]*20,[1]*20,[True]*20,seen,[TouchEvent(5,'H','kink')],2,8)
        with self.assertRaises(ValueError):o.observed_evidence_rows([(0.,)*3],[1],[True],[True],[],-1,8)
