"""Evaluation regimes for Experiment A: visible-ball noise, pure live gaps, stoppage and reacquisition.

Nothing here reads the provided match or any statistic derived from it.  Reference-built masks are
evaluation machinery only: they are generated and sealed before any prediction, and inference receives
only the transformed geometry.
"""
from dataclasses import replace
import hashlib
import json
from math import hypot, isfinite
import random

import numpy as np

from gap_solver.temporal import mask_motion_frames
from memory_ablation_training import semantic_digest

JITTER_PREFIX = 'recent-geometry-jitter-v1:1729:'
JITTER_SIGMA = .25
LIVE_WINDOW = 250
LIVE_FRACTION_NUM, LIVE_FRACTION_DEN = 1, 10     # mask up to 10% of a period's known live frames
LIVE_MAX_WINDOWS = 10
LIVE_MIN_VISIBLE = 200                           # 80% of 250
STOPPAGE_TAIL = 25


def noise_seed(case_id):
    digest = hashlib.sha256((JITTER_PREFIX + case_id).encode('utf-8')).hexdigest()
    return int(digest[:8], 16)


def _nearest(points, x, y):
    values = [hypot(px - x, py - y) for px, py in points]
    return min(values) if values else None


def add_visible_ball_noise(frames, case_id):
    """Zero-mean Gaussian (sigma 0.25 m) on each naturally visible ball coordinate; distances recomputed.

    One fresh ``random.Random`` per case; rows ascending; x then y; nothing drawn on missing rows;
    no clipping, retiming or visibility change.  Any non-finite or unrecomputable record stops.
    """
    rng = random.Random(noise_seed(case_id))
    out = []
    for frame in frames:
        if not frame.ball_observed:
            out.append(frame)
            continue
        if not hasattr(frame, 'home_xy') or not hasattr(frame, 'away_xy'):
            raise ValueError('visible-ball noise needs player positions to recompute distances')
        x = frame.ball_x + rng.gauss(0, JITTER_SIGMA)
        y = frame.ball_y + rng.gauss(0, JITTER_SIGMA)
        distances = [_nearest(frame.home_xy, x, y), _nearest(frame.away_xy, x, y)]
        if not (isfinite(x) and isfinite(y)) or any(d is not None and not isfinite(d) for d in distances):
            raise ValueError('non-finite transformed record')
        out.append(replace(frame, ball_x=x, ball_y=y, home_distance=distances[0], away_distance=distances[1]))
    return out


def distance_recompute_audit(frames):
    """Compare the noise regime's recomputation (zero noise) with the loader's stored distances, exactly.

    Aggregates only.  ``exact_rows == checked_rows`` and ``max_abs_diff == 0`` are required before the freeze.
    """
    checked = exact = none_disagreements = unobserved_with_distance = 0
    max_abs_diff = 0.
    for frame in frames:
        if not frame.ball_observed:
            unobserved_with_distance += int(frame.home_distance is not None or frame.away_distance is not None)
            continue
        if not hasattr(frame, 'home_xy') or not hasattr(frame, 'away_xy'):
            raise ValueError('distance audit needs player positions')
        checked += 1
        same = True
        for got, stored in ((_nearest(frame.home_xy, frame.ball_x, frame.ball_y), frame.home_distance),
                            (_nearest(frame.away_xy, frame.ball_x, frame.ball_y), frame.away_distance)):
            if got is None or stored is None:
                if got is not stored:
                    none_disagreements += 1
                    same = False
            else:
                max_abs_diff = max(max_abs_diff, abs(got - stored))
                same = same and got == stored
        exact += int(same)
    return dict(checked_rows=checked, exact_rows=exact, mismatched_rows=checked - exact,
                none_disagreements=none_disagreements, max_abs_diff=max_abs_diff,
                unobserved_rows_with_stored_distance=unobserved_with_distance)


def apply_ball_mask(frames, mask):
    """Clear ball observation, provenance and distances where ``mask``; player tracks are kept."""
    return mask_motion_frames(list(frames), np.asarray(mask, dtype=bool))


def _runs(periods):
    start = None
    for i, p in enumerate(periods):
        if start is None or p != periods[start]:
            if start is not None and periods[start] in (1, 2):
                yield start, i
            start = i
    if start is not None and periods[start] in (1, 2):
        yield start, len(periods)


def live_gap_windows(case_id, periods, reference, observed):
    """Tile complete 250-frame windows per period, qualify them, order by SHA-256 and select to 10%."""
    periods = np.asarray(periods)
    reference = np.asarray(reference)
    seen = np.asarray(observed, dtype=bool)
    if periods.ndim != 1 or reference.shape != periods.shape or seen.shape != periods.shape:
        raise ValueError('live-gap input dimensions differ')
    mask = np.zeros(len(periods), dtype=bool)
    eligible, selected = [], []
    for first, stop in _runs(periods.tolist()):
        period = int(periods[first])
        known_live = int((reference[first:stop] < 2).sum())
        windows = []
        index = 0
        w_first = first
        while w_first + LIVE_WINDOW <= stop:
            w_stop = w_first + LIVE_WINDOW
            before, after = w_first - 1, w_stop
            if (before >= first and after < stop and seen[before] and seen[after]
                    and bool((reference[w_first:w_stop] < 2).all())
                    and int(seen[w_first:w_stop].sum()) >= LIVE_MIN_VISIBLE):
                windows.append(dict(period=period, index=index, first=w_first, stop=w_stop))
            index += 1
            w_first = w_stop
        eligible.extend(windows)
        ordered = sorted(windows, key=lambda w: hashlib.sha256(
            f'{case_id}:live250-v1:{period}:{w["index"]}'.encode()).hexdigest())
        chosen = []
        while (len(chosen) < min(len(ordered), LIVE_MAX_WINDOWS)
               and len(chosen) * LIVE_WINDOW * LIVE_FRACTION_DEN < known_live * LIVE_FRACTION_NUM):
            window = ordered[len(chosen)]
            chosen.append(window)
            mask[window['first']:window['stop']] = True
        selected.extend(chosen)
    return dict(mask=mask, eligible=eligible, selected=selected)


def stoppage_mask(periods, reference):
    """Hide every full reference-D run plus its first 25 post-D frames (same period, before any X)."""
    periods = np.asarray(periods)
    reference = np.asarray(reference)
    if periods.ndim != 1 or reference.shape != periods.shape:
        raise ValueError('stoppage input dimensions differ')
    mask = np.zeros(len(periods), dtype=bool)
    for first, stop in _runs(periods.tolist()):
        i = first
        while i < stop:
            if reference[i] != 2:
                i += 1
                continue
            run_start = i
            while i < stop and reference[i] == 2:
                i += 1
            mask[run_start:i] = True
            tail = i
            while tail < stop and tail - i < STOPPAGE_TAIL and reference[tail] != 3:
                mask[tail] = True
                tail += 1
    return mask


def seal_digest(arrays):
    """Hash of named arrays (dtype, shape, bytes); recorded before any prediction."""
    value = {name: semantic_digest(array) for name, array in sorted(arrays.items())}
    return hashlib.sha256((json.dumps(value, sort_keys=True, separators=(',', ':')) + '\n').encode()).hexdigest()
