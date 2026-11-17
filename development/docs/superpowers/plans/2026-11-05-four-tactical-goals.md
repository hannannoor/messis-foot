# Four tactical goals implementation plan

> For agentic workers: use superpowers:executing-plans inline, TDD for production changes, and one fresh whole-change review before delivery.

**Goal:** Complete the four user-approved tactical-only workstreams with measured evidence and limitations.

**Spec:** ../specs/2026-11-05-four-tactical-goals-design.md

**Architecture:** Separate external reference loading and scoring from portable inference; keep label fields out of features. Preserve existing inference as baseline. Use an externally selected rule/policy/model, freeze before held-out evaluation, then run local challenge inference once.

**Tech stack:** Python 3.9+ standard library for production; installed NumPy/Pandas and optional installed sklearn for external development; XML streaming and official metric code.

## Global constraints

- No challenge GT, video checking, manual game data, fitting/tuning from challenge diagnostics or external upload of challenge assets.
- Fixed external match split in the design; licensed acquisition/checksums and provider-reference qualification mandatory.
- Keep H/A/D/X, original challenge indices and current baseline route. Do not apply the disputed fixed D interval.
- One source-file delivery, no runtime sklearn dependency, no camera work.
- Unknown reference states remain excluded; whole periods and official X fill must not cross halftime.

## Tasks

### Task 1: External data and exact scoring

Files: gap_solver/external.py, gap_solver/benchmark.py, tests/test_external.py, tests/test_benchmark.py, development acquisition utility, vendored official metric + MIT licence.

- [x] Acquire the seven declared matches and verify primary-manifest checksums and attribution.
- [x] RED tests: raw label-code mapping, features independent of reference changes, correct pitch scaling/home identity, frame/period gaps, malformed XML, half boundary isolation, official metric parity and all-X handling.
- [x] Implement strict streaming adapter with cached feature/evidence arrays and a reproducible manifest. No target fields as features or only_alive filtering.
- [x] Implement benchmark against the exact official scoring module; run baseline on development/validation only, save machine-readable reports and error categories.

### Task 2: Diagnose and implement a validated improvement

Files: gap_solver/tactical.py or temporal policy module, optional exported gap_solver/tactical_model.py, development training/selection utility, tests/test_tactical.py.

- [x] Inspect external development errors; choose the contained candidate family from the approved alternatives and record the reason.
- [x] RED tests for flight/occlusion, new owner confirmation, explicit stoppage evidence, missing-opponent/ball, conflict, period resets and stable deterministic inference.
- [x] Implement candidate with portable model/policy metadata. Compare only on development/validation; report coverage and newly resolved correctness alongside spellF1.
- [x] Freeze selection, parameters and checksums before test scoring. Score final held-out matches once, record both improvements and regressions. No test-driven retuning.

### Task 3: Reduce undecided intervals and deliver

Files: tactical CLI, standalone bundle builder, tests/test_tactical_cli.py, local comparison report, FOUR_GOALS.md.

- [x] RED tests for no fixed-D shortcut, complete original row indices, uncertainty accounting, output protection, CLI and bundle parity.
- [x] Run the frozen approach on challenge tracking/automatic tags once, without reading video or GT. Compare X, causes, newly assigned frames and scorer-expanded behavior; mark accuracy unmeasured.
- [x] Run appropriate full suite, generated fixtures, Python 3.9 source parsing and a fresh code review. Fix important findings with regression tests.
- [x] Document each goal's reasoning, solution, results, limitations and actual completion status; install tested source and reports locally with backups and hash verification.

## Review focus

- Label-field leakage through external metadata, filters, splits or temporal features.
- Unknown ownership silently converted to away; absent tracking silently converted to D.
- Half boundaries and annotation holes changing X fill or matching.
- Holdout/challenge feedback reused for model selection.
- Coverage increases that conceal errors, domain shift or lack of support.

## Ledger

