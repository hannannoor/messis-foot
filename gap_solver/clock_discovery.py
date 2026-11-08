"""Automatic local clock-region discovery; not dense alignment or replay verification."""
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
