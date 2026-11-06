#!/usr/bin/env python3
"""Single-file football possession prototype. Python 3.9+.

Run:
    python football_pipeline.py camera demo
    python football_pipeline.py camera --help
    python football_pipeline.py --guide

Keep this ONE source file. Future updates replace it in place. The program
loads its bundled modules in memory; no package extraction is required.
Result CSV/JSON files use the same output folders on each run and are overwritten.
Real video OCR additionally needs local FFmpeg/ffprobe and Tesseract executables.
Published pre-kickoff D context is included; no general live/dead classifier,
network calls or automatic updater is included.
Synthetic examples do not establish real-match accuracy.
"""
import importlib.abc
import importlib.util
import importlib
import sys

VERSION = '2026.11.06-temporal-research'

# Inspectable source modules, bundled verbatim and loaded only in memory.
SOURCES = {
    'gap_solver': r'''"""Experimental, local possession-gap handling."""
''',
    'gap_solver.__main__': r'''"""Run from the extracted project folder: python -m gap_solver demo."""
import argparse
import json
from dataclasses import replace
from pathlib import Path
import xml.etree.ElementTree as ET

from .core import Config, Frame, infer, summary
from .io import N_FRAMES, apply_published_dead, load_atd, load_tags, read_evidence, write_outputs


def demo_frames():
    def control(side, n=20):
        return [Frame(ball_x=10, ball_y=10,
                      home_distance=0.5 if side == 'H' else 8,
                      away_distance=0.5 if side == 'A' else 8) for _ in range(n)]

    examples = [
        ('short_occlusion', control('H') + [Frame()] * 10 + control('H')),
        ('tag_supported_occlusion', control('H') + [Frame(tag_team='H')] * 35 + control('H')),
        ('hidden_turnover_ambiguous', control('H') + [Frame()] * 20 + control('A')),
        ('long_gap_ambiguous', control('A') + [Frame()] * 70 + control('A')),
        ('restart_ambiguous', control('H') + [Frame(restart_hint=True)] * 10 + control('H')),
        ('brief_deflection', control('H') + control('A', 2) + control('H')),
        ('confirmed_turnover', control('H') + control('A')),
        ('upstream_dead_detector', control('H') + [Frame(dead_evidence=True)] * 15 + control('H')),
    ]
    frames, scenes = [], []
    for name, clip in examples:
        scenes.append({'name': name, 'start_frame': len(frames),
                       'end_frame_exclusive': len(frames) + len(clip)})
        frames.extend(clip)
        frames.append(Frame(period=0))  # isolate independent synthetic scenarios
    return frames, scenes


def main():
    parser = argparse.ArgumentParser(description='Experimental local possession-gap handler')
    sub = parser.add_subparsers(dest='command', required=True)
    for command in ('demo', 'evidence', 'match'):
        p = sub.add_parser(command)
        p.add_argument('--out', default='outputs/' + command)
        p.add_argument('--config', help='JSON object with Config fields; defaults are provisional')
        if command == 'demo':
            p.add_argument('--full-length', action='store_true',
                           help='pad SYNTHETIC demo to 199319 rows for format validation only')
        elif command == 'evidence':
            p.add_argument('--input', required=True)
        else:
            p.add_argument('--data-dir', required=True,
                           help='local parent of tactical/; never uploads assets')
    args = parser.parse_args()
    try:
        cfg = Config(**(json.loads(Path(args.config).read_text()) if args.config else {}))
        cfg.validate()
        scenes = None
        if args.command == 'demo':
            frames, scenes = demo_frames()
            if args.full_length:
                frames += [Frame(period=0)] * (N_FRAMES - len(frames))
        elif args.command == 'evidence':
            frames = read_evidence(args.input)
        else:
            tactical = Path(args.data_dir) / 'tactical'
            stem = tactical / 'BAR-ATH_tactical'
            frames, names = load_atd(str(stem) + '_atd.xml', str(stem) + '_atd.txt')
            tag_path = Path(str(stem) + '_smart_tagging.xml')
            if tag_path.exists():
                frames = load_tags(tag_path, frames, names, cfg.fps)
            frames = apply_published_dead(frames)
            print('EXPERIMENTAL: published pre-kickoff D context included; general live/dead detector absent.')
        decisions = infer(frames, cfg)
        report = write_outputs(args.out, frames, decisions, cfg)
        if scenes is not None:
            before = summary(frames, infer(frames, replace(cfg, short_bridge_s=0, tagged_bridge_s=0)))
            comparison = {'synthetic_only': True, 'accuracy_measured': False,
                          'before': before, 'after': report, 'scenarios': scenes}
            Path(args.out, 'demo_comparison.json').write_text(json.dumps(comparison, indent=2) + '\n')
            print('Synthetic scenarios only; not a match benchmark or a real recovery estimate.')
            print('Unresolved frames before/after bridging: {} / {}'.format(
                before['labels']['X'], report['labels']['X']))
        print('Active frames: {}; inferred: {}; unresolved: {}'.format(
            report['active_frames'], report['inferred_frames'], report['labels']['X']))
        print('Output: ' + str(Path(args.out).resolve()))
    except (OSError, ValueError, TypeError, KeyError, ET.ParseError) as exc:
        parser.error(str(exc))


if __name__ == '__main__':
    main()
''',
    'gap_solver.acquisition': r'''"""Verified external acquisition with no unverified resume or overwrite of edited caches."""
import hashlib
import os
from pathlib import Path
import tempfile
import urllib.request


def asset_digest(path,size,algorithm):
    digest=hashlib.sha256() if algorithm=='sha256' else hashlib.sha1()
    if algorithm=='git_blob_sha1':digest.update(b'blob '+str(size).encode()+b'\0')
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda:handle.read(4*1024*1024),b''):digest.update(chunk)
    return digest.hexdigest()


def acquire_asset(url,destination,size,expected,algorithm='sha256'):
    destination=Path(destination)
    length=64 if algorithm=='sha256' else 40
    if algorithm not in ('sha256','git_blob_sha1') or type(size) is not int or size<0 or len(expected)!=length or any(c not in '0123456789abcdef' for c in expected):
        raise ValueError('invalid immutable acquisition identity')
    if destination.is_symlink():raise ValueError('external asset destination cannot be a link')
    def verified(path):return path.stat().st_size==size and asset_digest(path,size,algorithm)==expected
    if destination.exists():
        if not destination.is_file() or not verified(destination):raise ValueError('Existing external asset differs; preserving it: '+str(destination))
        return dict(path=str(destination),bytes=size,digest=expected,cached=True)
    destination.parent.mkdir(parents=True,exist_ok=True)
    descriptor,temporary=tempfile.mkstemp(prefix='.'+destination.name+'.download-',suffix='.part',dir=destination.parent)
    temporary=Path(temporary)
    with os.fdopen(descriptor,'wb') as output:
        with urllib.request.urlopen(url,timeout=90) as response:
            for chunk in iter(lambda:response.read(4*1024*1024),b''):output.write(chunk)
    if not verified(temporary):raise ValueError('Source size/checksum mismatch; unverified partial preserved: '+str(temporary))
    if destination.exists():
        if not verified(destination):raise ValueError('External destination changed during acquisition; preserving both files')
        temporary.unlink()
    elif os.name=='nt':
        # Unlike POSIX rename, Windows rename refuses an existing destination.
        os.rename(temporary,destination)
    else:
        os.link(temporary,destination)
        temporary.unlink()
    return dict(path=str(destination),bytes=size,digest=expected,cached=False)
''',
    'gap_solver.audit': r'''"""Controlled behavior comparisons, without reading or scoring ground truth."""
from collections import Counter

from .core import Config, _blocks, infer, summary


def scorer_expanded_labels(frames, decisions):
    """Mirror official X filling inside grading blocks; this is not an accuracy score."""
    if len(frames) != len(decisions) or any(d.label not in ('H', 'A', 'D', 'X') for d in decisions):
        raise ValueError('audit requires one valid decision per original frame')
    labels = [d.label for d in decisions]
    for low, high in _blocks(frames):
        first = next((i for i in range(low, high) if labels[i] != 'X'), None)
        if first is None:
            continue
        previous = labels[first]
        for i in range(low, high):
            if labels[i] == 'X':
                labels[i] = previous
            else:
                previous = labels[i]
    return labels


def _spell_count(frames, labels):
    count = 0
    for low, high in _blocks(frames):
        previous = None
        for label in labels[low:high]:
            count += label in ('H', 'A') and label != previous
            previous = label
    return count


def compare_decisions(frames, before, after):
    old = scorer_expanded_labels(frames, before)
    new = scorer_expanded_labels(frames, after)
    active = [i for i, f in enumerate(frames) if f.period]
    changed = [i for i in active if before[i].label != after[i].label]
    return {
        'raw_label_changes': len(changed),
        'newly_assigned_frames': sum(before[i].label == 'X' and after[i].label != 'X' for i in changed),
        'newly_assigned_missing_ball_team_frames': sum(
            before[i].label == 'X' and after[i].label in ('H', 'A') and not frames[i].ball_observed
            for i in changed),
        'scorer_expanded_label_changes': sum(old[i] != new[i] for i in active),
        'propagated_changes_on_raw_unchanged_frames': sum(
            old[i] != new[i] and before[i].label == after[i].label for i in active),
        'raw_changes_without_scorer_effect': sum(old[i] == new[i] for i in changed),
        'label_transition_counts': dict(Counter(before[i].label+'->'+after[i].label for i in changed)),
        'changed_from_reason_counts': dict(Counter(before[i].reason for i in changed)),
        'changed_to_reason_counts': dict(Counter(after[i].reason for i in changed)),
        'possession_spells_before': _spell_count(frames, old),
        'possession_spells_after': _spell_count(frames, new),
        'accuracy_measured': False,
    }


def bridge_diagnostics(frames, decisions, cfg=Config()):
    """Explain remaining X runs after the existing bridge rules, without filling them."""
    if len(frames) != len(decisions):
        raise ValueError('bridge audit dimensions differ')
    intervals, counts, missing = Counter(), Counter(), 0
    for low, high in _blocks(frames):
        i = low
        while i < high:
            if decisions[i].label != 'X':
                i += 1
                continue
            start = i
            while i < high and decisions[i].label == 'X':
                missing += not frames[i].ball_observed
                i += 1
            segment = frames[start:i]
            left = decisions[start-1] if start > low else None
            right = decisions[i] if i < high else None
            if left is None or right is None:
                cause = 'unbounded_gap'
            elif any(f.restart_hint or f.dead_evidence for f in segment):
                cause = 'restart_or_dead_context'
            elif left.label not in ('H', 'A') or right.label not in ('H', 'A'):
                cause = 'non_team_anchor'
            elif left.label != right.label:
                cause = 'opposing_anchors'
            elif any(f.tag_team in ('H', 'A', 'CONFLICT') and f.tag_team != left.label for f in segment):
                cause = 'conflicting_tags'
            elif ((i-start)/cfg.fps > cfg.short_bridge_s and
                  ((i-start)/cfg.fps > cfg.tagged_bridge_s or
                   not all(f.tag_team == left.label for f in segment))):
                cause = 'duration_or_tag_support'
            else:
                cause = 'unsupported_or_unconfirmed_anchor'
            intervals[cause] += 1
            counts[cause] += i-start
    return {'intervals_by_cause': dict(intervals), 'frames_by_cause': dict(counts),
            'unresolved_missing_ball_frames': missing,
            'note': 'Diagnostic categories after existing rules; not new possession evidence.'}


def build_baseline_audit(raw_frames, corrected_frames, fused_decisions, cfg=Config()):
    if (len(raw_frames) != len(corrected_frames) or len(raw_frames) != len(fused_decisions)
            or any(a.period != b.period for a, b in zip(raw_frames, corrected_frames))):
        raise ValueError('controlled comparisons require identical frame and half indices')
    stages = {'legacy_tactical': infer(raw_frames, cfg, legacy_restart_veto=True),
              'restart_repaired': infer(raw_frames, cfg),
              'published_context': infer(corrected_frames, cfg)}
    report = {
        'accuracy_measured': False,
        'stages': {name: summary(raw_frames if name != 'published_context' else corrected_frames, decisions)
                   for name, decisions in stages.items()},
        'comparisons': {
            'restart_repair': compare_decisions(raw_frames, stages['legacy_tactical'], stages['restart_repaired']),
            'published_context': compare_decisions(corrected_frames, stages['restart_repaired'], stages['published_context']),
            'broadcast_fusion': compare_decisions(corrected_frames, stages['published_context'], fused_decisions),
            'total': compare_decisions(corrected_frames, stages['legacy_tactical'], fused_decisions),
        },
        'remaining_gap_diagnostics': bridge_diagnostics(corrected_frames, stages['published_context'], cfg),
        'note': 'Fixed-input behavior ablation. Scorer-expanded changes are not spellF1 or accuracy.',
    }
    return report, stages
''',
    'gap_solver.automatic_sync': r'''"""Automatic local clock correspondence. No possession labels or live-footage claim."""
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
''',
    'gap_solver.benchmark': r'''"""External provider-reference evaluation with unchanged official metric functions."""
import numpy as np
from . import official_metrics


def _validate(reference,prediction,periods):
    arrays=[np.asarray(x) for x in (reference,prediction,periods)]
    if any(a.ndim!=1 for a in arrays) or not len(arrays[0]) or len({len(a) for a in arrays})!=1:
        raise ValueError('external metric inputs need nonempty matching one-dimensional arrays')
    gt,pred,period=arrays
    if not np.isin(gt,[0,1,2,3]).all() or not np.isin(pred,[0,1,2,3]).all() or not np.isin(period,[1,2]).all():
        raise ValueError('invalid external reference, prediction or period code')
    if not (gt<3).any():
        raise ValueError('external reference has no scored support')
    chunks=period[np.r_[True,period[1:]!=period[:-1]]]
    if len(set(chunks.tolist()))!=len(chunks):
        raise ValueError('external periods cannot reappear after a reset')
    return gt.astype(np.uint8),pred.astype(np.uint8),period.astype(np.uint8)


def evaluation_arrays(reference,prediction,periods):
    gt,pred,period=_validate(reference,prediction,periods)
    starts=np.r_[0,np.flatnonzero(period[1:]!=period[:-1])+1,len(period)]
    a=[];b=[]
    separator=np.full(max(official_metrics.TAUS)+1,3,dtype=np.uint8)
    for index,(first,stop) in enumerate(zip(starts,starts[1:])):
        if index:
            a.append(separator);b.append(separator)
        a.append(gt[first:stop]);b.append(pred[first:stop])
    return np.concatenate(a),np.concatenate(b)


def evaluate_external(reference,prediction,periods):
    gt,pred,period=_validate(reference,prediction,periods)
    scored=gt<3
    a,b=evaluation_arrays(gt,pred,period)
    result=official_metrics.evaluate(a,b,bootstrap_n=0)
    n=int(scored.sum());x=int(((pred==3)&scored).sum())
    decided=scored&(pred<3)
    return dict(reference_type='external provider reference; not challenge accuracy',metrics=result,
                coverage=dict(original_frames=len(gt),graded_frames=n,undecided_frames=x,undecided_fraction=x/n,
                              decided_correct_fraction=float((gt[decided]==pred[decided]).mean()) if decided.any() else None),
                evaluation_only_separator_frames=len(a)-len(gt))


def compare_external(reference,before,after,periods):
    gt,old,period=_validate(reference,before,periods)
    _,new,_=_validate(reference,after,periods)
    scored=gt<3
    assigned=scored&(old==3)&(new<3)
    support=int(assigned.sum())
    labels={}
    for code,name in enumerate('HAD'):
        mask=assigned&(new==code)
        count=int(mask.sum())
        labels[name]=dict(frames=count,correct_fraction=float((gt[mask]==new[mask]).mean()) if count else None)
    padded_gt,padded_old=evaluation_arrays(gt,old,period)
    _,padded_new=evaluation_arrays(gt,new,period)
    runs=official_metrics.valid_runs(padded_gt)
    expanded_old=official_metrics.fill_abstentions(padded_old,runs)
    expanded_new=official_metrics.fill_abstentions(padded_new,runs)
    starts=assigned&np.r_[True,(~assigned[:-1])|(period[1:]!=period[:-1])]
    changed_decided=scored&(old<3)&(new!=old)
    return dict(newly_resolved_frames=support,newly_resolved_intervals=int(starts.sum()),
                newly_resolved_correct_fraction=float((gt[assigned]==new[assigned]).mean()) if support else None,
                newly_resolved_by_label=labels,
                raw_label_changes=int((scored&(old!=new)).sum()),
                changed_already_decided_frames=int(changed_decided.sum()),
                already_decided_corrections=int((changed_decided&(old!=gt)&(new==gt)).sum()),
                already_decided_regressions=int((changed_decided&(old==gt)&(new!=gt)).sum()),
                reversions_to_undecided=int((scored&(old<3)&(new==3)).sum()),
                scorer_expanded_label_changes=int(((padded_gt<3)&(expanded_old!=expanded_new)).sum()),
                reference_type='external provider reference; not challenge accuracy')
''',
    'gap_solver.clock_discovery': r'''"""Automatic local clock-region discovery; not dense alignment or replay verification."""
import csv
import io
import re
import subprocess
import threading
import time
from collections import defaultdict, deque
from math import ceil, isfinite
from pathlib import Path

from .clock_ocr import probe_video
from .clock_sync import parse_clock


def _valid_roi(roi):
    return (len(roi) == 4 and all(isfinite(v) for v in roi)
            and min(roi[0], roi[1]) >= 0 and min(roi[2], roi[3]) > 0
            and roi[0] + roi[2] <= 1.000000001 and roi[1] + roi[3] <= 1.000000001)


def _iou(a, b):
    intersection = (max(0, min(a[0]+a[2], b[0]+b[2])-max(a[0], b[0]))
                    * max(0, min(a[1]+a[3], b[1]+b[3])-max(a[1], b[1])))
    return intersection / (a[2]*a[3]+b[2]*b[3]-intersection)


def clock_candidates(tsv, width, height, min_confidence=.7):
    """Find clock words or adjacent split tokens anywhere in a full-frame TSV."""
    if (not isfinite(width) or not isfinite(height) or min(width, height) <= 0
            or not isfinite(min_confidence) or not 0 <= min_confidence <= 1):
        raise ValueError('invalid image dimensions or OCR confidence cutoff')
    reader = csv.DictReader(io.StringIO(tsv.lstrip('\ufeff')), delimiter='\t')
    required = {'level', 'page_num', 'block_num', 'par_num', 'line_num',
                'left', 'top', 'width', 'height', 'conf', 'text'}
    if not required.issubset(reader.fieldnames or []):
        raise ValueError('Tesseract did not return full-frame TSV box columns')
    lines = defaultdict(list)
    for row in reader:
        if row.get('level') != '5' or not (row.get('text') or '').strip():
            continue
        try:
            x, y, w, h = (int(row[k]) for k in ('left', 'top', 'width', 'height'))
            confidence = float(row['conf']) / 100
        except (ValueError, TypeError):
            continue
        if (not isfinite(confidence) or not 0 <= confidence <= 1
                or min(x, y) < 0 or min(w, h) <= 0 or x+w > width or y+h > height):
            continue
        line = tuple(row[k] for k in ('page_num', 'block_num', 'par_num', 'line_num'))
        lines[line].append((x, y, w, h, row['text'].strip(), confidence))
    result, seen = [], set()
    for line, words in lines.items():
        words.sort(key=lambda w: w[0])
        for start in range(len(words)):
            for count in range(1, min(3, len(words)-start)+1):
                span = words[start:start+count]
                if any(b[0]-(a[0]+a[2]) > max(a[3], b[3])
                       or min(a[1]+a[3], b[1]+b[3])-max(a[1], b[1]) < .5*min(a[3], b[3])
                       for a, b in zip(span, span[1:])):
                    break
                text = ''.join(w[4] for w in span)
                seconds = parse_clock(text)
                confidence = min(w[5] for w in span)
                if seconds is None:
                    continue
                # A complete clock must not absorb an adjacent unrelated number.
                # Explicit stoppage notation is different: 45+ and 01:30 together
                # are one clock, and the suffix is not independent evidence.
                if (count > 1 and any(parse_clock(w[4]) is not None for w in span)
                        and not text.startswith(('45+', '90+'))):
                    continue
                x, y = min(w[0] for w in span), min(w[1] for w in span)
                right, bottom = max(w[0]+w[2] for w in span), max(w[1]+w[3] for w in span)
                key = (seconds, x, y, right, bottom)
                if key not in seen:
                    seen.add(key)
                    result.append(({'text': text, 'seconds': seconds, 'confidence': confidence,
                                    'roi': [x/width, y/height, (right-x)/width, (bottom-y)/height]},
                                   frozenset((line, i) for i in range(start, start+count))))
    # Suppress constituent readings before the confidence cutoff. A weak
    # recognised stoppage prefix must not turn its strong suffix into a clock.
    clocks = [c for c, tokens in result if c['confidence'] >= min_confidence
              and not any(tokens < other for _, other in result)]
    return sorted(clocks, key=lambda c: (c['roi'][1], c['roi'][0], c['seconds']))


def clock_segments(samples, fps, stride):
    """Associate unique stable boxes with progressing clocks; export observations only."""
    if not isfinite(fps) or fps <= 0 or not isinstance(stride, int) or stride < 1:
        raise ValueError('invalid clock discovery rate or stride')
    active, finished, previous_frame = [], [], -1
    for sample in samples:
        frame, candidates = sample['frame'], sample['candidates']
        if not isinstance(frame, int) or frame < 0 or frame <= previous_frame:
            raise ValueError('discovery samples need ordered original frame IDs')
        previous_frame = frame
        for c in candidates:
            if (not _valid_roi(c['roi']) or parse_clock(c['text']) != c['seconds']
                    or not isfinite(c['confidence']) or not 0 <= c['confidence'] <= 1):
                raise ValueError('invalid clock detection')
        expired = [t for t in active if frame-t[-1]['frame'] > 2*stride]
        finished.extend(expired)
        active = [t for t in active if frame-t[-1]['frame'] <= 2*stride]
        # Contradictory overlapping detections are ambiguity, not confidence votes.
        ambiguous = {i for i, c in enumerate(candidates)
                     if any(i != j and _iou(c['roi'], b['roi']) >= .5
                            for j, b in enumerate(candidates))}
        blocked = [t for t in active
                   if any(_iou(t[-1]['roi'], candidates[i]['roi']) >= .5 for i in ambiguous)]
        finished.extend(blocked)
        active = [t for t in active if t not in blocked]
        candidates = [c for i, c in enumerate(candidates) if i not in ambiguous]
        edges = [[j for j, c in enumerate(candidates) if _iou(t[-1]['roi'], c['roi']) >= .5]
                 for t in active]
        incoming = [[i for i, neighbors in enumerate(edges) if j in neighbors]
                    for j in range(len(candidates))]
        next_active = []
        for track, neighbors in zip(active, edges):
            if not neighbors:
                next_active.append(track)
                continue
            if len(neighbors) != 1 or len(incoming[neighbors[0]]) != 1:
                finished.append(track)
                continue
            c = candidates[neighbors[0]]
            reading = dict(c, frame=frame)
            elapsed = (frame-track[-1]['frame']) / fps
            delta = c['seconds']-track[-1]['seconds']
            if (delta > 0 and abs(delta-elapsed) <= 1.000000001
                    and _iou(track[0]['roi'], c['roi']) >= .5):
                track.append(reading)
                next_active.append(track)
            else:
                finished.append(track)
                next_active.append([reading])
        next_active.extend([[dict(c, frame=frame)] for j, c in enumerate(candidates) if not incoming[j]])
        active = next_active
    finished.extend(active)
    result = []
    for track in finished:
        if len(track) < 3:
            continue
        x, y = min(r['roi'][0] for r in track), min(r['roi'][1] for r in track)
        right = max(r['roi'][0]+r['roi'][2] for r in track)
        bottom = max(r['roi'][1]+r['roi'][3] for r in track)
        result.append({'start_frame': track[0]['frame'], 'end_frame_exclusive': track[-1]['frame']+1,
                       'roi': [x, y, right-x, bottom-y], 'readings': track,
                       'live_verified': False})
    return sorted(result, key=lambda s: (s['start_frame'], s['roi'][1], s['roi'][0]))


def read_pgm(stream):
    """Read exactly one 8-bit grayscale image, retaining all binary pixel values."""
    magic = stream.readline(4097)
    if magic == b'':
        return None
    if magic.strip() != b'P5':
        raise ValueError('Invalid PGM sample from video decoder')
    header_size, tokens = len(magic), []
    while len(tokens) < 3:
        line = stream.readline(4097)
        header_size += len(line)
        if not line or header_size > 4096 or not line.endswith(b'\n'):
            raise ValueError('Truncated or oversized PGM header')
        tokens.extend(line.split(b'#', 1)[0].split())
    try:
        width, height, maximum = map(int, tokens)
    except (ValueError, TypeError) as exc:
        raise ValueError('Invalid PGM dimensions') from exc
    if min(width, height) <= 0 or width*height > 40000000 or maximum != 255:
        raise ValueError('Unsupported PGM dimensions or pixel depth')
    remaining, chunks = width*height, []
    while remaining:
        chunk = stream.read(remaining)
        if not chunk:
            raise ValueError('Truncated PGM pixels; refusing to shift sample indices')
        chunks.append(chunk)
        remaining -= len(chunk)
    header = 'P5\n{} {}\n255\n'.format(width, height).encode('ascii')
    return header+b''.join(chunks), width, height


def iter_video_samples(video, n_frames, stride, ffmpeg='ffmpeg', windows=None, roi=None,
                       stall_timeout_s=120.0):
    """One decoder, bounded image memory, no frame files and original decoded indices."""
    if (not isinstance(n_frames, int) or n_frames < 1
            or not isinstance(stride, int) or stride < 1):
        raise ValueError('invalid video frame count or discovery stride')
    if not isfinite(stall_timeout_s) or stall_timeout_s<=0:
        raise ValueError('invalid decoder stall timeout')
    if windows is None:
        indices = range(0, n_frames, stride)
        select = "not(mod(n,{}))".format(stride)
    else:
        if any(not isinstance(a,int) or not isinstance(b,int) or not 0 <= a < b <= n_frames
               for a,b in windows):
            raise ValueError('invalid original-frame processing windows')
        indices = sorted({i for a,b in windows for i in range(((a+stride-1)//stride)*stride,b,stride)})
        if not indices:
            return
        select = "({})*not(mod(n,{}))".format(
            '+'.join('between(n,{},{})'.format(a,b-1) for a,b in windows),stride)
    filters = "showinfo=checksum=0,select='{}',format=gray".format(select)
    if roi is not None:
        if not _valid_roi(roi):
            raise ValueError('invalid automatic clock crop')
        x,y,w,h=roi
        filters += ',crop=iw*{}:ih*{}:iw*{}:ih*{},scale=iw*4:ih*4'.format(w,h,x,y)
    expected = len(indices)
    command = [ffmpeg, '-nostdin', '-hide_banner', '-nostats', '-loglevel', 'info',
               '-xerror', '-err_detect', 'explode', '-i', str(video),
               '-map', '0:v:0', '-an', '-sn', '-dn', '-vf',
               filters,
               '-fps_mode', 'vfr', '-frames:v', str(expected+1), '-c:v', 'pgm',
               '-f', 'image2pipe', 'pipe:1']
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except FileNotFoundError as exc:
        raise ValueError('Executable not found: {}. Install it locally or pass its path.'.format(ffmpeg)) from exc
    timed_out, recent = threading.Event(), deque(maxlen=10)
    decoded = {'frames': 0, 'ordered': True, 'log_error': False, 'progress_at': time.monotonic()}

    def drain_log():
        # Count before selection so dropped/extra decoded frames cannot hide
        # inside the same sparse sample count. No growing log file is retained.
        try:
            for line in iter(lambda: process.stderr.readline(8192), b''):
                match = re.search(rb'\bn:\s*(\d+)\s+pts:', line)
                if match:
                    number = int(match.group(1))
                    decoded['ordered'] &= number == decoded['frames']
                    decoded['frames'] += 1
                    decoded['progress_at'] = time.monotonic()
                elif b'showinfo' not in line:
                    recent.append(line[-400:].decode('utf-8', errors='replace').strip())
        except (OSError, ValueError):
            decoded['log_error'] = True

    log_reader = threading.Thread(target=drain_log, daemon=True)
    log_reader.start()
    monitor_done = threading.Event()

    def stop_decoder():
        timed_out.set()
        try:
            process.kill()
        except OSError:
            pass

    def monitor_progress():
        while not monitor_done.wait(min(1.0,stall_timeout_s/4)):
            if process.poll() is not None:
                return
            if time.monotonic()-decoded['progress_at']>stall_timeout_s:
                stop_decoder()
                return

    monitor = threading.Thread(target=monitor_progress,daemon=True)
    monitor.start()

    def next_image():
        result = read_pgm(process.stdout)
        if timed_out.is_set():
            raise ValueError('Video decoder stalled without forward original-frame progress')
        return result

    try:
        for index in range(expected):
            image = next_image()
            if image is None:
                raise ValueError('Decoded sample count differs from original indices: '+'\n'.join(recent)[-2000:])
            yield (indices[index], *image)
        if next_image() is not None:
            raise ValueError('Decoded sample count exceeds the reported video frame count')
        try:
            status = process.wait(timeout=30)
        except subprocess.TimeoutExpired as exc:
            raise ValueError('Video decoder did not finish after its final clock sample') from exc
        log_reader.join(timeout=5)
        if status:
            raise ValueError('Video decoder failed: '+'\n'.join(recent)[-2000:])
        if (log_reader.is_alive() or decoded['log_error'] or not decoded['ordered']
                or decoded['frames'] != n_frames):
            raise ValueError('Decoded full frame count differs from reported original frame count')
    finally:
        monitor_done.set()
        if process.poll() is None:
            process.kill()
        process.wait()
        monitor.join(timeout=2)
        process.stdout.close()
        log_reader.join(timeout=5)
        process.stderr.close()


def _sparse_ocr(image, tesseract):
    command = [tesseract, 'stdin', 'stdout', '-l', 'eng', '--oem', '1', '--psm', '11',
               '-c', 'tessedit_create_tsv=1']
    try:
        result = subprocess.run(command, input=image, capture_output=True, timeout=60)
    except FileNotFoundError as exc:
        raise ValueError('Executable not found: {}. Install it locally or pass its path.'.format(tesseract)) from exc
    except subprocess.TimeoutExpired as exc:
        raise ValueError('Tesseract timed out reading a full-frame clock sample') from exc
    if result.returncode:
        raise ValueError('Tesseract failed: '+result.stderr.decode('utf-8', errors='replace')[-2000:])
    return result.stdout.decode('utf-8-sig', errors='replace')


def scan_video(video, stride_seconds=30.0, min_confidence=.7,
               ffmpeg='ffmpeg', ffprobe='ffprobe', tesseract='tesseract'):
    """Scan a whole recording automatically; do not infer halves, dense time or live play."""
    if not isfinite(stride_seconds) or stride_seconds < 1:
        raise ValueError('discovery stride must be finite and at least one second')
    if not isfinite(min_confidence) or not 0 <= min_confidence <= 1:
        raise ValueError('OCR confidence cutoff must be between 0 and 1')
    try:
        n_frames, fps = probe_video(video, ffprobe)
    except subprocess.TimeoutExpired as exc:
        raise ValueError('Video metadata probe timed out') from exc
    if n_frames < 1:
        raise ValueError('Video must contain at least one frame')
    stride = max(1, round(stride_seconds*fps))
    samples, stream = [], iter_video_samples(video, n_frames, stride, ffmpeg)
    try:
        for frame, image, width, height in stream:
            candidates = clock_candidates(_sparse_ocr(image, tesseract), width, height, min_confidence)
            samples.append({'frame': frame, 'candidates': candidates})
            if len(samples) == 1 or len(samples) % 10 == 0:
                print('Scanned {} / {} full-frame clock samples'.format(len(samples), ceil(n_frames/stride)), flush=True)
    finally:
        stream.close()
    segments = clock_segments(samples, fps, stride)
    return {'schema_version': 1, 'method': 'automatic_sparse_full_frame_tesseract',
            'frame_count': n_frames, 'fps': fps, 'sample_stride_frames': stride,
            'settings': {'stride_seconds': stride_seconds, 'min_confidence': min_confidence,
                         'minimum_segment_readings': 3, 'minimum_box_iou': .5,
                         'progression_tolerance_seconds': 1.0, 'maximum_missed_samples': 1},
            'parameter_provenance': 'Engineering defaults or caller values; not calibrated correctness probabilities. Tune only on permitted external data.',
            'sample_count': len(samples),
            'samples_with_clock_candidate': sum(bool(s['candidates']) for s in samples),
            'samples_with_multiple_candidates': sum(len(s['candidates']) > 1 for s in samples),
            'candidate_segment_count': len(segments), 'samples': samples, 'segments': segments,
            'ready_for_fusion': False, 'live_verified': False, 'accuracy_measured': False,
            'half_assignment_included': False, 'dense_clock_included': False,
            'warning': 'Candidate discovery only. No dense alignment, half assignment, possession evidence or replay verification. A replay may carry a progressing live clock.'}
''',
    'gap_solver.clock_ocr': r'''"""Optional FFmpeg + Tesseract OCR, entirely local. No model/API uploads."""
import csv
import io
import json
import subprocess
import tempfile
from fractions import Fraction
from math import ceil, isfinite
from pathlib import Path

from .clock_sync import ClockRead, parse_clock

# Approximate crop layouts, NOT time offsets. Verify on original-resolution video locally.
PRESETS = {'broadcast': (0.082, 0.155, 0.084, 0.073),
           'tactical': (0.101, 0.019, 0.057, 0.049)}


def clock_from_tsv(tsv):
    tokens = []
    reader = csv.DictReader(io.StringIO(tsv.lstrip('\ufeff')), delimiter='\t')
    if not {'level', 'conf', 'text'}.issubset(reader.fieldnames or []):
        raise ValueError('Tesseract did not return TSV columns level/conf/text. '
                         'This is an OCR-output format error, not an unreadable clock.')
    for row in reader:
        if row.get('level') == '5' and (row.get('text') or '').strip():
            confidence = float(row.get('conf', -1))
            if isfinite(confidence) and 0 <= confidence <= 100:
                tokens.append((row['text'].strip(), confidence / 100))
    if not tokens:
        return '', 0.0
    text = ''.join(t[0] for t in tokens)
    if parse_clock(text) is None:
        return '', 0.0
    return text, min(t[1] for t in tokens)


def ocr_summary(reads, min_confidence=.7):
    """Requested-clip statistics, including unreadable crops as zero (not filtered out)."""
    if not 0 <= min_confidence <= 1:
        raise ValueError('OCR confidence cutoff must be between 0 and 1')
    scores=[]
    parsed=accepted=0
    for reading in reads:
        if not isfinite(reading.confidence) or not 0 <= reading.confidence <= 1:
            raise ValueError('invalid OCR confidence')
        valid=parse_clock(reading.text) is not None
        parsed += valid
        accepted += valid and reading.confidence >= min_confidence
        scores.append(reading.confidence if valid else 0.0)
    scores.sort()
    def percentile(fraction):
        if not scores:
            return None
        index=fraction*(len(scores)-1)
        low=int(index)
        high=min(low+1,len(scores)-1)
        return scores[low]+(scores[high]-scores[low])*(index-low)
    p01=percentile(.01)
    return {'samples':len(reads),'parsed':parsed,'unreadable':len(reads)-parsed,
            'accepted_by_score':accepted,'cutoff':min_confidence,'p01_all':p01,
            'median_all':percentile(.5),'minimum_all':scores[0] if scores else None,
            'p01_above_half':p01 is not None and p01 > .5,
            'retried':sum(r.attempts > 1 for r in reads),
            'recovered':sum(r.attempts > 1 and parse_clock(r.text) is not None
                            and r.confidence >= min_confidence for r in reads),
            'conflicts':sum(r.method == 'conflict' for r in reads)}


def preprocessing_filter(source):
    """Overlay polarity is source-specific; add a modest light border for segmentation."""
    if source not in PRESETS:
        raise ValueError('unknown camera source')
    invert = 'negate,' if source == 'tactical' else ''
    return 'format=gray,' + invert + 'pad=iw+24:ih+24:12:12:color=white'


def select_clock_candidate(candidates, min_confidence):
    """Keep measured scores; disagreeing eligible treatments make a sample missing."""
    valid = [(text, confidence, method) for method, text, confidence in candidates
             if parse_clock(text) is not None]
    eligible = [candidate for candidate in valid if candidate[1] >= min_confidence]
    if len({parse_clock(candidate[0]) for candidate in eligible}) > 1:
        return '', 0.0, 'conflict'
    return max(eligible or valid, key=lambda candidate: candidate[1]) if valid else ('', 0.0, 'unreadable')


def read_clock_image(image, tesseract='tesseract'):
    # Explicit parameter avoids depending on an optional tessdata/configs/tsv file.
    tsv = _run([tesseract, str(image), 'stdout', '-l', 'eng', '--oem', '1', '--psm', '7',
                '-c', 'tessedit_char_whitelist=0123456789:+',
                '-c', 'tessedit_create_tsv=1'], 30)
    return clock_from_tsv(tsv)


def read_clock_with_retries(image, source, min_confidence=.7,
                            ffmpeg='ffmpeg', tesseract='tesseract'):
    """Retry weak processed crops with restored original polarity and a binary image."""
    primary = read_clock_image(image, tesseract)
    if parse_clock(primary[0]) is not None and primary[1] >= min_confidence:
        return primary[0], primary[1], 'primary', 1
    # The input has preprocessing_filter's 12-pixel border. Undo it and its
    # tactical inversion exactly, preserving the original enlarged crop.
    restore = 'crop=iw-24:ih-24:12:12' + (',negate' if source == 'tactical' else '')
    with tempfile.TemporaryDirectory(prefix='local-clock-retry-') as directory:
        raw, binary = Path(directory)/'unprocessed.png', Path(directory)/'thresholded.png'
        filters = ('[0:v]split=2[a][b];[a]' + restore + '[raw];'
                   "[b]lut=y='if(lt(val,128),0,255)'[binary]")
        _run([ffmpeg, '-hide_banner', '-loglevel', 'error', '-i', str(image),
              '-filter_complex', filters, '-map', '[raw]', '-frames:v', '1', '-update', '1', str(raw),
              '-map', '[binary]', '-frames:v', '1', '-update', '1', str(binary)], 60)
        candidates = [('primary', *primary),
                      ('unprocessed', *read_clock_image(raw, tesseract)),
                      ('thresholded', *read_clock_image(binary, tesseract))]
    return (*select_clock_candidate(candidates, min_confidence), 3)


def check_clock_image(image, source, ffmpeg='ffmpeg', tesseract='tesseract'):
    """Compare raw and preprocessed OCR on one local image without a video rescan."""
    raw = read_clock_image(image, tesseract)
    with tempfile.TemporaryDirectory(prefix='local-ocr-check-') as d:
        processed = Path(d)/'processed.png'
        _run([ffmpeg, '-hide_banner', '-loglevel', 'error', '-i', str(image),
              '-vf', preprocessing_filter(source), '-frames:v', '1', '-update', '1',
              str(processed)], 60)
        improved = read_clock_image(processed, tesseract)
    return raw, improved


def crop_filter(roi, start, end, stride):
    x, y, width, height = roi
    if (any(not isfinite(v) for v in roi) or min(x, y) < 0 or min(width, height) <= 0
            or x + width > 1 or y + height > 1 or start < 0 or end <= start or stride < 1):
        raise ValueError('invalid normalised clock ROI, frame range or stride')
    return ("select='gte(n,{})*lt(n,{})*not(mod(n-{},{}))',"
            'crop=iw*{}:ih*{}:iw*{}:ih*{},scale=iw*4:ih*4,format=gray').format(
                start, end, start, stride, width, height, x, y)


def _run(command, timeout):
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
    except FileNotFoundError as exc:
        raise ValueError('Executable not found: {}. Install it locally or pass its path.'.format(command[0])) from exc
    if result.returncode:
        raise ValueError('{} failed: {}'.format(Path(command[0]).name, result.stderr[-2000:]))
    return result.stdout


def probe_video(video, ffprobe='ffprobe'):
    result = json.loads(_run([ffprobe, '-v', 'error', '-select_streams', 'v:0',
                              '-show_entries', 'stream=width,height,r_frame_rate,avg_frame_rate,nb_frames',
                              '-of', 'json', str(video)], 60))
    if not result.get('streams'):
        raise ValueError('No video stream')
    stream = result['streams'][0]
    dimensions = [str(stream.get(field, '')) for field in ('width', 'height')]
    if (not all(value.isdigit() and int(value) > 0 for value in dimensions)
            or int(dimensions[0])*int(dimensions[1]) > 40000000):
        raise ValueError('Invalid or unsupported video dimensions')
    fps = float(Fraction(stream['avg_frame_rate']))
    if abs(fps - 25) > 1e-6 or abs(float(Fraction(stream['r_frame_rate'])) - fps) > 1e-6:
        raise ValueError('Prototype requires the reference 25 fps export; do not resample to force alignment.')
    if not str(stream.get('nb_frames', '')).isdigit():
        raise ValueError('Container frame count unavailable; verify the reference export before using it.')
    return int(stream['nb_frames']), fps


def extract_clock(video, source, half, start, end, stride=5, roi=None,
                  ffmpeg='ffmpeg', ffprobe='ffprobe', tesseract='tesseract', preview=None,
                  min_confidence=.7):
    if source not in PRESETS or half not in (1, 2):
        raise ValueError('source must be tactical/broadcast and half must be 1/2')
    if not 0 <= min_confidence <= 1:
        raise ValueError('OCR confidence cutoff must be between 0 and 1')
    n_frames, fps = probe_video(video, ffprobe)
    if not 0 <= start < end <= n_frames:
        raise ValueError('Selected frame interval is outside the video')
    expression = (crop_filter(roi or PRESETS[source], start, end, stride)
                  + ',' + preprocessing_filter(source))
    samples = ceil((end - start) / stride)
    reads = []
    with tempfile.TemporaryDirectory(prefix='local-clock-') as directory:
        pattern = str(Path(directory) / '%09d.png')
        _run([ffmpeg, '-hide_banner', '-loglevel', 'error', '-i', str(video), '-an',
              '-vf', expression, '-fps_mode', 'vfr', '-frames:v', str(samples),
              '-start_number', '0', pattern], 3600)
        images = sorted(Path(directory).glob('*.png'))
        if len(images) != samples:
            raise ValueError('Decoded sample count differs from reference indices; refusing to pad/trim')
        if preview is not None and images:
            # A local clock crop only, never part of an uploaded or public deliverable.
            destination = Path(preview)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(images[0].read_bytes())
        for i, image in enumerate(images):
            text, confidence, method, attempts = read_clock_with_retries(
                image, source, min_confidence, ffmpeg, tesseract)
            reads.append(ClockRead(start + i * stride, text, confidence, half, method, attempts))
            if (i + 1) % 100 == 0:
                print('Read {} / {} local clock crops'.format(i + 1, samples), flush=True)
    return reads, n_frames, fps
''',
    'gap_solver.clock_sync': r'''"""Clock-only candidate mapping. A matching clock is NOT proof of live footage."""
import re
from bisect import bisect_left
from dataclasses import dataclass
from math import ceil, floor, isfinite
from typing import Optional


def parse_clock(text):
    text = re.sub(r'\s+', '', text)
    match = re.fullmatch(r'(?:(45|90)\+)?(\d{1,3}):(\d{2})', text)
    if not match:
        return None
    base, minutes, seconds = match.groups()
    if int(seconds) >= 60 or int(minutes) > 150:
        return None
    return (int(base or 0) + int(minutes)) * 60 + int(seconds)


@dataclass(frozen=True)
class ClockRead:
    frame: int
    text: str
    confidence: float
    half: int
    method: str = 'primary'
    attempts: int = 1


@dataclass(frozen=True)
class ClockTime:
    seconds: float
    uncertainty_s: float
    half: int
    segment: int


@dataclass(frozen=True)
class Alignment:
    broadcast_frame: Optional[int] = None
    uncertainty_s: Optional[float] = None
    status: str = 'no_tactical_clock'


def dense_clock(reads, n_frames, fps=25.0, min_confidence=0.7, max_sample_gap_s=0.5):
    """Infer per-frame match time only BETWEEN consistent second-tick anchors.

    Readings bracket each clock tick; the midpoint is an estimate with an explicit
    interval-width uncertainty. At least three consistent ticks per run are required.
    Unreadable/weak samples can be skipped only within max_sample_gap_s between
    accepted observations; at stride 5 / 25 fps this tolerates one missed sample.
    No extrapolation, no filling frozen clocks and no crossing clock resets/cuts.
    """
    if n_frames < 0 or not isfinite(fps) or fps <= 0 or max_sample_gap_s <= 0:
        raise ValueError('invalid clock dimensions')
    if not 0 <= min_confidence <= 1:
        raise ValueError('invalid OCR confidence threshold')
    result, runs, run = [None] * n_frames, [], []
    last_frame = -1
    for reading in reads:
        if (reading.frame <= last_frame or not 0 <= reading.frame < n_frames
                or reading.half not in (1, 2) or not isfinite(reading.confidence)
                or not 0 <= reading.confidence <= 1):
            raise ValueError('clock reads need ordered frame IDs, half 1/2, confidence 0..1')
        last_frame = reading.frame
        seconds = parse_clock(reading.text)
        if seconds is None or reading.confidence < min_confidence:
            if run and reading.half != run[-1][0].half:
                runs.append(run)
                run = []
            continue
        if run:
            previous, prev_seconds = run[-1]
            dt = (reading.frame - previous.frame) / fps
            dc = seconds - prev_seconds
            if (reading.half != previous.half or dt > max_sample_gap_s
                    or dc < 0 or abs(dc - dt) > 1.05):
                runs.append(run)
                run = []
        run.append((reading, seconds))
    if run:
        runs.append(run)
    segment = 0
    for run in runs:
        ticks = []
        for (a, sa), (b, sb) in zip(run, run[1:]):
            if sb - sa == 1:
                tick_frame = (a.frame + b.frame) / 2
                uncertainty = (b.frame - a.frame + 1) / (2 * fps)
                ticks.append((tick_frame, sb, uncertainty, b.half))
        pieces, piece = [], []
        for a, b in zip(ticks, ticks[1:]):
            fa, sa, ua, half = a
            fb, sb, ub, _ = b
            elapsed = (fb - fa) / fps
            if sb - sa != 1 or not 0.75 <= elapsed <= 1.25:
                if piece:
                    pieces.append(piece)
                piece = []
                continue
            if not piece:
                piece = [a]
            piece.append(b)
        if piece:
            pieces.append(piece)
        for piece in pieces:
            if len(piece) < 3:
                continue
            for a, b in zip(piece, piece[1:]):
                fa, sa, ua, half = a
                fb, sb, ub, _ = b
                for frame in range(max(0, ceil(fa)), min(n_frames, floor(fb) + 1)):
                    fraction = (frame - fa) / (fb - fa)
                    result[frame] = ClockTime(sa + fraction, max(ua, ub), half, segment)
            segment += 1
    return result


def validate_timeline(timeline, fps=25.0):
    """Fail on corrupted dense CSV/API inputs rather than sorting away contradictions."""
    previous, previous_frame, active = None, None, None
    seen = set()
    for frame, clock in enumerate(timeline):
        if clock is None:
            active = None
            previous = None
            continue
        if (clock.half not in (1, 2) or clock.segment < 0 or not isfinite(clock.seconds)
                or clock.seconds < 0 or not isfinite(clock.uncertainty_s) or clock.uncertainty_s < 0):
            raise ValueError('invalid dense clock')
        if active != clock.segment:
            if clock.segment in seen:
                raise ValueError('dense clock segment reused after a gap/reset')
            seen.add(clock.segment)
            active, previous = clock.segment, None
        if previous is not None:
            rate = (clock.seconds - previous.seconds) * fps / (frame - previous_frame)
            if clock.half != previous.half or not .79 <= rate <= 1.35:
                raise ValueError('dense clock must progress consistently within one half/segment')
        previous, previous_frame = clock, frame


def align_clocks(tactical, broadcast, max_uncertainty_s=0.25, broadcast_fps=25.0):
    """Reject repeated clock candidates instead of arbitrarily selecting a replay."""
    if (not isfinite(broadcast_fps) or broadcast_fps <= 0
            or not isfinite(max_uncertainty_s) or max_uncertainty_s <= 0):
        raise ValueError('invalid alignment limits')
    validate_timeline(tactical)
    validate_timeline(broadcast, broadcast_fps)
    groups = {}
    for frame, clock in enumerate(broadcast):
        if clock is not None:
            groups.setdefault((clock.half, clock.segment), []).append((clock.seconds, frame, clock))
    index = []
    for (half, _), rows in groups.items():
        rows.sort()
        index.append((half, [r[0] for r in rows], rows))
    result = []
    tolerance = 0.51 / broadcast_fps
    for clock in tactical:
        if clock is None:
            result.append(Alignment())
            continue
        candidates = []
        for half, times, rows in index:
            if half != clock.half or not times[0] - tolerance <= clock.seconds <= times[-1] + tolerance:
                continue
            pos = bisect_left(times, clock.seconds)
            choices = rows[max(0, pos - 1):min(len(rows), pos + 1)]
            candidate = min(choices, key=lambda r: abs(r[0] - clock.seconds))
            error = abs(candidate[0] - clock.seconds)
            if error <= tolerance:
                candidates.append((candidate, error))
        if len(candidates) > 1:
            result.append(Alignment(status='duplicate_clock_candidates'))
        elif not candidates:
            result.append(Alignment(status='no_broadcast_clock_match'))
        else:
            (_, frame, other), error = candidates[0]
            uncertainty = clock.uncertainty_s + other.uncertainty_s + error
            if uncertainty > max_uncertainty_s + 1e-9:
                result.append(Alignment(uncertainty_s=uncertainty, status='timing_uncertain'))
            else:
                result.append(Alignment(frame, uncertainty, 'clock_candidate'))
    return result
''',
    'gap_solver.core': r'''"""Conservative team-control evidence and offline gap handling. No learned probabilities."""
from collections import Counter
from dataclasses import dataclass
from math import ceil, hypot, isfinite
from typing import List, Optional


@dataclass(frozen=True)
class Frame:
    period: int = 1  # 0 = outside grading; 1/2 = halves
    ball_x: Optional[float] = None  # metres
    ball_y: Optional[float] = None
    home_distance: Optional[float] = None
    away_distance: Optional[float] = None
    tag_team: str = ''  # possession-oriented, NOT merely the tag's named team
    restart_hint: bool = False
    dead_evidence: bool = False  # algorithmic evidence or explicitly published context
    dead_source: str = ''  # provenance; never inferred from missing tracking

    @property
    def ball_observed(self):
        return (self.ball_x is not None and self.ball_y is not None
                and isfinite(self.ball_x) and isfinite(self.ball_y))


@dataclass(frozen=True)
class Config:
    fps: float = 25.0
    control_distance_m: float = 2.0
    distance_margin_m: float = 0.75
    confirmation_s: float = 0.24
    short_bridge_s: float = 0.6
    tagged_bridge_s: float = 2.0
    interpolation_s: float = 0.4
    max_ball_speed_m_s: float = 35.0

    def validate(self):
        for key, value in vars(self).items():
            if not isinstance(value, (int, float)) or not isfinite(value) or value < 0:
                raise ValueError('invalid config: ' + key)
        if self.fps <= 0 or self.confirmation_s <= 0 or self.control_distance_m <= 0:
            raise ValueError('fps, confirmation_s and control_distance_m must be positive')
        if self.tagged_bridge_s < self.short_bridge_s:
            raise ValueError('tagged_bridge_s must be >= short_bridge_s')


@dataclass(frozen=True)
class Decision:
    label: str = 'X'
    reason: str = 'insufficient_evidence'
    evidence_level: str = 'unresolved'


def _candidate(f, cfg):
    if not f.ball_observed:
        return ''
    distances = (f.home_distance, f.away_distance)
    # Do not interpret a completely missing opposing team as infinitely far away.
    if any(d is None or not isfinite(d) or d < 0 for d in distances):
        return ''
    home, away = distances
    if min(home, away) > cfg.control_distance_m or abs(home - away) < cfg.distance_margin_m:
        return ''
    return 'H' if home < away else 'A'


def _blocks(frames):
    start = 0
    while start < len(frames):
        period = frames[start].period
        end = start + 1
        while end < len(frames) and frames[end].period == period:
            end += 1
        if period:
            yield start, end
        start = end


def infer(frames: List[Frame], cfg: Config = Config(), *, legacy_restart_veto=False) -> List[Decision]:
    """Restart phases block unsupported bridging, not sustained observed candidates.

    legacy_restart_veto reproduces the previous prototype only for ablation.
    Observed proximity remains a heuristic, including during tagged phases.
    """
    cfg.validate()
    if any(f.period not in (0, 1, 2) for f in frames):
        raise ValueError('period must be 0, 1 or 2')
    out = [Decision(reason='ungraded') if f.period == 0 else Decision() for f in frames]
    required = max(1, ceil(cfg.confirmation_s * cfg.fps))
    for low, high in _blocks(frames):
        owner, candidate, run_start, run_length = '', '', low, 0
        for i in range(low, high):
            f = frames[i]
            if f.dead_evidence:
                published = f.dead_source == 'published_pre_kickoff'
                out[i] = Decision('D', f.dead_source or 'upstream_dead_evidence',
                                  'published_metadata' if published else 'upstream')
                owner, candidate, run_length = '', '', 0
                continue
            if f.restart_hint and legacy_restart_veto:
                owner, candidate, run_length = '', '', 0
                out[i] = Decision(reason='restart_ambiguous')
                continue
            if (not legacy_restart_veto and i > low
                    and f.restart_hint != frames[i-1].restart_hint):
                owner, candidate, run_length = '', '', 0
            observed = _candidate(f, cfg)
            if not observed:
                # Reacquisition needs a new confirmed run, even for the old owner.
                # Otherwise one isolated detection after a long gap becomes a false anchor.
                owner, candidate, run_length = '', '', 0
                reason = ('restart_ambiguous' if f.restart_hint else
                          'ball_missing' if not f.ball_observed else 'control_ambiguous')
                out[i] = Decision(reason=reason)
                continue
            if observed == owner:
                out[i] = Decision(owner, 'observed_control', 'direct_heuristic')
                candidate, run_length = '', 0
                continue
            if observed != candidate:
                candidate, run_start, run_length = observed, i, 1
            else:
                run_length += 1
            if run_length >= required:
                owner = observed
                for j in range(run_start, i + 1):
                    out[j] = Decision(owner, 'confirmed_control', 'direct_heuristic')
                candidate, run_length = '', 0
        # Resolve only gaps between DIRECT anchors; never cascade inferred bridges.
        anchors = list(out[low:high])
        i = low
        while i < high:
            if anchors[i - low].label != 'X':
                i += 1
                continue
            start = i
            while i < high and anchors[i - low].label == 'X':
                i += 1
            end = i
            if start == low or end == high:
                continue
            left, right = anchors[start - low - 1].label, anchors[end - low].label
            if left not in ('H', 'A') or left != right:
                continue
            if any(f.restart_hint or f.dead_evidence for f in frames[start:end]):
                continue
            tags = [f.tag_team for f in frames[start:end]]
            # Conflicting automatic evidence blocks even the short bridge.
            if any(t in ('H', 'A', 'CONFLICT') and t != left for t in tags):
                continue
            duration = (end - start) / cfg.fps
            if duration <= cfg.short_bridge_s:
                reason = 'short_same_team_bridge'
            elif duration <= cfg.tagged_bridge_s and all(t == left for t in tags):
                reason = 'tag_supported_bridge'
            else:
                continue
            for j in range(start, end):
                out[j] = Decision(left, reason, 'inferred_heuristic')
    return out


def interpolate_ball(frames: List[Frame], cfg: Config = Config()):
    """Diagnostic estimates only. Does not mutate frames or infer control."""
    cfg.validate()
    estimates = [None] * len(frames)
    for low, high in _blocks(frames):
        left = None
        for right in range(low, high):
            if not frames[right].ball_observed:
                continue
            if left is not None and right > left + 1:
                missing = right - left - 1
                segment = frames[left:right + 1]
                a, b = frames[left], frames[right]
                speed = hypot(b.ball_x - a.ball_x, b.ball_y - a.ball_y) * cfg.fps / (right - left)
                if (missing / cfg.fps <= cfg.interpolation_s and speed <= cfg.max_ball_speed_m_s
                        and not any(f.restart_hint or f.dead_evidence for f in segment)):
                    for j in range(left + 1, right):
                        t = (j - left) / (right - left)
                        estimates[j] = (a.ball_x + t * (b.ball_x - a.ball_x),
                                        a.ball_y + t * (b.ball_y - a.ball_y))
            left = right
    return estimates


def unresolved_intervals(frames, decisions):
    result = []
    for low, high in _blocks(frames):
        i = low
        while i < high:
            if decisions[i].label != 'X':
                i += 1
                continue
            start = i
            while i < high and decisions[i].label == 'X':
                i += 1
            left = decisions[start - 1].label if start > low else None
            right = decisions[i].label if i < high else None
            if any(f.restart_hint for f in frames[start:i]):
                cause = 'restart_ambiguous'
            elif left in ('H', 'A') and right in ('H', 'A') and left != right:
                cause = 'opposing_anchors'
            elif left is None or right is None:
                cause = 'unbounded_gap'
            else:
                cause = 'insufficient_or_conflicting_evidence'
            result.append({'start_frame': start, 'end_frame_exclusive': i,
                           'period': frames[start].period, 'cause': cause,
                           'left_anchor': left, 'right_anchor': right,
                           'missing_ball_frames': sum(not f.ball_observed for f in frames[start:i]),
                           'next_step': 'local_algorithmic_video_recovery'})
    return result


def summary(frames, decisions):
    active = [(f, d) for f, d in zip(frames, decisions) if f.period]
    n = len(active)
    counts = Counter(d.label for _, d in active)
    missing = sum(not f.ball_observed for f, _ in active)
    inferred = sum(d.evidence_level in ('inferred_heuristic', 'fused_heuristic','external_model') for _, d in active)
    return {'total_frames': len(frames), 'active_frames': n,
            'missing_ball_frames': missing, 'missing_ball_fraction': missing / n if n else 0,
            'published_dead_frames': sum(f.dead_source == 'published_pre_kickoff' and f.dead_evidence
                                         for f, _ in active),
            'labels': {label: counts[label] for label in 'HADX'},
            'resolved_fraction': (n - counts['X']) / n if n else 0,
            'inferred_frames': inferred,
            'missing_ball_assigned_team_frames': sum(not f.ball_observed and d.label in 'HA' for f, d in active),
            'reason_counts': dict(Counter(d.reason for _, d in active)),
            'accuracy_measured': False,
            'warning': 'Coverage is not correctness. Heuristic levels are not probabilities.'}
''',
    'gap_solver.dfl_motion': r'''"""Motion-only reconstruction for explicitly seen DFL regression data, never fresh testing."""
from array import array
import xml.etree.ElementTree as ET
import numpy as np
from .motion import motion_frame


def load_dfl_motion(metadata_path,tracking_path,base):
    general=ET.parse(metadata_path).getroot().find('.//General')
    home,away=general.get('HomeTeamId'),general.get('GuestTeamId')
    if not home or not away or home==away:raise ValueError('invalid DFL team identities')
    pitch=base.notes['source_pitch_m'];tracks=[];current=None;sections={'firstHalf':1,'secondHalf':2}
    for event,element in ET.iterparse(tracking_path,events=('start','end')):
        tag=element.tag.rsplit('}',1)[-1]
        if event=='start' and tag=='FrameSet':
            team=element.get('TeamId');period=sections.get(element.get('GameSection'))
            current=dict(side=int(team==away),period=period,person=element.get('PersonId'),n=array('i'),x=array('f'),y=array('f')) if team in (home,away) and period else None
        elif event=='end' and tag=='Frame':
            if current is not None:
                current['n'].append(int(element.get('N')))
                for axis in ('x','y'):
                    raw=element.get(axis.upper());current[axis].append(float(raw) if raw and raw.lower() not in ('nan','none') else float('nan'))
            element.clear()
        elif event=='end' and tag=='FrameSet':
            if current is not None and current['n']:tracks.append(current)
            current=None;element.clear()
    identities=[sorted({r['person'] for r in tracks if r['side']==side}) for side in (0,1)]
    if any(None in ids or len(ids)>64 for ids in identities):raise ValueError('unsupported DFL player identities')
    xy=[np.full((len(base.periods),len(ids),2),np.nan,dtype=np.float32) for ids in identities]
    seen=set()
    for row in tracks:
        at=np.flatnonzero(base.periods==row['period']);numbers=base.source_frames[at]
        native=np.asarray(row['n']);indices=np.searchsorted(numbers,native)
        if (indices>=len(numbers)).any() or not np.array_equal(numbers[indices],native):raise ValueError('DFL player grid differs from frozen baseline')
        if len(native)>1 and (np.diff(native)<=0).any():raise ValueError('DFL track indices do not increase')
        side=row['side'];person=identities[side].index(row['person']);selected=at[indices]
        key=(side,person,row['period'])
        if key in seen and np.isfinite(xy[side][selected,person]).any():raise ValueError('overlapping DFL player tracks')
        seen.add(key)
        xy[side][selected,person,0]=(np.asarray(row['x'])/pitch[0]+.5)*105.3
        xy[side][selected,person,1]=(np.asarray(row['y'])/pitch[1]+.5)*68
    result=[]
    for i,(period,ball) in enumerate(zip(base.periods,base.ball_xy)):
        points=[];ids=[]
        for side in (0,1):
            selected=np.flatnonzero(np.isfinite(xy[side][i]).all(axis=1))
            points.append(tuple(map(tuple,xy[side][i,selected])));ids.append(tuple(map(int,selected)))
        result.append(motion_frame(int(period),tuple(ball) if np.isfinite(ball).all() else None,*points,*ids,
            ball_native_observation=None,ball_provenance='available_freshness_unverified'))
    return result
''',
    'gap_solver.external': r'''"""Strict IDSSE adapter for external evaluation. Target attributes never become features."""
from array import array
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np
from .core import Frame


@dataclass
class ExternalMatch:
    match_id: str
    periods: object
    source_frames: object
    ball_xy: object
    distances: object
    player_counts: object
    reference: object
    notes: dict

    def frames(self):
        def number(x):
            return float(x) if np.isfinite(x) else None
        return [Frame(period=int(p),ball_x=number(b[0]),ball_y=number(b[1]),
                      home_distance=number(d[0]),away_distance=number(d[1]))
                for p,b,d in zip(self.periods,self.ball_xy,self.distances)]


def _coordinate(value):
    if value is None or value.lower() in ('','nan','none'):
        return float('nan')
    result=float(value)
    if not np.isfinite(result):
        raise ValueError('nonfinite external coordinate')
    return result


def reference_code(status,possession):
    if status=='0':
        return 2
    if status=='1' and possession in ('1','2'):
        return int(possession)-1
    return 3


def load_external(metadata_path,tracking_path):
    metadata=ET.parse(metadata_path).getroot()
    general=metadata.find('.//General')
    if general is None:
        raise ValueError('external metadata lacks General record')
    home,away=general.get('HomeTeamId'),general.get('GuestTeamId')
    if not home or not away or home==away:
        raise ValueError('external metadata needs distinct home and away identities')
    match_id=general.get('MatchId','unknown')
    records=[]
    current=None
    pitch=None
    excluded=Counter()
    raw_states,raw_possessions=Counter(),Counter()
    previous_last={}
    sections={'firstHalf':1,'secondHalf':2}
    for event,element in ET.iterparse(tracking_path,events=('start','end')):
        tag=element.tag.rsplit('}',1)[-1]
        if event=='start' and tag=='FrameSet':
            section=element.get('GameSection')
            team=element.get('TeamId','')
            kind='ball' if team.lower()=='ball' else 'player' if team in (home,away) else None
            if section not in sections or kind is None:
                excluded[str(section)+':'+str(team)]+=1
                current=None
            else:
                source_match=element.get('MatchId')
                if source_match and match_id!='unknown' and source_match!=match_id:
                    raise ValueError('tracking match ID disagrees with external metadata')
                current=dict(period=sections[section],team=team,person=element.get('PersonId',team),kind=kind,
                             n=array('i'),x=array('f'),y=array('f'),target=array('B'),first_t=None,last_t=None)
        elif event=='end' and tag=='PitchSize':
            candidate=(float(element.get('X','0')),float(element.get('Y','0')))
            if not all(np.isfinite(v) and v>0 for v in candidate) or pitch is not None and candidate!=pitch:
                raise ValueError('invalid/inconsistent external pitch dimensions')
            pitch=candidate
            element.clear()
        elif event=='end' and tag=='Frame':
            if current is not None:
                n=int(element.get('N','-1'))
                if n<0 or current['n'] and n<=current['n'][-1]:
                    raise ValueError('external frame IDs must increase within each track')
                current['n'].append(n)
                current['x'].append(_coordinate(element.get('X')))
                current['y'].append(_coordinate(element.get('Y')))
                timestamp=element.get('T')
                if timestamp:
                    current['first_t']=current['first_t'] or timestamp
                    current['last_t']=timestamp
                if current['kind']=='ball':
                    status,possession=element.get('BallStatus',''),element.get('BallPossession','')
                    raw_states[status]+=1;raw_possessions[possession]+=1
                    current['target'].append(reference_code(status,possession))
            element.clear()
        elif event=='end' and tag=='FrameSet':
            if current is not None and current['n']:
                key=(current['period'],current['team'],current['person'])
                if key in previous_last and current['n'][0]<=previous_last[key]:
                    raise ValueError('external track reuses original frame IDs')
                previous_last[key]=current['n'][-1]
                if current['first_t'] and len(current['n'])>1:
                    duration=(datetime.fromisoformat(current['last_t'])-datetime.fromisoformat(current['first_t'])).total_seconds()
                    expected=(current['n'][-1]-current['n'][0])/25
                    if abs(duration-expected)>.01:
                        raise ValueError('external timestamps disagree with canonical 25 Hz frame grid')
                records.append(current)
            current=None
            element.clear()
    if pitch is None or not records or not any(r['kind']=='ball' for r in records):
        raise ValueError('external tracking lacks pitch dimensions or ball records')
    periods=[];numbers=[];balls=[];distances=[];counts=[];references=[]
    for period in sorted({r['period'] for r in records}):
        rows=[r for r in records if r['period']==period]
        first=min(r['n'][0] for r in rows);last=max(r['n'][-1] for r in rows)
        n=last-first+1
        if n>1000000:
            raise ValueError('unreasonable external period frame range')
        xy=np.full((n,2),np.nan,dtype=np.float32)
        target=np.full(n,3,dtype=np.uint8)
        ball_seen=np.zeros(n,dtype=bool)
        for r in rows:
            if r['kind']!='ball':
                continue
            indices=np.asarray(r['n'],dtype=np.int64)-first
            if ball_seen[indices].any():
                raise ValueError('duplicate external ball frame')
            ball_seen[indices]=True
            xy[indices,0]=(np.asarray(r['x'])/pitch[0]+.5)*105.3
            xy[indices,1]=(np.asarray(r['y'])/pitch[1]+.5)*68
            target[indices]=np.asarray(r['target'])
        minimum=np.full((n,2),np.inf,dtype=np.float32)
        visible=np.zeros((n,2),dtype=np.uint8)
        for r in rows:
            if r['kind']!='player':
                continue
            side=0 if r['team']==home else 1
            indices=np.asarray(r['n'],dtype=np.int64)-first
            px=(np.asarray(r['x'])/pitch[0]+.5)*105.3
            py=(np.asarray(r['y'])/pitch[1]+.5)*68
            seen=np.isfinite(px)&np.isfinite(py)
            visible[indices[seen],side]+=1
            observed=seen&np.isfinite(xy[indices]).all(axis=1)
            selected=indices[observed]
            d=np.hypot(px[observed]-xy[selected,0],py[observed]-xy[selected,1])
            minimum[selected,side]=np.minimum(minimum[selected,side],d)
        minimum[~np.isfinite(minimum)]=np.nan
        periods.append(np.full(n,period,dtype=np.uint8));numbers.append(np.arange(first,last+1,dtype=np.int32))
        balls.append(xy);distances.append(minimum);counts.append(visible);references.append(target)
    notes=dict(fps=25,canonical_pitch_m=[105.3,68],source_pitch_m=list(pitch),
               raw_status_counts=dict(raw_states),raw_possession_counts=dict(raw_possessions),
               excluded_track_sections=dict(excluded),reference_type='provider reference; not competition gold',
               label_features_excluded=['BallStatus','BallPossession','events','match/team identities'],
               unknown_reference_preserved=True)
    return ExternalMatch(match_id,np.concatenate(periods),np.concatenate(numbers),np.concatenate(balls),
                         np.concatenate(distances),np.concatenate(counts),np.concatenate(references),notes)


def save_cache(match,prefix):
    prefix=Path(prefix);prefix.parent.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(str(prefix)+'.features.npz',periods=match.periods,source_frames=match.source_frames,
                        ball_xy=match.ball_xy,distances=match.distances,player_counts=match.player_counts)
    np.savez_compressed(str(prefix)+'.reference.npz',periods=match.periods,source_frames=match.source_frames,reference=match.reference)
    Path(str(prefix)+'.metadata.json').write_text(json.dumps(dict(match_id=match.match_id,notes=match.notes),indent=2)+'\n',encoding='utf-8')


def load_cache(prefix):
    prefix=str(prefix)
    meta=json.loads(Path(prefix+'.metadata.json').read_text(encoding='utf-8'))
    with np.load(prefix+'.features.npz',allow_pickle=False) as features,np.load(prefix+'.reference.npz',allow_pickle=False) as reference:
        for key in ('periods','source_frames'):
            if not np.array_equal(features[key],reference[key]):
                raise ValueError('external feature/reference frame grids disagree')
        return ExternalMatch(meta['match_id'],features['periods'],features['source_frames'],features['ball_xy'],
                             features['distances'],features['player_counts'],reference['reference'],meta['notes'])
''',
    'gap_solver.frozen_protocol': r'''"""Integrity and split checks before final external evaluation; no model fitting."""
import hashlib
import json
from pathlib import Path
from .tactical import Policy,PortableTree


def artifact_digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode('utf-8')).hexdigest()


def load_frozen(root,code_directory):
    root,code_directory=Path(root),Path(code_directory)
    artifact=json.loads((root/'frozen'/'tactical-selected.json').read_text(encoding='utf-8'))
    manifest=json.loads((root/'frozen'/'freeze-manifest.json').read_text(encoding='utf-8'))
    provenance=json.loads((root/'provenance.json').read_text(encoding='utf-8'))
    if (artifact.get('schema_version')!=1 or not artifact.get('features_exclude_reference_labels')
            or manifest.get('frozen_before_test_scores') is not True
            or artifact_digest(artifact)!=manifest.get('artifact_sha256')):
        raise ValueError('Frozen model/policy integrity failed')
    split=manifest.get('split',{})
    if set(split)!={'development','validation','test'} or split!=provenance.get('split'):
        raise ValueError('Frozen external split differs from acquisition protocol')
    all_ids=[]
    for name,field in [('development','training_matches'),('validation','validation_matches'),('test','test_matches')]:
        ids=split[name]
        if not isinstance(ids,list) or not ids or any(not isinstance(x,str) or not x for x in ids) or artifact.get(field)!=ids:
            raise ValueError('Invalid/changed external match partition')
        all_ids.extend(ids)
    if len(all_ids)!=len(set(all_ids)):
        raise ValueError('External train/validation/test partitions overlap')
    sources=manifest.get('source_sha256',{})
    if not sources:
        raise ValueError('Frozen prediction/evaluation sources are missing')
    for name,expected in sources.items():
        if Path(name).name!=name or not name.endswith('.py'):
            raise ValueError('Invalid frozen source name')
        if hashlib.sha256((code_directory/name).read_bytes()).hexdigest()!=expected:
            raise ValueError('Prediction/evaluation source changed after freezing: '+name)
    PortableTree(artifact['model'])
    Policy(**artifact['policy']).validate()
    return artifact,manifest
''',
    'gap_solver.fusion': r'''"""Quality-gated heuristic votes; these weights are not calibrated probabilities."""
from dataclasses import dataclass
from math import ceil, exp, hypot, isfinite
from statistics import median
from typing import Optional, Tuple

from .core import Decision


@dataclass(frozen=True)
class Scene:
    home: Tuple = ()
    away: Tuple = ()
    ball: Optional[Tuple] = None
    homography_valid: bool = False
    reprojection_error: float = float('inf')


@dataclass(frozen=True)
class Verification:
    accepted: bool = False
    quality: float = 0.0
    reason: str = 'not_verified'


@dataclass(frozen=True)
class Vote:
    decision: Decision
    status: str
    tactical_weight: float
    broadcast_weight: float


def verify_geometry(tactical, broadcast, max_player_error_m=3.0, max_ball_error_m=4.0,
                    max_reprojection_error=3.0):
    """Compare team point sets, not unstable player IDs. Assumes same pitch orientation.

    Broadcast-to-tactical nearest distances tolerate a narrower broadcast view.
    Agreement is a heuristic check, not proof that footage is live.
    """
    for scene in (tactical, broadcast):
        if (not scene.homography_valid or not isfinite(scene.reprojection_error)
                or not 0 <= scene.reprojection_error <= max_reprojection_error):
            return Verification(reason='homography_unreliable')
        points = list(scene.home) + list(scene.away)
        if (len(scene.home) < 3 or len(scene.away) < 3
                or any(len(p) != 2 or not all(isfinite(v) for v in p) for p in points)):
            return Verification(reason='insufficient_player_geometry')
    errors = []
    for first, second in ((tactical.home, broadcast.home), (tactical.away, broadcast.away)):
        distances = [min(hypot(x-a, y-b) for a, b in first) for x, y in second]
        error = median(distances)
        if error > max_player_error_m:
            return Verification(reason='player_geometry_disagrees')
        # Deduplicate overlapping tracklets, then require distinct spatial support.
        def distinct(points):
            unique = []
            for x, y in points:
                if all(hypot(x-a, y-b) > .5 for a, b in unique):
                    unique.append((x, y))
            return unique
        first, second = distinct(first), distinct(second)
        pairs = sorted((hypot(x-a, y-b), i, j)
                       for i,(a,b) in enumerate(first) for j,(x,y) in enumerate(second))
        used_first, used_second = set(), set()
        for distance, i, j in pairs:
            if distance <= max_player_error_m and i not in used_first and j not in used_second:
                used_first.add(i)
                used_second.add(j)
        if len(used_second) < max(3, ceil(.6 * len(second))):
            return Verification(reason='insufficient_distinct_spatial_matches')
        errors.append(error)
    if tactical.ball is not None and broadcast.ball is not None:
        if (not all(isfinite(v) for v in tactical.ball + broadcast.ball)
                or hypot(tactical.ball[0] - broadcast.ball[0],
                         tactical.ball[1] - broadcast.ball[1]) > max_ball_error_m):
            return Verification(reason='ball_geometry_disagrees')
    quality = exp(-max(errors) / max_player_error_m) / (
        1 + max(tactical.reprojection_error, broadcast.reprojection_error))
    return Verification(True, quality, 'geometry_consistent')


def fuse_vote(tactical, broadcast, verification, uncertainty_s,
              max_uncertainty_s=0.25, min_broadcast_weight=0.3, vote_margin=0.2):
    """Retain direct primary disagreements; use trusted secondary for unknown/weak primary."""
    levels = {'direct_heuristic': 1.0, 'upstream': 1.0, 'published_metadata': 1.0,
              'inferred_heuristic': 0.35, 'fused_heuristic': 0.35}
    tw = levels.get(tactical.evidence_level, 0.0) if tactical.label != 'X' else 0.0
    if (not verification.accepted or not isfinite(verification.quality)
            or not 0 <= verification.quality <= 1
            or uncertainty_s is None or not isfinite(uncertainty_s)
            or not 0 <= uncertainty_s <= max_uncertainty_s):
        return Vote(tactical, 'secondary_not_verified', tw, 0.0)
    # Do not propagate an interpolated/bridged broadcast guess as new direct evidence.
    if broadcast.label not in ('H', 'A') or broadcast.evidence_level != 'direct_heuristic':
        return Vote(tactical, 'secondary_no_direct_control', tw, 0.0)
    bw = 0.9 * verification.quality * (1 - 0.5 * uncertainty_s / max_uncertainty_s)
    if tactical.label == 'D':
        return Vote(tactical, 'keep_upstream_stoppage', tw, bw)
    if tw >= 1 and tactical.label != broadcast.label:
        return Vote(tactical, 'conflict_keep_tactical', tw, bw)
    if bw < min_broadcast_weight:
        return Vote(tactical, 'secondary_weight_too_low', tw, bw)
    if tactical.label == 'X':
        return Vote(Decision(broadcast.label, 'broadcast_rescue', 'fused_heuristic'),
                    'broadcast_rescue', tw, bw)
    if tactical.label == broadcast.label:
        return Vote(Decision(tactical.label, 'camera_agreement', tactical.evidence_level),
                    'camera_agreement', tw, bw)
    margin = (bw - tw) / (bw + tw) if bw + tw else 0
    if margin >= vote_margin:
        return Vote(Decision(broadcast.label, 'broadcast_overrides_inferred', 'fused_heuristic'),
                    'broadcast_overrides_inferred', tw, bw)
    return Vote(tactical, 'weak_vote_conflict_keep_tactical', tw, bw)
''',
    'gap_solver.io': r'''"""Local adapters. Match data must remain on the participant's machine."""
import csv
import json
from dataclasses import asdict, replace
from math import hypot, isfinite
from pathlib import Path
import xml.etree.ElementTree as ET

from .core import Config, Frame, interpolate_ball, summary, unresolved_intervals

N_FRAMES = 199319
BLOCKS = [(1, 11185, 90651), (2, 110808, 190197)]  # inclusive, published boundaries
PUBLISHED_PRE_KICKOFF = (110808, 113742)  # half-open; official FAQ: all 2934 frames are D


def apply_published_dead(frames):
    """Apply official reference-export context, never to another recording/game."""
    first, stop = PUBLISHED_PRE_KICKOFF
    if len(frames) != N_FRAMES or any(f.period != 2 for f in frames[first:stop]):
        raise ValueError('published context requires the reference tactical dimensions and half-2 block')
    result = list(frames)
    for i in range(first, stop):
        result[i] = replace(frames[i], dead_evidence=True, dead_source='published_pre_kickoff')
    return result


def _number(value):
    if value is None or str(value).strip().lower() in ('', 'nan', 'none'):
        return None
    n = float(value)
    if not isfinite(n):
        raise ValueError('infinite input is invalid')
    return n


def _bool(value):
    text = str(value).strip().lower()
    if text in ('', '0', 'false', 'none'):
        return False
    if text in ('1', 'true'):
        return True
    raise ValueError('boolean must be true/false or 1/0')


def load_atd(meta_path, raw_path, n_frames=N_FRAMES, blocks=None):
    """Strict 1-based ATD -> 0-based evidence, no legacy IdFrame offsets."""
    blocks = BLOCKS if blocks is None else blocks
    root = ET.parse(meta_path).getroot()
    teams = list(root.iter('Team'))
    if len(teams) != 2 or len({t.get('id') for t in teams}) != 2:
        raise ValueError('expected two distinct teams in metadata')
    ids = [t.get('id') for t in teams]
    names = tuple(t.findtext('Name') or '' for t in teams)
    slots = [p.get('teamId') for p in root.iter('Player')]
    if not slots or any(t not in ids for t in slots):
        raise ValueError('missing or invalid team membership')
    periods = [0] * n_frames
    for period, first, last in blocks:
        for i in range(max(0, first), min(n_frames, last + 1)):
            periods[i] = period
    frames = []
    with open(raw_path, encoding='utf-8-sig') as handle:
        for i, line in enumerate(handle):
            parts = line.strip().split(':')
            if len(parts) != 3 or int(parts[0]) != i + 1 or i >= n_frames:
                raise ValueError('ATD must have ordered, contiguous frame IDs 1..N')
            players = parts[1].split(';')
            if len(players) != len(slots):
                raise ValueError('player slot count differs from metadata at frame ' + str(i))
            ball = parts[2].split(',')
            if len(ball) != 3:
                raise ValueError('expected ball x,y,speed')
            bx, by = _number(ball[0]), _number(ball[1])
            if bx is None or by is None:
                frames.append(Frame(period=periods[i]))
                continue
            bx, by = bx * 105.3, by * 68.0
            nearest = [None, None]
            for slot, player in enumerate(players):
                xyz = player.split(',')
                if len(xyz) != 3:
                    raise ValueError('expected player x,y,speed')
                x, y = _number(xyz[0]), _number(xyz[1])
                if x is None or y is None:
                    continue
                distance = hypot(x * 105.3 - bx, y * 68.0 - by)
                side = ids.index(slots[slot])
                if nearest[side] is None or distance < nearest[side]:
                    nearest[side] = distance
            frames.append(Frame(period=periods[i], ball_x=bx, ball_y=by,
                                home_distance=nearest[0], away_distance=nearest[1]))
    if len(frames) != n_frames:
        raise ValueError('expected {} records; got {}'.format(n_frames, len(frames)))
    return frames, names


def load_tags(path, frames, team_names, fps=25):
    """Soft possession-oriented votes. Set-piece intervals only block bridging."""
    def norm(s):
        return ' '.join((s or '').lower().split())

    mapping = {norm(team_names[0]): 'H', norm(team_names[1]): 'A'}
    # Documented provider spelling variations, not player/match annotations.
    for name, side in zip(team_names, ('H', 'A')):
        if 'barcelona' in norm(name):
            mapping.update({'barcelona': side, 'fc barcelona': side})
        if 'atletic' in norm(name) or 'athletic' in norm(name):
            mapping.update({'atletic club': side, 'athletic club': side})
    attacking = {'build up', 'progression', 'creating chances', 'attacking transition',
                 'long ball', 'ball in final third', 'ball in the box', 'players in the box'}
    defending = {'defending in attacking third', 'defending in middle third',
                 'defending in defensive third', 'defensive transition'}
    votes = [set() for _ in frames]
    restarts = [False] * len(frames)
    for event in ET.parse(path).iter('instance'):
        code = norm(event.findtext('code'))
        tags = {norm(l.findtext('group')): norm(l.findtext('text')) for l in event.findall('label')}
        side = mapping.get(tags.get('team'))
        start_s, end_s = float(event.findtext('start')), float(event.findtext('end'))
        if not isfinite(start_s) or not isfinite(end_s) or end_s < start_s:
            raise ValueError('invalid tagging interval')
        start, end = max(0, round(start_s * fps)), min(len(frames), round(end_s * fps))
        if code in defending and side:
            side = 'A' if side == 'H' else 'H'
        if code not in attacking | defending:
            side = None
        for i in range(start, end):
            if side:
                votes[i].add(side)
            if code == 'set pieces':
                restarts[i] = True
    return [replace(f, tag_team=next(iter(v)) if len(v) == 1 else ('CONFLICT' if v else ''),
                    restart_hint=f.restart_hint or restarts[i])
            for i, (f, v) in enumerate(zip(frames, votes))]


def read_evidence(path):
    frames = []
    with open(path, newline='', encoding='utf-8-sig') as handle:
        for i, row in enumerate(csv.DictReader(handle)):
            if int(row['frame']) != i:
                raise ValueError('evidence frame IDs must be ordered 0..N-1')
            period = int(row['period'])
            tag = row.get('tag_team', '').strip().upper()
            if period not in (0, 1, 2) or tag not in ('', 'H', 'A', 'CONFLICT'):
                raise ValueError('invalid period or tag_team')
            frames.append(Frame(period=period,
                                ball_x=_number(row.get('ball_x_m')),
                                ball_y=_number(row.get('ball_y_m')),
                                home_distance=_number(row.get('home_distance_m')),
                                away_distance=_number(row.get('away_distance_m')),
                                tag_team=tag, restart_hint=_bool(row.get('restart_hint')),
                                dead_evidence=_bool(row.get('dead_evidence'))))
    if not frames:
        raise ValueError('evidence file is empty')
    return frames


def write_outputs(directory, frames, decisions, cfg=Config(), audit_stages=None):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    if len(frames) != len(decisions):
        raise ValueError('frame/decision length mismatch')
    audit_stages = audit_stages or {}
    if audit_stages:
        from .audit import scorer_expanded_labels
        expanded = {name: scorer_expanded_labels(frames, labels) for name, labels in audit_stages.items()}
        final_expanded = scorer_expanded_labels(frames, decisions)
    xy = interpolate_ball(frames, cfg)
    with (directory / 'submission.csv').open('w', newline='', encoding='utf-8') as handle:
        writer = csv.writer(handle, lineterminator='\n')
        writer.writerow(['frame', 'label'])
        writer.writerows((i, d.label) for i, d in enumerate(decisions))
    with (directory / 'diagnostics.csv').open('w', newline='', encoding='utf-8') as handle:
        writer = csv.writer(handle, lineterminator='\n')
        writer.writerow(['frame', 'period', 'label', 'reason', 'evidence_level', 'ball_observed',
                         'estimated_ball_x_m', 'estimated_ball_y_m'] +
                        [column for name in audit_stages for column in (name+'_label', 'scorer_'+name+'_label')] +
                        (['scorer_final_label'] if audit_stages else []))
        for i, (f, d, estimate) in enumerate(zip(frames, decisions, xy)):
            writer.writerow([i, f.period, d.label, d.reason, d.evidence_level,
                             int(f.ball_observed), *(estimate or ('', ''))] +
                            [value for name, labels in audit_stages.items() for value in (labels[i].label, expanded[name][i])] +
                            ([final_expanded[i]] if audit_stages else []))
    report = summary(frames, decisions)
    report['config'] = asdict(cfg)
    report['live_dead_classifier_included'] = False
    for name, obj in [('report.json', report),
                      ('unresolved_intervals.json', unresolved_intervals(frames, decisions))]:
        (directory / name).write_text(json.dumps(obj, indent=2) + '\n', encoding='utf-8')
    return report
''',
    'gap_solver.motion': r'''"""Geometry records that retain player context when ball coordinates are unavailable."""
from dataclasses import dataclass,replace
from math import hypot
from typing import Optional
import xml.etree.ElementTree as ET

from .core import Frame
from .io import N_FRAMES,BLOCKS,_number


@dataclass(frozen=True)
class MotionFrame(Frame):
    home_xy: tuple=()
    away_xy: tuple=()
    home_ids: tuple=()
    away_ids: tuple=()
    geometry_valid: bool=True
    ball_native_observation: Optional[bool]=None
    ball_provenance: str='available_unverified'
    ball_interpolated: bool=False
    ball_sample_time_s: Optional[float]=None
    interpolated: bool=False
    native_frame: Optional[int]=None


def motion_frame(period,ball,home,away,home_ids=(),away_ids=(),**flags):
    home,away=tuple(home),tuple(away)
    bx,by=ball if ball is not None else (None,None)
    if ball is None:
        flags.update(ball_native_observation=False,ball_provenance='missing',ball_interpolated=False,ball_sample_time_s=None)
    def nearest(points):
        return min((hypot(x-bx,y-by) for x,y in points),default=None) if ball is not None else None
    return MotionFrame(period=period,ball_x=bx,ball_y=by,
        home_distance=nearest(home),away_distance=nearest(away),
        home_xy=home,away_xy=away,home_ids=tuple(home_ids),away_ids=tuple(away_ids),**flags)


def load_motion_atd(meta_path,raw_path,quality_path,n_frames=N_FRAMES,blocks=None):
    """Strict local parsing; no tags, labels, fixed D, or freshness assumptions."""
    from .tactical_cli import apply_geometry_quality
    metadata=ET.parse(meta_path).getroot()
    teams=list(metadata.iter('Team'))
    if len(teams)!=2 or len({t.get('id') for t in teams})!=2:
        raise ValueError('motion metadata requires two distinct teams')
    ids=[t.get('id') for t in teams]
    slots=[p.get('teamId') for p in metadata.iter('Player')]
    if not slots or any(side not in ids for side in slots):
        raise ValueError('invalid motion player membership')
    sides=[ids.index(side) for side in slots]
    periods=[0]*n_frames
    for period,first,last in BLOCKS if blocks is None else blocks:
        if period not in (1,2):raise ValueError('invalid motion period')
        for i in range(max(0,first),min(n_frames,last+1)):periods[i]=period
    frames=[]
    with open(raw_path,encoding='utf-8-sig') as handle:
        for i,line in enumerate(handle):
            parts=line.strip().split(':')
            if len(parts)!=3 or int(parts[0])!=i+1 or i>=n_frames:
                raise ValueError('motion ATD must retain contiguous original frame IDs')
            values=parts[1].split(';')
            if len(values)!=len(slots):raise ValueError('motion player slot count differs from metadata')
            points=[[],[]];members=[[],[]]
            for slot,(side,value) in enumerate(zip(sides,values)):
                xyz=value.split(',')
                if len(xyz)!=3:raise ValueError('motion player requires x,y,speed')
                x,y=_number(xyz[0]),_number(xyz[1])
                if x is not None and y is not None:
                    points[side].append((x*105.3,y*68.));members[side].append(slot)
            values=parts[2].split(',')
            if len(values)!=3:raise ValueError('motion ball requires x,y,speed')
            x,y=_number(values[0]),_number(values[1])
            ball=(x*105.3,y*68.) if x is not None and y is not None else None
            frames.append(motion_frame(periods[i],ball,*points,*members,native_frame=i,
                                       ball_sample_time_s=i/25 if ball is not None else None))
    if len(frames)!=n_frames:raise ValueError('motion tracking row count differs from expected source')
    _,valid=apply_geometry_quality(frames,quality_path)
    frames=[f if ok else replace(f,ball_x=None,ball_y=None,home_distance=None,away_distance=None,
             home_xy=(),away_xy=(),home_ids=(),away_ids=(),geometry_valid=False,
             ball_native_observation=False,ball_provenance='missing',ball_interpolated=False,ball_sample_time_s=None)
            for f,ok in zip(frames,valid)]
    return frames,tuple(t.findtext('Name') or '' for t in teams)
''',
    'gap_solver.multicam': r'''"""Local two-camera clock and evidence experiment: python -m gap_solver.multicam demo."""
import argparse
import csv
import json
from collections import Counter, deque
from dataclasses import replace
from math import isfinite
from pathlib import Path
import xml.etree.ElementTree as ET

from .clock_sync import Alignment, ClockRead, ClockTime, align_clocks, dense_clock, validate_timeline
from .core import Frame, infer, summary
from .fusion import Scene, fuse_vote, verify_geometry
from .io import N_FRAMES, _number, apply_published_dead, load_atd, load_tags, write_outputs


def resolve_source_prefix(root, source, source_dir=None):
    """Use existing export folders; never copy or rename match assets."""
    folders = ([Path(source_dir)] if source_dir is not None else
               [Path(root)/source, Path(root)/(source+' cam')])
    prefixes = [folder/('BAR-ATH_'+source) for folder in folders]
    suffixes = ('_atd.xml', '_atd.txt', '_homography.csv')
    complete = [prefix for prefix in prefixes
                if all(Path(str(prefix)+suffix).is_file() for suffix in suffixes)]
    if len(complete) > 1:
        raise ValueError('Multiple {} exports found; choose one with --{}-dir'.format(source, source))
    if not complete:
        missing = [str(prefix)+suffix for prefix in prefixes for suffix in suffixes
                   if not Path(str(prefix)+suffix).is_file()]
        raise ValueError('Missing {} export files: {}'.format(source, '; '.join(missing)))
    return complete[0]


def write_dense_clock(path, clocks):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.writer(handle, lineterminator='\n')
        writer.writerow(['frame', 'half', 'match_seconds', 'uncertainty_s', 'segment'])
        for frame, clock in enumerate(clocks):
            writer.writerow([frame, clock.half, clock.seconds, clock.uncertainty_s, clock.segment]
                            if clock else [frame, '', '', '', ''])


def read_dense_clock(path):
    clocks = []
    with open(path, newline='', encoding='utf-8-sig') as handle:
        for i, row in enumerate(csv.DictReader(handle)):
            if int(row['frame']) != i:
                raise ValueError('clock CSV must contain consecutive 0-based original frame IDs')
            if row['match_seconds'] == '':
                clocks.append(None)
            else:
                clock = ClockTime(float(row['match_seconds']), float(row['uncertainty_s']),
                                  int(row['half']), int(row['segment']))
                if (clock.half not in (1, 2) or not isfinite(clock.seconds) or clock.seconds < 0
                        or not isfinite(clock.uncertainty_s) or clock.uncertainty_s < 0):
                    raise ValueError('invalid clock CSV value')
                clocks.append(clock)
    if not clocks:
        raise ValueError('clock CSV empty')
    validate_timeline(clocks)
    return clocks


def write_alignment(path, mapping, tactical_clock):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.writer(handle, lineterminator='\n')
        writer.writerow(['tactical_frame', 'broadcast_frame', 'half', 'uncertainty_s', 'status'])
        for i, (link, clock) in enumerate(zip(mapping, tactical_clock)):
            writer.writerow([i, link.broadcast_frame if link.broadcast_frame is not None else '',
                             clock.half if clock else 0,
                             link.uncertainty_s if link.uncertainty_s is not None else '', link.status])


def read_alignment(path, n_tactical, n_broadcast):
    mapping, periods = [], [0] * n_broadcast
    previous_target, reuse = -1, Counter()
    recent = deque()
    with open(path, newline='', encoding='utf-8-sig') as handle:
        for i, row in enumerate(csv.DictReader(handle)):
            if int(row['tactical_frame']) != i:
                raise ValueError('alignment must preserve tactical frame index')
            frame = int(row['broadcast_frame']) if row['broadcast_frame'] else None
            uncertainty = float(row['uncertainty_s']) if row['uncertainty_s'] else None
            half = int(row['half'])
            if frame is not None:
                if (not 0 <= frame < n_broadcast or half not in (1, 2) or uncertainty is None
                        or not isfinite(uncertainty) or uncertainty < 0):
                    raise ValueError('invalid alignment target')
                if periods[frame] not in (0, half):
                    raise ValueError('one broadcast frame mapped into different halves')
                reuse[frame] += 1
                # At 25 fps in both exports, occasional rounding repeats are valid.
                if frame < previous_target or reuse[frame] > 2:
                    raise ValueError('broadcast mapping goes backwards or collapses time')
                recent.append((i, frame))
                while recent and i - recent[0][0] > 25:
                    recent.popleft()
                if recent and i - recent[0][0] >= 20:
                    rate = (frame - recent[0][1]) / (i - recent[0][0])
                    if rate < .55:
                        raise ValueError('broadcast mapping has sustained time collapse')
                previous_target = frame
                periods[frame] = half
            mapping.append(Alignment(frame, uncertainty, row['status']))
    if len(mapping) != n_tactical:
        raise ValueError('alignment row count differs from tactical recording')
    return mapping, periods


def load_scenes(meta_path, raw_path, homography_path, n_frames):
    root = ET.parse(meta_path).getroot()
    teams = [t.get('id') for t in root.iter('Team')]
    slots = [p.get('teamId') for p in root.iter('Player')]
    if len(teams) != 2 or not slots or any(t not in teams for t in slots):
        raise ValueError('invalid tracking metadata for scene comparison')
    transforms = []
    with open(homography_path, newline='', encoding='utf-8-sig') as handle:
        for i, row in enumerate(csv.DictReader(handle)):
            if int(row['frame']) != i:
                raise ValueError('homography frame sequence differs from original recording')
            matrix = [_number(row['h'+str(a)+str(b)]) for a in range(3) for b in range(3)]
            valid = row['valid'].strip() == '1' and all(v is not None for v in matrix)
            if valid:
                a,b,c,d,e,f,g,h,j = matrix
                determinant = a*(e*j-f*h)-b*(d*j-f*g)+c*(d*h-e*g)
                scale = max(abs(v) for v in matrix)
                valid = scale > 0 and abs(determinant) > 1e-12 * scale**3
            error = _number(row['reprojection_error'])
            transforms.append((valid, error if error is not None else float('inf')))
    if len(transforms) != n_frames:
        raise ValueError('homography frame count differs from tracking')
    scenes = []
    with open(raw_path, encoding='utf-8-sig') as handle:
        for i, line in enumerate(handle):
            parts = line.strip().split(':')
            if len(parts) != 3 or int(parts[0]) != i + 1 or i >= n_frames:
                raise ValueError('scene tracking counter mismatch')
            players = parts[1].split(';')
            if len(players) != len(slots):
                raise ValueError('scene player slot count mismatch')
            positions = [[], []]
            for slot, player in enumerate(players):
                xyz = player.split(',')
                x, y = _number(xyz[0]), _number(xyz[1])
                if x is not None and y is not None:
                    positions[teams.index(slots[slot])].append((x * 105.3, y * 68))
            ball = parts[2].split(',')
            x, y = _number(ball[0]), _number(ball[1])
            valid, error = transforms[i]
            scenes.append(Scene(tuple(positions[0]), tuple(positions[1]),
                                (x*105.3, y*68) if x is not None and y is not None else None,
                                valid, error))
    if len(scenes) != n_frames:
        raise ValueError('scene count differs from video')
    return scenes


def ensemble(frames, broadcast_frames, scenes, broadcast_scenes, mapping):
    if (len(frames) != len(mapping) or len(frames) != len(scenes)
            or len(broadcast_frames) != len(broadcast_scenes)):
        raise ValueError('ensemble inputs must preserve original camera dimensions')
    # Shared match context can constrain either camera; it is not new visual evidence.
    shared = list(broadcast_frames)
    for i, link in enumerate(mapping):
        j = link.broadcast_frame
        if frames[i].period == 0 or j is None or link.status != 'clock_candidate':
            continue
        if not 0 <= j < len(shared):
            raise ValueError('broadcast candidate outside original frame range')
        f, b = frames[i], shared[j]
        if f.period == b.period and (f.restart_hint or f.dead_evidence):
            shared[j] = replace(b, restart_hint=b.restart_hint or f.restart_hint,
                                dead_evidence=b.dead_evidence or f.dead_evidence,
                                dead_source=f.dead_source if f.dead_evidence and f.dead_source else b.dead_source)
    primary, secondary = infer(frames), infer(shared)
    decisions, rows = list(primary), []
    verified_reasons, skip_reasons = Counter(), Counter()
    funnel = dict.fromkeys(('candidates_with_missing_tactical_ball', 'unresolved_missing_ball_candidates',
                            'broadcast_ball_observed', 'broadcast_direct_control', 'geometry_verified',
                            'broadcast_weight_sufficient', 'rescued'), 0)

    def record(i, j, status, tw, bw, reason, quality=None):
        f, link = frames[i], mapping[i]
        rows.append((i, j if j is not None else '', status, tw, bw, reason,
                     int(f.ball_observed), int(shared[j].ball_observed) if j is not None else '',
                     int(f.restart_hint), int(f.dead_evidence),
                     link.uncertainty_s if link.uncertainty_s is not None else '',
                     quality if quality is not None else '', primary[i].label,
                     secondary[j].label if j is not None else '', decisions[i].label))

    for i, link in enumerate(mapping):
        if (frames[i].period == 0 or link.broadcast_frame is None or link.status != 'clock_candidate'):
            reason = 'ungraded' if frames[i].period == 0 else link.status
            skip_reasons[reason] += 1
            record(i, None, 'no_verified_clock_candidate', 0, 0, reason)
            continue
        j = link.broadcast_frame
        if frames[i].period != shared[j].period:
            skip_reasons['half_mismatch'] += 1
            record(i, j, 'half_mismatch', 0, 0, 'half_mismatch')
            continue
        verification = verify_geometry(scenes[i], broadcast_scenes[j])
        vote = fuse_vote(primary[i], secondary[j], verification, link.uncertainty_s)
        decisions[i] = vote.decision
        reason = verification.reason
        if verification.accepted and (link.uncertainty_s is None or not isfinite(link.uncertainty_s)
                                      or not 0 <= link.uncertainty_s <= .25):
            reason = 'timing_uncertain'
        verified_reasons[reason] += 1
        record(i, j, vote.status, vote.tactical_weight, vote.broadcast_weight, reason, verification.quality)
        if not frames[i].ball_observed:
            funnel['candidates_with_missing_tactical_ball'] += 1
            if primary[i].label == 'X':
                funnel['unresolved_missing_ball_candidates'] += 1
                if shared[j].ball_observed:
                    funnel['broadcast_ball_observed'] += 1
                    if secondary[j].label in ('H', 'A') and secondary[j].evidence_level == 'direct_heuristic':
                        funnel['broadcast_direct_control'] += 1
                        if verification.accepted:
                            funnel['geometry_verified'] += 1
                            if vote.broadcast_weight >= .3:
                                funnel['broadcast_weight_sufficient'] += 1
                                funnel['rescued'] += vote.status == 'broadcast_rescue'
    statuses = Counter(r[2] for r in rows)
    report = {'accuracy_measured': False, 'before': summary(frames, primary),
              'after': summary(frames, decisions), 'fusion_status_counts': dict(statuses),
              'broadcast_rescued_frames': statuses['broadcast_rescue'],
              'weak_tactical_replaced_frames': statuses['broadcast_overrides_inferred'],
              'camera_comparison_frames': sum(verified_reasons.values()),
              'not_compared_frames': sum(skip_reasons.values()),
              'verification_reason_counts': dict(verified_reasons),
              'comparison_skip_reason_counts': dict(skip_reasons),
              'alignment_status_counts': dict(Counter(link.status for link in mapping)),
              'missing_ball_funnel': funnel,
              'shared_restart_context': True,
              'replay_detector_included': False,
              'general_live_dead_detector_included': False,
              'scope_note': 'Unmapped frames are not failed comparisons. Alignment alone cannot distinguish unscanned frames from OCR failure.',
              'warning': 'Heuristic quality gates do not prove alignment, live footage or accuracy.'}
    return decisions, rows, report


def save_ensemble(directory, frames, decisions, rows, report, audit_stages=None):
    write_outputs(directory, frames, decisions, audit_stages=audit_stages)
    directory = Path(directory)
    with (directory / 'fusion_diagnostics.csv').open('w', newline='', encoding='utf-8') as handle:
        writer = csv.writer(handle, lineterminator='\n')
        writer.writerow(['tactical_frame', 'broadcast_frame', 'fusion_status',
                         'tactical_weight', 'broadcast_weight', 'verification',
                         'tactical_ball_observed', 'broadcast_ball_observed', 'restart_phase_hint',
                         'dead_evidence', 'timing_uncertainty_s', 'geometry_quality',
                         'tactical_label', 'broadcast_label', 'final_label'])
        writer.writerows(rows)
    (directory / 'ensemble_report.json').write_text(json.dumps(report, indent=2) + '\n')


def _demo(directory):
    frames = [Frame(ball_x=40, ball_y=30, home_distance=.5, away_distance=8)] * 200
    for start in (60, 140):
        frames[start:start+20] = [Frame()] * 20
    broadcast = [Frame(period=0)] * 37 + [Frame(ball_x=40, ball_y=30,
                                              home_distance=.5, away_distance=8)] * 200
    def reads(offset=0):
        return [ClockRead(i+offset, '19:{:02d}'.format(i//25), .95, 1) for i in range(0, 200, 5)]
    tc, bc = dense_clock(reads(), 200), dense_clock(reads(37), 237)
    mapping = align_clocks(tc, bc)
    scene = Scene(((10,10), (20,15), (30,20), (40,25)),
                  ((12,40), (22,45), (32,50), (42,55)), (40,30), True, .2)
    scenes = [replace(scene, ball=None) if not f.ball_observed else scene for f in frames]
    broadcast_scenes = [scene] * 237
    for i in range(177, 197):  # second synthetic gap has an unreliable broadcast transform
        broadcast_scenes[i] = replace(scene, homography_valid=False)
    decisions, rows, report = ensemble(frames, broadcast, scenes, broadcast_scenes, mapping)
    report['synthetic_only'] = True
    save_ensemble(directory, frames, decisions, rows, report)
    write_dense_clock(Path(directory) / 'tactical_clock.csv', tc)
    write_dense_clock(Path(directory) / 'broadcast_clock.csv', bc)
    write_alignment(Path(directory) / 'alignment.csv', mapping, tc)
    print('SYNTHETIC camera experiment only; no match accuracy measured.')
    print('Unresolved tactical frames before/after: {} / {}'.format(
        report['before']['labels']['X'], report['after']['labels']['X']))
    print('Verified broadcast rescues: ' + str(report['broadcast_rescued_frames']))


def main():
    parser = argparse.ArgumentParser(description='Local clock alignment and gated two-camera fusion')
    sub = parser.add_subparsers(dest='command', required=True)
    demo = sub.add_parser('demo')
    demo.add_argument('--out', default='outputs/two-camera-demo')
    discovery = sub.add_parser('discover-clock', help='scan the whole video for clock regions automatically; discovery only')
    discovery.add_argument('--video', required=True)
    discovery.add_argument('--stride-seconds', type=float, default=30.0,
                           help='whole-recording sample interval, at least 1 second; choose/tune externally')
    discovery.add_argument('--min-confidence', type=float, default=.7)
    discovery.add_argument('--ffmpeg', default='ffmpeg')
    discovery.add_argument('--ffprobe', default='ffprobe')
    discovery.add_argument('--tesseract', default='tesseract')
    discovery.add_argument('--out', required=True, help='one overwritten local discovery JSON; not an alignment CSV')
    automatic = sub.add_parser('auto-sync', help='automatic crops and bounded dense clock candidates from discovery; no fusion')
    automatic.add_argument('--tactical-video', required=True)
    automatic.add_argument('--broadcast-video', required=True)
    automatic.add_argument('--tactical-discovery', required=True)
    automatic.add_argument('--broadcast-discovery', required=True)
    automatic.add_argument('--ffmpeg', default='ffmpeg')
    automatic.add_argument('--ffprobe', default='ffprobe')
    automatic.add_argument('--tesseract', default='tesseract')
    automatic.add_argument('--out', default='outputs/automatic-sync')
    check = sub.add_parser('ocr-check', help='test one local clock image without rescanning video')
    check.add_argument('--image', required=True)
    check.add_argument('--source', choices=('tactical', 'broadcast'), required=True)
    check.add_argument('--ffmpeg', default='ffmpeg')
    check.add_argument('--tesseract', default='tesseract')
    clock = sub.add_parser('clock')
    clock.add_argument('--video', required=True)
    clock.add_argument('--source', choices=('tactical', 'broadcast'), required=True)
    clock.add_argument('--half', type=int, choices=(1,2), required=True)
    clock.add_argument('--start-frame', type=int, required=True)
    clock.add_argument('--end-frame', type=int, required=True, help='exclusive; choose a clip within the selected half')
    clock.add_argument('--stride', type=int, default=5)
    clock.add_argument('--min-confidence', type=float, default=.7,
                       help='OCR score cutoff; 0.5 is an explicit trial setting, not measured accuracy')
    crop_options=clock.add_mutually_exclusive_group()
    crop_options.add_argument('--roi', help='normalised x,y,width,height; overrides provisional crop preset')
    crop_options.add_argument('--roi-file', help='reuse a saved local clock-box JSON file')
    crop_options.add_argument('--select-roi', action='store_true', help='draw the clock box locally before OCR')
    clock.add_argument('--preview', help='save first enlarged clock crop locally for inspection')
    clock.add_argument('--ffmpeg', default='ffmpeg')
    clock.add_argument('--ffprobe', default='ffprobe')
    clock.add_argument('--tesseract', default='tesseract')
    clock.add_argument('--out', required=True, help='dense clock CSV; original video frame count')
    align = sub.add_parser('align')
    align.add_argument('--tactical-clock', required=True)
    align.add_argument('--broadcast-clock', required=True)
    align.add_argument('--max-uncertainty', type=float, default=.25)
    align.add_argument('--out', default='outputs/alignment.csv')
    fuse = sub.add_parser('fuse')
    fuse.add_argument('--data-dir', default='.', help='parent of tactical/ and broadcast/, or tactical cam/ and broadcast cam/')
    fuse.add_argument('--tactical-dir', help='explicit folder containing BAR-ATH_tactical tracking and homography')
    fuse.add_argument('--broadcast-dir', help='explicit folder containing BAR-ATH_broadcast tracking and homography')
    fuse.add_argument('--alignment', required=True)
    fuse.add_argument('--audit-baseline', action='store_true',
                      help='isolate legacy restart, restart repair, published dead context and fusion using cached alignment')
    fuse.add_argument('--out', default='outputs/ensemble')
    args = parser.parse_args()
    try:
        if args.command == 'demo':
            _demo(args.out)
        elif args.command == 'auto-sync':
            from .automatic_sync import automatic_sync
            report = automatic_sync(args.tactical_video,args.broadcast_video,
                args.tactical_discovery,args.broadcast_discovery,args.out,
                args.ffmpeg,args.ffprobe,args.tesseract)
            print(json.dumps(report,indent=2))
        elif args.command == 'discover-clock':
            from .clock_discovery import scan_video
            video, output = Path(args.video), Path(args.out)
            if (video.resolve() == output.resolve()
                    or video.exists() and output.exists() and video.samefile(output)):
                raise ValueError('Discovery output must not overwrite the source video or an alias of it')
            report = scan_video(args.video, args.stride_seconds, args.min_confidence,
                                args.ffmpeg, args.ffprobe, args.tesseract)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
            print('Clock discovery samples: {}'.format(report['sample_count']))
            print('Samples with clock candidates: {}'.format(report['samples_with_clock_candidate']))
            print('Samples with multiple candidates: {}'.format(report['samples_with_multiple_candidates']))
            print('Candidate progressing-clock segments: {}'.format(report['candidate_segment_count']))
            print('Discovery only: dense alignment and live/replay verification are not included.')
            print('Output: '+str(output.resolve()))
        elif args.command == 'ocr-check':
            from .clock_ocr import check_clock_image
            raw, processed = check_clock_image(args.image, args.source, args.ffmpeg, args.tesseract)
            print('Original: clock={!r}; Tesseract confidence={:.3f}'.format(*raw))
            print('Preprocessed: clock={!r}; Tesseract confidence={:.3f}'.format(*processed))
            print('Confidence is an OCR score, not measured correctness. Clock default cutoff is 0.7; --min-confidence overrides it for a trial.')
        elif args.command == 'clock':
            from .clock_ocr import extract_clock, ocr_summary
            if not 0 <= args.min_confidence <= 1:
                raise ValueError('--min-confidence must be between 0 and 1')
            roi = tuple(float(v) for v in args.roi.split(',')) if args.roi else None
            if roi is not None and len(roi) != 4:
                raise ValueError('ROI needs x,y,width,height')
            if args.roi_file:
                from .roi import load_roi
                roi=load_roi(args.roi_file,args.source)
            if args.select_roi:
                from .roi import choose_roi
                roi=choose_roi(args.video,args.start_frame,args.source,
                               str(args.out)+'.roi.json',args.ffmpeg,args.ffprobe)
            reads, count, fps = extract_clock(args.video, args.source, args.half,
                args.start_frame, args.end_frame, args.stride, roi,
                args.ffmpeg, args.ffprobe, args.tesseract, args.preview,
                min_confidence=args.min_confidence)
            timeline = dense_clock(reads, count, fps, min_confidence=args.min_confidence)
            write_dense_clock(args.out, timeline)
            with Path(str(args.out) + '.reads.csv').open('w', newline='', encoding='utf-8') as handle:
                writer = csv.writer(handle, lineterminator='\n')
                writer.writerow(['frame', 'half', 'clock_text', 'ocr_confidence', 'ocr_method', 'ocr_attempts'])
                writer.writerows((r.frame, r.half, r.text, r.confidence, r.method, r.attempts) for r in reads)
            print('OCR samples: {}; frames with bounded clock estimate: {}'.format(
                len(reads), sum(c is not None for c in timeline)))
            stats=ocr_summary(reads,args.min_confidence)
            print('Clock-shaped readings: {}; accepted at cutoff {:.3f}: {}; unreadable: {}'.format(
                stats['parsed'],stats['cutoff'],stats['accepted_by_score'],stats['unreadable']))
            print('OCR retries: {}; recovered at cutoff: {}; conflicting retries: {}'.format(
                stats['retried'],stats['recovered'],stats['conflicts']))
            if stats['p01_all'] is not None:
                print('Confidence across ALL crops (unreadable=0): p01={:.3f}; median={:.3f}; minimum={:.3f}'.format(
                    stats['p01_all'],stats['median_all'],stats['minimum_all']))
                print('First-percentile confidence > 0.5: '+('YES' if stats['p01_above_half'] else 'NO'))
            print('Clock matching alone does not verify live footage or possession.')
        elif args.command == 'align':
            tactical = read_dense_clock(args.tactical_clock)
            broadcast = read_dense_clock(args.broadcast_clock)
            mapping = align_clocks(tactical, broadcast, args.max_uncertainty)
            write_alignment(args.out, mapping, tactical)
            print(json.dumps(dict(Counter(m.status for m in mapping)), indent=2))
        else:
            root = Path(args.data_dir)
            t = str(resolve_source_prefix(root, 'tactical', args.tactical_dir))
            b = str(resolve_source_prefix(root, 'broadcast', args.broadcast_dir))
            mapping, periods = read_alignment(args.alignment, N_FRAMES, 164488)
            candidates = sum(link.broadcast_frame is not None and link.status == 'clock_candidate'
                             for link in mapping)
            if not candidates:
                raise ValueError('No clock candidates in alignment; select overlapping match-clock clips first.')
            print('Clock candidates: {}; loading tactical tracking...'.format(candidates), flush=True)
            frames, teams = load_atd(t+'_atd.xml', t+'_atd.txt')
            tagging = Path(t+'_smart_tagging.xml')
            if tagging.exists():
                frames = load_tags(tagging, frames, teams)
            raw_frames = frames
            frames = apply_published_dead(raw_frames)
            print('Loading broadcast tracking...', flush=True)
            other, other_teams = load_atd(b+'_atd.xml', b+'_atd.txt', n_frames=164488,
                                         blocks=[(1, 0, 164487)])
            other = [replace(f, period=p) for f, p in zip(other, periods)]
            print('Loading both camera scenes and homographies...', flush=True)
            scenes = load_scenes(t+'_atd.xml', t+'_atd.txt', t+'_homography.csv', N_FRAMES)
            other_scenes = load_scenes(b+'_atd.xml', b+'_atd.txt', b+'_homography.csv', 164488)
            def norm(name):
                return name.lower().replace('fc ', '').replace('atletic', 'athletic').strip()
            if tuple(map(norm, teams)) == tuple(reversed(tuple(map(norm, other_teams)))):
                other = [replace(f, home_distance=f.away_distance, away_distance=f.home_distance) for f in other]
                other_scenes = [replace(s, home=s.away, away=s.home) for s in other_scenes]
            elif tuple(map(norm, teams)) != tuple(map(norm, other_teams)):
                raise ValueError('Team identities do not match across exports')
            print('Comparing camera evidence and writing results...', flush=True)
            decisions, rows, report = ensemble(frames, other, scenes, other_scenes, mapping)
            audit_stages = None
            if args.audit_baseline:
                from .audit import build_baseline_audit
                comparison, audit_stages = build_baseline_audit(raw_frames, frames, decisions)
                report['controlled_comparison'] = comparison
            save_ensemble(args.out, frames, decisions, rows, report, audit_stages=audit_stages)
            print('EXPERIMENTAL: live/dead detector still absent; no match accuracy measured.')
            print('Unresolved tactical frames before/after: {} / {}'.format(
                report['before']['labels']['X'], report['after']['labels']['X']))
            print('Broadcast-rescued frames: {}'.format(report['broadcast_rescued_frames']))
            print('Camera comparison frames: {}'.format(report['camera_comparison_frames']))
            print('Missing-ball opportunity funnel: '+json.dumps(report['missing_ball_funnel']))
            if args.audit_baseline:
                print('Controlled baseline comparison (coverage and behavior, not measured accuracy):')
                for name, stage in report['controlled_comparison']['stages'].items():
                    print('  {}: H={H}; A={A}; D={D}; X={X}'.format(name, **stage['labels']))
                for name, change in report['controlled_comparison']['comparisons'].items():
                    print('  {}: raw changes={}; scorer-expanded changes={}'.format(
                        name, change['raw_label_changes'], change['scorer_expanded_label_changes']))
            print('Detailed verification reasons: '+json.dumps(report['verification_reason_counts']))
            print(json.dumps(report['fusion_status_counts'], indent=2))
    except (OSError, ValueError, TypeError, KeyError, IndexError, ET.ParseError) as exc:
        parser.error(str(exc))


if __name__ == '__main__':
    main()
''',
    'gap_solver.official_metrics': r'''"""Metrics for per-frame possession inference, scored against a H/A/D/X ground truth.

numpy and pandas only, on purpose: no sklearn, nothing that pins a Python version, and
hand-rolling a 4x4 confusion matrix is fifteen lines. Keeping it dependency-free means the scorer
runs anywhere, and produces identical output under 3.8 and 3.11.

THE RANKING METRIC is spell_f1_mean -- possessions matched one-to-one by temporal IoU, defined
further down. macro-F1 over {H, A, D} is reported beside it as the per-frame view and is the first
tie-break. It is averaged unweighted over the frames where the ground truth is not X, rather than
counting frames, which is what stops a degenerate always-one-label submission from scoring
respectably, which is exactly what plain accuracy would do. It is however nearly blind to a uniform timing offset: lagging every
transition by ten frames barely moves it, because only a small fraction of frames sit near a
boundary. That is why the transition metrics below are computed as well, not as extras.

READ THIS BEFORE COMPARING TWO SCORES. A match has a great many frames but far fewer segments, so
consecutive frames are nowhere near independent and the effective sample size is the segment
count, not the frame count. One misjudged long dead-ball stretch moves macro-F1 by about a
percentage point on its own, so macro-F1 gaps below roughly 0.01 are segment-level noise rather
than signal. Set BOOTSTRAP_N to get a block-bootstrap interval over segments, which is the honest
way to answer "is this gap real"; do not compute per-frame intervals, they come out an order of
magnitude too narrow.

Usage:
    import possession_metrics as pm
    gt = pm.label_codes(pm.read_label_csv("gt/BAR-ATH_possession_gt.csv"))
    pred = pm.label_codes(pm.read_label_csv("results/mine.csv"))
    print(pm.evaluate(gt, pred)["macro_f1"])
"""

import numpy as np
import pandas as pd

# Params
# X is both "no ground truth here" (in the GT) and "I abstain" (in a submission). One symbol for
# both because the grading rule is the same either way: GT X is never scored, and a predicted X
# on a graded frame is a miss.
LABELS = ("H", "A", "D", "X")
SCORED = ("H", "A", "D")
H, A, D, X = 0, 1, 2, 3
N_LABELS = len(LABELS)
N_SCORED = len(SCORED)

# Tolerances for transition matching, in frames at 25 fps: ~0.5 s and 1.0 s. Reported as a pair
# because the gap between them is a lag detector -- a submission that scores badly at 12 and well
# at 25 has a systematic delay in that range, which no frame-level metric reveals.
TAUS = (12, 25)

# A possession is a team spell with the ball alive. D runs are stoppages, not possessions, so
# spells are maximal runs of H or of A. Dead-ball detection is covered separately by
# alive_dead_f1 and by the D row of the per-class table.
POSSESSION_LABELS = (H, A)
# IoU thresholds for possession-spell matching, averaged mAP-style. Averaging over IoU is the
# temporal action detection convention and is principled here, because IoU is a real quality
# axis for an interval. (Averaging over *frame tolerances* is not, and was rejected: the
# frame metric already costs only 0.0031 for a uniform 1-frame lag, below the noise floor.)
#
# Not called mAP anywhere on purpose: submissions are hard labels with no confidence scores, so
# there is no precision-recall curve to integrate. This is a mean F1 over IoU thresholds, and the
# mAP analogy is to the averaging axis alone.
SPELL_IOUS = (0.3, 0.4, 0.5, 0.6, 0.7)
SPELL_IOU_HEADLINE = 0.5
FPS = 25  # only used to report spell durations in seconds, which is how coaches read them

# Typical 5-95 percentile width of spell_f1_mean under a bootstrap over the ground-truth
# possessions of a full match, so a gap smaller than this is not a result. Measured across a set
# of reference submissions spanning realistic failure modes. It is 3-4x the ~0.01 floor on
# macro_f1, because the effective sample is the possessions scored hit-or-miss rather than every
# frame -- but the gaps between submissions widen in proportion, so exactly as many adjacent
# pairs stay separable under either metric.
SPELL_NOISE_BAND = 0.04

# Block bootstrap draws over GT segments. 0 = off (fast); 1000 for a final leaderboard.
BOOTSTRAP_N = 0
BOOTSTRAP_SEED = 0
BOOTSTRAP_PERCENTILES = (5, 95)

# Sentinel for possession share when a submission predicts no alive frames at all. Paired with
# share_defined in the output so it can never be mistaken for a measurement.
SHARE_UNDEFINED = 1.0


# -- reading and validation --------------------------------------------------------------------

def read_label_csv(path):
    """Read a frame,label CSV and return the label column as an object array.

    Tolerant about header case and surrounding whitespace, strict about everything else: the
    validation lives in validate_submission so a bad file can be reported rather than raised.
    """
    frame = pd.read_csv(path, dtype={"label": "object"})
    frame.columns = [str(c).strip().lower() for c in frame.columns]
    if "label" not in frame.columns or "frame" not in frame.columns:
        raise ValueError("expected columns 'frame' and 'label', got {}".format(
            list(frame.columns)))
    return frame


def validate_submission(frame, n_expected):
    """Return None if the table is a usable submission, else a one-line reason why it is not."""
    if len(frame) != n_expected:
        return "row count {} != {}".format(len(frame), n_expected)

    frames = frame["frame"].values
    if not np.issubdtype(frames.dtype, np.integer):
        return "'frame' column is not integer (dtype {})".format(frames.dtype)
    if not np.array_equal(frames, np.arange(n_expected)):
        # One comparison covers 0-based, monotonic, contiguous and duplicate-free.
        return "'frame' column is not 0..{} in order".format(n_expected - 1)

    labels = frame["label"].values
    blank = pd.isna(labels)
    if blank.any():
        # Never coerce a blank cell to X: an empty field is a mistake, while X is a deliberate
        # abstention, and scoring one as the other would hide the mistake.
        return "empty label in {} rows; write X to abstain".format(int(blank.sum()))

    cleaned = np.array([str(v).strip().upper() for v in labels], dtype=object)
    bad = sorted(set(cleaned) - set(LABELS))
    if bad:
        return "labels outside {}: {}".format(list(LABELS), bad[:5])
    return None


def label_codes(frame_or_labels):
    """Map label strings to 0..3. Accepts the DataFrame from read_label_csv or a bare array."""
    values = frame_or_labels
    if isinstance(values, pd.DataFrame):
        values = values["label"].values
    values = np.array([str(v).strip().upper() for v in values], dtype=object)

    codes = np.full(len(values), -1, dtype=np.int8)
    for index, name in enumerate(LABELS):
        codes[values == name] = index
    if (codes < 0).any():
        raise ValueError("labels outside {}: {}".format(
            list(LABELS), sorted(set(values[codes < 0]))))
    return codes


# -- frame-level metrics -----------------------------------------------------------------------

def confusion(gt_codes, pred_codes):
    """4x4 counts, rows = ground truth, cols = prediction."""
    pair = gt_codes.astype(np.int64) * N_LABELS + pred_codes.astype(np.int64)
    return np.bincount(pair, minlength=N_LABELS * N_LABELS).reshape(N_LABELS, N_LABELS)


def scored_confusion(cm):
    """The 3x4 slice everything is scored on: GT rows H/A/D only, all four prediction columns.

    The whole X policy is this slice. False positives are summed over three GT rows, so a frame
    the ground truth does not cover can never manufacture one. False negatives are summed over
    four prediction columns, so a predicted X on a graded frame does count as a miss. No
    special-casing anywhere else.
    """
    return cm[:N_SCORED, :]


def per_class_prf(cm3, k):
    """(precision, recall, f1) for class k from the 3x4 scored confusion."""
    true_positive = float(cm3[k, k])
    false_positive = float(cm3[:, k].sum()) - true_positive
    false_negative = float(cm3[k, :].sum()) - true_positive

    precision = true_positive / (true_positive + false_positive) \
        if true_positive + false_positive else 0.0
    recall = true_positive / (true_positive + false_negative) \
        if true_positive + false_negative else 0.0
    if precision + recall == 0.0:
        return 0.0, 0.0, 0.0  # absent class or nothing predicted -> 0, never nan
    return precision, recall, 2.0 * precision * recall / (precision + recall)


def macro_f1(cm3):
    """Unweighted mean F1 over H, A and D. The metric the scoreboard ranks on."""
    return float(np.mean([per_class_prf(cm3, k)[2] for k in range(N_SCORED)]))


def accuracy(cm3):
    """Fraction of graded frames labelled correctly. Predicted X counts against."""
    total = float(cm3.sum())
    if not total:
        return 0.0
    return float(sum(cm3[k, k] for k in range(N_SCORED))) / total


def cohens_kappa(cm3):
    """Chance-corrected agreement. Exactly 0.0 for any constant-guess submission.

    Reported as a secondary column only. Its chance level is computed from the submission's own
    marginals, so shifting your predicted class proportions changes your score without improving
    any single decision -- a bad property to rank a leaderboard on.
    """
    square = np.zeros((N_LABELS, N_LABELS), dtype=np.float64)
    square[:N_SCORED, :] = cm3  # the unused GT X row stays zero and drops out of both terms
    total = square.sum()
    if not total:
        return 0.0

    observed = np.trace(square) / total
    expected = sum(square[k, :].sum() * square[:, k].sum()
                   for k in range(N_LABELS)) / total ** 2
    if expected >= 1.0:
        return 0.0
    return float((observed - expected) / (1.0 - expected))


def alive_dead_f1(cm3):
    """F1 of the alive/dead call alone, with ALIVE as the positive class.

    ALIVE and not DEAD because dead ball is a large share of all frames: with DEAD positive, an
    always-dead submission scores well on this and reads like competence. With ALIVE positive it
    scores 0, which is the honest answer.
    """
    true_positive = float(cm3[:D, :D].sum())              # GT alive, predicted alive
    false_positive = float(cm3[D, :D].sum())              # GT dead, predicted alive
    false_negative = float(cm3[:D, D:].sum())             # GT alive, predicted dead or X

    precision = true_positive / (true_positive + false_positive) \
        if true_positive + false_positive else 0.0
    recall = true_positive / (true_positive + false_negative) \
        if true_positive + false_negative else 0.0
    if precision + recall == 0.0:
        return 0.0
    return 2.0 * precision * recall / (precision + recall)


def team_accuracy(cm3):
    """(strict, both_alive) H-vs-A accuracy.

    strict is over every GT-alive frame, so answering D or X there counts as wrong. both_alive is
    over the frames where GT and prediction agree the ball is alive, i.e. the team call in
    isolation, with the alive/dead call already charged by alive_dead_f1.
    """
    correct = float(cm3[H, H] + cm3[A, A])
    gt_alive = float(cm3[:D, :].sum())
    both_alive = float(cm3[:D, :D].sum())
    return (correct / gt_alive if gt_alive else 0.0,
            correct / both_alive if both_alive else 0.0)


def possession_share(cm3):
    """(gt_share, pred_share, abs_err, defined) home share of alive time.

    Each side is measured over its own alive frames, because this is the number a submission
    would actually report as "the home side had 55% of the ball" -- not a per-frame agreement.
    """
    gt_alive = float(cm3[:D, :].sum())
    pred_alive = float(cm3[:, :D].sum())
    gt_share = float(cm3[H, :].sum()) / gt_alive if gt_alive else 0.0
    if not pred_alive:
        return gt_share, 0.0, SHARE_UNDEFINED, False
    pred_share = float(cm3[:, H].sum()) / pred_alive
    return gt_share, pred_share, abs(pred_share - gt_share), True


# -- temporal structure ------------------------------------------------------------------------

def valid_runs(gt_codes):
    """Half-open [start, stop) spans where the ground truth is not X.

    Derived from the data, never hard-coded: for BAR-ATH this returns the two halves,
    (11185, 90652) and (110808, 190198). Everything temporal is computed inside a run and never
    across one, so the 20156-frame halftime hole cannot produce a phantom transition. That
    matters even when the labels either side happen to match -- here they are both D, so a
    whole-array run-length encoding silently merges them and undercounts the segments by one.
    """
    graded = (gt_codes != X).astype(np.int8)
    edges = np.diff(np.concatenate(([0], graded, [0])))
    return list(zip(np.flatnonzero(edges == 1).tolist(),
                    np.flatnonzero(edges == -1).tolist()))


def fill_abstentions(pred_codes, runs):
    """Copy of pred_codes with X forward-filled (then back-filled at the run head) inside runs.

    Frame-level metrics see the raw X and charge it. The temporal metrics see this filled version
    instead, because 'H X X H' is one uninterrupted possession that the model went quiet during,
    not two possessions with a pair of transitions in between. Without this, an abstention is
    charged twice: once as a frame-level miss and again as two spurious transitions.
    """
    filled = pred_codes.copy()
    for start, stop in runs:
        window = filled[start:stop]
        known = np.flatnonzero(window != X)
        if not len(known):
            continue  # a run the submission abstained on entirely; nothing to carry forward
        # For each position, the index of the most recent non-X at or before it, then clamp the
        # leading positions to the first known value (the back-fill).
        carry = np.maximum.accumulate(np.where(window != X, np.arange(len(window)), -1))
        carry[carry < 0] = known[0]
        filled[start:stop] = window[carry]
    return filled


def segments(codes, runs):
    """[(start, stop, code)] constant-label runs, encoded inside each valid run separately."""
    out = []
    for start, stop in runs:
        window = codes[start:stop]
        if not len(window):
            continue
        breaks = np.flatnonzero(window[1:] != window[:-1]) + 1
        bounds = np.concatenate(([0], breaks, [len(window)]))
        for i in range(len(bounds) - 1):
            out.append((start + int(bounds[i]), start + int(bounds[i + 1]),
                        int(window[bounds[i]])))
    return out


def transitions(codes, runs):
    """[(frame, from_code, to_code)] label changes, never spanning a run boundary.

    frame is the first frame of the new label, so it is directly usable as a seek target in a
    video player.
    """
    out = []
    for start, stop in runs:
        window = codes[start:stop]
        for index in (np.flatnonzero(window[1:] != window[:-1]) + 1).tolist():
            out.append((start + int(index), int(window[index - 1]), int(window[index])))
    return out


def match_transitions(gt_trans, pred_trans, tol, typed="to"):
    """One-to-one match of predicted transitions to ground-truth ones within +/- tol frames.

    Returns (pairs, missed, spurious), pairs being [(gt_transition, pred_transition)].

    Matching is on the destination label by default. 'D -> H' and 'D -> A' at the same frame are
    materially different events -- you spotted the restart but gave it to the wrong team -- so the
    destination has to agree. The origin does not: a predicted 'A -> H' against a true 'D -> H'
    got the event right and only the preceding state wrong, and that preceding state is already
    fully charged at frame level. typed="pair" demands both, typed="none" neither.

    Both lists are frame-sorted and feasibility is an interval, so matching earliest-to-earliest
    within each key is maximum-cardinality (the standard interval exchange argument) as well as
    deterministic. Cross-run pairing needs no explicit guard: runs are 20156 frames apart and
    tol is at most a few dozen, so the interval test rejects it.

    Caveat worth knowing: maximum cardinality does not mean minimum total latency, and when
    several maximum matchings exist the reported mean latency can shift by a few frames. A
    handful of ground-truth segments are shorter than the loose tolerance, so at tol=25 the
    windows really can overlap. That is what n_ambiguous in transition_scores is for.
    """
    def key(transition):
        if typed == "pair":
            return (transition[1], transition[2])
        if typed == "none":
            return 0
        return transition[2]

    pairs, missed, spurious = [], [], []
    gt_by_key, pred_by_key = {}, {}
    for transition in gt_trans:
        gt_by_key.setdefault(key(transition), []).append(transition)
    for transition in pred_trans:
        pred_by_key.setdefault(key(transition), []).append(transition)

    for group in sorted(set(gt_by_key) | set(pred_by_key)):
        gts = gt_by_key.get(group, [])
        preds = pred_by_key.get(group, [])
        i = j = 0
        while i < len(gts) and j < len(preds):
            delta = preds[j][0] - gts[i][0]
            if delta < -tol:
                spurious.append(preds[j])  # too early for this or any later gt
                j += 1
            elif delta > tol:
                missed.append(gts[i])      # no remaining pred can reach back to it
                i += 1
            else:
                pairs.append((gts[i], preds[j]))
                i += 1
                j += 1
        missed.extend(gts[i:])
        spurious.extend(preds[j:])
    return pairs, missed, spurious


def transition_scores(gt_trans, pred_trans, tol, typed="to"):
    """Precision, recall, F1 and latency for transition detection at one tolerance.

    Precision and recall are reported separately and always should be: jitter shows up as recall
    near 1.0 with precision near 0, which a single F1 hides.
    """
    pairs, missed, spurious = match_transitions(gt_trans, pred_trans, tol, typed)
    true_positive, false_positive, false_negative = len(pairs), len(spurious), len(missed)

    precision = true_positive / float(true_positive + false_positive) \
        if true_positive + false_positive else 0.0
    recall = true_positive / float(true_positive + false_negative) \
        if true_positive + false_negative else 0.0
    f1 = 2.0 * precision * recall / (precision + recall) if precision + recall else 0.0

    latencies = np.array([pred[0] - gt[0] for gt, pred in pairs], dtype=np.float64)
    ambiguous = _count_ambiguous(gt_trans, pred_trans, tol, typed)
    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "n_gt": len(gt_trans),
        "n_pred": len(pred_trans),
        "n_matched": true_positive,
        "n_missed": false_negative,
        "n_spurious": false_positive,
        "n_ambiguous": ambiguous,
        "mean_latency": float(latencies.mean()) if len(latencies) else None,
        "median_latency": float(np.median(latencies)) if len(latencies) else None,
        "mean_abs_latency": float(np.abs(latencies).mean()) if len(latencies) else None,
        "p90_abs_latency": float(np.percentile(np.abs(latencies), 90)) if len(latencies) else None,
        "pairs": pairs,
        "missed": missed,
        "spurious": spurious,
    }


def _count_ambiguous(gt_trans, pred_trans, tol, typed):
    """GT transitions with more than one feasible prediction, i.e. where the match was a choice.

    When this is 0 the latency figures are exact; when it is large they are indicative only.
    """
    def key(transition):
        if typed == "pair":
            return (transition[1], transition[2])
        if typed == "none":
            return 0
        return transition[2]

    by_key = {}
    for transition in pred_trans:
        by_key.setdefault(key(transition), []).append(transition[0])
    for group in by_key:
        by_key[group] = np.array(sorted(by_key[group]))

    count = 0
    for transition in gt_trans:
        frames = by_key.get(key(transition))
        if frames is None:
            continue
        if int(np.sum(np.abs(frames - transition[0]) <= tol)) > 1:
            count += 1
    return count


def fragmentation(gt_codes, pred_codes, runs):
    """(n_gt_segments, n_pred_segments, ratio). A jitter detector: a flickering submission can
    hold a respectable macro-F1 while producing thirty times too many possessions."""
    n_gt = len(segments(gt_codes, runs))
    n_pred = len(segments(pred_codes, runs))
    return n_gt, n_pred, (n_pred / float(n_gt) if n_gt else 0.0)


# -- possession-spell level --------------------------------------------------------------------
#
# Why this level exists at all. Frame macro-F1 is the right per-frame metric, but no per-frame
# metric can represent possession, because the overwhelming majority of graded frames sit in the
# interior of a segment where nothing is happening. A jittery submission can hold a per-frame
# score near 0.97 while reporting well over half as many possessions again as the truth, each far
# too short. Per-frame scoring also over-weights dead ball, which is a much larger share of frames
# than of segments, and lets the longest possession of a match count hundreds of times the
# shortest. Treating each possession as one object fixes all three.

def possession_spells(codes, runs):
    """[(start, stop, code)] maximal H or A runs -- the possessions, stoppages excluded.

    Built on the gap-aware segments(), so no spell can ever straddle the halftime hole.
    """
    return [(a, b, k) for a, b, k in segments(codes, runs) if k in POSSESSION_LABELS]


def spell_overlaps(gt_spells, pred_spells):
    """[(iou, gt_index, pred_index)] for every same-team overlapping pair, sorted for matching.

    Computed once and filtered per threshold by match_spells: the IoU of a pair does not depend
    on the threshold, so recomputing it for each of SPELL_IOUS would be five times the work for
    identical results. Sorted by (-iou, gt_index, pred_index) so ties break the same way on
    every run and the matching is reproducible.
    """
    out = []
    for i, (gt_start, gt_stop, gt_code) in enumerate(gt_spells):
        for j, (pred_start, pred_stop, pred_code) in enumerate(pred_spells):
            if pred_code != gt_code or pred_stop <= gt_start or gt_stop <= pred_start:
                continue
            intersection = min(gt_stop, pred_stop) - max(gt_start, pred_start)
            union = max(gt_stop, pred_stop) - min(gt_start, pred_start)
            out.append((intersection / float(union), i, j))
    out.sort(key=lambda item: (-item[0], item[1], item[2]))
    return out


def matched_gt_flags(overlaps, n_gt, threshold):
    """Boolean array over ground-truth spells, True where one was matched at this IoU.

    Greedy on the IoU-descending list, marking both sides consumed, so every ground-truth spell
    is credited to at most one prediction and vice versa. Returned per spell rather than as a
    count because the bootstrap needs to resample individual possessions.
    """
    flags = np.zeros(n_gt, dtype=bool)
    matched_pred = set()
    for iou, gt_index, pred_index in overlaps:
        if iou < threshold:
            break  # the list is IoU-descending, so nothing later can qualify either
        if flags[gt_index] or pred_index in matched_pred:
            continue
        flags[gt_index] = True
        matched_pred.add(pred_index)
    return flags


def match_spells(overlaps, n_gt, n_pred, threshold):
    """(tp, fp, fn) from a one-to-one greedy match of spells at one IoU threshold."""
    true_positive = int(matched_gt_flags(overlaps, n_gt, threshold).sum())
    return true_positive, n_pred - true_positive, n_gt - true_positive


def spell_scores(gt_codes, pred_codes, runs, ious=SPELL_IOUS):
    """Possession-spell detection precision/recall/F1 at each IoU, plus the mean F1 over them."""
    gt_spells = possession_spells(gt_codes, runs)
    pred_spells = possession_spells(pred_codes, runs)
    overlaps = spell_overlaps(gt_spells, pred_spells)

    per_iou, f1s = {}, []
    for threshold in ious:
        true_positive, false_positive, false_negative = match_spells(
            overlaps, len(gt_spells), len(pred_spells), threshold)
        precision = true_positive / float(true_positive + false_positive) \
            if true_positive + false_positive else 0.0
        recall = true_positive / float(true_positive + false_negative) \
            if true_positive + false_negative else 0.0
        f1 = 2.0 * precision * recall / (precision + recall) if precision + recall else 0.0
        per_iou[threshold] = {"precision": precision, "recall": recall, "f1": f1,
                              "n_matched": true_positive, "n_spurious": false_positive,
                              "n_missed": false_negative}
        f1s.append(f1)

    return {
        "per_iou": per_iou,
        "mean_f1": float(np.mean(f1s)) if f1s else 0.0,
        "n_gt": len(gt_spells),
        "n_pred": len(pred_spells),
    }


def possession_stats(codes, runs):
    """What a coach reads off a possession signal: how many, how long, and the home share.

    Reported alongside the F1s because they need no metric literacy -- a predicted possession
    count next to the truth's states the failure more plainly than any score. Note the home share
    is a poor discriminator on its own: a jittery submission can get it almost exactly right while
    inventing hundreds of possessions, so it is reported and never ranked on.
    """
    spells = possession_spells(codes, runs)
    lengths = [b - a for a, b, _ in spells]
    alive = int(np.sum((codes == H) | (codes == A)))
    return {
        "n_spells": len(spells),
        "mean_duration_s": float(np.mean(lengths)) / FPS if lengths else 0.0,
        "home_share": float(np.sum(codes == H)) / alive if alive else 0.0,
    }


# -- bootstrap ---------------------------------------------------------------------------------

def bootstrap_macro_f1(gt_codes, pred_codes, runs, n_draws,
                       seed=BOOTSTRAP_SEED, percentiles=BOOTSTRAP_PERCENTILES):
    """Block-bootstrap interval for macro-F1, resampling whole GT segments.

    Segments, not frames, because frames inside a possession are not independent observations.
    Returns (low, high) or (None, None) when disabled.
    """
    if not n_draws:
        return None, None

    gt_segments = segments(gt_codes, runs)
    if not gt_segments:
        return None, None

    # Per-segment prediction histogram, so a draw is a matrix add rather than a rescan of 199k
    # frames: contributions[i, p] = frames of segment i the submission called p.
    gt_of_segment = np.array([code for _, _, code in gt_segments], dtype=np.int64)
    contributions = np.zeros((len(gt_segments), N_LABELS), dtype=np.int64)
    for index, (start, stop, _) in enumerate(gt_segments):
        contributions[index] = np.bincount(pred_codes[start:stop].astype(np.int64),
                                           minlength=N_LABELS)

    rng = np.random.RandomState(seed)
    scores = np.empty(n_draws, dtype=np.float64)
    for draw in range(n_draws):
        picks = rng.randint(0, len(gt_segments), len(gt_segments))
        cm3 = np.zeros((N_SCORED, N_LABELS), dtype=np.int64)
        np.add.at(cm3, gt_of_segment[picks], contributions[picks])
        scores[draw] = macro_f1(cm3)
    low, high = np.percentile(scores, percentiles)
    return float(low), float(high)


def bootstrap_spell_f1(gt_codes, pred_codes, runs, n_draws,
                       seed=BOOTSTRAP_SEED, percentiles=BOOTSTRAP_PERCENTILES):
    """Bootstrap interval for spell_f1_mean, resampling whole possessions.

    Possessions, not segments and not frames, because spell_f1_mean scores each possession as one
    hit-or-miss observation, and that count is the sample size governing its variance. This is the
    interval that matters once the board ranks on spellF1; bootstrap_macro_f1 above answers the
    same question for the frame-level metric.

    Returns (low, high) or (None, None) when disabled.
    """
    if not n_draws:
        return None, None

    gt_spells = possession_spells(gt_codes, runs)
    if not gt_spells:
        return None, None
    pred_spells = possession_spells(pred_codes, runs)
    overlaps = spell_overlaps(gt_spells, pred_spells)
    n_gt, n_pred = len(gt_spells), len(pred_spells)

    # Matched-or-not per possession per threshold, computed once. A draw is then a resample of
    # rows rather than a re-run of the matching.
    flags = np.vstack([matched_gt_flags(overlaps, n_gt, threshold)
                       for threshold in SPELL_IOUS])

    rng = np.random.RandomState(seed)
    scores = np.empty(n_draws, dtype=np.float64)
    for draw in range(n_draws):
        picks = rng.randint(0, n_gt, n_gt)
        f1s = []
        for row in flags:
            true_positive = int(row[picks].sum())
            false_negative = n_gt - true_positive
            # n_pred is fixed while the resampled tp moves, so for a submission predicting fewer
            # spells than the truth a draw can imply tp > n_pred. Clamp rather than go negative.
            false_positive = max(0, n_pred - true_positive)
            f1s.append(2.0 * true_positive / (2 * true_positive + false_positive + false_negative)
                       if true_positive else 0.0)
        scores[draw] = np.mean(f1s)
    low, high = np.percentile(scores, percentiles)
    return float(low), float(high)


# -- entry point -------------------------------------------------------------------------------

def evaluate(gt_codes, pred_codes, taus=TAUS, bootstrap_n=BOOTSTRAP_N, typed="to"):
    """Every metric for one submission. The only function run_evaluation.py needs.

    Touches the full-length arrays exactly twice: once for the confusion matrix, once for the
    run-length encoding behind the temporal metrics.
    """
    if len(gt_codes) != len(pred_codes):
        raise ValueError("length mismatch: gt {} vs pred {}".format(
            len(gt_codes), len(pred_codes)))

    cm = confusion(gt_codes, pred_codes)
    cm3 = scored_confusion(cm)

    runs = valid_runs(gt_codes)
    filled = fill_abstentions(pred_codes, runs)
    gt_trans = transitions(gt_codes, runs)
    pred_trans = transitions(filled, runs)

    n_gt_seg, n_pred_seg, frag = fragmentation(gt_codes, filled, runs)
    gt_share, pred_share, share_err, share_defined = possession_share(cm3)
    strict_team, both_alive_team = team_accuracy(cm3)
    boot_low, boot_high = bootstrap_macro_f1(gt_codes, pred_codes, runs, bootstrap_n)
    spell_boot_low, spell_boot_high = bootstrap_spell_f1(gt_codes, filled, runs, bootstrap_n)

    # Possession-spell level, on the abstention-filled prediction for the same reason the
    # transition metrics use it: 'H X X H' is one possession the model went quiet during, not
    # two possessions with a gap.
    spells = spell_scores(gt_codes, filled, runs)
    gt_stats = possession_stats(gt_codes, runs)
    pred_stats = possession_stats(filled, runs)

    result = {
        "macro_f1": macro_f1(cm3),
        # Co-headline, deliberately not folded into macro_f1: they answer different questions
        # ("right label" vs "right possessions") and their disagreement is the useful signal.
        "spell_f1_mean": spells["mean_f1"],
        "spell_f1_at_headline": spells["per_iou"][SPELL_IOU_HEADLINE]["f1"],
        "spell_iou_headline": SPELL_IOU_HEADLINE,
        "spell_bootstrap_low": spell_boot_low,
        "spell_bootstrap_high": spell_boot_high,
        "n_gt_spells": spells["n_gt"],
        "n_pred_spells": spells["n_pred"],
        "spell_count_error": spells["n_pred"] - spells["n_gt"],
        "mean_spell_duration_s": pred_stats["mean_duration_s"],
        "gt_mean_spell_duration_s": gt_stats["mean_duration_s"],
        "accuracy": accuracy(cm3),
        "kappa": cohens_kappa(cm3),
        "alive_dead_f1": alive_dead_f1(cm3),
        "team_acc_gt_alive": strict_team,
        "team_acc_both_alive": both_alive_team,
        "gt_home_share": gt_share,
        "pred_home_share": pred_share,
        "share_err": share_err,
        "share_defined": share_defined,
        "n_gt_segments": n_gt_seg,
        "n_pred_segments": n_pred_seg,
        "fragmentation": frag,
        "n_frames": int(len(gt_codes)),
        "n_graded": int(cm3.sum()),
        "n_abstain_on_graded": int(cm3[:, X].sum()),
        "bootstrap_low": boot_low,
        "bootstrap_high": boot_high,
        "bootstrap_n": bootstrap_n,
        "confusion": cm.tolist(),
        "per_class": {},
        "transitions": {},
        # The per-IoU breakdown is for the detail block and the JSON report, not the CSV: five
        # thresholds x three figures would add fifteen columns for what the mean already ranks.
        "spell_f1": spells["per_iou"],
        "gt_home_share_spells": gt_stats["home_share"],
    }
    for k, name in enumerate(SCORED):
        precision, recall, f1 = per_class_prf(cm3, k)
        result["per_class"][name] = {
            "precision": precision, "recall": recall, "f1": f1,
            "support": int(cm3[k, :].sum()),
        }
    for tol in taus:
        result["transitions"][tol] = transition_scores(gt_trans, pred_trans, tol, typed)
    return result


OFFICIAL_SOURCE_LICENSE = 'SCOPE OF THIS LICENCE\n---------------------\n\nThe MIT Licence below covers the contents of this repository only: the source code, the\ndocumentation, and the public 5-minute ground truth in evaluation/gt/.\n\nIt does NOT cover the match data — the videos, the tracking data, the Smart Tagging and the\nhomography. Those assets are separately licensed for this competition only, under the terms you\naccept at enrolment, and nothing in the licence below grants any right to use or redistribute\nthem. See DATA.md and RULES.md.\n\n---\n\nMIT License\n\nCopyright (c) 2026-2027 Metrica Sports\n\nPermission is hereby granted, free of charge, to any person obtaining a copy\nof this software and associated documentation files (the "Software"), to deal\nin the Software without restriction, including without limitation the rights\nto use, copy, modify, merge, publish, distribute, sublicense, and/or sell\ncopies of the Software, and to permit persons to whom the Software is\nfurnished to do so, subject to the following conditions:\n\nThe above copyright notice and this permission notice shall be included in all\ncopies or substantial portions of the Software.\n\nTHE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR\nIMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,\nFITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE\nAUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER\nLIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,\nOUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE\nSOFTWARE.\n'
''',
    'gap_solver.roi': r'''"""Local clock-box selection; choosing a crop does not annotate possession."""
import json
import tempfile
from math import ceil, isfinite
from pathlib import Path

from .clock_ocr import _run, crop_filter, probe_video


def normalise_box(box, width, height, display_scale=1):
    if width <= 0 or height <= 0 or display_scale <= 0 or any(not isfinite(v) for v in box):
        raise ValueError('invalid selection dimensions')
    x0,x1 = sorted((box[0]*display_scale, box[2]*display_scale))
    y0,y1 = sorted((box[1]*display_scale, box[3]*display_scale))
    x0,x1 = max(0,min(width,x0)), max(0,min(width,x1))
    y0,y1 = max(0,min(height,y0)), max(0,min(height,y1))
    if x1-x0 < 8 or y1-y0 < 8:
        raise ValueError('Draw a larger box around the COMPLETE clock digits.')
    return x0/width, y0/height, (x1-x0)/width, (y1-y0)/height


def load_roi(path, source):
    config=json.loads(Path(path).read_text(encoding='utf-8'))
    if config.get('source') != source:
        raise ValueError('Saved clock box belongs to a different camera source')
    roi=tuple(float(v) for v in config['roi'])
    if len(roi) != 4:
        raise ValueError('Saved clock ROI needs four values')
    crop_filter(roi,0,1,1)
    return roi


def extract_reference_frame(video, frame, output, ffmpeg='ffmpeg', ffprobe='ffprobe'):
    count,_=probe_video(video,ffprobe)
    if not 0 <= frame < count:
        raise ValueError('Clock selection frame is outside video')
    _run([ffmpeg,'-hide_banner','-loglevel','error','-i',str(video),'-an',
          '-vf','select=eq(n\\,{})'.format(frame),'-frames:v','1','-update','1','-y',str(output)],3600)
    if not Path(output).is_file():
        raise ValueError('No reference frame was decoded')


def choose_roi(video, frame, source, save_path, ffmpeg='ffmpeg', ffprobe='ffprobe'):
    try:
        import tkinter as tk
    except ImportError as exc:
        raise ValueError('Clock selector needs tkinter. In this conda environment install: conda install tk') from exc
    print('Preparing one local reference frame for clock selection...',flush=True)
    with tempfile.TemporaryDirectory(prefix='local-clock-box-') as d:
        image_path=Path(d)/'reference.png'
        extract_reference_frame(video,frame,image_path,ffmpeg,ffprobe)
        try:
            window=tk.Tk()
        except tk.TclError as exc:
            raise ValueError('A local desktop display is needed for --select-roi') from exc
        window.title('Select clock digits - football pipeline')
        try:
            original=tk.PhotoImage(file=str(image_path))
            width,height=original.width(),original.height()
            max_width=max(320,min(1440,window.winfo_screenwidth()-100))
            max_height=max(180,min(700,window.winfo_screenheight()-330))
            factor=max(1,ceil(max(width/max_width,height/max_height)))
            shown=original.subsample(factor,factor)
            tk.Label(window,text='Drag around ALL the clock digits, with a small margin. Exclude the score.').pack(padx=10,pady=5)
            canvas=tk.Canvas(window,width=shown.width(),height=shown.height(),highlightthickness=0)
            canvas.pack()
            canvas.create_image(0,0,anchor='nw',image=shown)
            message=tk.StringVar(value='Drag a box. Inspect the enlarged preview below, then click Use clock box.')
            tk.Label(window,textvariable=message).pack(pady=3)
            preview=tk.Label(window)
            preview.pack(pady=3)
            selection=[None]
            accepted=[False]
            start=[0,0]
            rectangle=[None]
            preview_image=[None]
            buttons=tk.Frame(window)
            buttons.pack(pady=5)

            def accept():
                if selection[0] is not None:
                    accepted[0]=True
                    window.destroy()

            use_button=tk.Button(buttons,text='Use clock box',state='disabled',command=accept)
            use_button.pack(side='left',padx=5)
            tk.Button(buttons,text='Cancel',command=window.destroy).pack(side='left',padx=5)

            def press(event):
                start[:]=[event.x,event.y]
                selection[0]=None
                use_button.configure(state='disabled')
                if rectangle[0] is not None:
                    canvas.delete(rectangle[0])
                rectangle[0]=canvas.create_rectangle(event.x,event.y,event.x,event.y,outline='#ff3030',width=2)

            def drag(event):
                if rectangle[0] is not None:
                    canvas.coords(rectangle[0],start[0],start[1],event.x,event.y)

            def release(event):
                drag(event)
                try:
                    roi=normalise_box((start[0],start[1],event.x,event.y),width,height,factor)
                except ValueError as exc:
                    message.set(str(exc))
                    return
                x,y,w,h=roi
                left,top,right,bottom=round(x*width),round(y*height),round((x+w)*width),round((y+h)*height)
                zoom=max(1,min(4,600//max(1,right-left),100//max(1,bottom-top)))
                enlarged=tk.PhotoImage()
                enlarged.tk.call(str(enlarged),'copy',str(original),'-from',left,top,right,bottom,'-zoom',zoom,zoom)
                preview_image[0]=enlarged
                preview.configure(image=enlarged)
                selection[0]=roi
                message.set('Does the preview show the complete clock and exclude the score? Redraw if needed.')
                use_button.configure(state='normal')

            canvas.bind('<ButtonPress-1>',press)
            canvas.bind('<B1-Motion>',drag)
            canvas.bind('<ButtonRelease-1>',release)
            window.mainloop()
        finally:
            try:
                window.destroy()
            except tk.TclError:
                pass
        if not accepted[0] or selection[0] is None:
            raise ValueError('Clock-box selection cancelled. OCR was not run.')
        result={'source':source,'roi':list(selection[0]),'video_width':width,
                'video_height':height,'selection_frame':frame}
        path=Path(save_path)
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
        print('Saved clock box: '+str(path),flush=True)
        return selection[0]
''',
    'gap_solver.selection': r'''"""Development-only external augmentation and portable export helpers; no challenge inputs."""
from dataclasses import replace
import numpy as np
from .tactical import FEATURE_NAMES


def ball_mask(periods,rate,seed=1729):
    periods=np.asarray(periods)
    if periods.ndim!=1 or not len(periods) or not np.isin(periods,[1,2]).all() or not 0<=rate<=1:
        raise ValueError('invalid external masking request')
    mask=np.zeros(len(periods),dtype=bool)
    target=round(rate*len(periods))
    stops=np.empty(len(periods),dtype=np.int32)
    starts=np.r_[0,np.flatnonzero(periods[1:]!=periods[:-1])+1,len(periods)]
    for first,stop in zip(starts,starts[1:]):
        stops[first:stop]=stop
    rng=np.random.RandomState(seed)
    durations=(5,15,50,125)
    count=0
    while count<target:
        first=int(rng.randint(len(periods)))
        stop=min(int(stops[first]),first+durations[int(rng.randint(len(durations)))])
        candidates=np.flatnonzero(~mask[first:stop])+first
        chosen=candidates[:target-count]
        mask[chosen]=True
        count+=len(chosen)
    return mask


def mask_frames(frames,mask):
    if len(frames)!=len(mask):
        raise ValueError('external observation mask dimensions differ')
    return [replace(f,ball_x=None,ball_y=None,home_distance=None,away_distance=None) if hidden else f
            for f,hidden in zip(frames,mask)]


def export_tree(classifier):
    if list(classifier.classes_)!=[0,1,2] or classifier.n_features_in_!=len(FEATURE_NAMES):
        raise ValueError('external state classifier needs the declared feature schema and H/A/D targets')
    tree=classifier.tree_
    values=tree.value[:,0,:].astype(float)
    values/=values.sum(axis=1,keepdims=True)
    return dict(feature_names=list(FEATURE_NAMES),children_left=tree.children_left.tolist(),
                children_right=tree.children_right.tolist(),feature=tree.feature.tolist(),
                threshold=tree.threshold.tolist(),probabilities=values.tolist())
''',
    'gap_solver.skillcorner': r'''"""Independent-provider features and phase reference; no reference-dependent inference filtering."""
from dataclasses import dataclass
from collections import Counter
import csv
import hashlib
import json
from math import isfinite
from pathlib import Path
import uuid

import numpy as np
from .motion import MotionFrame,motion_frame

_ADAPTER_SOURCES={name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
                  for name in ('skillcorner.py','motion.py')}


def _sha256(path):
    digest=hashlib.sha256()
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda:handle.read(4*1024*1024),b''):digest.update(chunk)
    return digest.hexdigest()


@dataclass
class MotionMatch:
    match_id: str
    records: list
    reference: object
    source_frames: object
    notes: dict
    native_ball_available: object=None
    native_periods: object=None
    native_reference: object=None

    def frames(self):return self.records

    @property
    def periods(self):return np.fromiter((f.period for f in self.records),dtype=np.uint8,count=len(self.records))


def _clock(value):
    parts=str(value).split(':')
    if len(parts)!=3:raise ValueError('tracking timestamp must be HH:MM:SS')
    h,m,s=map(float,parts)
    if not all(isfinite(x) and x>=0 for x in (h,m,s)) or m>=60 or s>=60:
        raise ValueError('invalid tracking clock')
    return h*3600+m*60+s


def _phase_clock(value):
    parts=str(value).split(':')
    if len(parts)==2:
        minute,second=map(float,parts)
        if not isfinite(minute) or not isfinite(second) or minute<0 or not 0<=second<60:raise ValueError('invalid phase clock')
        return minute*60+second
    return _clock(value)


def _position(value,detected_only):
    detected=value.get('is_detected')
    if detected is not None and type(detected) is not bool:
        raise ValueError('observation flag must be JSON boolean or null')
    x,y=value.get('x'),value.get('y')
    if x is None or y is None:return None
    if type(x) not in (int,float) or type(y) not in (int,float) or not isfinite(x) or not isfinite(y):
        raise ValueError('invalid external position')
    return (float(x),float(y)) if not detected_only or detected is True else None


def load_skillcorner(metadata_path,tracking_path,phases_path,detected_only=True):
    meta=json.loads(Path(metadata_path).read_text(encoding='utf-8-sig'))
    home,away=meta['home_team']['id'],meta['away_team']['id']
    if home==away:raise ValueError('external teams must be distinct')
    length,width=float(meta['pitch_length']),float(meta['pitch_width'])
    if not all(isfinite(x) and x>0 for x in (length,width)):raise ValueError('invalid external pitch')
    membership={}
    for player in meta['players']:
        person,team=player['id'],player['team_id']
        if person in membership or team not in (home,away):raise ValueError('invalid external roster membership')
        membership[person]=0 if team==home else 1
    def normalize(point):return ((point[0]/length+.5)*105.3,(point[1]/width+.5)*68.)
    native=[];previous=-1;origins={};groups=Counter();raw_periods=Counter();native_observed=0
    with open(tracking_path,encoding='utf-8-sig') as handle:
        for line in handle:
            row=json.loads(line)
            number=row['frame']
            if type(number) is not int or not previous<number<=1000000:
                raise ValueError('native frame IDs must increase without duplication')
            while len(native)<number:native.append(None)
            source_period=row.get('period');raw_periods[str(source_period)]+=1
            period=source_period if source_period in (1,2) else 0
            if period:
                time=_clock(row.get('timestamp'))
                origins.setdefault(period,time-number/10)
                if abs(time-(origins[period]+number/10))>.011:
                    raise ValueError('native tracking clock disagrees with 10 Hz indices')
            ball=_position(row.get('ball_data') or {},detected_only)
            players=[{},{}];seen=set()
            for player in row.get('player_data') or []:
                person=player.get('player_id')
                if person not in membership or person in seen:
                    raise ValueError('unknown/duplicate tracked player identity')
                seen.add(person)
                point=_position(player,detected_only)
                if point is not None:players[membership[person]][person]=normalize(point)
            groups[str((row.get('possession') or {}).get('group'))]+=1
            native_observed+=ball is not None
            native.append(dict(period=period,ball=normalize(ball) if ball is not None else None,
                               players=players,detected=(row.get('ball_data') or {}).get('is_detected') is True))
            previous=number
    if not native:raise ValueError('external tracking is empty')
    n=len(native);native_ref=np.full(n,3,dtype=np.uint8);annotated=np.zeros(n,dtype=bool);conflict=np.zeros(n,dtype=bool)
    period_conflict=np.zeros(n,dtype=bool);requested=np.zeros(n,dtype=bool);reconciliation=Counter()
    with open(phases_path,newline='',encoding='utf-8-sig') as handle:
        for row in csv.DictReader(handle):
            first,stop,period=int(row['frame_start']),int(row['frame_end']),int(row['period'])
            if first<0 or stop<first:raise ValueError('invalid phase interval')
            reconciliation['intervals_total']+=1
            if period not in (1,2):
                reconciliation['unsupported_period_intervals']+=1
                continue
            reconciliation['requested_native_frames']+=stop-first
            reconciliation['out_of_range_native_frames']+=max(0,stop-max(first,n))
            clock_bad=False
            if all(row.get(key) not in (None,'') for key in ('time_start','time_end','duration')):
                reconciliation['clock_checked_intervals']+=1
                try:
                    start_t,stop_t=_phase_clock(row['time_start']),_phase_clock(row['time_end'])
                    duration=float(row['duration'])
                    clock_bad=(period not in origins or not isfinite(duration)
                         or abs(start_t-(origins.get(period,0)+first/10))>.011
                         or abs(stop_t-(origins.get(period,0)+stop/10))>.011
                         or abs(duration-(stop-first)/10)>.011)
                except (TypeError,ValueError):clock_bad=True
                if clock_bad:reconciliation['clock_disagreement_intervals']+=1
            else:reconciliation['clock_unverified_intervals']+=1
            try:team=int(row['team_in_possession_id'])
            except (TypeError,ValueError):team=None
            code=0 if team==home else 1 if team==away else 3
            if code==3:reconciliation['invalid_team_intervals']+=1
            for i in range(first,min(stop,n)):
                requested[i]=True
                if native[i] is None:
                    reconciliation['missing_native_rows']+=1
                    continue
                if clock_bad:
                    conflict[i]=True;native_ref[i]=3
                    continue
                if native[i]['period']!=period:
                    period_conflict[i]=True;conflict[i]=True;native_ref[i]=3
                    continue
                if annotated[i] and native_ref[i]!=code:conflict[i]=True
                annotated[i]=True;native_ref[i]=3 if conflict[i] else code
    count=(n*5+1)//2
    records=[];reference=np.full(count,3,dtype=np.uint8);mapping=np.arange(count,dtype=np.float64)*.4
    empty=dict(period=0,ball=None,players=[{},{}],detected=False)
    def value_at(k):return native[k] if 0<=k<n and native[k] is not None else empty
    for k in range(count):
        index=(k*2)//5;fraction=(k*2%5)/5
        left=value_at(index);right=value_at(index+1);period=left['period']
        compatible=period!=0 and right['period']==period
        def interpolate(a,b):return tuple(x+(y-x)*fraction for x,y in zip(a,b))
        ball=(left['ball'] if fraction==0 else interpolate(left['ball'],right['ball'])
              if compatible and left['ball'] is not None and right['ball'] is not None else None)
        ball_interpolated=bool(fraction and ball is not None)
        provenance=('native_detected' if left['detected'] else 'provider_extrapolated') if ball is not None and not fraction else (
            'interpolated_detected' if left['detected'] and right['detected'] else 'interpolated_available') if ball is not None else 'missing'
        native_detection=bool(ball is not None and not fraction and left['detected'])
        sample_time=index/10 if ball is not None and not fraction else None
        players=[{},{}];player_interpolated=False
        for side in (0,1):
            if fraction==0:players[side]=dict(left['players'][side])
            elif compatible:
                players[side]={person:interpolate(point,right['players'][side][person])
                               for person,point in left['players'][side].items() if person in right['players'][side]}
                player_interpolated=player_interpolated or bool(players[side])
        # Isolated native samples may sit halfway between 25 Hz ticks. Retain one
        # at the following tick (<=.02 s), without filling the missing interval.
        nearest=(index*5+1)//2
        snap=k==nearest
        if snap and period:
            if ball is None and left['ball'] is not None:
                ball=left['ball'];ball_interpolated=False;native_detection=left['detected'];sample_time=index/10
                provenance='snapped_detected' if left['detected'] else 'provider_extrapolated'
            for side in (0,1):
                for person,point in left['players'][side].items():players[side].setdefault(person,point)
        members=[tuple(sorted(x)) for x in players]
        records.append(motion_frame(period,ball,
            tuple(players[0][p] for p in members[0]),tuple(players[1][p] for p in members[1]),*members,
            native_frame=index,ball_native_observation=native_detection,ball_provenance=provenance,
            ball_interpolated=ball_interpolated,ball_sample_time_s=sample_time,
            interpolated=bool(ball_interpolated or player_interpolated)))
        if period:reference[k]=native_ref[index]
    notes=dict(fps=25,native_fps=10,native_grid_rows=n,canonical_rows=count,
        native_numeric_positions_used=native_observed,raw_tracking_possession_groups=dict(groups),raw_period_counts=dict(raw_periods),
        position_regime='detected_only' if detected_only else 'available_including_extrapolation',
        reference_type='provider phase reference; known in-play H/A only; missing phases are unknown, not D',
        unknown_reference_preserved=True,reference_fields_excluded_from_features=True,
        resampling='linear only across consecutive available native samples within period; isolated samples snapped <=.02s',
        phase_interval='left closed, right open; native frame IDs',canonical_pitch_m=[105.3,68.])
    notes['phase_period_conflict_native_frames']=int(period_conflict.sum())
    reconciliation['requested_unique_native_frames']=int(requested.sum())
    reconciliation['assigned_known_reference_native_frames']=int((native_ref<2).sum())
    reconciliation['conflicting_native_frames']=int(conflict.sum())
    reconciliation['retained_reference_fraction']=float((native_ref<2).sum()/requested.sum()) if requested.any() else 0.
    notes['phase_reconciliation']=dict(reconciliation)
    notes['input_sha256']={Path(p).name:_sha256(p) for p in (metadata_path,tracking_path,phases_path)}
    notes['ball_sample_time_definition']='source-frame elapsed seconds, not match clock; absent for synthetic blends'
    return MotionMatch(str(meta['id']),records,reference,mapping,notes,
        np.asarray([r is not None and r['ball'] is not None for r in native],dtype=bool),
        np.asarray([r['period'] if r is not None else 0 for r in native],dtype=np.uint8),native_ref)


def save_motion_cache(match,prefix):
    prefix=Path(prefix);prefix.parent.mkdir(parents=True,exist_ok=True)
    frames=match.frames();n=len(frames)
    generation=uuid.uuid4().hex
    identity=dict(match_id=match.match_id,position_regime=match.notes['position_regime'],
                  input_sha256=match.notes.get('input_sha256',{}),adapter_sources=_ADAPTER_SOURCES)
    identity_digest=hashlib.sha256(json.dumps(identity,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    shared=dict(generation_id=np.asarray(generation),input_identity=np.asarray(identity_digest),
                match_id=np.asarray(match.match_id),position_regime=np.asarray(match.notes['position_regime']))
    arrays=dict(periods=match.periods,source_frames=np.asarray(match.source_frames,dtype=np.float64),
        ball=np.asarray([(f.ball_x if f.ball_x is not None else np.nan,f.ball_y if f.ball_y is not None else np.nan) for f in frames]),
        flags=np.asarray([(f.geometry_valid,2 if f.ball_native_observation is None else f.ball_native_observation,
                           f.interpolated,f.ball_interpolated) for f in frames],dtype=np.uint8),
        ball_provenance=np.asarray([f.ball_provenance for f in frames]),
        ball_sample_time=np.asarray([f.ball_sample_time_s if f.ball_sample_time_s is not None else np.nan for f in frames]),
        native_frame=np.asarray([f.native_frame if f.native_frame is not None else -1 for f in frames],dtype=np.int32),**shared)
    if match.native_ball_available is not None:
        arrays.update(native_ball_available=match.native_ball_available,native_periods=match.native_periods)
    for side in ('home','away'):
        maximum=max((len(getattr(f,side+'_xy')) for f in frames),default=0)
        xy=np.full((n,maximum,2),np.nan,dtype=np.float64);ids=np.full((n,maximum),-1,dtype=np.int64)
        counts=np.zeros(n,dtype=np.uint8)
        for i,f in enumerate(frames):
            points=getattr(f,side+'_xy');members=getattr(f,side+'_ids');counts[i]=len(points)
            if points:xy[i,:len(points)]=points;ids[i,:len(points)]=members
        arrays[side+'_xy']=xy;arrays[side+'_ids']=ids;arrays[side+'_count']=counts
    def publish_npz(suffix,values):
        target=Path(str(prefix)+suffix);temporary=Path(str(target)+'.new')
        with temporary.open('wb') as handle:np.savez_compressed(handle,**values)
        temporary.replace(target)
    publish_npz('.features.npz',arrays)
    targets=dict(reference=match.reference,periods=match.periods,source_frames=match.source_frames,**shared)
    if match.native_reference is not None:targets['native_reference']=match.native_reference
    publish_npz('.reference.npz',targets)
    array_hashes={suffix:_sha256(str(prefix)+suffix) for suffix in ('.features.npz','.reference.npz')}
    target=Path(str(prefix)+'.metadata.json');temporary=Path(str(target)+'.new')
    temporary.write_text(json.dumps(dict(schema_version=2,match_id=match.match_id,notes=match.notes,
        adapter_sources=_ADAPTER_SOURCES,generation_id=generation,input_identity=identity_digest,
        position_regime=match.notes['position_regime'],array_sha256=array_hashes),indent=2)+'\n',encoding='utf-8')
    temporary.replace(target)


def load_motion_cache(prefix):
    prefix=str(prefix);metadata=json.loads(Path(prefix+'.metadata.json').read_text(encoding='utf-8'))
    if metadata.get('adapter_sources')!=_ADAPTER_SOURCES:raise ValueError('Motion cache was built by a different adapter; rebuild from verified raw sources')
    if metadata.get('schema_version')!=2 or metadata['position_regime']!=metadata['notes']['position_regime']:
        raise ValueError('Motion cache provenance schema/regime disagree')
    for suffix in ('.features.npz','.reference.npz'):
        if _sha256(prefix+suffix)!=metadata['array_sha256'][suffix]:raise ValueError('Motion cache generation content changed')
    with np.load(prefix+'.features.npz',allow_pickle=False) as feature_archive,np.load(prefix+'.reference.npz',allow_pickle=False) as reference_archive:
        features={key:feature_archive[key] for key in feature_archive.files}
        target={key:reference_archive[key] for key in reference_archive.files}
        for field in ('generation_id','input_identity','match_id','position_regime'):
            if any(str(a[field].item())!=str(metadata[field]) for a in (features,target)):
                raise ValueError('Motion cache generation identities disagree')
        if any(not np.array_equal(features[k],target[k]) for k in ('periods','source_frames')):
            raise ValueError('motion feature/reference cache indices disagree')
        records=[]
        for i,period in enumerate(features['periods']):
            players=[];members=[]
            for side in ('home','away'):
                count=int(features[side+'_count'][i]);players.append(tuple(map(tuple,features[side+'_xy'][i,:count])))
                members.append(tuple(map(int,features[side+'_ids'][i,:count])))
            ball=tuple(features['ball'][i]) if np.isfinite(features['ball'][i]).all() else None
            flags=features['flags'][i];native=int(features['native_frame'][i]);sample_time=float(features['ball_sample_time'][i])
            records.append(motion_frame(int(period),ball,*players,*members,geometry_valid=bool(flags[0]),
                ball_native_observation=None if flags[1]==2 else bool(flags[1]),interpolated=bool(flags[2]),
                ball_interpolated=bool(flags[3]),ball_provenance=str(features['ball_provenance'][i]),
                ball_sample_time_s=sample_time if isfinite(sample_time) else None,native_frame=native if native>=0 else None))
        return MotionMatch(metadata['match_id'],records,target['reference'].copy(),features['source_frames'].copy(),metadata['notes'],
            features['native_ball_available'].copy() if 'native_ball_available' in features else None,
            features['native_periods'].copy() if 'native_periods' in features else None,
            target['native_reference'].copy() if 'native_reference' in target else None)
''',
    'gap_solver.tactical': r'''"""Portable geometry-only state inference, selected exclusively on external references."""
from collections import deque
from dataclasses import dataclass,replace
from itertools import zip_longest
from math import hypot,isfinite
import struct

from .core import Config,Decision,_blocks,_candidate,infer


FEATURE_NAMES=('ball_observed','home_observed','away_observed','home_distance','away_distance',
               'distance_margin','min_distance','ball_edge_x','ball_edge_y','ball_speed',
               'recent_speed','slow_ball_age','missing_ball_age','last_home_distance',
               'last_away_distance','last_control_home','last_control_away','last_control_age')


def feature_rows(frames):
    """No reference/status/tag inputs. Physical features and retained confirmed control only."""
    cfg=Config()
    previous_period=None
    previous_ball=None
    speeds=deque(maxlen=12)
    last_ball=last_control=None
    last_side=candidate=''
    run=0
    last_h=last_a=30.
    slow=0.
    for i,f in enumerate(frames):
        if f.period not in (0,1,2):
            raise ValueError('invalid tactical period')
        if f.period!=previous_period or f.period==0:
            previous_ball=None;speeds.clear();last_ball=last_control=None
            last_side=candidate='';run=0;last_h=last_a=30.;slow=0.
        previous_period=f.period
        h_ok=f.home_distance is not None and isfinite(f.home_distance) and f.home_distance>=0
        a_ok=f.away_distance is not None and isfinite(f.away_distance) and f.away_distance>=0
        h=min(30.,f.home_distance) if h_ok else 30.
        a=min(30.,f.away_distance) if a_ok else 30.
        observed=f.ball_observed and f.period!=0
        speed=0.
        if observed:
            if previous_ball is not None:
                speed=min(50.,hypot(f.ball_x-previous_ball[0],f.ball_y-previous_ball[1])*25)
                slow=min(10.,slow+.04) if speed<=.5 else 0.
            else:
                slow=0.
            previous_ball=(f.ball_x,f.ball_y)
            last_ball=i;last_h=h;last_a=a
        else:
            previous_ball=None;slow=0.
        speeds.append(speed)
        side=_candidate(f,cfg) if f.period else ''
        if side and side==candidate:
            run+=1
        else:
            candidate=side;run=1 if side else 0
        if run>=6:
            last_side=side;last_control=i
        row=(float(observed),float(h_ok),float(a_ok),h,a,a-h,min(h,a),
             abs(f.ball_x-52.65)/52.65 if observed else 0.,abs(f.ball_y-34)/34 if observed else 0.,
             speed,sum(speeds)/len(speeds),slow,min(10.,(i-last_ball)/25) if last_ball is not None else 10.,
             last_h,last_a,float(last_side=='H'),float(last_side=='A'),
             min(10.,(i-last_control)/25) if last_control is not None else 10.)
        yield row


@dataclass(frozen=True)
class Policy:
    confidence: float=.9
    minimum_run_frames: int=6
    max_gap_s: float=2.
    bridge_s: float=2.

    def validate(self):
        if (not isfinite(self.confidence) or not 0<self.confidence<=1
                or type(self.minimum_run_frames) is not int or self.minimum_run_frames<1
                or any(not isfinite(x) or x<0 for x in (self.max_gap_s,self.bridge_s))):
            raise ValueError('invalid tactical policy')


class PortableTree:
    def __init__(self,model):
        if tuple(model.get('feature_names',()))!=FEATURE_NAMES:
            raise ValueError('exported tree feature schema differs from portable geometry features')
        names=('children_left','children_right','feature','threshold','probabilities')
        if any(name not in model for name in names):
            raise ValueError('incomplete exported tree')
        n=len(model['feature'])
        if not n or n>4095 or any(len(model[name])!=n for name in names):
            raise ValueError('invalid exported tree dimensions')
        reachable={0}
        for i in range(n):
            left,right=model['children_left'][i],model['children_right'][i]
            probabilities=model['probabilities'][i]
            if (len(probabilities)!=3 or any(not isfinite(p) or not 0<=p<=1 for p in probabilities)
                    or abs(sum(probabilities)-1)>1e-6 or not isfinite(model['threshold'][i])):
                raise ValueError('invalid exported leaf support')
            if left==right==-1:
                continue
            if (type(left) is not int or type(right) is not int or not i<left<n or not i<right<n
                    or left==right or not 0<=model['feature'][i]<len(FEATURE_NAMES)):
                raise ValueError('invalid/cyclic exported tree')
            if i in reachable:
                reachable.update((left,right))
        if len(reachable)!=n:
            raise ValueError('unreachable exported tree nodes')
        self.model=model

    def predict(self,row):
        if len(row)!=len(FEATURE_NAMES) or any(not isfinite(x) for x in row):
            raise ValueError('invalid portable feature row')
        node=0
        while self.model['children_left'][node]!=-1:
            key=self.model['feature'][node]
            # sklearn trees compare float32 inputs against stored float64 thresholds.
            value=struct.unpack('<f',struct.pack('<f',row[key]))[0]
            node=(self.model['children_left'][node] if value<=self.model['threshold'][node]
                  else self.model['children_right'][node])
        return self.model['probabilities'][node]


def apply_policy(frames,feature_probability_pairs,policy,baseline=None):
    policy.validate()
    if any(f.dead_evidence and f.dead_source=='published_pre_kickoff' for f in frames):
        raise ValueError('published pre-kickoff D shortcut is excluded from the new tactical route')
    # Automatic challenge-only tags are not part of this external geometry benchmark.
    geometry=[replace(f,tag_team='',restart_hint=False) for f in frames]
    baseline=infer(geometry) if baseline is None else baseline
    if len(baseline)!=len(frames):
        raise ValueError('tactical baseline dimensions differ')
    raw=[]
    sentinel=object()
    for f,pair in zip_longest(geometry,feature_probability_pairs,fillvalue=sentinel):
        if f is sentinel or pair is sentinel:
            raise ValueError('tactical feature/probability frame counts differ')
        row,probabilities=pair
        if len(row)!=len(FEATURE_NAMES) or len(probabilities)!=3 or any(not isfinite(p) or p<0 for p in probabilities):
            raise ValueError('invalid external state predictions')
        winner=max(range(3),key=lambda k:probabilities[k])
        label='HAD'[winner] if probabilities[winner]>=policy.confidence and f.period else 'X'
        if label=='D' and (not f.ball_observed or not row[1] or not row[2]):
            label='X'
        elif label in ('H','A'):
            if f.ball_observed:
                if not row[1] or not row[2]:
                    label='X'
            elif not (row[15 if label=='H' else 16] and row[17]<=policy.max_gap_s+1e-9):
                label='X'
        raw.append(label)
    result=list(baseline)
    for low,high in _blocks(geometry):
        first=low
        while first<high:
            stop=first+1
            while stop<high and raw[stop]==raw[first]:
                stop+=1
            label=raw[first]
            if label!='X' and stop-first>=policy.minimum_run_frames:
                for i in range(first,stop):
                    if geometry[i].dead_evidence:
                        continue
                    if label=='D' or baseline[i].label=='X':
                        reason=('external_model_dead' if label=='D' else 'external_model_control'
                                if geometry[i].ball_observed else 'external_model_retained_owner')
                        result[i]=Decision(label,reason,'external_model')
            first=stop
        anchors=list(result)
        i=low
        while i<high:
            if anchors[i].label!='X':
                i+=1;continue
            first=i
            while i<high and anchors[i].label=='X':
                i+=1
            stop=i
            if first==low or stop==high or (stop-first)/25>policy.bridge_s:
                continue
            owner=anchors[first-1].label
            if owner not in ('H','A') or anchors[stop].label!=owner:
                continue
            if any(raw[j] not in ('X',owner) or geometry[j].dead_evidence
                   or _candidate(geometry[j],Config()) not in ('',owner) for j in range(first,stop)):
                continue
            plausible=True
            for a,b in zip(geometry[first-1:stop],geometry[first:stop+1]):
                if a.ball_observed and b.ball_observed and hypot(a.ball_x-b.ball_x,a.ball_y-b.ball_y)*25>35:
                    plausible=False;break
            if plausible:
                for j in range(first,stop):
                    result[j]=Decision(owner,'bounded_same_owner_interval','inferred_heuristic')
    return result


def infer_tactical(frames,model,policy=Policy()):
    tree=PortableTree(model)
    return apply_policy(frames,((row,tree.predict(row)) for row in feature_rows(frames)),policy)
''',
    'gap_solver.tactical_cli': r'''"""Local frozen-model tactical route; no video, challenge GT, fitting or camera synchronization."""
import argparse
from collections import Counter
import csv
from dataclasses import replace
import json
from math import isfinite
from pathlib import Path
import tempfile
import xml.etree.ElementTree as ET

from .audit import bridge_diagnostics,compare_decisions
from .automatic_sync import publish_outputs
from .core import Config,infer,summary,unresolved_intervals
from .frozen_protocol import artifact_digest
from .io import _bool,_number,load_atd,load_tags,read_evidence,write_outputs
from .multicam import resolve_source_prefix
from .tactical import FEATURE_NAMES,Policy,PortableTree,feature_rows,infer_tactical


OUTPUT_FILES={'submission.csv','diagnostics.csv','report.json','unresolved_intervals.json','tactical_report.json'}
METHOD='frozen_external_tactical_v1'


def protect_output(directory,inputs):
    directory=Path(directory)
    for name in OUTPUT_FILES:
        target=directory/name
        for source in map(Path,inputs):
            if target.resolve()==source.resolve() or target.exists() and source.exists() and target.samefile(source):
                raise ValueError('Tactical output must not replace an input or an alias of it')
    if directory.is_symlink():
        raise ValueError('Tactical output requires a dedicated directory, not a link')
    if directory.exists():
        if not directory.is_dir():
            raise ValueError('Tactical output must be a directory')
        if any(directory.iterdir()):
            try:
                report=json.loads((directory/'tactical_report.json').read_text(encoding='utf-8'))
                owned=report.get('method')==METHOD and all(p.name in OUTPUT_FILES and p.is_file() and not p.is_symlink()
                                                         for p in directory.iterdir())
            except (OSError,ValueError,AttributeError):
                owned=False
            if not owned:
                raise ValueError('Nonempty output is not owned by this tactical route; use a dedicated folder')


def apply_geometry_quality(frames,path,max_reprojection_error=3.):
    valid=[]
    with open(path,newline='',encoding='utf-8-sig') as handle:
        for i,row in enumerate(csv.DictReader(handle)):
            if int(row['frame'])!=i or i>=len(frames):
                raise ValueError('Tactical homography indices disagree with original tracking')
            matrix=[_number(row['h'+str(a)+str(b)]) for a in range(3) for b in range(3)]
            accepted=row['valid'].strip()=='1' and all(v is not None for v in matrix)
            if accepted:
                a,b,c,d,e,f,g,h,j=matrix
                determinant=a*(e*j-f*h)-b*(d*j-f*g)+c*(d*h-e*g)
                scale=max(abs(v) for v in matrix)
                accepted=scale>0 and abs(determinant)>1e-12*scale**3
            error=_number(row['reprojection_error'])
            valid.append(accepted and error is not None and 0<=error<=max_reprojection_error)
    if len(valid)!=len(frames):
        raise ValueError('Tactical homography row count differs from original tracking')
    return ([f if usable else replace(f,ball_x=None,ball_y=None,home_distance=None,away_distance=None)
             for f,usable in zip(frames,valid)],valid)


def load_model(path=None):
    if path:
        artifact=json.loads(Path(path).read_text(encoding='utf-8'))
        externally_validated=False
        identifier=artifact_digest(artifact)
    else:
        from .tactical_model import FROZEN_MODEL
        artifact=FROZEN_MODEL
        externally_validated=artifact.get('externally_heldout_validated') is True
        identifier=artifact['artifact_sha256']
        actual=artifact_digest(dict(model=artifact['model'],policy=artifact['policy']))
        if actual!=artifact.get('model_policy_sha256') or not externally_validated:
            raise ValueError('Embedded model is not the verified externally frozen policy')
    if artifact.get('schema_version')!=1:
        raise ValueError('Unsupported tactical model schema')
    PortableTree(artifact['model']);Policy(**artifact['policy']).validate()
    return artifact,identifier,externally_validated


def load_geometry_evidence(path):
    with open(path,newline='',encoding='utf-8-sig') as handle:
        for row in csv.DictReader(handle):
            if _bool(row.get('dead_evidence')) or str(row.get('dead_source') or '').strip():
                raise ValueError('Geometry-only tactical evidence cannot contain dead_evidence/dead_source labels')
    tagged=read_evidence(path)
    geometry=[replace(f,tag_team='',restart_hint=False) for f in tagged]
    return tagged,geometry


def unresolved_explanations(frames,decisions,quality,artifact):
    tree=PortableTree(artifact['model']);policy=Policy(**artifact['policy'])
    counts=Counter()
    for f,d,usable,row in zip(frames,decisions,quality,feature_rows(frames)):
        if not f.period or d.label!='X':
            continue
        probabilities=tree.predict(row)
        winner=max(range(3),key=lambda k:probabilities[k])
        if not usable:
            reason='homography_quality_rejected'
        elif not f.ball_observed and (not (row[15] or row[16]) or row[17]>policy.max_gap_s):
            reason='missing_ball_without_recent_confirmed_owner'
        elif not f.ball_observed and winner==2:
            reason='missing_ball_cannot_confirm_dead'
        elif f.ball_observed and (not row[1] or not row[2]):
            reason='incomplete_team_geometry'
        elif probabilities[winner]<policy.confidence:
            reason='model_leaf_support_below_gate'
        else:
            reason='insufficient_stable_run_or_conflicting_interval'
        counts[reason]+=1
    return dict(counts)


def run(frames,tagged,quality,artifact,identifier,externally_validated,directory,inputs,source_kind):
    destination=Path(directory)
    protect_output(destination,inputs)
    policy=Policy(**artifact['policy'])
    tagged_before=infer(tagged)
    quality_before=infer(frames)
    print('Running frozen tactical model on {} original frames...'.format(len(frames)),flush=True)
    decisions=infer_tactical(frames,artifact['model'],policy)
    before=summary(tagged,tagged_before);after=summary(frames,decisions)
    model_input=summary(frames,quality_before)
    report=dict(schema_version=1,method=METHOD,source_kind=source_kind,model_id=identifier,
                model_externally_validated=externally_validated,model_reference_type=artifact.get('reference_type','custom model; unverified'),
                model_policy=artifact['policy'],leaf_support_is_calibrated_probability=False,
                selected_features=list(FEATURE_NAMES),smart_tagging_used_for_selected_inference=False,
                before=before,baseline_on_model_inputs=model_input,after=after,
                unresolved_intervals_before=len(unresolved_intervals(tagged,tagged_before)),
                unresolved_intervals_after=len(unresolved_intervals(frames,decisions)),
                reference_free_changes=compare_decisions(frames,tagged_before,decisions),
                reference_free_changes_on_identical_inputs=compare_decisions(frames,quality_before,decisions),
                remaining_gap_diagnostics=bridge_diagnostics(frames,decisions),
                unresolved_reasons=unresolved_explanations(frames,decisions,quality,artifact),
                quality=dict(original_frames=len(frames),unusable_homography_frames=sum(not v for v in quality),
                             unusable_graded_homography_frames=sum(f.period!=0 and not q for f,q in zip(frames,quality)),
                             maximum_reprojection_error=3.),
                undecided_relative_reduction=1-after['labels']['X']/before['labels']['X'] if before['labels']['X'] else None,
                accuracy_measured=False,challenge_ground_truth_used=False,predictions_checked_against_video=False,
                challenge_training_or_tuning_performed=False,published_dead_interval_applied=False,
                live_dead_classifier_included=True,replay_detector_included=False,
                warning='Challenge coverage/behavior only. External provider-reference validation does not establish challenge correctness.')
    if externally_validated:
        report['external_heldout_summary']=artifact.get('heldout_summary')
        report['external_attribution']=artifact.get('citation')
        report['external_license']=artifact.get('license')
        report['external_validation_limitations']=artifact.get('validation_limitations',[])
    destination.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.tactical-result-',dir=destination.parent) as staging:
        stage=Path(staging)
        output=write_outputs(stage,frames,decisions,audit_stages={'legacy_tagged_no_fixed_D':tagged_before,
                                                               'geometry_on_model_inputs':quality_before})
        output.update(live_dead_classifier_included=True,external_model_id=identifier,method=METHOD)
        (stage/'report.json').write_text(json.dumps(output,indent=2)+'\n',encoding='utf-8')
        (stage/'tactical_report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
        protect_output(destination,inputs)
        publish_outputs(stage,destination)
    print('Undecided graded frames: {} -> {}'.format(before['labels']['X'],after['labels']['X']),flush=True)
    print('Resolved coverage: {:.2%} -> {:.2%}'.format(before['resolved_fraction'],after['resolved_fraction']),flush=True)
    print('No challenge accuracy measured. Output: '+str(destination.resolve()),flush=True)
    return report


def main():
    parser=argparse.ArgumentParser(description='Frozen externally validated tactical possession model; local inference only')
    sub=parser.add_subparsers(dest='command',required=True)
    for name in ('run','evidence'):
        command=sub.add_parser(name)
        command.add_argument('--model',help='optional custom JSON artifact; reported as unverified')
        command.add_argument('--out',default='outputs/tactical-validated')
        if name=='run':
            command.add_argument('--data-dir',required=True)
            command.add_argument('--tactical-dir')
        else:
            command.add_argument('--input',required=True,help='automatic evidence CSV for development; original indices required')
    args=parser.parse_args()
    try:
        artifact,identifier,validated=load_model(args.model)
        inputs=[args.model] if args.model else []
        if args.command=='evidence':
            inputs.append(args.input)
            protect_output(args.out,inputs)
            tagged,frames=load_geometry_evidence(args.input)
            quality=[True]*len(frames)
        else:
            prefix=str(resolve_source_prefix(args.data_dir,'tactical',args.tactical_dir))
            inputs.extend(prefix+suffix for suffix in ('_atd.xml','_atd.txt','_homography.csv'))
            protect_output(args.out,inputs)
            raw,teams=load_atd(prefix+'_atd.xml',prefix+'_atd.txt')
            tagging=Path(prefix+'_smart_tagging.xml')
            tagged=load_tags(tagging,raw,teams) if tagging.exists() else raw
            frames,quality=apply_geometry_quality(raw,prefix+'_homography.csv')
        run(frames,tagged,quality,artifact,identifier,validated,args.out,inputs,args.command)
    except (OSError,ValueError,TypeError,KeyError,ET.ParseError) as error:
        parser.error(str(error))


if __name__=='__main__':
    main()
''',
    'gap_solver.tactical_model': r'''"""Frozen external-reference model, CC BY 4.0 attribution below. No challenge fitting."""

FROZEN_MODEL = {'schema_version': 1,
 'model': {'feature_names': ['ball_observed',
                             'home_observed',
                             'away_observed',
                             'home_distance',
                             'away_distance',
                             'distance_margin',
                             'min_distance',
                             'ball_edge_x',
                             'ball_edge_y',
                             'ball_speed',
                             'recent_speed',
                             'slow_ball_age',
                             'missing_ball_age',
                             'last_home_distance',
                             'last_away_distance',
                             'last_control_home',
                             'last_control_away',
                             'last_control_age'],
           'children_left': [1,
                             2,
                             3,
                             4,
                             -1,
                             -1,
                             7,
                             -1,
                             -1,
                             10,
                             11,
                             -1,
                             -1,
                             14,
                             -1,
                             -1,
                             17,
                             18,
                             19,
                             -1,
                             -1,
                             22,
                             -1,
                             -1,
                             25,
                             26,
                             -1,
                             -1,
                             29,
                             -1,
                             -1],
           'children_right': [16,
                              9,
                              6,
                              5,
                              -1,
                              -1,
                              8,
                              -1,
                              -1,
                              13,
                              12,
                              -1,
                              -1,
                              15,
                              -1,
                              -1,
                              24,
                              21,
                              20,
                              -1,
                              -1,
                              23,
                              -1,
                              -1,
                              28,
                              27,
                              -1,
                              -1,
                              30,
                              -1,
                              -1],
           'feature': [10,
                       12,
                       11,
                       3,
                       -2,
                       -2,
                       8,
                       -2,
                       -2,
                       17,
                       15,
                       -2,
                       -2,
                       14,
                       -2,
                       -2,
                       16,
                       17,
                       5,
                       -2,
                       -2,
                       11,
                       -2,
                       -2,
                       17,
                       9,
                       -2,
                       -2,
                       11,
                       -2,
                       -2],
           'threshold': [0.010414917953312397,
                         0.4599999934434891,
                         0.019999999552965164,
                         9.96244478225708,
                         -2.0,
                         -2.0,
                         0.008235258050262928,
                         -2.0,
                         -2.0,
                         7.300000190734863,
                         0.5,
                         -2.0,
                         -2.0,
                         3.101701855659485,
                         -2.0,
                         -2.0,
                         0.5,
                         1.5399999618530273,
                         0.984589695930481,
                         -2.0,
                         -2.0,
                         0.019999999552965164,
                         -2.0,
                         -2.0,
                         0.13999999687075615,
                         0.12493133544921875,
                         -2.0,
                         -2.0,
                         0.019999999552965164,
                         -2.0,
                         -2.0],
           'probabilities': [[0.292157192811927, 0.25812246479475937, 0.44972034239331365],
                             [0.0700119547379043, 0.06323592714847735, 0.8667521181136183],
                             [0.0022668638203543422, 0.0016189785486808031, 0.9961141576309649],
                             [0.05064785971097865, 0.04255516555655918, 0.9067969747324622],
                             [0.31880454674588626, 0.24735689365902747, 0.4338385595950862],
                             [0.011139825548021919, 0.012381337859129406, 0.9764788365928487],
                             [0.0004905478850541524, 0.0001159999519417901, 0.999393452163004],
                             [0.0572415669302739, 0.0, 0.9427584330697262],
                             [0.0003176065412566451, 0.00011635344669668995, 0.9995660400120466],
                             [0.27828471053394227, 0.2526685711202919, 0.4690467183457659],
                             [0.38232391406890054, 0.34505756558844003, 0.27261852034265954],
                             [0.15464045620323127, 0.5568457465987089, 0.28851379719806],
                             [0.6045290947578811, 0.13836520651094852, 0.25710569873117034],
                             [0.11083244789788563, 0.10396745038204021, 0.7852001017200743],
                             [0.20639302266951692, 0.3267775691738245, 0.4668294081566584],
                             [0.09593777851059561, 0.06923887048937107, 0.8348233510000332],
                             [0.5242133975621257, 0.4617038274882389, 0.014082774949635276],
                             [0.8569764563839516, 0.12895961019954247, 0.014063933416506028],
                             [0.8971526505788151, 0.09257552957798766, 0.010271819843197201],
                             [0.8029503788373463, 0.180958698052865, 0.01609092310978874],
                             [0.9359791632440988, 0.056147424960664716, 0.007873411795236655],
                             [0.6668949130002579, 0.3010999121305309, 0.032005174869211235],
                             [0.6878752076069831, 0.3107362087495104, 0.0013885836435066046],
                             [0.10372794894098063, 0.042436055716250476, 0.853835995342769],
                             [0.14118940562763052, 0.8447061320417524, 0.014104462330617152],
                             [0.056358099098897024, 0.9348160711994866, 0.008825829701616265],
                             [0.019767384376998858, 0.6298450883778383, 0.3503875272451629],
                             [0.05730358982317394, 0.9426964101768259, 0.0],
                             [0.21640134157394914, 0.7648141293202958, 0.01878452910575511],
                             [0.22048453519342623, 0.778812896694831, 0.0007025681117428057],
                             [0.036198078560659736, 0.14700762927539812, 0.8167942921639422]]},
 'policy': {'confidence': 0.8, 'minimum_run_frames': 12, 'max_gap_s': 2.0, 'bridge_s': 2.0},
 'artifact_sha256': 'be756fce3c52d21fda0b10d8a6026f78f9b7d599298d467d2d6ebc59efe9fd38',
 'model_policy_sha256': '4070ade795443cfdd7d9912bd355ac881498d85e1f95c783665811a75178b2ab',
 'externally_heldout_validated': True,
 'reference_type': 'external provider reference, not competition gold',
 'training_matches': ['J03WOH', 'J03WOY', 'J03WPY', 'J03WMX'],
 'validation_matches': ['J03WQQ'],
 'test_matches': ['J03WR9', 'J03WN1'],
 'citation': 'Bassek, Rein, Weber et al., Scientific Data 12, 195 (2025), doi:10.1038/s41597-025-04505-y; '
             'DFL / Sportec Solutions.',
 'license': {'value': 52, 'name': 'CC BY', 'url': 'https://creativecommons.org/licenses/by/4.0/'},
 'leaf_support_is_calibrated_probability': False,
 'heldout_summary': {'natural': {'baseline': {'match_macro_spell_f1': 0.3736074924101682,
                                              'match_macro_macro_f1': 0.38871054654433934,
                                              'match_macro_undecided_fraction': 0.6047234429410505},
                                 'selected': {'match_macro_spell_f1': 0.5051315308124646,
                                              'match_macro_macro_f1': 0.8604085467573892,
                                              'match_macro_undecided_fraction': 0.09855754293580665},
                                 'newly_resolved_correct_fraction': 0.9632307586868618,
                                 'every_match_spell_f1_improved': True,
                                 'every_match_macro_f1_not_degraded': True,
                                 'every_match_x_reduced': True},
                     'ball_mask_0.1': {'baseline': {'match_macro_spell_f1': 0.34313162279853804,
                                                    'match_macro_macro_f1': 0.3658300324975863,
                                                    'match_macro_undecided_fraction': 0.645652955567203},
                                       'selected': {'match_macro_spell_f1': 0.46499576178691004,
                                                    'match_macro_macro_f1': 0.8137513033508208,
                                                    'match_macro_undecided_fraction': 0.18348726263259174},
                                       'newly_resolved_correct_fraction': 0.9648787005344382,
                                       'every_match_spell_f1_improved': True,
                                       'every_match_macro_f1_not_degraded': True,
                                       'every_match_x_reduced': True},
                     'ball_mask_0.3': {'baseline': {'match_macro_spell_f1': 0.30681346073950977,
                                                    'match_macro_macro_f1': 0.3089593664039759,
                                                    'match_macro_undecided_fraction': 0.7226981299566784},
                                       'selected': {'match_macro_spell_f1': 0.4027594627594627,
                                                    'match_macro_macro_f1': 0.7031455221496168,
                                                    'match_macro_undecided_fraction': 0.35856285772112056},
                                       'newly_resolved_correct_fraction': 0.9652127527838371,
                                       'every_match_spell_f1_improved': True,
                                       'every_match_macro_f1_not_degraded': True,
                                       'every_match_x_reduced': True},
                     'ball_mask_0.5': {'baseline': {'match_macro_spell_f1': 0.24820473644003052,
                                                    'match_macro_macro_f1': 0.24363756572789722,
                                                    'match_macro_undecided_fraction': 0.8013165514881082},
                                       'selected': {'match_macro_spell_f1': 0.33146616697321296,
                                                    'match_macro_macro_f1': 0.5621283321479538,
                                                    'match_macro_undecided_fraction': 0.5429039619454848},
                                       'newly_resolved_correct_fraction': 0.9665056360708535,
                                       'every_match_spell_f1_improved': True,
                                       'every_match_macro_f1_not_degraded': True,
                                       'every_match_x_reduced': True}},
 'validation_limitations': ['Experimental provider-reference agreement, not challenge accuracy or '
                            'cross-provider validation.',
                            'External inactive ball coordinates repeat the previous frame on 99.9993% of '
                            'contiguous inactive frames; motion features can exploit this provider '
                            'convention.',
                            'Newly resolved H/A agreement is 86.36%/88.95%; pooled 96.32% agreement is '
                            'dominated by D.',
                            'Active-only diagnostic spellF1 slightly regressed on both held-out matches; '
                            'conditional team accuracy and one home-share estimate also regressed.',
                            'Finite ball coordinates do not establish a fresh physical observation.']}
''',
    'gap_solver.temporal': r'''"""Portable player-motion evidence and offline team-state inference, without reference inputs."""
from dataclasses import dataclass,replace
from math import exp,hypot,isfinite,log,log1p
import struct

from .core import Decision,_blocks,infer


MOTION_FEATURES=('ball_available','home_count','away_count','home_cx','home_cy','away_cx','away_cy',
    'home_width','home_length','away_width','away_length','home_vx','home_vy','away_vx','away_vy',
    'home_speed','away_speed','home_continuity','away_continuity','home_distance','away_distance',
    'last_owner','next_owner','last_anchor_available','next_anchor_available','last_anchor_age','next_anchor_age',
    'gap_progress','gap_duration','last_ball_x','last_ball_y','next_ball_x','next_ball_y',
    'home_path_distance','away_path_distance','home_near_path','away_near_path','home_count_delta','away_count_delta')
_INDEX={name:i for i,name in enumerate(MOTION_FEATURES)}


def _clip(value,low=-1.,high=1.):return max(low,min(high,value))


def _quantile(values,q):
    values=sorted(values)
    if not values:return 0.
    at=q*(len(values)-1);low=int(at);high=min(len(values)-1,low+1)
    return values[low]+(values[high]-values[low])*(at-low)


def _points(frame,side):
    points=getattr(frame,side+'_xy',());ids=getattr(frame,side+'_ids',())
    if ids and len(ids)!=len(points):raise ValueError('motion identity/position dimensions disagree')
    ids=ids or tuple(range(len(points)))
    if len(set(ids))!=len(ids):raise ValueError('duplicate motion track identity')
    return {person:(float(x),float(y)) for person,(x,y) in zip(ids,points)
            if isfinite(x) and isfinite(y) and -10<=x<=115.3 and -10<=y<=78}


def anchor_context(frames):
    clean=[replace(f,tag_team='',restart_hint=False,dead_evidence=False,dead_source='') for f in frames]
    geometry=infer(clean);n=len(frames);left=[-1]*n;right=[-1]*n;owners=[0]*n
    for i,(f,d) in enumerate(zip(clean,geometry)):
        if (f.ball_observed and getattr(f,'geometry_valid',True) and d.label in ('H','A')
                and len(_points(f,'home'))>=3 and len(_points(f,'away'))>=3):owners[i]=-1 if d.label=='H' else 1
    for first,stop in _blocks(clean):
        last=-1
        for i in range(first,stop):
            if owners[i]:last=i
            left[i]=last
        following=-1
        for i in range(stop-1,first-1,-1):
            if owners[i]:following=i
            right[i]=following
    return left,right,owners


def motion_feature_rows(frames):
    left,right,owners=anchor_context(frames)
    previous=[{},{}];previous_period=0
    for i,f in enumerate(frames):
        if not f.period or f.period!=previous_period or not getattr(f,'geometry_valid',True):previous=[{},{}]
        previous_period=f.period
        teams=[_points(f,side) if getattr(f,'geometry_valid',True) else {} for side in ('home','away')]
        summaries=[]
        for points,prior in zip(teams,previous):
            xy=list(points.values());xs=[p[0] for p in xy];ys=[p[1] for p in xy]
            common=[person for person in points if person in prior]
            vx=[(points[p][0]-prior[p][0])*25 for p in common];vy=[(points[p][1]-prior[p][1])*25 for p in common]
            speeds=[hypot(a,b) for a,b in zip(vx,vy)]
            summaries.append(dict(count=min(len(xy),11)/11,cx=_clip((_quantile(xs,.5)-52.65)/52.65) if xy else 0.,
                cy=_clip((_quantile(ys,.5)-34)/34) if xy else 0.,
                width=(_quantile(ys,.9)-_quantile(ys,.1))/68 if xy else 0.,
                length=(_quantile(xs,.9)-_quantile(xs,.1))/105.3 if xy else 0.,
                vx=_clip(_quantile(vx,.5)/15),vy=_clip(_quantile(vy,.5)/15),
                speed=_clip(_quantile(speeds,.5)/20,0,1),
                continuity=len(common)/max(len(points),len(prior),1),
                count_delta=_clip((len(points)-len(prior))/11)))
        a,b=left[i],right[i];last=frames[a] if a>=0 else None;following=frames[b] if b>=0 else None
        progress=(i-a)/(b-a) if a>=0 and b>a else .5
        if f.ball_observed:path=(f.ball_x,f.ball_y)
        elif last is not None and following is not None:
            path=(last.ball_x+(following.ball_x-last.ball_x)*progress,last.ball_y+(following.ball_y-last.ball_y)*progress)
        else:path=None
        distances=[];near=[]
        for points in teams:
            values=[hypot(x-path[0],y-path[1]) for x,y in points.values()] if path is not None else []
            distances.append(min(min(values,default=30.),30.)/30)
            near.append(sum(d<=5 for d in values)/max(len(values),1))
        def ball_coord(anchor,axis):
            if anchor is None:return 0.
            return _clip(((anchor.ball_x if axis==0 else anchor.ball_y)-(52.65 if axis==0 else 34))/(52.65 if axis==0 else 34))
        h,away=summaries
        row=(float(f.ball_observed),h['count'],away['count'],h['cx'],h['cy'],away['cx'],away['cy'],
            h['width'],h['length'],away['width'],away['length'],h['vx'],h['vy'],away['vx'],away['vy'],
            h['speed'],away['speed'],h['continuity'],away['continuity'],
            min(f.home_distance,30.)/30 if f.home_distance is not None else 1.,
            min(f.away_distance,30.)/30 if f.away_distance is not None else 1.,
            float(owners[a]) if a>=0 else 0.,float(owners[b]) if b>=0 else 0.,float(a>=0),float(b>=0),
            min((i-a)/25,30.)/30 if a>=0 else 1.,min((b-i)/25,30.)/30 if b>=0 else 1.,progress,
            min(max(b-a-1,0)/25,120.)/120 if a>=0 and b>=0 else 1.,
            ball_coord(last,0),ball_coord(last,1),ball_coord(following,0),ball_coord(following,1),
            *distances,*near,h['count_delta'],away['count_delta'])
        if len(row)!=len(MOTION_FEATURES) or not all(isfinite(x) for x in row):raise ValueError('nonfinite motion feature')
        yield row
        previous=teams if f.period and getattr(f,'geometry_valid',True) else [{},{}]


def swap_feature_row(row):
    values=list(row)
    for name,index in _INDEX.items():
        if name.startswith('home_'):values[index]=row[_INDEX['away_'+name[5:]]]
        elif name.startswith('away_'):values[index]=row[_INDEX['home_'+name[5:]]]
    for name in ('last_owner','next_owner'):values[_INDEX[name]]=-row[_INDEX[name]]
    return tuple(values)


def reflect_feature_row(row):
    values=list(row)
    for name in ('home_cx','home_cy','away_cx','away_cy','home_vx','home_vy','away_vx','away_vy',
                 'last_ball_x','last_ball_y','next_ball_x','next_ball_y'):values[_INDEX[name]]=-row[_INDEX[name]]
    return tuple(values)


def mask_motion_frames(frames,mask):
    if len(frames)!=len(mask):raise ValueError('motion mask dimensions disagree')
    return [replace(f,ball_x=None,ball_y=None,home_distance=None,away_distance=None,
             ball_native_observation=False,ball_provenance='missing',ball_interpolated=False,ball_sample_time_s=None)
            if remove else f for f,remove in zip(frames,mask)]


class PortableBoosted:
    def __init__(self,model):
        if tuple(model.get('feature_names',()))!=MOTION_FEATURES:raise ValueError('portable motion feature schema differs')
        self.model=model
        if not isfinite(model.get('initial_log_odds',float('nan'))) or not 0<model.get('learning_rate',0)<=1:
            raise ValueError('invalid portable ensemble scale')
        trees=model.get('trees',[])
        if not trees or len(trees)>1000:raise ValueError('invalid portable ensemble dimensions')
        for tree in trees:
            n=len(tree.get('feature',[]))
            if not n or n>4095 or any(len(tree.get(k,[]))!=n for k in ('children_left','children_right','threshold','value')):
                raise ValueError('invalid regression tree dimensions')
            reached={0}
            for i in range(n):
                a,b=tree['children_left'][i],tree['children_right'][i]
                if not isfinite(tree['threshold'][i]) or not isfinite(tree['value'][i]):raise ValueError('invalid regression tree value')
                if a==b==-1:continue
                if type(a) is not int or type(b) is not int or not i<a<n or not i<b<n or a==b or not 0<=tree['feature'][i]<len(MOTION_FEATURES):
                    raise ValueError('invalid/cyclic regression tree')
                if i in reached:reached.update((a,b))
            if len(reached)!=n:raise ValueError('unreachable regression tree')

    def score(self,row):
        if len(row)!=len(MOTION_FEATURES) or not all(isfinite(v) for v in row):raise ValueError('invalid motion feature row')
        values=struct.unpack('<'+'f'*len(row),struct.pack('<'+'f'*len(row),*row))
        score=self.model['initial_log_odds'];rate=self.model['learning_rate']
        for tree in self.model['trees']:
            node=0
            while tree['children_left'][node]!=-1:
                node=tree['children_left'][node] if values[tree['feature'][node]]<=tree['threshold'][node] else tree['children_right'][node]
            score+=rate*tree['value'][node]
        return score

    def symmetric_score(self,row):return (self.score(row)-self.score(swap_feature_row(row)))/2


@dataclass(frozen=True)
class TemporalPolicy:
    confidence: float=.95
    max_gap_s: float=5.
    minimum_players: int=3
    switch_multiplier: float=1.

    def validate(self):
        if (not .5<self.confidence<=1 or not isfinite(self.max_gap_s) or self.max_gap_s<0
                or type(self.minimum_players) is not int or self.minimum_players<1
                or not isfinite(self.switch_multiplier) or self.switch_multiplier<=0):
            raise ValueError('invalid temporal policy')


def _logadd(a,b):
    maximum=max(a,b)
    return maximum+log(exp(a-maximum)+exp(b-maximum)) if isfinite(maximum) else maximum


def decode_team_sequence(scores,frames,baseline,switch_cost):
    n=len(frames)
    if len(scores)!=n or len(baseline)!=n or not isfinite(switch_cost) or switch_cost<0 or not all(isfinite(z) for z in scores):
        raise ValueError('invalid temporal decoder inputs')
    posterior=[0.]*n;i=0
    def usable(k):return frames[k].period and getattr(frames[k],'geometry_valid',True) and baseline[k].label!='D'
    while i<n:
        if not usable(i):i+=1;continue
        first=i;period=frames[i].period
        while i<n and usable(i) and frames[i].period==period:i+=1
        stop=i;emissions=[]
        for k in range(first,stop):
            label=baseline[k].label
            if label=='H':emissions.append((0.,-float('inf')))
            elif label=='A':emissions.append((-float('inf'),0.))
            else:
                z=_clip(scores[k],-50,50);emissions.append((-log1p(exp(z)),-log1p(exp(-z))))
        forward=[];a=b=0.
        for e0,e1 in emissions:
            x=e0+_logadd(a,b-switch_cost);y=e1+_logadd(b,a-switch_cost)
            normal=max(x,y);a,b=x-normal,y-normal;forward.append((a,b))
        a=b=0.
        for j in range(stop-first-1,-1,-1):
            f0,f1=forward[j];posterior[first+j]=_clip((f1+b)-(f0+a),-50,50)
            e0,e1=emissions[j]
            x=_logadd(e0+a,e1+b-switch_cost);y=_logadd(e1+b,e0+a-switch_cost)
            normal=max(x,y);a,b=x-normal,y-normal
    return posterior


def apply_temporal_policy(frames,baseline,posterior,policy,context=None):
    policy.validate();n=len(frames)
    if len(baseline)!=n or len(posterior)!=n:raise ValueError('temporal policy dimensions disagree')
    left,right,_=anchor_context(frames) if context is None else context
    barriers=[0]
    for f,d in zip(frames,baseline):barriers.append(barriers[-1]+int(not f.period or not getattr(f,'geometry_valid',True) or d.label=='D'))
    result=list(baseline)
    for i,(f,d,z) in enumerate(zip(frames,baseline,posterior)):
        if d.label!='X' or not f.period or not getattr(f,'geometry_valid',True):continue
        if len(_points(f,'home'))<policy.minimum_players or len(_points(f,'away'))<policy.minimum_players:continue
        a,b=left[i],right[i]
        if a<0 or b<0 or max(b-a-1,0)/25>policy.max_gap_s or barriers[b+1]!=barriers[a]:continue
        if not isfinite(z):raise ValueError('nonfinite temporal posterior')
        p=1/(1+exp(-_clip(z,-50,50)))
        if max(p,1-p)<policy.confidence:continue
        result[i]=Decision('A' if p>.5 else 'H','temporal_player_motion','external_temporal_experiment')
    return result


def infer_temporal(frames,artifact,baseline=None):
    if any(f.dead_evidence for f in frames):raise ValueError('geometry-only temporal inference cannot consume dead labels')
    if baseline is None:
        from .tactical import infer_tactical,Policy
        from .tactical_model import FROZEN_MODEL
        baseline=infer_tactical(frames,FROZEN_MODEL['model'],Policy(**FROZEN_MODEL['policy']))
    policy=TemporalPolicy(**artifact['policy']);policy.validate()
    temperature=float(artifact['temperature'])
    if not isfinite(temperature) or temperature<=0:raise ValueError('invalid temporal score scale')
    tree=PortableBoosted(artifact['model'])
    scores=[tree.symmetric_score(row) if d.label=='X' else 0. for row,d in zip(motion_feature_rows(frames),baseline)]
    posterior=decode_team_sequence(scores,frames,baseline,float(artifact['transition_cost'])*policy.switch_multiplier)
    return apply_temporal_policy(frames,baseline,[z/temperature for z in posterior],policy)
''',
    'gap_solver.temporal_acceptance': r'''"""Predeclared held-out acceptance, with paired matches as the resampling unit."""
import numpy as np
from .temporal_selection import validation_gate


def final_acceptance(reports,endpoints,masked_reports=None,masked_endpoints=None,
                     validation_passed=False,regression_passed=False):
    gate=validation_gate(reports,endpoints,masked_reports,masked_endpoints)
    checks=dict(gate['checks']);checks.pop('team_spell_no_match_decline')
    changes=np.asarray([r['selected']['metrics']['spell_f1_mean']-r['baseline']['metrics']['spell_f1_mean'] for r in reports])
    rng=np.random.RandomState(1729);draws=rng.choice(changes,size=(10000,len(changes))).mean(axis=1)
    lower=float(np.quantile(draws,.025))
    checks.update(validation_eligibility=bool(validation_passed),seen_data_regression=bool(regression_passed),
        team_spell_mean_nonnegative=bool(changes.mean()>=0),team_spell_match_tolerance=bool((changes>=-.02).all()),
        paired_bootstrap_lower_bound=lower>-.02)
    return dict(passes=all(checks.values()),checks=checks,paired_spell_changes=changes.tolist(),
        paired_match_bootstrap=dict(draws=10000,seed=1729,lower_95_percent_bound=lower,mean_change=float(changes.mean())),
        recovery_gate=gate,reference_scope='known in-play H/A only; no independent full-state validation')
''',
    'gap_solver.temporal_development': r'''"""External experiment helpers. Reference labels are absent from feature/inference APIs."""
import numpy as np
from .core import Decision
from .tactical import infer_tactical,Policy
from .tactical_model import FROZEN_MODEL
from .temporal import (MOTION_FEATURES,motion_feature_rows,mask_motion_frames,anchor_context,
    swap_feature_row,reflect_feature_row,apply_temporal_policy,TemporalPolicy)
from .temporal_selection import contiguous_mask


def codes(decisions):return np.fromiter(('HADX'.index(d.label) for d in decisions),dtype=np.uint8,count=len(decisions))
def decisions(values):return [Decision('HADX'[int(v)]) for v in values]


def feature_cases(frames,seed):
    result={}
    periods=np.asarray([f.period for f in frames])
    mask=contiguous_mask(periods,.3,seed)
    for name,case in (('natural',frames),('masked',mask_motion_frames(frames,mask))):
        result[name]=dict(x=np.asarray(list(motion_feature_rows(case)),dtype=np.float32),
            baseline=codes(infer_tactical(case,FROZEN_MODEL['model'],Policy(**FROZEN_MODEL['policy']))),
            mask=np.zeros(len(frames),dtype=bool) if name=='natural' else mask)
    return result


def training_sample(x,reference,baseline,offset=0,stride=5):
    x=np.asarray(x,dtype=np.float32);gt=np.asarray(reference);old=np.asarray(baseline)
    if x.shape!=(len(gt),len(MOTION_FEATURES)) or old.shape!=gt.shape:raise ValueError('external training dimensions disagree')
    rows=np.flatnonzero((gt<2)&(old==3)&((np.arange(len(gt))-offset)%stride==0))
    if not len(rows):raise ValueError('empty external training case')
    values=x[rows];target=gt[rows].astype(np.uint8)
    swapped=np.asarray([swap_feature_row(r) for r in values],dtype=np.float32)
    reflected=np.asarray([reflect_feature_row(r) for r in values],dtype=np.float32)
    both=np.asarray([reflect_feature_row(r) for r in swapped],dtype=np.float32)
    return np.concatenate((values,swapped,reflected,both)),np.concatenate((target,1-target,target,1-target)),np.full(4*len(rows),1/(4*len(rows)))


def ensemble_scores(model,x):
    """Vectorized portable-tree evaluation, using the exact runtime float32 input."""
    x=np.asarray(x,dtype=np.float32)
    if x.ndim!=2 or x.shape[1]!=len(MOTION_FEATURES) or not np.isfinite(x).all():raise ValueError('invalid ensemble input')
    result=np.full(len(x),model['initial_log_odds'],dtype=np.float64)
    for tree in model['trees']:
        nodes=np.zeros(len(x),dtype=np.int32)
        left=np.asarray(tree['children_left']);right=np.asarray(tree['children_right'])
        feature=np.asarray(tree['feature']);threshold=np.asarray(tree['threshold']);value=np.asarray(tree['value'])
        while True:
            active=np.flatnonzero(left[nodes]!=-1)
            if not len(active):break
            at=nodes[active]
            nodes[active]=np.where(x[active,feature[at]]<=threshold[at],left[at],right[at])
        result+=model['learning_rate']*value[nodes]
    return result


def symmetric_scores(model,x):
    swapped=np.asarray([swap_feature_row(row) for row in x],dtype=np.float32)
    return (ensemble_scores(model,x)-ensemble_scores(model,swapped))/2


def endpoint_predictions(frames,baseline,proposal,max_gap_s,mode='two_sided'):
    """Choose only from input evidence; match proposal's added-frame count without GT.

    Rank eligible frames by shorter anchor gap then nearest observed endpoint. The
    comparator may use different rows from the model; report reference coverage too.
    """
    n=len(frames);context=anchor_context(frames);left,right,owners=context
    eligible=apply_temporal_policy(frames,baseline,[-50.]*n,
        TemporalPolicy(confidence=.9,max_gap_s=max_gap_s),context)
    wanted=sum(b.label=='X' and p.label in ('H','A') for b,p in zip(baseline,proposal))
    candidates=[i for i,(a,b) in enumerate(zip(baseline,eligible)) if a.label=='X' and b.label!='X']
    candidates.sort(key=lambda i:(right[i]-left[i],min(i-left[i],right[i]-i),i))
    if len(candidates)<wanted:raise ValueError('comparator cannot match candidate input coverage')
    result=list(baseline)
    for i in candidates[:wanted]:
        a,b=left[i],right[i]
        owner=owners[a] if mode=='last_owner' or i-a<=b-i else owners[b]
        result[i]=Decision('H' if owner<0 else 'A','endpoint_comparator','external_comparison')
    return result,dict(matched_added_count=wanted,eligible_input_frames=len(candidates),
        matching='same total added input-frame count; reference labels never used for ranking')
''',
    'gap_solver.temporal_diagnostics': r'''"""Reference-free eligibility denominators, reported independently of model confidence."""
from collections import Counter
from .temporal import anchor_context,_points


def eligibility_diagnostics(frames,baseline,policy):
    policy.validate()
    if len(frames)!=len(baseline):raise ValueError('eligibility dimensions disagree')
    left,right,_=anchor_context(frames);barriers=[0]
    for f,d in zip(frames,baseline):barriers.append(barriers[-1]+int(not f.period or not f.geometry_valid or d.label=='D'))
    reasons=Counter();unknown=0
    for i,(f,d) in enumerate(zip(frames,baseline)):
        if d.label!='X':continue
        unknown+=1;a,b=left[i],right[i]
        if not f.period:reason='unknown_structural_period'
        elif not f.geometry_valid:reason='invalid_geometry'
        elif min(len(_points(f,'home')),len(_points(f,'away')))<policy.minimum_players:reason='insufficient_players'
        elif a<0 or b<0:reason='missing_two_sided_control_anchors'
        elif max(b-a-1,0)/25>policy.max_gap_s:reason='anchor_span_exceeds_cap'
        elif barriers[b+1]!=barriers[a]:reason='dead_or_invalid_geometry_barrier'
        else:reason='eligible_before_confidence'
        reasons[reason]+=1
    return dict(baseline_unknown_rows=unknown,reasons=dict(reasons),reference_used=False,policy=policy.__dict__)
''',
    'gap_solver.temporal_metrics': r'''"""Gap-aware external diagnostics; provider reference holes never become inference inputs."""
from collections import Counter
import numpy as np

from . import official_metrics as official
from .benchmark import evaluate_external,compare_external
from .core import infer


def _codes(values):
    array=np.asarray(values)
    if array.ndim!=1 or not np.isin(array,[0,1,2,3]).all():raise ValueError('invalid temporal label code')
    return array.astype(np.uint8)


def metric_periods(reference,periods):
    gt=np.asarray(reference);period=np.asarray(periods)
    if gt.ndim!=1 or period.ndim!=1 or len(gt)!=len(period) or not len(gt):
        raise ValueError('temporal reference/period dimensions disagree')
    if not np.isin(period,[0,1,2]).all() or not np.isin(gt,[0,1,2,3]).all():
        raise ValueError('invalid temporal reference/period code')
    if ((period==0)&(gt!=3)).any():raise ValueError('reference cannot label structurally unknown periods')
    active=np.flatnonzero(period)
    if not len(active):raise ValueError('no structurally supported period')
    # Preserve original unknown rows. Only supply a bookkeeping period to the
    # unchanged scorer; GT X still splits every unknown region into valid runs.
    result=period.copy();current=period[active[0]]
    for i,value in enumerate(period):
        if value:current=value
        else:result[i]=current
    return result.astype(np.uint8)


def score_temporal(reference,prediction,periods):
    gt=_codes(reference);pred=_codes(prediction)
    mapped=metric_periods(gt,periods)
    report=evaluate_external(gt,pred,mapped)
    report['scope']=dict(canonical_frames=len(gt),structural_period_frames=int((np.asarray(periods)>0).sum()),
        unknown_annotation_frames_within_period=int(((np.asarray(periods)>0)&(gt==3)).sum()),
        reference_contract='known in-play provider team reference; outside annotation remains unknown')
    confusion=np.asarray(report['metrics']['confusion'])
    values=[]
    for code in (0,1):
        tp=int(confusion[code,code]);denominator=int(confusion[code].sum()+confusion[:,code].sum())
        values.append(2*tp/denominator if denominator else 0.)
    report['known_team_macro_f1']=float(np.mean(values))
    runs=official.valid_runs(gt)
    filled=official.fill_abstentions(pred,runs)
    transitions=official.transitions(filled,runs)
    switches=sum(a<2 and b<2 for _,a,b in transitions)
    minutes=int((gt<2).sum())/25/60
    report['predicted_team_switches_per_known_live_minute']=switches/minutes if minutes else None
    return report


def missing_intervals(frames):
    result=[];i=0
    while i<len(frames):
        if not frames[i].period or frames[i].ball_observed:i+=1;continue
        first=i;period=frames[i].period
        while i<len(frames) and frames[i].period==period and not frames[i].ball_observed:i+=1
        result.append((first,i))
    return result


def duration_bucket(seconds):
    return next((name for upper,name in ((.2,'<=0.2s'),(.6,'0.2-0.6s'),(2,'0.6-2s'),(5,'2-5s'),(10,'5-10s'))
                 if seconds<=upper),'over10s')


def native_gap_statistics(data):
    available=np.asarray(data.native_ball_available,dtype=bool);periods=np.asarray(data.native_periods)
    if available.ndim!=1 or periods.shape!=available.shape:raise ValueError('native availability arrays disagree')
    missing=(~available)&(periods>0);intervals=0;buckets=Counter();i=0
    fps=float(data.notes['native_fps'])
    while i<len(missing):
        if not missing[i]:i+=1;continue
        first=i;period=periods[i]
        while i<len(missing) and missing[i] and periods[i]==period:i+=1
        intervals+=1;buckets[duration_bucket((i-first)/fps)]+=i-first
    return dict(native_fps=fps,native_rows=len(available),missing_native_frames=int(missing.sum()),
                missing_native_intervals=intervals,missing_native_seconds=float(missing.sum()/fps),
                missing_native_frames_by_duration=dict(buckets))


def hidden_opponent_scores(reference,before,after,frames):
    gt=np.asarray(reference,dtype=np.uint8);runs=official.valid_runs(gt)
    all_truth=official.possession_spells(gt,runs)
    anchors=infer(frames)
    predicted=[official.possession_spells(_codes(p),runs)
               for p in (before,after)]
    short=[];all_opponents=[];opposing_predictions=[{},{}];same_endpoint_gaps=0
    for first,stop in missing_intervals(frames):
        if first==0 or stop==len(frames) or frames[first-1].period!=frames[first].period or frames[stop].period!=frames[first].period:continue
        owner=anchors[first-1].label
        if owner not in ('H','A') or anchors[stop].label!=owner:continue
        code='HA'.index(owner)
        if gt[first-1]!=code or gt[stop]!=code:continue
        same_endpoint_gaps+=1
        for spell in all_truth:
            a,b,label=spell
            if label==1-code and first<=a<b<=stop:
                all_opponents.append(spell)
                if .2<=(b-a)/25<=2.:short.append(spell)
        for j,spells in enumerate(predicted):
            for index,spell in enumerate(spells):
                a,b,label=spell
                if label==1-code and a<stop and b>first:opposing_predictions[j][index]=spell
    short=list(dict.fromkeys(short));all_opponents=list(dict.fromkeys(all_opponents))
    result=dict(reference_short_spells=len(short),same_team_endpoint_gaps=same_endpoint_gaps,mechanism_uses_raw_spans=True,
                short_definition='0.2-2s, wholly inside missing-ball interval; both credible endpoints are opposite team; IoU>=0.5')
    for name,spells in zip(('baseline','selected'),opposing_predictions):
        candidates=list(spells.values())
        matches=official.match_spells(official.spell_overlaps(short,candidates),len(short),len(candidates),.5)
        _,false,_=official.match_spells(official.spell_overlaps(all_opponents,candidates),len(all_opponents),len(candidates),.5)
        result[name+'_hits']=matches[0]
        result[name+'_recall']=matches[0]/len(short) if short else None
        result[name+'_false_opposing_spells']=false
    return result


def gap_strata(frames,reference,before,after):
    gt=np.asarray(reference);old=np.asarray(before);new=np.asarray(after);buckets={}
    gap_agreement=[];labels={name:dict(frames=0,correct=0,gaps=0) for name in ('H','A')}
    for first,stop in missing_intervals(frames):
        bucket=duration_bucket((stop-first)/25)
        record=buckets.setdefault(bucket,dict(intervals=0,frames=0,known_reference_frames=0,
            newly_assigned_frames=0,newly_assigned_correct=0,native_ball_samples=0))
        record['intervals']+=1;record['frames']+=stop-first
        known=gt[first:stop]<3;assigned=known&(old[first:stop]==3)&(new[first:stop]<2)
        correct=assigned&(gt[first:stop]==new[first:stop])
        record['known_reference_frames']+=int(known.sum())
        record['newly_assigned_frames']+=int(assigned.sum());record['newly_assigned_correct']+=int(correct.sum())
        record['native_ball_samples']+=sum(getattr(f,'ball_native_observation',False) is True for f in frames[first:stop])
        for code,name in enumerate(('H','A')):
            selected=assigned&(new[first:stop]==code)
            labels[name]['frames']+=int(selected.sum());labels[name]['correct']+=int((selected&(gt[first:stop]==code)).sum())
            labels[name]['gaps']+=int(selected.any())
        if assigned.any():gap_agreement.append(float(correct.sum()/assigned.sum()))
    return dict(by_duration=buckets,newly_assigned_gap_macro_agreement=float(np.mean(gap_agreement)) if gap_agreement else None,
                newly_assigned_gaps=len(gap_agreement),per_label=labels)


def compare_temporal(reference,before,after,periods,frames):
    gt=_codes(reference);old=_codes(before);new=_codes(after)
    if len(frames)!=len(gt):raise ValueError('temporal frame/reference dimensions disagree')
    mapped=metric_periods(gt,periods)
    change=compare_external(gt,old,new,mapped)
    unmeasured=(np.asarray(periods)>0)&(gt==3)&(old==3)&(new<2)
    return dict(baseline=score_temporal(gt,old,periods),selected=score_temporal(gt,new,periods),change=change,
        hidden_opponents=hidden_opponent_scores(gt,old,new,frames),gap_strata=gap_strata(frames,gt,old,new),
        unmeasured_new_ha_outside_reference=int(unmeasured.sum()),
        warning='Known-reference team agreement only; assignments outside support have unmeasured correctness.')
''',
    'gap_solver.temporal_protocol': r'''"""Fail-closed freeze and eligibility contract; a rejected validation result stays rejected."""
import hashlib,json
from pathlib import Path


def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def evidence_identity(sources,inputs,artifact):
    return dict(artifact_sha256=artifact,source_sha256={name:hashlib.sha256(Path(p).read_bytes()).hexdigest() for name,p in sources.items()},
        input_sha256={name:hashlib.sha256(Path(p).read_bytes()).hexdigest() for name,p in inputs.items()})


def require_evidence(report,expected):
    if report.get('identity')!=expected:raise ValueError('Stale or mismatched evidence identity')


def load_temporal_frozen(directory,code_directory):
    directory=Path(directory);code_directory=Path(code_directory)
    artifact=json.loads((directory/'temporal-selected.json').read_text(encoding='utf-8'))
    manifest=json.loads((directory/'freeze-manifest.json').read_text(encoding='utf-8'))
    if manifest.get('frozen_before_final_test') is not True or digest(artifact)!=manifest.get('artifact_sha256'):
        raise ValueError('Temporal artifact freeze integrity failed')
    split=manifest.get('split',{})
    if set(split)!={'development','calibration','validation','test'} or any(not isinstance(v,list) or not v for v in split.values()):
        raise ValueError('Invalid temporal partition')
    ids=sum(split.values(),[])
    if len(ids)!=len(set(ids)):raise ValueError('Temporal match partitions overlap')
    sources=manifest.get('source_sha256',{})
    if not sources:raise ValueError('Temporal freeze lacks prediction/evaluation sources')
    for name,expected in sources.items():
        path=Path(name)
        if path.is_absolute() or '..' in path.parts or path.suffix!='.py':raise ValueError('Invalid temporal source path')
        if hashlib.sha256((code_directory/path).read_bytes()).hexdigest()!=expected:raise ValueError('Temporal source changed after freeze: '+name)
    if (artifact.get('eligibility')=='eligible')!=(artifact.get('validation_passed') is True):raise ValueError('Inconsistent temporal validation eligibility')
    if artifact.get('eligibility') not in ('eligible','rejected_before_final_test'):raise ValueError('Unknown temporal eligibility')
    return artifact,manifest


def local_eligible(artifact,final_report):
    return (artifact.get('eligibility')=='eligible' and artifact.get('validation_passed') is True
        and final_report.get('artifact_sha256')==digest(artifact) and final_report.get('acceptance',{}).get('passes') is True)
''',
    'gap_solver.temporal_selection': r'''"""External-only fitting helpers; sklearn is consumed by the developer, never runtime inference."""
from math import log
import numpy as np
from .temporal import MOTION_FEATURES


def export_boosted(classifier):
    if list(classifier.classes_)!=[0,1] or classifier.estimators_.shape[1]!=1:
        raise ValueError('portable model requires explicit binary H/A classes')
    prior=classifier.init_.class_prior_
    if len(prior)!=2 or min(prior)<=0:raise ValueError('unsupported ensemble initial estimator')
    trees=[]
    for estimator in classifier.estimators_[:,0]:
        tree=estimator.tree_
        trees.append(dict(children_left=tree.children_left.tolist(),children_right=tree.children_right.tolist(),
                          feature=tree.feature.tolist(),threshold=tree.threshold.tolist(),value=tree.value[:,0,0].tolist()))
    return dict(feature_names=list(MOTION_FEATURES),learning_rate=float(classifier.learning_rate),
                initial_log_odds=log(float(prior[1])/float(prior[0])),trees=trees)


def fit_temperature(scores,target,weights=None):
    z=np.asarray(scores,dtype=np.float64);y=np.asarray(target)
    if z.ndim!=1 or y.shape!=z.shape or not len(z) or not np.isfinite(z).all() or not np.isin(y,[0,1]).all():
        raise ValueError('invalid external calibration data')
    w=np.ones(len(z)) if weights is None else np.asarray(weights,dtype=np.float64)
    if w.shape!=z.shape or not np.isfinite(w).all() or (w<0).any() or w.sum()<=0:raise ValueError('invalid calibration weights')
    w=w/w.sum();low=0.;high=20.
    for _ in range(70):
        beta=(low+high)/2
        p=1/(1+np.exp(-np.clip(z*beta,-50,50)))
        gradient=float(np.dot(w,z*(p-y)))
        if gradient>0:high=beta
        else:low=beta
    return 1/max((low+high)/2,.001)


def contiguous_mask(periods,rate,seed):
    periods=np.asarray(periods)
    if periods.ndim!=1 or not np.isin(periods,[0,1,2]).all() or not 0<=rate<=1:raise ValueError('invalid contiguous mask protocol')
    rng=np.random.RandomState(seed);active=np.flatnonzero(periods>0);target=round(len(active)*rate)
    mask=np.zeros(len(periods),dtype=bool);remaining=target;attempts=0
    while remaining and attempts<max(100,len(active)*10):
        first=int(rng.choice(active));length=int(rng.choice([5,15,50,125,250]));stop=first
        while stop<len(periods) and periods[stop]==periods[first] and stop-first<length:stop+=1
        selected=np.flatnonzero(~mask[first:stop])+first
        selected=selected[:remaining];mask[selected]=True;remaining-=len(selected);attempts+=1
    if remaining:
        selected=rng.choice(np.flatnonzero((periods>0)&~mask),remaining,replace=False);mask[selected]=True
    return mask


def validation_gate(reports,endpoints,masked_reports=None,masked_endpoints=None):
    if len(reports)!=len(endpoints) or len(reports)<2:raise ValueError('validation gate requires paired independent matches')
    checks={}
    checks['source_quality']=all(r.get('source_quality_gate_passed') is True for r in reports)
    checks['coverage_gain']=float(np.mean([r['baseline']['coverage']['undecided_fraction']-r['selected']['coverage']['undecided_fraction'] for r in reports]))>=.05
    checks['team_spell_no_match_decline']=all(r['selected']['metrics']['spell_f1_mean']>=r['baseline']['metrics']['spell_f1_mean'] for r in reports)
    checks['mean_spell_advantage_over_endpoint']=float(np.mean([r['selected']['metrics']['spell_f1_mean']-e['selected']['metrics']['spell_f1_mean'] for r,e in zip(reports,endpoints)]))>0
    checks['natural_hidden_nonregression']=all(r['hidden_opponents']['reference_short_spells']==0 or
        r['hidden_opponents']['selected_hits']>=r['hidden_opponents']['baseline_hits'] for r in reports)
    label_details={}
    for name in ('H','A'):
        total=sum(r['change']['newly_resolved_by_label'][name]['frames'] for r in reports)
        correct=sum(r['change']['newly_resolved_by_label'][name]['frames']*(r['change']['newly_resolved_by_label'][name]['correct_fraction'] or 0.) for r in reports)
        missing_total=sum(r['gap_strata']['per_label'][name]['frames'] for r in reports)
        missing_correct=sum(r['gap_strata']['per_label'][name]['correct'] for r in reports)
        gaps=sum(r['gap_strata']['per_label'][name]['gaps'] for r in reports)
        checks[name+'_new_agreement']=total>=100 and correct/total>=.9
        checks[name+'_missing_gap_agreement']=missing_total>=100 and gaps>=10 and missing_correct/missing_total>=.9
        label_details[name]=dict(frames=total,correct_fraction=correct/total if total else None,
            missing_frames=missing_total,missing_correct_fraction=missing_correct/missing_total if missing_total else None,gaps=gaps)
    def hidden_support(values):return sum(r['hidden_opponents']['reference_short_spells'] for r in values)
    use=reports;against=endpoints;scope='natural'
    if hidden_support(reports)<20 and masked_reports is not None:
        use=masked_reports;against=masked_endpoints;scope='masked'
    support=hidden_support(use)
    hits=sum(r['hidden_opponents']['selected_hits'] for r in use)
    other_hits=sum(r['hidden_opponents']['selected_hits'] for r in against)
    false=sum(r['hidden_opponents']['selected_false_opposing_spells'] for r in use)
    other_false=sum(r['hidden_opponents']['selected_false_opposing_spells'] for r in against)
    checks['hidden_support']=support>=20 and sum(r['hidden_opponents']['reference_short_spells']>0 for r in use)>=2
    checks['positive_hidden_recovery']=hits>other_hits
    checks['hidden_nonregression_against_baseline']=all(r['hidden_opponents']['selected_hits']>=r['hidden_opponents']['baseline_hits'] for r in use)
    checks['bounded_false_opposing_spells']=false-other_false<=hits-other_hits
    return dict(passes=all(checks.values()),checks=checks,labels=label_details,
                hidden_scope=scope,hidden_reference_spells=support,hidden_hits=hits,endpoint_hits=other_hits,
                natural_hidden_claim_supported=scope=='natural' and checks['hidden_support'] and checks['positive_hidden_recovery'])
''',
}

