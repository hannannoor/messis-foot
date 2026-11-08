import csv
import json
from pathlib import Path
import tempfile
import shutil
from collections import Counter
from unittest.mock import patch
import unittest
import numpy as np

try:
    from gap_solver.skillcorner import load_skillcorner,save_motion_cache,load_motion_cache
except ImportError:
    load_skillcorner=save_motion_cache=load_motion_cache=None


def write_source(root,phases=None,mutate=None):
    metadata=dict(id=7,home_team=dict(id=1),away_team=dict(id=2),pitch_length=105.3,pitch_width=68,
                  players=[dict(id=i,team_id=1 if i<103 else 2) for i in range(100,106)])
    meta=root/'match.json';meta.write_text(json.dumps(metadata))
    rows=[]
    for n in range(4):
        rows.append(dict(frame=n,timestamp='00:00:00.{:02d}'.format(n*10),period=1,
            ball_data=dict(x=n*10.,y=0.,is_detected=n!=2),
            player_data=[dict(player_id=i,x=-10. if i<103 else 10.,y=float(i%3),is_detected=True) for i in range(100,106)],
            possession=dict(group='home team',player_id=100)))
    if mutate:mutate(rows)
    tracking=root/'tracking.jsonl';tracking.write_text(''.join(json.dumps(r)+'\n' for r in rows))
    source=root/'phases.csv'
    with source.open('w',newline='') as handle:
        writer=csv.DictWriter(handle,fieldnames=['frame_start','frame_end','period','team_in_possession_id'])
        writer.writeheader();writer.writerows(phases if phases is not None else [dict(frame_start=1,frame_end=3,period=1,team_in_possession_id=1)])
    return meta,tracking,source


