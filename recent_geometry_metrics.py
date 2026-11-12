"""Scores, strata and conjunctive gates for Experiment A.  Aggregates only; thresholds fixed in advance.

Interpretations fixed before any fit (also recorded in docs/recent-geometry-protocol.md):
  * "interior" frame: reference H/A, ball observed, and more than 50 frames from the start or last frame of its
    constant (period, reference-code) run, so period edges and every state/annotation change count as boundaries;
  * D precision/recall, false-D, short-spell and owner-presence checks are evaluated per primary match in every
    regime that is run; spell-F1 checks use the regime's provider weights;
  * the gain hurdle uses a 1e-12 floating round-off tolerance (not a slack on the 0.010 hurdle); loss checks
    use the 1e-6 slack the brief grants;
  * provider-level support counts are pooled over a provider's primary cases.
"""
from math import isfinite

import numpy as np

from gap_solver import official_metrics as official
from memory_ablation_metrics import MATCHES, score_variant
from ownership_diagnosis import _arrays, _evaluation

EPS = 1e-6
ROUNDOFF = 1e-12
GAIN_THRESHOLD = .010
STRESS_PRIMARY_LOSS = .005
MATCH_LOSS = .020
DEAD_LOSS = .010
FALSE_D_RISE = .005
SHORT_RECALL_LOSS = .020
SHORT_FRAMES = 25
SHORT_SUPPORT = 20
INTERIOR_MARGIN = 50
RESTART_WINDOW = 25
RECOVERY_FRAMES = 50
MIN_LIVE_WINDOWS = 5
MIN_RESTART_EVENTS = 20
BINS = ((1, 25), (26, 75), (76, 250), (251, None))

REGIMES = ('natural', 'noise', 'live-gap', 'stoppage')
METHODS = ('control', 'candidate')
PROVIDERS = ('skillcorner', 'dfl', 'wcsf')
PROVIDER = {cid: provider for cid, provider, _ in MATCHES}
PRIMARY = tuple(cid for cid, _, role in MATCHES if role == 'fit-disjoint')
SECONDARY = tuple(cid for cid, _, role in MATCHES if role != 'fit-disjoint')
STOPPAGE_CASES = ('dfl-J03WR9', 'dfl-J03WN1', 'dfl-J03WOH', 'dfl-J03WOY', 'wcsf-used-match')
REGIME_CASES = {'natural': tuple(c for c, _, _ in MATCHES), 'noise': tuple(c for c, _, _ in MATCHES),
                'live-gap': tuple(c for c, _, _ in MATCHES), 'stoppage': STOPPAGE_CASES}
REGIME_WEIGHTS = {'natural': {'skillcorner': 1 / 3, 'dfl': 1 / 3, 'wcsf': 1 / 3},
                  'noise': {'skillcorner': 1 / 3, 'dfl': 1 / 3, 'wcsf': 1 / 3},
                  'live-gap': {'skillcorner': 1 / 3, 'dfl': 1 / 3, 'wcsf': 1 / 3},
                  'stoppage': {'dfl': .5, 'wcsf': .5}}


# ----- per-frame strata --------------------------------------------------------------------------

def interior_mask(gt, periods, margin=INTERIOR_MARGIN):
    gt = np.asarray(gt)
    periods = np.asarray(periods)
    n = len(gt)
    change = (gt[1:] != gt[:-1]) | (periods[1:] != periods[:-1])
    starts = np.r_[0, np.flatnonzero(change) + 1]
    stops = np.r_[starts[1:], n]
    mask = np.zeros(n, dtype=bool)
    for first, stop in zip(starts, stops):
        if stop - first > 2 * margin + 1:
            mask[first + margin + 1:stop - margin - 1] = True
    return mask & (np.asarray(gt) < 2) & (periods > 0)


def interior_accuracy(gt, pred, periods, observed):
    consider = interior_mask(gt, periods) & np.asarray(observed, dtype=bool)
    return dict(n=int(consider.sum()), correct=int((consider & (pred == gt)).sum()))


