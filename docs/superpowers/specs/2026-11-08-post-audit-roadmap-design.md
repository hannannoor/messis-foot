# Post-audit accuracy and evidence roadmap

Date: 8 November 2026, Singapore. **Status: design being checked before execution.** The user first requested a Superpowers plan, then explicitly instructed the agent to finish planning and execute the next goals, creating a goal only after its predecessor is achieved. That later instruction authorizes the ordered workflow; it is not a claim that the user has individually reviewed the numerical proposals below. Their earlier whole-segment design approval remains specific to that diagnostic.

## Intent and starting point

Improve possession and stoppage correctness, measured with official spell F1 plus frame, stoppage and event diagnostics. Reducing undecided labels alone is not the objective: materializing a label does not create evidence that it is correct. Preserve `cee674190775e9356745f461ba1561e9f2a46f7e` / `w0-c32-neutral-missing` as the frozen experimental control.

Inputs to this proposal are the completed Council/pilot, the approved whole-segment plan, and `../../../../adversarial-review/VERIFIED-AUDIT-RESPONSE.md`. The audit review verified 78 cached external scorings and 341 tests with six skips. It established a synthetic cadence failure, a random-cache-ID portability defect, an old installer version defect and defects in the audit's own manifest. Those are different issues with different acceptance tests.

The immediate engineering question is: **Does one bounded correction to reacquisition velocity remove the demonstrated false-stationarity mechanism without worsening natural inputs or genuine stoppages?** The separate scientific question is whether any gain transfers to independently unused full H/A/D evidence.

## Approaches and proposed choice

1. **Staged mechanism repair, then causal diagnosis and qualification — recommended.** Reproduce cadence failure, compare one narrow feature correction and strong simple baselines, then apply the existing whole-path instrument to unresolved errors. Qualify new reference data in a separate track. This gives interpretable negative or positive results.
2. **Broad retraining with availability, symmetry and a new temporal model.** Potentially useful later; it changes several factors before attribution and lacks fresh full-state qualification. Defer until the measured failure categories justify a particular change.
3. **Packaging/reconstruction first.** Necessary for handoff, but cannot test accuracy. Do cheap documentation repairs alongside engineering and schedule complete export/reconstruction after a method is explicitly chosen.

The user asked to plan from the audited priorities. The detailed staged approach and numerical choices below are the planner's proposal, not previously approved user requirements. Design and companion plans are checked together first; implementation starts only after the planning goal is achieved, under the user's subsequent explicit plan-and-execute instruction.

## Scope, constraints and anti-goals

- Planning deliverables only until this planning goal is complete. Do not create the proposed Python modules or run comparisons while writing/checking the plan. Subsequent execution is limited to its declared external experiment; fitting and target inference remain excluded.
- At execution create an isolated checkout/copy from the reviewed commit through Superpowers isolation. Keep the old 309 tracked files, original source/evidence seals, CSV generations and Desktop installation intact.
- No challenge GT, videos, raw target tracking, target CSV inspection, manual target labels, target tuning, clock fitting or new target inference in these work packages.
- Use existing licensed external caches. Keep references outside inference; never split inference at reference-X holes or reference event boundaries. Per-frame inputs/features/predictions and event locations stay local; publish bounded aggregates only.
- Existing Python/NumPy/unittest; no new runtime dependencies. New portable analysis modules must parse with Python 3.9 grammar. Environment selection is explicit at execution; do not install dependencies during planning.
- Preserve current tree, motion weight 0, switch cost 32, floor 1e-6, source eligibility, neutral missing emissions, wholly unsupported latent-X behavior and separate materialization unless a later approved design specifically changes them.
- Do not rerun the old impossible 27-policy grid, confidence removal, endpoint carry or rejected motion search as new discoveries. Do not assume the proposed candidate or baseline will win.
- No accuracy percentage for the challenge match is available from this work. No automatic merge or claim of final eligibility follows from a passing experiment.

## Workstream A: first bounded engineering experiment

### A1. Preserve the mechanism and build an observation sidecar

Turn the audit's synthetic dense/alternate observation pair into a maintained fixture: 180 frames at 25 Hz; ball `(25 + .08*i, 34)`; three players on each side; one team near the moving ball. Preserve complete selected-runtime baseline outputs H180 dense / D180 alternate as a **known failing behavior**, not desired product behavior.

