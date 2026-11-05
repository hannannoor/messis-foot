"""Generated clock histories only; no challenge images, tracking or labels."""
import io
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from gap_solver import clock_ocr

try:
    from gap_solver import clock_discovery as discovery
except ImportError:
    discovery = None


HEADER = ('level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext\n')


def word(text, x=100, y=20, width=67, height=20, confidence=95, block=1):
    return '5\t1\t{}\t1\t1\t1\t{}\t{}\t{}\t{}\t{}\t{}\n'.format(
        block, x, y, width, height, confidence, text)


def candidate(seconds, roi=(.1, .04, .1, .04)):
    return {'text': '{}:{:02d}'.format(seconds // 60, seconds % 60),
            'seconds': seconds, 'confidence': .95, 'roi': list(roi)}


def sample(frame, seconds=None, roi=(.1, .04, .1, .04)):
    return {'frame': frame, 'candidates': [] if seconds is None else [candidate(seconds, roi)]}


class ClockCandidateParsing(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(discovery, 'automatic clock discovery is missing')

    def test_finds_clock_anywhere_without_including_score(self):
        tsv = HEADER + word('22:31', x=600, y=300) + word('0-0', x=700, y=300)
        found = discovery.clock_candidates(tsv, 1000, 500)
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]['text'], '22:31')
        self.assertEqual(found[0]['seconds'], 1351)
        self.assertEqual(found[0]['roi'], [.6, .6, .067, .04])
        self.assertEqual(found[0]['confidence'], .95)

    def test_adjacent_split_clock_tokens_form_one_tight_box(self):
        tsv = HEADER + word('27', width=28) + word(':', x=130, width=6, confidence=80) + word('02', x=139, width=28)
        found = discovery.clock_candidates(tsv, 1000, 500)
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]['text'], '27:02')
        self.assertEqual(found[0]['roi'], [.1, .04, .067, .04])
        self.assertEqual(found[0]['confidence'], .8)

    def test_far_apart_or_different_line_tokens_do_not_form_clock(self):
        for suffix in (word('31', x=500), word('31', x=145, block=2)):
            with self.subTest(suffix=suffix):
                self.assertEqual(discovery.clock_candidates(HEADER + word('22:', width=40) + suffix, 1000, 500), [])

    def test_bad_confidences_boxes_and_clock_formats_are_not_detections(self):
        rows = [word('22:31', confidence='nan'), word('22:31', confidence=101),
                word('22:31', confidence=60), word('22:31', x=-1),
                word('22:31', width=0), word('22:31', x=990),
                word('22:99'), word('2231'), word('0-0')]
        for row in rows:
            with self.subTest(row=row):
                self.assertEqual(discovery.clock_candidates(HEADER + row, 1000, 500), [])

    def test_duplicate_ocr_boxes_do_not_count_as_two_independent_clocks(self):
        row = word('22:31')
        self.assertEqual(len(discovery.clock_candidates(HEADER + row + row, 1000, 500)), 1)

    def test_invalid_dimensions_or_tsv_format_raise(self):
        for width, height in ((0, 500), (1000, -1), (float('nan'), 500)):
            with self.subTest(width=width, height=height), self.assertRaises(ValueError):
                discovery.clock_candidates(HEADER, width, height)
        with self.assertRaisesRegex(ValueError, 'TSV'):
            discovery.clock_candidates('22:31', 1000, 500)

    def test_split_stoppage_clock_does_not_emit_its_suffix_as_another_clock(self):
        for width in (40, 90):
            tsv = HEADER + word('45+', width=width) + word('01:30', x=100+width+2)
            found = discovery.clock_candidates(tsv, 1000, 500)
            self.assertEqual([c['text'] for c in found], ['45+01:30'])
            self.assertEqual(found[0]['seconds'], 2790)
        tsv = HEADER + word('90', width=28) + word('+', x=130, width=10) + word('02:10', x=142)
        self.assertEqual([c['text'] for c in discovery.clock_candidates(tsv, 1000, 500)], ['90+02:10'])

    def test_weak_stoppage_prefix_does_not_leave_high_confidence_suffix(self):
        tsv = HEADER + word('45+', width=40, confidence=60) + word('01:30', x=142)
        self.assertEqual(discovery.clock_candidates(tsv, 1000, 500), [])

    def test_an_adjacent_number_does_not_extend_an_already_complete_clock(self):
        tsv = HEADER + word('1', width=10) + word('12:31', x=112)
        self.assertEqual([c['text'] for c in discovery.clock_candidates(tsv, 1000, 500)], ['12:31'])


