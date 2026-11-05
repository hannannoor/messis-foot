# Local two-camera clock and fusion experiment

## Controlling update, 5 November 2026

The newer organiser clarification in RULES.md supersedes this historical experiment guide. Do not check predictions against provided video, manually create game data, upload provided data to AI services, or train/fit/calibrate/tune on the provided ground truth or video. All parameter tuning requires external data. Automatic checks and inference on provided inputs remain allowed.

The manual crop/clock-anchor and selected-clip instructions below record an earlier experiment, not an approved final-entry workflow. The executable still includes manual setup and the earlier organiser-answer D interval. Automatic replacement setup is not implemented; eligibility of the D exception needs clarification before final use. The controlled report includes a restart-only stage without that exception.

The new aggregate report is recorded in PROGRESS.md: restart-only resolved coverage was 30.808%, the earlier D context raised it to 32.251%, and fusion reached 32.259%. Fusion changed 13 raw labels and zero scorer-expanded labels. Of 284 compared missing-tactical-ball frames, none had an observed broadcast ball. No accuracy claim or match-based parameter adjustment follows from these counts.

## Controlled restart comparison, 2 November 2026

Use your existing tracking and cached alignment to isolate the Council's first proposed repair. No clock scan, video playback time or crop selection is needed:

```powershell
python football_pipeline.py camera fuse --data-dir "C:\football-data" --alignment "outputs/alignment.csv" --audit-baseline --out "outputs/ensemble"
```

This updates the existing outputs. Keep replacing the same single Python source file. A full-size tracking load may take time; progress is printed.

The corrected restart policy evaluates sustained observed proximity even inside an automatic set-piece phase. It resets control confirmation at phase edges, retains explicit dead-evidence precedence, and still blocks unsupported bridges across restart phases. Proximity is a heuristic, including during a stationary restart. The repair does not establish live play or correct possession by itself. Mapped restart/dead context constrains both cameras, so broadcast cannot simply escape the tactical phase restrictions.

The organiser-published tactical interval [110808,113742) is marked D, with reason `published_pre_kickoff` and evidence level `published_metadata`. This is exactly 2934 frames of the reference export, independently of general stoppage detection. The adapter refuses incompatible dimensions/half context. Missing ball and stationary proximity alone still do not establish D.

`ensemble_report.json` now contains:
- `controlled_comparison.stages`: legacy tactical, restart-repaired tactical, and repaired tactical plus published D context. The existing `after` field is the final fused stage.
- `controlled_comparison.comparisons`: separate changes due to restart repair, published context and fusion, plus the total.
- Each comparison includes raw label changes, scorer-expanded label changes, predicted possession-spell counts, changed reasons, missing-ball assignments and propagation into unchanged raw frames. These are behavior diagnostics, not spellF1 or measured accuracy. X filling follows the official half-local policy, including head backfill and all-X blocks remaining X.
- `verification_reason_counts`: the detailed reasons behind camera verification outcomes; rejected geometry must not be counted as known replays.
- `missing_ball_funnel`: matched frames with missing tactical ball, unresolved opportunities, visible broadcast ball, direct broadcast control, passing geometry, sufficient weight and rescues. Zero opportunities and zero successful recoveries are different outcomes.
- `controlled_comparison.remaining_gap_diagnostics`: why the existing bridge rules still leave X runs.
- `camera_comparison_frames`, skip reasons and alignment statuses distinguish attempted comparisons from frames with no eligible link. Alignment alone cannot identify whether every missing clock was unscanned or unreadable.

The existing diagnostics CSV gains the baseline-stage labels and their scorer-expanded forms when `--audit-baseline` is used. The existing fusion CSV gains timing uncertainty, geometry quality, ball visibility, phase/dead context and source/final labels. No extra prediction files are created for baseline variants.

The legacy restart behavior is reproduced for comparison, not used as the new baseline. Restoring tactical observations may turn previous broadcast rescues into baseline assignments; that is not evidence that broadcast became worse. This delivery deliberately preserves the existing clock/geometry fusion gates so their effects remain isolated. A dedicated replay detector, general live/dead detector and validated longer-gap possession model are later stages, not features claimed by this controlled repair.

The two display layouts both use MM:SS. Different fonts/backgrounds require different crops, not different time units. Screenshots from different moments do not establish a time offset. The program discovers candidate correspondence from the original video clocks; it does not use the screenshot values as anchors.

