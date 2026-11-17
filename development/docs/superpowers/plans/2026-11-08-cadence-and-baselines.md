# Cadence and strong baselines implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans or superpowers:subagent-driven-development to implement this plan task-by-task. These checkboxes describe future work, not completed implementation.

**Goal:** Test one bounded reacquisition-speed correction against the frozen experimental predictor and eight nearest-player/majority baseline variants on 20 declared external development cases.

**Architecture:** New top-level analysis modules derive a reference-free observation sidecar and narrowly corrected feature rows, then reuse the unchanged frozen tree, ball-gap decoder and materialization. A separate reference-free baseline module implements the official algorithm family and matched-input controls. An external-only driver freezes inputs/protocol/source identities, runs local arrays, and emits strictly bounded score receipts and a continuation decision.

**Tech Stack:** Existing Python standard library, NumPy and unittest. No dependency installation; portable modules parse with Python 3.9 grammar.

**Spec:** `../specs/2026-11-08-post-audit-roadmap-design.md`, Workstream A. The user subsequently instructed: finish the plan and execute the next goals, creating each goal only after its predecessor is achieved. Execute natively after the planning goal passes its builder/coverage check; use one independent final reviewer.

## Global constraints

- Preserve release `cee674190775e9356745f461ba1561e9f2a46f7e`, its original 309 files, 47 source and 34 evidence seals, existing CSV generations and Desktop installation. New sources are additive in an isolated checkout/copy.
- No challenge GT/video/raw tracking/prediction inspection, target tuning or new target inference. No head fitting, threshold search or decoder changes.
- Exactly SkillCorner 1874553/1886347 and DFL J03WOH/J03WOY, all seen development. Natural, retain-2/3/5 with per-period offset zero, and existing contiguous 30% seed-1729 mask: 20 cases, 10 variants, at most 200 official aggregate scorings.
- Candidate `bounded-reacquisition-speed-v1`: five canonical rows / .20 s maximum pair, old 50 m/s cap and 12-row rolling mean; change only eligible reacquisition `ball_speed` and its derived `recent_speed`. Preserve all other legacy features. Use 1e-9 s arithmetic tolerance only at the pair-duration upper bound, never in model acceptance.
- Use declared source time only when both endpoints supply finite increasing time; invalid/equal/reversed/too-long declared pairs receive no repair. Incomplete time metadata uses explicitly labeled canonical-grid elapsed time. Do not infer native freshness.
- Keep tree, w=0, c=32, floor=1e-6, input eligibility, neutral missing emissions, unsupported latent X and materialization unchanged. Do not split inference at reference masks/boundaries.
- Per-frame arrays/event locations stay local. Public reports contain named scalars/counts/bounded matrices only, checked by existing egress rules plus the new exact receipt schema. No archive overwrite or seal regeneration to conceal a mismatch.
- A gate pass means continuation of an exploratory candidate, not promotion or independent accuracy. A negative result is a valid completed experiment.

## Review focus

1. Missing observations, true measured zero, duplicate source timestamps and interpolated timing must remain distinguishable — Task 1.
2. A valid endpoint pair must not bridge geometry, eligibility or period barriers — Tasks 1 and 3.
3. A majority baseline must not become a different three-class filter or gain access to reference runs — Task 2.
4. Reference-mask changes must leave inference identical; an incomplete class reference must not produce fake D recall — Tasks 3 and 4.
5. Source/input mutations, resumed partial runs and event arrays disguised as JSON must fail verification without overwriting earlier evidence — Tasks 3 and 5.

## Task 1: bounded velocity feature contrast and maintained mechanism fixture

**Create:** `cadence_features.py`, `tests/test_cadence_features.py`, `tests/cadence_fixtures.py`.
**Read/reuse unchanged:** `gap_solver/tactical.py:16–67`, `gap_solver/motion.py`, `gap_solver/soft_sequence.py:6–9`, `gap_solver/tactical_model.py`.

**Interfaces:**
- `CadenceRow`: frozen dataclass with `legacy: tuple`, `candidate: tuple`, `velocity_valid: bool`, `time_basis: str`, `pair_dt_s: Optional[float]`, `repaired: bool`, `unavailable_reason: str`. Feature tuples have the original 18-column order; local-only fields are never serialized wholesale.
- `cadence_feature_rows(frames: Sequence[MotionFrame], max_gap_s: float=.20) -> Iterator[CadenceRow]`.
- `moving_fixture(count: int=180, stride: int=1) -> list` in the test helper: exact synthetic geometry from the audit, retaining ball every `stride` frames; original finite sample times remain on retained rows.

