"""Optional FFmpeg + Tesseract OCR, entirely local. No model/API uploads."""
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
