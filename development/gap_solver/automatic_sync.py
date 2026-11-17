"""Automatic local clock correspondence. No possession labels or live-footage claim."""
import csv
import io
import json
import os
import shutil
import subprocess
import tempfile
from collections import Counter, deque
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from math import ceil, floor, isfinite
from pathlib import Path

from .clock_discovery import _valid_roi, iter_video_samples, read_pgm
from .clock_ocr import clock_from_tsv, probe_video, select_clock_candidate
from .clock_sync import ClockRead, align_clocks, dense_clock, parse_clock, validate_timeline
from .io import BLOCKS, N_FRAMES


OUTPUT_NAMES=('tactical-clock.csv','broadcast-clock.csv','tactical-reads.csv',
              'broadcast-reads.csv','alignment.csv','sync-report.json')


def padded_roi(roi):
    if not _valid_roi(roi):
        raise ValueError('invalid discovered clock box')
    x,y,w,h=roi
    left,top=max(0,x-h),max(0,y-h/2)
    right,bottom=min(1,x+w+h),min(1,y+h+h/2)
    return (left,top,right-left,bottom-top)


def _validate_report(report):
    if (report.get('schema_version')!=1 or type(report.get('frame_count')) is not int
            or report['frame_count']<1 or report.get('fps')!=25
            or report.get('settings',{}).get('min_confidence')!=.7):
        raise ValueError('discovery needs schema 1, original dimensions, 25 fps and unchanged .7 cutoff')
    stride=report.get('sample_stride_frames')
    if type(stride) is not int or stride<1:
        raise ValueError('invalid discovery sample stride')
    segments=report.get('segments')
    if not isinstance(segments,list):
        raise ValueError('discovery segments must be a list')
    for segment in segments:
        first,end=segment['start_frame'],segment['end_frame_exclusive']
        if (type(first) is not int or type(end) is not int
                or not 0<=first<end<=report['frame_count'] or not _valid_roi(segment['roi'])):
            raise ValueError('invalid discovery segment bounds/box')
        reads=segment['readings']
        if len(reads)<3:
            raise ValueError('discovery segment needs at least three supported readings')
        previous=None
        boxes=[]
        for r in reads:
            if (type(r['frame']) is not int or not first<=r['frame']<end
                    or parse_clock(r['text'])!=r['seconds'] or not isfinite(r['seconds'])
                    or not isfinite(r['confidence']) or not .7<=r['confidence']<=1):
                raise ValueError('invalid discovery reading')
            if not _valid_roi(r['roi']) or r['frame']%stride:
                raise ValueError('invalid discovery observation box or sampling index')
            boxes.append(r['roi'])
            if previous is not None:
                dt=(r['frame']-previous['frame'])/25
                dc=r['seconds']-previous['seconds']
                if dt<=0 or dc<=0 or abs(dc-dt)>1.000001:
                    raise ValueError('discovery readings must progress in original frame order')
                if r['frame']-previous['frame']>2*stride:
                    raise ValueError('discovery segment crosses an unsupported sparse sample gap')
            previous=r
        if reads[0]['frame']!=first or reads[-1]['frame']+1!=end:
            raise ValueError('segment bounds must match its supported readings')
        union=(min(b[0] for b in boxes),min(b[1] for b in boxes),
               max(b[0]+b[2] for b in boxes),max(b[1]+b[3] for b in boxes))
        declared=(segment['roi'][0],segment['roi'][1],segment['roi'][0]+segment['roi'][2],segment['roi'][1]+segment['roi'][3])
        if any(abs(a-b)>1e-8 for a,b in zip(union,declared)):
            raise ValueError('discovery crop must be the union of its observed clock boxes')


def _uncontested(segments):
    return [(i,s) for i,s in enumerate(segments) if not any(
        i!=j and max(s['start_frame'],other['start_frame'])<min(s['end_frame_exclusive'],other['end_frame_exclusive'])
        for j,other in enumerate(segments))]


