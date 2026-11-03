import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from gap_solver.multicam import read_dense_clock, write_dense_clock, load_scenes, read_alignment
from gap_solver.clock_sync import Alignment, ClockTime
from gap_solver.core import Frame
from gap_solver.fusion import Scene
from gap_solver import multicam


class MultiCameraCLI(unittest.TestCase):
    def test_fusion_reports_missing_ball_opportunities_and_rescues(self):
        frames = [Frame()]*40
        other = [Frame(ball_x=40, ball_y=30, home_distance=.5, away_distance=8)]*40
        tactical_scene = Scene(((10,10),(20,15),(30,20),(40,25)),
                               ((12,40),(22,45),(32,50),(42,55)), None, True, .2)
        from dataclasses import replace
        broadcast_scene = replace(tactical_scene, ball=(40,30))
        mapping = [Alignment(i, .1, 'clock_candidate') for i in range(40)]
        decisions, rows, report = multicam.ensemble(frames, other, [tactical_scene]*40,
                                                  [broadcast_scene]*40, mapping)
        self.assertIn('missing_ball_funnel', report)
        funnel = report['missing_ball_funnel']
        self.assertEqual(funnel['unresolved_missing_ball_candidates'], 40)
        self.assertEqual(funnel['broadcast_direct_control'], 40)
        self.assertEqual(funnel['rescued'], 40)
        self.assertEqual(report['verification_reason_counts'], {'geometry_consistent':40})
        self.assertEqual(report['camera_comparison_frames'], 40)

    def test_restart_phase_edges_are_shared_with_broadcast_control(self):
        frames = [Frame(restart_hint=bool((i//5)%2)) for i in range(40)]
        other = [Frame(ball_x=40, ball_y=30, home_distance=.5, away_distance=8)]*40
        geometry = Scene(((10,10),(20,15),(30,20),(40,25)),
                         ((12,40),(22,45),(32,50),(42,55)), None, True, .2)
        mapping = [Alignment(i, .1, 'clock_candidate') for i in range(40)]
        decisions, rows, report = multicam.ensemble(frames, other, [geometry]*40, [geometry]*40, mapping)
        self.assertTrue(all(d.label == 'X' for d in decisions))
        self.assertEqual(report['broadcast_rescued_frames'], 0)

    def test_zero_missing_ball_opportunities_are_reported_as_zero(self):
        frames = [Frame(ball_x=40, ball_y=30, home_distance=.5, away_distance=8)]*40
        geometry = Scene(((10,10),(20,15),(30,20),(40,25)),
                         ((12,40),(22,45),(32,50),(42,55)), (40,30), True, .2)
        mapping = [Alignment(i, .1, 'clock_candidate') for i in range(40)]
        _, _, report = multicam.ensemble(frames, frames, [geometry]*40, [geometry]*40, mapping)
        self.assertIn('missing_ball_funnel', report)
        self.assertEqual(report['missing_ball_funnel']['unresolved_missing_ball_candidates'], 0)
        self.assertEqual(report['missing_ball_funnel']['rescued'], 0)

    def test_source_files_are_found_in_existing_camera_folders_with_spaces(self):
        resolve = getattr(multicam, 'resolve_source_prefix', None)
        self.assertIsNotNone(resolve, 'missing source-folder support')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            camera = root/'tactical cam'
            camera.mkdir()
            for suffix in ('_atd.xml', '_atd.txt', '_homography.csv'):
                (camera/('BAR-ATH_tactical'+suffix)).touch()
            self.assertEqual(resolve(root, 'tactical'), camera/'BAR-ATH_tactical')

    def test_source_files_remain_compatible_with_standard_folders(self):
        resolve = getattr(multicam, 'resolve_source_prefix', None)
        self.assertIsNotNone(resolve, 'missing source-folder support')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            camera = root/'broadcast'
            camera.mkdir()
            for suffix in ('_atd.xml', '_atd.txt', '_homography.csv'):
                (camera/('BAR-ATH_broadcast'+suffix)).touch()
            self.assertEqual(resolve(root, 'broadcast'), camera/'BAR-ATH_broadcast')

    def test_explicit_source_folder_resolves_duplicates_without_copying(self):
        resolve = getattr(multicam, 'resolve_source_prefix', None)
        self.assertIsNotNone(resolve, 'missing source-folder support')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ('tactical', 'tactical cam'):
                camera = root/name
                camera.mkdir()
                for suffix in ('_atd.xml', '_atd.txt', '_homography.csv'):
                    (camera/('BAR-ATH_tactical'+suffix)).touch()
            with self.assertRaisesRegex(ValueError, 'Multiple'):
                resolve(root, 'tactical')
            self.assertEqual(resolve(root, 'tactical', root/'tactical cam'),
                             root/'tactical cam'/'BAR-ATH_tactical')

    def test_incomplete_source_folder_names_the_missing_file(self):
        resolve = getattr(multicam, 'resolve_source_prefix', None)
        self.assertIsNotNone(resolve, 'missing source-folder support')
        with tempfile.TemporaryDirectory() as directory:
            camera = Path(directory)/'broadcast cam'
            camera.mkdir()
            for suffix in ('_atd.xml', '_atd.txt'):
                (camera/('BAR-ATH_broadcast'+suffix)).touch()
            with self.assertRaisesRegex(ValueError, 'BAR-ATH_broadcast_homography.csv'):
                resolve(Path(directory), 'broadcast', camera)

    def test_dense_clock_roundtrip_keeps_unknown_frames(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'clock.csv'
            clocks = [None, ClockTime(1146.12, 0.04, 1, 2)]
            write_dense_clock(path, clocks)
            self.assertEqual(read_dense_clock(path), clocks)

    def test_demo_rescues_only_verified_secondary_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run([sys.executable, '-m', 'gap_solver.multicam', 'demo',
                                     '--out', directory], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads((Path(directory) / 'ensemble_report.json').read_text())
            self.assertGreater(report['broadcast_rescued_frames'], 0)
            self.assertGreater(report['after']['labels']['X'], 0)
            self.assertFalse(report['accuracy_measured'])

    def test_scene_loader_uses_team_membership_and_homography_validity(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'meta.xml').write_text('<root><Team id="h"/><Team id="a"/><Player teamId="h"/><Player teamId="a"/></root>')
            (root / 'raw.txt').write_text('1:0.1,0.2,0;0.8,0.9,0:0.5,0.5,0\n')
            with (root / 'hom.csv').open('w', newline='') as handle:
                writer = csv.writer(handle)
                writer.writerow(['frame'] + ['h'+str(a)+str(b) for a in range(3) for b in range(3)] + ['reprojection_error', 'valid'])
                writer.writerow([0] + [1,0,0,0,1,0,0,0,1] + [0.2, 1])
            scenes = load_scenes(root/'meta.xml', root/'raw.txt', root/'hom.csv', 1)
            self.assertAlmostEqual(scenes[0].home[0][0], 10.53)
            self.assertTrue(scenes[0].homography_valid)
            # A finite matrix is not necessarily an invertible homography.
            with (root / 'hom.csv').open('w', newline='') as handle:
                writer = csv.writer(handle)
                writer.writerow(['frame'] + ['h'+str(a)+str(b) for a in range(3) for b in range(3)] + ['reprojection_error', 'valid'])
                writer.writerow([0] + [1]*9 + [0.2, 1])
            self.assertFalse(load_scenes(root/'meta.xml', root/'raw.txt', root/'hom.csv', 1)[0].homography_valid)

    def test_cyclic_or_collapsed_frame_mapping_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'alignment.csv'
            for targets in ([i % 6 for i in range(30)], [0]*30, [i//2 for i in range(30)]):
                with path.open('w', newline='') as handle:
                    writer = csv.writer(handle)
                    writer.writerow(['tactical_frame','broadcast_frame','half','uncertainty_s','status'])
                    writer.writerows((i,j,1,.02,'clock_candidate') for i,j in enumerate(targets))
                with self.assertRaises(ValueError):
                    read_alignment(path, 30, 30)
