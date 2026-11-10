import ast
from dataclasses import replace
import hashlib
from pathlib import Path
import unittest
from gap_solver.motion import motion_frame
try:
    import gap_liveness as g
except ImportError:
    g=None


def fixture(n=900,gaps=((300,500),),gap_speed=0.,periods=None,players=12):
    points=0.;frames=[]
    for i in range(n):
        inside=any(a<=i<b for a,b in gaps)
        speed=(gap_speed(i) if callable(gap_speed) else gap_speed) if inside else 2.
        points+=speed/25
        xy=tuple((points+j*.2,float(j)) for j in range(players))
        half=players//2
        frames.append(motion_frame(periods[i] if periods else 1,None if inside else (i*.12,0.),xy[:half],xy[half:],tuple(range(half)),tuple(range(half,players))))
    return frames


class GapLiveness(unittest.TestCase):
    def setUp(self):self.assertIsNotNone(g,'gap_liveness missing')
    def apply(self,frames):return g.apply_gap_rule(frames,['H']*len(frames))
    def test_no_long_gap_parity(self):
        f=fixture(gaps=());labels=tuple('HAD'[i%3] for i in range(len(f)))
        self.assertEqual(g.apply_gap_rule(f,labels).labels,labels)
    def test_slow_gap_only_is_dead(self):
        result=self.apply(fixture());self.assertEqual(result.labels,tuple('H'*300+'D'*200+'H'*400))
        self.assertAlmostEqual(result.summary['reference_speed_mps'],2.)
        self.assertEqual(result.summary['stoppage_gaps'],1)
    def test_fast_gap_unchanged(self):self.assertEqual(self.apply(fixture(gap_speed=4.)).labels,('H',)*900)
    def test_75_and_76_frame_boundary(self):
        for length in (75,76):
            result=self.apply(fixture(gaps=((300,300+length),)))
            self.assertEqual(result.summary['long_gaps'],int(length==76))
            self.assertEqual(result.labels[300:300+length],('D' if length==76 else 'H',)*length)
    def test_period_start_gap(self):
        result=self.apply(fixture(gaps=((0,200),)))
        self.assertEqual(result.labels[:200],('D',)*200)
    def test_period_boundary_splits_and_classifies_separately(self):
        f=fixture(gaps=((200,400),),periods=[1]*300+[2]*600,gap_speed=lambda i:0. if i<300 else 4.)
        result=self.apply(f)
        self.assertEqual(result.summary['long_gaps'],2)
        self.assertEqual(result.labels[200:400],tuple('D'*100+'H'*100))
    def test_restart_extension_and_cap(self):
        for length in (40,400):
            f=fixture(n=1100);ball=(f[299].ball_x,0.)
            for i in range(500,500+length):f[i]=replace(f[i],ball_x=ball[0],ball_y=0.)
            result=self.apply(f);stop=500+min(length,250)
            self.assertEqual(result.labels[500:stop],('D',)*(stop-500))
            self.assertEqual(result.labels[stop],'H')
    def test_restart_stops_at_next_missing_or_period_end(self):
        for barrier in ('missing','period'):
            f=fixture();x=f[299].ball_x
            for i in range(500,550):f[i]=replace(f[i],ball_x=x,ball_y=0.)
            f[510]=replace(f[510],ball_x=None,ball_y=None) if barrier=='missing' else replace(f[510],period=2)
            result=self.apply(f)
            self.assertEqual(result.labels[500:510],('D',)*10)
            self.assertEqual(result.labels[510],'H')
    def test_no_extension_for_nonstoppage(self):
        f=fixture(gap_speed=4.);x=f[299].ball_x
        for i in range(500,540):f[i]=replace(f[i],ball_x=x,ball_y=0.)
        self.assertEqual(self.apply(f).labels,('H',)*900)
    def test_insufficient_players(self):self.assertEqual(self.apply(fixture(players=8)).labels,('H',)*900)
    def test_period_zero_never_changes(self):
        f=fixture(gaps=((0,200),));f=[replace(v,period=0) if i<200 else v for i,v in enumerate(f)]
        self.assertEqual(self.apply(f).labels[:200],('H',)*200)
    def test_mirror_symmetry(self):
        f=fixture();mirror=[replace(v,home_xy=v.away_xy,away_xy=v.home_xy,home_ids=v.away_ids,away_ids=v.home_ids) for v in f]
        self.assertEqual(self.apply(f).labels,self.apply(mirror).labels)
    def test_scale_invariance_below_cap(self):
        f=fixture(gap_speed=.5)
        scaled=[replace(v,home_xy=tuple((2*x,2*y) for x,y in v.home_xy),away_xy=tuple((2*x,2*y) for x,y in v.away_xy)) for v in f]
        self.assertEqual(self.apply(f).labels,self.apply(scaled).labels)
    def test_determinism(self):
        f=fixture();digest=lambda:hashlib.sha256(''.join(self.apply(f).labels).encode()).hexdigest()
        self.assertEqual(digest(),digest())
    def test_exact_reference_tie_is_not_stoppage(self):self.assertEqual(self.apply(fixture(gap_speed=2.)).labels,('H',)*900)
    def test_no_reference_defined(self):self.assertEqual(self.apply(fixture(n=200,gaps=((0,200),))).labels,('H',)*200)
    def test_cap_and_team_identity_namespace(self):
        f=fixture(n=30,gaps=(),players=10)
        f=[replace(v,home_ids=tuple(range(5)),away_ids=tuple(range(5))) for v in f]
        stat=g.player_speed_statistics(f);self.assertAlmostEqual(stat[25],2.)
        f=[replace(v,home_xy=tuple((x*6,y) for x,y in v.home_xy),away_xy=tuple((x*6,y) for x,y in v.away_xy)) for v in f]
        self.assertIsNone(g.player_speed_statistics(f)[25])
    def test_restart_uses_last_observation_literally(self):
        f=fixture();new=f[299].ball_x+10
        for i in range(500,540):f[i]=replace(f[i],ball_x=new,ball_y=0.)
        self.assertEqual(self.apply(f).labels[500:540],('H',)*40)
    def test_invalid_dimensions_ids_or_labels(self):
        f=fixture(n=50,gaps=())
        with self.assertRaises(ValueError):g.apply_gap_rule(f,['H'])
        with self.assertRaises(ValueError):g.apply_gap_rule(f,['Z']*50)
        f[25]=replace(f[25],home_ids=(1,)*6)
        with self.assertRaises(ValueError):g.player_speed_statistics(f)
    def test_pure_imports_and_no_large_integer_literals(self):
        tree=ast.parse(Path('gap_liveness.py').read_text(encoding='utf-8-sig'))
        allowed={'dataclasses','math','statistics','numbers'}
        for node in ast.walk(tree):
            if isinstance(node,ast.ImportFrom):self.assertIn(node.module,allowed)
            if isinstance(node,ast.Import):self.assertTrue(all(a.name in allowed for a in node.names))
            if isinstance(node,ast.Constant) and type(node.value) is int:self.assertLessEqual(node.value,1000)
    def test_frozen_release_hash(self):
        self.assertEqual(hashlib.sha256(Path('competition_release.py').read_bytes()).hexdigest(),'e8d35e15be9524270bed82352791dc2849087b49b4c2b59c191023954b19eddb')

    def test_unassociated_players_are_excluded_not_fatal(self):
        f=fixture(n=30,gaps=(),players=12)
        f=[replace(v,home_ids=(None,)+v.home_ids[1:]) for v in f]
        self.assertAlmostEqual(g.player_speed_statistics(f)[25],2.)
    def test_player_order_does_not_define_correspondence(self):
        f=fixture(n=30,gaps=())
        f[25]=replace(f[25],home_xy=tuple(reversed(f[25].home_xy)),home_ids=tuple(reversed(f[25].home_ids)))
        self.assertAlmostEqual(g.player_speed_statistics(f)[25],2.)
