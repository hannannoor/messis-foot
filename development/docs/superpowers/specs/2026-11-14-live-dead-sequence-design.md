# Dedicated live/dead sequence model: design for approval

14 November 2026. **Proposed design, not approved for implementation.** The user chose option 1, a dedicated live/dead sequence model, after the broadcast proposal audit. Numerical settings, model family, player-only representation, safeguards and evaluation below are the author's proposals for approval. No new fit, inference, scoring, dependency installation or provided-match processing has been authorised by this file alone.

## Intent and evidence

Find better evidence for stoppages while retaining the frozen release as the comparison and submission. Experiment E added a stillness feature to the joint ownership tree; the resulting split affected missing-ball rows whose emissions were neutralised. Experiment F then acted only in the external provider with no known D reference. Neither establishes that an independently trained temporal liveness head cannot help on visible-ball rows.

The hypothesis is that ordered player movement around a frame distinguishes a pause and restart from active possession better than one instant can. This is an offline estimator: up to two seconds of future input is permitted. It is not a claim that all stoppages are observable from players, or that low movement proves dead ball.

The WCSF control's D recall is about .496; this is one already-used external match. Its large missed-D frame count does not establish the share of lost possession-spell F1. Earlier reference-assisted ownership and liveness repairs are diagnostics, not feasible predictors or attainable gain estimates.

Owning evidence: `docs/wcsf-transfer-results.md`, `docs/ownership-path-findings.md`; sibling `player-stillness-work/reports/player-stillness/2026-11-12-a/report.md`, `missing-evidence-work/reports/missing-evidence/2026-11-13-a/report.md`, and `ownership-only-work/reports/ownership-only/2026-11-12-a/report.md`. Preserve every prior experiment and its exhausted budget.

## Goals, non-goals and failure conditions

- Primary goal: improve externally measured final possession-spell F1 with a dedicated live/dead head and demonstrate an incremental temporal benefit.
- Mechanism goal: recover more WCSF dead-ball frames without sacrificing D precision or introducing unacceptable live-play fragmentation.
- Operational goal: a bounded external-only experiment using the existing installed environments and data. The proposed budget is one working day, capped at 24 elapsed hours from the first implementation action after plan approval; record start and deadline in Asia/Singapore.
- Non-goals: broadcast alignment; pixels or audio; new data acquisition; training an H/A head; changing transition costs, gap logic, restart logic or kickoff handling; tuning on the provided game; release installation or submission promotion.
- Failure includes an apparently better frame classifier that worsens possession spells, insufficient temporal support, unresolved input identities, budget expiry or selecting a second version after seeing outcomes.

## Approaches and selection

1. **Dedicated player-based temporal live/dead model: selected direction.** Use ordered tracking context, with the release's conditional H/A evidence retained. It can be checked against external D labels without camera synchronisation. Its risks are tracking-support differences, provider-specific motion conventions and uncertain binary scores.
2. **Transition/boundary verifier.** Learn evidence for H/A/D changes directly. It addresses more error types but introduces transition-target conventions and a larger change in decoding. Deferred.
3. **Whistle-audio evidence.** A genuinely additional observation, conditional on usable audio and external validation. Availability and timing are unresolved. Deferred.

Within option 1 the author proposes a small random forest over an ordered window, rather than a new neural training stack. This is a temporal classifier, not a recurrent network. Keeping the sample positions separate permits before/after patterns; it does not guarantee the forest learns those patterns. A matched instantaneous forest tests the incremental value of context. Do not describe the single-frame comparator as user-selected or promote it if the temporal experiment fails.

## Inputs and representation

Use geometry-only external player tracks, periods, canonical pitch dimensions and existing player associations from the pinned adapters. Do not read ball positions, ball availability, ownership predictions, event tags, reference status, provider identity, match identity, absolute frame/time or half number into the liveness feature function. Period is a boundary barrier only. References enter fitting targets and evaluation, never feature construction or inference eligibility.

The author chooses a player-only first experiment because ball freezing previously inflated external D evidence. Player freezing, smoothing and association quality can still differ by provider; removing the ball does not remove that risk.

Construct ten finite values at each canonical 25 Hz row:

