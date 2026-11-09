# Whole-segment ownership diagnosis implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans or superpowers:subagent-driven-development to implement this plan task-by-task. Checkboxes are future implementation steps, not claims of completed code.

**Goal:** Explain the frozen candidate's H/A decisions against provider references using complete-segment scores, without changing a predictor or fitting a head.

**Architecture:** A reference-free dynamic-programming instrument computes constrained path scores and deterministic emission/switch decompositions on input-only segments. A separate external-only driver supplies evaluation labels after inference, verifies exact release replay and exports bounded aggregates. Existing inference, carry, source/model/evidence guards and official metric helpers remain unchanged.

**Tech stack:** Existing Python standard library and NumPy for offline analysis, unittest; no new dependencies. Added sources must parse under Python3.9 grammar. No new runtime/submission route.

**Spec:** `docs/superpowers/specs/2026-11-08-ownership-path-diagnosis-design.md`, approved by the user8November2026. Source proposal and completed pilot evidence: `../next-phase-notes/ownership-council/`.

## Global constraints

- This task delivered the diagnosis and plan only. Execution of this plan is deferred until the separately requested full adversarial repository audit has been reviewed and priorities confirmed. Do not train a model or run new target inference under this plan.
- Preserve released commit `cee674190775e9356745f461ba1561e9f2a46f7e`, its309files, current CSV generations, Desktop installation,47pinned sources and34pinned evidence files.
- At execution, use Superpowers isolation: native worktree when available, otherwise an exact hash-verified sibling copy because the current workspace has no local Git repository. Retain recovery logs if no Git history exists. This setup belongs to Task1, not a separate project.
- Exactly four seen development cases, natural inputs: SkillCorner1874553/1886347; DFLJ03WOH/J03WOY. No mask generation, clock/label-lag fitting, cost grid, head fit, target GT/video, hand labels or new dataset downloads.
- Frozen tree, neutral missing emissions, w=0, c=32, floor1e-6, input periods/eligibility, wholly unsupported latent X and separate carry remain unchanged. Never use reference masks or boundaries to split inference segments.
- Deterministic predecessor/successor tie order H,A,D; compare accumulated objective/decomposition within absolute1e-6and relative1e-10 numerical tolerance. These are arithmetic tolerances, not model-acceptance thresholds.
- All per-frame arrays and episode/event locations stay local. New public JSON goes through `assert_public_report`; only named scalar/count aggregates and existing bounded matrices are allowed.

## Review focus

1. Future emissions must affect earlier constrained scores: Task1 tests identical prefixes with contrasting suffixes.
2. Reference unknowns must not become model barriers: Task2 tests identical paths after changing reference support masks.
3. All-neutral/unsupported segments and ordinary carry must not be mistaken for observed D: Task2 tests source segmentation and separate carry attribution.
4. Tied optima can have different decompositions: Task1 tests deterministic tie ordering and reports tie counts rather than asserting unique attribution.
5. New provenance keys, files or disguised arrays must not bypass bindings/egress: Task2 mutation tests cover source/input/receipt inventories and unsupported report shapes.

### Task1: Reference-free complete-segment path instrument

**Create:** `ownership_paths.py`, `tests/test_ownership_paths.py` in the future isolated copy. Do not create them merely to present this plan.

**Consumes:** one nonempty usable segment of finite H/A/D emission triples, already derived from input-only eligibility. No reference labels, reference masks or target metadata are accepted by `path_tables`.

**Produces:**

- `path_tables(emissions, switch_cost=32.0) -> PathTables`.
- `constraint_summary(tables, index, reference_owner) -> dict` for reference owner0/1; opposite is1-reference. D remains in every unconstrained recurrence.
- `patch_summary(emissions, labels, first, stop, reference_owner, switch_cost=32.0) -> dict` for a constant-reference H/A episode inside one source segment.

`PathTables` contains original emissions, forward scores including the current emission, backward scores excluding it, cumulative emission sums and transition counts for those deterministic optima, selected H/A/D labels, best full-segment score and exact-tie count. All state-indexed tables have shape(n,3). The first state is free; there is no transition charge before the segment. The terminal state is free. `reference_owner` is used only by post-inference score queries and never alters the tables.

- [ ] Write RED tests whose expected values come from independent enumeration of all3^npaths for n≤5. For every index and forced H/A/D state, assert constrained maxima and decomposition `emission_sum -32*switches == score`.
- [ ] Write a suffix-influence test: identical prefix emissions must give identical prefix margins but contrasting suffixes must change full-segment margins. Include observed D and a neutral middle span, so an H/A-only recurrence cannot pass accidentally.
- [ ] Add invalid dimensions/nonfinite values, empty segment, negative cost, unique-optimum H/A column exchange, tie ordering, and fixed reference-patch boundary-switch tests. Assert patch objective change equals emission gain minus32times additional switches; a patch cannot improve an already optimal path beyond arithmetic tolerance.
- [ ] Run `python -m unittest discover -s tests -p test_ownership_paths.py -v`; expect failures because the instrument is absent, then implement the above interfaces and rerun to GREEN.
- [ ] Implement `constraint_summary`: O=opposite, R=reference; `prefix = F[O]-F[R]`, `local = E[O]-E[R]`, `future = B[O]-B[R]`, `full = prefix+future`, with `F` already including local E. Also expose prefix-before-local by subtraction. Positive margins favor O. Report signed future delta, cumulative emission difference and transition-cost difference; never double-count E.
- [ ] Verify returned labels/objective against unchanged `decode_soft` with deterministic tie convention. Preserve exact source bytes after tests pass; record task evidence/commit or equivalent byte-hash checkpoint.

