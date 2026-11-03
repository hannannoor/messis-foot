"""Clock-only candidate mapping. A matching clock is NOT proof of live footage."""
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