1. Observed player count, capped at 22, divided by 22.
2. Usable speed-pair count, capped at 22, divided by 22.
3-5. Speed quartiles at .25, .50 and .75, divided by 12 m/s.
6. Fraction of usable speeds below 1 m/s.
7. Fraction of usable speeds above 3 m/s.
8. Pooled player RMS distance from the pooled centroid, divided by the canonical pitch diagonal.
9. Spatial-support mask.
10. Motion-support mask.

Pool both teams so swapping home and away cannot change any feature. For speeds, require the same unique non-null associated ID on the same team at rows t and t-5, finite valid geometry throughout those six rows, and the same nonzero period. Speed is displacement / .2 s. Reject speeds >=12 m/s rather than clipping them into evidence. No claim is made that associated IDs are true person identities. Spatial support requires at least 10 finite player positions with unique IDs within their team; motion support requires at least 10 usable pairs. Unsupported feature groups are zero with their mask zero. Use linearly interpolated quantiles, as defined in the implementation plan, with no provider-specific thresholds.

For each centre t, concatenate these vectors at offsets -50, -45, ..., 0, ..., +45, +50 rows: 21 positions, 210 columns, in chronological order. A position across a period boundary, outside the recording, or across any invalid-geometry barrier is unsupported, never padded by repeating an edge observation. The centre needs spatial and motion support and at least five motion-supported positions strictly before and five strictly after it. This fixed eligibility applies to training, both new model streams and inference. Availability may use future geometry; it may not use future reference labels.

The instantaneous comparator uses only the ten centre values but exactly the same eligible fitting rows and inference mask. Report temporal coverage, support counts and fallback by case, period and observed/missing-ball stratum in evaluation. Do not use reference-X gaps as inference barriers or infer missing support from annotation availability.