## Run the new demo first

From the extracted folder in Anaconda Prompt or PowerShell:

```bash
python -m gap_solver.multicam demo
```

Expected synthetic-only output:

```text
Unresolved tactical frames before/after: 40 / 20
Verified broadcast rescues: 20
```

The demonstration has two missing tactical intervals. Broadcast geometry supports one; an invalid broadcast homography blocks the other. This proves test behaviour, not real alignment or improved competition accuracy. This first ensemble runs the same possession rules independently on each camera, then combines the resulting evidence. No neural ensemble was trained.

## What the pipeline does

1. **Read the clock locally.** FFmpeg extracts small clock crops at original decoded frame indices; Tesseract reads the digits. Low-confidence/invalid OCR stays missing.
2. **Build a bounded per-frame time map.** Consecutive readings bracket second ticks. At least three consistent ticks establish a run. Between ticks, the script estimates fractional match time and records timing uncertainty. It leaves unsupported frames blank and does not extrapolate.
3. **Find corresponding moments.** Match half and fractional time, keeping separate tactical/broadcast frame numbers. Reject excessive uncertainty, duplicate clock candidates and unsupported stretches. Dense clocks with contradictory chronology fail validation.
4. **Check the pictures indirectly through tracking.** Require valid, nondegenerate homographies, enough distinct same-team player matches and consistent ball positions when both balls are visible. Team point sets are used because tracking slots are not persistent player IDs.
5. **Fuse reliable evidence.** Missing/inferred broadcast predictions have no vote. A verified direct broadcast prediction can fill a tactical X or outweigh a weak inferred label. Disagreement with direct tactical evidence is retained as a diagnostic conflict. D is never inferred from tracking absence.

## What you need on your computer

The synthetic demo uses only Python 3.9+. Reading actual video additionally requires **FFmpeg (including ffprobe)** and **Tesseract OCR with English language data**, installed locally. These are external executables, not pip packages. Check:

```bash
ffmpeg -version
ffprobe -version
tesseract --version
```

You can pass full executable paths using `--ffmpeg`, `--ffprobe` and `--tesseract`. The prototype requires the reference constant-25-fps export and a reported frame count; it refuses to resample/pad/trim an incompatible export. Metadata rate checks are a preliminary check, not a complete proof that a file has no irregular timestamps.

To fuse possession evidence, you also need the supplied ATD metadata, ATD tracking and homography for **both** sources. Footage alone is sufficient for clock extraction, but this version does not detect players/balls from video itself.

The fusion command accepts either `tactical/` and `broadcast/` or the existing Windows folders `tactical cam/` and `broadcast cam/` under `--data-dir`. It opens those files in place. You can also specify `--tactical-dir "PATH" --broadcast-dir "PATH"` directly; these override the parent-folder lookup. If multiple complete copies exist, it asks for explicit folders instead of guessing. All six required tracking and homography files are checked before loading. The command prints progress, total unresolved tactical frames before/after, broadcast rescues and fusion status counts. With a short clock pilot, only eligible mapped frames can change; the overall counts still cover the full tactical recording.

```text
data/
  tactical/BAR-ATH_tactical.mp4
  tactical/BAR-ATH_tactical_atd.xml
  tactical/BAR-ATH_tactical_atd.txt
  tactical/BAR-ATH_tactical_homography.csv
  tactical/BAR-ATH_tactical_smart_tagging.xml  (optional)
  broadcast/BAR-ATH_broadcast.mp4
  broadcast/BAR-ATH_broadcast_atd.xml
  broadcast/BAR-ATH_broadcast_atd.txt
  broadcast/BAR-ATH_broadcast_homography.csv
```

## Historical pilot: a short first-half interval

Start with roughly 30 seconds showing a progressing clock in each feed. Choose overlapping **match** time; the files' elapsed playback times will differ. Use original frame indices: at 25 fps, frame = elapsed playback seconds * 25. The newer prohibition on manually created game data means this earlier manual setup must not be assumed eligible for a final entry. Never hand-correct possession labels or training/validation labels on this match.

The published tactical first-half kickoff is frame 11185, so a first tactical pilot can use:

```bash
python -m gap_solver.multicam clock --video "D:/mtah-data/tactical/BAR-ATH_tactical.mp4" --source tactical --half 1 --start-frame 11185 --end-frame 11935 --stride 5 --preview outputs/tactical-clock-preview.png --out outputs/tactical-clock.csv
```