### Task2: Frozen replay, episode attribution and strict aggregate driver

**Create:** `ownership_diagnosis.py`, `tests/test_ownership_diagnosis.py`, `reports/ownership-path/` in the future isolated copy.

**Consumes:** Task1 interfaces; existing `selected_artifact`, `decode_ball_gap`, `sequence_usable`, `feature_rows`, `PortableTree`, `materialize_abstentions`, original external loaders, `assert_public_report` and official metric helpers. The completed pilot's fixed input/source hashes and four-case aggregates are comparison evidence.

**Produces:** `freeze()`, `run_cases()`, `summarize()`, `verify()`; a source/input/protocol freeze and four named aggregate case receipts. Proposed CLI: `python ownership_diagnosis.py freeze|run|summarize|verify`, one case at a time unless a tested bounded process pool is justified. No parameter-selection command exists.

- [ ] Write RED tests for period/geometry/unsupported segmentation, a reference-known-mask perturbation that leaves every inference path unchanged, exact frozen-decoder replay and materialization equality, and carry-versus-latent errors. Include a reference-unknown interval inside a usable source segment; it must retain its effect on both prefix and suffix scores.
- [ ] Add RED tests for exact case membership/filenames, actual source and input SHA checks, changed reference/archive bytes, source inventory omissions and disguised event arrays. Reuse existing guarded functions rather than trusting two editable manifests to attest to one another.
- [ ] Implement source-only segments. Within each segment compute unchanged emissions/latent labels, then Task1 tables. Require original labels and objective to agree before calculating any reference-conditioned diagnostics. Copy source barriers and all-neutral latent-X handling exactly; keep carry out of the objective.
- [ ] Define error episodes as contiguous H/A swaps with constant reference identity and constant latent predicted identity, split at reference-unknown runs, structural periods and source barriers. Count final carried errors separately. Count all episodes and frames; no favorable subset or minimum-duration selection determines conclusions.
- [ ] For known-live frames, aggregate full/prefix/local/future O-minus-R margins, emission and switch contributions, tie support and corresponding agreement-frame denominators. For each latent swap episode compute the fixed-path reference patch. Classify by objective: wrong-owner cumulative emission preference; reference-favoring emission gain blocked by extra switch cost; numerical tie/ambiguity; or separately unsupported/carry. Do not equate these model-objective classes with physical-control causes.
- [ ] Export provider/match/frame and episode counts, duration quantiles, existing2sboundary/annotation-edge strata, reference-team rates and input-quality/carry support. Use overlapping strata with explicit denominators; never add them as disjoint populations.
- [ ] Supplement official all-state boundary diagnostics with H↔A-only transitions on evaluation-valid runs, at12and25frames. Retain signed/absolute conditional latency and matched/missed/spurious counts. Whitelist scalars from metric returns; never export raw matched pairs/event locations.
- [ ] Run tests to GREEN; freeze exact sources, four input identities, release ID, numerical conventions and report rules **before** any deeper path report. Replay the four cases and require the pilot's raw/final totals to reproduce. Run `verify`; expect all source/identity/objective/decomposition/inventory/egress checks to pass. Stop on a mismatch; do not repair predictions or reselect settings to make the report look better.

### Task3: Decision, review and documentation

**Create:** `docs/ownership-path-findings.md`, `docs/ownership-path-review.md`; optional safe aggregate publication only after explicit allowlist verification. Existing runtime/experiment sources remain immutable.

**Consumes:** Task2's verified four-case reports and the queued adversarial audit's verified findings. **Produces:** a prioritized recommendation for at most one later intervention, or an explicit unresolved result. No new production route or submission CSV is produced.

- [ ] Reconcile episode frames with frame strata, objective margins with component sums and all input/source hash inventories. Run appropriate full regression checks once after code is complete; retain complete logs, including skips.
- [ ] Document observed evidence versus hypotheses. If whole-path future/switch effects repeatedly defeat reference-favoring evidence, prioritize one later decoder-only contrast. If observed interior emissions favor the opposite owner, prioritize one geometry/memory-only contrast. If provider-boundary/tie/carry ambiguity dominates, state what independent evidence is missing. These are recommendations, not automatic parameter choices.
- [ ] Request one fresh whole-change review of mathematical correctness, reference isolation, source binding, carry attribution, scientific claims and aggregate publication. Resolve Critical/Important findings with one RED-to-GREEN pass; document deferred minors and declined-to-judge limitations. Do not fit/reselect in response to review.
- [ ] Preserve the four-case scope and stop. Give the user the findings, reproduction commands, source hashes and one next action. A future candidate experiment needs its own design and validation; repeated seen-data improvement is not target or fresh accuracy.

Self-review: all spec requirements map to Tasks1–3. Forward scores include the current emission; the before/local/future equation is derived consistently, with no double counting. Task2 alone supplies evaluation labels after reference-free inference. Every review-focus failure has an owning test. Current execution order remains: delivered plan first, then full adversarial repository audit; no implementation of this plan has been started.
