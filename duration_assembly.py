"""Experiment D: spell-length rule and the research assembly with the duration-aware decoder.

``assemble_duration`` mirrors ``recent_geometry_assembly.assemble_research`` step for step (neutral
missing-ball rows, unsupported segments, gap rule, decoder restart across stoppage gaps, gap rule,
kickoff patch) with both decodes replaced by ``duration_decode``.  With ``extra == 0`` it returns the
same labels as ``assemble_research``.
"""
from math import ceil

import numpy as np

from duration_decoder import duration_decode, uniform_costs
from gap_liveness import apply_gap_rule
from gap_solver.materialization_control import materialize_abstentions
from gap_solver.soft_sequence import sequence_usable, soft_emissions
from kickoff_patch import apply_kickoff_patch
from recent_geometry_assembly import ResearchAssembly, SupportSet, _prepare

MIN_RUN_BOUNDS = (5, 50)
PERCENTILE = .10


def spell_length_rule(groups):
    """Nearest-rank 10th percentile of pooled maximal reference runs (codes 0/1/2, periods 1-2), clamped."""
    runs = []
    for group in groups:
        reference = np.asarray(group['reference'])
        periods = np.asarray(group['periods'])
        if reference.shape != periods.shape:
            raise ValueError('Reference and period dimensions differ')
        current, length, period = None, 0, None
        for code, p in zip(reference.tolist(), periods.tolist()):
            valid = p in (1, 2) and code in (0, 1, 2)
            if valid and code == current and p == period:
                length += 1
                continue
            if current is not None:
                runs.append(length)
            current, length, period = (code, 1, p) if valid else (None, 0, None)
        if current is not None:
            runs.append(length)
    if not runs:
        raise ValueError('No reference runs for the spell-length rule')
    rank = ceil(PERCENTILE * len(runs))
    value = sorted(runs)[rank - 1]
    lo, hi = MIN_RUN_BOUNDS
    return dict(min_run=int(min(hi, max(lo, value))), runs=len(runs), percentile_rank=rank, raw_value=int(value))


def _first_decode(supports, periods, usable, observed, *, min_run, extra):
    """``ball_gap_policy.decode_ball_gap`` with the duration decoder in place of ``decode_soft``."""
    n = len(periods)
    rows = soft_emissions(supports, [0.] * n, 0.)
    rows = [row if seen else (0., 0., 0.) for row, seen in zip(rows, observed)]
    effective = list(usable)
    i = 0
    while i < n:
        if not periods[i] or not usable[i]:
            i += 1
            continue
        first, period = i, periods[i]
        while i < n and periods[i] == period and usable[i]:
            i += 1
        if not any(observed[first:i]):
            effective[first:i] = [False] * (i - first)
    return duration_decode(rows, periods, effective, uniform_costs(n, 32.), min_run=min_run, extra=extra)


def assemble_duration(frames, support_set, starts=(), *, min_run, extra, use_restart=True):
    if not isinstance(support_set, SupportSet):
        raise ValueError('An explicit SupportSet is required')
    frames = list(frames)
    if len(frames) != len(support_set.supports):
        raise ValueError('Support rows differ from frames')
    if any(f.tag_team or f.restart_hint or f.dead_evidence or f.dead_source for f in frames):
        raise ValueError('Research assembly accepts geometry without label hints')
    supports = support_set.supports.tolist()
    periods = [f.period for f in frames]
    latent = _first_decode(supports, periods, [sequence_usable(f) for f in frames], [f.ball_observed for f in frames],
                           min_run=min_run, extra=extra)
    control = materialize_abstentions(latent, periods)
    rows, costs, periods, usable, _ = _prepare(frames, supports)
    first = apply_gap_rule(frames, control)
    passes = 1
    if use_restart:
        usable2 = list(usable)
        for first_frame, stop in first.stoppage_gaps:
            usable2[first_frame:stop] = [False] * (stop - first_frame)
        restart = duration_decode(rows, periods, usable2, costs, min_run=min_run, extra=extra)
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
