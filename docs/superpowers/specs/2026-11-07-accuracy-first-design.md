# Accuracy-first possession experiment — proposed design

Status: approved by the user on7 November2026 and executed as the bounded experiment. The original approved proposal SHA256 is recorded in the audit ledger; the results and review response document completion. Preserved baseline commit `9bd11dc847f71973782ea268045609f6a8c6bffd`; source/models, Desktop installation and experimental CSVs remain unchanged.

## Intent and success

The user asked to push accuracy upward using Superpowers. The goal is better possession decisions, not fewer X labels. Use the official team-possession spellF1 averaged over IoU thresholds0.3–0.7 as primary, with macroF1, raw-frame accuracy, H/A/D confusions and boundary errors alongside it. There is no defensible promise of100% correctness.

The existing four-policy comparison is already frozen. A read-only audit of the original external **development** references found26987 incorrect non-X incumbent labels among571928 known DFL frames, and36029 among653182 known SkillCorner frames. Even an oracle filling every X correctly cannot exceed95.28%/94.48% frame accuracy if it is forbidden to revise those non-X labels. This is an external reference bound, not target accuracy. H/A swaps account for24497/35820 of those protected errors. See `next-phase-notes/accuracy-development-loss-audit.json` in the workspace; no target data were used.

## Approaches and proposal

1. **Wait for a genuinely fresh full H/A/D reference before any model work.** Strongest independent evidence, but the data scout has not verified an accessible appropriately licensed cohort. The user approved independent accuracy evaluation; acquiring a qualified cohort remains the preferred validation route.
2. **Recommended builder proposal: one bounded soft-sequence experiment on the existing licensed external data, with explicit seen-data limitations.** Reuse both frozen heads, let their finite evidence revise existing H/A/D labels, and decode a consistent sequence. This directly tests the protected-error finding without a new neural training pipeline. It can demonstrate an exploratory external benchmark gain; it cannot demonstrate new-data generalization.
3. **Train a new joint deep model or add more detection/camera components immediately.** More flexibility and cost, while the independent-reference gap remains. Defer unless the bounded experiment identifies an evidence failure that a decoder cannot solve. Continuing to fill only X cannot correct the measured protected errors.

The user's selected high-level route is external validation first. The soft-decoder details and the decision to continue experimental development while fresh data is unavailable are proposed here for approval, not represented as already approved.

## One concrete change

Add a three-state offline Viterbi decoder using finite soft emissions for H/A/D. The current incumbent labels never become infinitely hard anchors. Reference labels, reference-known masks, phase IDs, BallStatus/BallPossession and automatic tagging are absent from the inference API.

For usable input frames, obtain the unchanged tactical tree's raw H/A/D leaf supports and the unchanged motion model's symmetric H/A score on **all usable frames**, including frames the incumbent decided. These are scores, not calibrated probabilities. Form relative emissions:

`log(max(p_H,1e-6)) - w*z/2`, `log(max(p_A,1e-6)) + w*z/2`, `log(max(p_D,1e-6))`.

Use the frozen raw motion score `z` and preserve float32 feature conversion. Its original training sampled incumbent-X rows, so applying it to decided rows is a distribution shift to test externally; it is not presumed valid. A `w=0` comparator isolates tactical-head sequence smoothing. Every H/A/D switch costs a finite `c`. Parameter grid is fixed before any candidate score: `w in (0,0.25,0.5,1)` and `c in (0,2,8,32)`,16 candidates. Include current incumbent/carry/agreement/agreement-plus-carry baselines. Ties are deterministic H,A,D order and are reported.

Frames outside periods1/2 remain X. Invalid geometry or insufficient source geometry is a decoder barrier, not a zero logit converted to H: require valid geometry and either an observed ball with both nearest-team distances, or at least3 available points for each team. These eligibility choices are fixed engineering calls, not tuned to the target. Split at period/geometry barriers. Preserve an X latent output at barriers and export explicit structural-period carry separately; no reference mask is used for carry. No fixed D interval or source-speed interpretation is added.

## Data and selection

No new model/head fitting in this experiment. Existing DFL/SkillCorner licences and source provenance remain in force. Freeze the candidate source, parameters, split IDs, source-cache hashes and model IDs before scoring the16 settings. Use the same automatic anonymous-correspondence adapter for incumbent comparators and candidate inputs. Cached coordinates may include provider-identity-assisted25Hz interpolation; disclose this limitation. Input-only masking has seed1729 and30% contiguous ball gaps, using the existing frozen masking definition, applied equally to all comparators/candidates. No labels or target missingness pattern determine the masks.

Select using only the previously designated external validation matches: DFL `J03WQQ`, SkillCorner `2006229,2006363`. All have been examined previously; these are **seen validation**, not fresh. Neither head was fitted on these matches, but prior project-wide exploration limits the interpretation. Give each provider equal weight, then matches equal weight within provider. Maximize natural-input mean spellF1; break ties by mean macroF1, then lower motion weight and lower switch cost. Report masked validation as a fixed stress, not another selection loop. If the selected candidate does not improve natural spellF1 over the current agreement-plus-carry candidate, retain the current candidate and report rejection.

After selection, freeze the selected artifact before a **single seen-regression comparison**, without further tuning: DFL `J03WR9,J03WN1`; SkillCorner `2007448,2007721,2010085,2011166,2013725,2015213,2016236,2017461`. These are previously opened old tests and must never be renamed independent holdouts. Report provider means, paired match deltas, per-class errors, corrections/regressions to incumbent decisions, false splits/merges and reference-supported versus unmeasured output. No artificial90% label gate or no-per-match-decline acceptance rule. If seen-regression primary quality declines, do not promote; retain the baseline and document why. Report frame accuracy even when it disagrees with spell quality.

If an actually qualified fresh cohort becomes available, check explicit rights, complete/reference semantics, clock alignment and non-overlap using documentation first; pin it and freeze protocol before opening/scoring labels. It is confirmatory only, with no parameter reselection. Otherwise state plainly that independent accuracy validation is still unavailable.

## Runtime and integration

Keep standard-library inference; NumPy is allowed for external experiments. Make an isolated verified copy of the203-file published tree after approval, because no local git repository exists. Add modules/tests/drivers; do not alter the34 frozen sources, model artifacts or standalone Desktop pipeline. Implement TDD and one fresh whole-change review. Meaningful tests cover correction of finite wrong anchors, period/quality barriers, H/A symmetry, parameter validity, exact source/model/cache binding, score-only aggregate exports and no reference leakage into inference.

An external result alone does not certify the target. Do not run or replace target outputs to pick parameters. If the prospective candidate is rejected, deliver its external evidence and keep the existing CLI unchanged. If it improves both validation and seen-regression primary metrics, deliver an explicitly experimental opt-in route; target inference, if performed, is a separate reproducibility/format exercise only. Preserve latent uncertainty and all four original comparator outputs. No baseline promotion or claim of target correctness follows from lower X or a software-test count.

## Documentation and final deliverables

Record design/plan, source/model/data hashes, exact commands, scalar/count aggregate score tables, source/reference limitations, rejected variants and the fresh review response. No raw assets, frame-level reference/prediction data or transition event arrays are published. Update the existing GitHub PR with safe code/docs/results; do not merge or alter repository visibility.

The expected outcome is a completed, reproducible external accuracy experiment with an honestly accepted or rejected candidate. New-data and target correctness may remain unmeasured; that limitation cannot be solved by relabelling old tests or forcing output coverage.
