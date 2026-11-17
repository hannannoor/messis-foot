# All-State Path Diagnosis Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. The user authorized implementation after planning the missing extension; no new predictor is selected here.

**Goal:** Explain the frozen control's all-state/spell errors on five fixed used cases and recommend at most one later intervention.

**Architecture:** A pure reference-free H/A/D path instrument supplies constrained scores and patch algebra. A separate reference-conditioned analyzer attributes episodes/spell objects and exactly two diagnostic repairs. A guarded runner binds existing inputs, executes each case once in a new lineage and publishes only bounded aggregates.

**Tech Stack:** Existing CPython 3.14.5 Windows x64, standard library, NumPy 2.5.1 and pandas 3.0.5 for existing loaders/metrics, SQLite; unittest. New source grammar remains Python 3.9 compatible, without certifying other runtime environments.

**Spec:** `docs/superpowers/specs/2026-11-09-all-state-path-diagnosis-addendum.md`, additive to the unchanged approved `2026-11-08-ownership-path-diagnosis-design.md`. Fresh builder check asked only about carry eligibility; both diagnostic repairs now explicitly exclude latent X.

## Global Constraints

- Base `8c7be9d33bd3e2bd85f04b4c460608fd52e69b8a`; new branch `codex/all-state-path-diagnosis-2026-11-09` in the existing isolated checkout. Preserve released source/artifact/CSV and original evidence byte-for-byte.
- Exactly SkillCorner 1874553/1886347, DFL J03WOH/J03WOY and WCSF's used two-half match; natural inputs only. No new acquisitions or challenge/public-window access/outcomes in diagnosis/selection.
- Frozen model `363c45c70838b398cd87aee7474d7e281fd392f059a31b85712e312058aaab4d`, w=0, c=32, floor1e-6, float32 tree, H/A/D ties, input-only barriers/unsupported X, separate carry.
- Absolute arithmetic tolerance 1e-6 and relative 1e-10. No parameter or alignment search, refitting, additional oracle variant, new submission route or automatic model promotion.
- Preserve original four-case reporting; WCSF is one separate used case. Cache loaders can parse reference containers before inference; log that honestly. Pure inference/path functions receive no reference.
- Exactly two supported-latent diagnostic repairs: D-involving errors and H/A swaps. GT-X and latent-X/materialized positions stay unchanged. Signed deltas are not additive causal loss fractions or guaranteed upper bounds.
- Source/input freeze before real diagnostics, exclusive run IDs/case claims, no overwrite/resume through partial generations. Read-only verify performs no inference or additional variant evaluation.
- Per-frame traces, oracle arrays, locations, input paths and original private stores remain local. New public JSON passes owned schema plus existing `assert_public_report`; original WCSF logs/seals remain untouched.

## Review Focus

1. Current-emission double counting and nonlocal suffix effects: exhaustive forced-state oracle and same-prefix/different-suffix tests in Task 1.
2. True D, neutral ties, unsupported rows and reference holes: source/reference-isolation and separate carry tests in Tasks 1–2.
3. Greedy spell collisions, overlapping split/merge flags and period pooling: literal toy/count reconciliation tests in Task 2.
4. Reference repair eligibility and non-monotonic signed effects: both repairs exclude latent X and GT X; independent toy expectations in Task 2.
5. Mutable input/source bindings, partial/concurrent runs and disguised array egress: protocol/attempt/schema tests in Task 3.

## Execution ledger and pre-flight

- [ ] Use the installed Superpowers workspace/task scripts where supported; preserve this plan's ledger at `.superpowers/sdd/2026-11-09-all-state-path-diagnosis/` and record every ruling/task checkpoint.
- [ ] Confirm both approved document hashes and frozen release artifact SHA `e8d35e15be9524270bed82352791dc2849087b49b4c2b59c191023954b19eddb`; the last full source suite was 489/19, and source is unchanged at start. Do not repeat it merely for bookkeeping.
- [ ] Pre-flight interfaces: Task 1 PathTables -> Task 2 state/patch queries; Task 2 InferenceTrace/analyze_case -> Task 3 loading/binding; Task 3 verified case receipts -> Task 4 report/review. Record any mismatch before implementation.

### Task 1: Complete-segment reference-free path tables

**Create:** `ownership_paths.py`, `tests/test_ownership_paths.py`.

**Interfaces:** `path_tables(emissions, switch_cost=32.0) -> PathTables`; `constraint_summary(tables,index,reference_owner) -> dict` (legacy H/A R versus 1-R); `state_summary(tables,index,reference_state,comparison_state) -> dict`; `patch_summary(emissions,labels,first,stop,reference_owner,switch_cost=32.0) -> dict` (R=0/1/2).

