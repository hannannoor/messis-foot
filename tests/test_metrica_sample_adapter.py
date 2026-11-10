from pathlib import Path
import csv,tempfile,unittest
from xml.etree.ElementTree import Element,SubElement,ElementTree
try:
    import metrica_sample_adapter as a
except ImportError:a=None


def csv_side(path,role,players,balls):
    ids=[str(i+1) for i in range(players)];head=['','','']+sum(([role,''] for _ in ids),[])+['','']
    numbers=['','','']+sum(([i,''] for i in ids),[])+['',''];names=['Period','Frame','Time [s]']+sum((['Player'+i,''] for i in ids),[])+['Ball','']
    with path.open('w',newline='') as f:
        w=csv.writer(f);w.writerows((head,numbers,names))
        for i,ball in enumerate(balls,1):w.writerow([1 if i<=2 else 2,i,i/25]+sum(([.1*j,.2*j] for j in range(players)),[])+(list(ball) if ball else ['nan','nan']))


def xml_fixture(path):
    root=Element('main');SubElement(root,'FrameRate').text='25'
    field=SubElement(root,'FieldSize');SubElement(field,'Width').text='105';SubElement(field,'Height').text='68'
    for tid in ('h','a'):SubElement(root,'Team',id=tid)
    for pid,team in (('h1','h'),('h2','h'),('a1','a')):SubElement(root,'Player',id=pid,teamId=team)
    for axis in 'xy':
        c=SubElement(root,'Channel',id=axis);SubElement(c,'Name').text='position_'+axis;SubElement(c,'Unit').text='normalized'
        for pid in ('h1','h2','a1'):SubElement(root,'PlayerChannel',id=pid+axis,playerId=pid,channelId=axis)
    for name,value in (('first_half_start',1),('first_half_end',2),('second_half_start',3),('second_half_end',4)):
        p=SubElement(root,'ProviderParameter');SubElement(p,'Name').text=name;SubElement(p,'Value').text=str(value)
    for start,end,h in ((1,2,'h1'),(3,4,'h2')):
        spec=SubElement(root,'DataFormatSpecification',startFrame=str(start),endFrame=str(end),separator=':');SubElement(spec,'StringRegister',name='frameCount')
        split=SubElement(spec,'SplitRegister',separator=';')
        for pid in (h,'a1'):
            pair=SubElement(split,'SplitRegister',separator=',')
            for axis in 'xy':SubElement(pair,'PlayerChannelRef',playerChannelId=pid+axis)
        ball=SubElement(spec,'SplitRegister',separator=',')
        for axis in 'xy':SubElement(ball,'BallChannelRef',channelId=axis)
    ElementTree(root).write(path,encoding='utf-8')

class MetricaAdapter(unittest.TestCase):
    def setUp(self):self.assertIsNotNone(a,'metrica_sample_adapter missing')
    def test_csv_varied_rosters_and_missing_ball(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()/'.tmp') as d:
            root=Path(d);home=root/'home';away=root/'away';balls=[(.5,.5),None,(.6,.5),(.7,.5)]
            csv_side(home,'Home',2,balls);csv_side(away,'Away',1,balls)
            frames=a.load_csv_tracking(home,away)
            self.assertEqual([f.period for f in frames],[1,1,2,2]);self.assertEqual(len(frames[0].home_xy),2)
            self.assertFalse(frames[1].ball_observed);self.assertAlmostEqual(frames[0].ball_x,52.65)
            self.assertEqual(frames[0].home_ids,('1','2'))
    def test_conflicting_duplicate_ball_stream_fails(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()/'.tmp') as d:
            root=Path(d);csv_side(root/'h','Home',1,[(.5,.5)]);csv_side(root/'a','Away',1,[(.4,.5)])
            with self.assertRaises(ValueError):a.load_csv_tracking(root/'h',root/'a')
    def test_xml_dynamic_channels_periods_and_ids(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()/'.tmp') as d:
            root=Path(d);xml_fixture(root/'meta.xml')
            (root/'track.txt').write_text(''.join(str(i)+':0.1,0.2;0.9,0.8:'+('nan,nan' if i==2 else '0.5,0.5')+'\n' for i in range(1,5)))
            frames,mapping=a.load_epts_tracking(root/'meta.xml',root/'track.txt')
            self.assertEqual(mapping,{'h':'H','a':'A'});self.assertEqual(frames[2].home_ids,('h2',))
            self.assertEqual([f.period for f in frames],[1,1,2,2]);self.assertFalse(frames[1].ball_observed)
    def test_reject_non_25hz_before_tracking(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()/'.tmp') as d:
            root=Path(d);xml_fixture(root/'meta.xml');s=(root/'meta.xml').read_text().replace('<FrameRate>25</FrameRate>','<FrameRate>10</FrameRate>');(root/'meta.xml').write_text(s)
            with self.assertRaises(ValueError):a.load_epts_tracking(root/'meta.xml',root/'missing')

    def test_one_sided_ball_missing_is_missing(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()/'.tmp') as d:
            root=Path(d);csv_side(root/'h','Home',1,[None]);csv_side(root/'a','Away',1,[(.5,.5)])
            self.assertFalse(a.load_csv_tracking(root/'h',root/'a')[0].ball_observed)
    def test_broken_xml_pair_reference_rejected(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()/'.tmp') as d:
            root=Path(d);xml_fixture(root/'meta.xml');s=(root/'meta.xml').read_text().replace('playerChannelId="h1y"','playerChannelId="a1y"');(root/'meta.xml').write_text(s)
            with self.assertRaises(ValueError):a.load_epts_tracking(root/'meta.xml',root/'missing')
