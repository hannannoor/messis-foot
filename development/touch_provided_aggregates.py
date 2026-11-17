"""Step 8.2: provided match, one run, bounded aggregates only (no per-frame rows, times or labels).

    python -I touch_provided_aggregates.py
"""
from collections import Counter
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from gap_release import assemble, labels_sha256
from kickoff_patch import kickoff_starts
from observed_touch import detect_observed_touches, observed_evidence_rows
from release_runtime import load_source, predict_selected
from touch_evidence import prepare_evidence
import touch_release as tr

ROOT = Path(__file__).resolve().parent
HANDLING = ROOT / '.superpowers/release/target-handling.json'
OUT = ROOT / 'reports/stoppage-regime/provided-match.json'


def quantile(values, fraction):
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int(fraction * (len(ordered) - 1) + .5))]


def stats(frames, labels):
    graded = [v for f, v in zip(frames, labels) if f.period in (1, 2)]
    counts = Counter(graded)
    runs, current, length = [], None, 0
    for f, v in zip(frames, labels):
        key = (f.period, v) if f.period in (1, 2) and v in ('H', 'A') else None
        if key != current:
            if current:
                runs.append(length)
            current, length = key, 0
        if key:
            length += 1
    if current:
        runs.append(length)
    return dict(counts={k: counts[k] for k in 'HADX'}, spells=len(runs), median_spell=quantile(runs, .5),
                spells_under_25=sum(r < 25 for r in runs))


def main():
    prefix = json.loads(HANDLING.read_text(encoding='utf-8'))['input_prefix']
    tags = prefix + '_smart_tagging.xml'
    frames, _ = load_source(*(Path(prefix + s) for s in ('_atd.xml', '_atd.txt', '_homography.csv')))
    starts = kickoff_starts(tags)
    old = assemble(frames, tuple(predict_selected(frames).labels), starts).final
    events = detect_observed_touches(frames, tr.THETA)
    new = assemble(frames, tr.predict_labels(frames), starts).final
    base, _, periods, usable, _ = prepare_evidence(frames, [], 0, 32)
    observed = [f.ball_observed for f in frames]
    rows, _ = observed_evidence_rows(base, periods, usable, observed, events, tr.BETA, tr.C_TOUCH)
    graded = [i for i, p in enumerate(periods) if p in (1, 2)]
    bonus = sum(1 for i in graded if observed[i] and tuple(rows[i]) != tuple(base[i]))
    pairs = Counter((a, b) for a, b in zip(old, new) if a != b)
    result = dict(touches_detected=len(events), bonus_share_of_graded=bonus / len(graded),
                  frames_changed=sum(a != b for a, b in zip(old, new)),
                  graded_changed_share=sum(old[i] != new[i] for i in graded) / len(graded),
                  changed_by_pair={a + '->' + b: n for (a, b), n in sorted(pairs.items())},
                  current=stats(frames, old), with_touch=stats(frames, new),
                  current_final_labels_sha256=labels_sha256(old), with_touch_final_labels_sha256=labels_sha256(new))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open('x', encoding='utf-8') as handle:
        json.dump(result, handle, sort_keys=True, indent=1)
        handle.write('\n')
    print(json.dumps(result, sort_keys=True, indent=1))


if __name__ == '__main__':
    main()
