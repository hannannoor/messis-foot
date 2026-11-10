# Gap Liveness and Observed Touch Addenda Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans in this chat. No implementation delegation; one fresh reviewer checks the completed code/protocol before scientific scoring.

**Goal:** Apply the fixed long-gap liveness rule and independent observed-only touch amendment without modifying any completed experiment.

**Architecture:** Pure additive gap_liveness.py patches only explicit gap/restart labels inside a new materialisation wrapper. observed_touch.py reuses the archived within-run detector and decoder but clears all touch state on gaps. A new bounded gap-rule driver owns its own immutable receipts and claims.

**Tech Stack:** CPython3.14.5; standard-library inference; existing adapters/NumPy and official metrics for external evaluation only.

**Spec:** docs/superpowers/specs/2026-11-10-gap-liveness-design.md; docs/superpowers/specs/2026-11-10-observed-touch-design.md

## Global Constraints

- Preserve all files existing at a5d5aa3, including old touch sources, results, seals and release bytes. Add new files only, except these two new draft specs.
- Fixed constants: gap >75 frames; baseline25; sample every5th global frame; discard speed>=12; minimum10 players; reference median outside long gaps; strict below-reference stoppage test; restart<=.5m/s, <=250frames.
- Scaling test keeps cap eligibility unchanged, per explicit user clarification. Use written addendum aggregates; missing probe-results.json is not verified. No Stage0 rerun.
- No public-window tuning, challenge per-frame egress, push, merge or promotion.
- 4a before amended touch evaluation; 30 control +30 gap scores maximum. Stop dependent stages on any gate failure.
- Original tested baseline:608 tests,21 environment skips,587 executed; reuse only after verifying exact source identity. Run complete expanded suite with source held fixed before scientific scoring; use normal Windows permissions for existing link tests.

## Review Focus

- Team/id namespace and 25-frame correspondence must not fabricate identity or cross a period barrier.
- Undefined reference or insufficient players must preserve control labels.
- Restart first-frame calculation must use the stated previous observation, not a guessed zero speed.
- Touch bonuses must remain bit-identical neutral on all missing frames and cannot resume after a gap.
- Scientific restarts, mutable receipts, wrong source commits and incomplete case inventories must fail before consuming dependent-stage budget.

### Task 1: Fixed gap-rule pure functions

**Files:** Create gap_liveness.py and tests/test_gap_liveness.py.
**Interfaces:** player_speed_statistics(frames)->tuple[float|None]; long_gaps(frames)->tuple[(start,stop)]; apply_gap_rule(frames,control_labels)->GapApplication(labels,summary,stoppage_gaps,extensions).
- [x] Write exact synthetic tests for all 15 addendum checks plus strict reference tie, cap cutoff, ids, no reference and restart termination cases.
- [x] Run red, implement minimal deterministic standard-library functions, run green, commit.

### Task 2: Observed-only touch amendment

**Files:** Create observed_touch.py and tests/test_observed_touch.py.
**Interfaces:** detect_observed_touches(frames,theta); observed_evidence_rows(rows,periods,usable,observed,events,beta,c_touch); predict_observed_touch(frames,theta,beta,c_touch).
- [x] Write failing tests: no reacquisition event regardless of new position; kink after five observed intervals detected; missing emissions exactly neutral; no owner resumes after gap without new touch; repeated touch-gap parity; no-events/zero-effects release-fixture parity; existing tie/finite/period behavior preserved.
- [x] Run red, implement beside archived code, run green, commit. No new touch scientific scores yet.

### Task 3: Prospective external harm protocol and execution

**Files:** Create gap_liveness_experiment.py, tests/test_gap_liveness_experiment.py, reports/gap-liveness/{freeze,control-reproduction,external-results}.json and bounded case receipts. Private owner/claim/seal registry outside tracked source.
**Interfaces:** freeze/control/external/audit CLI; pure provider aggregation and inclusive gate functions; exact phase inventories and immutable source/input binding.
- [ ] Test integer-label scoring boundary, equal-provider means/overlap exclusion, exact gate edges, missing/duplicate inventory, exclusive claims, immutable seals and source/input drift red; implement and run green.
- [ ] One fresh code/protocol reviewer; one important-fix pass if needed. Run complete suite once with unchanged source; executed count=587+new tests, zero failures. Verify all base tracked bytes and frozen release hash.
- [ ] Commit rule/source/input/runtime/budget freeze before scoring. Complete30 control cases once, reproduce primary natural .551816 and masked .469149; stop on mismatch.
- [ ] Complete30 paired rule cases once, report both regimes, provider gap counts/stoppage counts/relabelled frames. Natural primary loss<=.005 and each provider loss<=.01 gates. Masked descriptive only.
- [ ] Seal, audit without rescoring, commit/report. If gate fails, stop dependent stages and retain original control.

### Task 4: Conditional Metrica and challenge checks

**Files:** Add separately frozen source/acquisition/reference adapter, synthetic tests and bounded reports only if4a passes.
**Interfaces:** canonical25Hz MotionFrame and integer event reference; pure fixed gap module from Task1 unchanged.
- [ ] Pin public Metrica source revision/files for all three sample games; commit reference normalization/alignment before scores; validate on synthetic events/track records first. No formal dataset licence is asserted; acknowledge source and circularity.
- [ ] One matched control/rule evaluation per game; stop and report if sample mean spell F1 declines. No adapter amendment from observed scores.
- [ ] If permitted by gates, execute challenge self-consistency once, aggregate egress only. Stop if D share>60% or zero stoppage gaps. No rule adjustment from aggregates.
- [ ] Record recommendation, stage budgets and limitations; request explicit Stage5 go-ahead before release/public-window checks.

### Task 5: New observed-touch evaluation, conditional continuation

**Files:** New prospective experiment protocol/registry, never change original touch_evidence freeze/results.
- [ ] After the priority gap goal/gates and required user direction, declare unchanged12-config grid, split, jitter seeds and safeguards for the observed-only hypothesis in a new freeze before any scoring.
- [ ] Execute development/confirmation once under new budget, independent of the gap rule. Combined-parity test only if touch outcome Accept.
- [ ] Preserve all outcomes; no push/merge/promotion.
