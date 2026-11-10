from dataclasses import asdict
import unittest
try:
    import metrica_event_reference as r
except ImportError:r=None

class MetricaReference(unittest.TestCase):
    def setUp(self):self.assertIsNotNone(r,'metrica_event_reference missing')
    def event(self,start,end,team='H',kind='PASS',tokens=(),period=1):return r.Event(period,start,end,team,kind,tuple(tokens))
    def test_same_team_chain_and_owner_change(self):
        events=[self.event(1,3),self.event(4,6),self.event(7,8,team='A')]
        labels,summary=r.build_reference(events,[1]*10)
        self.assertEqual(labels,tuple('XHHHHHHAAX'));self.assertEqual(summary['known_frames'],8)
    def test_out_latch_and_restart(self):
        events=[self.event(1,1),self.event(3,4,kind='BALL OUT'),self.event(5,5,team='A'),self.event(7,8,team='A',kind='SET PIECE')]
        labels,_=r.build_reference(events,[1]*10)
        self.assertEqual(labels[4:7],('D',)*3);self.assertEqual(labels[7:9],('A',)*2)
    def test_goal_exact_token_and_foul(self):
        events=[self.event(1,1,kind='SET PIECE',tokens=('GOAL KICK',)),self.event(2,4,kind='SHOT',tokens=('ON TARGET','GOAL')),self.event(6,6,kind='SET PIECE'),self.event(7,8,kind='FAULT RECEIVED')]
        labels,_=r.build_reference(events,[1]*10)
        self.assertEqual(labels[1],'H');self.assertEqual(labels[4:6],('D','D'));self.assertEqual(labels[8],'D')
    def test_challenge_result_and_advantage(self):
        events=[self.event(1,1),self.event(2,3,team='A',kind='CHALLENGE',tokens=('LOST',)),self.event(4,5,team='A',kind='CHALLENGE',tokens=('ADVANTAGE','WON')),self.event(7,8,team='A',kind='CHALLENGE',tokens=('FAULT','WON'))]
        labels,_=r.build_reference(events,[1]*10)
        self.assertEqual(labels[3],'H');self.assertEqual(labels[5],'A');self.assertEqual(labels[8],'D')
    def test_conflict_and_period_reset(self):
        events=[self.event(1,1),self.event(1,1,team='A'),self.event(3,4,team='A'),self.event(7,8,team='H',period=2)]
        labels,_=r.build_reference(events,[1]*5+[2]*5)
        self.assertEqual(labels[1:3],('X','X'));self.assertEqual(labels[5:7],('X','X'));self.assertEqual(labels[7:9],('H','H'))
    def test_simultaneous_restart_wins_stop(self):
        labels,_=r.build_reference([self.event(1,3,kind='BALL OUT'),self.event(3,4,team='A',kind='SET PIECE')],[1]*6)
        self.assertEqual(labels[3],'A')
    def test_csv_and_json_normalize_equally(self):
        csv=dict(Team='Home',Type='SHOT',Subtype='ON TARGET-GOAL',Period='1',**{'Start Frame':'26','Start Time [s]':'1.04','End Frame':'51','End Time [s]':'2.04'})
        js=dict(team={'id':'one'},type={'name':'SHOT'},subtypes=[{'name':'ON TARGET'},{'name':'GOAL'}],period=1,start=dict(frame=26,time=1.04),end=dict(frame=51,time=2.04))
        self.assertEqual(r.normalize_csv(csv),r.normalize_json(js,{'one':'H'}))
    def test_bad_clock_or_unknown_kind_fail(self):
        js=dict(team={'id':'one'},type={'name':'UNKNOWN'},subtypes=None,period=1,start=dict(frame=1,time=.04),end=dict(frame=1,time=.04))
        with self.assertRaises(ValueError):r.normalize_json(js,{'one':'H'})
        js['type']['name']='PASS';js['start']['time']=10
        with self.assertRaises(ValueError):r.normalize_json(js,{'one':'H'})

    def test_pretracking_frame_zero_event_is_clipped_not_rejected(self):
        row=dict(Team='Home',Type='SET PIECE',Subtype='KICK OFF',Period='1',**{'Start Frame':'0','Start Time [s]':'0','End Frame':'0','End Time [s]':'0'})
        event=r.normalize_csv(row)
        self.assertEqual(event.start,-1)
        labels,summary=r.build_reference([event,self.event(1,3)],[1]*5)
        self.assertEqual(labels,tuple('XHHHX'));self.assertEqual(summary['outside_events'],1)

    def test_missing_set_piece_end_uses_only_documented_start(self):
        row=dict(Team='Away',Type='SET PIECE',Subtype='THROW IN',Period='1',**{'Start Frame':'26','Start Time [s]':'1.04','End Frame':'0','End Time [s]':'0'})
        event=r.normalize_csv(row)
        self.assertEqual((event.start,event.end,event.team),(25,25,'A'))
        self.assertTrue(event.missing_end)
        labels,summary=r.build_reference([event],[1]*30)
        self.assertEqual(labels[25],'A');self.assertEqual(summary['missing_end_events'],1)

    def test_card_is_inert_even_with_spurious_stop_tokens(self):
        labels,_=r.build_reference([self.event(1,1),self.event(3,4,team='A',kind='CARD',tokens=('GOAL','FAULT')),self.event(6,7)],[1]*9)
        self.assertEqual(labels[3:6],('H',)*3)
    def test_goal_only_stops_declared_goal_event_kinds(self):
        labels,_=r.build_reference([self.event(1,1),self.event(3,4,team='A',kind='RECOVERY',tokens=('GOAL',)),self.event(6,7,team='A')],[1]*9)
        self.assertEqual(labels[4:6],('A','A'))
    def test_unknown_team_and_period_gap_clipping(self):
        labels,_=r.build_reference([self.event(0,4),self.event(5,8,team='',period=2)],[1]*3+[0]*2+[2]*5)
        self.assertEqual(labels[3:5],('X','X'));self.assertEqual(labels[5:9],('X',)*4)
    def test_missing_end_non_restart_is_rejected(self):
        row=dict(Team='Home',Type='SHOT',Subtype='',Period='1',**{'Start Frame':'26','Start Time [s]':'1.04','End Frame':'0','End Time [s]':'0'})
        with self.assertRaises(ValueError):r.normalize_csv(row)

    def test_card_cannot_extend_reference_coverage(self):
        ordinary=[self.event(1,3)]
        a,_=r.build_reference(ordinary,[1]*10)
        b,_=r.build_reference(ordinary+[self.event(8,9,kind='CARD')],[1]*10)
        self.assertEqual(a,b)
