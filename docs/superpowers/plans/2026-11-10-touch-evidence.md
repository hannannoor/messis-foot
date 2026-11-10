# Touch Evidence Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans task-by-task, in this chat as the worker. Steps use checkbox syntax.

**Goal:** Test whether deterministic contact evidence improves the frozen possession control under the supplied external-only selection protocol.

**Architecture:** Add pure detector, evidence and decoder modules beside the preserved release. Separate aggregate probes and bounded experiment bookkeeping from inference. Preserve every existing tracked byte.

**Tech Stack:** CPython 3.14.5; standard library for inference and probes; existing external adapters and official metrics for external evaluation only.

**Spec:** docs/superpowers/specs/2026-11-10-touch-evidence-design.md

## Global Constraints

- Base 431d1ec; additive files only; author/committer The-leonjr; no push/merge/promotion.
- Challenge access: local computation, aggregate output only; no public-window access in Stages 0–4.
- theta {3,5}; beta {1,2,4}; c_touch {32,8}; jitter sigma 0.05 m, seed 1729; 25 Hz; R 2.5 m, attribution margin 0.5 m, five-interval windows, 10 s expiry.
- Freeze committed before scoring; development <=216 candidate calls, confirmation <=21; control <=45.
- No protocol amendment, retrial or threshold change after a failed gate without user authorization.

## Review Focus

- Missing/nonfinite and partial player coordinates must fail validation without leaking source rows.
- Flat surprise peaks must yield a deterministic single event; period boundaries must reset velocity and bonus.
- All-missing usable segments must remain excluded even when touch bonuses would favor an owner.
- Exact H/A/D ties and unusable-row splits must preserve incumbent tie order.
- Run restarts must not reuse scientific claims or overwrite receipts.

### Task 1: Baseline and aggregate probes (Stage 0)

**Files:** Create touch_probes.py, tests/test_touch_probes.py, reports/touch-evidence/stage0.json and baseline.json.
**Interfaces:** probe(frames, homographies) -> bounded dict; no references or video.
- [ ] Run full baseline suite, save log, record counts/runtime and release hash.
- [ ] Write synthetic homography scale/run/gap tests, run red, implement numeric Jacobian and run aggregates, run green.
- [ ] Verify raw input paths and hashes against retained release freeze locally; run probes once, read only aggregate JSON. Record pose rule (<100 px median drops pose).
- [ ] Commit source, tests and bounded probe receipts; report stage boundary.

### Task 2: Detector (Stage 1)

**Files:** Create touch_physics.py and tests/test_touch_physics.py.
**Interfaces:** detect_touches(frames, theta) -> list[TouchEvent]; TouchEvent(frame_index, team, kind).
- [ ] Write synthetic tests 1–10 in design: straight/decelerating, attributed/remote/contested kink, sigma .05 jitter at both theta values, on/off-line reacquisition, period reset, H/A mirror, invalid input. Add plateau/partial-coordinate tests.
- [ ] Run unittest discovery for this file; expect missing module/API failure before implementation.
- [ ] Implement deterministic pure standard-library functions; no I/O/references.
- [ ] Run targeted tests and commit; if declared jitter test fails, preserve it and stop.

### Task 3: Evidence and decoder (Stage 2)

**Files:** Create touch_decoder.py, touch_evidence.py, tests/test_touch_evidence.py.
**Interfaces:** decode_variable(emissions, periods, usable, costs) -> labels; evidence_rows(rows,periods,usable,events,beta,c_touch) -> (rows,costs); predict_touch(frames,theta,beta,c_touch,events=None) -> ReleasePrediction.
- [ ] Write tests 11–18: >=200 randomized constant-cost parity cases including ties/splits, release-fixture full parity, exact expiry/reset/missing bonus, H–A–H mechanism, invalid parameters/finite rows, import isolation, determinism, release hash preservation.
- [ ] Run targeted tests red, implement new modules without editing incumbent, run green.
- [ ] Run whole suite; executed count must equal baseline plus all new executed tests. Commit and report stage boundary.

### Task 4: Frozen external protocol and evaluation (Stage 3)

**Files:** Create touch_experiment.py, tests/test_touch_experiment.py, reports/touch-evidence/freeze.json and new bounded receipts; private arrays/logs outside tracked source.
**Interfaces:** freeze/run/summarize commands; shared exclusive claims and immutable input/source hashes; aggregate score records reuse score_variant schema.
- [ ] Verify exact 15-case input bindings/receipts, sorted split, historical mask and metrics.
- [ ] Test split/grid/selection/ties/safeguards/budget/restart protection and deterministic jitter red; implement and run green.
- [ ] Commit complete grid/split/seeds/gates/source/input identity freeze before any scoring. Record freeze commit in results.
- [ ] Reproduce control across 15 matches, natural and mask30: 0.551816 and 0.469149 to six decimals; stop on mismatch before candidate scores.
- [ ] Evaluate 12 configurations once on six development matches/three regimes. Reject if none eligible; otherwise choose highest natural equal-provider score with specified ties, seal selection before confirmation.
- [ ] Evaluate only selected configuration once on seven confirmation matches/three regimes. No extra regimes or versions.

### Task 5: Decision and verification (Stage 4)

**Files:** Create docs/touch-evidence-results.md, reports/touch-evidence/decision.json.
**Interfaces:** bounded provider/regime table, Accept/Inconclusive/Reject and preservation report.
- [ ] Apply exact gain/provider/D-recall/owner-presence/spell-ratio gates; state used-data limitations.
- [ ] Fresh whole-branch review, one test-backed important-fix pass if required, final full suite and byte preservation against base.
- [ ] Commit results/test counts/hashes; recommend control unless Accept. Stop at gate for user's decision. Stage 5 and video recovery are not authorized by this plan.
