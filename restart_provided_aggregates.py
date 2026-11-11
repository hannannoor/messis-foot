"""One bounded local comparison; set-piece team labels are reporting-only."""
from collections import Counter
import hashlib
import json
from pathlib import Path
from statistics import median
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kickoff_patch import apply_kickoff_patch, kickoff_starts
from release_runtime import load_source, submission_bytes
from restart_release import assemble

ROOT = Path(__file__).resolve().parent
OUT = ROOT/'reports/submission/restart-provided.json'


def label_stats(frames, labels):
    counts = Counter(label for f, label in zip(frames, labels) if f.period in (1, 2))
    lengths, current, length = [], None, 0
    for f, label in zip(frames, labels):
        key = (f.period, label) if f.period in (1, 2) and label in ('H', 'A') else None
        if key != current:
            if current:
                lengths.append(length)
            current, length = key, 0
        if key:
            length += 1
    if current:
        lengths.append(length)
    return dict(label_counts={k: counts[k] for k in 'HADX'}, spells=len(lengths),
                median_spell=median(lengths) if lengths else None,
                spells_under_25=sum(x < 25 for x in lengths), spells_under_50=sum(x < 50 for x in lengths),
                dead_share=counts['D']/sum(counts.values()) if counts else None)


def tag_check(path, periods, labels):
    # Identical reporting-only spelling aliases to tag_provided_aggregates.py.
    aliases = {'barcelona':'H', 'fcbarcelona':'H', 'athleticclub':'A', 'atleticclub':'A'}
    types = {}
    def normal(value):
        return ' '.join((value or '').upper().split())
    for item in ET.parse(path).iter('instance'):
        if normal(item.findtext('code')) != 'SET PIECES':
            continue
        fields = {normal(label.findtext('group')): label.findtext('text') or '' for label in item.findall('label')}
        team = aliases.get(''.join(c for c in fields.get('TEAM', '').lower() if c.isalnum()))
        if team is None:
            continue
        start, end = round(float(item.findtext('start'))*25), round(float(item.findtext('end'))*25)
        if not 0 <= start < len(periods) or periods[start] not in (1, 2):
            continue
        first = next((i for i in range(max(1, start-75), min(len(labels), end+250))
                      if periods[i] == periods[start] == periods[i-1] and labels[i-1] == 'D' and labels[i] in ('H','A')), None)
        outcome = 'no_transition' if first is None else 'match' if labels[first] == team else 'mismatch'
        kind = normal(fields.get('TYPE', 'UNSPECIFIED'))
        types.setdefault(kind, dict(match=0, mismatch=0, no_transition=0))[outcome] += 1
    return dict(by_type=types, total={k: sum(x[k] for x in types.values()) for k in ('match','mismatch','no_transition')})


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open('x', encoding='utf-8') as handle:
        handle.write('{"status":"running"}\n')
    prefix = json.loads((ROOT/'.superpowers/release/target-handling.json').read_text(encoding='utf-8'))['input_prefix']
    tags = prefix+'_smart_tagging.xml'
    frames, _ = load_source(*(Path(prefix+s) for s in ('_atd.xml','_atd.txt','_homography.csv')))
    starts = kickoff_starts(tags)
    result = assemble(frames, starts)
    old = apply_kickoff_patch(frames, result.gapped, starts).labels
    new = result.final
    old_hash = hashlib.sha256(submission_bytes(old)).hexdigest()
    if old_hash != '31b947d3b250b6267a7d8f0aac0c4e4eafd82a4fc873c82759806e676b1bf963':
        raise ValueError('Disabled restart does not reproduce the existing candidate')
    graded = [i for i, f in enumerate(frames) if f.period in (1, 2)]
    pairs = Counter(old[i]+'->'+new[i] for i in graded if old[i] != new[i])
    changed_owners = no_owner = 0
    for first, stop in result.stoppage_gaps:
        end = stop
        while end < len(frames) and frames[end].period == frames[first].period:
            end += 1
        owners = [next((labels[i] for i in range(stop, end) if labels[i] in ('H','A')), None) for labels in (old, new)]
        changed_owners += owners[0] != owners[1]
        no_owner += any(x is None for x in owners)
    old_stats, new_stats = label_stats(frames, old), label_stats(frames, new)
    changed = sum(pairs.values())
    stop = changed/len(graded) > .01 or abs(old_stats['spells']-434) > 2 or abs(new_stats['spells']-415) > 2
    value = dict(status='complete', graded_frames=len(graded), frames_changed=changed,
                 changed_share=changed/len(graded), changed_by_pair=dict(sorted(pairs.items())),
                 old=old_stats, new=new_stats, stoppage_gaps=len(result.stoppage_gaps),
                 gaps_with_different_first_owner=changed_owners, gaps_without_later_owner=no_owner,
                 tag_check=dict(old=tag_check(tags, [f.period for f in frames], old),
                                new=tag_check(tags, [f.period for f in frames], new)),
                 old_csv_sha256=old_hash, new_csv_sha256=hashlib.sha256(submission_bytes(new)).hexdigest(),
                 stop_required=stop)
    OUT.write_text(json.dumps(value, sort_keys=True, indent=1)+'\n', encoding='utf-8')
    print(json.dumps(value, sort_keys=True, indent=1))
    if stop:
        raise ValueError('Aggregate stop condition triggered: user decision required')


if __name__ == '__main__':
    main()