Add input-only sidecar information about velocity availability, time basis, pair duration, interpolation/provenance and barriers. It must distinguish a measured zero displacement from absence of a usable velocity pair. This sidecar does not change the old 18-feature schema or promise detection freshness. Repeated finite coordinates may be genuine, held or stale; source metadata cannot be invented.

### A2. One predeclared candidate: bounded-reacquisition-speed-v1

This is an experimental compatibility contrast with the old tree, not a complete availability-aware model.

- Begin with the exact original `feature_rows` values.
- Change a speed only on an observed row immediately following a missing-ball row, when a preceding observed ball exists within **five canonical rows and at most .20 seconds**, in the same period and input-usable segment. Do not bridge quality/eligibility/period barriers.
- Prefer the two finite, strictly increasing declared `ball_sample_time_s` values when both are available. If a declared pair is equal, reversed or exceeds .20 s, mark it unavailable and do not repair it. With an incomplete timestamp pair, use `(current_index-previous_observed_index)/25` and label the basis `canonical_grid`; this is not a claim of native sample freshness.
- The candidate value is displacement divided by pair duration, capped at the old **50 m/s**. Use an absolute **1e-9 seconds** arithmetic tolerance at the .20 s upper boundary only, so large elapsed timestamps do not reject an exact five-row interval through subtraction roundoff; this is not a model-acceptance tolerance. Never extrapolate velocity into missing rows. The .20 s horizon is one proposed engineering bound covering the inspected 2/3/5-row cadence fixtures; it is fixed before external scoring and is not searched.
- Replace only `ball_speed` on those eligible reacquisition rows and recompute `recent_speed` using the unchanged **12-canonical-row** rolling mean with those corrected entries. Clear that rolling window on period changes/period-0 exactly as the old generator does; quality/usability barriers reset the candidate's endpoint-pair memory, not additional legacy feature history. All other original features, including control memory and `slow_ball_age`, remain unchanged. Downstream effects on the next 11 recent-speed windows are expected and counted.
- Where no valid pair exists, retain legacy feature values for this compatibility contrast but mark velocity unavailable in the sidecar. **This candidate does not solve every unknown-speed case.** A truly availability-aware fitted head is a later, separately designed intervention.
- A fully observed input without reacquisitions must reproduce all original feature rows and predictions exactly. Observed zero motion with a valid pair remains measured zero; never replace it with an arbitrary moving speed.

The test establishes whether this limited repair is useful. It may fail, especially because the old tree learned different feature statistics. Do not change the horizon, smoothing cost or head after seeing the result.

### A3. Fair strong simple baselines

Port the pinned official nearest-player algorithm and centered H/A-only majority smoother, half-widths **0,25,50,125**. Its missing/no-player convention is D; D is not a third vote. Majority ties prefer H. Preserve attribution and source revision `f8f2629ff1e0985f81d7e59d8413678514ee1530`.

External frames store grouped teams rather than original mixed track-slot order. Raw equal-distance ties therefore use declared home-before-away canonical order and are counted; do not claim original slot-order equivalence on ties. Verify all non-tie nearest decisions and the entire smoothing function against the pinned source on synthetic input. External smoothing resets at input periods, not reference masks; this period wrapper is disclosed separately from the upstream whole-video function.

Compare two named families, all four windows reported:

1. `official-convention`: nearest team when any player and ball exist, otherwise D; per-period centered smoothing; no extra geometry gate or carry.
2. `matched-input`: same nearest rule on current input-usable rows; no vote on missing ball; smoothing within input-usable segments; no-vote output X, then the existing separate structural-period materialization. This family can improve under outages by continuity; it is explicitly not a native D detector.

This avoids claiming success against a weak missing→D convention alone. No baseline window is picked using regression or fresh qualification outcomes; report all four in this exploratory pilot.

### A4. Fixed pilot and decision rules

Exactly four **seen development** matches: SkillCorner 1874553/1886347 and DFL J03WOH/J03WOY. Exactly five regimes per match: natural; retain ball at every 2nd, 3rd or 5th row (offset zero within each source period); the existing 30% contiguous mask with seed 1729. Retention masks clear ball-related fields coherently, preserve player geometry/periods and do not use reference labels. Total **20 cases × 10 variants = 200 aggregate scorings maximum**: frozen control, candidate, and eight baseline settings. Do not expand to the 16-setting grid or full regression cohort here.

Inference uses input periods and barriers only. Score with existing official helpers after inference; keep true-D metrics DFL-only and SkillCorner false-D limited to known-live support. Report per match/provider/regime and equal-provider means, with exact denominators. Include:

