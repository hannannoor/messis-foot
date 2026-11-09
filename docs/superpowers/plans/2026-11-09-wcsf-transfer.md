# WCSF Transfer Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans for native inline execution, task by task, with one fresh-context final review. Checkboxes below are planned work, not execution evidence.

**Goal:** Qualify the pinned WCSF geometry and either retain a structural failure or complete one descriptive three-method audit without modifying the predictor.

**Architecture:** Stream the two source archives into isolated geometry/reference stores; qualify reconstruction using geometry alone. Freeze all code/protocol before ingestion, seal geometry and three predictions before opening reference summaries, then publish strict bounded aggregates.

**Tech Stack:** Existing Python 3.14/NumPy, standard-library SQLite/CSV/ZIP/urllib/unittest, no installation.

**Spec:** `../specs/2026-11-09-wcsf-transfer-design.md`; earlier `../../reference-qualification/evaluation-protocol.md` remains the source-selection proposal, clarified by this concrete design.

## Global Constraints

- Preserve all 309 original predictor-release files, 100 cadence-frozen source identities and the approved whole-path design/plan byte-for-byte. No challenge access, target output, fit, C1, parameter search or labels as inference inputs.
- Only two pinned WCSF archives; no contact, payment, accounts or additional acquisition. Private assets/stores/arrays remain in a dedicated sibling `wcsf-reference`; never print raw rows or publish them.
- Exactly `w0-c32-neutral-missing`, `official-convention-w50`, `matched-input-w50`; no advancement/superiority/population claim. Two halves are one match.
- Freeze complete code, hypotheses, thresholds, methods, scorer and reference mapping before ingestion. No reference statistics or outcome inspection until input qualification/prediction seals. Record first machine reference access at ingestion honestly.
- Failed qualification stops scoring and hands back to the approved C diagnosis. Preserve every failed/aborted generation; do not silently revise on the same outcomes.
- Use existing isolated-copy/hash checkpoint fallback if a native Git worktree remains unavailable. Task checkpoints substitute for local commits; GitHub publication must preserve exact parent history and authenticate as The-leonjr.

## Files and interfaces

Create `wcsf_source.py` (pins, safe acquisition, stream ingest); `wcsf_geometry.py` (input-only reconstruction/grid); `wcsf_reference.py` (evaluation-only consensus/mapping); `wcsf_audit.py` (frozen methods, freeze/stage CLI, scores); `wcsf_report.py` (bounded evidence schema). Create matching `tests/test_wcsf_*.py`, shared `tests/wcsf_fixtures.py`, `docs/wcsf-transfer-results.md` and `reports/wcsf-transfer/` aggregate receipts. Do not modify the old scorer or predictors.

Private interfaces: `SourcePaths` dataclass carries `archives: tuple[Path,Path]`, `geometry_db: Path`, `reference_db: Path`, `access_log: Path`. `GeometryDecision` carries `selected: str|None`, `eligible: int`, `candidate_counts: dict[str,int]`, `failure: str|None`. `CanonicalInput` carries `frames: list[MotionFrame]`, `index: list[tuple[int,int]]` (period, original source milliseconds), and `quality: dict[str,int]`; it never contains labels.

Public reports contain only exact method IDs, strings from fixed enumerations, scalar counts/rates, identity maps and explicitly bounded confusion/IoU aggregate shapes. The reference store and canonical index are private even if a filename is harmless.

## Review Focus

1. CSV row order/duplicates and mirrored player-relative geometry can silently alter distances; Task 2 tests all four interpretations, conflicts, row permutations and ambiguity.
2. Source labels can leak through clock, quality or missing-state decisions; Task 3 flips all labels and proves identical geometry/grid and inference.
3. Ten-to-25 Hz conversion can bridge gaps, extrapolate or invent precision; Tasks 2/3 test exact phase, missing native observations, endpoint membership and mapping.
4. A successful summary may conceal unsupported rates, extra methods or a source changed after scoring; Task 4 tests exact denominators/schema, duplicate JSON keys and source/input tampering.
5. Partial/colliding generations can double-count scientific attempts or overwrite artifacts; Tasks 1/4 test no-clobber paths, failed stages, attempt accounting and sealed-stage resume.

## Task 1: safe source stores and no-clobber acquisition

**Files:** `wcsf_source.py`, `tests/test_wcsf_source.py`, `tests/wcsf_fixtures.py`.

**Interfaces:** produce `acquire(generation: Path) -> tuple[Path,Path]`, `ingest(paths: SourcePaths) -> dict[str,int]`, `validate_archive(path: Path, expected_blob: str, expected_bytes: int) -> str` returning the sole safe CSV member name. `ingest` logs machine reference access and writes separate stores; geometry consumers never receive reference columns.

