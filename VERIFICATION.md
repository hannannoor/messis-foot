# Verification record

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
