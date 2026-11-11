"""Fixed touch-transfer and stoppage-restart evaluation. External references only."""
import json
from math import fsum
from pathlib import Path

from gap_liveness import apply_gap_rule
from gap_solver.materialization_control import materialize_abstentions
from gap_solver.temporal import mask_motion_frames
from observed_touch import detect_observed_touches, observed_evidence_rows
from release_runtime import predict_selected
from stoppage_regime import h, make_mask
from touch_decoder import decode_variable
from touch_evidence import prepare_evidence

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'reports/touch-transfer/results.json'
VARIANTS = ('control', 'candidate', 'candidate+touch', 'candidate+touch-thin', 'candidate+reset', 'candidate+touch+reset')
SC_CONFIRM = tuple('skillcorner-'+x for x in ('1886347', '2007721', '2011166', '2015213', '2017461'))
SC_DEV = tuple('skillcorner-'+x for x in ('1874553', '2007448', '2010085', '2013725', '2016236'))
PRIMARY = ('dfl-J03WN1', 'dfl-J03WR9', 'wcsf-used-match')


def validate_matches():
    from memory_ablation_metrics import MATCHES
    from touch_experiment import split_matches
    expected = {(c, 'skillcorner', 'fit-disjoint') for c in SC_CONFIRM+SC_DEV}
    expected |= {(c, 'dfl' if c.startswith('dfl') else 'wcsf', 'fit-disjoint') for c in PRIMARY}
    expected |= {(c, 'dfl', 'fitting-overlap') for c in ('dfl-J03WOH', 'dfl-J03WOY')}
    dev, confirmation = split_matches()
    if len(MATCHES) != 15 or set(MATCHES) != expected or set(dev) != set(SC_DEV+('dfl-J03WN1',)) or set(confirmation) != set(SC_CONFIRM+('dfl-J03WR9', 'wcsf-used-match')):
        raise ValueError('MATCHES or split differs from the brief')


def thin_events(match_id, events, observed_minutes, rate):
    owned = sum(e.team in ('H', 'A') for e in events)
    target = round(rate * observed_minutes)
    if owned <= target:
        return events
    keep = round(10000 * target / owned)
    return [e for e in events if h(f'{match_id}:thin:{e.frame_index}') % 10000 < keep]


def regime_frames(match_id, frames, reference):
    from touch_experiment import add_jitter
    mask, info = make_mask(match_id, reference, [f.period for f in frames], 'stop75')
    work = mask_motion_frames(frames, mask) if any(mask) else frames
    return add_jitter(work), info


def restart_decode(frames, rows, periods, usable, costs, labels):
    first = apply_gap_rule(frames, labels)
    usable2 = list(usable)
    for a, b in first.stoppage_gaps:
        usable2[a:b] = [False] * (b-a)
    latent = decode_variable(rows, periods, usable2, costs)
    return apply_gap_rule(frames, materialize_abstentions(latent, periods)), usable2


def decode_touch_rows(frames, prepared, events):
    base, _, periods, usable, _ = prepared
    rows, costs = observed_evidence_rows(base, periods, usable, [f.ball_observed for f in frames], events, 2, 8)
    labels = tuple(materialize_abstentions(decode_variable(rows, periods, usable, costs), periods))
    bonus = sum(p in (1, 2) and a != b for p, a, b in zip(periods, base, rows))
    return rows, costs, labels, bonus


def variant_labels(match_id, frames, rate):
    control = predict_selected(frames).labels
    events = detect_observed_touches(frames, 3)
    minutes = sum(f.period in (1, 2) and f.ball_observed for f in frames) / 1500
    thinned = thin_events(match_id, events, minutes, rate)
    prepared = prepare_evidence(frames, [], 0, 32)
    rows, costs, periods, usable, _ = prepared
    touch_rows, touch_costs, touch, bonus = decode_touch_rows(frames, prepared, events)
    _, _, thin, thin_bonus = decode_touch_rows(frames, prepared, thinned)
    parity = tuple(materialize_abstentions(decode_variable(rows, periods, usable, costs), periods))
    if parity != tuple(control):
        raise ValueError('Uniform-cost variable decoder differs from control')
    reset, _ = restart_decode(frames, rows, periods, usable, costs, control)
    touch_reset, _ = restart_decode(frames, touch_rows, periods, usable, touch_costs, touch)
    return dict(zip(VARIANTS, (control, apply_gap_rule(frames, control).labels,
                              apply_gap_rule(frames, touch).labels, apply_gap_rule(frames, thin).labels,
                              reset.labels, touch_reset.labels)), _events=events, _thinned=thinned,
                _bonus=bonus, _thin_bonus=thin_bonus)


