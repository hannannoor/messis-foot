"""Render the completed aggregate local audit as a short readable Markdown report."""
import json
from pathlib import Path

root=Path(__file__).resolve().parent.parent/'analysis'
data=json.loads((root/'camera-analysis.json').read_text(encoding='utf-8'))
sync=json.loads((root/'automatic-sync-verified'/'sync-report.json').read_text(encoding='utf-8'))
t,b=data['cameras']['tactical'],data['cameras']['broadcast']
camera_rows=[]
for name,c in [('Tactical',t),('Broadcast',b)]:
    camera_rows.append('| {} | {:,} | {:,} | {:.2f}% | {:.2f}% | {} / {} |'.format(
        name,c['video_frames'],c['tracking_frames'],c['ball_observed_percent'],
        100*c['homography_valid_frames']/c['homography_rows'],c['sparse_clock_samples'],c['sparse_samples']))
geometry='\n'.join('- {}: {:,} candidate frames'.format(name,count) for name,count in data['geometry_reason_counts'].items()) or '- No eligible timing candidates reached geometry comparison.'
op=data['missing_ball_opportunities']
temporal=data['temporal_geometry_diagnostic']
if data['candidate_frames']==0:
    main_finding='**Dense synchronization remains blocked:** this run produced no eligible cross-camera timing candidates. Joint missing-ball recovery could not be assessed, and no possession changes are justified by this run.'
    next_step='The immediate blocker is dense clock OCR support. Validate the automatic crop/OCR route on permitted external data before selecting any changes, then freeze those choices before another challenge inference run. Independent period anchors and temporal live/replay verification follow once timing support exists.'
    opportunity_text='Joint ball visibility and spatial/temporal geometry could not be evaluated because no timing candidates passed. This result does not establish that broadcast lacks useful missing-ball observations.'
else:
    main_finding='The automatic stage produced bounded clock candidates. These remain intermediate timing evidence and have not been verified as live footage or correct possession.'
    next_step='The next stage is externally validated temporal live/replay verification and an independent automatic period anchor.'
    opportunity_text=('Of the clock-candidate frames, {missing:,} lack tactical ball coordinates; broadcast ball coordinates are present in {visible:,} of those. The existing geometry gate passes in {passing:,} of these potential opportunities. These are observation opportunities, not recovered possession labels. The three-time-point diagnostic has both one-second neighbors for {neighbors:,} central frames; all three pass geometry for {consistent:,} frames. This diagnostic is not a replay classifier.').format(missing=op.get('clock_candidates_with_missing_tactical_ball',0),visible=op.get('broadcast_ball_visible_when_tactical_missing',0),passing=op.get('geometry_consistent_with_broadcast_ball_when_tactical_missing',0),neighbors=temporal['candidate_frames_with_both_neighbors'],consistent=temporal['all_three_geometry_consistent_frames'])
