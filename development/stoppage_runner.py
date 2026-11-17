"""Run the challenge-like stoppage test: 5 matches x 5 regimes x 3 variants, once. Aggregates only.

    python stoppage_runner.py
"""
import json
from math import fsum
from pathlib import Path

import gap_liveness_experiment as gap
import memory_ablation_protocol as protocol
from gap_liveness import apply_gap_rule, long_gaps
from gap_solver.temporal import mask_motion_frames
from memory_ablation_run import load_evaluation
from observed_touch import detect_observed_touches, observed_evidence_rows, predict_observed_touch
from release_runtime import predict_selected
from stoppage_regime import REGIMES, make_mask
from touch_evidence import prepare_evidence
from touch_experiment import add_jitter, score

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'reports/stoppage-regime/results.json'
PROXY = ROOT / 'reports/tag-ownership/proxy-accuracy.json'
MATCH_IDS = (('dfl-J03WN1', 'dfl', 'fit-disjoint'), ('dfl-J03WR9', 'dfl', 'fit-disjoint'), ('wcsf-used-match', 'wcsf', 'fit-disjoint'),
             ('dfl-J03WOH', 'dfl', 'fitting-overlap'), ('dfl-J03WOY', 'dfl', 'fitting-overlap'))
THETA, BETA, C_TOUCH = 3, 2, 8


def variant_labels(frames, events=None):
    control = predict_selected(frames).labels
    candidate = apply_gap_rule(frames, control)
    detected = detect_observed_touches(frames, THETA) if events is None else events
    touch = predict_observed_touch(frames, THETA, BETA, C_TOUCH, events=detected)
    touch_candidate = apply_gap_rule(frames, touch.labels)
    return {'control': control, 'candidate': candidate.labels, 'candidate+touch': touch_candidate.labels,
            '_candidate_application': candidate, '_touch_application': touch_candidate, '_events': detected}


def bonus_share(frames, events):
    base, _, periods, usable, _ = prepare_evidence(frames, [], 0, 32)
    observed = [f.ball_observed for f in frames]
    rows, _ = observed_evidence_rows(base, periods, usable, observed, events, BETA, C_TOUCH)
    graded = [i for i, p in enumerate(periods) if p in (1, 2)]
    changed = sum(1 for i in graded if observed[i] and tuple(rows[i]) != tuple(base[i]))
    return changed / len(graded)


def overlaps(gap_range, blocks):
    return any(a < gap_range[1] and gap_range[0] < b for a, b in blocks)


def origin(gap_range, info):
    if overlaps(gap_range, info['dead_blocks']):
        return 'dead'
    if overlaps(gap_range, info['live_blocks']):
        return 'live'
    return 'other'


def gap_counts(frames, application, info):
    gaps = long_gaps(frames)
    chosen = set(application.stoppage_gaps)
    out = {k: dict(long=0, relabelled=0) for k in ('dead', 'live', 'other')}
    for g in gaps:
        o = origin(g, info)
        out[o]['long'] += 1
        out[o]['relabelled'] += g in chosen
    return dict(long_gaps=len(gaps), stoppage_gaps=len(chosen), by_origin=out)


def summary(result):
    return dict(spell_f1=result['metrics']['spell_f1_mean'], macro_f1=result['metrics']['official_macro_f1'],
                accuracy=result['metrics']['accuracy'], dead_recall=result['dead']['recall'],
                n_pred=result['spells']['n_pred'], n_gt=result['spells']['n_gt'])


def primary(values):
    """values {match_id: number}: mean of (mean of the two primary DFL matches) and (the WCSF match)."""
    dfl = fsum(values[m] for m in ('dfl-J03WN1', 'dfl-J03WR9')) / 2
    return (dfl + values['wcsf-used-match']) / 2