`PathTables` owns original emission triples, forward scores including current, backward scores excluding current, corresponding cumulative emission sums and integer switch counts, canonical H/A/D string labels, full score and exact recurrence-tie count. State tables have shape (n,3). Normalize with offsets for stable scores and frozen tie arithmetic.

- [ ] **Write tests first.** An independent `itertools.product(range(3), repeat=n)` enumerator computes sum of literal emissions minus cost times adjacent switches for n=1..5, costs 0/1.75/32. For every index/state compare constrained maxima and emission-minus-cost decomposition; compare complete labels/objective to `decode_soft`. Do not derive expected values with the new instrument.
- [ ] Add tests `test_suffix_changes_full_not_prefix_margin`, `test_D_neutral_ties_and_unique_swap`, `test_patch_boundary_switch_algebra`, and invalid empty/dimension/nonfinite/overflow/negative-cost/index/state cases. A fixed patch cannot improve an already optimal path beyond tolerance. State-summary `prefix_before+local+future == full`; local is counted once.
- [ ] **Run RED:** `python -m unittest discover -s tests -p test_ownership_paths.py -v`; expected missing instrument. Fix incidental test errors before product code.
- [ ] Implement the declared signatures with deterministic forward/backward recurrences and constrained decompositions. Use input-only complete segments; this module knows no labels/reference masks beyond explicit post-table queries.
- [ ] **Run GREEN** and existing `test_soft_sequence.py` / `test_ball_gap_policy.py`. Preserve the test logs; commit `feat: add complete-segment path attribution instrument`.

### Task 2: Reference-isolated all-state and spell-object analysis

**Create:** `ownership_diagnosis.py`, `tests/test_ownership_diagnosis.py`.

**Interfaces:** `prepare_inference(frames) -> InferenceTrace`; `analyze_case(trace, reference) -> dict`; `spell_diagnosis(reference, prediction, periods) -> dict`; `diagnostic_repairs(trace, reference) -> dict`.

`InferenceTrace` contains no reference: emission triples, periods, observed/usable flags, latent/final HADX strings, raw state codes, retained-control owner/age and input-only supported segment bounds. Its constructor performs one unchanged head/decoder reconstruction. `analyze_case` alone accepts reference codes 0..3.

- [ ] **Write tests first.** Toy MotionFrames cover period-zero interruption, geometry barriers, observed D, a wholly unsupported block, neutral gaps and a reference-X hole. Change only the reference support mask and require identical trace, source segments and path tables. Compare trace labels to the pure released predictor. Distinguish latent supported errors from final carried errors.
- [ ] Test constant R/P episode splitting, all three error families, agreement/interior/observed support, exact frame reconciliation and patch objective classes. Include a D episode and a materialized-X D error with no fabricated path margin.
- [ ] Test spell counts using literal sequences and the official helpers: no-overlap, split, merge, one-to-one greedy collision, GT-X gap, and separate periods. At each IoU, matched+missed=GT and matched+spurious=pred. Unmatched partitions sum exactly; split/merge flags are explicitly overlapping. Pool integer counts before F1.
- [ ] Test both repairs on `latent='HXDDAA'`, final `HHDDAA`, reference `DDHAXH`: expected supported-liveness repair `DHHAAA`, supported-ownership repair `HHDDAH`. Position 1 (carried) and position 4 (GT-X) remain unchanged in both. Verify signed score/count changes against independent official baseline/repair calculations; do not assume nonnegative or additive deltas.
- [ ] **Run RED:** `python -m unittest discover -s tests -p test_ownership_diagnosis.py -v`.
- [ ] Implement input-only trace generation and post-inference episode/complete-path aggregation using Task 1 interfaces. Keep per-frame/event details internal. Include old pilot raw/final totals, reference-state confusions, boundary support/conditional latency at 12/25, memory associations and the frozen 2s strata with explicit denominators.
- [ ] Implement deterministic spell matching/count partitions, overlap flags and exactly the two repairs named `supported_liveness_repair` and `supported_ownership_repair`. Use official evaluation padding/known runs/X fill; preserve period boundaries and baseline convention.
- [ ] **Run GREEN** plus Task 1 tests; commit `feat: diagnose all-state path and spell-object errors`.

### Task 3: Bound existing-source replay and evidence generation

**Create:** `ownership_run.py`, `tests/test_ownership_protocol.py` and safe aggregate report directory `reports/ownership-path/2026-11-09-natural-v1/`. Add only precise .gitignore exceptions for safe receipts.

