import csv
import tempfile
import unittest
from pathlib import Path

try:
    from gap_solver.input_contract import read_epts_contract, iter_records, audit_source
except ImportError:
    read_epts_contract = iter_records = audit_source = None


def fixture(root, rows=3):
    meta, raw, quality = (root / n for n in ('meta.xml','raw.txt','quality.csv'))
    # Declaration order is deliberately opposite to the actual register order.
    text = '<Match><FrameRate>25</FrameRate><FieldSize><Width>105</Width><Height>68</Height></FieldSize>'
    text += '<Team id="a"><Name>Athletic Club</Name></Team><Team id="h"><Name>Barcelona</Name></Team>'
    text += '<Player id="pa" teamId="a"/><Player id="ph" teamId="h"/>'
    for channel,name,unit in [('x','position_x','normalized'),('y','position_y','normalized'),('s','speed_kph','kph')]:
        text += f'<Channel id="{channel}"><Name>{name}</Name><Unit>{unit}</Unit></Channel>'
    for p in ('pa','ph'):
        for c in 'xys': text += f'<PlayerChannel id="{p}{c}" playerId="{p}" channelId="{c}"/>'
    text += f'<DataFormatSpecification startFrame="1" endFrame="{rows}" separator=":"><StringRegister name="frameCount"/><SplitRegister separator=";">'
    for p in ('ph','pa'):
        text += '<SplitRegister separator=",">'+''.join(f'<PlayerChannelRef playerChannelId="{p}{c}"/>' for c in 'xys')+'</SplitRegister>'
    text += '</SplitRegister><SplitRegister separator=",">'+''.join(f'<BallChannelRef channelId="{c}"/>' for c in 'xys')+'</SplitRegister></DataFormatSpecification></Match>'
    meta.write_text(text)
    raw.write_text(''.join(f'{i+1}:0.2,0.3,0;0.8,0.6,0:nan,nan,nan\n' for i in range(rows)))
    with quality.open('w',newline='') as h:
        w=csv.writer(h);w.writerow(['frame','valid','reprojection_error']+['h'+str(a)+str(b) for a in range(3) for b in range(3)])
        for i in range(rows): w.writerow([i,1,1]+[int(a==b) for a in range(3) for b in range(3)])
    return meta,raw,quality


class InputContract(unittest.TestCase):
    def setUp(self): self.assertIsNotNone(read_epts_contract,'strict input contract is missing')

    def test_numeric_fps_declaration_accepts_decimal_representation(self):
        with tempfile.TemporaryDirectory() as d:
            m,r,q=fixture(Path(d));m.write_text(m.read_text().replace('<FrameRate>25','<FrameRate>25.0'))
            self.assertEqual(read_epts_contract(m).rows,3)

    def test_legacy_roles_include_team_order_and_both_registered_sides_are_required(self):
        with tempfile.TemporaryDirectory() as d:
            m,r,q=fixture(Path(d));text=m.read_text()
            text=text.replace('<Player id="pa" teamId="a"/><Player id="ph" teamId="h"/>','<Player id="ph" teamId="h"/><Player id="pa" teamId="a"/>')
            m.write_text(text);report=audit_source(m,r,q,'tactical')
            self.assertTrue(report['legacy_slot_order_matches'])
            self.assertFalse(report['legacy_slot_roles_match'])
            self.assertFalse(report['legacy_team_order_matches'])
            m.write_text(text.replace('id="pa" teamId="a"','id="pa" teamId="h"'))
            with self.assertRaises(ValueError):read_epts_contract(m)

    def test_malformed_quality_schema_flags_and_row_width_fail_structurally(self):
        with tempfile.TemporaryDirectory() as d:
            m,r,q=fixture(Path(d));lines=q.read_text().splitlines();header=lines[0];row=lines[1]
            variants=[header+',valid\n'+row+',0\n'+lines[2]+',0\n'+lines[3]+',0\n',
                '\n'.join([header,row.replace(',1,1,',',yes,1,',1),*lines[2:]])+'\n',
                '\n'.join([header,row.rsplit(',',1)[0],*lines[2:]])+'\n',
                '\n'.join([header,row+',0',*lines[2:]])+'\n']
            for value in variants:
                q.write_text(value)
                with self.subTest(value=value):
                    with self.assertRaises(ValueError):audit_source(m,r,q,'tactical')

    def test_register_references_determine_roles_and_missing_ball_keeps_players(self):
        with tempfile.TemporaryDirectory() as d:
            m,r,q=fixture(Path(d)); c=read_epts_contract(m)
            rows=list(iter_records(c,r))
            self.assertEqual(c.sides,('H','A'))
            self.assertEqual(len(rows[0].home_xy),1)
            self.assertAlmostEqual(rows[0].home_xy[0][0],21.06)
            self.assertAlmostEqual(rows[0].home_xy[0][1],20.4)
            self.assertFalse(rows[0].ball_observed)
            report=audit_source(m,r,q,'tactical')
            self.assertEqual(report['rows'],3)
            self.assertEqual(report['repeated_adjacent_ball_xy'],0)
            self.assertEqual(report['repeated_adjacent_player_xy'],4)
            self.assertFalse(report['freshness_verified'])
            self.assertTrue(report['speed_unit_conflict'])

    def test_ambiguous_roles_broken_refs_units_fps_and_split_specs_fail(self):
        with tempfile.TemporaryDirectory() as d:
            m,r,q=fixture(Path(d)); original=m.read_text()
            for old,new in [('Barcelona','Other'),('Athletic Club','Barcelona'),('playerChannelId="phx"','playerChannelId="absent"'),('<FrameRate>25','<FrameRate>30'),('<Unit>normalized','<Unit>meters'),('separator=";"','separator="|"')]:
                with self.subTest(old=old):
                    m.write_text(original.replace(old,new))
                    with self.assertRaises(ValueError):read_epts_contract(m)

    def test_malformed_numbers_dimensions_indices_and_quality_fail(self):
        with tempfile.TemporaryDirectory() as d:
            m,r,q=fixture(Path(d));c=read_epts_contract(m);original=r.read_text()
            for text in [original.replace('0.2','oops',1),original.replace('0.2','inf',1),original.replace('1:','2:',1),original.replace(';0.8,0.6,0','',1),original.rsplit('\n',2)[0]+'\n']:
                r.write_text(text)
                with self.assertRaises(ValueError):list(iter_records(c,r))
            r.write_text(original);q.write_text(q.read_text().replace('0,1,1','5,1,1',1))
            with self.assertRaises(ValueError):audit_source(m,r,q,'tactical')


if __name__=='__main__': unittest.main()
