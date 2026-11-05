# Verification record

## Tactical experiment and automatic synchronization, 5 November 2026

- Publication checkout verification: `C:\Python314\python.exe -m unittest discover -s tests` ran 183 tests, OK with 4 skips, using absolute `FOOTBALL_STANDALONE`, workspace TEMP/TMP and local OCR dependencies. The skips were opt-in full-index, training-only sklearn and two local-delivery integrations whose protected fixtures are absent. A fresh separate publication training/export run passed all 3 tests.
- Original local-delivery suite: 183 tests, OK with 2 skips (opt-in full-index and training-only sklearn under Python 3.14). The two Windows delivery tests passed there. In a clean publication checkout those two additionally skip because protected output/report fixtures are intentionally absent. They now state that dependency explicitly.
- Separate isolated development check:3 training/export tests passed using Python 3.12/NumPy 1.26.4/SciPy 1.13.1/sklearn 1.5.1. Six CLI tests passed in the football environment using isolated standalone child processes. Production inference imports neither NumPy nor sklearn.
- The standalone bundles 20 modules with exact source parity and Python 3.9 syntax. All 21 external raw source checksums were reverified. Freeze/source checks confirm the selected artifact predates final test scoring and was not refitted. The local 199,319-row output passed official format validation, but was not scored against challenge labels.
- RED->GREEN review regressions cover negative homography errors, dead-label injection in geometry evidence, and tag removal from an identical-input baseline. Delivery recovery was reproduced failing before staging/atomic replacement; recovery and unrelated-file preservation then passed. See [review disposition](docs/four-goal-final-review.md).
- Automatic-sync fixtures check original decoder counts, fixed preprocessing parity, moving overlays, half ambiguity, output aliases and interrupted output publication. Actual camera processing produced no bounded clock correspondence; no replay/live or possession-accuracy claim follows.
- The external benchmark improves the complete provider target. Provider coordinate freezing and active-only/team-share regressions limit scientific interpretation; see [FOUR_GOALS.md](FOUR_GOALS.md). Synthetic tests verify implementation behavior, not transferable possession quality.
- This publication includes code, narrative aggregates and external manifest/model metadata only. No challenge videos, tracking, tags, homography rows, predictions or frame-level diagnostics are committed. Requirements for the tested external-training environment are pinned separately from standard-library production inference.
- The publication executable was rebuilt with exact 20-module source parity and is byte-identical to the installed/tested local file: SHA256 `a09c7c373ea95e3719b24a973cf269057e69def96c7d9529deb5aa795eabbfc3`. The frozen model/source integrity check also passed in the publication checkout. These are local verification results; no GitHub-hosted CI result is claimed.

## Automatic clock discovery, 5 November 2026

- Current suite: 124 tests ran, 123 passed and one opt-in full-index integration skipped. The skipped full-index integration was last exercised for the earlier restart release, not rerun for discovery.
- New discovery coverage: 27 tests, including actual local FFmpeg/ffprobe/Tesseract on a generated clock video with a blank prefix and a clock away from the historical crop. Original sample indices, progressing readings, score exclusion and absence of extracted frame files were verified. A blank video returned zero candidates successfully.
- Parser/temporal regressions cover split tokens, split stoppage-time prefixes and suffixes, weak prefixes, malformed boxes/confidence, freezes, resets, competing clocks, excessive gaps and cumulative box drift.
- One independent whole-change review reproduced source-file overwrite, tolerant decoder frame skipping, cumulative box drift, stoppage-token duplication and invalid probe dimensions. Regression tests were observed failing before fixes. Source/alias output paths are now rejected before scanning. Decoder errors are fatal and all decoded frames are counted before sampling; a damaged generated packet and a full-count mismatch with identical sparse count both fail. Diagnostic logging stays bounded.
- Standalone version `2026.11.05-clock-discovery` contains the same 11 modular sources. Python 3.9 syntax, isolated help/version/guide and generated-video discovery execution are checked. A native Windows run remains unverified.
- Existing possession/fusion thresholds were not tuned. Discovery exports neither dense alignment nor half identity nor possession labels. No challenge assets or ground truth were used in these checks. Match OCR accuracy, replay discrimination and match runtime remain unmeasured.
- Tool interfaces follow official Tesseract documentation: https://tesseract-ocr.github.io/tessdoc/Command-Line-Usage.html and https://github.com/tesseract-ocr/tesseract/blob/main/doc/tesseract.1.asc . Sparse OCR reads stdin and returns TSV; no training is invoked.