body='''# Two-camera analysis — 5 November 2026

The existing discovery outputs were analyzed and the automatic dense synchronization stage was implemented and run locally. No possession predictions were checked against video or ground truth, no inference parameters were tuned on this match, and no possession labels were changed.

{main_finding}

## Full input audit

| Camera | Video frames | Tracking rows | Ball coordinates present | Valid homography rows | Sparse clock samples |
|---|---:|---:|---:|---:|---:|
{camera_rows}

Ball-coordinate percentages cover all tracking rows, including ungraded recording portions. Presence is not correctness or verified possession. The tactical grading windows contain {graded:,} frames; {missing:,} ({missing_pct:.2f}%) have no ball coordinates. Broadcast tracking and homography have one more row than the decoded video; the discrepancy is retained in diagnostics. No rows were shifted, padded or trimmed.

Tactical homographies meet the existing reprojection-error gate in {t_quality:.2f}% of rows; broadcast does so in {b_quality:.2f}%. Broadcast contains fewer observed player positions on average, which limits the existing distinct-player geometry gate.

## Automatic timing result

- Four windows per camera were selected automatically from discovery, about 5 minutes 40 seconds per feed.
- Tactical dense OCR: {t_reads:,} samples; {t_accepted:,} eligible readings; {t_bounded:,} original frames with bounded timestamps.
- Broadcast dense OCR: {b_reads:,} samples; {b_accepted:,} eligible readings; {b_bounded:,} original frames with bounded timestamps.
- Clock candidates: **{candidates:,} tactical frames ({candidate_seconds:.2f} seconds of frames)**. These need not form one continuous interval.
- Highest combined uncertainty among candidates: {max_uncertainty}.
- Unsupported time remains blank; sparse readings were used only to select processing windows.
- One ordinary broadcast-clock segment remains half-ambiguous. Ordinary clocks at/above 45 minutes require an independent period anchor in this stage. This conservative choice sacrifices second-half coverage rather than treating absent sparse coverage as half evidence.

## Cross-camera evidence

{geometry}

{opportunity_text}

## Delivered code and verification

- Updated standalone version: `2026.11.05-automatic-sync`; source parity checked across all 12 modules; Python 3.9 syntax verified.
- Complete synthetic suite: 148 tests, 147 passed, one optional full-index test skipped. Tests include real FFmpeg/Tesseract execution on generated two-camera clocks, independent frame offsets, moved regions, half ambiguity, malformed reports, output ownership, publication rollback, decoder stalls, long deliberately unselected tails and exact parity with the existing fixed OCR preprocessing/retry recipe.
- A fresh code review identified six issues. Each was addressed with regression coverage before delivery.
- Known minor limitation deferred: a Tesseract subprocess timeout can display a Python traceback. Staging protects the prior completed output.

## What remains

`ready_for_fusion`, `live_verified` and `accuracy_measured` are false. {next_step} Longer-gap possession inference and a general live/dead detector remain later work. The disputed manually published pre-kickoff D interval was not applied by this stage.

Local files: automatic-sync timing CSVs and sync-report.json; camera-analysis.json for aggregate camera/geometry evidence. The original manual pilot and existing possession outputs were preserved.
'''.format(main_finding=main_finding,next_step=next_step,opportunity_text=opportunity_text,camera_rows='\n'.join(camera_rows),graded=t['graded_frames'],missing=t['graded_missing_ball_frames'],
           missing_pct=100*t['graded_missing_ball_frames']/t['graded_frames'],
           t_quality=100*t['homography_within_existing_error_limit_frames']/t['homography_rows'],
           b_quality=100*b['homography_within_existing_error_limit_frames']/b['homography_rows'],
           t_reads=sync['cameras']['tactical']['ocr_samples'],t_accepted=sync['cameras']['tactical']['eligible_reads'],
           t_bounded=sync['cameras']['tactical']['bounded_clock_frames'],
           b_reads=sync['cameras']['broadcast']['ocr_samples'],b_accepted=sync['cameras']['broadcast']['eligible_reads'],
           b_bounded=sync['cameras']['broadcast']['bounded_clock_frames'],candidates=data['candidate_frames'],
           candidate_seconds=data['candidate_duration_seconds'],max_uncertainty=(
               'not applicable (no timing candidates)' if data['max_candidate_uncertainty_s'] is None
               else '{:.3f} seconds'.format(data['max_candidate_uncertainty_s'])),
           geometry=geometry,missing_candidates=op.get('clock_candidates_with_missing_tactical_ball',0),
           secondary_visible=op.get('broadcast_ball_visible_when_tactical_missing',0),
           geometry_opportunities=op.get('geometry_consistent_with_broadcast_ball_when_tactical_missing',0),
           neighbor_frames=temporal['candidate_frames_with_both_neighbors'],
           temporal_consistent=temporal['all_three_geometry_consistent_frames'])
(root/'camera-analysis.md').write_text(body,encoding='utf-8')
print('Rendered camera-analysis.md')