- This is the existing isolated non-git workspace; no worktree/branch mutation applies. User explicitly authorized completing the four goals after accepting tactical-only direction; repeated design approval is unnecessary under the session's autonomy instructions.
- External-reference and metric audits performed independently using the parallel-agent skill; no challenge data/GT were opened by agents. Primary Figshare licence CC BY 4.0 verified before data download.
- Source and prior successful automatic-sync delivery remain available; make a pre-tactical backup before new code.
- Pre-flight: external loader separates features/references; benchmark consumes references only for scoring; portable inference consumes features only; CLI consumes the frozen exported policy. Scoring period separators are evaluation-only, never production rows.
- Task 1 acquisition: 21 primary-manifest files (2.63 GB) acquired with verified MD5; features and reference cached separately for all seven predeclared matches. No held-out score opened. Eleven new adapter/metric tests were observed failing before implementation, then passed.
- External baseline on development: spellF1 .3420–.3848, X 61.02–65.64%; validation J03WQQ spellF1 .4297, macroF1 .4059, X60.10%. No D predictions; 8768–12779 decided development frames per match incorrectly call an inactive reference frame H/A. Duration/support and opposing-anchor intervals dominate X. This supports a compact joint state model plus bounded continuity rather than camera work.
- Builder choice, fixed before candidate scores: installed sklearn DecisionTreeClassifier candidates depth {4,6}, minimum leaf {125,500}; leaf-support gates {.8,.9,.95}; stable-run lengths {6,12} frames (24 configurations). Maximum retained-owner gap and same-anchor bridge are both 2 seconds. Training uses natural and a deterministic 30% ball-mask augmentation; masks use seed1729 and durations 5/15/50/125 frames, independent of reference labels. Report separate natural and 10/30/50% external stress cases; no mask choices derived from challenge missingness. Select using validation only and the predeclared safeguards. Production uses exported plain Python tree arrays and geometry-only features, not sklearn or Smart Tagging.
- Development dependency finding: installed base numpy1.26.4 was incompatible with its scipy1.18.0. Added scipy1.13.1 only to workspace .training-deps, preserving all environments. With PYTHONPATH pointing to that isolated overlay, sklearn1.5.1 imports and its portable-tree parity test passes. Production does not import these training dependencies.
- Final delivery: 31-node depth-four external-only tree selected on J03WQQ, frozen before final tests (artifact be756fce3c52d21fda0b10d8a6026f78f9b7d599298d467d2d6ebc59efe9fd38). Both complete provider-reference test scores improve; no post-test refitting. Natural mean spellF1 .37361 -> .50513, X60.47% ->9.86%. Active-only spellF1 and some conditional/team-share statistics regress; per-label H/A agreement86.36/88.95%.
- Validity audit found99.9993% of inactive external ball positions repeat the prior contiguous frame. This provider artifact limits D/transfer claims. No new post-test gate was invented. Independent review approves only an opt-in experiment; existing default remains. Flight/restart groups are observable/provider proxies, not physical-event ground truth.
- Local frozen inference preserves199319 original rows, excludes disputed D, and reduces X109917 ->89200 (69.192% ->56.151%), unresolved intervals1045 ->509. No challenge accuracy measured, no challenge-driven tuning. Missing-ball and low leaf support explain most residual X.
- Final fresh suite:183 tests, OK with2 skips; separate isolated training/export3 and stdlib CLI6 pass. Exact bundle parity20 modules/Python3.9 syntax. All21 licensed external checksums reverified. Important CLI review findings fixed RED->GREEN; installer partial-recovery regression failed then passed after staging/atomic publication fix. No extra review pass requested.
- Installed and independently hash-checked30 files in the original Desktop run folder, including source backup, qualified report, five inference outputs and provenance/model/metric/diagnostic/test evidence. Delivery manifest and -VerifyOnly check succeeded. All requested workstreams complete within explicitly documented provider/coverage scope; transferable physical D and local correctness remain unverified limitations, not hidden completion claims.
