"""Optional real-executable test. Uses generated clocks, never competition images."""
import importlib.util
import csv
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from gap_solver.multicam import read_dense_clock
from gap_solver import clock_ocr


@unittest.skipUnless(all(shutil.which(p) for p in ('ffmpeg', 'ffprobe', 'tesseract'))
                     and importlib.util.find_spec('PIL'),
                     'optional OCR integration needs FFmpeg, Tesseract and Pillow')
class SyntheticOCRIntegration(unittest.TestCase):
    def test_retry_treatments_do_not_invent_a_clock_on_a_blank_crop(self):
        from PIL import Image
        retry = getattr(clock_ocr, 'read_clock_with_retries', None)
        self.assertIsNotNone(retry, 'missing local OCR retries')
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'blank.png'
            Image.new('L', (440, 200), 'white').save(path)
            self.assertEqual(retry(path, 'tactical', .5), ('', 0.0, 'unreadable', 3))

    def test_generated_video_clock_extraction_preserves_original_frames(self):
        from PIL import Image, ImageDraw, ImageFont
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            # Pillow's bundled default font also works on systems without DejaVu.
            try:
                font = ImageFont.truetype('DejaVuSansMono-Bold.ttf', 48)
            except OSError:
                font = ImageFont.load_default(size=48)
            for i in range(125):
                image = Image.new('RGB', (320, 80), 'black')
                if i != 55:  # one sampled unreadable frame must be retried, then bounded in time
                    ImageDraw.Draw(image).text((20, 8), '19:{:02d}'.format(i//25), font=font, fill='white')
                image.save(root / ('{:04d}.png'.format(i)))
            video = root / 'clock.mp4'
            generated = subprocess.run(['ffmpeg', '-v', 'error', '-framerate', '25',
                '-i', str(root/'%04d.png'), '-c:v', 'libx264', '-pix_fmt', 'yuv420p', str(video)],
                capture_output=True, text=True)
            self.assertEqual(generated.returncode, 0, generated.stderr)
            check = subprocess.run([sys.executable, '-m', 'gap_solver.multicam', 'ocr-check',
                '--image', str(root/'0000.png'), '--source', 'tactical'], capture_output=True, text=True)
            self.assertEqual(check.returncode, 0, check.stderr)
            self.assertIn('Preprocessed:', check.stdout)
            output = root / 'clock.csv'
            run = subprocess.run([sys.executable, '-m', 'gap_solver.multicam', 'clock',
                '--video', str(video), '--source', 'tactical', '--half', '1',
                '--start-frame', '25', '--end-frame', '125', '--stride', '5',
                '--roi', '0,0,1,1', '--min-confidence', '0.5', '--out', str(output)], capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertIn('accepted at cutoff 0.500', run.stdout)
            self.assertIn('First-percentile confidence > 0.5:', run.stdout)
            self.assertIn('OCR retries: 1; recovered at cutoff: 0; conflicting retries: 0', run.stdout)
            with Path(str(output)+'.reads.csv').open(newline='') as handle:
                by_frame = {int(row['frame']):row for row in csv.DictReader(handle)}
            self.assertEqual(by_frame[55]['ocr_attempts'], '3')
            self.assertEqual(by_frame[55]['ocr_method'], 'unreadable')
            self.assertEqual(by_frame[80]['ocr_attempts'], '1')
            clocks = read_dense_clock(output)
            self.assertEqual(len(clocks), 125)
            self.assertTrue(all(c is None for c in clocks[:25]))
            self.assertIsNotNone(clocks[80])
            self.assertIsNotNone(clocks[55])
            self.assertAlmostEqual(clocks[80].seconds, 1143.3, delta=.2)