- Official spell F1, frame accuracy, DFL D recall and false-D counts, known-live H/A confusion.
- Velocity available/unavailable counts by time basis, pair duration, observed/missing, corrected feature rows and downstream rolling-window changes.
- True spell duration bins `<=1s`, `(1,3]s`, `(3,10]s`, `>10s`; pair-typed H↔A boundary matches/missed/spurious at 12 and 25 frames; signed matched latency with its matched denominator. These are evaluation diagnostics, not reference input to inference.
- Neutral rows, latent X and materialized rows separately; home/away exchange sensitivity and ties separately. Do not label all continuity as observed evidence.

**Continuation gate, not promotion:** candidate must preserve natural equal-provider spell F1 and frame accuracy, preserve natural DFL D recall, improve equal-provider mean cadence spell F1 and reduce cadence known-live false D, and preserve masked equal-provider spell F1 and masked DFL D recall, all versus frozen control. Use exact comparisons without acceptance tolerances. Report each match even if aggregate gates pass; a per-match loss in natural spell F1, cadence spell F1 or DFL D recall blocks automatic advancement and requires a documented scientific decision. Numerical replay tolerances, where necessary, are separate arithmetic checks.

If this gate fails, preserve the negative result and run the approved whole-segment diagnosis; do not retune this pilot. If it passes, the candidate earns one separately frozen regression/robustness comparison, **not** deployment, new target inference or a claim of independent accuracy. A failed reference-data qualification does not stop useful seen-data diagnosis, but keeps its claims exploratory.

## Workstream B: independent full-state evidence

This work is technically independent of A, but is scheduled as a separate goal after A finishes to respect the latest sequential-goal instruction. Source qualification completing is distinct from acquisition or scientific validation completing.

Begin with the existing source scouts, not another unbounded GitHub search. Rank at most three existing leads by lawful access, genuinely dense H/A/D coverage, provider/annotation independence, temporal/team non-overlap, and practical resource needs. Produce a source qualification record and pick one lead, or document why all fail.

Do not inspect candidate predictions while choosing a source or splits. Verify rights/ontology on documentation first; acquire only permitted external data after the concrete source and costs/access are resolved. A paid service, account credential or unavailable right is a real dependency and remains explicit. Do not ask for protected challenge assets as a fallback.

Before evaluation, freeze an access/use ledger, team/time split, candidate and comparator selection rules, all-state metrics and decision rules. If new external annotation is needed, use a written manual, blinded labeling and independent adjudication, with ambiguity X instead of fabricated D. Separate development/calibration access from unopened qualification; once opened, a failed set cannot become fresh again by renaming it. Minimum sample/support and power must be justified from accessible cohort structure and match-level variation before outcomes are opened, not assigned an arbitrary large-match target here.

Deliverable is either a qualified acquisition/annotation and evaluation protocol or a clearly documented unresolved external dependency. An asset list without rights or dense state truth is not successful qualification.

## Workstream C: whole-segment ownership diagnosis

Preserve the approved design and plan hashes. Execute `2026-11-08-ownership-path-diagnosis.md` after A's report, on its original four natural cases and frozen control only. The instrument separates emission preference, switch cost, future context, ties and carry; it does not certify physical control. Do not expand its scope or silently instrument the new candidate under the old approval.

Use its evidence to choose **at most one** next intervention:

- Observation/feature support is misleading: design an explicit availability-aware head and fit only on declared training data.
- Reference-favoring support loses to path persistence: compare one justified temporal alternative with short-spell and D safeguards.
- Exchange asymmetry is material: compare one symmetric feature/emission intervention, with D unchanged.
- Reference semantics/ties/hidden observations prevent attribution: state the information gap and prioritize independent evidence rather than inventing confidence.

These are decision branches, not four automatic model projects.

## Workstream D: current-winner robustness and bounded regression

Only after a candidate is frozen and A's gate is resolved: compare frozen control, candidate and baseline chosen on development. Reuse the 13 already-seen validation/regression matches under their true status; do not treat the old validation/regression distinction as new independence. No new grid.

