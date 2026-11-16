import unittest
try:
    import metrica_ball_reference as b
    import metrica_event_reference as r
except ImportError:b=r=None


class BallReference(unittest.TestCase):
    def setUp(self):self.assertIsNotNone(b,'metrica_ball_reference missing')
    def event(self,start,end,team='H',kind='PASS',tokens=(),period=1):return r.Event(period,start,end,team,kind,tuple(tokens))
    def seen(self,n,*gaps):
        out=[True]*n
        for first,stop in gaps:out[first:stop]=[False]*(stop-first)
        return out

    def test_long_ball_gap_is_dead_without_any_stop_event(self):
        events=[self.event(1,2),self.event(3,4,kind='BALL LOST',tokens=('FORCED',)),self.event(35,36,team='A',kind='SET PIECE'),self.event(40,41,team='A')]
        labels,summary=b.build_ball_reference(events,[1]*45,self.seen(45,(5,35)))
        self.assertEqual(labels[1:5],('H',)*4);self.assertEqual(labels[5:35],('D',)*30);self.assertEqual(labels[35:42],('A',)*7)
        self.assertEqual(summary['dead_gap_frames'],30)

    def test_glitch_carries_owner_and_medium_gap_is_unknown(self):
        events=[self.event(1,2),self.event(60,61,team='A')]
        labels,_=b.build_ball_reference(events,[1]*62,self.seen(62,(5,10),(20,35)))
        self.assertEqual(labels[5:10],('H',)*5);self.assertEqual(labels[20:35],('X',)*15);self.assertEqual(labels[35],'H')

    def test_stop_followed_by_open_play_is_unknown_not_dead(self):
        events=[self.event(1,2),self.event(3,4,team='A',kind='FAULT RECEIVED'),self.event(8,9),self.event(12,13,team='A')]
        labels,summary=b.build_ball_reference(events,[1]*14,self.seen(14))
        self.assertEqual(labels[4:8],('X',)*4);self.assertEqual(labels[8:12],('H',)*4);self.assertEqual(summary['reopened_stops'],1)

    def test_stop_confirmed_by_set_piece_with_ball_in_view(self):
        events=[self.event(1,2),self.event(3,4,kind='BALL OUT'),self.event(8,9,team='A',kind='SET PIECE'),self.event(12,13,team='A')]
        labels,_=b.build_ball_reference(events,[1]*14,self.seen(14))
        self.assertEqual(labels[4:8],('D',)*4);self.assertEqual(labels[8],'A')

    def test_stop_confirmed_by_ball_gap(self):
        events=[self.event(1,2),self.event(3,4,kind='BALL OUT'),self.event(40,41,team='A',kind='SET PIECE'),self.event(44,45,team='A')]
        labels,_=b.build_ball_reference(events,[1]*46,self.seen(46,(6,40)))
        self.assertEqual(labels[4:40],('D',)*36);self.assertEqual(labels[40],'A')

    def test_set_piece_inside_gap_waits_for_ball(self):
        events=[self.event(1,2),self.event(30,30,team='A',kind='SET PIECE'),self.event(45,46,team='A')]
        labels,_=b.build_ball_reference(events,[1]*47,self.seen(47,(5,40)))
        self.assertEqual(labels[5:40],('D',)*35);self.assertEqual(labels[40:46],('A',)*6)

    def test_owner_is_cleared_by_dead_gap_until_next_event(self):
        events=[self.event(1,2),self.event(40,41,team='A')]
        labels,_=b.build_ball_reference(events,[1]*42,self.seen(42,(5,35)))
        self.assertEqual(labels[35:40],('X',)*5);self.assertEqual(labels[40],'A')

    def test_periods_and_dimensions(self):
        with self.assertRaises(ValueError):b.build_ball_reference([],[1]*3,[True]*2)
        labels,_=b.build_ball_reference([self.event(1,2),self.event(6,7,team='A',period=2)],[1]*4+[0]+[2]*4,[True]*9)
        self.assertEqual(labels[4],'X');self.assertEqual(labels[5],'X');self.assertEqual(labels[6:8],('A','A'))


if __name__=='__main__':unittest.main()