## Restart controlled comparison, 2 November 2026

- Routine suite: 96 tests passed; one full-index integration skipped by default. That integration passed separately with `FOOTBALL_SLOW_TESTS=1 python3 -m unittest discover -s tests -p test_controlled_cli.py`.
- The opt-in test generates complete synthetic 199319/164488-frame ATD and homography exports, passes cached alignment through real CLI/loaders, verifies exact 2934-frame published dead context, isolates repair stages and deliberately hidden-ball recovery, and checks existing CSV outputs. It uses no videos or ground truth and does not estimate match accuracy.
- New regressions were observed failing before implementation: phase-wide restart veto, comparison/provenance helpers, missing-ball funnel and shared phase-edge behavior, extended existing diagnostics and --audit-baseline CLI integration.
- Fresh independent source review found no actionable blockers; 1000 randomized inputs reproduced prior legacy Decision fields. Scorer expansion follows the official source's half-local filling policy.
- Rebuilt standalone version `2026.11.02-restart-audit` has exact parity with 10 internal source modules. It passed the full-index integration through the actual standalone entry point, as well as isolated demo/help/version, no-extraction and Python 3.9 syntax checks. Actual updated-script Windows/match outcome remains for the participant's local run.
- General replay detection, general dead-play classification and learned longer-gap possession inference were intentionally not added to this isolated experiment. Known published D context is not a general classifier.

Verified on 1 November 2026, using Python 3.12 in the available environment. Code uses Python 3.9-compatible standard-library APIs; an actual Windows/Python 3.9 run remains unverified.

- `python -m unittest discover -s tests -v`: 29 tests passed.
- `python -m gap_solver demo --out examples/demo-output`: completed. The eight handcrafted scenarios had 147 unresolved frames before bridging and 100 afterwards; 47 inferred frames. These numbers only describe the synthetic fixture, not football accuracy or an expected real recovery rate.
- `python -m gap_solver demo --full-length --out ../format-check`: generated a synthetic 199319-row format fixture.
- Original uploaded `evaluation/validate_submission.py` accepted that fixture with frame IDs 0..199318. Format validity is not prediction correctness. The fixture was not scored against public labels.
- Independent source review found and prompted fixes for stale-owner reacquisition and metadata-order alias mapping. Both have regression tests; follow-up review found no remaining important findings in this scope.

No competition match assets, public labels, or private labels were used to tune the prototype. Real-match recovery, accuracy, runtime and actual-export adapter compatibility remain unmeasured. No automatic live/dead detector or tactical-video recovery algorithm is included.

## Two-camera update, 1 November 2026

- Full suite: 58 tests passed, including original gap behaviour, clock parsing, half separation, tick timing, duplicate/repeated timestamps, frozen-gap segmentation, cyclic/sustained collapsed mappings, geometry, weighted fusion and malformed input regressions.
- Real local FFmpeg/Tesseract integration ran on a newly generated 125-frame clock video. OCR preserved original decoded frame indices, emitted a 125-row dense clock map and produced a bounded fractional timestamp at the expected location. Competition screenshots/footage were not used in this integration test.
- `python -m gap_solver.multicam demo --out examples/two-camera-demo`: completed. Handcrafted tactical uncertainty was 40 frames before fusion, 20 after. The other interval was rejected due to an invalid broadcast homography. This is synthetic behavioural verification, not a real recovery estimate.
- Independent code review prompted regression fixes for malformed clock timelines, cyclic frame reuse, duplicate player geometry and degenerate homographies. Numerical weights are explicitly heuristic.
- Actual camera-overlay OCR, full-match timing precision, replay rejection, coordinate compatibility, runtime, changed possession boundaries and competition-score improvement remain unmeasured. The real-video route is a selected-clip pilot; merging half pilots is not automated. The live/dead classifier remains absent.
