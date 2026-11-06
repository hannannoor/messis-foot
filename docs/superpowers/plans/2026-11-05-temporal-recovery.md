# Temporal Possession Recovery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans for native implementation task-by-task; TDD for new behavior, and one fresh whole-change review before final scoring/delivery. Steps use checkbox syntax.

**Goal:** Test whether player context recovers missing-ball possession on an independent provider, retaining uncertainty and the existing frozen baseline.

**Architecture:** New motion records and adapters preserve player information independently of ball availability. A separate reference/evaluation layer isolates provider labels. Fit/export a compact H/A ensemble and temporal decoder externally; add a separate experimental local command only for a passed frozen candidate.

**Tech Stack:** Python3.9+ standard-library runtime; existing Python3.12 NumPy/pandas/scikit-learn/SciPy training environment and isolated compatible SciPy overlay. No GPU or new hosted inference.

**Spec:** `temporal-recovery-design.md` (user approved tracking-first design via the asynchronous question on5 November2026).

## Global constraints

- Preserve old frozen artifact and six source hashes; isolated working copy based on published commit `c4643e7d7680284776ad4a3789d920ba489dc408`.
- No challenge video/GT checks, hand game data, challenge training/tuning or asset uploads. Only automatic local aggregate diagnostics.
- Pinned SkillCorner revision/split from `skillcorner-source-protocol.json`; test scores stay unopened until freeze. Detected-only primary features; reference absence is X, never D.
- Canonical25Hz scorer mapping preserves native10Hz indices and known-reference holes. No oracle in-play filtering during inference.
- Production runtime standard library. Existing source/default/output preserved; new local output is experimental because independent D transfer remains unvalidated.
- Native execution is the builder's routine method choice: tasks share interfaces, the user approved implementation, and the separate provider agent hit a service limit. Blind audit and builder check are complete; final fresh review remains required. No repeat scope approval is needed.

## Review focus

1. False fresh observations from extrapolation or interpolation; never bridge a missing native detection.
2. Label-dependent features, filters or event outcomes; permuting reference fields must leave features identical.
3. Same-team endpoints hiding an opposing spell; do not force the interior to one owner.
4. Unknown periods/annotation holes silently merging spells or becoming D.
5. Portable tree/logit/calibration/decoder parity and local output alias protection.

## Task1: Motion evidence and independent-source contract

**Files:** `gap_solver/motion.py`, `gap_solver/skillcorner.py`, `acquire_skillcorner.py`, `tests/test_motion.py`, `tests/test_skillcorner.py`.

**Interfaces:** `MotionFrame(Frame)` adds `home_xy`, `away_xy`, native/interpolated availability metadata; `load_motion_atd(meta_path,raw_path,quality_path,n_frames,blocks)` returns records preserving all source rows. `load_skillcorner(metadata,tracking,phases,detected_only=True)` returns `MotionMatch` with frames, canonical/native mapping and separate reference array. `save_motion_cache/load_motion_cache` preserve feature/reference separation.

- [ ] RED: ATD retains players when ball is missing; validates every player slot even then; invalid homography clears all geometry; no dead shortcut/tags.
- [ ] RED: strict home/away mapping; finite extrapolated coordinates excluded in detected mode; canonical25/native10 interpolation never crosses missing detections, unknown periods or noncontiguous frames; categorical references use left-closed/right-open intervals; conflicts/absent phases stay X; reference permutation leaves features unchanged.
- [ ] Implement records/adapters and immutable acquisition receipts (git blobs/LFS SHA256+size, MIT attribution); run the two targeted unittest modules to GREEN.
- [ ] Acquire/cache the20 declared matches without scoring final test; reverify cached objects and preserve invalid/interrupted downloads rather than treating them as complete.

## Task2: Benchmark, error strata and frozen old-model transfer

**Files:** `gap_solver/temporal_metrics.py`, `diagnose_motion_gaps.py`, `run_skillcorner_baseline.py`, `tests/test_temporal_metrics.py`.

**Interfaces:** `gap_strata(frames,reference,predictions)` returns aggregate duration/anchor/visibility/support counts; `compare_temporal(reference,before,after,periods,frames)` wraps unchanged official scoring and per-class recovery/short-spell metrics. No mutation of `official_metrics.py` or `benchmark.py`.