def restart_agreement(reference, labels, periods, selected_starts):
    """First H/A owner after each selected reference long-dead run, within its period.

    Skip subsequent D/X separately in prediction and reference; include a run
    only when the reference has a later owner. No later predicted owner is wrong.
    """
    total = matched = 0
    for first in selected_starts:
        stop = first
        while stop < len(reference) and periods[stop] == periods[first] and reference[stop] == 2:
            stop += 1
        end = stop
        while end < len(reference) and periods[end] == periods[first]:
            end += 1
        actual = next((reference[i] for i in range(stop, end) if reference[i] in (0, 1)), None)
        if actual is None:
            continue
        predicted = next((labels[i] for i in range(stop, end) if labels[i] in ('H', 'A')), None)
        total += 1
        matched += predicted == 'HA'[int(actual)]
    return dict(matched=matched, total=total, share=matched / total if total else None)


def summary(result):
    return dict(spell_f1=result['metrics']['spell_f1_mean'], macro_f1=result['metrics']['official_macro_f1'],
                dead_recall=result['dead']['recall'], n_pred=result['spells']['n_pred'], n_gt=result['spells']['n_gt'])


def owner_agreement_means(matches, ids, weights):
    variants = ('candidate+reset', 'candidate+touch+reset')
    if not all('owner_agreement_without' in matches[c]['resets'][v] for c in ids for v in variants):
        return None
    return {v: {key: fsum(matches[c]['resets'][v]['owner_agreement_'+field]['share']*w for c, w in zip(ids, weights))
                if all(matches[c]['resets'][v]['owner_agreement_'+field]['share'] is not None for c in ids) else None
                for key, field in (('without', 'without'), ('with', 'with'))} for v in variants}


def means(matches, ids, weights=None):
    weights = weights or [1/len(ids)] * len(ids)
    out = {}
    for metric in ('spell_f1', 'macro_f1', 'dead_recall', 'n_pred', 'n_gt'):
        out[metric] = {v: fsum(matches[c]['variants'][v][metric]*w for c, w in zip(ids, weights))
                      if all(matches[c]['variants'][v][metric] is not None for c in ids) else None for v in VARIANTS}
    f = out['spell_f1']
    out['delta_touch_minus_candidate'] = f['candidate+touch']-f['candidate']
    out['delta_thin_minus_candidate'] = f['candidate+touch-thin']-f['candidate']
    out['delta_reset_minus_candidate'] = f['candidate+reset']-f['candidate']
    out['delta_touch_reset_minus_touch'] = f['candidate+touch+reset']-f['candidate+touch']
    for key in ('owned_touch_rate', 'thinned_owned_touch_rate', 'bonus_share', 'thinned_bonus_share'):
        out[key] = fsum(matches[c][key]*w for c, w in zip(ids, weights))
    out['reset_changed_share'] = {v: fsum(matches[c]['resets'][v]['graded_changed_share']*w for c, w in zip(ids, weights))
                                  for v in ('candidate+reset', 'candidate+touch+reset')}
    out['restart_owner_agreement'] = owner_agreement_means(matches, ids, weights)
    return out


