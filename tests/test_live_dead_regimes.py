"""Live/dead sequence experiment: jitter and player-degradation regimes.  Synthetic only."""
from dataclasses import replace
import hashlib
import unittest

import numpy as np

import live_dead_regimes as lr
from gap_solver.tactical import feature_rows
from live_dead_features import liveness_inputs
from live_dead_protocol import SEED_PREFIX
from recent_geometry_regimes import distance_recompute_audit
from tests.test_live_dead_features import frame, PITCH


def match(count=400):
    fs = [frame(i, period=1 if i < 260 else 2, ball=None if 100 <= i < 110 else (40. + i * .05, 30.))
          for i in range(count)]
    fs[0] = replace(fs[0], period=0)
    return fs


class JitterTest(unittest.TestCase):
    def test_jitter_leaves_players_identical(self):
        fs = match()
        out = lr.jitter_ball(fs, 'dfl-J03WR9')
        a, b = liveness_inputs(fs, PITCH), liveness_inputs(out, PITCH)
        for name in ('instant', 'temporal', 'eligible'):
            self.assertEqual(getattr(a, name).tobytes(), getattr(b, name).tobytes())
        self.assertNotEqual(fs[50].ball_x, out[50].ball_x)
        self.assertIs(out[105], fs[105])

    def test_jitter_seed_prefix(self):
        a, b = lr.jitter_ball(match(), 'x'), lr.jitter_ball(match(), 'y')
        self.assertNotEqual(a[50].ball_x, b[50].ball_x)
        self.assertEqual(lr.jitter_seed('x'), int(hashlib.sha256((SEED_PREFIX + 'jitter:x').encode()).hexdigest()[:8], 16))


class DegradeTest(unittest.TestCase):
    def test_degrade_deterministic(self):
        self.assertEqual(lr.degrade_players(match(), 'c'), lr.degrade_players(match(), 'c'))

    def test_degrade_quarter_per_block(self):
        fs = match()
        keys = lr.removal_keys(fs, 'c')
        by_block = {}
        for period, block, team, pid in keys:
            by_block.setdefault((period, block), []).append((team, pid))
        self.assertEqual(set(by_block), {(1, 0), (1, 1), (1, 2), (2, 0), (2, 1)})    # 259 rows -> 3 blocks; 140 -> 2
        self.assertTrue(all(len(v) == 5 for v in by_block.values()))         # 22 // 4
        period, block = 1, 0
        ranked = sorted((hashlib.sha256(f'{SEED_PREFIX}c:{period}:{block}:{team}:{pid}'.encode()).hexdigest(), team, pid)
                        for team, ids in (('home', fs[5].home_ids), ('away', fs[5].away_ids)) for pid in ids)
        self.assertEqual(sorted(by_block[(1, 0)]), sorted((t, p) for _, t, p in ranked[:5]))

    def test_removed_ids_absent_in_their_block_only(self):
        fs = match()
        out = lr.degrade_players(fs, 'c')
        removed = {(t, p) for per, blk, t, p in lr.removal_keys(fs, 'c') if (per, blk) == (1, 0)}
        for i in range(1, 126):                                               # block 0 of period 1 = rows 1..125
            present = {('home', p) for p in out[i].home_ids} | {('away', p) for p in out[i].away_ids}
            self.assertFalse(present & removed)
            self.assertEqual(len(out[i].home_ids), len(out[i].home_xy))
        self.assertEqual(len(out[1].home_ids) + len(out[1].away_ids), 17)
        self.assertEqual(out[0], fs[0])                                       # period 0 untouched

    def test_degrade_independent_of_reference(self):
        fs = match()
        tagged = [replace(f, tag_team='H', dead_source='x') for f in fs]
        a = lr.degrade_players(fs, 'c')
        b = lr.degrade_players(tagged, 'c')
        self.assertEqual([(f.home_xy, f.away_xy, f.home_ids) for f in a], [(f.home_xy, f.away_xy, f.home_ids) for f in b])

    def test_degrade_leaves_ball_and_periods(self):
        fs = match()
        out = lr.degrade_players(fs, 'c')
        self.assertEqual([(f.period, f.ball_x, f.ball_y, f.geometry_valid) for f in fs],
                         [(f.period, f.ball_x, f.ball_y, f.geometry_valid) for f in out])
        self.assertNotEqual(out[200].home_xy[0], fs[200].home_xy[0])            # noise applied

    def test_degrade_distances_recomputed(self):
        audit = distance_recompute_audit(lr.degrade_players(match(), 'c'))
        self.assertEqual((audit['mismatched_rows'], audit['none_disagreements'], audit['max_abs_diff']), (0, 0, 0.))

    def test_degrade_empty_team_distance_none(self):
        fs = [frame(i, n=8) for i in range(130)]                              # 4 home, 4 away -> 2 removed
        fs = [replace(f, home_xy=f.home_xy[:1], home_ids=f.home_ids[:1]) for f in fs]
        out = lr.degrade_players(fs, 'e')
        empty = [f for f in out[:125] if not f.home_ids]
        if not empty:
            self.skipTest('hash order kept the lone home player; covered by the forced case below')
        self.assertTrue(all(f.home_distance is None and f.home_xy == () for f in empty))
        self.assertEqual(len(list(feature_rows(out))), len(out))

    def test_degrade_empty_team_forced(self):
        fs = [frame(i, n=8) for i in range(130)]
        fs = [replace(f, home_xy=f.home_xy[:1], home_ids=f.home_ids[:1]) for f in fs]
        case = next(c for c in ('c%d' % k for k in range(200))
                    if any(t == 'home' for _, b, t, _ in lr.removal_keys(fs, c) if b == 0))
        out = lr.degrade_players(fs, case)
        self.assertTrue(all(f.home_xy == () and f.home_distance is None for f in out[:125]))
        self.assertEqual(len(list(feature_rows(out))), len(out))
        np.asarray(liveness_inputs(out, PITCH).temporal)


if __name__ == '__main__':
    unittest.main()
