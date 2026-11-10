"""Stoppage-like ball-removal regimes built from a match's reference labels. Pure, deterministic, standard library.

Reference codes: 0 = H, 1 = A, 2 = D, 3 = X. The result is a mask of frames on which the ball is removed.
"""
import hashlib

MIN_LONG = 76          # the provided match's long-gap threshold (label-free)
LIVE_WINDOW = 268      # the provided match's median gap length (label-free)
OFFSET_RANGE = 51      # 0..50 frames = up to 2 s at 25 fps
# name -> (selection level c, live-frame target as a fraction of the dead frames removed, jitter after masking)
REGIMES = {
    'natural': (None, (0, 1), False),
    'stop100': (1.0, (0, 1), False),
    'stop75': (.75, (1, 3), False),
    'stop50': (.5, (1, 1), False),
    'stop75-jitter': (.75, (1, 3), True),
}


def h(text):
    return int(hashlib.sha256(text.encode()).hexdigest(), 16)


def _periods(periods):
    """Maximal runs of equal period 1 or 2 as (period, first, stop)."""
    result, i, n = [], 0, len(periods)
    while i < n:
        if periods[i] not in (1, 2):
            i += 1
            continue
        j = i
        while j < n and periods[j] == periods[i]:
            j += 1
        result.append((periods[i], i, j))
        i = j
    return result


def make_mask(match_id, reference, periods, regime):
    if regime not in REGIMES:
        raise ValueError('Unknown regime')
    if len(reference) != len(periods):
        raise ValueError('Reference and periods differ in length')
    level, (numerator, denominator), _ = REGIMES[regime]
    n = len(periods)
    mask = [False] * n
    info = dict(long_dead_runs=0, selected=0, selected_starts=[], dead_blocks=[], live_blocks=[], dead_frames_removed=0)
    if level is None:
        return mask, info
    cutoff = round(100 * level)
    for _, first, stop in _periods(periods):
        i = first
        while i < stop:
            if reference[i] != 2:
                i += 1
                continue
            start = i
            while i < stop and reference[i] == 2:
                i += 1
            end = i
            if end - start < MIN_LONG:
                continue
            info['long_dead_runs'] += 1
            if h(f'{match_id}:sel:{start}') % 100 >= cutoff:
                continue
            info['selected'] += 1
            info['selected_starts'].append(start)
            a = h(f'{match_id}:a:{start}') % OFFSET_RANGE
            b = h(f'{match_id}:b:{start}') % OFFSET_RANGE
            block = (start + a, min(end + b, stop))
            if block[1] - block[0] < MIN_LONG:
                block = (start, end)
            info['dead_blocks'].append(block)
            for k in range(*block):
                mask[k] = True
    dead_removed = sum(mask)
    info['dead_frames_removed'] = dead_removed
    if numerator:
        candidates = []
        for period, first, stop in _periods(periods):
            for k in range((stop - first) // LIVE_WINDOW):
                a = first + k * LIVE_WINDOW
                b = a + LIVE_WINDOW
                if all(reference[j] in (0, 1) for j in range(a, b)):
                    candidates.append((h(f'{match_id}:live:{period}:{k}'), a, b))
        candidates.sort()
        removed = 0
        for _, a, b in candidates:
            if removed * denominator >= dead_removed * numerator:
                break
            if any(mask[a:b]):
                continue
            for j in range(a, b):
                mask[j] = True
            info['live_blocks'].append((a, b))
            removed += b - a
    return mask, info
