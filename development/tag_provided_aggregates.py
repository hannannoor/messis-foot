"""Run 6.3: provided match, one run, bounded aggregates only (no per-frame rows, tag times or labels).

    python -I tag_provided_aggregates.py
"""
from collections import Counter
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parent))

import tag_evidence as te
import tag_release as tr
from gap_release import assemble, labels_sha256
from kickoff_patch import kickoff_starts

ROOT = Path(__file__).resolve().parent
HANDLING = ROOT / '.superpowers/release/target-handling.json'
OUT = ROOT / 'reports/tag-ownership/provided-match.json'
CURRENT_SPELLS = 434


def quantile(values, fraction):
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int(fraction * (len(ordered) - 1) + .5))]


def spell_lengths(frames, labels):
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
    return runs


def label_stats(frames, labels):
    graded = [v for f, v in zip(frames, labels) if f.period in (1, 2)]
    counts = Counter(graded)
    runs = spell_lengths(frames, labels)
    return dict(counts={k: counts[k] for k in 'HADX'}, spells=len(runs), median_spell=quantile(runs, .5),
                spells_under_25=sum(r < 25 for r in runs))


def metadata_home_on_h(prefix, names, mapping):
    """Does the derived mapping put the metadata's home team on H? Roles follow the loader's documented-name rule."""
    aliases = {'barcelona': 'H', 'fcbarcelona': 'H', 'athleticclub': 'A', 'atleticclub': 'A'}
    roles = {}
    for team in ET.parse(prefix + '_atd.xml').getroot().iter('Team'):
        name = ''.join(c for c in (team.findtext('Name') or '').lower() if c.isalnum())
        roles[name] = aliases.get(name)
    home = [n for n in names if roles.get(''.join(c for c in n.lower() if c.isalnum())) == 'H']
    if not mapping or len(home) != 1:
        return 'not derivable'
    return 'yes' if mapping[home[0]] == 'H' else 'no'


def main():
    from release_runtime import load_source
    prefix = json.loads(HANDLING.read_text(encoding='utf-8'))['input_prefix']
    tags_path = prefix + '_smart_tagging.xml'
    frames, _ = load_source(*(Path(prefix + s) for s in ('_atd.xml', '_atd.txt', '_homography.csv')))
    parts = tr.control_parts(frames)
    _, rows, effective, control, periods, observed = parts
    predicted = tr.predict(frames, te.read_tags(tags_path), parts=parts)
    starts = kickoff_starts(tags_path)
    old = assemble(frames, predicted.control, starts).final
    new = assemble(frames, predicted.fused, starts).final
    estimate = predicted.estimate
    graded = [i for i, p in enumerate(periods) if p in (1, 2)]
    margins = [m for _, m in te.margins(predicted.control, rows, observed, periods)]
    owner = predicted.owner
    tagged = [i for i in graded if owner[i] >= 0]
    side = {}
    if estimate.mapping:
        side = {k: estimate.mapping[name] for k, name in enumerate(predicted.names)}

    def window_shares(labels):
        c = Counter()
        for i in tagged:
            mine = side.get(owner[i])
            v = labels[i]
            c['tagged' if v == mine else 'other' if v in ('H', 'A') else 'D' if v == 'D' else 'X'] += 1
        return {k: c[k] / len(tagged) for k in ('tagged', 'other', 'D', 'X')} if tagged else None

    pairs = Counter((a, b) for a, b in zip(old, new) if a != b)
    graded_changed = sum(old[i] != new[i] for i in graded)
    result = dict(
        tags_enabled=estimate.enabled, disabled_reason=estimate.reason,
        confident_tagged_frames=estimate.frames, p=estimate.p, agreement_a=estimate.agreement,
        metadata_home_team_on_H=metadata_home_on_h(prefix, predicted.names, estimate.mapping),
        owner_margin_quantiles={str(q): quantile(margins, q / 100) for q in (5, 25, 50, 75, 95)},
        tag_coverage_of_graded=len(tagged) / len(graded),
        frames_changed_vs_current_candidate=sum(a != b for a, b in zip(old, new)),
        graded_frames_changed_share=graded_changed / len(graded),
        changed_by_pair={a + '->' + b: n for (a, b), n in sorted(pairs.items())},
        current=label_stats(frames, old), with_tags=label_stats(frames, new),
        single_team_window_shares=dict(current=window_shares(old), with_tags=window_shares(new)),
        current_final_labels_sha256=labels_sha256(old), with_tags_final_labels_sha256=labels_sha256(new))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open('x', encoding='utf-8') as handle:
        json.dump(result, handle, sort_keys=True, indent=1)
        handle.write('\n')
    print(json.dumps(result, sort_keys=True, indent=1))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
