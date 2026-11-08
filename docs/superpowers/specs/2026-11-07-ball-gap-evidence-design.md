# Ball gaps without invented dead-ball evidence

Status: proposed for design approval, 7 November 2026. No candidate inference behavior has been changed. This follows the user's go-ahead to address the ball-gap failure identified after the accuracy-first experiment. The algorithm and acceptance rules below are the builder's proposed calls, not claims of prior detailed approval.

## Intent and evidence

Improve the current experimental `w0-c32` sequence candidate where missing ball observations cause false D predictions. Preserve its possession-spell improvement while checking that genuine stoppages are still recovered. A lower X count is not success and target accuracy remains unmeasured.

Published baseline: commit `b43327c101a8e33cadd5cf4f8a892910bad24c42`, open PR1 on `codex/tactical-validation-and-coverage`. Preserve this candidate, all four older policies, the Desktop installation and all original frozen sources/artifacts/reports. No refitting, new tracking model, camera fusion or confidence-threshold search in this experiment.

The original seen-regression results already showed SkillCorner masked-input mean frame accuracy falling from 80.95% for agreement-plus-carry to 75.78% for w0-c32. A subsequent pooled confusion audit found false D on 9.3565% of 612173 known-live regression frames under masking, versus 0.4177% naturally. These pooled error fractions are not per-match mean accuracy.

A read-only reproduction on two previously used external **development** matches, SkillCorner 1874553 and 1886347, reproduced masked false D on 7760/81805 and 7642/79980 known-live frames (9.4860% and 9.5549%). Of these false D frames, 7638 and 7583 respectively have missing ball observations. This establishes concentration in gaps, not a claim that every false D is inside a synthetic mask or that there is only one possible cause.

The source trace explains a mechanism: `feature_rows` appends speed zero on a missing observation. After the 12-sample recent-speed window empties, a missing ball takes the tree's `recent_speed <= 0.01041` branch. The subsequent missing-ball/last-control branches can favor D; stale control with last-away-distance above 3.1017 has raw leaf support approximately (H .09594, A .06924, D .83482). This is a learned score from the existing external tree, not calibrated correctness. The sequence decoder then treats repeated scores as accumulated evidence. No candidate counterfactual has yet been scored.

## Approaches

The user's selected high-level task is the focused missing-observation correction, checked against real stoppages on external data. Three implementation approaches were considered:

1. **Recommended: remove the tactical head's state preference only when its ball input is missing.** Use equal H/A/D emission scores in these slots, retain the existing temporal objective and observed-ball evidence, and let surrounding states determine any continuation. This directly tests the traced mechanism with one fixed intervention.
2. **Forbid or heavily penalize D in gaps.** This can reduce false D by construction while missing genuine hidden stoppages. It introduces a new penalty/constraint requiring justification; do not use it here.
3. **Refit a missingness-aware joint H/A/D head, possibly using player motion.** Potentially stronger evidence, but it changes training and inference together, and full-state references still have a provider shortcut. Defer until this isolated experiment reveals what remains unsolved.

Only approach 1 is proposed for this cycle. There is one candidate, with no parameter ranking or follow-up search.

## Fixed inference change

Keep the frozen raw tactical tree, motion weight 0, switch cost 32, log floor 1e-6, deterministic H/A/D tie order, periods, source geometry eligibility and original structural carry. Do not edit existing package modules or old artifacts. Add a separate standard-library function and explicitly experimental opt-in entry point.

Start with the existing three log emissions. If the source frame has no finite ball x/y, replace that entire emission triple with `(0, 0, 0)`. All three states therefore have equal local support: this does not assert that play is alive, and D may continue or emerge through surrounding observed evidence. Do not retain the stale H/A preference while selectively suppressing only D. Observed-ball emissions are unchanged, including on the first observation after a gap; residual feature-history effects are measured rather than adding a second intervention.

Keep the original `sequence_usable` mask and split at its barriers and period changes. Within any resulting contiguous segment with **no observed ball anywhere**, emit latent X for the entire segment instead of letting an all-neutral tie invent H. This is the necessary no-evidence convention for the new policy, not a data-selected cutoff. Retain existing explicit structural carry as a separate materialization step; an entirely latent-X active period may therefore materialize as D by convention. Count and disclose this separately from observed dead-ball evidence.

Use no reference-known mask, possession/alive flag, reference boundary, phase ID, video, tag or restart annotation in inference. Available ball coordinates mean coordinates are finite, not verified freshness/native detection. Do not introduce an age threshold, gap-duration threshold, D penalty, learned prior or new motion-head weight. No target inputs determine these choices.

Neutral spans cannot identify an unobserved possession change or hidden stoppage. With different endpoint states, several boundary locations can have equal cost; report the retained deterministic tie convention and do not claim precise timing inside a gap. Surrounding D evidence can extend too far, and D wholly hidden between same-team endpoints may disappear. These are reasons to test full-state references and boundary errors.

## Prospective external comparison

Use the same licensed, pinned external cohorts and old splits. They are all **previously examined** data, not fresh holdouts. The two diagnosis development matches stay outside the validation/regression reports.

- Seen validation: DFL J03WQQ; SkillCorner 2006229 and 2006363.
- Seen regression: DFL J03WR9 and J03WN1; SkillCorner 2007448, 2007721, 2010085, 2011166, 2013725, 2015213, 2016236 and 2017461.
- Each match has natural inputs and the unchanged input-only contiguous 30% ball mask, seed 1729. Do not add a mask tailored to the target or choose a favorable seed.
- Compare the single new policy with frozen w0-c32, and include agreement-plus-carry as the earlier reference comparator. Existing cached original control results may be reused after their identities are verified.

