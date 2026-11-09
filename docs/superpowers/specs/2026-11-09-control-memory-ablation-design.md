# Controlled retained-owner memory ablation

9 November 2026, Asia/Singapore. **Status: builder-checked design, awaiting approval before implementation.** The user chose option 1: matched training runs with only remembered-owner flags and age neutralized in the candidate. The exact cohort, thresholds, environment and execution limits below are planner proposals, not previously approved numerical requirements. One fresh ML/software builder check returned "nothing important left"; no fitting, inference, dependency installation or implementation occurred during planning.

## Intent and evidence

Test whether dependence on the retained-owner feature block harms possession spell quality. This is one candidate experiment, with a reproducible matched control, not a promise that removing memory will improve predictions.

Start from `b5878dd19ae3313803329f32482c2d500246ab39`, published draft PR #4. The completed [path diagnosis](../../ownership-path-findings.md) shows local emissions favoring the wrong owner on 95.6–99.2% of observed, supported interior ownership-error frames across five used cases. This establishes an emission-evidence problem relative to provider labels. It does not prove memory causes the errors.

The current features set remembered ownership after six consecutive automatic proximity candidates. The last-owner flags/age share geometry with the other features. A fitted ablation must neutralize the same block during training and inference; simply zeroing an already-trained tree's inputs would introduce a different feature distribution and answer a weaker question.

The earlier adversarial audit and its [verified response](../../../../adversarial-review/VERIFIED-AUDIT-RESPONSE.md) remain constraints: used cohorts are not fresh validation; DFL coordinate freezing is a shortcut risk; short spells and gaps require visibility; a symmetric head or a new decoder is not automatically better. Subsequent cadence experiments rejected velocity-only repair, added strong simple comparators, and the release separated selected inference from research machinery. Do not rerun those unchanged studies as discoveries. No new council or broad search belongs here.

## Approaches considered and user choice

1. **Matched retained-owner block ablation — selected by the user.** Reproduce the original fitted head, then train one otherwise identical head with its three explicit retained-owner inputs made constant. This isolates one feature block under one fixed learning algorithm. It may remove useful continuity and worsen ownership or D.
2. **Richer local player/ball geometry.** Potentially supplies information absent from the current nearest-distance summary, but changes the feature contract and introduces a larger hypothesis. Defer.
3. **Separate liveness and ownership heads.** Could reduce coupling, but changes architecture/training and needs separate qualification. Defer.

## Goals, non-goals and preservation

- Deliver a tested, reproducible experimental comparison with an explicit pass/fail/unresolved conclusion and every regression visible.
- Preserve the released predictor/artifact, model, original training script, approved designs, historical receipts, private stores, CSVs, recovery ledgers and PRs 1–4. No default change, merge, Desktop installation, challenge inference or target-output generation.
- No challenge data/video/GT, public-window outcomes, manual labels, lag fitting, cost tuning, symmetry augmentation, new observation repair, model family/grid search, or new data acquisition.
- No production-runtime training dependency. Fitting runs in an isolated training environment; portable evaluation remains separate.
- No claim of fresh validation or physical-control truth. All existing matches are permanently used evidence. Even a passing candidate is eligible only for a separately authorized fresh qualification, not automatic promotion.

## Exact intervention and model contract

Use the unchanged 18-feature generator in `gap_solver/tactical.py`.

| Index | Feature | Control | Candidate, during both fitting and inference |
|---|---|---|---|
| 15 | `last_control_home` | Original value | `0.0` |
| 16 | `last_control_away` | Original value | `0.0` |
| 17 | `last_control_age` | Original value | `10.0` |

`(0,0,10)` is the existing unknown-owner representation. Preserve the other fifteen feature values exactly, including last observed home/away distances at indices 13/14. The experiment removes the explicit retained-owner block, not every source of historical information or correlation. Do not modify how the original feature generator maintains memory.

Keep the original 18-column schema for portable compatibility. Apply a pure, deterministic mode-specific transform to generated rows/matrices. Train the candidate with the neutral columns and apply that same transform before its exported tree at evaluation. The candidate's fitted tree must have no split on indices 15/16/17. Report the feature block as a single intervention; do not test alternative neutral values or partial subsets.

Keep H/A/D targets, tree depth **4**, minimum leaf **125**, seed **1729**, sample order/weighting, float32 features, original portable exporter, class order, ties and probability arithmetic fixed. No leaf calibration. Use the current sequence policy: motion weight 0, switch cost 32, floor 1e-6, neutral missing-ball emissions, existing input-only eligibility/barriers, unsupported latent X and separate materialization.

