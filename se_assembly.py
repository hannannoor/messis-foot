"""Configurable copy of the release decoder chain (recent_geometry_assembly.assemble_research).

missing_w scales the log-evidence on rows without an observed ball (0.0 = release behaviour: neutral rows, and
usable runs with no observed ball become unusable). cost = switch cost (release 32). Returns every stage.
With missing_w=0 and cost=32 this reproduces assemble_research exactly (checked in se_score2 parity mode).
"""
import numpy as np

from gap_liveness import apply_gap_rule
from gap_solver.materialization_control import materialize_abstentions
from gap_solver.soft_sequence import decode_soft, sequence_usable, soft_emissions
from kickoff_patch import apply_kickoff_patch
from touch_decoder import decode_variable
from touch_evidence import evidence_rows


def _ha_only(row, w):
    from math import log, exp
    h, a = row[0], row[1]
    m = max(h, a)
    lse = m + log(exp(h - m) + exp(a - m))
    h2, a2 = w * (h - lse), w * (a - lse)
    return (h2, a2, max(h2, a2))


def _rows(supports, frames, periods, usable, observed, missing_w, mode='all'):
    rows = soft_emissions(supports, [0.] * len(frames), 0.)
    if mode == 'ha':
        rows = [row if seen else _ha_only(row, missing_w) for row, seen in zip(rows, observed)]
    else:
        rows = [row if seen else tuple(missing_w * v for v in row) for row, seen in zip(rows, observed)]
    effective = list(usable)
    i, n = 0, len(frames)
    while i < n:
        if not periods[i] or not usable[i]:
            i += 1
            continue
        first, period = i, periods[i]
        while i < n and periods[i] == period and usable[i]:
            i += 1
        if missing_w == 0 and not any(observed[first:i]):
            effective[first:i] = [False] * (i - first)
    return rows, effective


def assemble(frames, supports, starts=(), *, missing_w=0.0, cost=32.0, cost_d=None, mode='all'):
    frames = list(frames)
    supports = np.asarray(supports, np.float64).tolist()
    periods = [f.period for f in frames]
    usable = [sequence_usable(f) for f in frames]
    observed = [f.ball_observed for f in frames]
    rows, effective = _rows(supports, frames, periods, usable, observed, missing_w, mode)
    if cost_d is None:
        latent = decode_soft(rows, periods, effective, float(cost))
    else:
        latent = decode_variable(rows, periods, effective, [(float(cost), float(cost), float(cost_d))] * len(rows))
    control = materialize_abstentions(latent, periods)
    first = apply_gap_rule(frames, control)
    ev_rows, costs = evidence_rows(rows, periods, effective, [], 0, 32)
    if cost != 32.0 or cost_d is not None:
        costs = [(float(cost), float(cost), float(cost if cost_d is None else cost_d)) for _ in costs]
    usable2 = list(effective)
    for a, b in first.stoppage_gaps:
        usable2[a:b] = [False] * (b - a)
    latent2 = decode_variable(ev_rows, periods, usable2, costs)
    second = apply_gap_rule(frames, materialize_abstentions(latent2, periods))
    patch = apply_kickoff_patch(frames, second.labels, starts)
    nogap = apply_kickoff_patch(frames, tuple(control), starts)
    return dict(control=tuple(control), gapped=tuple(first.labels), restarted=tuple(second.labels),
                final=tuple(patch.labels), nogap=tuple(nogap.labels))
