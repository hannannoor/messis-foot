import hashlib
from pathlib import Path
import tempfile
import unittest

from gap_solver.temporal import mask_motion_frames
from gap_solver.motion import motion_frame
import stoppage_regime as s

H, A, D, X = 0, 1, 2, 3


def h(text):
    return int(hashlib.sha256(text.encode()).hexdigest(), 16)


def reference(parts):
    """parts: list of (value, length)."""
    result = []
    for value, length in parts:
        result += [value] * length
    return result


class DeadBlocks(unittest.TestCase):
    def mask(self, ref, periods=None, regime='stop100', match='m'):
        periods = periods or [1] * len(ref)
        return s.make_mask(match, ref, periods, regime)

    def test_no_dead_gives_empty_stop100_mask(self):
        mask, info = self.mask(reference([(H, 500), (A, 500)]))
        self.assertFalse(any(mask))
        self.assertEqual(info['long_dead_runs'], 0)

    def test_natural_is_empty(self):
        mask, _ = self.mask(reference([(H, 100), (D, 300), (A, 100)]), regime='natural')
        self.assertFalse(any(mask))

    def test_75_not_long_76_is_long(self):
        self.assertEqual(self.mask(reference([(H, 200), (D, 75), (A, 200)]))[1]['long_dead_runs'], 0)
        self.assertEqual(self.mask(reference([(H, 200), (D, 76), (A, 200)]))[1]['long_dead_runs'], 1)

    def test_block_offsets_clipping_and_fallback(self):
        ref = reference([(H, 1000), (D, 300), (A, 1000)])
        start, stop = 1000, 1300
        a, b = h('m:a:%d' % start) % 51, h('m:b:%d' % start) % 51
        mask, info = self.mask(ref)
        self.assertEqual(info['dead_blocks'], [(start + a, stop + b)])
        self.assertEqual([i for i, v in enumerate(mask) if v], list(range(start + a, stop + b)))
        # clipped at the period end
        ref2 = reference([(H, 100), (D, 300)])
        mask2, info2 = self.mask(ref2)
        a2 = h('m:a:100') % 51
        self.assertEqual(info2['dead_blocks'], [(100 + a2, 400)])
        # fallback: a 76-frame run whose offsets would leave under 76 frames at the period end
        ref3 = reference([(H, 100), (D, 76)])
        _, info3 = self.mask(ref3)
        a3, b3 = h('m:a:100') % 51, h('m:b:100') % 51
        expected = (100, 176) if 176 - (100 + a3) < 76 else (100 + a3, 176)
        self.assertEqual(info3['dead_blocks'], [expected])
        self.assertTrue(a3 > 0)   # fixture really exercises the fallback

    def test_selection_levels(self):
        ref = []
        starts = []
        for i in range(40):
            ref += [H] * 50
            starts.append(len(ref))
            ref += [D] * 100
        _, full = self.mask(ref)
        self.assertEqual(full['selected'], len(starts))
        _, half = self.mask(ref, regime='stop50')
        expected = [x for x in starts if h('m:sel:%d' % x) % 100 < 50]
        self.assertEqual(half['selected_starts'], expected)
        _, three = self.mask(ref, regime='stop75')
        self.assertEqual(three['selected_starts'], [x for x in starts if h('m:sel:%d' % x) % 100 < 75])


