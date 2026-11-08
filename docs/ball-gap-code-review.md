# Ball-gap review and response

One fresh whole-change review found no Critical defect in the scored policy or reference leakage. It independently reconciled all26 aggregate confusions, false/missed-D counts and boundary support counts, and reran the internal-consistency verifier. Six Important findings were addressed in one substantive pass; no predictor, parameter, original score receipt or disposition changed, and there was no second review.

## Fixed findings

1. **Late output ownership:** the new pinned runtime uses sibling-directory `os.rename`, which refuses a populated destination. An existing directory can be removed only atomically while empty. No recursive replacement is used. A deterministic test inserts a user result after the last preflight check; publication fails and its bytes survive.
2. **Released verification:** `ball_gap_post_review.py verify` first validates the independently pinned selection. Its source/evidence maps pin the runtime, actual approved design, runner seal and all26receipts. It also requires the exact runner-source key and stage-file inventory, replays additive diagnostics and rederives dispositions/summary. Empty runner maps, edited design bytes and extra receipts each fail a regression fixture. Frozen legacy helpers remain audit/internal-consistency interfaces.
3. **Fallback-D accounting:** additive `carry_counts` distinguishes wholly latent-X active periods and their fallback-D rows from ordinary carry, and counts all latent-X rows materialized as D/H/A. A fixture combines an unknown period with an ordinary D-carried gap. The additive26-case replay matches original latent/materialization totals; all these external cases have0wholly-X-period fallback rows. Some ordinary gaps still carry D. Counts include structurally active but reference-unmeasured regions and are not correctness estimates.
4. **Paired deltas:** the additive report provides signed candidate-minus-w0-c32 accuracy, macroF1 and spellF1 differences for every named case. A fixture checks positive and negative signs. No rescoring or reference fitting was required for these deltas.
5. **Runtime identity:** the small `ball_gap_candidate.py` loader checks the accepted source map before importing substantive `ball_gap_runtime.py`. An altered adapter with genuine policy/model/evidence bytes is rejected.
6. **Reproduction:** documentation now separates released verification from replay in a separate clean copy, with exact starting contents and cache prerequisites. Setup-only sealing still refuses a new seal after scoring starts; published evidence is preserved.

Five regression methods were RED against the pre-fix implementation and GREEN after the pass. The full post-fix suite passed341tests with6documented skips. Earlier policy7tests, experiment7tests, serialization-runner2tests and positive CLI3tests also passed RED/GREEN. The original scored policy/engine, pre-scoring freezes,26receipts and summary remain byte-for-byte intact. First-after-gap wording now distinguishes unchanged features/emissions from offline states that may change; no unchanged error rate is claimed.

## Deferred minors

- The preserved engine cannot average null D-interval F1 for a DFL case with no true or predicted D. Every pinned DFL case has support; a future cohort extension must propagate null before use.
- Interruption after creating the preserved engine's exclusive fixed `.new` file requires manual inspection/removal in an isolated replay copy. Completed receipts remain idempotent/protected; automatic interrupted-write recovery is deferred.

## Declined-to-judge rulings and costs

- **Target correctness/generalization:** unmeasured because there is no permitted independent reference. Cost: the opt-in remains experimental despite seen-reference gains.
- **Original-length repeatability/format:** checked separately by the author using fresh runs, hashes and the unchanged official format-only validator. Cost: the reviewer did not independently repeat these checks; they do not establish target quality.
- **Development diagnosis/full suite:** replayed/run by the author with logs retained. The reviewer inspected the mechanism and identities and independently reconciled26score cases, but did not replay the diagnosis or full suite. Cost: no second independent full rerun.
- **GitHub publication:** the author verifies explicit allowlists, all staged blobs, leased head, open/unmerged PR and unchanged main. Cost: remote execution has author receipts rather than a second review.

Other builder rulings: retain the isolated copy/ledger because there is no local Git history (additional disk use); preserve exact frozen engines and layer serialization/evidence audits on top (additional commands and original-cache prerequisites). These protect reproducibility without changing the accepted policy after observing results.
