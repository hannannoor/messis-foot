"""Live/dead sequence experiment: three-stream aggregation, fixed gates, support floors and the verdict.

Flats are ``{case_id: {stream: flat}}`` with the scalars of ``recent_geometry_metrics.flatten``.  Every comparison is
temporal against release except ``temporal_over_instant``.  Only the 13 fitting-disjoint primary cases enter gates;
the provider weight is 1/3 each with equal match weight within a provider.  A missing value is unresolved, never a
pass.  Interior team accuracy is reported and never required.
"""
from math import isfinite

from live_dead_protocol import PRIMARY, PROVIDERS, provider_of

STREAMS = ('release', 'instant', 'temporal')
EPS = 1e-6
ROUNDOFF = 1e-12
GAIN = .010
CASE_LOSS = .020
WCSF_RECALL_RISE = .030
DEAD_LOSS = .010
FALSE_D_RISE = .005
SHORT_SUPPORT = 20
SHORT_RECALL_LOSS = .020
STRESS_PRIMARY_LOSS = .005
MIN_INTEGRATION, MIN_SHARE, MIN_LIVE, MIN_D = 1000, .10, 125, 125
WCSF = 'wcsf-used-match'


def _num(value):
    if value is None:
        return None
    if type(value) not in (int, float) or not isfinite(value):
        raise ValueError('Invalid metric value')
    return float(value)


def _diff(a, b):
    a, b = _num(a), _num(b)
    return None if a is None or b is None else a - b


def _at_least(value, bound):
    return None if value is None else value >= bound - ROUNDOFF


def _at_most(value, bound):
    return None if value is None else value <= bound + ROUNDOFF


def _above(value, bound):
    return None if value is None else value > bound + ROUNDOFF


def _status(results, value=None, threshold=None, non_applicable=0):
    results = list(results)
    failed = sum(r is False for r in results)
    unresolved = sum(r is None for r in results)
    status = 'fail' if failed else 'unresolved' if unresolved else 'pass' if results else 'non_applicable'
    out = dict(status=status, assessed=len(results) - unresolved, failures=failed, unresolved=unresolved,
               non_applicable=non_applicable)
    if value is not None or threshold is not None:
        out.update(value=value, threshold=threshold)
    return out


def _primary(flats):
    missing = [cid for cid in PRIMARY if cid not in flats or set(flats[cid]) != set(STREAMS)]
    if missing:
        raise ValueError('Complete three-stream results required: ' + ','.join(missing))
    return {cid: flats[cid] for cid in PRIMARY}


def weighted(values):
    means = {}
    for provider in PROVIDERS:
        group = [_num(values.get(cid)) for cid in PRIMARY if provider_of(cid) == provider]
        means[provider] = None if not group or any(v is None for v in group) else sum(group) / len(group)
    if any(v is None for v in means.values()):
        return None, means
    return sum(means[p] for p in PROVIDERS) / len(PROVIDERS), means


def _stream(primary, stream, key):
    return {cid: row[stream][key] for cid, row in primary.items()}


def _harm_checks(primary):
    precision, recall, false_d, owners, short, short_na = [], [], [], [], [], 0
    for cid, row in primary.items():
        c, k = row['release'], row['temporal']
        if provider_of(cid) != 'skillcorner':
            precision.append(_at_least(_diff(k['dead_precision'], c['dead_precision']), -DEAD_LOSS - EPS))
            recall.append(_at_least(_diff(k['dead_recall'], c['dead_recall']), -DEAD_LOSS - EPS))
        false_d.append(_at_most(_diff(k['false_d'], c['false_d']), FALSE_D_RISE + EPS))
        for side in 'HA':
            if c['sup_' + side]:
                owners.append(k['pred_' + side] > 0)
        if c['short_n_gt'] != k['short_n_gt']:
            raise ValueError('Reference short-spell support changed')
        n = c['short_n_gt']
        if n == 0:
            short_na += 1
        elif n < SHORT_SUPPORT:
            short.append(k['short_matched'] >= c['short_matched'])
        else:
            short.append(_at_least(_diff(k['short_recall'], c['short_recall']), -SHORT_RECALL_LOSS - EPS))
    return dict(dead_precision=_status(precision, threshold=-DEAD_LOSS - EPS),
                dead_recall=_status(recall, threshold=-DEAD_LOSS - EPS),
                false_d=_status(false_d, threshold=FALSE_D_RISE + EPS), owner_presence=_status(owners),
                short_spells=_status(short, non_applicable=short_na))


