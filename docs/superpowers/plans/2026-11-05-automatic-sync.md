# Automatic two-camera synchronization implementation plan

> **For agentic workers:** Use superpowers:executing-plans to implement this plan task by task.

**Goal:** Continue the accepted automatic-setup plan with local dense clock correspondence and camera diagnostics.

**Architecture:** Use existing sparse clock segments to choose processing windows and crops automatically. Reuse the original-frame decoder, pretrained local OCR, existing dense-clock estimator and unchanged timing thresholds. Check continuous-clock semantics or explicit added-time notation against the published tactical half windows; ordinary clocks at or beyond 45 minutes remain ambiguous without an independent period anchor. Unsupported dense timing stays missing.

**Tech stack:** Python 3.9+ standard library, installed FFmpeg/ffprobe/Tesseract; synthetic integration fixtures use Pillow.

**Spec:** Existing TWO_CAMERA_DESIGN.md and RULES.md, plus the user's request to continue Plan Data Analysis Variables. This document narrows the next stage; it does not implement or claim a trained replay detector.

## Global constraints

- Keep original per-camera decoded frame indices. No resampling, padding or trimming to force correspondence.
- No challenge footage/crops/tracking in tools hosted outside the PC; return aggregate diagnostics only.
- No ground-truth possession inputs, video checking of predictions, hand correspondences, fitting or parameter tuning on this match.
- Preserve existing confidence .7 and maximum combined clock uncertainty .25 seconds.
- Published evaluation half windows are structural input metadata, distinct from the disputed pre-kickoff D labels. Do not apply those D labels in this stage.
- Do not overwrite the existing manual pilot clocks, alignment or possession results. Write automatic outputs into a separate folder.
- Clock correspondence is candidate evidence; ready_for_fusion and live_verified remain false.

## Task 1: Automatic window planning and selective decoding

Files: gap_solver/automatic_sync.py, gap_solver/clock_discovery.py, tests/test_automatic_sync.py.

- [x] Write failing tests for unique/ambiguous half assignment, independent camera frame numbers, cropped/windowed original indices and corrupt discovery inputs.
- [x] Implement plan_windows(tactical, broadcast, blocks), with no dense interpolation of sparse observations. Sparse interpolation selects processing bounds only.
- [x] Extend iter_video_samples with optional windows and ROI while preserving existing behavior and full decoded-count validation.
- [x] Run synthetic unit and generated-video tests.

## Task 2: Dense OCR, CLI and standalone delivery

Files: gap_solver/automatic_sync.py, gap_solver/multicam.py, football_pipeline.py, tests/test_automatic_sync.py.

- [x] Write failing tests for bounded dense reconstruction, unique segment IDs after gaps, protected output paths and CLI presence.
- [x] Add camera auto-sync using the two discovery reports, automatic crop padding, streaming local OCR, unchanged dense timing and candidate alignment.
- [x] Write original-length automatic clocks, raw reads, candidate alignment and aggregate report. Guard inputs against output path aliases before writing.
- [x] Rebuild the one-file bundle and verify exact source parity.
- [x] Run the full synthetic suite, including standalone execution, then run local inference and aggregate camera diagnostics.

## Review focus

- A discovery report from an incompatible export must fail on frame-count/rate disagreement.
- First-half stoppage clocks overlapping second-half minutes must remain ambiguous.
- Conflicting automatic clock regions must not be silently selected.
- Decoder errors must never shift original frame IDs.
- Automatic output paths must not replace videos, discovery inputs or historical pilot outputs.

## Ledger