class SkillCornerContract(unittest.TestCase):
    def ready(self):self.assertIsNotNone(load_skillcorner,'independent-provider adapter is missing')

    def test_half_open_references_preserve_unknown_outside_phases(self):
        self.ready()
        with tempfile.TemporaryDirectory() as d:
            data=load_skillcorner(*write_source(Path(d)))
            self.assertEqual(len(data.frames()),10)
            np.testing.assert_array_equal(data.reference,[3,3,3,0,0,0,0,0,3,3])
            self.assertFalse((data.reference==2).any())

    def test_no_coordinate_interpolation_across_missing_detection(self):
        self.ready()
        with tempfile.TemporaryDirectory() as d:
            frames=load_skillcorner(*write_source(Path(d))).frames()
            self.assertAlmostEqual(frames[1].ball_x,56.65)
            self.assertFalse(frames[4].ball_observed)
            self.assertFalse(frames[5].ball_observed)
            self.assertTrue(frames[8].ball_observed,'isolated native observation must survive nearest-grid mapping')

    def test_available_position_ablation_is_not_called_detected(self):
        self.ready()
        with tempfile.TemporaryDirectory() as d:
            paths=write_source(Path(d))
            observed=load_skillcorner(*paths).frames()
            available=load_skillcorner(*paths,detected_only=False)
            self.assertFalse(observed[5].ball_observed)
            self.assertTrue(available.frames()[5].ball_observed)
            self.assertEqual(available.notes['position_regime'],'available_including_extrapolation')

    def test_reference_fields_do_not_change_prediction_records(self):
        self.ready()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);a=root/'a';b=root/'b';a.mkdir();b.mkdir()
            before=load_skillcorner(*write_source(a))
            after=load_skillcorner(*write_source(b,phases=[dict(frame_start=1,frame_end=3,period=1,team_in_possession_id=2)],
                mutate=lambda rows:[row.update(possession=dict(group='away team',player_id=105)) for row in rows]))
            self.assertEqual(before.frames(),after.frames())
            self.assertFalse(np.array_equal(before.reference,after.reference))

    def test_removing_all_phases_does_not_change_nontrivial_decoded_predictions(self):
        from gap_solver.temporal import infer_temporal
        from gap_solver.core import Decision
        from test_temporal import stump
        def extend(rows):
            template=rows[0];rows.clear()
            for n in range(100):
                row=json.loads(json.dumps(template));row.update(frame=n,timestamp='00:00:{:02d}.{:02d}'.format(n//10,n%10*10))
                row['ball_data'].update(x=-10.,is_detected=not 20<=n<30)
                rows.append(row)
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);a=root/'a';b=root/'b';a.mkdir();b.mkdir()
            first=load_skillcorner(*write_source(a,phases=[dict(frame_start=1,frame_end=99,period=1,team_in_possession_id=1)],mutate=extend))
            second=load_skillcorner(*write_source(b,phases=[],mutate=extend))
            base=[Decision('X' if 50<=i<75 else 'H') for i in range(250)]
            artifact=dict(model=stump(),policy=dict(confidence=.9,max_gap_s=5.),temperature=1.,transition_cost=5.)
            before=infer_temporal(first.frames(),artifact,base)
            after=infer_temporal(second.frames(),artifact,base)
            self.assertNotEqual(first.reference.tolist(),second.reference.tolist())
            self.assertEqual(before,after)
            self.assertTrue(any(a.label!='X' and b.label=='X' for a,b in zip(before,base)))

    def test_conflicting_phase_overlap_remains_unknown(self):
        self.ready()
        with tempfile.TemporaryDirectory() as d:
            phases=[dict(frame_start=1,frame_end=3,period=1,team_in_possession_id=1),
                    dict(frame_start=2,frame_end=3,period=1,team_in_possession_id=2)]
            data=load_skillcorner(*write_source(Path(d),phases))
            np.testing.assert_array_equal(data.reference[5:8],[3,3,3])

    def test_duplicate_native_frames_and_bad_clocks_are_rejected(self):
        self.ready()
        for mutation in (lambda rows:rows[2].update(frame=1),lambda rows:rows[2].update(timestamp='00:00:09.00')):
            with tempfile.TemporaryDirectory() as d:
                with self.assertRaises(ValueError):load_skillcorner(*write_source(Path(d),mutate=mutation))

    def test_feature_reference_cache_is_separate_and_lossless(self):
        self.ready()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);data=load_skillcorner(*write_source(root));prefix=root/'cached'
            save_motion_cache(data,prefix)
            with np.load(str(prefix)+'.features.npz',allow_pickle=False) as features:
                self.assertNotIn('reference',features.files)
                self.assertNotIn('possession',features.files)
            restored=load_motion_cache(prefix)
            self.assertEqual(restored.frames(),data.frames())
            np.testing.assert_array_equal(restored.reference,data.reference)

    def test_phase_spilling_across_a_period_is_quarantined_without_changing_features(self):
        self.ready()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);a=root/'a';b=root/'b';a.mkdir();b.mkdir()
            clean=load_skillcorner(*write_source(a))
            corrupt=load_skillcorner(*write_source(b,phases=[dict(frame_start=1,frame_end=3,period=2,team_in_possession_id=1)]))
            self.assertEqual(clean.frames(),corrupt.frames())
            self.assertTrue((corrupt.reference==3).all())
            self.assertEqual(corrupt.notes['phase_period_conflict_native_frames'],2)

    def test_stale_adapter_cache_cannot_be_used_silently(self):
        self.ready()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);data=load_skillcorner(*write_source(root));prefix=root/'cached'
            save_motion_cache(data,prefix)
            path=Path(str(prefix)+'.metadata.json');meta=json.loads(path.read_text())
            meta.setdefault('adapter_sources',{})['skillcorner.py']='0'*64
            path.write_text(json.dumps(meta))
            with self.assertRaises(ValueError):load_motion_cache(prefix)

    def test_odd_native_tick_blend_is_not_mislabelled_as_a_native_detection(self):
        self.ready()
        with tempfile.TemporaryDirectory() as d:
            frames=load_skillcorner(*write_source(Path(d),mutate=lambda rows:rows[2]['ball_data'].update(is_detected=True))).frames()
            self.assertFalse(frames[3].ball_native_observation)
            self.assertEqual(getattr(frames[3],'ball_provenance',None),'interpolated_detected')
            self.assertTrue(frames[3].ball_interpolated)
            self.assertIsNone(frames[3].ball_sample_time_s)
            self.assertTrue(frames[5].ball_native_observation)
            self.assertAlmostEqual(frames[5].ball_sample_time_s,.2)

    def test_isolated_odd_native_tick_has_its_own_ball_source_time(self):
        self.ready()
        with tempfile.TemporaryDirectory() as d:
            data=load_skillcorner(*write_source(Path(d)));frame=data.frames()[3]
            self.assertTrue(frame.ball_native_observation)
            self.assertFalse(getattr(frame,'ball_interpolated',True))
            self.assertEqual(frame.ball_provenance,'snapped_detected')
            self.assertAlmostEqual(frame.ball_sample_time_s,.1)
            self.assertAlmostEqual(frame.ball_x,62.65)
            self.assertEqual(len(data.native_ball_available),4)
            np.testing.assert_array_equal(data.native_ball_available,[True,True,False,True])

    def test_mixed_cache_generations_or_regimes_are_rejected(self):
        self.ready()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);paths=write_source(root);a=root/'detected';b=root/'available'
            save_motion_cache(load_skillcorner(*paths),a)
            save_motion_cache(load_skillcorner(*paths,detected_only=False),b)
            shutil.copyfile(str(b)+'.features.npz',str(a)+'.features.npz')
            with self.assertRaises(ValueError):load_motion_cache(a)

    def test_phase_clock_disagreement_is_reported_and_quarantined(self):
        self.ready()
        with tempfile.TemporaryDirectory() as d:
            paths=write_source(Path(d))
            paths[2].write_text('frame_start,frame_end,period,team_in_possession_id,time_start,time_end,duration\n2,4,1,1,00:00.1,00:00.3,0.2\n')
            data=load_skillcorner(*paths)
            self.assertTrue((data.reference==3).all())
            self.assertEqual(data.notes['phase_reconciliation']['clock_disagreement_intervals'],1)

    def test_cache_columns_are_not_reinflated_once_per_record(self):
        self.ready()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);data=load_skillcorner(*write_source(root));prefix=root/'cached'
            save_motion_cache(data,prefix)
            with np.load(str(prefix)+'.features.npz',allow_pickle=False) as archive:archive_type=type(archive)
            original=archive_type.__getitem__;reads=Counter()
            def read_real_array(archive,key):
                reads[(id(archive),key)]+=1
                return original(archive,key)
            # Observe real decompression, without replacing arrays or their I/O.
            with patch.object(archive_type,'__getitem__',read_real_array):restored=load_motion_cache(prefix)
            self.assertEqual(restored.frames(),data.frames())
            self.assertLessEqual(max(reads.values()),2,'compressed columns must be materialized independently of frame count')