- [ ] Write RED tests `test_two_m_per_second_reacquisition_is_measured`, `test_true_zero_is_valid`, `test_first_observation_is_unknown`, `test_timestamp_pair_rejected_without_fallback`, `test_missing_clock_uses_labeled_grid`, `test_pair_five_rows_allowed_six_rejected`, `test_no_cross_barrier_or_period`, `test_recent_speed_uses_exact_twelve_rows`, and `test_dense_rows_are_identical`. For stride 2/3/5, repaired pairs have speed 2; row 0 is unavailable. Equal/reversed/nonfinite declared clocks never divide by zero or silently use a grid clock. At .20 s accept, at .24 s reject.
- [ ] Assert candidate columns other than indices 9/10 equal legacy exactly; candidate recent speed is the arithmetic mean of the last at-most-12 corrected speed entries, including legacy zero entries on missing rows. The rolling deque resets on period changes/period-0 exactly like the old generator; quality/usability barriers reset only endpoint-pair memory. Adjacent-observed speed stays byte-for-byte legacy. Valid pairs never cross `not sequence_usable`, geometry-invalid, period-0 or period changes. Unknown rows retain legacy features and an explicit reason. Include a five-row pair starting at 1800 s to test floating subtraction at the bound.
- [ ] Run `python -m unittest discover -s tests -p test_cadence_features.py -v`; verify RED due to missing new module, then implement the interfaces without editing the frozen source.
- [ ] Preserve the original dense H180 / sparse D180 behavior as a baseline fixture check using the frozen tree and existing decoder. Record candidate labels as an experiment result, not an invented pre-run expectation of H180. Verify the corrected features causally match the prescribed arithmetic regardless of whether the old tree improves.
- [ ] Rerun to GREEN and record a task checkpoint with source/test hashes or an isolated Git commit. No external scoring yet.

## Task 2: official-algorithm and matched-input comparator families

**Create:** `cadence_baselines.py`, `tests/test_cadence_baselines.py`.
**Reference:** pinned upstream `starter/baseline.py` and MIT notice at `f8f2629ff1e0985f81d7e59d8413678514ee1530`; fetch source/docs only, never upstream match assets or its evaluation runner.

**Interfaces:**
- `nearest_codes(frames: Sequence[MotionFrame]) -> list[int]`, codes H=0,A=1,no-vote=-1. Use finite ball/player geometry, any available side, minimum squared metre distance; canonical home-before-away raw ties are counted separately.
- `smooth_votes(codes: Sequence[int], half_width: int) -> list[str]`, upstream H/A-only centered vote semantics; no-vote window→D, H/A vote tie→H.
- `baseline_predictions(frames, half_width: int, mode: str) -> dict`, mode exactly `official-convention` or `matched-input`, returns local `latent`, `final` lists and scalar `raw_distance_ties`. Half-width exactly 0,25,50,125.

- [ ] Write RED tests for raw nearest choice, one missing team, no players, missing ball, canonical equal-distance tie, and metre scaling assumptions. Test `smooth_votes([0,-1,1],1)==['H','H','A']` and all-no-vote→D. Compare prefix-sum implementation with an independently written small-window oracle, including truncated edges and half-width 0.
- [ ] Test upstream smoothing parity on synthetic arrays; load only its `smooth` function without running `build`, challenge imports or its script entry point. Preserve attribution. Its raw nearest tie uses source slot order, so explicitly test/disclose the canonical external tie adaptation rather than falsely claiming slot-order identity.
- [ ] Test period reset and reference-free behavior. `official-convention` applies smoothing per input period and ignores the quality gate by design. `matched-input` segments on input usability, maps missing-ball votes to -1, emits X on no-vote windows/barriers, and then uses unchanged structural materialization; unsupported whole periods follow that convention. Reference-X is not a segmentation argument.
- [ ] Run `python -m unittest discover -s tests -p test_cadence_baselines.py -v` RED→GREEN. Verify all four settings are returned, not just a favorably selected window. Checkpoint.

## Task 3: exact protocol, input-only inference and immutable external receipts