def _error_class(gt, pred, latent):
    if latent is not None and latent == 3:
        return 'carried_unsupported'
    if pred == 2:
        return 'false_D'
    return 'wrong_team'


def interior_transitions(gt, pred_control, pred_candidate, periods, observed, latent_control=None, latent_candidate=None):
    """Corrections and newly introduced errors on observed interior frames, by error class."""
    consider = np.flatnonzero(interior_mask(gt, periods) & np.asarray(observed, dtype=bool))
    names = ('wrong_team', 'false_D', 'carried_unsupported')
    corrections = {k: 0 for k in names}
    introduced = {k: 0 for k in names}
    for i in consider:
        before, after = pred_control[i] == gt[i], pred_candidate[i] == gt[i]
        if not before and after:
            corrections[_error_class(gt[i], pred_control[i], None if latent_control is None else latent_control[i])] += 1
        elif before and not after:
            introduced[_error_class(gt[i], pred_candidate[i], None if latent_candidate is None else latent_candidate[i])] += 1
    return dict(corrections=corrections, introduced=introduced, considered=int(len(consider)))


# ----- restart events ----------------------------------------------------------------------------

def restart_events(gt, periods):
    """Maximal reference-D runs with known H/A immediately before and after, in the same period.

    Period-opening D, D preceded by X, and terminal D are ungroupable: counted separately, never grouped.
    """
    gt = np.asarray(gt)
    periods = np.asarray(periods)
    n = len(gt)
    events, ungroupable = [], 0
    i = 0
    while i < n:
        if gt[i] != 2 or periods[i] == 0:
            i += 1
            continue
        first = i
        while i < n and gt[i] == 2 and periods[i] == periods[first]:
            i += 1
        stop = i
        before_ok = first > 0 and periods[first - 1] == periods[first] and gt[first - 1] < 2
        after_ok = stop < n and periods[stop] == periods[first] and gt[stop] < 2
        if before_ok and after_ok:
            events.append(dict(first=first, stop=stop, before=int(gt[first - 1]), after=int(gt[stop]),
                               kind='same' if gt[first - 1] == gt[stop] else 'changed'))
        else:
            ungroupable += 1
    return events, ungroupable


def restart_outcomes(gt, pred, periods):
    """Aggregate counts per same/changed subgroup.  Correct = post-D team holds strictly more than half
    of all predictions in the first 25 reference-live frames after D (ending at the next reference change)."""
    gt = np.asarray(gt)
    pred = np.asarray(pred)
    periods = np.asarray(periods)
    events, ungroupable = restart_events(gt, periods)
    out = {kind: dict(n=0, correct=0, first_frame_correct=0, recovered=0, recovered_correct=0, latency_sum=0)
           for kind in ('same', 'changed')}
    for event in events:
        team, start = event['after'], event['stop']
        length = 0
        while (length < RESTART_WINDOW and start + length < len(gt) and gt[start + length] == team
               and periods[start + length] == periods[start]):
            length += 1
        row = out[event['kind']]
        row['n'] += 1
        row['correct'] += int(2 * int((pred[start:start + length] == team).sum()) > length)
        row['first_frame_correct'] += int(pred[start] == team)
        limit = 0
        while (limit < RECOVERY_FRAMES and start + limit < len(gt) and gt[start + limit] == team
               and periods[start + limit] == periods[start]):
            limit += 1
        hit = next((k for k in range(limit) if pred[start + k] < 2), None)
        if hit is not None:
            row['recovered'] += 1
            row['recovered_correct'] += int(pred[start + hit] == team)
            row['latency_sum'] += hit
    return dict(events=out, eligible=len(events), ungroupable=ungroupable)


# ----- spell bins --------------------------------------------------------------------------------