Before any new candidate scoring, freeze the added source bytes, exact policy, comparison/acceptance rules, split and masking definition, original comparison/selection identities, model IDs, consumed feature/reference cache bytes and original score archives/metadata. The driver must verify original evidence using the existing guarded public interface, not bypass old source/model/input bindings. Additional availability masks are derived from the same verified feature cache: finite `ball` for SkillCorner or `ball_xy` for DFL, then the exact frozen input mask. Check original-length periods and dimensions against each score archive. No reference data enter this derivation.

Keep per-frame intermediate masks/predictions locally. Give providers equal weight and matches equal weight within provider for combined means. Publish both per-match means and pooled counts with explicit denominators. Empty denominators are `null`, never a perfect score.

## Metrics and disposition

Report, separately by provider and regime:

- Official team-possession spellF1, frame accuracy and macroF1; paired match deltas and H/A/D-by-H/A/D/X confusion counts.
- False D on reference H/A, with both count and fraction of known-live frames; missed D on reference D, with count and fraction of reference-dead frames. Also D precision/recall and the underlying counts.
- D-interval detection F1 averaged over the same IoU thresholds 0.3, 0.4, 0.5, 0.6 and 0.7, with matched/missed/spurious counts at each threshold. Use the official one-to-one spell matching rule restricted to contiguous D intervals, split at reference-unknown regions and period boundaries; document it as a supplementary dead-interval metric, not the official primary team-spell score.
- Existing official boundary precision/recall/F1, matched/missed/spurious counts, and timing conditional on matches at 12/25 frames. No event locations are published.
- Error counts split by source ball available/missing, explicit neutralized input slots, wholly unsupported segments, latent X and carry materializations. Counts outside reference-supported regions are unmeasured, not correct predictions.

SkillCorner supports known-play H/A only: it measures false D, never D recall or real-stoppage validity. DFL supplies full H/A/D provider reference but includes an inactive-coordinate shortcut, so passing there still cannot establish independent target stoppage performance.

For an experimental opt-in acceptance, require all following comparisons against w0-c32, **separately in seen validation and seen regression**:

1. Natural equal-provider mean official spellF1 and natural equal-provider mean frame accuracy do not decline.
2. Masked SkillCorner mean frame accuracy strictly improves and its mean false-D fraction strictly decreases.
3. Masked equal-provider mean official spellF1 does not decline.
4. DFL mean D recall does not decline, checked separately on natural and masked inputs.

These are proposed conservative no-tradeoff rules with no chosen tolerance or target percentage. They may reject a useful tradeoff; publish that tradeoff rather than silently relaxing a gate. Report whether old agreement-plus-carry masked accuracy was recovered, but it is a comparator, not an extra selected threshold. Supplementary D-interval and boundary results remain visible even if all acceptance checks pass. Never describe passing these rules as target validation.

Run the fixed seen-regression comparison once even if validation rejects the candidate, to document failure scope; its outputs cannot trigger revised settings or a second candidate in this cycle. Freeze the validation disposition before starting that regression. Only offer a new opt-in candidate if both stages pass. Otherwise retain w0-c32 and publish the negative result. Do not repeat or expand the search without a new goal/design.

## Build, review and publication

After approval, use an isolated hash-verified copy of the current 256-file publication because the workspace has no local Git repository. Implement inline with TDD. Cover the decisive synthetic cases: missing-ball D-dominant scores do not accumulate D preference; observed stationary-ball evidence can still yield D; an observed D interval survives across an internal gap; a fully unsupported segment remains latent X; period/geometry barriers; same dimensions/indexing; malformed inputs; H/A emission-swap behavior and deterministic ties. Include a positive H/A/D opt-in CLI fixture, source/model/input/receipt binding and strict aggregate export regressions.

Use the existing fresh/empty-output checks so the new route cannot overwrite either earlier candidate generation. All older CSVs and the original Desktop pipeline remain byte-for-byte intact. If accepted, make two clean local target inference runs solely for reproducibility and official format validation; never use target GT, video or label distributions to select/tune. If rejected, do not generate a new target candidate merely to force a deliverable.

One fresh whole-change review, then one substantive Critical/Important fix pass and appropriate verification; document deferred minor findings. Preserve the exact scoring implementation and receipts if later additive verification is necessary. No head refitting or parameter reselection in response to review.

Deliver the approved design, plan, read-only diagnosis, freeze, safe aggregate receipts, results/tradeoffs, review response and reproduction commands. Use explicit publication allowlists and the strict bounded aggregate validator; exclude external raw data, NPZ caches, per-frame arrays, target CSVs and event locations. Push to the existing PR with a leased ref update after verifying the remote base and all staged blob hashes. Do not merge or change visibility.

## Remaining limits

No fresh licensed full-state cohort has been verified. All scores here are exploratory and repeated use can overfit project decisions even without retraining. Input-only masks are simulated missingness. Some external coordinates use identity-assisted interpolation; the target uses anonymous point association and lacks verified freshness. The tactical head is asymmetric; only the decoder's emission-swap property is promised. Missing evidence cannot reveal a hidden state change, and neutralization can trade false stops for missed stops. An honest rejection is a completed experiment, not a reason to conceal the limitation or force coverage.
