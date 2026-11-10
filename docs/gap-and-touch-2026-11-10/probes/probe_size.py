"""Aggregate-only probe: apparent player/ball size in the tactical view, ball-run shape.
Prints quantiles and counts only. No per-frame values leave this process."""
import csv, json, sys
from math import hypot, isfinite, sqrt
from pathlib import Path

repo, data = Path(sys.argv[1]), Path(sys.argv[2])
sys.path.insert(0, str(repo))
from gap_solver.input_contract import read_epts_contract, iter_records

stem = data / 'BAR-ATH_tactical'
contract = read_epts_contract(Path(str(stem) + '_atd.xml'))

H = {}
with open(str(stem) + '_homography.csv', newline='') as f:
    for row in csv.DictReader(f):
        if row['valid'].strip() in ('1', '1.0', 'True', 'true'):
            H[int(row['frame'])] = [float(row['h%d%d' % (i, j)]) for i in range(3) for j in range(3)]


def scales(h, xm, ym):
    """Singular values of d(pixel)/d(metre) at a pitch point (homography takes 0-1 coords)."""
    x, y = xm / 105.3, ym / 68.0
    w = h[6] * x + h[7] * y + h[8]
    u = (h[0] * x + h[1] * y + h[2]) / w
    v = (h[3] * x + h[4] * y + h[5]) / w
    a = (h[0] - u * h[6]) / w / 105.3; b = (h[1] - u * h[7]) / w / 68.0
    c = (h[3] - v * h[6]) / w / 105.3; d = (h[4] - v * h[7]) / w / 68.0
    s1 = a * a + b * b + c * c + d * d
    s2 = sqrt(max(0.0, (a * a + b * b - c * c - d * d) ** 2 + 4 * (a * c + b * d) ** 2))
    return sqrt((s1 + s2) / 2), sqrt(max(0.0, (s1 - s2) / 2)), u, v


def q(values, ps=(5, 25, 50, 75, 95)):
    s = sorted(values)
    return {str(p): round(s[min(len(s) - 1, int(p / 100 * len(s)))], 2) for p in ps} if s else {}


player_px, ball_px, inside = [], [], [0, 0]
runs, gaps, cur_run, cur_gap, prev_period = [], [], 0, 0, None
near = [0, 0]
graded = observed = 0
for i, f in enumerate(iter_records(contract, Path(str(stem) + '_atd.txt'))):
    if f.period not in (1, 2):
        if cur_run: runs.append(cur_run)
        if cur_gap: gaps.append(cur_gap)
        cur_run = cur_gap = 0; prev_period = f.period
        continue
    if f.period != prev_period:
        if cur_run: runs.append(cur_run)
        if cur_gap: gaps.append(cur_gap)
        cur_run = cur_gap = 0; prev_period = f.period
    graded += 1
    pts = list(f.home_xy) + list(f.away_xy)
    if f.ball_observed:
        observed += 1
        if cur_gap: gaps.append(cur_gap); cur_gap = 0
        cur_run += 1
        near[1] += 1
        if any(hypot(x - f.ball_x, y - f.ball_y) <= 2.5 for x, y in pts): near[0] += 1
    else:
        if cur_run: runs.append(cur_run); cur_run = 0
        cur_gap += 1
    if i % 5 == 0 and i in H:
        h = H[i]
        for x, y in pts:
            if isfinite(x) and isfinite(y):
                big, small, u, v = scales(h, x, y)
                inside[1] += 1
                if 0 <= u < 1920 and 0 <= v < 1080:
                    inside[0] += 1
                    player_px.append(1.8 * big)
        if f.ball_observed:
            big, small, u, v = scales(h, f.ball_x, f.ball_y)
            if 0 <= u < 1920 and 0 <= v < 1080: ball_px.append(0.22 * big)
if cur_run: runs.append(cur_run)
if cur_gap: gaps.append(cur_gap)

print(json.dumps(dict(
    graded_frames=graded, ball_observed_share=round(observed / graded, 4),
    est_player_height_px=q(player_px), est_ball_diameter_px=q(ball_px),
    player_samples=len(player_px), players_projecting_inside_image_share=round(inside[0] / max(1, inside[1]), 4),
    ball_runs=dict(count=len(runs), frames_quantiles=q(runs), share_runs_under_11_frames=round(sum(r < 11 for r in runs) / len(runs), 4)),
    ball_gaps=dict(count=len(gaps), frames_quantiles=q(gaps)),
    observed_frames_with_player_within_2p5m=round(near[0] / max(1, near[1]), 4),
), indent=1))
