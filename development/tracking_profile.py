"""Label-free, bounded ball-track aggregates. Only main loads the provided track."""
import json
from math import hypot
from pathlib import Path
from statistics import median

from observed_touch import detect_observed_touches, observed_evidence_rows
from touch_evidence import prepare_evidence
from touch_physics import attributed_team

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'reports/touch-transfer/tracking-profile.json'


def observed_runs(frames):
    i = 0
    while i < len(frames):
        if frames[i].period not in (1, 2) or not frames[i].ball_observed:
            i += 1
            continue
        first, period = i, frames[i].period
        while i < len(frames) and frames[i].period == period and frames[i].ball_observed:
            i += 1
        yield first, i


def run_surprises(frames, first, stop):
    def velocity(a, b):
        return ((frames[b].ball_x - frames[a].ball_x) * 25 / (b-a),
                (frames[b].ball_y - frames[a].ball_y) * 25 / (b-a))
    result = {}
    for t in range(first+5, stop-5):
        before, after = velocity(t-5, t), velocity(t, t+5)
        result[t] = hypot(after[0]-before[0], after[1]-before[1])
    return result


def surprise_values(frames):
    return [v for a, b in observed_runs(frames) for v in run_surprises(frames, a, b).values()]


def bonus_statistics(frames, events):
    base, _, periods, usable, _ = prepare_evidence(frames, [], 0, 32)
    rows, _ = observed_evidence_rows(base, periods, usable, [f.ball_observed for f in frames], events, 2, 8)
    count = sum(p in (1, 2) and tuple(a) != tuple(b) for p, a, b in zip(periods, base, rows))
    graded = sum(p in (1, 2) for p in periods)
    owned = sum(e.team in ('H', 'A') for e in events)
    return dict(bonus_frames=count, bonus_share=count / graded if graded else None,
                bonus_frames_per_owned_touch=count / owned if owned else None)


def profile(frames):
    graded = sum(f.period in (1, 2) for f in frames)
    observed = sum(f.period in (1, 2) and f.ball_observed for f in frames)
    speeds, surprises, peaks = [], [], []
    for first, stop in observed_runs(frames):
        speeds.extend(hypot(frames[i].ball_x-frames[i-1].ball_x,
                            frames[i].ball_y-frames[i-1].ball_y) * 25 for i in range(first+1, stop))
        values = run_surprises(frames, first, stop)
        surprises.extend(values.values())
        for t, value in values.items():
            if value < 3:
                continue
            neighborhood = range(max(first+5, t-5), min(stop-5, t+6))
            if max(neighborhood, key=lambda j: (values[j], -j)) == t:
                peaks.append(attributed_team(frames[t]) is None)
    events = detect_observed_touches(frames, 3)
    owned = sum(e.team in ('H', 'A') for e in events)
    minutes = observed / 1500
    return dict(graded=graded, observed=observed, observed_minutes=minutes,
                observed_share=observed / graded if graded else None,
                median_speed_mps=median(speeds) if speeds else None,
                median_surprise_mps=median(surprises) if surprises else None,
                surprise_samples=len(surprises), surprise_ge_3_share=sum(v >= 3 for v in surprises) / len(surprises) if surprises else None,
                kink_peaks=len(peaks), unattributed_peak_share=sum(peaks) / len(peaks) if peaks else None,
                owned_touches=owned, events=len(events), owned_touch_rate=owned / minutes if minutes else None,
                **bonus_statistics(frames, events))


def main():
    # This entry point is the sole provided-input reader in the new harness.
    from release_runtime import load_source
    from memory_ablation_metrics import MATCHES
    from memory_ablation_run import load_evaluation
    import memory_ablation_protocol as protocol
    import gap_liveness_experiment as gap
    from touch_transfer import validate_matches, regime_frames
    if OUT.exists():
        raise FileExistsError('Profile already exists')
    validate_matches()
    prefix = json.loads((ROOT / '.superpowers/release/target-handling.json').read_text(encoding='utf-8'))['input_prefix']
    frames, _ = load_source(*(Path(prefix+s) for s in ('_atd.xml', '_atd.txt', '_homography.csv')))
    provided = profile(frames)
    del frames
    result = dict(provided=provided, matches={}, checks={})
    bindings = protocol.input_bindings(ROOT)['evaluation']
    for cid, provider, role in MATCHES:
        gap.check_input(bindings[cid], bindings[cid]['expected'])
        case = load_evaluation(cid, bindings[cid])
        frames = case['frames']
        row = dict(provider=provider, role=role, natural=profile(frames))
        if provider != 'skillcorner':
            work, _ = regime_frames(cid, frames, case['reference']())
            row['stop75-jitter'] = profile(work)
        result['matches'][cid] = row
        print(json.dumps(dict(profile_complete=cid)), flush=True)
    result['checks'] = dict(
        provided_surprise_within_2_percent=abs(provided['median_surprise_mps']/1.127-1) <= .02,
        provided_rate_within_2_percent=abs(provided['owned_touch_rate']/10.46-1) <= .02,
        primary_noise_in_range=all(.9 <= result['matches'][cid]['stop75-jitter']['median_surprise_mps'] <= 1.4
                                  for cid in ('dfl-J03WN1', 'dfl-J03WR9', 'wcsf-used-match')))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open('x', encoding='utf-8') as handle:
        json.dump(result, handle, sort_keys=True, indent=1, allow_nan=False)
        handle.write('\n')
    print(json.dumps(dict(provided=provided, checks=result['checks']), sort_keys=True), flush=True)
    if not all(result['checks'].values()):
        raise ValueError('Profile stop condition triggered; do not score')


if __name__ == '__main__':
    main()
