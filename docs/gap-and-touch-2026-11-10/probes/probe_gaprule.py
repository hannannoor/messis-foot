"""Aggregate-only: control labels inside long ball gaps, and label-free stoppage signals. No ground truth."""
import json, sys, xml.etree.ElementTree as ET
from math import hypot
from pathlib import Path
repo, data = Path(sys.argv[1]), Path(sys.argv[2]); sys.path.insert(0, str(repo))
from release_runtime import load_source, predict_selected
stem = str(data / 'BAR-ATH_tactical')
frames, _ = load_source(Path(stem + '_atd.xml'), Path(stem + '_atd.txt'), Path(stem + '_homography.csv'))
labels = predict_selected(frames).labels
n = len(frames); per = [f.period for f in frames]
def q(v, ps=(10, 25, 50, 75, 90)):
    s = sorted(v); return {str(p): round(s[min(len(s)-1, int(p/100*len(s)))], 2) for p in ps} if s else {}
# per-frame median player speed over 1 s, by associated id
speed = [None] * n
for i in range(25, n, 5):
    f, g = frames[i], frames[i-25]
    if f.period not in (1, 2) or g.period != f.period: continue
    old = dict(zip(('H%s' % k for k in g.home_ids), g.home_xy)); old.update(zip(('A%s' % k for k in g.away_ids), g.away_xy))
    v = sorted(hypot(p[0]-old[k][0], p[1]-old[k][1]) for k, p in list(zip(('H%s' % k for k in f.home_ids), f.home_xy)) + list(zip(('A%s' % k for k in f.away_ids), f.away_xy)) if k in old)
    v = [x for x in v if x < 12]
    if len(v) >= 10: speed[i] = v[len(v)//2]
gaps = []; i = 0
while i < n:
    if per[i] in (1, 2) and not frames[i].ball_observed:
        j = i
        while j < n and per[j] == per[i] and not frames[j].ball_observed: j += 1
        if j - i > 75: gaps.append((i, j))
        i = j
    else: i += 1
root = ET.parse(stem + '_smart_tagging.xml').getroot()
sp = [round(float(x.findtext('start')) * 25) for x in root.iter('instance') if (x.findtext('code') or '').strip().upper() == 'SET PIECES']
ingap = [False] * n
for a, b in gaps:
    for k in range(a, b): ingap[k] = True
cnt = {'gap': {}, 'observed_or_short': {}}
for k in range(n):
    if per[k] in (1, 2):
        d = cnt['gap' if ingap[k] else 'observed_or_short']; d[labels[k]] = d.get(labels[k], 0) + 1
share = {k: {l: round(c / sum(v.values()), 4) for l, c in sorted(v.items())} for k, v in cnt.items()}
kinds = {}; tagged = []; untagged = []; edge_t = []; edge_u = []; dur_t = []; dur_u = []; bridge = 0
def edge(f): return min(f.ball_x, 105.3 - f.ball_x, f.ball_y, 68 - f.ball_y)
for a, b in gaps:
    inside = set(labels[a:b]); key = ''.join(sorted(inside)); kinds[key] = kinds.get(key, 0) + 1
    before = labels[a-1] if a > 0 and per[a-1] == per[a] else '-'; after = labels[b] if b < n and per[b] == per[a] else '-'
    if before == after and before in 'HA' and inside == {before}: bridge += 1
    sv = [s for s in speed[a:b] if s is not None]
    if not sv: continue
    med = sorted(sv)[len(sv)//2]; is_t = any(a <= s < b + 75 for s in sp)
    (tagged if is_t else untagged).append(med); (dur_t if is_t else dur_u).append((b - a) / 25)
    if a > 0 and frames[a-1].ball_observed: (edge_t if is_t else edge_u).append(edge(frames[a-1]))
obs_speed = [s for k, s in enumerate(speed) if s is not None and not ingap[k]]
print(json.dumps(dict(long_gaps=len(gaps), gap_frames=sum(ingap), control_label_share=share,
  gap_label_sets=kinds, gaps_bridged_by_one_owner_label=bridge,
  median_player_speed_mps=dict(frames_outside_gaps=q(obs_speed), per_gap_with_set_piece_tag=q(tagged), per_gap_without_tag=q(untagged)),
  n_tagged=len(tagged), n_untagged=len(untagged),
  share_gaps_slow_under_1p5=dict(tagged=round(sum(x < 1.5 for x in tagged)/max(1, len(tagged)), 3), untagged=round(sum(x < 1.5 for x in untagged)/max(1, len(untagged)), 3), frames_outside=round(sum(x < 1.5 for x in obs_speed)/max(1, len(obs_speed)), 3)),
  gap_seconds=dict(tagged=q(dur_t), untagged=q(dur_u)),
  last_seen_within_3m_of_boundary=dict(tagged=round(sum(e < 3 for e in edge_t)/max(1, len(edge_t)), 3), untagged=round(sum(e < 3 for e in edge_u)/max(1, len(edge_u)), 3))), indent=1))
