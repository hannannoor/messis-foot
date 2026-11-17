"""Full-index synthetic exports exercise the real loaders, CLI and audit together."""
import csv
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


@unittest.skipUnless(os.environ.get('FOOTBALL_SLOW_TESTS') == '1', 'full-index synthetic integration is opt-in')
class ControlledCLIIntegration(unittest.TestCase):
    def test_cached_alignment_runs_controlled_audit_without_any_video(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for source, count in (('tactical', 199319), ('broadcast', 164488)):
                folder = root/(source+' cam')
                folder.mkdir()
                prefix = folder/('BAR-ATH_'+source)
                metadata = '<root><Team id="h"><Name>Barcelona</Name></Team><Team id="a"><Name>Atletic Club</Name></Team>'
                metadata += '<Player teamId="h"/>'*3 + '<Player teamId="a"/>'*3 + '</root>'
                Path(str(prefix)+'_atd.xml').write_text(metadata)
                players = '0.1,0.2,0;0.2,0.3,0;0.3,0.4,0;0.5,0.6,0;0.6,0.7,0;0.7,0.8,0'
                with Path(str(prefix)+'_atd.txt').open('w') as handle:
                    for i in range(count):
                        ball = 'NaN,NaN,NaN' if source == 'tactical' and 45020 <= i < 45030 else '0.1,0.2,0'
                        handle.write(str(i+1)+':'+players+':'+ball+'\n')
                with Path(str(prefix)+'_homography.csv').open('w', newline='') as handle:
                    writer = csv.writer(handle)
                    writer.writerow(['frame'] + ['h'+str(a)+str(b) for a in range(3) for b in range(3)] + ['reprojection_error','valid'])
                    writer.writerows([i,1,0,0,0,1,0,0,0,1,.2,1] for i in range(count))
            (root/'tactical cam'/'BAR-ATH_tactical_smart_tagging.xml').write_text(
                '<root><instance><start>1799.6</start><end>1802</end><code>SET PIECES</code></instance></root>')
            mapping = root/'alignment.csv'
            with mapping.open('w', newline='') as handle:
                writer = csv.writer(handle)
                writer.writerow(['tactical_frame','broadcast_frame','half','uncertainty_s','status'])
                for i in range(199319):
                    writer.writerow([i,7000+i-45000,1,.1,'clock_candidate'] if 45000 <= i < 45100 else
                                    [i,'',0,'','no_tactical_clock'])
            destination = root/'outputs'
            script = os.environ.get('FOOTBALL_STANDALONE')
            command = ([sys.executable, script, 'camera'] if script else
                       [sys.executable, '-m', 'gap_solver.multicam'])
            run = subprocess.run(command + ['fuse','--data-dir',str(root),'--alignment',str(mapping),
                                            '--audit-baseline','--out',str(destination)],
                                 text=True,capture_output=True,timeout=180)
            self.assertEqual(run.returncode, 0, run.stderr)
            report = json.loads((destination/'ensemble_report.json').read_text())
            stages = report['controlled_comparison']['stages']
            self.assertEqual(stages['published_context']['labels']['D'], 2934)
            self.assertEqual(report['missing_ball_funnel']['unresolved_missing_ball_candidates'], 10)
            self.assertEqual(report['missing_ball_funnel']['rescued'], 10)
            self.assertEqual(report['after']['missing_ball_assigned_team_frames'], 10)
            self.assertEqual(report['controlled_comparison']['comparisons']['published_context']['raw_label_changes'], 2934)
            self.assertEqual(sum(report['verification_reason_counts'].values()), 100)
            self.assertEqual(report['not_compared_frames'] + report['camera_comparison_frames'], 199319)
            self.assertFalse(report['accuracy_measured'])
            self.assertFalse(report['replay_detector_included'])
            self.assertIn('Controlled baseline comparison', run.stdout)
            with (destination/'diagnostics.csv').open(newline='') as handle:
                self.assertIn('scorer_legacy_tactical_label', csv.DictReader(handle).fieldnames)
            self.assertFalse(any(root.rglob('*.mp4')))
