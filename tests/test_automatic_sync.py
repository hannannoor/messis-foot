import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from gap_solver.clock_discovery import iter_video_samples,read_pgm

try:
    from gap_solver import automatic_sync as automatic
except ImportError:
    automatic = None


def report(start, seconds, half_shift=0):
    readings = [dict(frame=start+i*25, text='{:02d}:{:02d}'.format((seconds+i)//60, (seconds+i)%60),
                     seconds=seconds+i, confidence=.95, roi=[.3,.3,.2,.15]) for i in range(5)]
    return dict(schema_version=1, frame_count=300, fps=25., sample_stride_frames=25,
                segments=[dict(start_frame=start, end_frame_exclusive=start+101,
                               roi=[.3,.3,.2,.15], readings=readings)],
                settings=dict(min_confidence=.7))


class AutomaticPlanning(unittest.TestCase):
    def module(self):
        self.assertIsNotNone(automatic, 'automatic dense synchronization is missing')
        return automatic

    def test_window_plan_keeps_independent_camera_frames_and_published_halves(self):
        jobs, audit = self.module().plan_windows(report(50,720), report(125,720), [(1,0,299)])
        self.assertEqual([(j['start'],j['end'],j['half']) for j in jobs['tactical']], [(50,151,1)])
        self.assertEqual([(j['start'],j['end'],j['half']) for j in jobs['broadcast']], [(125,226,1)])
        self.assertFalse(audit['live_verified'])

    def test_overlap_between_halves_is_not_resolved_by_clock_alone(self):
        tactical=report(0,2900)
        other=report(175,2900)['segments'][0]
        tactical['segments'].append(other)
        jobs,audit=self.module().plan_windows(tactical,report(75,2900),[(1,0,149),(2,150,299)])
        self.assertEqual(jobs, {'tactical':[], 'broadcast':[]})
        self.assertEqual(audit['ambiguous_broadcast_segments'],1)

    def test_half_boundary_crossing_is_rejected(self):
        jobs,audit=self.module().plan_windows(report(75,720),report(50,720),[(1,0,124),(2,125,299)])
        self.assertEqual(jobs['broadcast'],[])

    def test_explicit_first_half_added_time_cannot_be_assigned_to_second_half(self):
        b=report(75,2900)
        for i,r in enumerate(b['segments'][0]['readings']):
            r['text']='45+03:{:02d}'.format(20+i)
        jobs,audit=self.module().plan_windows(report(175,2900),b,[(2,150,299)])
        self.assertEqual(jobs['broadcast'],[])

    def test_missing_first_half_sparse_coverage_does_not_prove_second_half(self):
        jobs,audit=self.module().plan_windows(report(175,2900),report(75,2900),[(2,150,299)])
        self.assertEqual(jobs['broadcast'],[])
        self.assertEqual(audit['ambiguous_broadcast_segments'],1)

    def test_discovery_with_nan_box_or_disordered_readings_is_rejected(self):
        module=self.module()
        for change in ('box','order','bounds','confidence'):
            t=report(50,720)
            if change=='box': t['segments'][0]['roi'][0]=float('nan')
            elif change=='order': t['segments'][0]['readings'].reverse()
            elif change=='bounds': t['segments'][0]['end_frame_exclusive']=301
            else: t['segments'][0]['readings'][1]['confidence']=float('nan')
            with self.subTest(change=change),self.assertRaises(ValueError):
                module.plan_windows(t,report(125,720),[(1,0,299)])

    def test_conflicting_overlapping_clock_regions_are_not_selected(self):
        t=report(50,720)
        alternate=json.loads(json.dumps(t['segments'][0]))
        alternate['roi']=[.6,.3,.2,.15]
        for r in alternate['readings']:
            r['roi']=list(alternate['roi'])
        t['segments'].append(alternate)
        jobs,audit=self.module().plan_windows(t,report(125,720),[(1,0,299)])
        self.assertEqual(jobs['tactical'],[])
        self.assertEqual(jobs['broadcast'],[])

    def test_padding_stays_in_bounds_and_adds_room_for_full_clock(self):
        roi=self.module().padded_roi([.01,.01,.1,.03])
        self.assertEqual(roi[0],0)
        self.assertEqual(roi[1],0)
        self.assertGreater(roi[2],.1)
        self.assertLessEqual(roi[0]+roi[2],1)

    def test_unrelated_reading_boxes_and_unsupported_sparse_gaps_are_rejected(self):
        for change in ('boxes','gaps'):
            t=report(50,720)
            if change=='boxes':
                for r in t['segments'][0]['readings']:
                    r['roi']=[.8,.8,.1,.1]
            else:
                t['sample_stride_frames']=5
            with self.subTest(change=change),self.assertRaises(ValueError):
                self.module().plan_windows(t,report(125,720),[(1,0,299)])

    def test_each_job_ocr_receives_only_its_discovered_clock_region(self):
        module=self.module()
        pixels=bytes([10]*90+[200]*90)*80
        pgm=b'P5\n180 80\n255\n'+pixels
        jobs=[dict(start=0,end=1,half=1,roi=[.1,.3,.15,.1]),
              dict(start=5,end=6,half=1,roi=[.65,.3,.15,.1])]
        seen=[]
        def read(image,executable,*args):
            result,width,height=read_pgm(io.BytesIO(image))
            seen.append((width,set(result.split(b'\n',3)[3])))
            return '12:00',.95,'primary',1
        samples=(s for s in [(0,pgm,180,80),(5,pgm,180,80)])
        with patch.object(module,'iter_video_samples',return_value=samples),patch.object(module,'_read_image',side_effect=read):
            module._camera_reads('synthetic.mp4',{'frame_count':10},jobs,'tactical','ffmpeg','tesseract')
        self.assertEqual(len(seen),2)
        self.assertTrue(all(width<90 for width,_ in seen),seen)
        self.assertEqual({frozenset(values) for _,values in seen},{frozenset([10]),frozenset([200])})

    def test_automatic_ocr_uses_existing_fixed_retry_conflict_policy(self):
        module=self.module()
        self.assertIsNotNone(getattr(module,'_ocr_pgm',None),'automatic route is missing existing OCR treatment parity')
        image=b'P5\n2 2\n255\n'+bytes([0,60,170,255])
        with patch.object(module,'_ocr_pgm',side_effect=[('12:00',.4),('12:00',.95),('12:01',.95)]):
            self.assertEqual(module._read_image(image,'tesseract','tactical'),('',0.0,'conflict',3))

    def test_dense_merge_does_not_reuse_segments_after_missing_gaps(self):
        from gap_solver.clock_sync import ClockRead, validate_timeline
        batches=[]
        for start in [0,150]:
            batches.append([ClockRead(i,'00:{:02d}'.format((i-start)//25),.95,1)
                            for i in range(start,start+125,5)])
        timeline=self.module().merge_dense_reads(batches,300)
        validate_timeline(timeline)
        self.assertIsNotNone(timeline[60])
        self.assertIsNone(timeline[140])
        self.assertIsNotNone(timeline[210])
        self.assertNotEqual(timeline[60].segment,timeline[210].segment)

    def test_output_cannot_alias_video_or_discovery(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'alignment.csv'
            p.write_text('input')
            with self.assertRaisesRegex(ValueError,'input'):
                self.module().protect_outputs(Path(d),[p])
            self.assertEqual(p.read_text(),'input')

    def test_existing_unowned_output_folder_cannot_be_overwritten(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'alignment.csv'
            p.write_text('historical pilot')
            with self.assertRaisesRegex(ValueError,'dedicated|owned'):
                self.module().protect_outputs(Path(d),[])
            self.assertEqual(p.read_text(),'historical pilot')

    def test_same_video_cannot_masquerade_as_two_camera_inputs(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            video=root/'one.mp4'
            video.write_bytes(b'synthetic')
            with self.assertRaisesRegex(ValueError,'different'):
                try:
                    self.module().automatic_sync(video,video,root/'a.json',root/'b.json',root/'out')
                except FileNotFoundError as exc:
                    self.fail('camera identity was not checked before opening discovery: '+str(exc))

    def test_owned_output_directory_with_unrelated_files_is_preserved(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root/'sync-report.json').write_text(json.dumps({'schema_version':1,'method':'automatic_discovery_bounded_dense_ocr'}))
            (root/'notes.txt').write_text('user notes')
            with self.assertRaisesRegex(ValueError,'dedicated|owned'):
                self.module().protect_outputs(root,[])

    def test_publication_failure_preserves_the_previous_complete_generation(self):
        module=self.module()
        publish=getattr(module,'publish_outputs',None)
        self.assertIsNotNone(publish,'directory generation publication is missing')
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            stage,dest=root/'stage',root/'output'
            stage.mkdir();dest.mkdir()
            for name in module.OUTPUT_NAMES:
                (stage/name).write_text('new '+name)
                (dest/name).write_text('old '+name)
            replace=os.replace
            def fail_publication(source,target):
                if Path(source)==stage:
                    raise PermissionError('synthetic locked destination')
                return replace(source,target)
            with patch.object(module.os,'replace',side_effect=fail_publication),self.assertRaises(PermissionError):
                publish(stage,dest)
            self.assertTrue(all((dest/name).read_text()=='old '+name for name in module.OUTPUT_NAMES))

    def test_cli_exposes_automatic_command(self):
        run=subprocess.run([sys.executable,'-m','gap_solver.multicam','auto-sync','--help'],capture_output=True,text=True)
        self.assertEqual(run.returncode,0,run.stderr)
        self.assertIn('--tactical-discovery',run.stdout)
        self.assertIn('--broadcast-discovery',run.stdout)

    def test_failed_camera_run_does_not_mix_new_maps_with_previous_report(self):
        module=self.module()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            output=root/'results'
            output.mkdir()
            previous=output/'tactical-clock.csv'
            previous.write_text('previous complete run')
            (output/'sync-report.json').write_text(json.dumps({'schema_version':1,'method':'automatic_discovery_bounded_dense_ocr'}))
            t,b=report(12000,720),report(125,720)
            t['frame_count']=199319
            tp,bp=root/'tactical.json',root/'broadcast.json'
            tp.write_text(json.dumps(t)); bp.write_text(json.dumps(b))
            with patch.object(module,'probe_video',side_effect=[(199319,25),(300,25)]), \
                 patch.object(module,'_camera_reads',side_effect=[[],ValueError('synthetic camera failure')]):
                with self.assertRaisesRegex(ValueError,'synthetic camera failure'):
                    module.automatic_sync(root/'tactical.mp4',root/'broadcast.mp4',tp,bp,output)
            self.assertEqual(previous.read_text(),'previous complete run')


@unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'),'needs local FFmpeg')
class SelectiveDecoder(unittest.TestCase):
    def test_in_memory_preprocessing_matches_existing_ffmpeg_recipe_exactly(self):
        from gap_solver import clock_ocr
        self.assertIsNotNone(automatic,'automatic synchronization is missing')
        function=getattr(automatic,'_preprocess_pgm',None)
        self.assertIsNotNone(function,'existing OCR preprocessing parity is missing')
        image=b'P5\n4 4\n255\n'+bytes(range(0,256,16))
        for source in ('tactical','broadcast'):
            run=subprocess.run(['ffmpeg','-v','error','-f','image2pipe','-i','pipe:0','-vf',
                                clock_ocr.preprocessing_filter(source),'-frames:v','1','-c:v','pgm',
                                '-f','image2pipe','pipe:1'],input=image,capture_output=True,check=True)
            self.assertEqual(function(image,source),read_pgm(io.BytesIO(run.stdout))[0])

    def test_decoder_without_any_forward_progress_still_times_out(self):
        from gap_solver import clock_discovery
        popen=subprocess.Popen
        def stalled_decoder(*args,**kwargs):
            return popen([sys.executable,'-c','import time; time.sleep(10)'],
                         stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        with patch.object(clock_discovery.subprocess,'Popen',side_effect=stalled_decoder):
            with self.assertRaisesRegex(ValueError,'stalled'):
                list(iter_video_samples('synthetic.mp4',75,5,stall_timeout_s=.15))

    def test_long_unselected_tail_is_not_a_stall_while_original_frames_keep_decoding(self):
        with tempfile.TemporaryDirectory() as d:
            video=Path(d)/'tail.mp4'
            subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','testsrc2=size=640x360:rate=25:duration=20',
                            '-c:v','mpeg4',str(video)],check=True,capture_output=True)
            try:
                samples=list(iter_video_samples(video,500,5,windows=[(0,1)],roi=(.25,.25,.5,.5),
                                                stall_timeout_s=.25))
            except TypeError as exc:
                self.fail('progress-aware decoder stall detection is missing: '+str(exc))
            self.assertEqual([s[0] for s in samples],[0])

    def test_selected_crops_retain_original_frame_indices(self):
        with tempfile.TemporaryDirectory() as d:
            video=Path(d)/'synthetic.mp4'
            subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','testsrc2=size=128x64:rate=25:duration=3',
                            '-c:v','mpeg4',str(video)],check=True,capture_output=True)
            try:
                samples=list(iter_video_samples(video,75,5,windows=[(11,26),(50,61)],roi=(.25,.25,.5,.5)))
            except TypeError as exc:
                self.fail('selective original-index decoder is missing: '+str(exc))
            self.assertEqual([s[0] for s in samples],[15,20,25,50,55,60])
            self.assertEqual((samples[0][2],samples[0][3]),(256,128))


@unittest.skipUnless(all(shutil.which(p) for p in ('ffmpeg','ffprobe','tesseract'))
                     and importlib.util.find_spec('PIL'),'needs local OCR and Pillow')
class GeneratedClockPair(unittest.TestCase):
    def test_automatic_regions_produce_bounded_correspondence_with_different_video_indices(self):
        self.assertIsNotNone(automatic,'automatic synchronization is missing')
        from PIL import Image,ImageDraw,ImageFont
        try:
            font=ImageFont.truetype('DejaVuSansMono-Bold.ttf',36)
        except OSError:
            font=ImageFont.load_default(size=36)
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            for source,offset in [('tactical',0),('broadcast',2)]:
                directory=root/source
                directory.mkdir()
                for i in range(8):
                    image=Image.new('RGB',(640,300),'black')
                    seconds=720+i-offset
                    ImageDraw.Draw(image).text((200,100),'{:02d}:{:02d}'.format(seconds//60,seconds%60),font=font,fill='white')
                    image.save(directory/('{}.png'.format(i)))
                subprocess.run(['ffmpeg','-v','error','-framerate','1','-i',str(directory/'%d.png'),
                                '-r','25','-c:v','libx264','-pix_fmt','yuv420p',str(root/(source+'.mp4'))],
                               check=True,capture_output=True)
            t,b=report(25,721),report(75,721)
            t['frame_count']=b['frame_count']=200
            jobs,_=automatic.plan_windows(t,b,[(1,0,199)])
            timelines={}
            for source,discovery in [('tactical',t),('broadcast',b)]:
                batches=automatic._camera_reads(root/(source+'.mp4'),discovery,jobs[source],source,'ffmpeg','tesseract')
                timelines[source]=automatic.merge_dense_reads(batches,200)
                self.assertTrue(all(c is None for c in timelines[source][:jobs[source][0]['start']]))
            from gap_solver.clock_sync import align_clocks
            mapping=align_clocks(timelines['tactical'],timelines['broadcast'])
            candidates=[(i,m) for i,m in enumerate(mapping) if m.broadcast_frame is not None]
            self.assertGreater(len(candidates),20)
            self.assertTrue(all(abs(m.broadcast_frame-i-50)<=2 for i,m in candidates))


if __name__=='__main__':
    unittest.main()