def main():
    from memory_ablation_metrics import MATCHES
    from memory_ablation_run import load_evaluation
    import memory_ablation_protocol as protocol
    import gap_liveness_experiment as gap
    from touch_experiment import score
    from tracking_profile import OUT as PROFILE
    validate_matches()
    if OUT.exists():
        raise FileExistsError('The single evaluation run already exists')
    profile = json.loads(PROFILE.read_text(encoding='utf-8'))
    if not all(profile['checks'].values()):
        raise ValueError('Profile gates failed')
    # A simple exclusive marker prevents an interrupted run from silently restarting.
    marker = OUT.with_suffix('.started')
    with marker.open('x', encoding='utf-8') as handle:
        handle.write('Single fixed run started; any retry needs a demonstrated code defect.\n')
    rate = profile['provided']['owned_touch_rate']
    proxy = json.loads((ROOT/'reports/tag-ownership/proxy-accuracy.json').read_text(encoding='utf-8'))
    prior = json.loads((ROOT/'reports/stoppage-regime/results.json').read_text(encoding='utf-8'))
    bindings = protocol.input_bindings(ROOT)['evaluation']
    results, checks, calls = {}, {}, 0
    for cid, provider, role in MATCHES:
        gap.check_input(bindings[cid], bindings[cid]['expected'])
        case = load_evaluation(cid, bindings[cid])
        natural, reference = case['frames'], case['reference']()
        # Natural controls are mandatory reproduction checks, five additional scores.
        natural_control = predict_selected(natural).labels
        natural_score = summary(score(reference, natural_control, natural))
        calls += 1
        difference = natural_score['spell_f1'] - proxy['matches'][cid]['control']['spell_f1']
        checks[cid] = dict(natural_control_difference=difference)
        if abs(difference) > 1e-9:
            raise ValueError('Natural reproduction differs: '+cid)
        work, info = (natural, None) if provider == 'skillcorner' else regime_frames(cid, natural, reference)
        labels = variant_labels(cid, work, rate)
        row = dict(provider=provider, role=role, regime='natural' if info is None else 'stop75-jitter', variants={}, resets={})
        for name in VARIANTS:
            if name == 'control' and info is None:
                value = natural_score
            else:
                value = summary(score(reference, labels[name], work))
                calls += 1
            if provider == 'skillcorner':
                value['dead_recall'] = None
            row['variants'][name] = value
            if info is not None and name in VARIANTS[:3]:
                difference = value['spell_f1'] - prior['matches'][cid]['regimes']['stop75-jitter']['variants'][name]['spell_f1']
                checks[cid][name+'_regime_difference'] = difference
                if abs(difference) > 1e-9:
                    raise ValueError('Regime reproduction differs: '+cid+' '+name)
        minutes = profile['matches'][cid][row['regime']]['observed_minutes']
        events, thinned = labels['_events'], labels['_thinned']
        graded = [i for i, f in enumerate(work) if f.period in (1, 2)]
        row.update(owned_touch_rate=sum(e.team in ('H', 'A') for e in events)/minutes,
                   thinned_owned_touch_rate=sum(e.team in ('H', 'A') for e in thinned)/minutes,
                   bonus_share=labels['_bonus']/len(graded),
                   thinned_bonus_share=labels['_thin_bonus']/len(graded))
        if info is not None:
            row['median_surprise_mps'] = profile['matches'][cid]['stop75-jitter']['median_surprise_mps']
        for name, base in (('candidate+reset', 'candidate'), ('candidate+touch+reset', 'candidate+touch')):
            reset = dict(delta_spell_f1=row['variants'][name]['spell_f1']-row['variants'][base]['spell_f1'],
                         graded_changed_share=sum(labels[name][i] != labels[base][i] for i in graded)/len(graded))
            if info is not None:
                reset['owner_agreement_without'] = restart_agreement(reference, labels[base], [f.period for f in work], info['selected_starts'])
                reset['owner_agreement_with'] = restart_agreement(reference, labels[name], [f.period for f in work], info['selected_starts'])
            row['resets'][name] = reset
        row['delta_touch_minus_candidate'] = row['variants']['candidate+touch']['spell_f1']-row['variants']['candidate']['spell_f1']
        row['delta_thin_minus_candidate'] = row['variants']['candidate+touch-thin']['spell_f1']-row['variants']['candidate']['spell_f1']
        results[cid] = row
        # Incremental bounded receipt preserves completed work without allowing retries.
        with OUT.open('w', encoding='utf-8') as handle:
            json.dump(dict(status='running', matches=results, reproduction=checks, scoring_calls=calls), handle, sort_keys=True, indent=1, allow_nan=False)
            handle.write('\n')
        print(json.dumps(dict(case_complete=cid, scoring_calls=calls)), flush=True)
    aggregates = dict(skillcorner_confirmation=means(results, SC_CONFIRM), skillcorner_development=means(results, SC_DEV),
                      dfl_wcsf_primary=means(results, PRIMARY, [.25, .25, .5]))
    with OUT.open('w', encoding='utf-8') as handle:
        json.dump(dict(status='complete', matches=results, means=aggregates, reproduction=checks,
                       scoring_calls=calls, variant_scores=90, extra_natural_reproduction_scores=5), handle, sort_keys=True, indent=1, allow_nan=False)
        handle.write('\n')
    print(json.dumps(dict(status='complete', scoring_calls=calls, variant_scores=90)), flush=True)


if __name__ == '__main__':
    main()
