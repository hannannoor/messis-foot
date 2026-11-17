# All-state possession-path diagnosis — additive design

9 November 2026. Implements the approved whole-segment H/A diagnosis and adds D/spell-object analysis. The original 8 November design/plan remain byte-identical. The user has authorized implementation, with Superpowers planning and explicit tests for the missing scope. Engineering conventions below are planner decisions, not invented approvals. This task diagnoses the unchanged control; fitting or promoting an intervention is a separate decision.

## Intent, alternatives and limits

The frozen release at `8c7be9d33bd3e2bd85f04b4c460608fd52e69b8a` is reproducible. Performance history leaves two plausible mechanisms: wrong geometry/control-memory emissions, and correct local evidence defeated by the sequence objective. Missed D dominates WCSF frame errors but its contribution to spell loss is unmeasured. [Existing evidence](../../performance-history-and-next-step.md).

The selected approach is the already-approved complete-segment attribution, extended to all three graded states and official spell objects. Directly lowering D thresholds/switch cost would confound these mechanisms and risk fragmentation. Refitting a symmetric head now bundles another unproven cause. Those remain later alternatives; neither is implemented here.

Use exactly five already-used external cases, natural inputs: original SkillCorner 1874553/1886347 and DFL J03WOH/J03WOY, plus the WCSF two-half match as one separate case. Preserve original four-case reporting and add WCSF separately. No challenge raw data, predictions, video, public reference/outcomes, new acquisitions, new masks, lag/cost grids or refitting. One match/provider's labels are not physical-control truth; WCSF is permanently used development/regression evidence.

## Frozen inference and reference separation

Preserve the tactical model digest `363c45c70838b398cd87aee7474d7e281fd392f059a31b85712e312058aaab4d`, existing features/float32 tree, w=0, c=32, emission floor 1e-6, H/A/D predecessor/terminal ties, neutral missing rows, eligibility, unsupported latent X and separate materialization. Keep every original source/period/annotation convention. No source or reference clock corrections.

`prepare_inference(frames)` accepts geometry frames only, rejects label hints and returns an `InferenceTrace`: emissions, periods, observed/usable flags, raw codes, latent/final labels, retained-control owner/age and input-only usable segment bounds. A complete usable segment with no observed ball remains unsupported X and has no explanatory D path. Reference unknowns never split inference segments or erase their prefix/future influence. Carry is excluded from objective attribution and counted separately.

Reuse the original cache loaders for the four cases. They physically parse reference containers during loading; disclose that in a new private access log. This is used-data analysis, not a claim that references were first accessed after inference. The prediction/path functions receive no reference argument. Load WCSF reference codes only after geometry preparation, using the original read-only geometry/reference adapters. Do not call `wcsf_audit` acquisition/infer/score commands or any unused comparators; preserve its old attempts/access logs.

## Complete-segment path mathematics

Create `ownership_paths.py` with `PathTables`, `path_tables(emissions, switch_cost=32.0)`, original `constraint_summary(tables,index,reference_owner)` for H/A, generalized `state_summary(tables,index,reference_state,comparison_state)`, and `patch_summary(emissions,labels,first,stop,reference_owner,switch_cost=32.0)` accepting reference state 0/1/2.

Tables retain H/A/D throughout. Forward scores include the current emission; backward scores exclude it. Both retain emission sums and transition counts for deterministic optima. First and terminal states are free. Normalize recurrences to preserve the frozen decoder's arithmetic/tie behavior, retaining offsets for absolute scores. `labels` are H/A/D strings. Verify exact label equality to the frozen decoder and objective/decomposition within absolute 1e-6, relative 1e-10. Nonfinite/overflowing arithmetic fails closed.

For R (reference) and P (actual latent error state), report `prefix_before = F[P]-F[R]-(E[P]-E[R])`, `local = E[P]-E[R]`, `future = B[P]-B[R]`, `full = F[P]-F[R]+B[P]-B[R]`. Positive favors P. Emission/transition decompositions sum to each constrained full score. Report exact recurrence ties and numerical near-ties separately; one tied decomposition is not a unique cause.

For each constant R/P error episode, hold the rest of the original optimal segment path fixed and replace the episode by R. Split episodes at R/P identity, unknown-reference edges and source/period boundaries, only after inference. `objective_gain = emission_gain -32*additional_switches`. Counts classify emission preference against R, reference-favoring emissions blocked by additional switches, numerical ties and residual nonlocal/mixed cases. Episodes/frames reconcile; classification is a model-objective explanation, not physical causation.

All-state error families are missed_D (R=D,P=H/A), false_D (R=H/A,P=D), and ownership_swap (R=H/A,P=opposite H/A). Final errors originating from latent X/materialization remain a separate family with no fabricated path margin. Include agreement-frame denominators, observed/missing/usable/interior strata, reference-team rates, memory association and 12/25-frame H/A boundary counts/conditional latency. Original 2s boundary/annotation-edge strata remain descriptive, overlapping support.

## Spell objects and two diagnostic counterfactuals

Create `ownership_diagnosis.py` for pure reference-conditioned analysis. Use the unchanged official evaluation padding/valid-run/X-fill conventions and same-team IoU-descending greedy one-to-one matching at .3/.4/.5/.6/.7. Pool TP/FP/FN over periods before F1; never average per-half ratios as a match score.

