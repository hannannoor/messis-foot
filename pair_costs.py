"""Experiment G: pair switch costs from training transitions, and the research assembly with the pair decoder.

Rule (training data only): count consecutive-row pairs ``n_ij`` within one period with both codes in H/A/D
(0/1/2) and both periods in 1-2; ``p_ij = n_ij / sum_k n_ik``; for ``i != j`` ``q_ij = -log p_ij``, a pair with
``n_ij = 0`` gets the largest observed off-diagonal ``q``; ``C_ij = 32 * q_ij / mean_{i != j}(q_ij)``.

``assemble_pairs`` mirrors ``recent_geometry_assembly.assemble_research`` step for step with both decodes
replaced by ``decode_matrix``.  With ``uniform_matrix(32.)`` it returns the same assembly.
"""
from math import log

import numpy as np

from gap_liveness import apply_gap_rule
from gap_solver.materialization_control import materialize_abstentions
from gap_solver.soft_sequence import sequence_usable, soft_emissions
from kickoff_patch import apply_kickoff_patch
from pair_decoder import decode_matrix, validate_matrix
from recent_geometry_assembly import ResearchAssembly, SupportSet, _prepare

MEAN_COST = 32.


def transition_counts(groups):
    n = [[0] * 3 for _ in range(3)]
    for g in groups:
        reference = np.asarray(g['reference'])
        periods = np.asarray(g['periods'])
        if reference.shape != periods.shape or reference.ndim != 1:
            raise ValueError('Reference and period dimensions differ')
        ref, per = reference.tolist(), periods.tolist()
        for a, b, pa, pb in zip(ref, ref[1:], per, per[1:]):
            if pa == pb and pa in (1, 2) and a in (0, 1, 2) and b in (0, 1, 2):
                n[a][b] += 1
    return n


def costs_from_counts(counts):
    n = [[int(v) for v in row] for row in counts]
    off = [(i, j) for i in range(3) for j in range(3) if i != j]
    if not any(n[i][j] for i, j in off):
        raise ValueError('No transitions for the pair-cost rule')
    q = [[0.] * 3 for _ in range(3)]
    for i, j in off:
        if n[i][j]:
            q[i][j] = -log(n[i][j] / sum(n[i]))
    top = max(q[i][j] for i, j in off if n[i][j])
    for i, j in off:
        if not n[i][j]:
            q[i][j] = top
    mean = sum(q[i][j] for i, j in off) / len(off)
    if not mean > 0:
        raise ValueError('Degenerate transition rates')
    matrix = tuple(tuple(0. if i == j else MEAN_COST * q[i][j] / mean for j in range(3)) for i in range(3))
    return dict(matrix=validate_matrix(matrix), counts=n, q=q, mean=MEAN_COST)


def pair_cost_rule(groups):
    return costs_from_counts(transition_counts(groups))


def _first_decode(supports, periods, usable, observed, matrix):
    """``ball_gap_policy.decode_ball_gap`` with the pair decoder in place of ``decode_soft``."""
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
    return decode_matrix(rows, periods, effective, matrix)


def assemble_pairs(frames, support_set, starts=(), *, matrix, use_restart=True):
    if not isinstance(support_set, SupportSet):
        raise ValueError('An explicit SupportSet is required')
    matrix = validate_matrix(matrix)
    frames = list(frames)
    if len(frames) != len(support_set.supports):
        raise ValueError('Support rows differ from frames')
    if any(f.tag_team or f.restart_hint or f.dead_evidence or f.dead_source for f in frames):
        raise ValueError('Research assembly accepts geometry without label hints')
    supports = support_set.supports.tolist()
    periods = [f.period for f in frames]
    latent = _first_decode(supports, periods, [sequence_usable(f) for f in frames], [f.ball_observed for f in frames],
                           matrix)
    control = materialize_abstentions(latent, periods)
    rows, _, periods, usable, _ = _prepare(frames, supports)
    first = apply_gap_rule(frames, control)
    passes = 1
    if use_restart:
        usable2 = list(usable)
        for first_frame, stop in first.stoppage_gaps:
            usable2[first_frame:stop] = [False] * (stop - first_frame)
        restart = decode_matrix(rows, periods, usable2, matrix)
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
