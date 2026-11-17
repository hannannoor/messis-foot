"""Quality-gated heuristic votes; these weights are not calibrated probabilities."""
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