**Fixed support floors (author's decision after builder check):** each training match must supply at least 1,000 selected eligible rows, including at least 125 D and 125 live targets. For every primary evaluation case in each regime that is run, require at least 1,000 integration-eligible rows and integration eligibility on at least 10% of all active-period, ball-observed, release-geometry-valid rows. The integration-eligible set means the intersection of that denominator with the temporal eligibility mask, before reading reference labels. Require at least 125 known-live reference rows in that set per primary case and at least 125 known-D reference rows in it per primary DFL/WCSF case. SkillCorner has no D-support requirement. Reference-stratum counts are evaluation-support checks only; they never determine inference eligibility. These floors are practical safeguards against a nearly all-fallback experiment, not power calculations. A missing/zero denominator or failed required floor is UNRESOLVED; report all shortfalls and stop before fits for a training shortfall, or before prediction/scoring for an evaluation-regime shortfall. Do not drop the case, reduce a floor, or add a replacement regime. Secondary cases receive coverage reports without these evaluation floors.

## Fitting and model scope

Use the four existing DFL training matches in historical order: J03WOH, J03WOY, J03WPY, J03WMX. Reuse the hash-bound raw player inputs, caches, canonical transforms and alignment checks from `player_stillness_training.load_training_groups` and the earlier input bindings. Do not silently substitute caches with different geometry or regenerate historical stores. The implementation plan must pin the exact source/import closure and private input manifest before execution.

Fit on natural player tracks only. Select every fifth canonical row with known reference H/A/D and the fixed input-only eligibility above. Target is 1 for D and 0 for H/A. Reference-X is excluded only from supervised targets. Build windows on full geometry before target selection. Give each training match unit-total sample weight; do not balance D and live classes or duplicate ball-masked copies of identical player features. Record exact counts, class support and semantic array hashes in preflight; both classes must be present in every training match.

Exactly two fits: an instantaneous comparator and a temporal candidate. For both use installed scikit-learn `RandomForestClassifier(n_estimators=32, max_depth=6, min_samples_leaf=125, max_features=1.0, bootstrap=True, criterion='gini', class_weight=None, random_state=1729, n_jobs=1)`. No parameter search, calibration, extra seeds or early selection. The recipe is an author-selected bounded baseline, not a previously validated optimum. Both models use identical row identities, targets and weights.

Forest scores are empirical leaf fractions, not established calibrated probabilities. Export tree arrays and evaluate by the same float32 input/split convention as scikit-learn; require dead-score absolute error <=1e-12 for all fitting rows and synthetic edge cases. Export the new models separately; the frozen ownership model and its artifact remain unchanged. No dependency installation is in scope. If the pinned existing environment cannot support this, stop and report it.

## Integration with the release

Reuse the existing support-supplied research assembly, verified against `restart_release.assemble`, with empty kickoff starts for every external stream. The comparator is the actual frozen final pipeline, not only its first decode. Preserve cost 32, usability, missing-ball neutrality, materialisation, gap rule, decoder restart, second gap rule and kickoff logic.

Let the frozen three-state supports be h, a, d. On a temporal-eligible row with an observed ball and valid release geometry, let q be the new dead score clipped to [1e-6, 1-1e-6]. Set r=h/(h+a) when h+a>0 and r=.5 otherwise. Substitute `( (1-q)*r, (1-q)*(1-r), q )`. Apply the identical substitution for the instantaneous stream using its own q. On every other row copy the frozen support triple exactly. No fusion weight is fitted; the new head replaces the D-versus-live allocation on supported observed rows. It is not multiplied into the old D score as independent evidence.

This deliberately targets visible-ball rows, where the current D benchmark has room to act. Missing-ball emissions stay neutral under the existing assembly; no repeat of F's missing-ball amendment is included. The sequence model still receives no ball information. The wrapper uses ball availability only to select the predeclared integration rows.

Conditional H/A support ratios are preserved when h+a>0. Final H/A labels can nevertheless change through sequence decoding and changed D boundaries; do not promise fixed ownership labels. Existing gap-rule stoppage intervals depend only on the same frames and must remain identical. A disabled, absent or wholly unsupported head must reproduce frozen supports, latent labels, final labels and CSV bytes exactly. Malformed supplied models/inputs fail clearly; they are not silently treated as optional absence.

## Evaluation and decision

No new data acquisition. All evaluation is reused development/regression evidence, not a fresh holdout or a challenge-performance estimate.

Primary cases: DFL J03WR9 and J03WN1; WCSF `wcsf-used-match`, both halves pooled; SkillCorner 1874553, 1886347, 2007448, 2007721, 2010085, 2011166, 2013725, 2015213, 2016236, 2017461. These 13 cases are fitting-disjoint. DFL J03WOH and J03WOY are secondary training-overlap diagnostics, excluded from all benefit/loss gates. Use the existing canonical adapters and input identities from `docs/recent-geometry-protocol.md` and its records. SkillCorner has no known D reference: it supplies a known-live harm check, not D recall evidence.

Three fixed streams: frozen release, instantaneous binary-head integration, temporal binary-head integration. Primary score is the exact official five-IoU possession-spell F1, equal provider weight (1/3 each), equal match weight within provider. Pool WCSF halves before scoring. Retain per-IoU TP/FP/FN, macro F1, class confusion, D precision/recall, known-live false-D fraction, possession counts/durations, short-spell matches and restart diagnostics. Report corrections and newly introduced errors in visible/missing and supported/fallback strata. No significance or population claims.

Stage 1 is natural inputs on all 15 cases. Advance to stage 2 only if every natural requirement holds:

- Temporal minus release primary spell F1 >=.010, every primary provider delta >=-1e-6, and every primary case delta >=-.020-1e-6.
- Temporal minus instantaneous primary spell F1 >1e-6. Otherwise the experiment has not demonstrated incremental temporal value; do not substitute the instantaneous model as a second selected candidate.
- WCSF temporal D recall rises >=.030 versus release. On each primary DFL/WCSF match, D precision and D recall each lose no more than .010+1e-6. Thus WCSF has the stronger recall requirement. Missing required support is unresolved, not a pass.
- On every primary match, the known-live false-D fraction rises no more than .005+1e-6; both H and A remain represented wherever each has reference support.
- Short reference possessions <=25 rows, evaluated at IoU .5: at least 20 spells permits recall loss <=.020+1e-6; 1-19 permits no lost matched count; zero is explicitly non-applicable. Compare temporal against release.
- All parity, provenance, temporal coverage accounting and budget checks pass. Report strict observed-interior team accuracy, but do not require improvement: the new hypothesis concerns liveness, and a fixed-boundary H/A improvement would be a different objective.

The .010/.030 thresholds are practical author-proposed hurdles, not significance bands or predicted gains. Add only 1e-12 round-off tolerance to comparisons; exact counts and identities remain exact.

Stage 2, if reached, uses the same three frozen streams on two reference-independent stress regimes for the 13 primary cases:

1. Existing visible-ball jitter: independent .25 m Gaussian noise on observed ball x/y; players unchanged. The liveness features and scores must remain exactly invariant; integration/release emissions may change.
2. Player degradation: remove 25% of associated player tracks per fixed five-second block, then add independent .25 m Gaussian noise to retained player x/y at each canonical row. Never alter the ball, periods or references. Removal must be keyed by (case, period, block index, team, ID), not by reference. Use SHA-256-based seeds with fixed prefix `live-dead-sequence-v1:1729:`; the exact portable draw order, association timing and block convention must be fixed in the implementation plan before any run. Recompute speed support and every affected frozen-model input consistently; never pair a new liveness prediction with stale frozen supports.

For each stress regime, temporal must lose <=.005+1e-6 primary spell F1 against the release under the same transformed input and <=.020+1e-6 per primary case; retain the natural D, false-D, owner-presence and short-spell harm limits. The +.010 spell gain, +.030 WCSF recall and temporal-over-instantaneous benefit hurdles apply only to natural inputs. Record fallback separately so robustness cannot be misrepresented as useful coverage. Both new heads and the release receive identical transformed geometry.

A complete PASS means **supports a separate release investigation**, not permission to run on the provided match or replace the submission. A scientific failure is NO_ADVANCEMENT for this fixed recipe. Integrity problems, insufficient required support, incomplete execution or timeout are UNRESOLVED/INVALID, never evidence that the method helps or fails scientifically. Retain all completed outcomes. Do not change gates after opening results.

## Budget, preservation and verification

This is a new proposed experiment budget, separate from every closed experiment. Maximum two fits, one temporal candidate, one instantaneous comparator, one seed and one window. Maximum 41 case/regime bundles (15 natural + 13 per stress), each with exactly three scientific prediction/assembly streams and three official score bundles: 123 each, at most two decoder passes per assembly (246 scientific passes). Synthetic implementation checks and explicitly identified baseline-parity replays are separate; the plan must enumerate and cap the latter before execution rather than hiding them in the scientific budget. No real fit or score may be used as an uncounted scratch dry run.

Freeze and commit source/model recipe, design/approved-plan hashes, environments, exact input bindings, random rules, gates and a cumulative attempt ledger before scientific work. Count failed attempts before entry; a defect is not an automatic new scientific budget. Hash saved features/scores/labels privately so later verification can use rehashing and arithmetic rather than re-running models or scorers. No heavyweight reuse of old experiment ledgers and no rewriting their records.

Required implementation checks: feature independence from ball/status/reference and team exchange; ordered-window indexing, masks and barriers; ID ambiguity, outlier speeds and sparse support; identical training rows between models; exporter parity; exact disabled/unsupported-head release parity; normalised supports and H/A ratio invariant; original gap-interval equality; stress input consistency; exact baseline metric reconciliation; and untouched historical files/artifacts. Synthetic fixtures establish mechanics, not real-match accuracy.

Use a new isolated worktree/branch at implementation, based on an exact pinned source checkpoint containing the required immutable adapters. Current design checkout was clean at source checkpoint `693981530ca99218c400ee5b07fbad61b68395c2`. Some later feature/training helpers exist only in sibling experiment checkouts; do not assume this checkpoint contains them. The implementation plan must choose the exact dependency closure and source checkpoint without silently changing release behaviour. Add new files only; do not overwrite historical adapters, outputs, models or documents. Keep raw tracking, references, per-row predictions and reconstruction-capable derivatives in a separate private local root. Commit code, models, settings and bounded aggregate reports only. No provided match, public-window evaluation, hosted-model data upload, push, merge, PR, release installation or submission upload is included.

## Left to the builder and approval boundary

The builder may choose additive module names, report layout, chunk sizes and implementation details that preserve this contract. The plan must settle deterministic stress mechanics, quantile formula, input/import pinning, bounded parity-replay counts, portable export and the exact start/deadline record before execution. A missing dataset, absent motion IDs, incompatible adapter or runtime limitation is reported, not repaired by changing the cohort or consulting the provided game.

Builder check: a fresh ML-engineering reviewer read this draft and the relevant adapters. Their sole material question was whether insufficient temporal coverage is a reporting issue or an execution stop. The author resolved it with the explicit support floors above. Their source inspection also confirmed that the retained adapters provide associated player IDs; the feature contract still measures support and does not treat those IDs as verified identities.

Hand over the reviewed design for approval. Only after design approval invoke `superpowers:writing-plans`. No implementation begins under the brainstorming approval alone.