Changing joint H/A/D support can change final D decisions even though the decoder is fixed. D is protected by evaluation gates rather than a false claim that D probabilities remain unchanged.

## Reproduce the control before fitting the candidate

The owning historical recipe is `select_external_improvement.py`; do not invoke its old grid or remove its already-frozen sentinel.

Use retained DFL training caches in this exact order: **J03WOH, J03WOY, J03WPY, J03WMX**. For each match, prepare natural rows then the original 30% training augmentation from `gap_solver.selection.ball_mask`, seed `1729 + match_index`. That training mask uses its original 5/15/50/125-frame durations.

Construct features for the full input before selecting rows. Select original row indices divisible by five with known H/A/D reference. Within each match/regime, give each selected row weight `1 / selected_row_count`; concatenate in the original order. X is not a fitted class. Use float32 features, float64 weights and the original three-class exporter.

First fit one full-feature control. Its canonical exported model JSON SHA-256 must equal **`363c45c70838b398cd87aee7474d7e281fd392f059a31b85712e312058aaab4d`**, the existing model's digest. Confirm its exported supports match scikit-learn on the prepared training rows within absolute 1e-12, zero relative tolerance. Hash training row identities, feature/target/weight semantics privately.

Only after that gate passes, make a separate candidate matrix by changing the declared three columns, assert equality of the other columns/targets/weights/order, and fit the candidate once. Verify its portable supports against scikit-learn across all prepared candidate training rows at the same tolerance. Keep the reproduced control artifact, candidate artifact and provenance; never overwrite `FROZEN_MODEL` or its selected metadata.

If the control digest differs, stop before fitting the candidate. Do not change seed, row selection, weights, masks, dependency versions or acceptable equality after seeing the mismatch. Diagnose the reconstruction separately; no candidate result can then be called the intended matched comparison.

## Isolated training environment

Planning inspection found only CPython **3.14.5** registered and no importable scikit-learn. The installed `uv` executable is available. Do not install anything while this design is awaiting approval.

After approval, use a workspace-local Python **3.12 x64** managed interpreter and virtual environment, with the exact interpreter build/source and download identities recorded before fitting. Keep system Python and other environments unchanged. Honor the historical core pins in `requirements-training.txt`: NumPy 1.26.4, SciPy 1.13.1, scikit-learn 1.5.1, pandas 2.2.2. Resolve transitive packages once, lock all versions/wheel hashes before training, and use binary wheels; do not silently upgrade the estimator or compile a substitute stack.

The training artifact, not a claim of identical runtime names, proves reconstruction: the exact frozen control model digest is mandatory. Record Python/package/platform/BLAS/thread settings and use one training thread. Portable scoring uses the existing CPython 3.14.5 environment; record/check both environments at their respective execution boundaries.