def spell_bins(reference, prediction, periods):
    a, b = _evaluation(reference, prediction, periods)
    if not len(a):
        return {_bin_name(lo, hi): dict(n_gt=0, n_matched=0) for lo, hi in BINS}
    runs = official.valid_runs(a)
    filled = official.fill_abstentions(b, runs)
    actual = official.possession_spells(a, runs)
    estimated = official.possession_spells(filled, runs)
    flags = official.matched_gt_flags(official.spell_overlaps(actual, estimated), len(actual), .5)
    out = {}
    for lo, hi in BINS:
        chosen = [bool(flag) for (first, stop, _), flag in zip(actual, flags)
                  if stop - first >= lo and (hi is None or stop - first <= hi)]
        out[_bin_name(lo, hi)] = dict(n_gt=len(chosen), n_matched=sum(chosen))
    return out


def _bin_name(lo, hi):
    return f'{lo}-{hi}' if hi is not None else f'{lo}+'


# ----- one scored bundle -------------------------------------------------------------------------

def score_bundle(reference, final_codes, periods, observed, *, restart=False):
    gt, pred, period = _arrays(reference, final_codes, periods)
    seen = np.asarray(observed, dtype=bool)
    score = score_variant(reference, final_codes, periods, observed)
    extras = dict(interior=interior_accuracy(gt, pred, period, seen), spell_bins=spell_bins(reference, final_codes, periods))
    if restart:
        extras['restart'] = restart_outcomes(gt, pred, period)
    return dict(score=score, extras=extras)


def flatten(bundle):
    """The scalars the gates use."""
    score, extras = bundle['score'], bundle['extras']
    interior = extras['interior']
    flat = dict(spell_f1=score['metrics']['spell_f1_mean'], interior_n=interior['n'], interior_correct=interior['correct'],
                interior_acc=interior['correct'] / interior['n'] if interior['n'] else None,
                dead_precision=score['dead']['precision'], dead_recall=score['dead']['recall'],
                false_d=score['known_live_false_D_rate'], short_n_gt=score['short_spells']['n_gt'],
                short_matched=score['short_spells']['n_matched'], short_recall=score['short_spells']['recall'],
                pred_H=score['predicted_on_known']['H'], pred_A=score['predicted_on_known']['A'],
                sup_H=score['support']['H'], sup_A=score['support']['A'])
    if 'restart' in extras:
        flat['restart'] = extras['restart']['events']
    return flat


# ----- aggregation -------------------------------------------------------------------------------

def _num(value):
    if value is None:
        return None
    if type(value) not in (int, float) or not isfinite(value):
        raise ValueError('Invalid metric value')
    return float(value)


def provider_means(values, regime):
    """Mean per provider over primary cases present in the regime; None if any required value is None."""
    result = {}
    for provider in REGIME_WEIGHTS[regime]:
        group = [values.get(cid) for cid in REGIME_CASES[regime] if cid in PRIMARY and PROVIDER[cid] == provider]
        group = [_num(v) for v in group]
        if not group or any(v is None for v in group):
            result[provider] = None
        else:
            result[provider] = sum(group) / len(group)
    return result


def weighted(values, regime):
    means = provider_means(values, regime)
    if any(v is None for v in means.values()):
        return None, means
    return sum(REGIME_WEIGHTS[regime][p] * means[p] for p in means), means


def _pair(flats, regime, key):
    control = {cid: flats[cid]['control'][key] for cid in flats}
    candidate = {cid: flats[cid]['candidate'][key] for cid in flats}
    return control, candidate


def _diff(a, b):
    return None if a is None or b is None else a - b


def _at_least(value, bound):
    return value >= bound - ROUNDOFF


def _at_most(value, bound):
    return value <= bound + ROUNDOFF


def _above(value, bound):
    return value > bound + ROUNDOFF


def _status(values, non_applicable=0):
    failed = sum(v is False for v in values)
    unresolved = sum(v is None for v in values)
    assessed = len(values) - unresolved
    status = ('fail' if failed else 'unresolved' if unresolved else 'pass' if values else 'non_applicable')
    return dict(status=status, assessed=assessed, failures=failed, unresolved=unresolved, non_applicable=non_applicable)


