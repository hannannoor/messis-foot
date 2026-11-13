"""Experiment F: half-weight dead-ball evidence on missing-ball rows.

Visible rows keep the release emission of the control support.  A missing-ball row, which the release scores
as neutral (0, 0, 0), instead receives ``(0, 0, lam * max(0, log pD - log((pH + pA) / 2)))`` from Experiment
E's stillness tree (floors 1e-6).  The term only ever adds evidence for D, never for a team.

``assemble_missing`` mirrors ``recent_geometry_assembly.assemble_research`` step for step (unsupported
segments, first decode, materialisation, gap rule, decoder restart across stoppage gaps, gap rule, kickoff
patch) with these rows in both decodes.  With ``lam == 0`` it returns the same assembly as
``assemble_research``.
"""
from math import isfinite, log

from ball_gap_policy import decode_soft
from gap_liveness import apply_gap_rule
from gap_solver.materialization_control import materialize_abstentions
from gap_solver.soft_sequence import sequence_usable, soft_emissions
from kickoff_patch import apply_kickoff_patch
from recent_geometry_assembly import ResearchAssembly, SupportSet
from touch_decoder import decode_variable
from touch_evidence import evidence_rows
from touch_physics import validate_frames

LAMBDA = 0.5
FLOOR = 1e-6


def _check_lambda(lam):
    if not isinstance(lam, (int, float)) or not isfinite(lam) or lam < 0:
        raise ValueError('lambda must be finite and non-negative')


def missing_row(support, lam):
    _check_lambda(lam)
    if lam == 0:
        return (0., 0., 0.)
    pH, pA, pD = (float(v) for v in support)
    gain = log(max(pD, FLOOR)) - log(max((pH + pA) / 2, FLOOR))
    return (0., 0., float(lam) * max(0., gain))


def emission_rows(control_supports, still_supports, observed, lam):
    _check_lambda(lam)
    n = len(observed)
    if len(control_supports) != n or len(still_supports) != n:
        raise ValueError('Emission input dimensions differ')
    visible = soft_emissions(control_supports, [0.] * n, 0.)
    return [row if seen else missing_row(still, lam) for row, still, seen in zip(visible, still_supports, observed)]


def _effective(periods, usable, observed):
    """Release rule: a usable segment with no observed row is unusable for the decoder."""
    effective = list(usable)
    i, n = 0, len(periods)
    while i < n:
        if not periods[i] or not usable[i]:
            i += 1
            continue
        first, period = i, periods[i]
        while i < n and periods[i] == period and usable[i]:
            i += 1
        if not any(observed[first:i]):
            effective[first:i] = [False] * (i - first)
    return effective


def assemble_missing(frames, control_set, still_set, starts=(), *, lam, use_restart=True):
    if not isinstance(control_set, SupportSet) or not isinstance(still_set, SupportSet):
        raise ValueError('Explicit SupportSets are required')
    frames = list(frames)
    if len(frames) != len(control_set.supports) or len(frames) != len(still_set.supports):
        raise ValueError('Support rows differ from frames')
    if any(f.tag_team or f.restart_hint or f.dead_evidence or f.dead_source for f in frames):
        raise ValueError('Research assembly accepts geometry without label hints')
    validate_frames(frames)
    periods = [f.period for f in frames]
    usable = [sequence_usable(f) for f in frames]
    observed = [f.ball_observed for f in frames]
    rows = emission_rows(control_set.supports.tolist(), still_set.supports.tolist(), observed, lam)
    effective = _effective(periods, usable, observed)
    latent = decode_soft(rows, periods, effective, 32.)
    control = materialize_abstentions(latent, periods)
    rows, costs = evidence_rows(rows, periods, effective, [], 0, 32)
    first = apply_gap_rule(frames, control)
    passes = 1
    if use_restart:
        usable2 = list(effective)
        for first_frame, stop in first.stoppage_gaps:
            usable2[first_frame:stop] = [False] * (stop - first_frame)
        restart = decode_variable(rows, periods, usable2, costs)
        passes += 1
        second = apply_gap_rule(frames, materialize_abstentions(restart, periods))
        if second.stoppage_gaps != first.stoppage_gaps:
            raise ValueError('Stoppage gaps changed during the second application')
    else:
        second = first
    patch = apply_kickoff_patch(frames, second.labels, starts)
    return ResearchAssembly(tuple(control), first.labels, second.labels, patch.labels,
                            first.stoppage_gaps, second.summary, patch.changed,
                            latent=tuple(latent), decoder_passes=passes)