Primary packaging references: [scikit-learn 1.5.1 release metadata](https://pypi.org/pypi/scikit-learn/1.5.1/json), [Python 3.12 Windows distribution example](https://www.python.org/downloads/release/python-31210/). The exact chosen 3.12 patch/build is fixed in the environment lock before real fitting, not selected from model scores.

## Fixed external evaluation cohort

Use existing retained inputs only. Training overlap and earlier scientific reuse are different properties: every listed match is already used, while only two evaluation matches overlap this experiment's fitting set.

| Provider | Fixed matches | Role in this experiment |
|---|---|---|
| SkillCorner | 1874553, 1886347, 2007448, 2007721, 2010085, 2011166, 2013725, 2015213, 2016236, 2017461 | Ten fit-disjoint, previously used matches |
| DFL | J03WR9, J03WN1 | Two fit-disjoint, previously used matches |
| WCSF | Retained two-half used match | One fit-disjoint, previously used match; report separately |
| DFL | J03WOH, J03WOY | Two fitting-overlap diagnostic matches; excluded from the primary score |

For all fifteen matches use exactly two regimes: **natural** and the existing **30% contiguous mask, seed 1729**, from `gap_solver.temporal_selection.contiguous_mask` applied through the coherent motion-frame masking helper. Evaluation uses the retained 5/15/50/125/250-frame mask convention; it is deliberately distinct from the historical training augmentation. Freeze exact mask semantics/digests. No new masks, cadence grid or favorable seed selection.

Two predictors: reproduced frozen control and the single memory-ablated candidate. Since the reconstructed control model digest must equal the frozen model, this is one control identity, not a third method. Maximum **30 match/regime cases × 2 predictors = 60 real inference entries and 60 complete variant-scoring entries**. Fit the models before opening any candidate evaluation outcomes. Report all cases; no adaptive subset selection or early success claim.

Use the retained SkillCorner detected-geometry cache triples, DFL cache triples plus the original metadata/positions pairs for evaluation motion frames, and the existing WCSF geometry/reference DBs/canonical index. Reuse original adapters/team/time conventions. Bind exact logical inputs against retained provenance/previous seals before use; never glob an interchangeable replacement or rebuild a cache over old files. Preserve container and canonical semantic identities separately. References remain outside feature/inference APIs; old cache adapters' physical reference parsing is disclosed in access logs.

The five natural diagnostic controls must reproduce the completed ownership-path baseline scores/counts; WCSF also must reproduce its sealed canonical index/final predictions and all five IoU results/mean. Existing regression controls must reconcile to their owning retained natural/masked receipts before candidate results are accepted. A source/index/mask/baseline mismatch stops the case; it is not repaired by fitting or excluding a match.

## Primary outcome and proposed gates

All thresholds here are prospective engineering choices for this experiment. No candidate result has been computed.

The primary score is the arithmetic **equal-provider mean of per-match mean spell F1 across the five official IoUs**, natural inputs, over the **thirteen fit-disjoint matches**: ten SkillCorner, two DFL and one WCSF. Each provider contributes one third; each match has equal weight within its provider. This is a used-data development summary, not a pooled match F1 or a confidence estimate. Retain the original four-case and WCSF tables, all individual cases and the two fitting-overlap results separately.

A candidate is promising for later qualification only if every gate passes:

1. Natural primary increment is greater than **1e-6**, and no natural provider mean decreases beyond 1e-6.
2. No fit-disjoint match loses more than **.01** mean spell F1 under either regime. The masked primary mean must not decrease beyond 1e-6. Fitting-overlap match results cannot rescue primary failure.
3. On every full-state DFL/WCSF match and regime, including the overlap diagnostics, D precision and D recall each lose no more than **.01 absolute**. SkillCorner cannot measure positive D; its known-live false-D rate may increase by no more than .01 per match/regime. Undefined required support yields an unresolved gate, not an invented zero or pass.
4. Preserve short-spell visibility: for reference H/A spells of at most **25 frames**, measure matched reference-spell recall at IoU .5. Where a case has at least twenty such spells, recall loss may not exceed **.02**; with smaller positive support, matched count must not fall. Zero support is explicitly unassessable, never counted as success.
5. Reject H/A collapse: where both reference owners have support, both must retain nonzero predictions. No source/model/portable-parity/egress/attempt-integrity gate may fail.

The primary increment must strictly exceed 1e-6; do not add another tolerance to that requirement. Use absolute 1e-6 arithmetic slack for the other scalar nonregression/maximum-loss comparisons; exact integer/support identities remain exact. A zero-short-spell case is non-applicable to gate 4, with null recall and no positive short-spell evidence; it cannot rescue a failure on cases with support. Undefined required D or primary support makes the overall decision unresolved. Report effect sizes even when a gate fails. Do not interpret a tiny passing increment as a practical guarantee or call a failure an improvement because frame accuracy rises.

Also report H/A/D confusion and frame accuracy, all five spell TP/FP/FN/F1s, missed/spurious all-state destination-matched and H/A pair-matched boundaries at 12/25 frames with conditional signed/absolute latency, short-spell support, natural/masked and observed/missing-ball strata, and worst individual regressions. Match within valid periods/known runs before pooling. Reference-X holes never segment inference. Do not fit boundary lags or add an oracle repair.

## Execution, budgets and outputs

Create new additive experiment modules and a separate local lineage after design approval and implementation testing. Proposed command boundary: `memory_ablation_run.py freeze|fit|seal|evaluate|summarize|verify --run-id <new-id>`; final filenames/module division are builder decisions. Keep training entry points out of portable inference imports.

- `freeze`: bind protocol, source/dependency closure, both environments/locks, original model/release contracts, exact input inventories, cohort/roles, masks, gates and global attempt budget before fitting.
- `fit`: exclusive claims and append-only entries immediately before **at most two real estimator fits in this experiment**, control first. Synthetic training tests are clearly labeled and separate. Verify reconstruction before candidate entry; preserve failures and partial artifacts.
- `seal`: validate and bind the two exported models before any candidate evaluation. Recheck source/input/runtime identities. No model replacement after sealing.
- `evaluate`: exclusive case/variant claims, bounded counts above and complete persisted aggregate receipts. No overwrite/resume through interrupted attempts. Different run IDs do not silently reset the experiment's fit/score budget.
- `summarize`: derive prespecified provider/case tables and gate decisions from exactly the expected sealed receipts; no additional fitting, predictions, scoring or selection.
- `verify`: read-only identity/inventory/attempt/receipt/semantic checks. It must never call feature generation, fitting, inference or scoring. Require canonical public summary bytes and trusted per-case hash-key inventories, retaining the previous review fixes.

Private matrices, per-frame predictions, references, masks/indices, paths and events stay in a new sibling private directory. Public-candidate artifacts are source, design/tests, portable model arrays/metadata and bounded aggregate/hash receipts only. Use explicit owned schemas plus the existing publication guard. No raw/event arrays hidden in metadata keys. Preserve source/input/container and semantic identities honestly.

If a fit or evaluation fails, keep the attempt/incomplete marker and stop. A code fix can be tested synthetically, but additional real work beyond the declared two fits/sixty scoring attempts requires a documented protocol amendment and authorization; do not silently rerun a new generation. One fresh whole-change review and one material RED-to-GREEN fix pass are planned. Its findings cannot authorize resetting a consumed scientific budget.

## Tests defined before implementation

1. Literal feature-transform tests: all eighteen columns, exact `(0,0,10)`, other fifteen unchanged bitwise, input immutability, scalar/matrix equivalence, invalid/nonfinite dimensions, reference perturbation, period resets and consistent neutralization on natural/masked inputs.
2. Independent training-preparation fixtures: whole-input features before row subsampling; exact match/regime order, index modulo five, X exclusion, original per-group weights and both different mask conventions. Changing reference affects only training eligibility/targets, never generated features.
3. Synthetic paired training/export: two fixed estimator calls, identical targets/weights/order/hyperparameters, constant candidate block, no candidate splits on that block, all-row scikit-learn versus portable float32 parity, class/H/A/D and exporter validation. These tests run in the isolated pinned training environment rather than being silently skipped in the main runtime.
4. Inference parity: reproduced control matches released supports/latent/final labels on synthetic D, neutral ties, source/period barriers and unsupported carry. Candidate uses its transformed rows consistently, retains missing-row neutralization, and never receives reference. Input hints are rejected.
5. Literal metric/gate tests: unequal match/provider weighting, five-IoU mean, excluded fitting-overlap results, D/SkillCorner denominator differences, exact threshold edges, a mean hiding a worst-match failure, short-spell low/zero support, H/A collapse, period/run pooling and all-X/all-D conventions. No expected score is computed solely with the function under test.
6. Protocol tests: immutable source/input/model/environment/mask bindings, pre-freeze release drift, control-digest failure preventing candidate fit, fit/score count limits, duplicate/missing/extra cases, cross-run budget reuse, concurrent/no-clobber claims, interrupted fits/evaluations, corrupted persisted bytes, summary shadow arrays, coordinate-bearing hash keys, and read-only verification patched to fail if computation is entered.
7. Watch each relevant new test fail before implementation, then pass afterward. Run the complete main-runtime suite once after final code changes with native Windows link permissions and the existing code-only official fixture; run the training suite explicitly in Python 3.12. Do not repeat green suites for prose-only changes.

## Deliverables and completion

Deliver the checked design, a Superpowers implementation plan with interfaces/test commands, tested additive code, isolated environment lock, prospective freezes, two fitted artifacts or an honestly stopped reconstruction, all bounded comparison receipts, exact gate decision, preservation evidence, review/fix record, and reproducible local commands. State whether the candidate improved the prespecified used-data objective, which safeguards passed, and which failed or lacked support. No requirement says the candidate must win.

Publication is a separate external action: the user's previous approval covered PR #4. This design can be approved either for local execution only or explicitly together with a new draft PR containing code/tests/docs, fitted portable-model arrays/metadata and bounded derived aggregates, with no private per-frame assets. Any authorized write must live-authenticate as The-leonjr /277591257 and preserve main and existing PRs. Do not infer new publication permission from the earlier PR-specific approval.

Builder choices left open: cohesive module/file boundaries, bounded in-memory chunk sizes, vectorized support traversal verified against PortableTree, exact compatible Python 3.12 patch/build and locked transitive wheels before real fitting, strict JSON schema implementation and readable documentation layout. They may not change the intervention, training recipe, cohort, regimes, gates, attempt limits or evidence claims without an explicit design revision.
