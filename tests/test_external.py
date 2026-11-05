import tempfile
import unittest
from pathlib import Path
import numpy as np

try:
    from gap_solver.external import load_external
except ImportError:
    load_external=None


META='<Root><General MatchId="fixture" HomeTeamId="home" GuestTeamId="away"/><Teams><Team TeamId="away" Role="guest"/><Team TeamId="home" Role="home"/></Teams></Root>'


def xml(ball_rows,sections=('firstHalf',),player_numbers=(100,101,102),home=True,away=True):
    pieces=['<Root><PitchSize X="105.3" Y="68"/>']
    for section in sections:
        for team,x in [('away',20),('home',0)]:
            if not (home if team=='home' else away):
                continue
            pieces.append('<FrameSet GameSection="{}" TeamId="{}" PersonId="{}">'.format(section,team,team))
            pieces.extend('<Frame N="{}" X="{}" Y="0"/>'.format(n,x) for n in player_numbers)
            pieces.append('</FrameSet>')
        pieces.append('<FrameSet GameSection="{}" TeamId="ball" PersonId="ball">'.format(section))
        pieces.extend('<Frame N="{}" X="0.5" Y="0" BallStatus="{}" BallPossession="{}"/>'.format(*row) for row in ball_rows)
        pieces.append('</FrameSet>')
    return ''.join(pieces)+'</Root>'


class ExternalAdapter(unittest.TestCase):
    def load(self,text):
        self.assertIsNotNone(load_external,'strict external adapter is missing')
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            meta,tracking=root/'meta.xml',root/'tracking.xml'
            meta.write_text(META);tracking.write_text(text)
            return load_external(meta,tracking)

    def test_raw_reference_states_and_metadata_team_order(self):
        result=self.load(xml([(100,1,1),(101,1,2),(102,0,0)]))
        self.assertEqual(result.reference.tolist(),[0,1,2])
        np.testing.assert_allclose(result.distances[:,0],.5)
        np.testing.assert_allclose(result.distances[:,1],19.5)
        np.testing.assert_allclose(result.ball_xy[0],[53.15,34],atol=.00001)

    def test_unknown_ownership_or_status_never_defaults_to_away(self):
        result=self.load(xml([(100,1,0),(101,2,1),(102,0,2)]))
        self.assertEqual(result.reference.tolist(),[3,3,2])

    def test_target_fields_cannot_change_inference_features(self):
        first=self.load(xml([(100,1,1),(101,1,2),(102,0,0)]))
        second=self.load(xml([(100,0,2),(101,0,1),(102,1,1)]))
        for name in ('periods','source_frames','ball_xy','distances','player_counts'):
            np.testing.assert_array_equal(getattr(first,name),getattr(second,name))
        self.assertFalse(np.array_equal(first.reference,second.reference))

    def test_missing_ball_and_missing_source_rows_are_preserved(self):
        result=self.load(xml([(100,1,1),(102,1,2)],player_numbers=(100,102)))
        self.assertEqual(result.source_frames.tolist(),[100,101,102])
        self.assertTrue(np.isnan(result.ball_xy[1]).all())
        self.assertEqual(result.reference.tolist(),[0,3,1])
        self.assertEqual(result.player_counts[1].tolist(),[0,0])

    def test_same_source_ids_in_two_periods_are_distinct(self):
        result=self.load(xml([(100,1,1),(101,1,1),(102,1,1)],sections=('firstHalf','secondHalf')))
        self.assertEqual(result.periods.tolist(),[1,1,1,2,2,2])
        self.assertEqual(result.source_frames.tolist(),[100,101,102,100,101,102])

    def test_missing_opponent_is_nan_not_infinity(self):
        result=self.load(xml([(100,1,1),(101,1,1),(102,1,1)],away=False))
        self.assertTrue(np.isnan(result.distances[:,1]).all())
        self.assertTrue(all(f.away_distance is None for f in result.frames()))

    def test_duplicate_ball_frame_and_incompatible_pitch_fail(self):
        for text in [xml([(100,1,1),(100,1,1)]),xml([(100,1,1)]).replace('X="105.3" Y="68"','X="0" Y="68"')]:
            with self.subTest(text=text[:50]),self.assertRaises(ValueError):
                self.load(text)


if __name__=='__main__':
    unittest.main()
