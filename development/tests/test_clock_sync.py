import unittest

from gap_solver.clock_sync import ClockRead, ClockTime, parse_clock, dense_clock, align_clocks


def reads(offset=0, half=1, seconds=8, stride=5):
    return [ClockRead(frame=i + offset, text='19:{:02d}'.format(i // 25),
                      confidence=0.95, half=half) for i in range(0, seconds * 25, stride)]


class ClockAlignment(unittest.TestCase):
    def test_clock_formats_and_added_time(self):
        self.assertEqual(parse_clock('27:02'), 1622)
        self.assertEqual(parse_clock('19 : 06'), 1146)
        self.assertEqual(parse_clock('45+02:13'), 2833)
        self.assertEqual(parse_clock('90+01:02'), 5462)
        for invalid in ('19:99', '1-0', 'abc', '01:19:06', '2702'):
            self.assertIsNone(parse_clock(invalid))

    def test_second_ticks_produce_fractional_time_not_equal_second_buckets(self):
        clock = dense_clock(reads(), n_frames=200)
        self.assertIsNotNone(clock[80])
        self.assertGreater(clock[90].seconds, clock[80].seconds)
        self.assertLess(clock[80].uncertainty_s, 0.13)
        self.assertIsNone(clock[0])  # no extrapolation before first reliable tick

    def test_piecewise_alignment_preserves_different_frame_indices(self):
        t = dense_clock(reads(), 200)
        b = dense_clock(reads(offset=37), 237)
        mapped = align_clocks(t, b)
        self.assertEqual(mapped[80].broadcast_frame, 117)
        self.assertEqual(mapped[80].status, 'clock_candidate')

    def test_duplicate_clock_segments_are_rejected(self):
        t = dense_clock(reads(), 200)
        b = dense_clock(reads() + reads(offset=250), 450)
        self.assertEqual(align_clocks(t, b)[80].status, 'duplicate_clock_candidates')

    def test_opposite_halves_never_match(self):
        t = dense_clock(reads(), 200)
        b = dense_clock(reads(half=2), 200)
        self.assertIsNone(align_clocks(t, b)[80].broadcast_frame)

    def test_frozen_clock_and_poor_ocr_provide_no_dense_clock(self):
        frozen = [ClockRead(i, '19:00', 0.99, 1) for i in range(100)]
        poor = [ClockRead(r.frame, r.text, 0.1, 1) for r in reads()]
        self.assertTrue(all(x is None for x in dense_clock(frozen, 100)))
        self.assertTrue(all(x is None for x in dense_clock(poor, 200)))

    def test_large_sampling_uncertainty_blocks_fusion_candidates(self):
        t = dense_clock(reads(stride=25), 200, max_sample_gap_s=1.1)
        b = dense_clock(reads(stride=25), 200, max_sample_gap_s=1.1)
        self.assertEqual(align_clocks(t, b, max_uncertainty_s=0.25)[80].status,
                         'timing_uncertain')

    def test_invalid_or_reordered_frame_ids_fail(self):
        with self.assertRaises(ValueError):
            dense_clock([ClockRead(5, '19:00', 0.9, 1), ClockRead(4, '19:01', 0.9, 1)], 100)

    def test_frozen_dense_input_cannot_become_a_candidate(self):
        with self.assertRaises(ValueError):
            align_clocks([ClockTime(1140, .04, 1, 0)], [ClockTime(1140, .04, 1, 0)] * 10)

    def test_three_tick_requirement_applies_to_each_piece_after_frozen_gap(self):
        readings = []
        for f in range(0, 225, 5):
            seconds = f//25 if f < 75 else (2 if f < 175 else f//25-4)
            readings.append(ClockRead(f, '19:{:02d}'.format(seconds), .95, 1))
        self.assertTrue(all(t is None for t in dense_clock(readings, 225)))

    def test_explicit_trial_cutoff_allows_moderate_progressing_clock(self):
        observations = [ClockRead(r.frame, r.text, .6, 1) for r in reads()]
        self.assertTrue(all(t is None for t in dense_clock(observations, 200)))
        self.assertIsNotNone(dense_clock(observations, 200, min_confidence=.5)[80])
        frozen = [ClockRead(i,'12:34',.6,1) for i in range(100)]
        self.assertTrue(all(t is None for t in dense_clock(frozen,100,min_confidence=.5)))

    def test_isolated_unreadable_or_low_score_sample_keeps_bounded_clock(self):
        for text, confidence in [('', 0.0), ('19:03', .2)]:
            observations = [ClockRead(r.frame, text, confidence, 1) if r.frame == 75 else r
                            for r in reads()]
            clock = dense_clock(observations, 200, min_confidence=.5)
            self.assertIsNotNone(clock[75])
            self.assertAlmostEqual(clock[75].seconds, 1143.0)
            self.assertAlmostEqual(clock[75].uncertainty_s, .22)

    def test_two_consecutive_misses_leave_gap_unresolved(self):
        observations = [ClockRead(r.frame, '', 0.0, 1) if r.frame in (75, 80) else r
                        for r in reads()]
        self.assertIsNone(dense_clock(observations, 200)[80])

    def test_contradictory_accepted_read_still_splits_clock(self):
        observations = [ClockRead(r.frame, '19:22', .99, 1) if r.frame == 75 else r
                        for r in reads()]
        self.assertIsNone(dense_clock(observations, 200)[80])