GUIDE = 'Temporal external research update, 6 November 2026\n\nNew motion/reference adapters and a portable temporal model support independent\ndevelopment experiments. These research modules do not change the existing\ntactical command or install a new local prediction policy. See\nTEMPORAL_RECOVERY.md for eligibility, held-out results and limitations.\n\nFrozen tactical possession update, 5 November 2026\n\nThe experimental new route is tactical-only. Its small state model was fitted on\nfour licensed external matches, selected on a fifth, frozen and evaluated on two\nheld-out matches. Raw BallStatus/BallPossession labels never enter prediction\nfeatures. Standard-library inference and model data are embedded in this file.\n\npython football_pipeline.py tactical run --data-dir "C:\\football-data" --out outputs/tactical-validated\n\nThis route uses tracking geometry and the existing homography reliability gate.\nIt does not use video, challenge ground truth, Smart Tagging as model features,\nor the disputed fixed pre-kickoff D interval. Local reports measure coverage and\nbehavior; challenge accuracy remains unmeasured. Model leaf support is not a\ncalibrated correctness probability. Keep residual uncertainty instead of blindly\nfilling unknown frames. Reproducible external metrics and limitations are recorded\nin FOUR_GOALS.md. External inactive coordinates are usually frozen; motion features\ncan exploit this provider convention. External D agreement is not proof of robust\nstoppage recognition, and conditional H/A metrics slightly regress. This is a\ncandidate for further independent validation. The historical camera experiment below remains available but\nis paused; do not interpret clock discovery as verified possession evidence.\n\nAutomatic dense synchronization update, 5 November 2026\n\nRun camera auto-sync with both original video paths and both discovery reports.\nIt derives processing windows/crops automatically, uses the published tactical\nevaluation half windows as structural metadata and leaves overlapping half clocks\nambiguous. It writes a separate automatic output folder. It uses unchanged .7\nOCR confidence, stride 5 and .25-second combined timing limits. No fitting,\nparameter tuning, manual game labels or prediction/video checks are performed.\n\nExample:\npython football_pipeline.py camera auto-sync --tactical-video "data/tactical cam/BAR-ATH_tactical.mp4" --broadcast-video "data/broadcast cam/BAR-ATH_broadcast.mp4" --tactical-discovery outputs/tactical-discovery.json --broadcast-discovery outputs/broadcast-discovery.json --out outputs/automatic-sync\n\nThese are clock candidates, not replay-verified possession evidence.\nNo fusion is performed, live_verified/ready_for_fusion remain false, and\nunsupported timing is left blank. This stage does not apply the disputed\npre-kickoff D labels. Earlier guide content below records historical experiments.\n\n# Local two-camera clock and fusion experiment\n\n## Controlling update, 5 November 2026\n\nThe newer organiser clarification in RULES.md supersedes this historical experiment guide. Do not check predictions against provided video, manually create game data, upload provided data to AI services, or train/fit/calibrate/tune on the provided ground truth or video. All parameter tuning requires external data. Automatic checks and inference on provided inputs remain allowed.\n\nThe manual crop/clock-anchor and selected-clip instructions below record an earlier experiment, not an approved final-entry workflow. The executable still includes manual setup and the earlier organiser-answer D interval. Automatic clock-region discovery is now implemented as the first replacement stage; dense alignment and half assignment are still pending. Eligibility of the D exception needs clarification before final use. The controlled report includes a restart-only stage without that exception.\n\nThe new aggregate report is recorded in PROGRESS.md: restart-only resolved coverage was 30.808%, the earlier D context raised it to 32.251%, and fusion reached 32.259%. Fusion changed 13 raw labels and zero scorer-expanded labels. Of 284 compared missing-tactical-ball frames, none had an observed broadcast ball. No accuracy claim or match-based parameter adjustment follows from these counts.\n\n## Automatic clock discovery\n\nThe clarification does not require training. It requires external data if training or tuning is performed. The new command uses the installed pretrained Tesseract engine without training it:\n\n```powershell\npython football_pipeline.py camera discover-clock --video "C:\\football-data\\tactical cam\\BAR-ATH_tactical.mp4" --out "outputs/tactical-discovery.json"\npython football_pipeline.py camera discover-clock --video "C:\\football-data\\broadcast cam\\BAR-ATH_broadcast.mp4" --out "outputs/broadcast-discovery.json"\n```\n\nIt scans the whole recording every 30 seconds by default, without a selected ROI, half or playback-time anchor. Full images are streamed through memory into local OCR and discarded; only the JSON report remains and is overwritten on the next run. At least three spatially consistent progressing readings support a candidate segment. Competing clocks remain competing candidates. Freezes, resets, moved overlays and long unreadable gaps split support.\n\nThe report includes sampled original frame indices, clock text/scores/boxes, candidate segments and explicit `ready_for_fusion: false` / `live_verified: false` fields. Sparse observations do not form a dense clock map, determine halves or prove the pictures are live. A replay with a live clock may pass discovery. Do not pass this JSON to fusion. Keep per-frame/region details local; aggregate console counts describe execution only. Do not tune scan settings from challenge-video or match-coverage feedback.\n\nThis feature was tested on generated clocks/video only. It makes no real-match OCR, alignment, replay-rejection or accuracy claim.\n\n## Controlled restart comparison, 2 November 2026\n\nUse your existing tracking and cached alignment to isolate the Council\'s first proposed repair. No clock scan, video playback time or crop selection is needed:\n\n```powershell\npython football_pipeline.py camera fuse --data-dir "C:\\football-data" --alignment "outputs/alignment.csv" --audit-baseline --out "outputs/ensemble"\n```\n\nThis updates the existing outputs. Keep replacing the same single Python source file. A full-size tracking load may take time; progress is printed.\n\nThe corrected restart policy evaluates sustained observed proximity even inside an automatic set-piece phase. It resets control confirmation at phase edges, retains explicit dead-evidence precedence, and still blocks unsupported bridges across restart phases. Proximity is a heuristic, including during a stationary restart. The repair does not establish live play or correct possession by itself. Mapped restart/dead context constrains both cameras, so broadcast cannot simply escape the tactical phase restrictions.\n\nThe organiser-published tactical interval [110808,113742) is marked D, with reason `published_pre_kickoff` and evidence level `published_metadata`. This is exactly 2934 frames of the reference export, independently of general stoppage detection. The adapter refuses incompatible dimensions/half context. Missing ball and stationary proximity alone still do not establish D.\n\n`ensemble_report.json` now contains:\n- `controlled_comparison.stages`: legacy tactical, restart-repaired tactical, and repaired tactical plus published D context. The existing `after` field is the final fused stage.\n- `controlled_comparison.comparisons`: separate changes due to restart repair, published context and fusion, plus the total.\n- Each comparison includes raw label changes, scorer-expanded label changes, predicted possession-spell counts, changed reasons, missing-ball assignments and propagation into unchanged raw frames. These are behavior diagnostics, not spellF1 or measured accuracy. X filling follows the official half-local policy, including head backfill and all-X blocks remaining X.\n- `verification_reason_counts`: the detailed reasons behind camera verification outcomes; rejected geometry must not be counted as known replays.\n- `missing_ball_funnel`: matched frames with missing tactical ball, unresolved opportunities, visible broadcast ball, direct broadcast control, passing geometry, sufficient weight and rescues. Zero opportunities and zero successful recoveries are different outcomes.\n- `controlled_comparison.remaining_gap_diagnostics`: why the existing bridge rules still leave X runs.\n- `camera_comparison_frames`, skip reasons and alignment statuses distinguish attempted comparisons from frames with no eligible link. Alignment alone cannot identify whether every missing clock was unscanned or unreadable.\n\nThe existing diagnostics CSV gains the baseline-stage labels and their scorer-expanded forms when `--audit-baseline` is used. The existing fusion CSV gains timing uncertainty, geometry quality, ball visibility, phase/dead context and source/final labels. No extra prediction files are created for baseline variants.\n\nThe legacy restart behavior is reproduced for comparison, not used as the new baseline. Restoring tactical observations may turn previous broadcast rescues into baseline assignments; that is not evidence that broadcast became worse. This delivery deliberately preserves the existing clock/geometry fusion gates so their effects remain isolated. A dedicated replay detector, general live/dead detector and validated longer-gap possession model are later stages, not features claimed by this controlled repair.\n\nThe two display layouts both use MM:SS. Different fonts/backgrounds require different crops, not different time units. Screenshots from different moments do not establish a time offset. The program discovers candidate correspondence from the original video clocks; it does not use the screenshot values as anchors.\n\n## Run the new demo first\n\nFrom the extracted folder in Anaconda Prompt or PowerShell:\n\n```bash\npython -m gap_solver.multicam demo\n```\n\nExpected synthetic-only output:\n\n```text\nUnresolved tactical frames before/after: 40 / 20\nVerified broadcast rescues: 20\n```\n\nThe demonstration has two missing tactical intervals. Broadcast geometry supports one; an invalid broadcast homography blocks the other. This proves test behaviour, not real alignment or improved competition accuracy. This first ensemble runs the same possession rules independently on each camera, then combines the resulting evidence. No neural ensemble was trained.\n\n## What the pipeline does\n\n1. **Read the clock locally.** FFmpeg extracts small clock crops at original decoded frame indices; Tesseract reads the digits. Low-confidence/invalid OCR stays missing.\n2. **Build a bounded per-frame time map.** Consecutive readings bracket second ticks. At least three consistent ticks establish a run. Between ticks, the script estimates fractional match time and records timing uncertainty. It leaves unsupported frames blank and does not extrapolate.\n3. **Find corresponding moments.** Match half and fractional time, keeping separate tactical/broadcast frame numbers. Reject excessive uncertainty, duplicate clock candidates and unsupported stretches. Dense clocks with contradictory chronology fail validation.\n4. **Check the pictures indirectly through tracking.** Require valid, nondegenerate homographies, enough distinct same-team player matches and consistent ball positions when both balls are visible. Team point sets are used because tracking slots are not persistent player IDs.\n5. **Fuse reliable evidence.** Missing/inferred broadcast predictions have no vote. A verified direct broadcast prediction can fill a tactical X or outweigh a weak inferred label. Disagreement with direct tactical evidence is retained as a diagnostic conflict. D is never inferred from tracking absence.\n\n## What you need on your computer\n\nThe synthetic demo uses only Python 3.9+. Reading actual video additionally requires **FFmpeg (including ffprobe)** and **Tesseract OCR with English language data**, installed locally. These are external executables, not pip packages. Check:\n\n```bash\nffmpeg -version\nffprobe -version\ntesseract --version\n```\n\nYou can pass full executable paths using `--ffmpeg`, `--ffprobe` and `--tesseract`. The prototype requires the reference constant-25-fps export and a reported frame count; it refuses to resample/pad/trim an incompatible export. Metadata rate checks are a preliminary check, not a complete proof that a file has no irregular timestamps.\n\nTo fuse possession evidence, you also need the supplied ATD metadata, ATD tracking and homography for **both** sources. Footage alone is sufficient for clock extraction, but this version does not detect players/balls from video itself.\n\nThe fusion command accepts either `tactical/` and `broadcast/` or the existing Windows folders `tactical cam/` and `broadcast cam/` under `--data-dir`. It opens those files in place. You can also specify `--tactical-dir "PATH" --broadcast-dir "PATH"` directly; these override the parent-folder lookup. If multiple complete copies exist, it asks for explicit folders instead of guessing. All six required tracking and homography files are checked before loading. The command prints progress, total unresolved tactical frames before/after, broadcast rescues and fusion status counts. With a short clock pilot, only eligible mapped frames can change; the overall counts still cover the full tactical recording.\n\n```text\ndata/\n  tactical/BAR-ATH_tactical.mp4\n  tactical/BAR-ATH_tactical_atd.xml\n  tactical/BAR-ATH_tactical_atd.txt\n  tactical/BAR-ATH_tactical_homography.csv\n  tactical/BAR-ATH_tactical_smart_tagging.xml  (optional)\n  broadcast/BAR-ATH_broadcast.mp4\n  broadcast/BAR-ATH_broadcast_atd.xml\n  broadcast/BAR-ATH_broadcast_atd.txt\n  broadcast/BAR-ATH_broadcast_homography.csv\n```\n\n## Historical pilot: a short first-half interval\n\nStart with roughly 30 seconds showing a progressing clock in each feed. Choose overlapping **match** time; the files\' elapsed playback times will differ. Use original frame indices: at 25 fps, frame = elapsed playback seconds * 25. The newer prohibition on manually created game data means this earlier manual setup must not be assumed eligible for a final entry. Never hand-correct possession labels or training/validation labels on this match.\n\nThe published tactical first-half kickoff is frame 11185, so a first tactical pilot can use:\n\n```bash\npython -m gap_solver.multicam clock --video "D:/mtah-data/tactical/BAR-ATH_tactical.mp4" --source tactical --half 1 --start-frame 11185 --end-frame 11935 --stride 5 --preview outputs/tactical-clock-preview.png --out outputs/tactical-clock.csv\n```\n\nFor broadcast, replace START and END below with the original frame range containing the same match-clock interval. These are placeholders, not literal arguments:\n\n```bash\npython -m gap_solver.multicam clock --video "D:/mtah-data/broadcast/BAR-ATH_broadcast.mp4" --source broadcast --half 1 --start-frame START --end-frame END --stride 5 --preview outputs/broadcast-clock-preview.png --out outputs/broadcast-clock.csv\n```\n\nInspect the saved clock previews **locally**. Crop presets are provisional normalised coordinates based on the supplied display layouts, not guaranteed original-video coordinates. If the crop misses digits or includes the score, override with `--roi x,y,width,height`, where values are fractions from 0 to 1. For example `--roi 0.1,0.02,0.06,0.05`. ROI describes the clock box only; it does not label the match. Temporary crops are deleted after OCR; previews remain at the chosen local path.\n\n**Historical selector capability:** add `--select-roi` to the clock command. A local window opens on the first selected frame. Drag around the complete time digits, leaving a small margin and excluding the score. Inspect the enlarged preview, redraw if necessary, and click **Use clock box**. OCR then continues automatically using your selection. The window uses Python\'s tkinter; if it is unavailable, the command explains how to install `tk` in your conda environment. Selection geometry and frame extraction are automatically tested; the graphical window still needs verification on your Windows desktop.\n\nThe clock box is saved beside the clock CSV, for example `outputs/tactical-clock.csv.roi.json`. Future runs can replace `--select-roi` with `--roi-file "outputs/tactical-clock.csv.roi.json"`. These options are mutually exclusive with `--roi`. These manual options remain software capabilities, not an exemption from the newer rule. Do not upload provided frames or crops to AI services.\n\n**OCR update:** tactical crops are converted to dark digits on a light background and given a small white border. Broadcast crops retain their dark-on-light polarity and receive the same border. TSV output is requested with the explicit `tessedit_create_tsv=1` parameter; an optional `configs/tsv` file is no longer required. Unexpected non-TSV output raises a format error instead of silently becoming zero clock readings. Polarity processing can help or hurt depending on the installed model. Default confidence cutoff is 0.7; for the user-authorised initial trial, add `--min-confidence 0.5` to the clock command. This changes OCR eligibility only; it is not a claim of better timing or possession accuracy. All existing progressing-tick, half, duplicate-match and geometry checks remain.\n\nThe trial prints the first percentile (linear interpolation), median and minimum confidence across ALL sampled crops in the requested clip, counting unreadable/invalid clocks as zero. It also prints parsed, unreadable and accepted counts. `First-percentile confidence > 0.5` means the first percentile, not the minimum or a calibrated probability of correctness. Expected clock-absent intervals will lower these all-crop statistics; the first trial intentionally uses a visible mid-game interval. Do not optimise from this challenge clip; subsequent tuning requires external data.\n\n**Retry update:** only a crop that is unreadable or below the chosen cutoff is retried. Two local treatments restore the original enlarged crop (undoing the tactical inversion and added border) and threshold the processed crop to black and white. If eligible treatments disagree on the clock, the sample stays unresolved. Otherwise the highest measured eligible score is retained; scores are never increased by agreement. Retry counts, recoveries at the cutoff and conflicts are printed. These are selected OCR scores after retries, not independent accuracy measurements. The reads CSV records the chosen treatment and number of attempts.\n\nThe timeline can now skip a weak or unreadable sample when the accepted observations on either side are at most 0.5 seconds apart and the clock remains consistent. At the pilot\'s stride 5 and 25 fps, this tolerates one missed sample; two consecutive misses split the run. Tick uncertainty increases across the gap. At least three consistent second ticks are still required, with no extrapolation. A bounded time estimate can therefore exist at a frame whose own OCR remained unreadable; this does not change its all-crop OCR score from zero. Stricter combined timing uncertainty can still reject a two-camera correspondence.\n\nTo test one existing raw crop without rescanning a video:\n\n```bash\npython -m gap_solver.multicam ocr-check --image "outputs/tactical-clock-preview.png" --source tactical\n```\n\nThis prints OCR text and Tesseract\'s confidence score before and after preprocessing. Scores are not measured accuracy. Previews saved by the updated clock command already show the preprocessed OCR input; applying `ocr-check` to one of those compares that input against an additional polarity transformation, so the Original score is the relevant current-input score. No image leaves your machine.\n\nThe user-specified half must match the entire selected interval. Do not run a half-1 command across halftime or the second half. MM:SS alone cannot distinguish first-half stoppage time from overlapping second-half minutes. This version is a selected-clip pilot; joining separate half pilots into one full-match clock map is not automated. A later merge must preserve original indices and use distinct segment IDs.\n\nThen build candidate alignment and fuse:\n\n```bash\npython -m gap_solver.multicam align --tactical-clock outputs/tactical-clock.csv --broadcast-clock outputs/broadcast-clock.csv --out outputs/alignment.csv\npython -m gap_solver.multicam fuse --data-dir "D:/mtah-data" --alignment outputs/alignment.csv --out outputs/ensemble\n```\n\nThe dense clock CSV has one row per original video frame, including blank estimates outside the pilot. Fusion retains the original tactical-only result wherever no eligible broadcast correspondence exists. The resulting submission-shaped CSV remains experimental; an automatic live/dead classifier is still absent.\n\nAutomatic diagnostics can report missing readings, timing uncertainty and absent overlap. Do not check predictions against challenge video or hand-adjust its crop/timing setup. Choose processing parameters and OCR stride using external evaluation, not this game\'s assignment coverage. Clock scans decode from the start of the file to preserve decoded indices; later intervals can therefore cost more than their clip duration suggests.\n\n## Files to inspect\n\n| File | Meaning |\n|---|---|\n| `tactical-clock.csv` / `broadcast-clock.csv` | Original frame, half, estimated match seconds, timing uncertainty, segment ID |\n| `*.reads.csv` | Selected OCR reading, measured score, chosen treatment and attempt count; generated automatically |\n| `alignment.csv` | Tactical frame, candidate broadcast frame, uncertainty and candidate/rejection status |\n| `fusion_diagnostics.csv` | Camera weights, fusion decision and geometry result per tactical frame |\n| `ensemble_report.json` | Tactical-only vs fused label coverage; rescues, replacements and conflicts |\n| `submission.csv` | Experimental predictions on the tactical timeline |\n\nFor example, a frame can have estimated match time 1622.32 seconds while its counterpart has a completely different file frame index. Timing uncertainty is reported separately; this is not a claim of exact frame synchronisation.\n\n## Weights and safeguards\n\nProvisional values in code:\n\n- Direct tactical control: weight 1.0. Inferred tactical continuity: 0.35.\n- Eligible broadcast control: `0.9 * geometry_quality * (1 - 0.5 * uncertainty / 0.25)`.\n- Geometry quality combines player-position agreement with reprojection error.\n- Broadcast needs weight >= 0.3 to rescue X; replacing a conflicting inferred tactical label additionally requires a normalised vote advantage >= 0.2.\n- Maximum combined clock uncertainty: 0.25 seconds. Coarse one-second OCR is often insufficient. The geometry limits default to 3 m median player residual, at least three distinct matches per team and 60% of unique broadcast points, 4 m ball residual when visible in both views, and reprojection error <= 3.\n\nThese values are engineering defaults, not calibrated probabilities or values tuned on the public five minutes. The exact numbers will need independent evaluation on compatible other-match data. The fusion default preserves direct tactical disagreements; it is intentionally more restrictive than blindly averaging two labels.\n\n## Limitations to assess on local data\n\n- A replay can carry a live clock and plausible player positions. The checks reduce false matches but do **not** constitute a complete replay detector.\n- Camera overlays can have systematic delay or rounding differences; tick matching alone does not prove the same physical moment.\n- Both ATD exports must use compatible pitch orientation and coordinates. If they disagree, geometry rejects the match; automatic orientation calibration is not implemented.\n- A narrow broadcast shot may have too few players to verify. Invalid homography does not mean dead ball.\n- Player point sets can agree accidentally; no persistent player identity is assumed. Distinct spatial matching prevents duplicate tracks from counting as independent support.\n- Added-time parser accepts `45+02:13` and `90+01:02`, but actual live OCR/crop behaviour for added-time overlays is untested. Clocks freezing at 45:00/90:00 without a readable added-time timer leave unsupported intervals.\n- No actual competition footage/tracking was processed here. The displayed screenshots were only used to identify clock format and approximate layout. They are not bundled or used as labels or timing anchors.\n\nKeep all footage, crops, tracking and derived alignment outputs local. Do not upload restricted competition assets or extracts to hosted/cloud LLMs, publish them, or use public labels for model selection. No network calls exist in these modules.\n\nOfficial tool references: https://tesseract-ocr.github.io/tessdoc/Command-Line-Usage.html and https://ffmpeg.org/ffmpeg-filters.html . Competition formats follow the uploaded starter snapshot.\n'

class _BundledModules(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    def find_spec(self, fullname, path=None, target=None):
        if fullname in SOURCES:
            return importlib.util.spec_from_loader(fullname, self,
                                                   is_package=(fullname == "gap_solver"))
        return None

    def create_module(self, spec):
        return None

    def exec_module(self, module):
        filename = __file__ + "::" + module.__name__
        module.__file__ = filename
        exec(compile(SOURCES[module.__name__], filename, "exec"), module.__dict__)


def main():
    if sys.version_info < (3, 9):
        raise SystemExit("Use Python 3.9 or newer.")
    if len(sys.argv) > 1 and sys.argv[1] == "--guide":
        print(GUIDE)
        return
    if len(sys.argv) > 1 and sys.argv[1] == "--version":
        print(VERSION)
        return
    sys.meta_path.insert(0, _BundledModules())
    module = "gap_solver.__main__"
    if len(sys.argv) > 1 and sys.argv[1] == "camera":
        sys.argv.pop(1)
        module = "gap_solver.multicam"
    if len(sys.argv) > 1 and sys.argv[1] == "tactical":
        sys.argv.pop(1)
        module = "gap_solver.tactical_cli"
    importlib.import_module(module).main()


if __name__ == "__main__":
    main()
