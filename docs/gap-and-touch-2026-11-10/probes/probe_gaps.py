"""Aggregate-only: are missing-ball stretches stoppage-like? No labels used."""
import json, sys
from math import hypot
from pathlib import Path
repo, data = Path(sys.argv[1]), Path(sys.argv[2]); sys.path.insert(0, str(repo))
from gap_solver.input_contract import read_epts_contract, iter_records
stem = data / 'BAR-ATH_tactical'
c = read_epts_contract(Path(str(stem) + '_atd.xml'))
def q(v, ps=(10, 25, 50, 75, 90)):
    s = sorted(v); return {str(p): round(s[min(len(s)-1, int(p/100*len(s)))], 2) for p in ps} if s else {}
hist = []; sp_obs = []; sp_gap = []; gap_len = 0; gaps = []; last_edge = []; first_edge = []; last_ball = None; prev = None
miss_by_len = {'<=1s': 0, '1-3s': 0, '3-10s': 0, '>10s': 0}
def close(n):
    k = '<=1s' if n <= 25 else '1-3s' if n <= 75 else '3-10s' if n <= 250 else '>10s'; miss_by_len[k] += n; gaps.append(n)
def edge(x, y): return min(x, 105.3 - x, y, 68 - y)
for i, f in enumerate(iter_records(c, Path(str(stem) + '_atd.txt'))):
    if f.period not in (1, 2) or f.period != prev:
        if gap_len: close(gap_len)
        gap_len = 0; hist = []; last_ball = None; prev = f.period
        if f.period not in (1, 2): continue
    cur = dict(zip(('H%s' % k for k in f.home_ids), f.home_xy)); cur.update(zip(('A%s' % k for k in f.away_ids), f.away_xy))
    hist.append(cur)
    if len(hist) > 6: hist.pop(0)
    if len(hist) == 6 and i % 5 == 0:
        old = hist[0]; v = sorted(hypot(p[0]-old[k][0], p[1]-old[k][1]) / 0.2 for k, p in cur.items() if k in old)
        v = [x for x in v if x < 12]
        if len(v) >= 10: (sp_obs if f.ball_observed else sp_gap).append(v[len(v)//2])
    if f.ball_observed:
        if gap_len:
            close(gap_len)
            if gap_len > 75: first_edge.append(edge(f.ball_x, f.ball_y))
            if gap_len > 75 and last_ball: last_edge.append(edge(*last_ball))
        gap_len = 0; last_ball = (f.ball_x, f.ball_y)
    else: gap_len += 1
if gap_len: close(gap_len)
tot = sum(miss_by_len.values())
print(json.dumps(dict(missing_frames=tot, missing_share_by_gap_length={k: round(v/tot, 4) for k, v in miss_by_len.items()},
  gap_count=len(gaps), median_player_speed_mps=dict(ball_observed=q(sp_obs), ball_missing=q(sp_gap)),
  long_gaps_over_3s=dict(n=len(last_edge), last_seen_distance_to_boundary_m=q(last_edge), share_last_seen_within_3m_of_boundary=round(sum(e < 3 for e in last_edge)/max(1, len(last_edge)), 3),
    reappear_distance_to_boundary_m=q(first_edge), share_reappear_within_3m_of_boundary=round(sum(e < 3 for e in first_edge)/max(1, len(first_edge)), 3))), indent=1))