- Source modules extracted verbatim from the user's current single-file bundle. Current tests fetched through the authenticated GitHub connector at commit 3a1c860.
- The current workspace is a separate non-git development copy; no branch/worktree mutation applies. Original source and outputs remain untouched during implementation.
- Baseline: 124 tests, 122 passed, one opt-in integration skipped, one hardlink test blocked by the Windows sandbox. Temp-directory and Tesseract model-path environment issues were identified and resolved without changing inference code.
- Pre-flight: planning produces source-specific windows; decoding consumes windows with original indices; dense timing consumes OCR reads, never the sparse interpolations. Existing alignment consumes unchanged ClockTime objects. No incompatible shared interface found.
- Task 1: complete. Initial 10 tests failed for missing functionality, then passed. Generated two-video OCR recovered a known 50-frame offset without manually selected crops.
- Final review: fresh code reviewer identified six correctness/output-safety findings. All six received failing regression tests and were fixed: explicit added-time half semantics, absent-coverage ambiguity, active-job-only OCR crops, dedicated owned output directories, complete-generation publication with rollback, sparse observation bounds, and duplicate camera input rejection. One additional ownership test protects unrelated files placed inside an otherwise owned directory.
- Ruling: ordinary broadcast elapsed clocks at or beyond 45 minutes remain unassigned without an independent half anchor or explicit added-time notation. Missing sparse coverage is not half evidence. This costs second-half coverage until an independent automatic period anchor is implemented.
- Final: minor (deferred): local Tesseract subprocess timeouts can still produce a CLI traceback; outputs remain protected by staging.
- Local integration exposed a decoder inactivity-timeout defect: long deliberately unselected stretches were treated as stalls although original frames were advancing. A generated long-tail test failed before a progress-aware heartbeat fix and passed afterwards. The 120-second operational stall budget and all OCR/alignment thresholds were preserved.
- Current verification: 145 tests ran, 144 passed, the optional full-index test skipped. Final run used the standalone entry point for the supported integration tests. Bundle has exact parity across all 12 source modules and passes Python 3.9 syntax parsing.
- The first completed dense draft produced no bounded clocks. Investigation found an implementation omission relative to the approved reuse-existing-OCR design: raw-only OCR bypassed the existing fixed source-polarity, border and weak-read retries. Restored that predetermined recipe, rather than changing cutoffs or selecting a new treatment on challenge footage. Generated PGM tests establish byte-for-byte preprocessing equivalence with the original FFmpeg recipe and exercise the existing conflicting-retry policy. The initial aggregate result is retained locally as initial-dense-ocr-summary.json; a single corrected inference run follows.
- Updated final synthetic suite: 148 tests ran, 147 passed, one optional integration skipped. All 12 bundled modules individually pass Python 3.9 AST parsing. Possession core, dense timing estimator, fusion weights and input adapters match the original bundle exactly.
- Active corrected real inference: exec session 54323; stdout/stderr in automatic-run-final.log. Output destination ../analysis/automatic-sync-verified (complete generation replaces the initial zero-clock result only after both cameras finish). Do not start a duplicate run. Pending: wait for completion; run analyse_camera_outputs.py with this sync folder; render_analysis_report.py; verify row counts/index invariants; install the tested single file and completed outputs into the original Desktop run-files folder; retain the original Python source backup in this workspace.
- Corrected inference session 54323 completed with exit 0 and both full decoded-frame counts verified. Each camera supplied 1704 OCR samples; 117 tactical and 229 broadcast readings passed the unchanged .7 gate. Neither formed bounded dense timing; alignment consequently has zero eligible candidates. This is an unsupported inference result, not a successful synchronization or an accuracy result. Do not rerun or change parameters on challenge feedback.
- Final local aggregate audit completed. Tactical: 199319 video/tracking/homography rows, 64643 missing-ball frames within 158857 grading frames. Broadcast: 164487 video frames versus 164488 tracking/homography rows; 65.809% valid homographies. No rows were repaired or shifted; without eligible timing, joint ball/geometry opportunities remain unassessed.
- Task 2: complete as implementation and local diagnostics. Verified original-index output lengths 199319 tactical, 164487 broadcast and 199319 alignment. Installed version 2026.11.05-automatic-sync plus six hash-verified automatic outputs and aggregate JSON/Markdown into the original Desktop run-files folder. Historical clocks, alignment and possession outputs were preserved. Original source backup remains football_pipeline.original.py in this workspace. No GitHub push was performed.
- Remaining project work: externally validate the automatic crop/OCR route before selecting any changes; independent period anchors, temporal replay validation, longer-gap possession handling and general live/dead inference remain unfinished.
