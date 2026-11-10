"""External runs 6.1 and 6.2 for tag evidence; aggregates only. Each stage runs once.

    python tag_external_experiment.py control     # 6.1
    python tag_external_experiment.py simulate    # 6.2 (refuses unless 6.1 passed)
"""
import argparse
from collections import defaultdict
import hashlib
import json
from math import fsum
from pathlib import Path
import pickle

import gap_liveness_experiment as gap
import memory_ablation_protocol as protocol
import tag_evidence as te
import tag_release as tr
from memory_ablation_metrics import MATCHES
from memory_ablation_run import load_evaluation
from touch_experiment import score

ROOT = Path(__file__).resolve().parent
PUBLIC = ROOT / 'reports/tag-ownership'
PRIVATE = ROOT.parent / 'tag-ownership-private'
WINDOW = 440
SHARE = 42
LEVELS = (.9, .7)
PROVIDERS = ('skillcorner', 'dfl', 'wcsf')


def write_new(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as handle:
        json.dump(value, handle, sort_keys=True, indent=1)
        handle.write('\n')


def key_number(text):
    return int(hashlib.sha256(text.encode()).hexdigest(), 16)


def bindings():
    result = protocol.input_bindings(ROOT)['evaluation']
    for cid, b in result.items():
        gap.check_input(b, b['expected'])
    return result


def primary_means(values):
    """values: {cid: number}. Equal weight per match within a provider, equal weight per provider (13 fitting-disjoint)."""
    groups = defaultdict(list)
    for cid, cohort, role in MATCHES:
        if role == 'fit-disjoint':
            groups[cohort].append(values[cid])
    providers = {p: fsum(groups[p]) / len(groups[p]) for p in PROVIDERS}
    return providers, fsum(providers.values()) / len(providers)


def summary(result):
    return dict(spell_f1=result['metrics']['spell_f1_mean'], macro_f1=result['metrics']['official_macro_f1'],
                accuracy=result['metrics']['accuracy'], n_pred=result['spells']['n_pred'], n_gt=result['spells']['n_gt'])


def control_stage():
    if (PUBLIC / 'proxy-accuracy.json').exists():
        raise FileExistsError('Run 6.1 already performed')
    binds = bindings()
    PRIVATE.mkdir(parents=True, exist_ok=True)
    rows_out, score_calls = {}, 0
    for cid, cohort, role in MATCHES:
        case = load_evaluation(cid, binds[cid])
        frames = case['frames']
        parts = tr.control_parts(frames)
        _, rows, effective, labels, periods, observed = parts
        stored = json.loads((ROOT / 'reports/gap-liveness/control' / (cid + '-natural.json')).read_text(encoding='utf-8'))
        if gap.hashlib.sha256(''.join(labels).encode('ascii')).hexdigest() != stored['labels_sha256']:
            raise ValueError('Rebuilt control differs from the stored control: ' + cid)
        reference = case['reference']()
        result = score(reference, labels, frames)
        score_calls += 1
        pairs = te.margins(labels, rows, observed, periods)
        ordered = sorted(m for _, m in pairs)
        threshold = ordered[(3 * len(ordered) + 3) // 4 - 1]
        confident = [i for i, m in pairs if m >= threshold and reference[i] < 3]
        correct = sum('HA'.index(labels[i]) == reference[i] for i in confident)
        rows_out[cid] = dict(provider=cohort, role=role, control=summary(result), confident_known=len(confident),
                             confident_accuracy=correct / len(confident) if confident else None)
        with (PRIVATE / (cid + '.pkl')).open('wb') as handle:
            pickle.dump(dict(rows=rows, effective=effective, labels=labels, score=result), handle)
        print(json.dumps(dict(stage='control', done=len(rows_out), case_id=cid)), flush=True)
    f1_providers, f1_primary = primary_means({c: r['control']['spell_f1'] for c, r in rows_out.items()})
    acc_providers, acc_primary = primary_means({c: r['confident_accuracy'] for c, r in rows_out.items()})
    out = dict(matches=rows_out, control_primary_spell_f1=f1_primary, control_provider_spell_f1=f1_providers,
               control_reproduced=round(f1_primary, 6) == .551816,
               proxy_accuracy_by_provider=acc_providers, proxy_accuracy_primary=acc_primary,
               gate_threshold=.75, passed=bool(round(f1_primary, 6) == .551816 and acc_primary >= .75), scoring_calls=score_calls)
    write_new(PUBLIC / 'proxy-accuracy.json', out)
    return {k: v for k, v in out.items() if k != 'matches'}


def windows(periods):
    result, k, i, n = [], 0, 0, len(periods)
    while i < n:
        if periods[i] not in (1, 2):
            i += 1
            continue
        j = i
        while j < n and periods[j] == periods[i]:
            j += 1
        for a in range(i, j, WINDOW):
            result.append((k, a, min(a + WINDOW, j)))
            k += 1
        i = j
    return result


def simulated_tags(match_id, periods, reference, q, home_name, away_name):
    tags = []
    for k, a, b in windows(periods):
        if key_number(f'{match_id}:{k}') % 100 >= SHARE:
            continue
        h = sum(1 for v in reference[a:b] if v == 0)
        w = sum(1 for v in reference[a:b] if v == 1)
        if h == w:
            continue
        side = 'H' if h > w else 'A'
        if key_number(f'flip:{match_id}:{k}') % 1000 >= 1000 * q:
            side = 'A' if side == 'H' else 'H'
        tags.append(te.Tag(home_name if side == 'H' else away_name, a / te.FPS, b / te.FPS))
    return tuple(tags)


def simulate_stage():
    gate = json.loads((PUBLIC / 'proxy-accuracy.json').read_text(encoding='utf-8'))
    if not gate['passed']:
        raise ValueError('Run 6.1 gate not passed; 6.2 not permitted')
    if (PUBLIC / 'simulated-tags.json').exists():
        raise FileExistsError('Run 6.2 already performed')
    from gap_solver.materialization_control import materialize_abstentions
    binds = bindings()
    out, calls = {str(q): {} for q in LEVELS}, 0
    for cid, cohort, role in MATCHES:
        case = load_evaluation(cid, binds[cid])
        frames, reference = case['frames'], case['reference']()
        periods = [f.period for f in frames]
        observed = [f.ball_observed for f in frames]
        with (PRIVATE / (cid + '.pkl')).open('rb') as handle:
            cached = pickle.load(handle)
        rows, effective, control = cached['rows'], cached['effective'], cached['labels']
        base = summary(cached['score'])
        flip_names = key_number(cid) % 2
        home_name, away_name = ('Zulu', 'Alpha') if flip_names else ('Alpha', 'Zulu')
        for q in LEVELS:
            tags = simulated_tags(cid, periods, reference, q, home_name, away_name)
            owner, names = te.owner_track(tags, periods)
            estimate = te.estimate_mapping(control, rows, observed, periods, owner, names)
            if estimate.enabled:
                fused_rows = te.fuse(rows, owner, estimate.mapping, names, estimate.p)
                fused = tuple(materialize_abstentions(te.decode_rows(fused_rows, periods, effective), periods))
            else:
                fused = control
            result = score(reference, fused, frames)
            calls += 1
            side = {home_name: 0, away_name: 1}
            tagged = [i for i, w in enumerate(owner) if w >= 0 and reference[i] < 2]
            hits = sum(side[names[owner[i]]] == reference[i] for i in tagged)
            out[str(q)][cid] = dict(provider=cohort, role=role, control=base, fused=summary(result),
                                    tag_frames=sum(1 for w in owner if w >= 0), tag_precision=hits / len(tagged) if tagged else None,
                                    enabled=estimate.enabled, p_estimated=estimate.p, confident_tagged_frames=estimate.frames,
                                    mapping_correct=bool(estimate.enabled and estimate.mapping[home_name] == 'H'))
        print(json.dumps(dict(stage='simulate', case_id=cid, calls=calls)), flush=True)
    report = {}
    for q in LEVELS:
        rows_q = out[str(q)]
        stats = {}
        for name in ('spell_f1', 'macro_f1'):
            c_prov, c_main = primary_means({c: r['control'][name] for c, r in rows_q.items()})
            f_prov, f_main = primary_means({c: r['fused'][name] for c, r in rows_q.items()})
            stats[name] = dict(control=c_main, fused=f_main, delta=f_main - c_main,
                               by_provider={p: dict(control=c_prov[p], fused=f_prov[p], delta=f_prov[p] - c_prov[p]) for p in PROVIDERS})
        extra = {}
        for name in ('tag_precision', 'p_estimated'):
            prov, main = primary_means({c: r[name] for c, r in rows_q.items()})
            extra[name] = dict(by_provider=prov, primary=main)
        extra['mapping_correct'] = {c: r['mapping_correct'] for c, r in rows_q.items()}
        extra['enabled'] = {c: r['enabled'] for c, r in rows_q.items()}
        extra['spells_before_after'] = {c: [r['control']['n_pred'], r['fused']['n_pred']] for c, r in rows_q.items()}
        report[str(q)] = dict(stats, **extra)
    gates = dict(q09_not_lower=report['0.9']['spell_f1']['delta'] >= 0,
                 q07_loss_within_005=report['0.7']['spell_f1']['delta'] >= -.005)
    result = dict(levels=report, gates=gates, passed=all(gates.values()), matches=out, scoring_calls=calls,
                  note='Mechanism test with tags simulated from reference labels; not a prediction of the gain on the provided match.')
    write_new(PUBLIC / 'simulated-tags.json', result)
    return dict(levels={q: {k: v for k, v in r.items() if k in ('spell_f1', 'macro_f1', 'tag_precision', 'p_estimated')} for q, r in report.items()},
                gates=gates, passed=result['passed'], scoring_calls=calls)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=('control', 'simulate'))
    args = parser.parse_args()
    print(json.dumps({'control': control_stage, 'simulate': simulate_stage}[args.stage](), sort_keys=True, indent=1))


if __name__ == '__main__':
    main()
