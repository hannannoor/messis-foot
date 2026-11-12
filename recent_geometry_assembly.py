"""Emission-supplied research assembly: supports -> decode -> gap rule -> decoder restart -> gap rule -> kickoff.

Reproduces ``restart_release.assemble`` step for step, but every decision is driven by one explicit
``SupportSet`` (one method's per-row H/A/D supports).  This module never touches the frozen model or the
release inference entry points; the first decode and the restart decode necessarily share the same
supports because both are fed from a single prepared row set.  Kickoff starts are empty for both methods.
"""
from dataclasses import dataclass
from math import isfinite

import numpy as np

from ball_gap_policy import decode_ball_gap
from gap_liveness import apply_gap_rule
from gap_solver.materialization_control import materialize_abstentions
from gap_solver.soft_sequence import sequence_usable, soft_emissions
from kickoff_patch import apply_kickoff_patch
from memory_ablation import predict_supports
from recent_geometry_training import predict_supports_research
from restart_release import Assembly
from touch_decoder import decode_variable
from touch_evidence import evidence_rows
from touch_physics import validate_frames

METHODS = ('control', 'candidate')


@dataclass(frozen=True)
class SupportSet:
    method: str
    supports: object

    def __post_init__(self):
        if self.method not in METHODS:
            raise ValueError('Unknown method')
        values = np.array(self.supports, dtype=np.float64, copy=True)
        if values.ndim != 2 or values.shape[1] != 3 or not np.isfinite(values).all():
            raise ValueError('Supports must be a finite (n, 3) array')
        values.setflags(write=False)
        object.__setattr__(self, 'supports', values)

    @classmethod
    def from_matrix(cls, method, matrix, model):
        """Control uses the 18-column prefix with the frozen-style tree; candidate uses all 20 columns."""
        matrix = np.asarray(matrix)
        if method == 'control':
            return cls(method, predict_supports(matrix[:, :18], model))
        if method == 'candidate':
            return cls(method, predict_supports_research(matrix, model))
        raise ValueError('Unknown method')


def _prepare(frames, supports):
    validate_frames(frames)
    periods = [f.period for f in frames]
    usable = [sequence_usable(f) for f in frames]
    observed = [f.ball_observed for f in frames]
    rows = soft_emissions(supports, [0.] * len(frames), 0.)
    rows = [row if seen else (0., 0., 0.) for row, seen in zip(rows, observed)]
    effective = list(usable)
    segments = unsupported = 0
    i, n = 0, len(frames)
    while i < n:
        if not periods[i] or not usable[i]:
            i += 1
            continue
        first, period = i, periods[i]
        while i < n and periods[i] == period and usable[i]:
            i += 1
        if not any(observed[first:i]):
            segments += 1
            unsupported += i - first
            effective[first:i] = [False] * (i - first)
    rows, costs = evidence_rows(rows, periods, effective, [], 0, 32)
    return rows, costs, periods, effective, dict(unsupported_segments=segments, unsupported_active_rows=unsupported)


@dataclass(frozen=True)
class ResearchAssembly(Assembly):
    """``Assembly`` plus the first decode's latent labels and the decoder passes actually executed."""
    latent: tuple = ()
    decoder_passes: int = 0


def _decode_stoppages(frames, control, prepared, *, use_restart, verify_decoder):
    """``restart_release.decode_stoppages`` logic; the control-reproduction decode is optional (parity runs only)."""
    rows, costs, periods, usable, _ = prepared
    passes = 0
    if verify_decoder:
        original = tuple(materialize_abstentions(decode_variable(rows, periods, usable, costs), periods))
        passes += 1
        if original != tuple(control):
            raise ValueError('Variable decoder does not reproduce the first decode')
    first = apply_gap_rule(frames, control)
    if not use_restart:
        return first, first, passes
    usable2 = list(usable)
    for first_frame, stop in first.stoppage_gaps:
        usable2[first_frame:stop] = [False] * (stop - first_frame)
    latent = decode_variable(rows, periods, usable2, costs)
    passes += 1
    second = apply_gap_rule(frames, materialize_abstentions(latent, periods))
    if second.stoppage_gaps != first.stoppage_gaps:
        raise ValueError('Stoppage gaps changed during the second application')
    return first, second, passes


def assemble_research(frames, support_set, starts=(), *, use_restart=True, verify_decoder=False):
    if not isinstance(support_set, SupportSet):
        raise ValueError('An explicit SupportSet is required')
    frames = list(frames)
    if len(frames) != len(support_set.supports):
        raise ValueError('Support rows differ from frames')
    if any(f.tag_team or f.restart_hint or f.dead_evidence or f.dead_source for f in frames):
        raise ValueError('Research assembly accepts geometry without label hints')
    supports = support_set.supports.tolist()
    periods = [f.period for f in frames]
    latent, _ = decode_ball_gap(supports, periods, [sequence_usable(f) for f in frames],
                                [f.ball_observed for f in frames])
    control = materialize_abstentions(latent, periods)
    prepared = _prepare(frames, supports)
    first, second, passes = _decode_stoppages(frames, control, prepared, use_restart=use_restart,
                                              verify_decoder=verify_decoder)
    patch = apply_kickoff_patch(frames, second.labels, starts)
    return ResearchAssembly(tuple(control), first.labels, second.labels, patch.labels,
                            first.stoppage_gaps, second.summary, patch.changed,
                            latent=tuple(latent), decoder_passes=1 + passes)
