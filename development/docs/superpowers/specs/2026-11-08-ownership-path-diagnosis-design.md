# Whole-segment ownership diagnosis — proposed design

8 November2026. Scope: plan one bounded, read-only attribution experiment; preserve released candidate `w0-c32-neutral-missing` and commit `cee674190775e9356745f461ba1561e9f2a46f7e`. The user requested Superpowers planning and a five-advisor Council diagnosis, then a full adversarial repository audit. No production refit, parameter selection or challenge comparison is part of this design.

## Why this diagnostic

Five independent advisors, five fresh anonymous reviewers and a separate chairman challenged the ownership-model premise. The completed read-only replay on SkillCorner1874553/1886347 and DFLJ03WOH/J03WOY found remembered automatic control opposite the reference on94.16%/92.03%of H/A swap frames. That is correlation, because memory and model share geometry. On observed usable live rows, decoding corrects more raw-tree decisions than it spoils in aggregate:2720versus431for SkillCorner and1828versus1661for DFL. Observed reference interiors still contain5602/112356and2883/84921swap frames beyond2sfrom known state boundaries/annotation edges. A consistent team exchange changes690/161785and1194/148231known-live outputs; asymmetry exists but is not established as the main cause.

Coordinates are available on most frames, so their raw share of errors cannot establish missingness is unimportant. SkillCorner has known-play H/A phase reference only, DFL full-state provider flags with frozen-inactive-coordinate shortcut. All matches are already seen; no independent physical-control truth or target accuracy is established. Clock/ID checks support mechanical consistency, not possession semantics.

## Approaches

1. **Recommended within the requested diagnosis:** attribute the unchanged decoder's decisions using whole-segment path scores, fixed reference patches and carry accounting. This tests whether the objective favors wrong local evidence, avoids additional switches, or uses future context. It can explain the model's decision against a provider reference, not prove who physically controlled the ball.
2. Immediately refit an all-frame head while adding movement/receiving features and symmetry. Potential upside, but too many changing factors to attribute the result. Defer until a single mechanism is supported and the subsequent adversarial audit is reviewed.
3. Change the reference clock/team mapping or lower switch cost on these examples. No global correction is established, and selecting a favorable alignment/cost on the diagnosis would turn explanation into tuning. Do not do that.

The requested current deliverable is diagnosis and a plan. This design proposes approach1for a subsequent bounded experiment; it does not silently authorize training or execution of a new predictor. The already completed four-match replay is exploratory evidence, not this stronger causal-path calculation.

## Fixed inputs and algorithm

Use only the same four development matches, natural inputs, original input hashes, source/model/release identities and25Hz canonical grid. No fresh mask, label-lag search, video/GT inspection, hand labels or new external assets. Keep periods, geometry eligibility, neutral missing emissions, unsupported segments, c=32, w=0, floor1e-6and H/A/D tie order exactly unchanged. Anonymous player identity is not a selected feature; do not introduce native identity-dependent features.

Construct every complete usable segment from **input-only** periods/eligibility. Segments without observed ball remain latent X as in the release. Reference labels must never split an inference segment; unknown reference regions remain inside the model path and are excluded only from evaluation. Materialization is audited separately and must not become evidence in path scoring.

For each actual source segment, compute forward and backward max scores with state H/A/D and switch cost32. At a known-live frame, compare the best **complete segment** path constrained there to the reference owner with the best complete path constrained to the opposite owner. Retain the best unconstrained D state too: H/A-only forced comparisons do not redefine live/dead inference.

Let F-before include emissions/transitions strictly before the current emission, E be its three scores, and B-after include future emissions/transitions after the current state. For opposite owner O and reference owner R, report signed margin:

`M_full = (F_before[O]-F_before[R]) + (E[O]-E[R]) + (B_after[O]-B_after[R])`.

Positive favors O. Report prefix/local/future contributions and `M_full - M_prefix`, without describing a future contribution as proof of physical cause. Track cumulative emission and transition-count contributions of each constrained optimum with deterministic H/A/D predecessor/successor tie order; ties can have multiple decompositions, so report tie counts and avoid causal certainty from one tied path. No new emission/head/cost is selected.

Also patch each contiguous H/A swap episode with the reference state while holding the rest of the original full path fixed. Episodes must split at reference identity, predicted identity, known-reference runs, structural period and source barriers. The change in objective equals emission gain minus32times the additional switch count. Report episodes/frames where cumulative emission favors the wrong state, where a reference-favoring patch loses to switch cost, and where ties/unsupported evidence leave attribution unresolved. These fixed counterfactual score calculations are diagnostics, not exported prediction candidates.

## Verification and report

The new path scorer must match exhaustive enumeration on short synthetic three-state sequences, including neutral spans, genuine D, boundary conditions and ties. Verify objective decomposition, forward/backward constrained optima, no crossing of source barriers, and independence of inferred paths from the reference-known mask. Reproduce the frozen decoder's objective and label output before applying diagnostic constraints; reject a mismatch. Reproduce every original four-match aggregate and pin all consumed source/cache identities before the deeper report.

Report per provider and match: support denominators, episode counts/durations, boundary-distance strata, reference-team rates, local/global score margins and decomposition, source quality/carry cases, and signed matched ownership-boundary timing. Use the unchanged12/25frame boundary tolerances, including missed/spurious counts alongside conditional timing. Keep all per-frame arrays, episode locations and reference traces local; publish bounded scalar/count aggregates only. No statistical independence claim from adjacent frames or Council agreement. Equal provider/match summaries supplement, not replace, per-case values.

Stop after the fixed four cases. If future context/switch penalty dominates identifiable reference-favoring episodes, propose one later decoder-only contrast. If observed interior emissions already favor the opposite owner, propose one geometry/memory-only contrast. If ambiguity clusters around provider boundaries/ties or source carry, retain that uncertainty. No production head refit follows automatically. The full adversarial audit requested by the user must be reviewed before committing to that later intervention.

## Deliverables and limits

For the current request: Council verdict/transcript, completed four-match aggregate diagnosis, this reviewed design and a concrete Superpowers implementation plan. Build/execution of the proposed whole-path instrument is a subsequent step, not concealed as already done. The plan must name exact interfaces, tests, source/egress guards, stop rules and commands. All existing candidates, sealed309-file release and Desktop pipeline stay intact.

The diagnostic explains an optimization decision relative to provider labels. It cannot establish provider control truth, target accuracy, new-data generalization, or that correlated memory is causal. Any later improvement must use external data and fresh validation when available, preserve D/missed-transition visibility and avoid another bundled feature/training search.