def _frame_at(segment,seconds):
    reads=segment['readings']
    for a,b in zip(reads,reads[1:]):
        if a['seconds']<=seconds<=b['seconds']:
            return a['frame']+(seconds-a['seconds'])*(b['frame']-a['frame'])/(b['seconds']-a['seconds'])
    raise ValueError('cannot extrapolate processing windows beyond discovery support')


def _job(index,segment,half,low,high):
    return dict(segment=index,half=half,start=max(segment['start_frame'],floor(_frame_at(segment,low))),
                end=min(segment['end_frame_exclusive'],ceil(_frame_at(segment,high))+1),roi=segment['roi'])


def _merge_jobs(jobs):
    merged=[]
    for job in sorted(jobs,key=lambda j:(j['segment'],j['start'])):
        if merged and merged[-1]['segment']==job['segment'] and job['start']<=merged[-1]['end']:
            merged[-1]['end']=max(merged[-1]['end'],job['end'])
        else:
            merged.append(dict(job))
    return sorted(merged,key=lambda j:j['start'])


def plan_windows(tactical,broadcast,blocks=BLOCKS):
    """Sparse interpolation chooses work bounds only; it is never a timing estimate."""
    _validate_report(tactical)
    _validate_report(broadcast)
    jobs={'tactical':[],'broadcast':[]}
    qualified=[]
    for ti,t in _uncontested(tactical['segments']):
        halves={half for half,first,last in blocks if first<=t['start_frame'] and t['end_frame_exclusive']<=last+1}
        if len(halves)==1:
            qualified.append((ti,t,next(iter(halves))))
    ambiguous=unmatched=0
    for bi,b in _uncontested(broadcast['segments']):
        # Explicit added-time notation carries half identity. Ordinary elapsed
        # minutes >=45 can describe either half; absent sparse coverage proves nothing.
        markers={r['text'].replace(' ','').split('+')[0] for r in b['readings'] if '+' in r['text']}
        if markers=={'45'}:
            allowed={1}
        elif markers=={'90'}:
            allowed={2}
        elif not markers and max(r['seconds'] for r in b['readings'])<45*60:
            allowed={1}
        else:
            ambiguous+=1
            continue
        overlaps=[]
        for ti,t,half in qualified:
            if half not in allowed:
                continue
            low=max(t['readings'][0]['seconds'],b['readings'][0]['seconds'])
            high=min(t['readings'][-1]['seconds'],b['readings'][-1]['seconds'])
            if low<high:
                overlaps.append((ti,t,half,low,high))
        halves={row[2] for row in overlaps}
        if len(halves)>1:
            ambiguous+=1
            continue
        if not overlaps:
            unmatched+=1
            continue
        for ti,t,half,low,high in overlaps:
            jobs['tactical'].append(_job(ti,t,half,low,high))
            jobs['broadcast'].append(_job(bi,b,half,low,high))
    jobs={source:_merge_jobs(rows) for source,rows in jobs.items()}
    return jobs,dict(ambiguous_broadcast_segments=ambiguous,unmatched_broadcast_segments=unmatched,
                     tactical_segments_with_published_half=len(qualified),
                     half_provenance='continuous-clock semantics or explicit added-time notation, checked against published tactical evaluation half windows',
                     sparse_interpolation_used_for_timing=False,live_verified=False,ready_for_fusion=False)


def merge_dense_reads(batches,n_frames):
    result=[None]*n_frames
    conflicted=set()
    segment_offset=0
    for reads in batches:
        dense=dense_clock(reads,n_frames,min_confidence=.7)
        for frame,clock in enumerate(dense):
            if clock is None or frame in conflicted:
                continue
            clock=replace(clock,segment=clock.segment+segment_offset)
            if result[frame] is not None and result[frame]!=clock:
                result[frame]=None
                conflicted.add(frame)
            else:
                result[frame]=clock
        segment_offset+=1+max((c.segment for c in dense if c is not None),default=-1)
    # Every discontinuity gets a new ID, including those introduced by conflicting support.
    segment=-1
    previous=None
    for frame,clock in enumerate(result):
        if clock is None:
            previous=None
            continue
        if previous is None or clock.segment!=previous.segment:
            segment+=1
        previous=clock
        result[frame]=replace(clock,segment=segment)
    validate_timeline(result)
    return result