Reuse the existing opponent-loss, identity-discontinuity, false-ball and ball-time-shift drivers. Add stale-finite, joint player dropout and fragmented cadence; pair identical corruptions across methods. Additional masks use fixed seeds 1729,2718,3141. First freeze resource limits from one unscored dry run; then freeze the exact case matrix, not a vague promise of exhaustive testing. Report natural, each corruption, each provider and worst-match outcomes, alongside short-spell/boundary/uncertainty strata. Repeat targeted failing checks after fixes; run the full suite once at the completed change, not after every documentation edit.

Fresh full-state qualification is a separate locked evaluation when B provides it. Another pass on old matches is neither an independent gate nor proof of zero errors.

## Workstream E: reproducibility and delivery

Cheap immediate documentation work: route/commit matrix; correct audit manifest paths and final-byte hashes; mark missing original probe/log unavailable rather than fabricating them; link the independently delivered verification scripts as new evidence. Archive the old installer to its intended generation or make pre-copy artifact/interpreter checks explicit. Keep repair commits separate from scientific changes.

Next reproduction project: stable raw/adapter/model/policy/scorer identities and canonical semantic array hashes, plus generation-specific byte seals. New reconstructed generations get new linked receipts; old seals and score archives stay immutable. Verify a raw-to-report rebuild in a fresh workspace, distinct from replaying original caches.

Next delivery project, after an explicit selected-method decision: a versioned selected-only export with optional all-controls research mode; synthetic/external selected-label parity; declared inputs and experimental status; actual time/memory measurements. Do not weaken old guards to make a smaller export appear to work. Do not rebuild the old bundle and imply it now exports the newest top-level route.

GitHub publication, when execution is authorized, uses the verified **The-leonjr** identity. Publish code, reasoning, failed experiments, bounded metrics and limitations; no raw/reference/per-frame archives, secrets or protected assets. Verify final Git-visible hashes. Keep PR integration separate from scientific acceptance; do not auto-merge PR #1.

## Order, dependencies and stopping points

1. Finish the builder/coverage check of this design and first-experiment plan; mark the planning goal complete before creating the execution goal.
2. A: fixture/sidecar → candidate and baseline unit checks → protocol freeze → 20-case pilot → decision report. Mark A complete before creating B's source-qualification goal.
3. B: complete a concrete source qualification/access proposal, without claiming unresolved acquisition or truth has been achieved. Then C's existing whole-segment plan, unchanged, explains frozen-control residuals. Cheap E documentation repairs can accompany C without touching predictor files.
4. Select at most one next candidate intervention or a justified stop; freeze D. B governs any fresh generalization claim.
5. Complete E rebuild/export for the explicitly selected experimental method; publish evidence and limitations using the requested GitHub account.
6. Revisit cameras only after an external timing/live-correspondence and additional-information milestone. Defer broad architecture searches until current causes and evidence access warrant them.

No promised wall-clock estimate before profiling. Budget work by cases and milestones: one builder check of this plan, one pilot candidate, 20 cases, 10 variants, one final implementation review. Implement and synthetically verify **all** feature, comparator, driver, diagnostic and gate code before freezing the complete source/input/schema/protocol. The sole external scoring run follows that freeze; no later task may rewrite sealed receipts to add metrics. Stop on replay/hash/reference-isolation failures; do not hide them by regenerating seals.

## Concrete planning deliverables

- This design/roadmap.
- `../plans/2026-11-08-cadence-and-baselines.md`: executable first-project plan.
- `../plans/2026-11-08-fresh-reference-qualification.md`: bounded independent evidence work package.
- Existing whole-path plan remains immutable; this document explains its new position.
- A builder check and a self-review/coverage record. Implementation checkboxes remain unchecked.

## Execution correction: report revision 2

The first external attempt stopped during construction of the first frozen-control report, before any complete case receipt or comparison was saved. The official evaluator keeps a diagnostic truth-X row in its 4x4 raw confusion matrix while scoring only the first three rows. The new formatter incorrectly required the diagnostic row to be zero. A synthetic unknown-reference-island regression reproduces the mistake; revision 2 uses the unchanged official `scored_confusion` helper.

The failed freeze, all 100 source files and its attempt/log are preserved under this plan's local execution ledger. New output is `reports/cadence-v2`; the old `reports/cadence` stage is not overwritten. No predictor, feature rule, candidate, mask, match, metric definition or acceptance criterion is reselected. Revision 2 keeps the exact 20 cases/200 completed variant comparisons. Transparently account for **one additional aborted variant-scoring invocation**, giving 201 total external invocations across the failed formatter preflight and completed experiment. This is an implementation-correctness ruling within the authorized work, not an extra model search.
