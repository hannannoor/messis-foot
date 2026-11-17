# Accuracy-First Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans inline, TDD, and one fresh whole-change review. The user approved the bounded experiment; execution continues without another scope confirmation.

**Goal:** Evaluate whether finite H/A/D sequence evidence improves the official possession objective over the four frozen comparators.

**Architecture:** Add a standard-library three-state decoder around the unchanged frozen heads; an external-only NumPy driver caches label-free scores, freezes16 settings, selects on seen validation, then runs one frozen seen-regression comparison. Results can accept or reject the candidate; no target selection or baseline replacement.

**Tech Stack:** Python3.9+ inference, unittest, existing NumPy experiment dependencies.

**Spec:** `../specs/2026-11-07-accuracy-first-design.md`, approved by user7 November2026.

## Global Constraints

Preserve203 published files except explicit additive documentation changes, the34 frozen sources/models and Desktop baseline. No target GT/video checks, hand labels, challenge-driven tuning or raw/per-frame publication. All external matches are seen; no fresh-generalization claim. Primary spellF1 averages0.3–0.7 IoU; macroF1 breaks ties. Fixed weight grid0,.25,.5,1 and cost grid0,2,8,32. Period/invalid/insufficient geometry are barriers. No reference masks enter inference or carry. No new head fitting. Standard-library runtime, aggregate-only reports.

## Review Focus

Skipped geometry and empty/degenerate segments must abstain, not create a default H.
Three-state ties and H/A reversal must be deterministic without treating baseline labels as hard anchors.
Cache/source/model changes must invalidate receipts rather than silently reuse stale scores.
Selection must exclude seen-regression scores and treat providers equally; reference holes remain unknown.
Publication must exclude transitions, raw coordinates and per-frame reference/prediction arrays.

## Task1 — Soft decoder and source eligibility

Create `gap_solver/soft_sequence.py`, `tests/test_soft_sequence.py`.

Interfaces: `soft_emissions(supports,motion_scores,weight)` returns finite H/A/D tuples; `decode_soft(emissions,periods,usable,switch_cost)` returns original-length H/A/D/X labels; `sequence_usable(frame)` derives input-only eligibility.

- [ ] RED: literal H,A,H sequence smooths to H,H,H at finite switch cost; strong A evidence revises H; D remains an available finite state; H/A swap; exact ties; period/quality barriers; insufficient points; nonfinite/bad dimensions/parameters.
- [ ] Implement GREEN; use compact byte backpointers and normalized rolling dynamic scores. Verify independently enumerated synthetic paths, not a mirrored implementation assertion.
- [ ] Run `python -m unittest discover -s tests -p test_soft_sequence.py` and then project suite at task completion.

## Task2 — External protocol, safe scoring and experiment driver

Create `gap_solver/accuracy_protocol.py`, `accuracy_experiment.py`, `tests/test_accuracy_protocol.py`, `tests/test_accuracy_experiment.py`.

Interfaces: explicit validation/regression splits; deterministic provider-balanced ranking; source/input/model digests; `aggregate_metrics(reference,prediction,periods,incumbent)` returns named scalar/count metrics, confusion, spell matched/spurious/missed counts and correction/regression counts only. Driver stages `freeze`, `prepare`, `validate`, `select`, `regress`, `summarize`, default workers2.

- [ ] RED: provider weighting, macro tie breaks, malformed/incomplete candidate sets, source/input changes, no selection from regression, unknown-label handling and recursive export rejection for event arrays.
- [ ] Implement GREEN. Cache raw tactical supports and motion scores on anonymous frames plus all four comparator labels; use existing30% input-only masks at seed1729. Bind both source files and generated cache archives to receipts. Vectorized head evaluation must match portable heads on fixed synthetic rows. Do not score test/regression references during preparation.
- [ ] Freeze all sources, split IDs, fixed grids, models and consumed inputs **before** preparing/scoring candidates. Validation IDs: DFLJ03WQQ; SC2006229,2006363. Regression IDs exactly from approved spec.
- [ ] Run validation natural/masked; select from natural results only with equal provider then match weights. Freeze selected settings, acceptance decision and evidence hashes. Even rejected validation candidates may receive the approved single frozen regression diagnostic, never a retune.

## Task3 — One frozen regression and evidence-based disposition

Files: safe aggregate reports under `reports/accuracy-first/`, `docs/accuracy-first-results.md`, conditional `gap_solver/soft_candidate_cli.py`/`soft_candidate.py` only if both primary comparisons improve.

- [ ] Run one natural/masked seen-regression comparison for the frozen selection against four unchanged policies. Validate receipt completeness and compare primary spell quality, macro/frame metrics, per-class errors, corrections/regressions and unmeasured output.
- [ ] If either validation or seen-regression primary score fails to improve agreement-plus-carry, retain current route and report rejection with actual evidence. If both improve, add/test an explicitly experimental opt-in route with original indices, latent/carry diagnostics and existing output safety; no target selection.
- [ ] Include original development loss audit and reference/readiness recon, with explicit no-fresh-H/A/D validation and interpolation limitations. No extra search/parameter grid after observing scores.

## Task4 — Review, verify, publish

- [ ] Full suite; stdlib/Python3.9 grammar checks; verify frozen sources/baselines and receipt/code identities. Fresh reviewer reads whole change, approved spec and ledger rulings. One substantive fix pass, each fix RED->GREEN; no repeated review loops.
- [ ] Safe explicit publication allowlist, recursive no-event export check, local/remote Git blob equality, update existing PR with findings and limitations. Preserve local prediction caches and audit ledger. No merge or visibility change.

Self-review: Task1 runtime feeds Task2 score arrays, Task2 frozen selection feeds Task3 single regression, Task3 disposition determines whether a new route exists. All five review-focus cases have owning tests. No interface conflict. Source isolation uses exact-byte copies because this workspace has no local git repository; the approved spec already chose that fallback.