def protect_outputs(directory,inputs):
    for name in OUTPUT_NAMES:
        target=Path(directory)/name
        for path in map(Path,inputs):
            if target.resolve()==path.resolve() or target.exists() and path.exists() and target.samefile(path):
                raise ValueError('automatic output must not replace an input or an alias of it')
    directory=Path(directory)
    if directory.exists():
        if not directory.is_dir():
            raise ValueError('automatic output requires a dedicated directory')
        if any(directory.iterdir()):
            try:
                report=json.loads((directory/'sync-report.json').read_text(encoding='utf-8'))
                owned=(report.get('schema_version')==1 and report.get('method')=='automatic_discovery_bounded_dense_ocr'
                       and not directory.is_symlink() and all(p.name in OUTPUT_NAMES and p.is_file() and not p.is_symlink()
                                                               for p in directory.iterdir()))
            except (OSError,ValueError,AttributeError):
                owned=False
            if not owned:
                raise ValueError('Refusing to overwrite a nonempty output folder not owned by automatic-sync; use a dedicated directory')


def _job_image(image,width,height,box,union):
    left,top,right,bottom=union
    x0=max(0,floor((box[0]-left)*width/(right-left)))
    x1=min(width,ceil((box[0]+box[2]-left)*width/(right-left)))
    y0=max(0,floor((box[1]-top)*height/(bottom-top)))
    y1=min(height,ceil((box[1]+box[3]-top)*height/(bottom-top)))
    if x0>=x1 or y0>=y1:
        raise ValueError('active automatic clock crop is empty')
    _,actual_width,actual_height=read_pgm(io.BytesIO(image))
    if (actual_width,actual_height)!=(width,height):
        raise ValueError('automatic clock crop dimensions do not match decoder output')
    pixels=image[-width*height:]
    body=b''.join(pixels[y*width+x0:y*width+x1] for y in range(y0,y1))
    return 'P5\n{} {}\n255\n'.format(x1-x0,y1-y0).encode('ascii')+body


def _ocr_pgm(image,tesseract):
    result=subprocess.run([tesseract,'stdin','stdout','-l','eng','--oem','1','--psm','7',
                           '-c','tessedit_char_whitelist=0123456789:+','-c','tessedit_create_tsv=1'],
                          input=image,capture_output=True,timeout=30)
    if result.returncode:
        raise ValueError('Local Tesseract failed: '+result.stderr.decode('utf-8',errors='replace')[-1500:])
    return clock_from_tsv(result.stdout.decode('utf-8-sig',errors='replace'))


def _preprocess_pgm(image,source):
    if source not in ('tactical','broadcast'):
        raise ValueError('unknown camera source')
    raw,width,height=read_pgm(io.BytesIO(image))
    pixels=raw[-width*height:]
    if source=='tactical':
        pixels=pixels.translate(bytes(255-v for v in range(256)))
    # Exactly preprocessing_filter(): source polarity plus a 12-pixel white border.
    border=b'\xff'*12
    rows=[border+pixels[y*width:(y+1)*width]+border for y in range(height)]
    blank=b'\xff'*(width+24)
    body=blank*12+b''.join(rows)+blank*12
    return 'P5\n{} {}\n255\n'.format(width+24,height+24).encode('ascii')+body


