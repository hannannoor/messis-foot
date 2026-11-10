"""Aggregate-only: do automatic set-piece tags coincide with missing-ball gaps? No labels used."""
import json, sys, xml.etree.ElementTree as ET
from pathlib import Path
repo, data = Path(sys.argv[1]), Path(sys.argv[2]); sys.path.insert(0, str(repo))
from gap_solver.input_contract import read_epts_contract, iter_records
stem = data / 'BAR-ATH_tactical'
c = read_epts_contract(Path(str(stem) + '_atd.xml'))
miss = []; per = []
for f in iter_records(c, Path(str(stem) + '_atd.txt')):
    per.append(f.period); miss.append(f.period in (1, 2) and not f.ball_observed)
n = len(miss)
gaps = []; i = 0
while i < n:
    if miss[i]:
        j = i
        while j < n and miss[j]: j += 1
        if j - i > 75: gaps.append((i, j))
        i = j
    else: i += 1
zone = [False] * n   # inside a long gap or within 3 s after it ends
for a, b in gaps:
    for k in range(a, min(n, b + 75)): zone[k] = True
graded = sum(p in (1, 2) for p in per); base = sum(z and p in (1, 2) for z, p in zip(zone, per)) / graded
root = ET.parse(str(stem) + '_smart_tagging.xml').getroot()
starts = {}
for inst in root.iter('instance'):
    code = (inst.findtext('code') or '').strip().upper(); fr = round(float(inst.findtext('start')) * 25)
    if 0 <= fr < n and per[fr] in (1, 2): starts.setdefault(code, []).append(fr)
sp = starts.get('SET PIECES', [])
hit_gaps = sum(any(a <= s < b + 75 for s in sp) for a, b in gaps)
out = dict(long_gaps=len(gaps), graded_share_in_gap_zone=round(base, 4),
  set_piece_tags=len(sp), set_piece_starts_in_gap_zone=round(sum(zone[s] for s in sp) / max(1, len(sp)), 4),
  long_gaps_with_set_piece_tag=round(hit_gaps / len(gaps), 4),
  other_codes_start_in_gap_zone={k: [len(v), round(sum(zone[s] for s in v) / len(v), 3)] for k, v in sorted(starts.items()) if k != 'SET PIECES'})
print(json.dumps(out, indent=1))
