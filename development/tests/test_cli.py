import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class CommandLine(unittest.TestCase):
    def test_demo_preserves_ambiguity_and_reports_coverage_separately(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run([sys.executable, '-m', 'gap_solver', 'demo', '--out', directory],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads((Path(directory) / 'report.json').read_text())
            self.assertFalse(report['accuracy_measured'])
            self.assertGreater(report['inferred_frames'], 0)
            self.assertGreater(report['labels']['X'], 0)
            comparison = json.loads((Path(directory) / 'demo_comparison.json').read_text())
            self.assertGreater(comparison['before']['labels']['X'], comparison['after']['labels']['X'])

    def test_missing_match_assets_error_is_actionable(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run([sys.executable, '-m', 'gap_solver', 'match', '--data-dir', directory],
                                    capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('tactical', result.stderr)

    def test_invalid_config_rejects_unknown_keys(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'config.json'
            path.write_text('{"invented_setting": 1}')
            result = subprocess.run([sys.executable, '-m', 'gap_solver', 'demo', '--config', str(path)],
                                    capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('invented_setting', result.stderr)