def main():
    if OUT.exists():
        raise FileExistsError('The stoppage run was already performed')
    from memory_ablation_metrics import MATCHES
    listed = {c: (p, r) for c, p, r in MATCHES}
    for cid, provider, role in MATCH_IDS:
        if listed.get(cid) != (provider, role):
            raise ValueError('Match id or role differs from MATCHES: ' + cid)
    proxy = json.loads(PROXY.read_text(encoding='utf-8'))
    bindings = protocol.input_bindings(ROOT)['evaluation']
    for cid, b in bindings.items():
        gap.check_input(b, b['expected'])
    results = {}
    for cid, provider, role in MATCH_IDS:
        case = load_evaluation(cid, bindings[cid])
        frames, reference = case['frames'], case['reference']()
        periods = [f.period for f in frames]
        results[cid] = dict(provider=provider, role=role, regimes={})
        for regime in REGIMES:
            mask, info = make_mask(cid, reference, periods, regime)
            work = mask_motion_frames(frames, mask) if any(mask) else frames
            if REGIMES[regime][2]:
                work = add_jitter(work)
            labels = variant_labels(work)
            graded = [i for i, p in enumerate(periods) if p in (1, 2)]
            row = dict(removed_share=sum(mask[i] for i in graded) / len(graded),
                       missing_share=sum(not work[i].ball_observed for i in graded) / len(graded),
                       dead_blocks=len(info['dead_blocks']), live_blocks=len(info['live_blocks']),
                       gap_rule=gap_counts(work, labels['_candidate_application'], info),
                       touches_detected=len(labels['_events']), bonus_share=bonus_share(work, labels['_events']), variants={})
            for name in ('control', 'candidate', 'candidate+touch'):
                row['variants'][name] = summary(score(reference, labels[name], work))
            results[cid]['regimes'][regime] = row
            print(json.dumps(dict(case=cid, regime=regime)), flush=True)
            if regime == 'natural':
                stored = proxy['matches'][cid]['control']['spell_f1']
                if abs(row['variants']['control']['spell_f1'] - stored) > 1e-9:
                    raise ValueError('Control natural reproduction differs for ' + cid)
    report = {}
    for regime in REGIMES:
        entry = {}
        for metric in ('spell_f1', 'macro_f1', 'dead_recall'):
            entry[metric] = {v: primary({c: results[c]['regimes'][regime]['variants'][v][metric] for c, _, _ in MATCH_IDS})
                             for v in ('control', 'candidate', 'candidate+touch')}
        f1 = entry['spell_f1']
        entry['delta_candidate_minus_control'] = f1['candidate'] - f1['control']
        entry['delta_touch_minus_candidate'] = f1['candidate+touch'] - f1['candidate']
        entry['per_match_delta_touch_minus_candidate'] = {c: results[c]['regimes'][regime]['variants']['candidate+touch']['spell_f1']
                                                           - results[c]['regimes'][regime]['variants']['candidate']['spell_f1'] for c, _, _ in MATCH_IDS}
        report[regime] = entry
    s75, sj, nat = report['stop75'], report['stop75-jitter'], report['natural']
    stop_71 = s75['delta_candidate_minus_control'] < -.005
    conditions = {
        'touch_gain_stop75_ge_004': s75['delta_touch_minus_candidate'] >= .04,
        'touch_gain_jitter_ge_0': sj['delta_touch_minus_candidate'] >= 0,
        'touch_natural_ge_minus_0005': nat['delta_touch_minus_candidate'] >= -.005,
        'dead_recall_within_002': s75['dead_recall']['candidate+touch'] >= s75['dead_recall']['candidate'] - .02,
        'no_primary_match_loses_002': all(s75['per_match_delta_touch_minus_candidate'][c] >= -.02
                                          for c in ('dfl-J03WN1', 'dfl-J03WR9', 'wcsf-used-match'))}
    decision = dict(stop_7_1=stop_71, conditions_7_2=conditions, touch_replaces_candidate=bool(not stop_71 and all(conditions.values())))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open('x', encoding='utf-8') as handle:
        json.dump(dict(matches=results, primary=report, decision=decision, scoring_calls=75), handle, sort_keys=True, indent=1)
        handle.write('\n')
    print(json.dumps(dict(primary=report, decision=decision), sort_keys=True, indent=1))


if __name__ == '__main__':
    main()
