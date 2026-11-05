# Automatic Clock Discovery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Automatically locate progressing clock regions throughout a video without manual game setup.

**Architecture:** Stream original-index grayscale video samples into local sparse Tesseract OCR. Group valid clock detections into conservative candidate segments and expose a separate discovery command, without changing fusion or possession inference.

**Tech Stack:** Python standard library, FFmpeg/ffprobe, pretrained Tesseract English; Pillow only for optional synthetic integration tests.

**Spec:** `docs/superpowers/specs/2026-11-05-clock-discovery-design.md`

## Global Constraints

- Python 3.9+; Windows single-file entry point; no runtime Python dependencies or asset uploads.
- Defaults: 30-second samples, OCR score 0.7, three readings, box IoU 0.5, clock progression tolerance one second, at most one missed sample.
- Discovery is not dense alignment or live/replay verification; no match-data training/tuning.

## Review Focus

- A decoder failure or truncated image must fail rather than silently shift frame indices.
- Multiple clocks/overlapping detections must not silently become a unique verified clock.
- Blank prefixes, clock resets and halftime gaps must not be joined into a timing map.
- OCR timeouts and consumer errors must terminate the decoder and release pipes/files.
- Negative/NaN/zero dimensions and sample settings must fail before external execution.

## Task 1: Candidate parsing and temporal grouping

**Files:** Create `gap_solver/clock_discovery.py`, `tests/test_clock_discovery.py`.

**Interfaces:** `clock_candidates(tsv, width, height, min_confidence=.7)` returns dictionaries with `text`, `seconds`, `confidence`, normalized `roi`. `clock_segments(samples, fps, stride)` consumes ordered dictionaries `{frame, candidates}` and returns candidate segments with sampled readings, union ROI and original frame bounds.

- [x] Write parser/temporal tests for score exclusion, split tokens, spacing, invalid values, progression, freezes, gaps, ambiguity and overlay changes; run discovery-only unittest and observe missing feature failures.
- [x] Implement parser and mutual-unique spatial/temporal association; run the same tests to green and the complete existing suite.

## Task 2: Streaming scanner and CLI

**Files:** Modify `clock_discovery.py`, `gap_solver/multicam.py`; add streaming and synthetic executable tests to `tests/test_clock_discovery.py`.

**Interfaces:** `read_pgm(stream)` returns `(image_bytes, width, height)` or None only at clean EOF. `scan_video(video, stride_seconds=30.0, min_confidence=.7, ffmpeg='ffmpeg', ffprobe='ffprobe', tesseract='tesseract')` returns a JSON-serializable report. `camera discover-clock --video PATH --out PATH` writes one report.

- [x] Add failing PGM/validation tests and generated-video CLI test; confirm failures arise from the missing implementation.
- [x] Implement streamed extraction, sparse OCR and cleanup; register CLI with fixed defaults and progress messages. Return no-clock reports successfully without a crop-selection fallback.
- [x] Run discovery tests and complete suite. Verify generated-video output contains expected frame indices, region, progressing readings and explicit non-fusion status. Verify missing executables produce useful errors.

## Task 3: Bundle, guidance and final verification

**Files:** Modify `football_pipeline.py`, README, RULES, TWO_CAMERA, PROGRESS, VERIFICATION; update the plan and execution ledger.

- [x] Rebuild the standalone SOURCES dictionary from modular sources; version `2026.11.05-clock-discovery`; preserve the one-file interface.
- [x] Explain that external training is conditional, document the two local discovery commands, identify the remaining dense-alignment/replay stages and preserve historical pilot findings.
- [x] Run all tests and standalone generated-video CLI, source-parity and Python 3.9 syntax checks.
- [x] Obtain one independent whole-change review; fix material findings with failing regression tests before code changes.
- [ ] Publish only code/docs/tests to the already authorised private repository with a leased fast-forward and verify remote blob hashes. No game outputs or assets are published.