def _read_image(image,tesseract,source):
    primary_image=_preprocess_pgm(image,source)
    primary=_ocr_pgm(primary_image,tesseract)
    if parse_clock(primary[0]) is not None and primary[1]>=.7:
        return primary[0],primary[1],'primary',1
    _,width,height=read_pgm(io.BytesIO(primary_image))
    pixels=primary_image[-width*height:].translate(bytes(0 if v<128 else 255 for v in range(256)))
    binary='P5\n{} {}\n255\n'.format(width,height).encode('ascii')+pixels
    candidates=[('primary',*primary),('unprocessed',*_ocr_pgm(image,tesseract)),
                ('thresholded',*_ocr_pgm(binary,tesseract))]
    return (*select_clock_candidate(candidates,.7),3)


def _camera_reads(video,report,jobs,source,ffmpeg,tesseract):
    if not jobs:
        return []
    boxes=[padded_roi(j['roi']) for j in jobs]
    left,top=min(b[0] for b in boxes),min(b[1] for b in boxes)
    right,bottom=max(b[0]+b[2] for b in boxes),max(b[1]+b[3] for b in boxes)
    stream=iter_video_samples(video,report['frame_count'],5,ffmpeg,
                              [(j['start'],j['end']) for j in jobs],(left,top,right-left,bottom-top))
    batches=[[] for _ in jobs]
    pending=deque()
    count=0
    def collect(item):
        nonlocal count
        frame,half,index,future=item
        text,confidence,method,attempts=future.result()
        batches[index].append(ClockRead(frame,text,confidence,half,method,attempts))
        count+=1
        if count==1 or count%100==0:
            print('{}: {} dense OCR samples processed'.format(source,count),flush=True)
    try:
        with ThreadPoolExecutor(max_workers=4) as pool:
            for frame,image,width,height in stream:
                index=next(i for i,j in enumerate(jobs) if j['start']<=frame<j['end'])
                active=_job_image(image,width,height,boxes[index],(left,top,right,bottom))
                pending.append((frame,jobs[index]['half'],index,pool.submit(_read_image,active,tesseract,source)))
                if len(pending)>=8:
                    collect(pending.popleft())
            while pending:
                collect(pending.popleft())
    finally:
        stream.close()
    return batches


def _automatic_sync_impl(tactical_video,broadcast_video,tactical_discovery,broadcast_discovery,directory,
                         ffmpeg='ffmpeg',ffprobe='ffprobe',tesseract='tesseract'):
    # Import lazily to avoid a circular import at the multicam CLI entry point.
    from .multicam import write_alignment,write_dense_clock
    paths={'tactical':Path(tactical_discovery),'broadcast':Path(broadcast_discovery)}
    videos={'tactical':Path(tactical_video),'broadcast':Path(broadcast_video)}
    historical=[paths['tactical'].parent/name for name in ('tactical-clock.csv','broadcast-clock.csv','alignment.csv')]
    protect_outputs(directory,list(paths.values())+list(videos.values())+historical)
    reports={source:json.loads(path.read_text(encoding='utf-8-sig')) for source,path in paths.items()}
    jobs,audit=plan_windows(reports['tactical'],reports['broadcast'])
    if reports['tactical']['frame_count']!=N_FRAMES:
        raise ValueError('published half windows require the reference tactical export dimensions')
    for source in videos:
        count,fps=probe_video(videos[source],ffprobe)
        if (count,fps)!=(reports[source]['frame_count'],reports[source]['fps']):
            raise ValueError('{} discovery does not match original video dimensions/rate'.format(source))
    timelines={}
    stats={}
    destination=Path(directory)
    destination.mkdir(parents=True,exist_ok=True)
    for source in ('tactical','broadcast'):
        print('{}: {} automatically selected processing windows'.format(source,len(jobs[source])),flush=True)
        batches=_camera_reads(videos[source],reports[source],jobs[source],source,ffmpeg,tesseract)
        timelines[source]=merge_dense_reads(batches,reports[source]['frame_count'])
        reads=[r for batch in batches for r in batch]
        stats[source]=dict(original_frames=reports[source]['frame_count'],processing_windows=len(jobs[source]),
                           ocr_samples=len(reads),eligible_reads=sum(parse_clock(r.text) is not None and r.confidence>=.7 for r in reads),
                           retried_samples=sum(r.attempts>1 for r in reads),conflicting_retry_samples=sum(r.method=='conflict' for r in reads),
                           bounded_clock_frames=sum(c is not None for c in timelines[source]))
        write_dense_clock(destination/(source+'-clock.csv'),timelines[source])
        with (destination/(source+'-reads.csv')).open('w',newline='',encoding='utf-8') as handle:
            writer=csv.writer(handle,lineterminator='\n')
            writer.writerow(['frame','half','clock_text','ocr_confidence','ocr_method','ocr_attempts'])
            writer.writerows((r.frame,r.half,r.text,r.confidence,r.method,r.attempts) for r in reads)
    mapping=align_clocks(timelines['tactical'],timelines['broadcast'])
    write_alignment(destination/'alignment.csv',mapping,timelines['tactical'])
    audit.update(schema_version=1,method='automatic_discovery_bounded_dense_ocr',cameras=stats,
                 alignment_status_counts=dict(Counter(m.status for m in mapping)),
                 accuracy_measured=False,video_visual_check_performed=False,half_assignment_included=True,
                 dense_clock_included=True,parameters=dict(ocr_cutoff=.7,stride_frames=5,max_uncertainty_s=.25),
                 parameter_provenance='Existing engineering defaults; no tuning on challenge outputs.',
                 ocr_recipe='existing fixed source preprocessing and weak-read retry policy; in-memory pixel parity checked against FFmpeg',
                 warning='Clock candidates only. Temporal live/replay verification and possession fusion were not performed.')
    (destination/'sync-report.json').write_text(json.dumps(audit,indent=2)+'\n',encoding='utf-8')
    return audit


