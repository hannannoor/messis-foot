import tempfile
import unittest
from pathlib import Path

from gap_solver.clock_ocr import clock_from_tsv, crop_filter, ocr_summary
from gap_solver import clock_ocr


class LocalClockOCR(unittest.TestCase):
    def test_clock_tokens_and_confidence_are_preserved(self):
        tsv = 'level\tconf\ttext\n5\t96\t19:06\n'
        self.assertEqual(clock_from_tsv(tsv), ('19:06', 0.96))
        self.assertEqual(clock_from_tsv('level\tconf\ttext\n5\t90\t27\n5\t80\t:02\n'),
                         ('27:02', 0.8))

    def test_scoreline_and_unreadable_text_do_not_become_a_clock(self):
        self.assertEqual(clock_from_tsv('level\tconf\ttext\n5\t95\t1-0\n'), ('', 0.0))

    def test_plain_text_output_is_reported_as_a_format_error(self):
        with self.assertRaises(ValueError):
            clock_from_tsv('22:31\n')

    def test_empty_ocr_with_valid_tsv_header_is_legitimate_missing_data(self):
        self.assertEqual(clock_from_tsv('level\tconf\ttext\n'), ('', 0.0))

    def test_utf8_bom_in_header_does_not_discard_every_clock(self):
        self.assertEqual(clock_from_tsv('\ufefflevel\tconf\ttext\n5\t95\t22:31\n'),
                         ('22:31', .95))

    def test_confidence_summary_includes_unreadable_crops_as_zero(self):
        from gap_solver.clock_sync import ClockRead
        reads = [ClockRead(i,'12:34',.6,1) for i in range(100)]
        reads[0] = ClockRead(0,'',0.0,1)
        report = ocr_summary(reads,.5)
        self.assertEqual(report['unreadable'],1)
        self.assertEqual(report['accepted_by_score'],99)
        self.assertAlmostEqual(report['p01_all'],.594)

    def test_p01_trial_condition_is_strictly_above_half(self):
        from gap_solver.clock_sync import ClockRead
        reads = [ClockRead(i,'12:34',.5,1) for i in range(100)]
        report = ocr_summary(reads,.5)
        self.assertFalse(report['p01_above_half'])
        self.assertEqual(report['accepted_by_score'],100)

    def test_crop_filter_preserves_original_decoded_frame_index(self):
        expression = crop_filter((0.1, 0.2, 0.2, 0.1), start=100, end=200, stride=5)
        self.assertIn('n-100', expression)
        self.assertIn('gte(n', expression)
        with self.assertRaises(ValueError):
            crop_filter((0.9, 0.1, 0.3, 0.2), 0, 100, 1)

    def test_retry_recovers_clock_without_promoting_its_score(self):
        select = getattr(clock_ocr, 'select_clock_candidate', None)
        self.assertIsNotNone(select, 'missing retry candidate selection')
        self.assertEqual(select([('primary', '', 0.0), ('unprocessed', '22:31', .66),
                                 ('thresholded', '22:31', .82)], .5),
                         ('22:31', .82, 'thresholded'))

    def test_conflicting_accepted_retry_readings_remain_unresolved(self):
        select = getattr(clock_ocr, 'select_clock_candidate', None)
        self.assertIsNotNone(select, 'missing retry candidate selection')
        self.assertEqual(select([('primary', '', 0.0), ('unprocessed', '22:31', .66),
                                 ('thresholded', '22:37', .92)], .5),
                         ('', 0.0, 'conflict'))

    def test_retry_keeps_weak_read_weak_and_all_unreadable_missing(self):
        select = getattr(clock_ocr, 'select_clock_candidate', None)
        self.assertIsNotNone(select, 'missing retry candidate selection')
        self.assertEqual(select([('primary', '22:31', .3), ('unprocessed', '22:31', .49)], .5),
                         ('22:31', .49, 'unprocessed'))
        self.assertEqual(select([('primary', '', 0), ('unprocessed', '2231', .9)], .5),
                         ('', 0.0, 'unreadable'))