At each threshold, partition unmatched reference and prediction spells into no same-team overlap, overlaps all below threshold, or qualifying overlap consumed by greedy matching. Also report reference spells with multiple overlapping predictions and predictions with multiple overlapping reference spells. These split/merge flags overlap and are not additive causal loss fractions. All counts reconcile to the exact baseline metric. Publish counts only, not intervals/pairs.

Predeclare two reference-only diagnostic arrays, held locally and never exported as candidates: (1) correct known-reference errors involving D while leaving H/A swaps unchanged; (2) correct known-reference H/A swaps while leaving liveness/carry/unknown errors unchanged. In both, retain GT-X positions unchanged. Score these with the exact same spell convention and report signed aggregate TP/FP/FN/F1 changes. These are counterfactual effects under supplied labels, not feasible models, guaranteed upper bounds or new validation. Their interaction/non-monotonicity prevents summing the deltas as total loss. No further oracle variants or search are allowed.

Both counterfactuals require a supported latent H/A/D decision: exclude every latent-X/materialized row from both repairs, even when its final error involves D. Count excluded carried errors separately. This planner decision resolves the fresh builder check's sole question: it isolates model-objective errors rather than attributing unsupported carry to the head; the cost is that it does not measure all possible liveness headroom in unsupported rows. Unit tests pin this eligibility before real analysis.

The counterfactuals answer whether the two observed error families alter spell quality on these fixed used cases. They do not select a threshold or a model; any later intervention needs a separate protocol. Record five frozen baseline metric reconciliations and ten reference-conditioned counterfactual evaluations in the new generation, distinct from the historical WCSF three-method audit.

## Replay, binding and output protocol

Create `ownership_run.py` for the CLI `freeze`, `run`, `summarize`, `verify`, each with an explicit new `--run-id`. This is an additive execution-boundary change to the original proposed CLI, not an edit to its frozen documents. Sources include all local Python dependencies reached from explicit entry points/imports; pin the model, selection, approved documents, prior pilot/results/seals and exact consumed cache/raw/store/index/prediction hashes. Environment records Python/NumPy/pandas/SQLite and platform. No dependency installation.

Use the known original cache paths under sibling `independent-reference`/`external-reference`, and WCSF `wcsf-reference/wcsf-2026-11-09-2`. Resolve only the declared files. Hashes for the four cases must match the retained pilot input maps. WCSF DB hashes must match acquisition and existing control/index hashes must match prediction seals. Geometry/index and final labels must match the retained WCSF arrays exactly; four-case known-live/swap/raw-correct-final-wrong/raw-wrong-final-correct totals must match the original pilot before deeper reporting. Reject drift rather than rebuilding/reselecting.

Freeze code/protocol/input identities before real diagnostic computation. One case at a time; create exclusive attempt claims and incomplete markers, then promote validated aggregate receipts with no overwrite. Existing/incomplete run IDs cannot be silently reused or deleted. Keep private logs/intermediates outside the public report directory. `verify` is read-only and never infers or evaluates another variant. Source/input mutations, missing/extra cases, partial receipts and invalid egress fail closed. Preserve prior release/scientific files, original logs and recovery ledgers.

Public reports pass the existing `assert_public_report` plus an owned schema whitelist. Only named scalars/counts, fixed confusion matrices and hash identities are allowed; no location arrays hidden behind new keys, reference traces, raw paths, predictions or episode coordinates. Case receipts identify their source/protocol and expected method count. Summary keeps provider/case support visible; it does not treat five cases or adjacent frames as independent fresh samples.

## Tests planned before implementation

- Exhaustive enumeration of all 3^n paths at lengths 1..5: unconstrained labels/objective, every forced state, forward/backward score and emission-minus-switch decomposition; toy expected values independent of the implementation.
- Same prefix/different suffix, real D, neutral gaps, empty/nonfinite/overflow inputs, negative costs, H/A exchange under a unique optimum, deterministic ties and patch boundary-switch algebra.
- Source barriers, wholly unsupported segments, period resets, reference-mask perturbation with unchanged inferred paths, and separate carried errors.
- Synthetic same-team spell matching with one-to-one collisions, no overlap, below-threshold overlap, splits/merges, GT-X holes, per-period pooling and both signed diagnostic counterfactuals. Compare baseline spell counts with official helpers.
- Input/model/source/hash mutations, omitted source entries, extra/missing/duplicate cases, interrupted/existing run IDs, concurrent claims, corrupted persisted receipts and event arrays disguised under plausible keys.
- Exact four-case pilot and WCSF index/prediction/aggregate parity; full regression suite once after final implementation, plus one fresh whole-change mathematical/protocol review and one material RED→GREEN fix pass if required.

Write actual tests first, observe missing-feature failures, implement to pass, and run the checks again after implementation. The user's request for tests after implementation is satisfied by the GREEN and final verification runs, with test definitions fixed before code/outcomes.

## Deliverables and stop rule

Deliver tested instrumentation, frozen five-case aggregate findings, reproducible local commands, provenance/verification receipts, one fresh review and a recommendation for at most one later intervention or an explicitly unresolved result. No production prediction source, release artifact, current target CSV or historical evidence changes. Preserve the original four-case results separately from the WCSF extension and all new diagnostic attempts honestly. Do not claim that the diagnostic itself improves performance.