class LiveBlocks(unittest.TestCase):
    def setUp(self):
        ref = []
        for i in range(30):
            ref += [D] * 100 + [H] * 400 + [A] * 400
        self.ref = ref
        self.periods = [1] * len(ref)

    def test_stop100_has_no_live_blocks(self):
        _, info = s.make_mask('m', self.ref, self.periods, 'stop100')
        self.assertEqual(info['live_blocks'], [])

    def test_live_blocks_rules(self):
        mask, info = s.make_mask('m', self.ref, self.periods, 'stop50')
        dead_removed = info['dead_frames_removed']
        live = info['live_blocks']
        self.assertGreaterEqual(sum(b - a for a, b in live), dead_removed)
        self.assertLess(sum(b - a for a, b in live[:-1]), dead_removed)   # exceeded by at most one window
        dead_cover = set()
        for a, b in info['dead_blocks']:
            dead_cover.update(range(a, b))
        for a, b in live:
            self.assertEqual(b - a, s.LIVE_WINDOW)
            self.assertTrue(all(self.ref[i] in (H, A) for i in range(a, b)))
            self.assertFalse(dead_cover & set(range(a, b)))
        order = [h('m:live:1:%d' % (a // s.LIVE_WINDOW)) for a, _ in live]
        self.assertEqual(order, sorted(order))

    def test_stop75_target_is_a_third(self):
        _, info = s.make_mask('m', self.ref, self.periods, 'stop75')
        live = sum(b - a for a, b in info['live_blocks'])
        self.assertGreaterEqual(3 * live, info['dead_frames_removed'])
        self.assertLess(3 * (live - s.LIVE_WINDOW), info['dead_frames_removed'])


class Structure(unittest.TestCase):
    def test_periods_independent_and_period_zero_untouched(self):
        ref = reference([(D, 200), (H, 100), (D, 200), (A, 100), (D, 200)])
        periods = [0] * 200 + [1] * 100 + [0] * 200 + [2] * 100 + [0] * 200
        mask, _ = s.make_mask('m', ref, periods, 'stop100')
        self.assertFalse(any(m for m, p in zip(mask, periods) if p == 0))
        ref2 = reference([(H, 50), (D, 200), (A, 50), (D, 200)])
        periods2 = [1] * 250 + [2] * 250
        _, info = s.make_mask('m', ref2, periods2, 'stop100')
        self.assertEqual(info['long_dead_runs'], 2)   # the dead run does not continue across the period boundary
        for a, b in info['dead_blocks']:
            self.assertTrue(b <= 250 or a >= 250)

    def test_deterministic_and_match_id_changes_selection(self):
        ref = []
        for i in range(60):
            ref += [H] * 30 + [D] * 100
        a1 = s.make_mask('m', ref, [1] * len(ref), 'stop50')
        a2 = s.make_mask('m', ref, [1] * len(ref), 'stop50')
        b = s.make_mask('other', ref, [1] * len(ref), 'stop50')
        self.assertEqual(a1, a2)
        self.assertNotEqual(a1[1]['selected_starts'], b[1]['selected_starts'])

    def test_masked_frames_lose_the_ball_and_others_unchanged(self):
        frames = [motion_frame(1, (float(i), 0.), [(0., 0.)], [(1., 1.)]) for i in range(300)]
        mask = [100 <= i < 200 for i in range(300)]
        out = mask_motion_frames(frames, mask)
        for i, (before, after) in enumerate(zip(frames, out)):
            if mask[i]:
                self.assertFalse(after.ball_observed)
            else:
                self.assertEqual(before, after)

    def test_modules_read_no_match_or_ground_truth_file(self):
        source = (Path(__file__).resolve().parent.parent / 'stoppage_regime.py').read_text(encoding='utf-8')
        for word in ('open(', 'read_text', 'ground', 'gt_public', 'target-handling', 'smart_tagging', '_atd'):
            self.assertNotIn(word, source)


class TouchParity(unittest.TestCase):
    def test_candidate_touch_with_no_events_equals_candidate(self):
        from release_fixtures import release_fixture
        from release_runtime import load_source
        import stoppage_runner as r
        with tempfile.TemporaryDirectory() as directory:
            for case in ('positive', 'invalid', 'unsupported'):
                frames, _ = load_source(*release_fixture(Path(directory) / case, case), scope='synthetic')
                labels = r.variant_labels(frames, events=[])
                self.assertEqual(labels['candidate+touch'], labels['candidate'])


if __name__ == '__main__':
    unittest.main()