**Create:** `cadence_protocol.py`, `cadence_experiment.py`, `tests/test_cadence_protocol.py`, `tests/test_cadence_experiment.py`; future `reports/cadence/` only during execution.
**Reuse unchanged:** completed `next-phase-notes/ownership-council/run_development_diagnosis.py` loading/replay pattern; `ball_gap_candidate.selected_artifact`, `PortableTree`, `decode_ball_gap`, `materialize_abstentions`, external cache loaders, `contiguous_mask`, hash/egress helpers.

**Interfaces:**
- `CaseInput`: dataclass with `cohort`, `match`, `frames`, `reference`, `periods`, `input_paths`. References are available only to post-inference scoring, never feature/baseline functions.
- `case_keys() -> tuple[tuple[str,str,str], ...]`: exactly 20 unique `(cohort,match,regime)` keys; string match IDs in receipts.
- `apply_regime(frames, regime: str) -> list[MotionFrame]`: natural, retain-2/3/5 or mask30-seed1729 only. Use input periods, no reference argument; clear all ball provenance/XY/distances coherently using existing constructors/mask helper.
- `infer_variants(frames) -> dict[str, dict]`: exactly `frozen-control`, `bounded-reacquisition-speed-v1`, and `{official-convention,matched-input}-w{0,25,50,125}`. Each value contains local `latent`, `final`, and scalar diagnostics. Tree probabilities are produced by unchanged `PortableTree`; decoder behavior stays frozen.
- `freeze()`, `run_case(cohort,match,regime)`, `summarize()`, `verify()` in driver; CLI `python cadence_experiment.py freeze|run|summarize|verify`, with exact case arguments for `run` and one worker by default.

- [ ] Write RED tests for exact case/variant inventories, coherent masked fields, stride offset reset only by period, malformed protocol/horizon/window rejection, and identical inference after changing only reference labels/masks. Include an unknown reference island inside an otherwise usable segment; paths remain unchanged.
- [ ] Test fixed-control equality with the released functions on synthetic inputs, including all-missing segments, quality barriers, period-0 and structural carry. Candidate dense/no-reacquisition parity must hold. Compare any vectorized tree scoring with `PortableTree.predict` on every synthetic row and every 257th external feature row; stop on mismatch.
- [ ] Implement verified external loading without running the old diagnostic script wholesale. Bind the original release, all consumed original and new source bytes, model/scorer identities, exact protocol and exact input files. Hash files before and after each case. A fresh output stage is mandatory; a resumed receipt may be reused only if every bound identity/schema matches exactly.
- [ ] Add mutation RED tests: changed source/cache/reference bytes, omitted source inventory, unexpected case/variant, stale freeze, partial receipt, attempted overwrite, raw event arrays and unknown JSON keys. Invalid provenance must fail before scoring/publication. Implement strict stage/receipt validation and atomic no-clobber output.
- [ ] Run Task 3 tests to GREEN on synthetic inputs only. **Do not freeze or run external cases yet.** Task 4 must first complete the metric/gate implementation and exact receipt schema; those source bytes and rules are part of the pre-outcome freeze.
- [ ] Implement the verification that will later compare initial/final release/input hashes and require the complete 20-case/200-scoring receipt inventory. Exercise it on small synthetic receipts now. The actual freeze, external run and final verification belong to Task 5, after all implementation sources are complete.

## Task 4: honest diagnostics and a deterministic continuation gate

**Create:** `cadence_metrics.py`, `tests/test_cadence_metrics.py`.
**Reuse unchanged:** `accuracy_experiment.aggregate_metrics`, `ball_gap_experiment.dead_metrics`, official scorer functions and evaluation-only period handling. The new module owns supplementary diagnostics and gate logic; it does not change official matching.

**Interfaces:**
- `diagnostic_metrics(reference, prediction, periods, sidecars) -> dict`: bounded count/matrix aggregates; truth used after inference only.
- `assess_continuation(receipts: Sequence[dict]) -> dict`: exact Boolean checks plus per-match losses; missing support is explicit, never treated as a perfect result.