- [ ] RED: H/X/H reference yields two separate spells; predicted X is a miss for raw recall; a .2–2s hidden opposing spell is matched only at IoU>=.5; natural vs synthetic gaps/support remain separate; no phase holes are D.
- [ ] Implement metrics and report known-reference denominator/coverage, false switches, boundary timing and risk-by-duration; targeted unittest to GREEN.
- [ ] Run old frozen versus legacy geometry on development only; save per-match and mean transfer results, natural observation audits and baseline same/opposite-anchor errors. No final-test inspection.
- [ ] Preserve automatic challenge availability aggregates separately. They are descriptive and may not choose model/policy parameters.

## Task3: Externally selected model, portable ensemble and temporal decoder

**Files:** `gap_solver/temporal.py`, `gap_solver/temporal_selection.py`, `select_temporal_recovery.py`, `tests/test_temporal.py`, `tests/test_temporal_selection.py`.

**Interfaces:** `motion_feature_rows(frames)` yields a fixed geometry/count/history schema; `PortableBoosted(model).score(row)` reproduces sklearn logits; `decode_team_sequence(scores,frames,policy)` returns posterior/decisions with hard period/quality/anchor boundaries; `infer_temporal(frames,artifact,baseline)` changes eligible X only.

- [ ] RED: exact portable model logits/probabilities; home/away swap symmetry; no input-label use; no bridge across D/period/quality boundaries; missing opponent/insufficient players remains X; future evidence can support an internal short opposing spell even with same-team endpoints.
- [ ] Implement forty depth-two trees/minimum leaf150, reflection/team-swap augmentation, scalar calibration fitted only on two calibration matches, and training-derived switch prior. Targeted GREEN including synthetic hidden-turnover cases.
- [ ] Train on eight development matches with natural and declared30% contiguous masks; compare geometry/current frozen/last-owner/two-sided/motion/no-decoder/decoded variants. Use calibration then the27-policy validation grid exactly as specified. Report H/A recovery separately and require declared short-spell support.
- [ ] If motion fails, retain the measured comparison and its rejection. Only a genuinely eligible simpler rule may proceed. If none qualifies, freeze best validation challenger as rejected before final diagnostic test; never promote it from lucky test results.

## Task4: Review, freeze, final evaluation and conditional local delivery

**Files:** `gap_solver/temporal_cli.py`, `gap_solver/temporal_model.py` only for passed export, `evaluate_temporal_final.py`, `export_temporal_runtime.py`, `build_standalone.py`, `tests/test_temporal_cli.py`, `TEMPORAL_RECOVERY.md`.

**Interfaces:** separate `temporal run` CLI consumes local automatic tracking with the frozen artifact, writes a dedicated experimental output folder with original indices, confidence/evidence metadata and explicit local-accuracy/full-state-validation flags. Existing tactical/default routes remain unchanged.

- [ ] RED: preserve every index, reject output/input aliases and unowned directories, no fixed D/tag injection, custom artifact labelled unverified, invalid/failed acceptance artifact cannot claim validated runtime, no dependency on NumPy/sklearn in portable inference.
- [ ] Implement new route/bundle with exact module parity; targeted GREEN and isolated standard-library command checks.
- [ ] Complete full suite and a fresh whole-change scientific/code review before final freeze/test. Fix important findings with RED->GREEN regressions; review once, no endless re-review loop.
- [ ] Freeze artifact, calibration, policy, source hashes and candidate eligibility BEFORE final scores. Evaluate eight test matches once, plus declared stresses and explicitly seen DFL regressions. Preserve failures and conditionals.
- [ ] Apply a passed frozen candidate locally once in separate experimental output; otherwise preserve old inference and explain rejection. No local-driven retuning.
- [ ] Document baseline transfer, candidate comparison, per-class/support/short-turnover metrics, coverage, limitations and all gate outcomes. Publish only source/docs/licensed metadata, not challenge assets or per-frame outputs. Verify remote hashes/PR state if publishing.

## Current evidence and ledger

- [x] User approved the tracking-first design, including experimental local scope.
- [x] Initial no-history audit memo preserved with hash; independent builder check resolved four material questions.
- [x] Pinned all20 source LFS objects (1,823,448,331 tracking bytes), licence and pre-score split; first development match downloaded and hash-verified for schema research only. No model score yet.
- [x] Read-only challenge availability research found59,821 unresolved missing-ball frames with at least3 available players per side, but freshness is unverified and most missing intervals are long. These counts are not a recovery forecast and will not change the approved grid.
- [ ] Task1 through Task4 implementation/evaluation/delivery remain outstanding; the goal is active.

Self-review: each spec deliverable maps to a task; method-specific mathematical choices are explicit builder calls; primary source/reference/time invariants and all five review risks have test steps. Numeric gates and the experimental D limitation stay in the approved spec and apply to selection/evaluation rather than becoming a challenge coverage target.