- [ ] Write fixtures and failing tests: `test_pinned_bytes_and_blob`, `test_rejects_zip_traversal_symlink_encryption_duplicate_and_size_ratio`, `test_existing_generation_never_overwritten`, `test_delimiter_and_bom_unique_headers`, `test_only_geometry_columns_reach_geometry_store`, `test_required_ids_clocks_and_conflicting_geometry_duplicates`, `test_identical_geometry_duplicates_preserve_conflicting_reference_rows`, `test_ids_keep_team_and_clock_span_cap`. Assert all source reference duplicates survive with ordinal keys and geometry remains label-independent. Network is stubbed with local ZIP fixture bytes; assert only the two exact public URLs are accepted and no authentication header is sent.
- [ ] Run `python -m unittest discover -s tests -p test_wcsf_source.py`; expected RED from missing new module/behavior.
- [ ] Implement the interfaces, pins and resource bounds verbatim from the spec. CSV ingest is streaming with batched SQLite transactions, not a full dataframe. Sort/query by typed keys, not source row ordering. Do not report reference values/counters publicly yet.
- [ ] Rerun the same command; expected all tests pass. Save a task source-hash checkpoint and RED/GREEN logs in the plan-owned ledger workspace; do not acquire the real archives.

## Task 2: input-only reconstruction and canonical geometry

**Files:** `wcsf_geometry.py`, `tests/test_wcsf_geometry.py`.

**Interfaces:** consumes `SourcePaths.geometry_db`; produces `qualify(geometry_db: Path) -> GeometryDecision`, `canonical_input(geometry_db: Path, decision: GeometryDecision) -> CanonicalInput`. Only a passing decision can construct inference frames.

- [ ] Write failing tests: `test_four_global_hypotheses_recover_known_geometry` uses >=100 synthetic timestamps with spatially varying ball/player positions to uniquely exercise each interpretation; `test_ambiguous_zero_and_multiple_pass_stop`; `test_quarter_metre_and_99_percent_bounds`; `test_common_eligibility_missing_player_and_coordinatewise_median`; `test_row_order_and_label_perturbations_do_not_select_transform`; `test_center_to_corner_conversion` asserts source center maps `(52.65,34)` and source corners map `(0,0)` / `(105.3,68)`; `test_no_gap_or_endpoint_extrapolation`; `test_clock_span_rejected_before_grid_allocation`; `test_player_membership_changes_not_interpolated`; `test_native_vs_interpolated_endpoints_retained`.
- [ ] Run `python -m unittest discover -s tests -p test_wcsf_geometry.py`; expected RED.
- [ ] Implement four fixed global candidates with all-eligible-timestamp counts, unique passing rule, per-frame consensus/missing handling, and 40 ms per-half grids exactly as the spec. Use stable source player IDs; no anonymous-nearest association. Record input-only aggregate quality and private endpoint provenance.
- [ ] Rerun tests; expected GREEN, with swapped/permuted or reference-perturbed inputs producing the same reconstruction and canonical geometry. Save checkpoint. No real archive access.

## Task 3: reference contract and reference-free fixed inference

**Files:** `wcsf_reference.py`, initial inference functions in `wcsf_audit.py`, `tests/test_wcsf_reference.py`, `tests/test_wcsf_inference.py`.

**Interfaces:** `reference_codes(reference_db: Path, index: list[tuple[int,int]]) -> np.ndarray` returns HADX codes 0..3. `infer_fixed(frames: list[MotionFrame]) -> dict[str,np.ndarray]` returns exactly the three method arrays and accepts no reference. Source labels never affect `CanonicalInput` or `sequence_usable`.

- [ ] Write failing tests: `test_dead_consensus_ignores_owner_disagreement`, `test_alive_owner_conflict_missing_invalid_are_X`, `test_conflicting_duplicate_reference_is_X_independent_of_row_order`, `test_exact_native_before_gap_preserved_but_intermediate_gap_X` (native 0/100/200/500 ms: grid 200 uses its native label, 240/280/320/360/400/440/480 are X), `test_left_interval_mapping_and_missing_native_gap`, `test_periods_are_archive_roles_not_reference`, `test_reference_flip_leaves_all_three_predictions_identical`, `test_control_matches_released_functions`, `test_only_two_w50_comparators`, `test_unsupported_and_period_barrier_behaviour`.
- [ ] Run `python -m unittest discover -s tests -p test_wcsf_reference.py` and then `... -p test_wcsf_inference.py`; expected RED before each interface exists.
- [ ] Implement strict native consensus and fixed left-interval mapping. Control calls unchanged tactical feature_rows/portable support, decode_ball_gap and materialize_abstentions; comparator calls unchanged baseline_predictions w50. Do not call infer_variants (it computes C1) or any fitting routine. Count attempted method calls separately from successfully sealed files.
- [ ] Rerun both commands; expected GREEN and exact equality with released functions on meaningful synthetic full-state/gap inputs. Save checkpoint.

## Task 4: complete freeze, stage seals and strict aggregate evidence

**Files:** remaining `wcsf_audit.py`, `wcsf_report.py`, `tests/test_wcsf_audit.py`, `tests/test_wcsf_report.py`.