def automatic_sync(tactical_video,broadcast_video,tactical_discovery,broadcast_discovery,directory,
                   ffmpeg='ffmpeg',ffprobe='ffprobe',tesseract='tesseract'):
    destination=Path(directory)
    paths=[Path(tactical_video),Path(broadcast_video),Path(tactical_discovery),Path(broadcast_discovery)]
    for a,b in ((paths[0],paths[1]),(paths[2],paths[3])):
        if a.resolve()==b.resolve() or a.exists() and b.exists() and a.samefile(b):
            raise ValueError('two-camera synchronization requires different video and discovery inputs')
    paths.extend(Path(tactical_discovery).parent/name for name in ('tactical-clock.csv','broadcast-clock.csv','alignment.csv'))
    protect_outputs(destination,paths)
    destination.parent.mkdir(parents=True,exist_ok=True)
    # Failed OCR/decoding cannot leave a new camera map next to an old successful report.
    with tempfile.TemporaryDirectory(prefix='.automatic-sync-',dir=destination.parent) as staging:
        audit=_automatic_sync_impl(tactical_video,broadcast_video,tactical_discovery,broadcast_discovery,
                                   staging,ffmpeg,ffprobe,tesseract)
        protect_outputs(destination,paths)
        destination.mkdir(parents=True,exist_ok=True)
        publish_outputs(Path(staging),destination)
    return audit


def publish_outputs(staging,destination):
    staging,destination=Path(staging),Path(destination)
    backup=staging.with_name(staging.name+'.previous')
    if backup.exists():
        raise ValueError('automatic output backup path already exists')
    moved=False
    if destination.exists():
        os.replace(destination,backup)
        moved=True
    try:
        os.replace(staging,destination)
    except BaseException:
        if moved:
            os.replace(backup,destination)
        raise
    if moved:
        # Verify the resolved computed target before deleting the superseded generation.
        if backup.resolve().parent!=destination.resolve().parent or not backup.name.endswith('.previous'):
            raise ValueError('automatic backup escaped its expected output parent')
        try:
            shutil.rmtree(backup)
        except OSError:
            print('Previous complete output retained locally at {}'.format(backup),flush=True)