def _case_loss(primary):
    per_case = {cid: _diff(row['temporal']['spell_f1'], row['release']['spell_f1']) for cid, row in primary.items()}
    return _status([_at_least(d, -CASE_LOSS - EPS) for d in per_case.values()], per_case, -CASE_LOSS - EPS)


def gate_natural(flats):
    primary = _primary(flats)
    release, release_p = weighted(_stream(primary, 'release', 'spell_f1'))
    temporal, temporal_p = weighted(_stream(primary, 'temporal', 'spell_f1'))
    instant, _ = weighted(_stream(primary, 'instant', 'spell_f1'))
    gain = _diff(temporal, release)
    providers = {p: _diff(temporal_p[p], release_p[p]) for p in PROVIDERS}
    over_instant = _diff(temporal, instant)
    wcsf = _diff(primary[WCSF]['temporal']['dead_recall'], primary[WCSF]['release']['dead_recall'])
    interior = {s: weighted(_stream(primary, s, 'interior_acc'))[0] for s in STREAMS}
    return dict(spell_gain=_status([_at_least(gain, GAIN)], gain, GAIN),
                provider_nonregression=_status([_at_least(d, -EPS) for d in providers.values()], providers, -EPS),
                case_loss=_case_loss(primary),
                temporal_over_instant=_status([_above(over_instant, EPS)], over_instant, EPS),
                wcsf_dead_recall_rise=_status([_at_least(wcsf, WCSF_RECALL_RISE)], wcsf, WCSF_RECALL_RISE),
                **_harm_checks(primary),
                primary_spell_f1=dict(status='reported', release=release, instant=instant, temporal=temporal,
                                      providers=dict(release=release_p, temporal=temporal_p)),
                interior_accuracy=dict(status='reported', **interior))


def gate_stress(flats):
    primary = _primary(flats)
    release, _ = weighted(_stream(primary, 'release', 'spell_f1'))
    temporal, _ = weighted(_stream(primary, 'temporal', 'spell_f1'))
    instant, _ = weighted(_stream(primary, 'instant', 'spell_f1'))
    change = _diff(temporal, release)
    return dict(primary_loss=_status([_at_least(change, -STRESS_PRIMARY_LOSS - EPS)], change, -STRESS_PRIMARY_LOSS - EPS),
                case_loss=_case_loss(primary), **_harm_checks(primary),
                primary_spell_f1=dict(status='reported', release=release, instant=instant, temporal=temporal))


def coverage_floors(case_counts):
    problems = []
    for cid in PRIMARY:
        c = case_counts.get(cid)
        if not c or not c.get('denominator'):
            problems.append(f'{cid}: missing or zero denominator')
            continue
        if c['integration'] < MIN_INTEGRATION:
            problems.append(f"{cid}: integration-eligible rows {c['integration']} < {MIN_INTEGRATION}")
        if c['integration'] < MIN_SHARE * c['denominator'] - ROUNDOFF:
            problems.append(f"{cid}: integration share {c['integration']}/{c['denominator']} < 10%")
        if c['known_live'] < MIN_LIVE:
            problems.append(f"{cid}: known-live rows {c['known_live']} < {MIN_LIVE}")
        if provider_of(cid) != 'skillcorner' and c['known_d'] < MIN_D:
            problems.append(f"{cid}: known-D rows {c['known_d']} < {MIN_D}")
    return problems


def _statuses(gates):
    for checks in gates.values():
        for check in checks.values():
            if check['status'] != 'reported':
                yield check['status']


def verdict(gates, problems):
    statuses = list(_statuses(gates))
    if problems or 'unresolved' in statuses:
        return 'UNRESOLVED'
    if 'fail' in statuses:
        return 'NO_ADVANCEMENT'
    return 'PASS'
