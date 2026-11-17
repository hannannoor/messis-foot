"""Conservative team-control evidence and offline gap handling. No learned probabilities."""
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