def _primary(flats, regime):
    return {cid: flats[cid] for cid in REGIME_CASES[regime] if cid in PRIMARY}


def _require_regime(flats, regime):
    missing = [cid for cid in REGIME_CASES[regime] if cid not in flats]
    if missing or any(set(flats[cid]) != set(METHODS) for cid in flats):
        raise ValueError('Complete paired regime results required: ' + ','.join(missing))


# ----- gates -------------------------------------------------------------------------------------

def gate_natural_benefit(flats):
    _require_regime(flats, 'natural')
    primary = _primary(flats, 'natural')
    control, candidate = _pair(primary, 'natural', 'spell_f1')
    wc, mc = weighted(control, 'natural')
    wk, mk = weighted(candidate, 'natural')
    gain = _diff(wk, wc)
    provider_change = {p: _diff(mk[p], mc[p]) for p in PROVIDERS}
    acc_control, acc_candidate = _pair(primary, 'natural', 'interior_acc')
    ac, acc_c = weighted(acc_control, 'natural')
    ak, acc_k = weighted(acc_candidate, 'natural')
    acc_gain = _diff(ak, ac)
    checks = dict(
        spell_gain=dict(value=gain, threshold=GAIN_THRESHOLD, status=_status([None if gain is None else _at_least(gain, GAIN_THRESHOLD)])['status']),
        provider_nonregression=dict(value=provider_change, threshold=-EPS,
            status=_status([None if d is None else _at_least(d, -EPS) for d in provider_change.values()])['status']),
        interior_accuracy=dict(value=acc_gain, threshold=EPS, status=_status([None if acc_gain is None else _above(acc_gain, EPS)])['status'],
            per_provider={p: _diff(acc_k[p], acc_c[p]) for p in PROVIDERS}))
    return checks


def gate_loss(flats, regime):
    """Gate 2: provider-weighted primary loss (stress regimes) and per-match loss (every regime)."""
    _require_regime(flats, regime)
    primary = _primary(flats, regime)
    control, candidate = _pair(primary, regime, 'spell_f1')
    wc, _ = weighted(control, regime)
    wk, _ = weighted(candidate, regime)
    change = _diff(wk, wc)
    per_match = {cid: _diff(candidate[cid], control[cid]) for cid in primary}
    out = dict(match_loss=dict(value=per_match, threshold=-MATCH_LOSS,
                               **_status([None if d is None else _at_least(d, -MATCH_LOSS - EPS) for d in per_match.values()])))
    if regime != 'natural':
        out['primary_loss'] = dict(value=change, threshold=-STRESS_PRIMARY_LOSS,
                                   status=_status([None if change is None else _at_least(change, -STRESS_PRIMARY_LOSS - EPS)])['status'])
    return out


def gate_dead_and_owners(flats, regime):
    """Gate 3: D precision/recall (DFL, WCSF), false-D rise (all), owner presence (all), per primary match."""
    _require_regime(flats, regime)
    primary = _primary(flats, regime)
    precision, recall, false_d, owners = [], [], [], []
    for cid, row in primary.items():
        c, k = row['control'], row['candidate']
        if PROVIDER[cid] != 'skillcorner':
            for key, sink in (('dead_precision', precision), ('dead_recall', recall)):
                d = _diff(_num(k[key]), _num(c[key]))
                sink.append(None if d is None else _at_least(d, -DEAD_LOSS - EPS))
        d = _diff(_num(k['false_d']), _num(c['false_d']))
        false_d.append(None if d is None else _at_most(d, FALSE_D_RISE + EPS))
        for side in 'HA':
            if c['sup_' + side]:
                owners.append(k['pred_' + side] > 0)
    return dict(dead_precision=_status(precision), dead_recall=_status(recall), false_d=_status(false_d),
                owner_presence=_status(owners))


