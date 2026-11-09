"""Independent geometry/clock expectations for the quarantined adapter."""
from contextlib import closing
from pathlib import Path
import sqlite3
import tempfile
import unittest

from wcsf_fixtures import rows,source_paths
from wcsf_source import ingest


class GeometryTests(unittest.TestCase):
    def setUp(self):
        try:import wcsf_geometry
        except ImportError:self.fail('Missing input-only reconstruction and grid')
        self.api=wcsf_geometry;self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)

    def store(self,name,first=None,second=None):
        paths=source_paths(self.root/name,first,second);ingest(paths);return paths.geometry_db

    def test_four_global_hypotheses_recover_known_geometry(self):
        for h in ('absolute-x','absolute-xy','offset-x','offset-xy'):
            db=self.store(h,rows(hypothesis=h),rows(hypothesis=h));d=self.api.qualify(db)
            with self.subTest(h=h):self.assertEqual((d.selected,d.eligible,d.failure),(h,202,None))
            c=self.api.canonical_input(db,d);f=c.frames[0]
            self.assertAlmostEqual(f.ball_x,62.67857142857143);self.assertAlmostEqual(f.ball_y,38.)
            self.assertAlmostEqual(f.away_xy[0][0],72.70714285714286)

    def test_ambiguous_zero_and_multiple_pass_stop(self):
        ambiguous=rows()
        for r in ambiguous:r['y_ball']=0
        db=self.store('ambiguous',ambiguous,ambiguous);d=self.api.qualify(db)
        self.assertIsNone(d.selected)
        with self.assertRaises(ValueError):self.api.canonical_input(db,d)
        data=rows()
        for i,r in enumerate(data):r['x_ball']=i*3
        d=self.api.qualify(self.store('none',data,data));self.assertIsNone(d.selected)
        self.assertIsNone(self.api.qualify(self.store('short',rows(49),rows(49))).selected)

    def test_quarter_metre_and_99_percent_bounds(self):
        first=rows(100);second=rows(100)
        for data in (first,second):data[0]['x_ball']+=.25
        self.assertEqual(self.api.qualify(self.store('quarter',first,second)).selected,'absolute-x')
        for data in (first,second):data[0]['x_ball']+=.001
        d=self.api.qualify(self.store('99',first,second));self.assertEqual(d.selected,'absolute-x');self.assertEqual(d.candidate_counts['absolute-x'],198)
        first[6]['x_ball']+=1
        self.assertIsNone(self.api.qualify(self.store('985',first,second)).selected)

    def test_common_eligibility_missing_player_and_coordinatewise_median(self):
        data=rows()
        data.append(dict(data[0],player_id=999,x='',y='',x_ball=999,y_ball=999))
        db=self.store('missing',data,data);d=self.api.qualify(db);self.assertEqual(d.selected,'absolute-x')
        c=self.api.canonical_input(db,d);self.assertAlmostEqual(c.frames[0].ball_x,62.67857142857143)
        # Six agreeing points, deterministic even-count median, not first/last row.
        first=rows()
        for r in first:
            if r['group_id']==1:r['x_ball']+=(r['player_id']-101)*.1
        db=self.store('median',first,first);d=self.api.qualify(db);c=self.api.canonical_input(db,d)
        self.assertAlmostEqual(c.frames[0].ball_x,62.67857142857143)

    def test_row_order_and_label_perturbations_do_not_select_transform(self):
        first=rows();other=[dict(r,AliveFlag=0,PossessionFlag=999) for r in reversed(first)]
        a=self.store('a',first,first);b=self.store('b',other,other)
        da=self.api.qualify(a);db=self.api.qualify(b)
        self.assertEqual(da,db)
        self.assertEqual(self.api.canonical_input(a,da),self.api.canonical_input(b,db))

    def test_center_to_corner_conversion(self):
        data=rows()
        for r in data:
            if r['group_id']==1:
                r['x']=(-52.5,0,52.5)[r['player_id']-100];r['y']=(-34,0,34)[r['player_id']-100]
        db=self.store('corners',data,data);c=self.api.canonical_input(db,self.api.qualify(db))
        for got,want in zip(c.frames[0].home_xy,((0.,0.),(52.65,34.),(105.3,68.))):
            self.assertAlmostEqual(got[0],want[0]);self.assertAlmostEqual(got[1],want[1])

    def test_no_gap_or_endpoint_extrapolation(self):
        data=[r for r in rows(105) if r['timestamp_ms']!=100]
        db=self.store('gap',data,data);c=self.api.canonical_input(db,self.api.qualify(db))
        at={t:f for (p,t),f in zip(c.index,c.frames) if p==1}
        self.assertTrue(at[0].ball_observed);self.assertFalse(at[40].geometry_valid);self.assertFalse(at[160].ball_observed)
        self.assertTrue(at[200].ball_observed);self.assertTrue(at[240].ball_interpolated)
        self.assertEqual(max(at),10400);self.assertEqual(min(at),0)

    def test_player_membership_changes_not_interpolated(self):
        data=rows(101);data=[r for r in data if not(r['timestamp_ms']==100 and r['player_id']==102)]
        db=self.store('ids',data,data);c=self.api.canonical_input(db,self.api.qualify(db))
        self.assertEqual(c.frames[0].home_ids,(100,101,102));self.assertEqual(c.frames[1].home_ids,(100,101))
        self.assertFalse(c.frames[1].dead_evidence);self.assertEqual(c.frames[1].tag_team,'')

    def test_native_vs_interpolated_endpoints_retained(self):
        db=self.store('provenance');c=self.api.canonical_input(db,self.api.qualify(db))
        self.assertEqual(c.endpoints[:3],[(0,0),(0,100),(0,100)])
        self.assertTrue(c.frames[0].ball_native_observation);self.assertFalse(c.frames[1].ball_native_observation)
        self.assertEqual(c.quality['canonical_rows'],502);self.assertEqual(c.quality['native_grid_rows'],102)

    def test_clock_span_rejected_before_grid_allocation(self):
        db=self.store('clock')
        with closing(sqlite3.connect(db)) as con:
            con.execute('update geometry set t=t+5400100 where t=10000');con.commit()
        with self.assertRaises(ValueError):self.api.qualify(db)


if __name__=='__main__':unittest.main()
