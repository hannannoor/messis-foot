"""Research-only 20-column feature adapter (Experiment A: support-aware recent geometry).

Columns 1-18 are produced by the unmodified ``gap_solver.tactical.feature_rows`` and are never
altered.  Two columns are appended:

  19  recent_distance_margin   mean of the existing ``distance_margin`` column (index 5, ``a-h`` on the
                               30 m clipped distances) over *qualifying* rows of the trailing window of
                               12 canonical rows including the current one; 0.0 when none qualify.
  20  recent_distance_support  qualifying rows in that window / 12.

A row qualifies when the period is 1 or 2, the geometry is valid, the ball is observed and both
distances are finite and non-negative.  Non-qualifying rows still occupy a window slot, so stale
evidence expires after 12 rows.  Only this new window is cleared (period change, period 0, explicit
invalid geometry); the original feature state is never touched.  No reference, status or tag field
is read.  The mean is ``math.fsum`` so the value does not depend on the interpreter's ``sum``.
"""
from collections import deque
from math import fsum, isfinite

import numpy as np

from gap_solver.motion import MotionFrame
from gap_solver.tactical import FEATURE_NAMES, feature_rows

WINDOW = 12
NEW_NAMES = ('recent_distance_margin', 'recent_distance_support')
RESEARCH_FEATURE_NAMES = tuple(FEATURE_NAMES) + NEW_NAMES
_MISSING = object()


def geometry_valid(frame):
    """Plain records without the field are valid; MotionFrame or any declaring record needs a real bool."""
    value = getattr(frame, 'geometry_valid', _MISSING)
    if value is _MISSING:
        if isinstance(frame, MotionFrame):
            raise ValueError('motion record lacks the required geometry_valid flag')
        return True
    if type(value) is not bool:
        raise ValueError('geometry_valid must be an explicit bool')
    return value


def _distance_ok(value):
    return value is not None and isfinite(value) and value >= 0


def research_rows(frames):
    """Yield 20-tuples; the first 18 equal ``feature_rows(frames)`` exactly."""
    frames = list(frames)
    window = deque(maxlen=WINDOW)          # margin for qualifying rows, None for unsupported slots
    previous_period = None
    for frame, row in zip(frames, feature_rows(frames)):
        valid = geometry_valid(frame)      # malformed flags stop preparation on every row
        if frame.period != previous_period or frame.period == 0 or not valid:
            window.clear()
        previous_period = frame.period
        if frame.period in (1, 2) and valid:
            qualifies = (frame.ball_observed and _distance_ok(frame.home_distance)
                         and _distance_ok(frame.away_distance))
            window.append(row[5] if qualifies else None)
        used = [m for m in window if m is not None]
        margin = fsum(used) / len(used) if used else 0.
        yield tuple(row) + (margin, len(used) / WINDOW)


def research_matrix(frames):
    """float32 (n, 20) matrix; the first 18 columns equal ``np.asarray(list(feature_rows), float32)``."""
    values = np.asarray(list(research_rows(frames)), dtype=np.float32)
    if values.ndim != 2 or values.shape[1] != 20 or not np.isfinite(values).all():
        raise ValueError('invalid research feature matrix')
    return values
