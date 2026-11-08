import csv
from pathlib import Path
import tempfile
import unittest

try:
    from gap_solver.motion import load_motion_atd
except ImportError:
    load_motion_atd=None


def write_atd(root,broken=False,bad_quality=False):
    metadata=root/'meta.xml'
    metadata.write_text('<Match><Team id="h"><Name>Home</Name></Team><Team id="a"><Name>Away</Name></Team>'+
                        ''.join('<Player id="p{}" teamId="{}"/>'.format(i,'h' if i<3 else 'a') for i in range(6))+'</Match>')
    raw=root/'tracking.txt'
    players=';'.join('0.2,0.3,0' if i<3 else '0.7,0.6,0' for i in range(6))
    missing=players if not broken else 'bad;'+players.split(';',1)[1]
    raw.write_text('1:'+missing+':nan,nan,nan\n2:'+players+':0.2,0.3,0\n3:'+players+':0.2,0.3,0\n')
    quality=root/'homography.csv'
    with quality.open('w',newline='') as handle:
        writer=csv.writer(handle)
        writer.writerow(['frame','valid','reprojection_error']+['h'+str(i)+str(j) for i in range(3) for j in range(3)])
        for n in range(3):writer.writerow([n,1,4 if bad_quality and n==1 else 1]+[int(i==j) for i in range(3) for j in range(3)])
    return metadata,raw,quality


class MotionATD(unittest.TestCase):
    def test_missing_ball_does_not_discard_available_players(self):
        self.assertIsNotNone(load_motion_atd,'motion adapter is missing')
        with tempfile.TemporaryDirectory() as d:
            records,names=load_motion_atd(*write_atd(Path(d)),n_frames=3,blocks=[(1,0,2)])
            self.assertEqual(names,('Home','Away'))
            self.assertEqual(len(records),3)
            self.assertFalse(records[0].ball_observed)
            self.assertEqual(len(records[0].home_xy),3)
            self.assertEqual(len(records[0].away_xy),3)
            self.assertAlmostEqual(records[0].home_xy[0][0],21.06)
            self.assertIsNone(records[0].home_distance)
            self.assertEqual(records[0].home_ids,records[1].home_ids)
            self.assertTrue(all(not f.dead_evidence and not f.tag_team for f in records))
            self.assertIsNone(records[1].ball_native_observation,'ATD availability is not independent detection evidence')

    def test_malformed_player_is_rejected_even_when_ball_is_missing(self):
        self.assertIsNotNone(load_motion_atd)
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):load_motion_atd(*write_atd(Path(d),broken=True),n_frames=3,blocks=[(1,0,2)])

    def test_bad_homography_masks_players_as_well_as_ball(self):
        self.assertIsNotNone(load_motion_atd)
        with tempfile.TemporaryDirectory() as d:
            frames,_=load_motion_atd(*write_atd(Path(d),bad_quality=True),n_frames=3,blocks=[(1,0,2)])
            self.assertFalse(frames[1].geometry_valid)
            self.assertEqual(frames[1].home_xy,())
            self.assertFalse(frames[1].ball_observed)
            self.assertTrue(frames[2].geometry_valid)

