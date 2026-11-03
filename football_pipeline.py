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

VERSION = '2026.11.02-restart-audit'

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
    inferred = sum(d.evidence_level in ('inferred_heuristic', 'fused_heuristic') for _, d in active)
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
}

GUIDE = '# Local two-camera clock and fusion experiment\n\n## Controlled restart comparison, 2 November 2026\n\nUse your existing tracking and cached alignment to isolate the Council\'s first proposed repair. No clock scan, video playback time or crop selection is needed:\n\n```powershell\npython football_pipeline.py camera fuse --data-dir "C:\\football-data" --alignment "outputs/alignment.csv" --audit-baseline --out "outputs/ensemble"\n```\n\nThis updates the existing outputs. Keep replacing the same single Python source file. A full-size tracking load may take time; progress is printed.\n\nThe corrected restart policy evaluates sustained observed proximity even inside an automatic set-piece phase. It resets control confirmation at phase edges, retains explicit dead-evidence precedence, and still blocks unsupported bridges across restart phases. Proximity is a heuristic, including during a stationary restart. The repair does not establish live play or correct possession by itself. Mapped restart/dead context constrains both cameras, so broadcast cannot simply escape the tactical phase restrictions.\n\nThe organiser-published tactical interval [110808,113742) is marked D, with reason `published_pre_kickoff` and evidence level `published_metadata`. This is exactly 2934 frames of the reference export, independently of general stoppage detection. The adapter refuses incompatible dimensions/half context. Missing ball and stationary proximity alone still do not establish D.\n\n`ensemble_report.json` now contains:\n- `controlled_comparison.stages`: legacy tactical, restart-repaired tactical, and repaired tactical plus published D context. The existing `after` field is the final fused stage.\n- `controlled_comparison.comparisons`: separate changes due to restart repair, published context and fusion, plus the total.\n- Each comparison includes raw label changes, scorer-expanded label changes, predicted possession-spell counts, changed reasons, missing-ball assignments and propagation into unchanged raw frames. These are behavior diagnostics, not spellF1 or measured accuracy. X filling follows the official half-local policy, including head backfill and all-X blocks remaining X.\n- `verification_reason_counts`: the detailed reasons behind camera verification outcomes; rejected geometry must not be counted as known replays.\n- `missing_ball_funnel`: matched frames with missing tactical ball, unresolved opportunities, visible broadcast ball, direct broadcast control, passing geometry, sufficient weight and rescues. Zero opportunities and zero successful recoveries are different outcomes.\n- `controlled_comparison.remaining_gap_diagnostics`: why the existing bridge rules still leave X runs.\n- `camera_comparison_frames`, skip reasons and alignment statuses distinguish attempted comparisons from frames with no eligible link. Alignment alone cannot identify whether every missing clock was unscanned or unreadable.\n\nThe existing diagnostics CSV gains the baseline-stage labels and their scorer-expanded forms when `--audit-baseline` is used. The existing fusion CSV gains timing uncertainty, geometry quality, ball visibility, phase/dead context and source/final labels. No extra prediction files are created for baseline variants.\n\nThe legacy restart behavior is reproduced for comparison, not used as the new baseline. Restoring tactical observations may turn previous broadcast rescues into baseline assignments; that is not evidence that broadcast became worse. This delivery deliberately preserves the existing clock/geometry fusion gates so their effects remain isolated. A dedicated replay detector, general live/dead detector and validated longer-gap possession model are later stages, not features claimed by this controlled repair.\n\nThe two display layouts both use MM:SS. Different fonts/backgrounds require different crops, not different time units. Screenshots from different moments do not establish a time offset. The program discovers candidate correspondence from the original video clocks; it does not use the screenshot values as anchors.\n\n## Run the new demo first\n\nFrom the extracted folder in Anaconda Prompt or PowerShell:\n\n```bash\npython football_pipeline.py camera demo\n```\n\nExpected synthetic-only output:\n\n```text\nUnresolved tactical frames before/after: 40 / 20\nVerified broadcast rescues: 20\n```\n\nThe demonstration has two missing tactical intervals. Broadcast geometry supports one; an invalid broadcast homography blocks the other. This proves test behaviour, not real alignment or improved competition accuracy. This first ensemble runs the same possession rules independently on each camera, then combines the resulting evidence. No neural ensemble was trained.\n\n## What the pipeline does\n\n1. **Read the clock locally.** FFmpeg extracts small clock crops at original decoded frame indices; Tesseract reads the digits. Low-confidence/invalid OCR stays missing.\n2. **Build a bounded per-frame time map.** Consecutive readings bracket second ticks. At least three consistent ticks establish a run. Between ticks, the script estimates fractional match time and records timing uncertainty. It leaves unsupported frames blank and does not extrapolate.\n3. **Find corresponding moments.** Match half and fractional time, keeping separate tactical/broadcast frame numbers. Reject excessive uncertainty, duplicate clock candidates and unsupported stretches. Dense clocks with contradictory chronology fail validation.\n4. **Check the pictures indirectly through tracking.** Require valid, nondegenerate homographies, enough distinct same-team player matches and consistent ball positions when both balls are visible. Team point sets are used because tracking slots are not persistent player IDs.\n5. **Fuse reliable evidence.** Missing/inferred broadcast predictions have no vote. A verified direct broadcast prediction can fill a tactical X or outweigh a weak inferred label. Disagreement with direct tactical evidence is retained as a diagnostic conflict. D is never inferred from tracking absence.\n\n## What you need on your computer\n\nThe synthetic demo uses only Python 3.9+. Reading actual video additionally requires **FFmpeg (including ffprobe)** and **Tesseract OCR with English language data**, installed locally. These are external executables, not pip packages. Check:\n\n```bash\nffmpeg -version\nffprobe -version\ntesseract --version\n```\n\nYou can pass full executable paths using `--ffmpeg`, `--ffprobe` and `--tesseract`. The prototype requires the reference constant-25-fps export and a reported frame count; it refuses to resample/pad/trim an incompatible export. Metadata rate checks are a preliminary check, not a complete proof that a file has no irregular timestamps.\n\nTo fuse possession evidence, you also need the supplied ATD metadata, ATD tracking and homography for **both** sources. Footage alone is sufficient for clock extraction, but this version does not detect players/balls from video itself.\n\nThe fusion command accepts either `tactical/` and `broadcast/` or the existing Windows folders `tactical cam/` and `broadcast cam/` under `--data-dir`. It opens those files in place. You can also specify `--tactical-dir "PATH" --broadcast-dir "PATH"` directly; these override the parent-folder lookup. If multiple complete copies exist, it asks for explicit folders instead of guessing. All six required tracking and homography files are checked before loading. The command prints progress, total unresolved tactical frames before/after, broadcast rescues and fusion status counts. With a short clock pilot, only eligible mapped frames can change; the overall counts still cover the full tactical recording.\n\n```text\ndata/\n  tactical/BAR-ATH_tactical.mp4\n  tactical/BAR-ATH_tactical_atd.xml\n  tactical/BAR-ATH_tactical_atd.txt\n  tactical/BAR-ATH_tactical_homography.csv\n  tactical/BAR-ATH_tactical_smart_tagging.xml  (optional)\n  broadcast/BAR-ATH_broadcast.mp4\n  broadcast/BAR-ATH_broadcast_atd.xml\n  broadcast/BAR-ATH_broadcast_atd.txt\n  broadcast/BAR-ATH_broadcast_homography.csv\n```\n\n## First real-video pilot: a short first-half interval\n\nStart with roughly 30 seconds showing a progressing clock in each feed. Choose overlapping **match** time; the files\' elapsed playback times will differ. Use original frame indices: at 25 fps, frame = elapsed playback seconds * 25. Choosing a crop, half and processing range is setup metadata, not possession annotation. Never hand-correct possession labels or training/validation labels on this match.\n\nThe published tactical first-half kickoff is frame 11185, so a first tactical pilot can use:\n\n```bash\npython football_pipeline.py camera clock --video "D:/mtah-data/tactical/BAR-ATH_tactical.mp4" --source tactical --half 1 --start-frame 11185 --end-frame 11935 --stride 5 --preview outputs/tactical-clock-preview.png --out outputs/tactical-clock.csv\n```\n\nFor broadcast, replace START and END below with the original frame range containing the same match-clock interval. These are placeholders, not literal arguments:\n\n```bash\npython football_pipeline.py camera clock --video "D:/mtah-data/broadcast/BAR-ATH_broadcast.mp4" --source broadcast --half 1 --start-frame START --end-frame END --stride 5 --preview outputs/broadcast-clock-preview.png --out outputs/broadcast-clock.csv\n```\n\nInspect the saved clock previews **locally**. Crop presets are provisional normalised coordinates based on the supplied display layouts, not guaranteed original-video coordinates. If the crop misses digits or includes the score, override with `--roi x,y,width,height`, where values are fractions from 0 to 1. For example `--roi 0.1,0.02,0.06,0.05`. ROI describes the clock box only; it does not label the match. Temporary crops are deleted after OCR; previews remain at the chosen local path.\n\n**Preferred when a preset crop is wrong:** add `--select-roi` to the clock command. A local window opens on the first selected frame. Drag around the complete time digits, leaving a small margin and excluding the score. Inspect the enlarged preview, redraw if necessary, and click **Use clock box**. OCR then continues automatically using your selection. The window uses Python\'s tkinter; if it is unavailable, the command explains how to install `tk` in your conda environment. Selection geometry and frame extraction are automatically tested; the graphical window still needs verification on your Windows desktop.\n\nThe clock box is saved beside the clock CSV, for example `outputs/tactical-clock.csv.roi.json`. Future runs can replace `--select-roi` with `--roi-file "outputs/tactical-clock.csv.roi.json"`. These options are mutually exclusive with `--roi`. A clock crop is camera setup, not a possession label. No frames or crops need to be uploaded.\n\n**OCR update:** tactical crops are converted to dark digits on a light background and given a small white border. Broadcast crops retain their dark-on-light polarity and receive the same border. TSV output is requested with the explicit `tessedit_create_tsv=1` parameter; an optional `configs/tsv` file is no longer required. Unexpected non-TSV output raises a format error instead of silently becoming zero clock readings. Polarity processing can help or hurt depending on the installed model. Default confidence cutoff is 0.7; for the user-authorised initial trial, add `--min-confidence 0.5` to the clock command. This changes OCR eligibility only; it is not a claim of better timing or possession accuracy. All existing progressing-tick, half, duplicate-match and geometry checks remain.\n\nThe trial prints the first percentile (linear interpolation), median and minimum confidence across ALL sampled crops in the requested clip, counting unreadable/invalid clocks as zero. It also prints parsed, unreadable and accepted counts. `First-percentile confidence > 0.5` means the first percentile, not the minimum or a calibrated probability of correctness. Expected clock-absent intervals will lower these all-crop statistics; the first trial intentionally uses a visible mid-game interval. Optimise based on the trial output and independent evidence afterwards.\n\n**Retry update:** only a crop that is unreadable or below the chosen cutoff is retried. Two local treatments restore the original enlarged crop (undoing the tactical inversion and added border) and threshold the processed crop to black and white. If eligible treatments disagree on the clock, the sample stays unresolved. Otherwise the highest measured eligible score is retained; scores are never increased by agreement. Retry counts, recoveries at the cutoff and conflicts are printed. These are selected OCR scores after retries, not independent accuracy measurements. The reads CSV records the chosen treatment and number of attempts.\n\nThe timeline can now skip a weak or unreadable sample when the accepted observations on either side are at most 0.5 seconds apart and the clock remains consistent. At the pilot\'s stride 5 and 25 fps, this tolerates one missed sample; two consecutive misses split the run. Tick uncertainty increases across the gap. At least three consistent second ticks are still required, with no extrapolation. A bounded time estimate can therefore exist at a frame whose own OCR remained unreadable; this does not change its all-crop OCR score from zero. Stricter combined timing uncertainty can still reject a two-camera correspondence.\n\nTo test one existing raw crop without rescanning a video:\n\n```bash\npython football_pipeline.py camera ocr-check --image "outputs/tactical-clock-preview.png" --source tactical\n```\n\nThis prints OCR text and Tesseract\'s confidence score before and after preprocessing. Scores are not measured accuracy. Previews saved by the updated clock command already show the preprocessed OCR input; applying `ocr-check` to one of those compares that input against an additional polarity transformation, so the Original score is the relevant current-input score. No image leaves your machine.\n\nThe user-specified half must match the entire selected interval. Do not run a half-1 command across halftime or the second half. MM:SS alone cannot distinguish first-half stoppage time from overlapping second-half minutes. This version is a selected-clip pilot; joining separate half pilots into one full-match clock map is not automated. A later merge must preserve original indices and use distinct segment IDs.\n\nThen build candidate alignment and fuse:\n\n```bash\npython football_pipeline.py camera align --tactical-clock outputs/tactical-clock.csv --broadcast-clock outputs/broadcast-clock.csv --out outputs/alignment.csv\npython football_pipeline.py camera fuse --data-dir "D:/mtah-data" --alignment outputs/alignment.csv --out outputs/ensemble\n```\n\nThe dense clock CSV has one row per original video frame, including blank estimates outside the pilot. Fusion retains the original tactical-only result wherever no eligible broadcast correspondence exists. The resulting submission-shaped CSV remains experimental; an automatic live/dead classifier is still absent.\n\nIf few candidates survive, first inspect OCR reads, crop placement, timing uncertainty and the selected match-time overlap. Do not loosen every threshold to make the coverage number look better. A finer OCR stride, such as `--stride 1`, can reduce tick timing uncertainty at increased runtime. Clock scans decode from the start of the file to preserve decoded indices; later intervals can therefore cost more than their clip duration suggests.\n\n## Files to inspect\n\n| File | Meaning |\n|---|---|\n| `tactical-clock.csv` / `broadcast-clock.csv` | Original frame, half, estimated match seconds, timing uncertainty, segment ID |\n| `*.reads.csv` | Selected OCR reading, measured score, chosen treatment and attempt count; generated automatically |\n| `alignment.csv` | Tactical frame, candidate broadcast frame, uncertainty and candidate/rejection status |\n| `fusion_diagnostics.csv` | Camera weights, fusion decision and geometry result per tactical frame |\n| `ensemble_report.json` | Tactical-only vs fused label coverage; rescues, replacements and conflicts |\n| `submission.csv` | Experimental predictions on the tactical timeline |\n\nFor example, a frame can have estimated match time 1622.32 seconds while its counterpart has a completely different file frame index. Timing uncertainty is reported separately; this is not a claim of exact frame synchronisation.\n\n## Weights and safeguards\n\nProvisional values in code:\n\n- Direct tactical control: weight 1.0. Inferred tactical continuity: 0.35.\n- Eligible broadcast control: `0.9 * geometry_quality * (1 - 0.5 * uncertainty / 0.25)`.\n- Geometry quality combines player-position agreement with reprojection error.\n- Broadcast needs weight >= 0.3 to rescue X; replacing a conflicting inferred tactical label additionally requires a normalised vote advantage >= 0.2.\n- Maximum combined clock uncertainty: 0.25 seconds. Coarse one-second OCR is often insufficient. The geometry limits default to 3 m median player residual, at least three distinct matches per team and 60% of unique broadcast points, 4 m ball residual when visible in both views, and reprojection error <= 3.\n\nThese values are engineering defaults, not calibrated probabilities or values tuned on the public five minutes. The exact numbers will need independent evaluation on compatible other-match data. The fusion default preserves direct tactical disagreements; it is intentionally more restrictive than blindly averaging two labels.\n\n## Limitations to assess on local data\n\n- A replay can carry a live clock and plausible player positions. The checks reduce false matches but do **not** constitute a complete replay detector.\n- Camera overlays can have systematic delay or rounding differences; tick matching alone does not prove the same physical moment.\n- Both ATD exports must use compatible pitch orientation and coordinates. If they disagree, geometry rejects the match; automatic orientation calibration is not implemented.\n- A narrow broadcast shot may have too few players to verify. Invalid homography does not mean dead ball.\n- Player point sets can agree accidentally; no persistent player identity is assumed. Distinct spatial matching prevents duplicate tracks from counting as independent support.\n- Added-time parser accepts `45+02:13` and `90+01:02`, but actual live OCR/crop behaviour for added-time overlays is untested. Clocks freezing at 45:00/90:00 without a readable added-time timer leave unsupported intervals.\n- No actual competition footage/tracking was processed here. The displayed screenshots were only used to identify clock format and approximate layout. They are not bundled or used as labels or timing anchors.\n\nKeep all footage, crops, tracking and derived alignment outputs local. Do not upload restricted competition assets or extracts to hosted/cloud LLMs, publish them, or use public labels for model selection. No network calls exist in these modules.\n\nOfficial tool references: https://tesseract-ocr.github.io/tessdoc/Command-Line-Usage.html and https://ffmpeg.org/ffmpeg-filters.html . Competition formats follow the uploaded starter snapshot.\n'

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
    importlib.import_module(module).main()


if __name__ == "__main__":
    main()
