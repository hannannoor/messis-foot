# Two-camera experiment

User authorised a local clock-alignment and reliability-weighted possession experiment. The supplied display examples both use MM:SS, with different clock crops. They depict different match moments, not an offset measurement.

## Chosen approach and alternatives

Use local OCR of the clock as a candidate time map, then cross-view tracking geometry as an independent gate before fusion. Clock-only matching cannot reject replays with a live overlay. Pure visual synchronisation is a possible later alternative but would require more engineering; averaging labels without alignment is invalid.

Keep original per-camera frame indices. Locate clock-second transitions, estimate fractional match time between consistent ticks, and report timing uncertainty. Reject poor OCR, frozen/jumping clocks, unsupported gaps, duplicate matches, excessive uncertainty and missing geometry. No guessed extrapolation. Half identity must be supplied for the selected clip, not inferred from a potentially ambiguous 45:xx display.

Use the existing possession inference separately for each camera. A broadcast label may rescue a tactical X or replace a weak inferred label only after timing and geometry pass. Weights combine evidence source, homography quality and alignment quality; they are heuristics, not calibrated probabilities. Direct tactical evidence wins unresolved disagreements. Missing broadcast evidence has zero vote. Do not infer D from a missing ball or an invalid homography.

## Modules

- clock_sync.py: clock parsing, tick-based dense timeline and mapping.
- clock_ocr.py: optional local FFmpeg/Tesseract extraction, no Python dependencies.
- fusion.py: geometry checks and transparent weighted votes.
- multicam.py: demo, clock, align and fuse commands; ATD and homography adapters.

## Boundaries

This is an experiment, not a trained ensemble. Real alignment and improvement remain unmeasured. Clock crops from screenshots are provisional normalised presets; the user must verify them on their original video locally. Images and competition assets are not bundled or uploaded. No public labels are used. The existing absent live/dead classifier remains absent.

## Implementation plan

1. Add failing tests for clock formats, second transitions, resets, frozen clocks, half identity and duplicate mappings. Implement clock timeline and matching.
2. Add failing tests for missing/invalid camera evidence, geometry disagreement and direct-versus-inferred votes. Implement weighted fusion.
3. Add a local OCR script and synthetic rendered-video integration check. Expose start/end frame, normalised ROI, OCR stride, executable paths and half selection. Preserve decoded frame indices.
4. Add raw two-camera ATD/homography fusion and a synthetic CLI demonstration. Document unsupported cases and run the full test suite and review before packaging.
