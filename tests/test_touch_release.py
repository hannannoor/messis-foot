import json
from pathlib import Path
import tempfile
import unittest

HANDLING = Path(__file__).resolve().parent.parent / '.superpowers/release/target-handling.json'
CONTROL_SHA = '8d233ff132826d1c4eb96f9e43aa0c39f9a1c514cacf3f18edc673810d18a847'
CSV_SHA = '31b947d3b250b6267a7d8f0aac0c4e4eafd82a4fc873c82759806e676b1bf963'


class TouchReleaseSynthetic(unittest.TestCase):
    def test_touches_disabled_equals_candidate_labels_on_fixtures(self):
        from release_fixtures import release_fixture
        from release_runtime import load_source, predict_selected
        import touch_release as r
        with tempfile.TemporaryDirectory() as directory:
            for case in ('positive', 'invalid', 'unsupported'):
                frames, _ = load_source(*release_fixture(Path(directory) / case, case), scope='synthetic')
                self.assertEqual(r.predict_labels(frames, use_touch=False), tuple(predict_selected(frames).labels))


@unittest.skipUnless(HANDLING.exists(), 'provided-match handling file absent')
class TouchReleaseProvided(unittest.TestCase):
    def test_touches_disabled_reproduces_current_candidate_csv(self):
        import touch_release as r
        prefix = json.loads(HANDLING.read_text(encoding='utf-8'))['input_prefix']
        if not Path(prefix + '_atd.txt').exists():
            self.skipTest('inputs absent')
        with tempfile.TemporaryDirectory() as d:
            receipt = r.generate(prefix, prefix + '_smart_tagging.xml', Path(d) / 'out', use_touch=False)
        self.assertEqual(receipt['control_labels_sha256'], CONTROL_SHA)
        self.assertEqual(receipt['csv_sha256'], CSV_SHA)


if __name__ == '__main__':
    unittest.main()