**Interfaces:** `freeze(run_id)`, `run_cases(run_id)`, `summarize(run_id)`, `verify(run_id)`; CLI `python ownership_run.py freeze|run|summarize|verify --run-id <new-id>`. Consumes Task 2 trace/analysis functions and existing provider adapters/metric/publication guards.

- [ ] **Write tests first.** Synthetic loader fixtures exercise source/input/model binding, exact five-case membership, case/inference/evaluation claims, output no-clobber, interrupted/existing run IDs, concurrent claims, corrupted persisted receipt, missing/extra cases and source inventory omissions. Mutating reference support changes diagnosis only, never inference. `verify` is asserted not to call prediction or variant scoring.
- [ ] Add egress tests for forbidden keys and arrays hidden in new innocuous keys; only explicitly owned schemas, scalar/count dictionaries and fixed confusions pass. Pin zero-support null behavior and aggregation/count reconciliation.
- [ ] **Run RED:** `python -m unittest discover -s tests -p test_ownership_protocol.py -v`.
- [ ] Implement strict run-ID validation, explicit logical input inventory, AST local-dependency source closure, frozen selection/model/approved-document/prior-result identities, actual environment and prospective source/input freeze. Public freeze contains logical identities/hashes; private mapping/access/attempt logs stay in new sibling `ownership-reference/<run-id>`.
- [ ] Load only known original four cache triples/DFL source pairs and WCSF's retained DB/index/control files. Before deeper reports, reconcile four pilot support/swap/raw-final counts and exact input maps. WCSF index/final codes must equal sealed arrays, and baseline match counts must equal 411 GT /490 predicted and IoU .5 TP233/FN178/FP257; metric tolerance follows spec.
- [ ] Implement one case-at-a-time exclusive attempts and completed aggregate receipts. Record five input-only diagnostic reconstructions, five baseline metric reconciliations and ten reference-only repair evaluations in this new lineage; do not append to historical WCSF logs or invoke its old three-method runner.
- [ ] `verify` checks source/input/report/trace hashes, exact inventory, claims/order, original-baseline parity and public schema without another inference/repair score. Report snapshot/access chronology honestly, including reference container parsing by old cache loaders.
- [ ] **Run GREEN** for the new protocol tests and relevant old guards; commit `feat: freeze and guard bounded ownership diagnosis runs`.

### Task 4: Execute fixed cases, review, report and publish

**Create:** `docs/ownership-path-findings.md`, `docs/ownership-path-review.md`; safe frozen/result/verification receipts. Historical documents and release sources remain untouched.

- [ ] After code/synthetic tests pass, freeze a new named run before real diagnostics. Execute exactly the declared cases. Stop on baseline/source/index/objective mismatch; preserve an incomplete generation rather than adjusting settings or excluding cases.
- [ ] Run `summarize` and read-only `verify`. Reconcile all frame/episode/objective/spell partitions and signed counterfactual deltas; keep provider/case values visible and WCSF separate from the original four-case report. Record exact inference/analytic evaluation counts.
- [ ] Request one fresh whole-change review of mathematics, parity, reference isolation, oracle eligibility, pooling, provenance, egress and scientific claims. Grade by user-visible effect; address Important/Critical findings in one RED→GREEN pass. A required recalculation uses a new lineage and preserves the first one; never silently rewrite outcomes.
- [ ] Run the full suite once after final code changes with native Windows link permissions, TEMP/TMP in checkout .tmp, FOOTBALL_STANDALONE and the existing code-only FOOTBALL_OFFICIAL_CODE set. The source-only official fixture is allowed; the public reference/window is not reopened. Do not repeat a green suite for prose-only changes.
- [ ] Write findings distinguishing optimization decisions from provider truth. Recommend at most one later intervention using all fixed cases, D safeguards and primary spell objective, or state unresolved evidence. Reference-only repair deltas are diagnostic and may overlap; no new predictor or performance gain is claimed.
- [ ] Verify released artifact SHA, both original approved documents, original WCSF result/seals/logs and prior CSV generations remain unchanged. Review exact diff/JSON allowlist. Commit and publish a draft PR against the frozen-release branch as live-verified The-leonjr /277591257; no merge/default change or message to source owners. Preserve recovery ledgers/private data and provide findings/commands/evidence.

## Self-review

All original C mathematical/query requirements map to Tasks 1–2, used-case replay/guards to Task 3, and decision/review/preservation to Task 4. The addendum supplies D families, spell partitions and exactly two supported-latent repairs. Each review-focus failure has named tests. No numerical acceptance threshold is selected from challenge or new outcomes. This plan authorizes diagnostic implementation; a subsequent candidate experiment remains separate.