For broadcast, replace START and END below with the original frame range containing the same match-clock interval. These are placeholders, not literal arguments:

```bash
python -m gap_solver.multicam clock --video "D:/mtah-data/broadcast/BAR-ATH_broadcast.mp4" --source broadcast --half 1 --start-frame START --end-frame END --stride 5 --preview outputs/broadcast-clock-preview.png --out outputs/broadcast-clock.csv
```

Inspect the saved clock previews **locally**. Crop presets are provisional normalised coordinates based on the supplied display layouts, not guaranteed original-video coordinates. If the crop misses digits or includes the score, override with `--roi x,y,width,height`, where values are fractions from 0 to 1. For example `--roi 0.1,0.02,0.06,0.05`. ROI describes the clock box only; it does not label the match. Temporary crops are deleted after OCR; previews remain at the chosen local path.

**Historical selector capability:** add `--select-roi` to the clock command. A local window opens on the first selected frame. Drag around the complete time digits, leaving a small margin and excluding the score. Inspect the enlarged preview, redraw if necessary, and click **Use clock box**. OCR then continues automatically using your selection. The window uses Python's tkinter; if it is unavailable, the command explains how to install `tk` in your conda environment. Selection geometry and frame extraction are automatically tested; the graphical window still needs verification on your Windows desktop.

The clock box is saved beside the clock CSV, for example `outputs/tactical-clock.csv.roi.json`. Future runs can replace `--select-roi` with `--roi-file "outputs/tactical-clock.csv.roi.json"`. These options are mutually exclusive with `--roi`. These manual options remain software capabilities, not an exemption from the newer rule. Do not upload provided frames or crops to AI services.

**OCR update:** tactical crops are converted to dark digits on a light background and given a small white border. Broadcast crops retain their dark-on-light polarity and receive the same border. TSV output is requested with the explicit `tessedit_create_tsv=1` parameter; an optional `configs/tsv` file is no longer required. Unexpected non-TSV output raises a format error instead of silently becoming zero clock readings. Polarity processing can help or hurt depending on the installed model. Default confidence cutoff is 0.7; for the user-authorised initial trial, add `--min-confidence 0.5` to the clock command. This changes OCR eligibility only; it is not a claim of better timing or possession accuracy. All existing progressing-tick, half, duplicate-match and geometry checks remain.

The trial prints the first percentile (linear interpolation), median and minimum confidence across ALL sampled crops in the requested clip, counting unreadable/invalid clocks as zero. It also prints parsed, unreadable and accepted counts. `First-percentile confidence > 0.5` means the first percentile, not the minimum or a calibrated probability of correctness. Expected clock-absent intervals will lower these all-crop statistics; the first trial intentionally uses a visible mid-game interval. Do not optimise from this challenge clip; subsequent tuning requires external data.

**Retry update:** only a crop that is unreadable or below the chosen cutoff is retried. Two local treatments restore the original enlarged crop (undoing the tactical inversion and added border) and threshold the processed crop to black and white. If eligible treatments disagree on the clock, the sample stays unresolved. Otherwise the highest measured eligible score is retained; scores are never increased by agreement. Retry counts, recoveries at the cutoff and conflicts are printed. These are selected OCR scores after retries, not independent accuracy measurements. The reads CSV records the chosen treatment and number of attempts.

The timeline can now skip a weak or unreadable sample when the accepted observations on either side are at most 0.5 seconds apart and the clock remains consistent. At the pilot's stride 5 and 25 fps, this tolerates one missed sample; two consecutive misses split the run. Tick uncertainty increases across the gap. At least three consistent second ticks are still required, with no extrapolation. A bounded time estimate can therefore exist at a frame whose own OCR remained unreadable; this does not change its all-crop OCR score from zero. Stricter combined timing uncertainty can still reject a two-camera correspondence.

To test one existing raw crop without rescanning a video:

```bash
python -m gap_solver.multicam ocr-check --image "outputs/tactical-clock-preview.png" --source tactical
```

This prints OCR text and Tesseract's confidence score before and after preprocessing. Scores are not measured accuracy. Previews saved by the updated clock command already show the preprocessed OCR input; applying `ocr-check` to one of those compares that input against an additional polarity transformation, so the Original score is the relevant current-input score. No image leaves your machine.