class ClockSegmentDiscovery(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(discovery, 'automatic clock discovery is missing')

    def test_blank_prefix_then_progressing_clock_retains_original_indices(self):
        samples = [sample(0), sample(750), sample(1500, 720), sample(2250, 750), sample(3000, 780)]
        segments = discovery.clock_segments(samples, fps=25, stride=750)
        self.assertEqual(len(segments), 1)
        self.assertEqual(segments[0]['start_frame'], 1500)
        self.assertEqual(segments[0]['end_frame_exclusive'], 3001)
        self.assertEqual([r['frame'] for r in segments[0]['readings']], [1500, 2250, 3000])
        self.assertFalse(segments[0]['live_verified'])

    def test_static_clock_or_advert_time_is_not_progressing_segment(self):
        self.assertEqual(discovery.clock_segments([sample(f, 720) for f in (0, 750, 1500)], 25, 750), [])

    def test_single_missed_scan_is_supported_but_two_consecutive_misses_split(self):
        one_miss = [sample(0, 720), sample(750), sample(1500, 780), sample(2250, 810)]
        self.assertEqual(len(discovery.clock_segments(one_miss, 25, 750)), 1)
        two_misses = [sample(0, 720), sample(750), sample(1500), sample(2250, 810), sample(3000, 840), sample(3750, 870)]
        segments = discovery.clock_segments(two_misses, 25, 750)
        self.assertEqual(len(segments), 1)
        self.assertEqual(segments[0]['start_frame'], 2250)

    def test_reset_or_moving_overlay_starts_a_new_segment(self):
        first = [sample(0, 720), sample(750, 750), sample(1500, 780)]
        for suffix in ([sample(2250, 0), sample(3000, 30), sample(3750, 60)],
                       [sample(2250, 810, (.7, .4, .1, .04)), sample(3000, 840, (.7, .4, .1, .04)), sample(3750, 870, (.7, .4, .1, .04))]):
            with self.subTest(suffix=suffix):
                segments = discovery.clock_segments(first + suffix, 25, 750)
                self.assertEqual([s['start_frame'] for s in segments], [0, 2250])

    def test_two_distinct_progressing_clocks_are_both_reported(self):
        samples = [{'frame': f, 'candidates': [candidate(s), candidate(s + 600, (.7, .4, .1, .04))]}
                   for f, s in ((0, 720), (750, 750), (1500, 780))]
        segments = discovery.clock_segments(samples, 25, 750)
        self.assertEqual(len(segments), 2)
        self.assertEqual(sorted(s['readings'][0]['seconds'] for s in segments), [720, 1320])

    def test_overlapping_conflicting_clocks_are_not_silently_resolved_by_confidence(self):
        samples = [{'frame': f, 'candidates': [candidate(s), candidate(s + 1)]}
                   for f, s in ((0, 720), (750, 750), (1500, 780))]
        self.assertEqual(discovery.clock_segments(samples, 25, 750), [])

    def test_nonchronological_frames_and_invalid_settings_raise(self):
        for samples, fps, stride in (([sample(750, 750), sample(0, 720)], 25, 750),
                                     ([sample(0, 720), sample(0, 720)], 25, 750),
                                     ([], float('nan'), 750), ([], 25, 0)):
            with self.subTest(samples=samples, fps=fps, stride=stride), self.assertRaises(ValueError):
                discovery.clock_segments(samples, fps, stride)

    def test_cumulative_box_drift_cannot_become_one_stable_clock_region(self):
        samples = [sample(i*750, 720+i*30, (.1+i*.025, .04, .1, .04)) for i in range(20)]
        self.assertEqual(discovery.clock_segments(samples, 25, 750), [])


class ClockDiscoveryStream(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(discovery, 'automatic clock discovery is missing')

    def test_pgm_reads_exact_pixels_without_eating_whitespace_valued_pixels(self):
        read = getattr(discovery, 'read_pgm', None)
        self.assertIsNotNone(read, 'streamed clock samples are missing')
        stream = io.BytesIO(b'P5\n# generated\n2 2\n255\n\x0a\x20\x00\xffP5\n1 1\n255\n\x33')
        image, width, height = read(stream)
        self.assertEqual((width, height), (2, 2))
        self.assertEqual(image[-4:], b'\x0a\x20\x00\xff')
        self.assertEqual(read(stream), (b'P5\n1 1\n255\n\x33', 1, 1))
        self.assertIsNone(read(stream))

    def test_corrupt_truncated_or_unbounded_pgm_is_an_error(self):
        read = getattr(discovery, 'read_pgm', None)
        self.assertIsNotNone(read, 'streamed clock samples are missing')
        for data in (b'P2\n1 1\n255\n0', b'P5\n2 2\n255\n\x00',
                     b'P5\n0 2\n255\n', b'P5\n999999999 999999999\n255\n',
                     b'P5\n1 1\n65535\n', b'P5\n'):
            with self.subTest(data=data), self.assertRaises(ValueError):
                read(io.BytesIO(data))

    def test_invalid_scan_settings_fail_before_opening_a_video(self):
        scan = getattr(discovery, 'scan_video', None)
        self.assertIsNotNone(scan, 'whole-video clock scanner is missing')
        for kwargs in ({'stride_seconds': 0}, {'stride_seconds': float('nan')},
                       {'stride_seconds': .5}, {'min_confidence': -1}, {'min_confidence': float('nan')}):
            with self.subTest(kwargs=kwargs), self.assertRaisesRegex(ValueError, 'stride|confidence'):
                scan('this-video-does-not-exist.mp4', **kwargs)

    def test_missing_decoder_has_useful_error(self):
        iterator = getattr(discovery, 'iter_video_samples', None)
        self.assertIsNotNone(iterator, 'streamed clock samples are missing')
        with self.assertRaisesRegex(ValueError, 'Executable not found'):
            list(iterator('unused.mp4', 10, 5, ffmpeg='nonexistent-clock-discovery-ffmpeg'))

    def test_invalid_probe_dimensions_fail_at_metadata_boundary(self):
        stream = {'width': 960, 'height': 360, 'nb_frames': '75',
                  'r_frame_rate': '25/1', 'avg_frame_rate': '25/1'}
        for override in ({'width': 0}, {'height': -3}, {'width': 'nan'},
                         {'width': 100000, 'height': 100000}):
            with self.subTest(override=override), patch.object(clock_ocr, '_run',
                    return_value=json.dumps({'streams': [dict(stream, **override)]})), self.assertRaisesRegex(ValueError, 'dimensions'):
                clock_ocr.probe_video('not-opened.mp4')


@unittest.skipUnless(all(shutil.which(p) for p in ('ffmpeg', 'ffprobe', 'tesseract'))
                     and importlib.util.find_spec('PIL'),
                     'optional generated-video clock discovery needs FFmpeg, Tesseract and Pillow')
class SyntheticDiscoveryIntegration(unittest.TestCase):
    def make_pattern_video(self, root):
        video = root/'pattern.mp4'
        make = subprocess.run(['ffmpeg', '-v', 'error', '-threads', '1', '-f', 'lavfi',
                               '-i', 'testsrc2=size=128x64:rate=25:duration=3',
                               '-c:v', 'mpeg4', '-g', '1', str(video)], capture_output=True, text=True)
        self.assertEqual(make.returncode, 0, make.stderr)
        return video

    def test_damaged_packet_is_not_silently_skipped_under_original_frame_ids(self):
        self.assertIsNotNone(discovery, 'automatic clock discovery is missing')
        with tempfile.TemporaryDirectory() as directory:
            video = self.make_pattern_video(Path(directory))
            probe = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_packets',
                                    '-show_entries', 'packet=pos,size', '-of', 'json', str(video)],
                                   capture_output=True, text=True, check=True)
            packet = json.loads(probe.stdout)['packets'][5]
            with video.open('r+b') as handle:
                handle.seek(int(packet['pos']))
                handle.write(b'\0'*int(packet['size']))
            with self.assertRaises(ValueError):
                list(discovery.iter_video_samples(video, 75, 25))

    def test_full_frame_count_mismatch_is_caught_when_sparse_count_is_identical(self):
        with tempfile.TemporaryDirectory() as directory:
            video = self.make_pattern_video(Path(directory))
            with self.assertRaisesRegex(ValueError, 'frame count'):
                list(discovery.iter_video_samples(video, 74, 25))

    def test_output_path_cannot_replace_source_video_or_its_hardlink(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            video = self.make_pattern_video(root)
            before = video.read_bytes()
            alias = root/'alias.mp4'
            os.link(video, alias)
            entry = ([sys.executable, os.environ['FOOTBALL_STANDALONE'], 'camera']
                     if os.environ.get('FOOTBALL_STANDALONE') else [sys.executable, '-m', 'gap_solver.multicam'])
            for output in (video, alias):
                with self.subTest(output=output):
                    run = subprocess.run(entry + ['discover-clock', '--video', str(video), '--out', str(output)],
                                         capture_output=True, text=True, timeout=30)
                    self.assertNotEqual(run.returncode, 0)
                    self.assertIn('source video', run.stderr)
                    self.assertNotIn('Scanned', run.stdout)
                    self.assertEqual(video.read_bytes(), before)

    def test_whole_video_cli_finds_offset_clock_after_blank_prefix_without_frame_files(self):
        from PIL import Image, ImageDraw, ImageFont
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            try:
                font = ImageFont.truetype('DejaVuSansMono-Bold.ttf', 48)
            except OSError:
                font = ImageFont.load_default(size=48)
            for second in range(6):
                image = Image.new('RGB', (960, 360), 'black')
                if second:
                    draw = ImageDraw.Draw(image)
                    draw.text((500, 200), '12:{:02d}'.format(second), font=font, fill='white')
                    draw.text((730, 200), '0-0', font=font, fill='white')
                image.save(root / ('{}.png'.format(second)))
            video = root / 'generated.mp4'
            make = subprocess.run(['ffmpeg', '-v', 'error', '-framerate', '1', '-i', str(root/'%d.png'),
                                   '-r', '25', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', str(video)],
                                  capture_output=True, text=True)
            self.assertEqual(make.returncode, 0, make.stderr)
            for image in root.glob('*.png'):
                image.unlink()
            output = root / 'discovery.json'
            entry = ([sys.executable, os.environ['FOOTBALL_STANDALONE'], 'camera']
                     if os.environ.get('FOOTBALL_STANDALONE') else [sys.executable, '-m', 'gap_solver.multicam'])
            run = subprocess.run(entry + ['discover-clock', '--video', str(video), '--stride-seconds', '1',
                                          '--out', str(output)], capture_output=True, text=True, timeout=90)
            self.assertEqual(run.returncode, 0, run.stderr)
            report = json.loads(output.read_text())
            self.assertEqual(report['frame_count'], 150)
            self.assertEqual([s['frame'] for s in report['samples']], [0, 25, 50, 75, 100, 125])
            self.assertEqual(report['samples'][0]['candidates'], [])
            self.assertEqual(report['candidate_segment_count'], 1)
            segment = report['segments'][0]
            self.assertEqual(segment['start_frame'], 25)
            self.assertEqual(segment['end_frame_exclusive'], 126)
            self.assertEqual([r['text'] for r in segment['readings']], ['12:01', '12:02', '12:03', '12:04', '12:05'])
            self.assertGreater(segment['roi'][0], .5)
            self.assertFalse(report['ready_for_fusion'])
            self.assertFalse(report['live_verified'])
            self.assertFalse(report['accuracy_measured'])
            self.assertEqual(sorted(p.name for p in root.iterdir()), ['discovery.json', 'generated.mp4'])
            self.assertIn('Clock discovery samples: 6', run.stdout)
            self.assertIn('Candidate progressing-clock segments: 1', run.stdout)

    def test_blank_video_is_successful_missing_evidence_not_crop_prompt(self):
        self.assertIsNotNone(discovery, 'automatic clock discovery is missing')
        scan = getattr(discovery, 'scan_video', None)
        self.assertIsNotNone(scan, 'whole-video clock scanner is missing')
        with tempfile.TemporaryDirectory() as directory:
            video = Path(directory)/'blank.mp4'
            make = subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'color=c=black:s=320x180:r=25:d=3',
                                   '-c:v', 'libx264', '-pix_fmt', 'yuv420p', str(video)], capture_output=True, text=True)
            self.assertEqual(make.returncode, 0, make.stderr)
            report = scan(video, stride_seconds=1)
            self.assertEqual(report['sample_count'], 3)
            self.assertEqual(report['samples_with_clock_candidate'], 0)
            self.assertEqual(report['segments'], [])
