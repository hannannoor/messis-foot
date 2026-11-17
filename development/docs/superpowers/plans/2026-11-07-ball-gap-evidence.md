# Ball-gap evidence implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Test one neutral missing-ball policy against frozen w0-c32, preserving existing candidates and documenting both false and missed stoppages.

**Architecture:** Add root-level modules so all original sealed package/runtime bytes remain unchanged. Reuse verified original external score archives, derive ball availability from the same feature caches, and score one fixed candidate. Conditional opt-in integration follows only if both prospectively declared stages pass.

**Tech stack:** Python standard library inference; existing NumPy external evaluation; unittest. No dependencies installed.

**Spec:** `docs/superpowers/specs/2026-11-07-ball-gap-evidence-design.md`, approved 7 November 2026, SHA256 `35990be277f4d7a64c5509355b066674e6f92c1287ad3c2cfaf8204f8434abb0`.

## Global constraints

- One candidate: neutral H/A/D emissions for missing finite ball coordinates; w=0, c=32, floor=1e-6. Keep observed emissions and first-after-gap behavior unchanged.
- Whole usable segments without any ball observation remain latent X; materialization is separate and unchanged.
- Preserve all original sources/models/reports, candidate folders and Desktop pipeline; isolate from the current 256-file published tree.
- Exact original validation/regression IDs, natural and frozen 30% masking with seed1729. Previously examined references, no fresh holdout claim.
- No challenge GT/video, raw uploads, target-driven selection or fitting. Publish bounded aggregate counts only.
- The approved design authorizes inline execution, one final fresh review, conservative acceptance and a safe push to the existing PR. No repeated execution-method approval is needed.

## Review focus

1. No-observation segments must not silently become H from deterministic ties; Task1 tests latent X and separate carry.
2. A genuine observed D interval spanning missing inputs must remain possible; Task1 tests D continuation and all three positive states.
3. Availability cache periods or source content can change independently of score archives; Task2 tests mismatches and rehashes both inputs.
4. An absent D reference denominator must not look like perfect recall; Task2 tests null metrics and gate rejection without support.
5. Existing candidate outputs must never be overwritten; conditional Task3 reuses fresh/empty ownership checks and tests both prior generations.

### Task1: Fixed neutral-evidence policy

**Create:** `ball_gap_policy.py`, `tests/test_ball_gap_policy.py`.

**Interfaces:** `decode_ball_gap(supports, periods, usable, observed) -> (latent_labels, diagnostics)`; diagnostics contain only scalar counts. Uses unchanged `soft_emissions`/`decode_soft` and fixed32. `observed` is a same-length bool sequence, never reference data.

- [ ] Write behavior tests for D-dominant missing slots between H observations, observed D, H/A/D positive transitions, D across an internal gap, fully unsupported segments, period/geometry barriers, malformed flags/dimensions and emission-swap unique-optimum symmetry.
- [ ] Run `python -m unittest discover -s tests -p test_ball_gap_policy.py -v`; expect missing-policy failure.
- [ ] Implement the fixed policy and validate inputs; neutralize whole triples, never D alone. Count neutral active usable rows, unsupported segments and unsupported active rows.
- [ ] Run the same tests; expect all pass. Check old published bytes still match their manifest; ledger Task1 with RED/GREEN evidence.

### Task2: Bound evidence and execute one external comparison

**Create:** `ball_gap_experiment.py`, `tests/test_ball_gap_experiment.py`, `reports/ball-gap/{comparison-freeze,validation-disposition,summary}.json` and per-case aggregate receipts.

**Interfaces:** consume Task1 policy; `dead_metrics(gt,pred,periods) -> aggregate dict`, `availability(cohort,match,regime,periods) -> bool array`, `assess(reports) -> checks/disposition`, `freeze()`, `score_stage(stage,workers)`, `summarize()`.

- [ ] Write RED tests for false/missed D denominators, unknown/period-bounded D intervals, official matching counts, exact stage membership, all four acceptance rules, absent support, strict aggregate export, period/source/archive binding and validation-disposition freezing before regression.
- [ ] Implement full-state D-interval diagnostics using official `segments`, `spell_overlaps` and `match_spells`; score only reference-known period runs. Empty denominator is null.
- [ ] Implement observed masks from verified finite `ball`/`ball_xy`, unchanged contiguous masks and exact original periods. Guard original evidence through `accuracy_experiment.source_check`/`GUARD`; pin new source bytes, protocol, source/score inputs and original identities. Re-entry rejects mutated identities or receipts.
- [ ] Export only strict aggregate reports: original metrics, supplementary D/boundary metrics, observed/missing confusion, policy/materialization diagnostics and source hashes. No per-frame arrays.
- [ ] Freeze code/rules before scoring. Run `python ball_gap_experiment.py freeze`, then `validate --workers 2`, then `decide`; ledger disposition digest. Run `regress --workers 2` once and `summarize`; no policy adjustments from scores.
- [ ] Reverify source/data/report identities and unchanged old receipts. Record Task2 complete even if the fixed candidate is rejected.

### Task3: Conditional integration, review and safe publication

**Create:** `docs/ball-gap-results.md`, `docs/ball-gap-code-review.md`; conditional `ball_gap_candidate.py`, `benchmark/ball-gap/selected.json`, `tests/test_ball_gap_candidate.py` only if both stages pass. Update README with final disposition.

- [ ] If rejected, document exact failed checks and retain current candidate. No new target inference or production CLI.
- [ ] If accepted, TDD a separate CLI using the original strict source parser, current four comparator outputs, fixed new policy, source/model/evidence-pinned artifact, fresh/empty output checks and explicit latent X/neutralization materialization flags. Positive synthetic fixture must emit H/A/D, plus old-generation overwrite protection and source/selection mutation failures.
- [ ] If accepted, two clean local original-length inference runs and unchanged official format-only validation; compare all6 CSV hashes and the4 old control hashes. No target reference comparison or tuning.
- [ ] Run appropriate full suite and stdlib/Python floor checks. One fresh capable whole-change reviewer assesses spec, code, evidence and operational safety. Regrade findings; one Critical/Important RED-to-GREEN fix pass, minor findings documented, no re-review or score-driven tuning.
- [ ] Create explicit allowlist publication; verify original immutable bytes, all new aggregate shapes and remote blob hashes. Publish with expected-head lease to existing PR; verify main unchanged, PR open/unmerged and head exact. Save receipt and final requirement audit. Retain local ledger because no Git history exists locally.

Self-review: Task1 policy supplies Task2 and conditional Task3 unchanged signature. Task2 frozen disposition controls Task3 only; no selection feedback. All spec requirements and five review risks have an owning task. Original score caches remain local under sibling `accuracy-reference`, with exact identity verification.