The user-specified half must match the entire selected interval. Do not run a half-1 command across halftime or the second half. MM:SS alone cannot distinguish first-half stoppage time from overlapping second-half minutes. This version is a selected-clip pilot; joining separate half pilots into one full-match clock map is not automated. A later merge must preserve original indices and use distinct segment IDs.

Then build candidate alignment and fuse:

```bash
python -m gap_solver.multicam align --tactical-clock outputs/tactical-clock.csv --broadcast-clock outputs/broadcast-clock.csv --out outputs/alignment.csv
python -m gap_solver.multicam fuse --data-dir "D:/mtah-data" --alignment outputs/alignment.csv --out outputs/ensemble
```

The dense clock CSV has one row per original video frame, including blank estimates outside the pilot. Fusion retains the original tactical-only result wherever no eligible broadcast correspondence exists. The resulting submission-shaped CSV remains experimental; an automatic live/dead classifier is still absent.

Automatic diagnostics can report missing readings, timing uncertainty and absent overlap. Do not check predictions against challenge video or hand-adjust its crop/timing setup. Choose processing parameters and OCR stride using external evaluation, not this game's assignment coverage. Clock scans decode from the start of the file to preserve decoded indices; later intervals can therefore cost more than their clip duration suggests.

## Files to inspect

| File | Meaning |
|---|---|
| `tactical-clock.csv` / `broadcast-clock.csv` | Original frame, half, estimated match seconds, timing uncertainty, segment ID |
| `*.reads.csv` | Selected OCR reading, measured score, chosen treatment and attempt count; generated automatically |
| `alignment.csv` | Tactical frame, candidate broadcast frame, uncertainty and candidate/rejection status |
| `fusion_diagnostics.csv` | Camera weights, fusion decision and geometry result per tactical frame |
| `ensemble_report.json` | Tactical-only vs fused label coverage; rescues, replacements and conflicts |
| `submission.csv` | Experimental predictions on the tactical timeline |

For example, a frame can have estimated match time 1622.32 seconds while its counterpart has a completely different file frame index. Timing uncertainty is reported separately; this is not a claim of exact frame synchronisation.

## Weights and safeguards

Provisional values in code:

- Direct tactical control: weight 1.0. Inferred tactical continuity: 0.35.
- Eligible broadcast control: `0.9 * geometry_quality * (1 - 0.5 * uncertainty / 0.25)`.
- Geometry quality combines player-position agreement with reprojection error.
- Broadcast needs weight >= 0.3 to rescue X; replacing a conflicting inferred tactical label additionally requires a normalised vote advantage >= 0.2.
- Maximum combined clock uncertainty: 0.25 seconds. Coarse one-second OCR is often insufficient. The geometry limits default to 3 m median player residual, at least three distinct matches per team and 60% of unique broadcast points, 4 m ball residual when visible in both views, and reprojection error <= 3.

These values are engineering defaults, not calibrated probabilities or values tuned on the public five minutes. The exact numbers will need independent evaluation on compatible other-match data. The fusion default preserves direct tactical disagreements; it is intentionally more restrictive than blindly averaging two labels.

## Limitations to assess on local data

- A replay can carry a live clock and plausible player positions. The checks reduce false matches but do **not** constitute a complete replay detector.
- Camera overlays can have systematic delay or rounding differences; tick matching alone does not prove the same physical moment.
- Both ATD exports must use compatible pitch orientation and coordinates. If they disagree, geometry rejects the match; automatic orientation calibration is not implemented.
- A narrow broadcast shot may have too few players to verify. Invalid homography does not mean dead ball.
- Player point sets can agree accidentally; no persistent player identity is assumed. Distinct spatial matching prevents duplicate tracks from counting as independent support.
- Added-time parser accepts `45+02:13` and `90+01:02`, but actual live OCR/crop behaviour for added-time overlays is untested. Clocks freezing at 45:00/90:00 without a readable added-time timer leave unsupported intervals.
- No actual competition footage/tracking was processed here. The displayed screenshots were only used to identify clock format and approximate layout. They are not bundled or used as labels or timing anchors.

Keep all footage, crops, tracking and derived alignment outputs local. Do not upload restricted competition assets or extracts to hosted/cloud LLMs, publish them, or use public labels for model selection. No network calls exist in these modules.

Official tool references: https://tesseract-ocr.github.io/tessdoc/Command-Line-Usage.html and https://ffmpeg.org/ffmpeg-filters.html . Competition formats follow the uploaded starter snapshot.
