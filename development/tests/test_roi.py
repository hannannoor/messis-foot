import json
import shutil
import struct
import subprocess
import tempfile
import unittest
from pathlib import Path

from gap_solver.roi import normalise_box, load_roi, extract_reference_frame


class ClockSelection(unittest.TestCase):
    def test_display_selection_maps_back_to_original_video_coordinates(self):
        roi = normalise_box((50, 10, 100, 25), width=1920, height=1080, display_scale=2)
        self.assertAlmostEqual(roi[0], 100/1920)
        self.assertAlmostEqual(roi[1], 20/1080)
        self.assertAlmostEqual(roi[2], 100/1920)
        self.assertAlmostEqual(roi[3], 30/1080)

    def test_reverse_drag_and_outside_coordinates_are_clamped(self):
        roi = normalise_box((100, 25, -10, -10), 1920, 1080, 2)
        self.assertEqual(roi[:2], (0, 0))
        self.assertAlmostEqual(roi[2], 200/1920)
        self.assertAlmostEqual(roi[3], 50/1080)

    def test_tiny_box_is_rejected(self):
        with self.assertRaises(ValueError):
            normalise_box((10,10,11,11), 1920, 1080, 2)

    def test_saved_roi_must_match_camera_source(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d)/'roi.json'
            path.write_text(json.dumps({'source':'tactical','roi':[.1,.02,.06,.05]}))
            self.assertEqual(load_roi(path,'tactical'), (.1,.02,.06,.05))
            with self.assertRaises(ValueError):
                load_roi(path,'broadcast')

    @unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'), 'needs FFmpeg')
    def test_local_frame_extraction_produces_original_resolution_png(self):
        with tempfile.TemporaryDirectory() as d:
            video, output = Path(d)/'test.mp4', Path(d)/'frame.png'
            result = subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i',
                'color=c=white:s=320x180:r=25','-frames:v','50',str(video)],
                capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            extract_reference_frame(video, 25, output)
            data=output.read_bytes()
            self.assertEqual(data[:8], b'\x89PNG\r\n\x1a\n')
            self.assertEqual(struct.unpack('>II', data[16:24]), (320,180))