- [ ] Write RED fixtures for short/long true spells, H→A and A→H pair-typed events, reference-X edges, unmatched boundaries and absent D support. Spell bins are `<=25`, `26..75`, `76..250`, `>250` canonical frames; report support, matched recall at official IoUs .3/.4/.5/.6/.7, and existing overall score. Events cannot cross reference-X runs. Retain matched/missed/spurious counts and signed matched latency with its denominator; no event positions leave the process.
- [ ] Distinguish `velocity_valid=False` from valid zero; report source/grid timing, pair-duration bins `<=.08`, `(.08,.12]`, `(.12,.20]`, unavailable; unknown metadata does not imply source freshness. Separate neutral, latent-X and materialized counts, and unique-preference exchange changes from ties. Apply full-input exchange only to control/candidate for sensitivity; it does not add official scoring cases.
- [ ] Implement seven aggregate checks versus frozen control: natural equal-provider spell F1 preserved; natural equal-provider accuracy preserved; natural DFL D recall preserved; cadence equal-provider spell F1 improved; cadence known-live false-D rate reduced; masked equal-provider spell F1 preserved; masked DFL D recall preserved. Cadence combines the three stride means within match, then match means within provider, then equal provider means. False-D rates use known-live denominators, not counts alone. Missing D support blocks the applicable DFL check; SkillCorner D recall is null and never pooled as success.
- [ ] Add tests where the mean passes but one match loses natural/cadence spell F1 or any DFL D recall. Emit `aggregate_gate_passed` and `per_match_review_required`; `automatic_continuation_allowed` is true only when aggregate gates pass and no such per-match loss exists. Use exact metric comparisons with no acceptance tolerances. Record all deltas without deciding after the fact that a small loss is acceptable.
- [ ] Run RED→GREEN; integrate the diagnostics into the **future** receipt/summary schema before any external freeze or run. All ten variants remain visible, with no chosen baseline winner. Exercise the complete driver→metric→gate path synthetically. Report physical/ontology ambiguity and reused-cohort status prominently.

## Task 5: final review, findings and next-goal decision

**Create:** `docs/cadence-and-baselines-results.md`, `docs/cadence-and-baselines-review.md`, final aggregate proof under `reports/cadence/`.
**Consumes:** all verified Task 1–4 artifacts. **Produces:** reproducible positive or negative experiment report and one concrete next-goal recommendation.

- [ ] Run all new focused tests, then the appropriate full suite once after Task 1–4 implementation settles. Capture failures, executed counts and skips; compare frozen source hashes to the original release. No redundant full-suite reruns after documentation-only edits.
- [ ] Freeze the now-complete feature, baseline, driver, metrics, gates, exact receipt schema, protocol and input identities **before** opening external outcome reports. Execute the sole external run: at most 20 cases, one at a time, keeping per-frame arrays local and printing brief case progress only. No extra windows, horizons, seeds, fits or cost search. Later review cannot silently change these rules or rewrite these receipts.
- [ ] Run `python cadence_experiment.py verify`; require 20 cases/10 variants, strict egress, fixed identities and deterministic summary replay. Recompute all summary means from case receipts. Check Python 3.9 grammar for new portable modules.
- [ ] Request one fresh whole-change reviewer for clock/velocity arithmetic, original feature parity, baseline fairness, reference isolation, source binding, event metrics, gate logic and scientific claims. Fix important findings with targeted RED→GREEN verification; preserve an honest inability to judge provider truth.
- [ ] Write findings covering mechanism reproduction, every regime/provider/match, baseline families, candidate tradeoffs, uncertainty/short-spell safeguards and limitations. A failed candidate is not promoted or tuned. Update the roadmap status without overwriting the old whole-path design/plan.
- [ ] Complete this execution goal when the bounded experiment/report is verified, regardless of whether its hypothesis succeeds. Only then create the next goal: bounded independent source qualification, followed by the original frozen-control whole-path diagnosis. A documented prerequisite repair takes precedence if verification failed; do not claim an unverified experiment complete. No nested simultaneous goal records.
- [ ] For a later GitHub publication: authenticate as The-leonjr, allowlist sources/docs/bounded receipts, verify Git-visible final bytes, and preserve existing PR state unless integration is explicitly requested. No target arrays or original omitted audit script may be fabricated.

## Plan self-review

Tasks 1–2 are independently testable algorithm units; Task 3 owns exact inference/provenance; Task 4 owns post-inference diagnostics and decisions; Task 5 owns the complete pre-outcome freeze, sole external run, whole-change verification and reporting. The builder check caught and resolved an earlier ordering problem that would have run Task 3 before Task 4's metrics were frozen. All five Review Focus conditions have tests. No step instructs an implementer to tune against outcomes. The experiment may finish with no improved candidate; the user still receives a concrete answer and the next justified action.