**Interfaces:** `source_paths(root: Path) -> dict[str,Path]` includes every checkout source `.py`, model/scorer artifacts and the adapter/reference protocol, including all four wrappers omitted by the earlier cadence freeze. `score_fixed(gt, periods, methods) -> dict` uses existing aggregate/official metrics once per fixed method. `validate_report(value: dict) -> None` validates exact bounded shapes/types/ratios. CLI stages are `freeze`, `acquire`, `qualify`, `infer`, `score`, `verify`; each consumes and verifies prior seals.

- [ ] Write failing tests: `test_freeze_covers_transitive_wrappers_and_protocol`, `test_source_input_or_protocol_change_stops_before_scoring`, `test_all_predictions_sealed_before_reference_summary`, `test_failed_geometry_has_zero_scoring_calls`, `test_resume_reuses_seals_without_new_calls`, `test_partial_or_conflicting_receipts_preserved`, `test_pool_both_halves_counts_not_mean_f1`, `test_wholly_X_half_has_nulls_and_other_half_scores`, `test_absent_class_official_and_supported_macro_conventions`, `test_event_both_absent_null_but_predicted_only_zero`, `test_null_operand_delta_is_null`, `test_support_nulls_exact_ints_and_ratios`, `test_reject_unknown_method_vectors_duplicate_json_keys_and_nonfinite`, `test_attempt_counter_includes_aborted_call`. Use a synthetic two-period integration fixture with state conflicts and gaps, not real WCSF.
- [ ] Run `python -m unittest discover -s tests -p test_wcsf_audit.py` and `... -p test_wcsf_report.py`; expected RED.
- [ ] Implement prospective all-source SHA-256/environment identity, ordered no-clobber private/public stages, strict JSON loading and aggregate schema. Reuse old official scoring; primary match metrics pool period-separated counts, per-half diagnostics are secondary. Unsupported ratios are null with explicit counts. Preserve the old supplementary boundary limitation; use existing run-local pair-typed H/A diagnostic for the named H/A result. Do not use generic legacy boundary matching to claim crossing-X correctness.
- [ ] Run both focused commands and all `test_wcsf_*.py`; expected GREEN. Run full existing unittest discovery once with local TEMP/TMP and FOOTBALL_STANDALONE as in the cadence ledger (Windows link fixtures may need approved unsandboxed execution). Expected zero failures/errors; disclose optional-environment skips. Save exact test/source checkpoint. All source/schema/test implementation must be finished before Task 5.

## Task 5: acquire, qualify, then conditionally audit exactly once

**Files:** private `wcsf-reference/<generation>/`; public `reports/wcsf-transfer/` and `docs/wcsf-transfer-results.md`; plan-owned local ledger.

- [ ] Verify no protected/new target files are inputs, all original/frozen source and C-design hashes match, and private paths are within the authorized workspace. Run `python wcsf_audit.py freeze`; expected a new complete prospective seal, no data acquisition or scoring. Check its full source inventory manually.
- [ ] Run `python wcsf_audit.py acquire`; expected two exact verified ZIPs, separate stores, first machine reference-access log, no raw/state values in stdout, no outcomes. Run `python wcsf_audit.py qualify`; expected either a sealed unique input-only geometry contract and quality counts or a retained structural-failure reason. Never edit the frozen implementation to turn a failure into a pass.
- [ ] If qualification fails, do not run infer/score; write the bounded failure/limitations and hand back to approved C. Otherwise run `python wcsf_audit.py infer`; expected exactly three sealed private prediction arrays. Then run `python wcsf_audit.py score`; expected exactly three completed method scores or an honestly retained incomplete/scoring-failure report; log first outcome opening and permanent used status.
- [ ] Run `python wcsf_audit.py verify`; expected all code/input/geometry/prediction/report identities, permitted method counts and numeric derivations match. Verify structural failure has zero model/scoring calls, or complete result has exactly three planned methods; aborts stay counted. Report every support denominator and uncertainty, not a selected favorable metric.
- [ ] Obtain one fresh final read-only review against this plan/spec and all five Review Focus risks. Fix important implementation findings once with RED→GREEN and the appropriate suite, preserving any already consumed scientific generation. Report any code fix after acquisition as post-run attestation/amendment, never retroactive prospective proof. No automatic rescore.
- [ ] Publish source, tests, bounded receipts and reasoned results as The-leonjr to the existing draft branch via non-force advancement with full-tree verification; no raw/private data. Verify author/account/main/PR1 invariants. Complete this execution goal only after failure-or-result evidence and publication withstand requirement-by-requirement audit; only then set a next goal.

## Self-review and handoff

Dependencies: Task 2 consumes geometry-only Task 1 stores; Task 3 consumes Task 2 canonical index and separate reference store, never vice versa; Task 4 consumes all fixed interfaces; Task 5 alone acquires/scientifically scores. All five review risks have named synthetic tests. The design's numeric/clock/state contracts take precedence over implementation convenience. Native inline execution with one final reviewer continues the user-authorized method; no new user permission is inferred from a planned checkbox.