def gate_short_spells(flats, regime):
    _require_regime(flats, regime)
    values, na = [], 0
    for cid, row in _primary(flats, regime).items():
        c, k = row['control'], row['candidate']
        if c['short_n_gt'] != k['short_n_gt']:
            raise ValueError('Reference short-spell support changed')
        n = c['short_n_gt']
        if n == 0:
            na += 1
        elif n < SHORT_SUPPORT:
            values.append(k['short_matched'] >= c['short_matched'])
        else:
            d = _diff(_num(k['short_recall']), _num(c['short_recall']))
            values.append(None if d is None else _at_least(d, -SHORT_RECALL_LOSS - EPS))
    return _status(values, na)


def gate_noise_mechanism(flats):
    _require_regime(flats, 'noise')
    control, candidate = _pair(_primary(flats, 'noise'), 'noise', 'interior_acc')
    wc, _ = weighted(control, 'noise')
    wk, _ = weighted(candidate, 'noise')
    d = _diff(wk, wc)
    return dict(value=d, threshold=-EPS, status=_status([None if d is None else _at_least(d, -EPS)])['status'])


def gate_support_and_restart(flats, live_windows, restart_eligible):
    """Gate 6.  ``live_windows``: provider -> selected windows (pooled primary cases).  ``restart_eligible``:
    provider -> eligible reference events (pooled; DFL = WR9+WN1, WCSF).  Stoppage ``flats`` carry restart counts."""
    problems = []
    windows = {p: live_windows.get(p) for p in PROVIDERS}
    for p, n in windows.items():
        if n is None or n < MIN_LIVE_WINDOWS:
            problems.append('live-gap windows for ' + p)
    events = {p: restart_eligible.get(p) for p in ('dfl', 'wcsf')}
    for p, n in events.items():
        if n is None or n < MIN_RESTART_EVENTS:
            problems.append('restart events for ' + p)
    groups, checks = {}, []
    if flats is not None:
        _require_regime(flats, 'stoppage')
        for provider in ('dfl', 'wcsf'):
            for kind in ('same', 'changed'):
                totals = {m: dict(n=0, correct=0) for m in METHODS}
                for cid in REGIME_CASES['stoppage']:
                    if cid in PRIMARY and PROVIDER[cid] == provider:
                        for m in METHODS:
                            row = flats[cid][m]['restart'][kind]
                            totals[m]['n'] += row['n']
                            totals[m]['correct'] += row['correct']
                if totals['control']['n'] != totals['candidate']['n']:
                    raise ValueError('Restart event support differs between methods')
                supported = totals['control']['n'] > 0
                ok = totals['candidate']['correct'] >= totals['control']['correct'] if supported else None
                groups[provider + '/' + kind] = dict(n=totals['control']['n'], control_correct=totals['control']['correct'],
                                                     candidate_correct=totals['candidate']['correct'],
                                                     status='unsupported' if not supported else 'pass' if ok else 'fail')
                if supported:
                    checks.append(ok)
    status = ('blocked' if problems else 'fail' if any(v is False for v in checks) else 'pass')
    return dict(status=status, problems='; '.join(problems), live_windows=windows, restart_events=events, subgroups=groups)


# ----- verdict -----------------------------------------------------------------------------------

def _leaves(label, result):
    """Yield (label, status) for every check; a check is a dict with a string ``status``."""
    if isinstance(result.get('status'), str):
        yield label, result['status']
        return
    for key, child in result.items():
        if isinstance(child, dict):
            yield from _leaves(label + '/' + key, child)


def verdict(named_gates):
    """PASS only if every check passes (non_applicable is stated, not a failure); otherwise FAIL naming each."""
    statuses = [leaf for label, result in named_gates.items() for leaf in _leaves(label, result)]
    failing = sorted(name for name, status in statuses if status not in ('pass', 'non_applicable'))
    return dict(verdict='FAIL' if failing or not statuses else 'PASS', failing=failing, assessed=len(statuses))
