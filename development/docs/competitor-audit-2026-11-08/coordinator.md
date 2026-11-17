# Reviewer 6 — coordinator's independent competitor audit

**Reviewed:** `hannannoor/messis-foot`, open PR #1, commit `cee674190775e9356745f461ba1561e9f2a46f7e`, on 8 November 2026 (Singapore). The local source's 309 tracked files matched their GitHub blob hashes. Default `main` is the older `3a1c8608e050e2f812826719e1af882d87cf2f67`.

I approached this as a competitor looking for the strongest defensible case against your approach. My verdict is that you have built a carefully preserved experimental pipeline, but your evidence of transferable possession inference is substantially weaker than your evidence of reproducible execution. A rival would attack the gap between those two things. Nothing I inspected establishes that an actual competitor scores higher on the hidden challenge match.

I inspected inference, ingestion, decoding, evaluation, committed aggregate receipts, release construction and current experiment documentation. I checked the current official competition revision through GitHub; it is still `f8f2629ff1e0985f81d7e59d8413678514ee1530`. I did not inspect challenge video, GT, tracking, predictions or frame-level derivatives. I did not retrain, acquire assets or change project code. My review was conducted alongside the agents; their progress messages were visible to me, while their full reports were kept unread until this report was written. This is a separate assessment, not a claim of perfect reviewer blinding.

**Severity:** P1 means a core competitiveness or validity weakness to address next; P2 means a material limitation. These are audit priorities, not a claim that every item is a software bug.

## 1. P1 — You have exhausted the independence of the evidence you keep using

**Confidence: high. Evidence-backed research limitation.**

The latest experiment uses three already examined validation matches and ten already examined regression matches. It follows earlier tactical, motion, confidence, ensemble, input-contract and decoder investigations on overlapping material. Freezing each experiment before its next scoring stage is good discipline. It does not make the overall research program independent of information acquired in the previous stages.

Your [latest results, lines 28–40](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/docs/ball-gap-results.md#L28) disclose this correctly. The problem is unresolved even though it is disclosed.

As a competitor, I would say: “You can demonstrate that the current policy addresses failures you have already seen. You cannot yet demonstrate that you selected the policy that generalizes.”

There is useful evidence here, and I checked rather than dismissing it. From the ten natural regression receipts, I independently computed a paired, provider-stratified match bootstrap, retaining equal provider weighting. The missing-ball correction's mean spellF1 delta is **+0.00178627**, with a conditional 95% percentile interval of approximately **[+0.00048952, +0.00328566]** over 20,000 draws, seed 1729. That supports a small positive change within this already selected, seen cohort. It does not correct adaptive reuse, provider selection or mismatch to the target. It would be wrong to declare the gain “just noise” solely because it is below the official challenge's illustrative noise band.

**Better alternative:** prioritize an independently controlled external evaluation before another parameter cycle. If a suitable public full-state cohort is unavailable, external-game annotations with clear rights and accessible provenance are an alternative permitted by the public rules; do not create challenge labels. Define the annotation ontology and evaluate it before seeing candidate scores.

**Acceptance criterion:** freeze the candidate and hypotheses before opening new references; report every match and class, including failures, with paired match-level uncertainty. Until then, retain the experimental designation.

## 2. P1 — The two-provider benchmark does not close the most important state-recognition gap

**Confidence: high. Evidence-backed transfer limitation.**

DFL supplies H/A/D reference, but inactive ball coordinates are usually frozen. SkillCorner offers independent tracking behavior but only known-play H/A reference. Those are complementary sources, not an independent full-state confirmation. High D recall on DFL and low false D on SkillCorner cannot jointly prove robust stoppage recognition.

The latest correction changes missing observations to neutral emissions. It does not neutralize finite stale coordinates. The feature extractor still derives speed and recent speed from finite coordinates ([tactical.py, lines 39–61](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/gap_solver/tactical.py#L39)); “available” is not “fresh.”

I verified a related narrow property: keeping 180 frames' coordinates fixed while changing native-detection/provenance/interpolation flags leaves every tactical support vector identical. That is not automatically a bug, especially because the target feed lacks those flags. It shows that the chosen head cannot distinguish those observation regimes when such metadata exists.

**Competitor's attack:** your best dead-ball reference contains an observation-production shortcut, while your independent provider cannot expose missed stoppages.

**Better alternative:** separate live/dead evidence from H/A ownership. Test a small externally trained state head against stationary in-play ball, genuine stoppages, stale/extrapolated coordinates, restarts and sparse tracking. Use automatic player-set motion or other justified inputs rather than treating repetition alone as proof of dead ball. A genuine stationary ball must remain possible during live play.

**Acceptance criterion:** unseen full-state references must support D precision and recall, short stoppage recovery and H/A spell quality under both native and degraded observation regimes.

## 3. P1 — Your selected missing-ball route discards the very evidence that could resolve a hidden change

**Confidence: high about mechanism; target impact unmeasured.**

[ball_gap_policy.py, lines 14–24](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/ball_gap_policy.py#L14) replaces the entire H/A/D emission vector with zeros on missing-ball frames. The selected motion weight is zero. Player availability can make a frame usable, but player arrangement or motion cannot supply selected H/A/D evidence inside that gap.

This is a sensible correction to the earlier false-D mechanism. It is not hidden-possession recovery. The decoder chooses a path from outside evidence and switching cost; it cannot see an entirely hidden turnover, stoppage or brief opposing possession.

In my 1,000-frame neutral-gap probe, strong H observations before and A observations after the gap produce **1,000 H gap labels and zero latent X**. After swapping H/A emissions, the gap is still all H because of deterministic ties. The gap is 40 seconds at 25 Hz. Its label count says nothing about how much of that interval was identifiable.

The exported flags help: `neutralized` distinguishes these rows from ordinary observations. But `latent_unknown_active` alone is not a meaningful total of epistemic uncertainty ([runtime, lines 43–62](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/ball_gap_runtime.py#L43)).

**Better alternative:** preserve an explicit distinction between an observed state, a transition-prior assignment, an unresolved transition window and final format materialization. Evaluate a modest permutation-invariant player-set model for missing-ball intervals before reviving identity-heavy motion machinery or the full broadcast pipeline.

**Acceptance criterion:** score externally labelled hidden changes separately from same-owner gaps. Report gap-length strata and feasible boundary windows; never count a deterministic optimal path as independently recovered ownership.

## 4. P1 — The global switching cost suppresses exactly the short events the ranking metric counts

**Confidence: high. Demonstrated decoder behavior.**

The official ranking metric matches H/A possession spells. Optimizing it is the correct objective. However, your selected fixed switching cost creates a concrete duration/evidence tradeoff.

Each switch costs 32. An A interval between H anchors costs 64 to enter and leave. With per-frame support A=.90 and H=.05, an interval needs more than `64 / log(18) = 22.14` frames to overcome those two switches. My direct selected-policy probe confirms that **10-, 20- and 22-frame A bursts disappear; 23 frames survives**. This is a synthetic input-level result, not a claim about the model's real calibration.

That behavior is implemented in [soft_sequence.py, lines 24–44](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/gap_solver/soft_sequence.py#L24). The committed real-provider diagnostics show the same type of tradeoff: fewer spurious cuts but more missed transitions ([accuracy-first results, line 59](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/docs/accuracy-first-results.md#L59); [ball-gap results, line 34](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/docs/ball-gap-results.md#L34)).

**Competitor's attack:** you improved average spell overlap partly by removing cuts, but some removed cuts are real possessions.

**Better alternative:** compare the constant-cost decoder with an externally selected state/duration model or a boundary-evidence model. Keep the simple decoder as a serious baseline. Do not assert that a more complex decoder must win.

**Acceptance criterion:** predeclare short-spell recall and a maximum permissible loss alongside mean spellF1, and examine both false cuts and erased genuine changes.

## 5. P2 — The full selected pipeline has an avoidable team-label bias

**Confidence: high about behavior; prevalence and score impact unknown.**

A geometry-only team estimator should have a clear policy for exchanging team identities. Your decoder can exchange unique-optimum emission columns correctly, but the retained head is asymmetric; the documentation acknowledges this.

I checked the actual frozen head on 180 moving-ball frames with nearest-team distances 0.5m and 1m, then exchanged the teams. Both versions emit **H for every frame**, with the same final support vector, approximately **(.687875, .310736, .001389)**. This is a counterexample to end-to-end H/A equivariance. It does not establish which team truly possessed those synthetic frames.

There are two distinct problems: asymmetry learned by the head, and H-preferring choices among equal-cost paths in a neutral interval. Fixing only decoder tie-breaking would not repair the former. See [documented limitation](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/docs/accuracy-first-results.md#L38).

**Better alternative:** evaluate team-swap augmentation, a symmetric feature/head construction, or symmetrized emissions. Preserve D under the transformation. An explicit prior favoring a named team would need evidence and justification; none should arrive accidentally from a small external cohort.

**Acceptance criterion:** metamorphic team-swap tests across complete runtime inputs, plus held-out H/A-specific error and possession-share results. Treat legitimate ambiguous ties separately from unique-optimum failures.

## 6. P2 — Your missingness stress is too narrow to justify broad robustness language

**Confidence: high about test scope; wider failures remain hypotheses.**

The masking protocol removes 30% of ball input with one seed and chosen block lengths of 5, 15, 50, 125 or 250 frames ([temporal_selection.py, lines 37–49](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/gap_solver/temporal_selection.py#L37)). This is a useful controlled intervention. It is not a model of every real failure process.

It does not independently test correlated ball/player loss, stale-but-finite coordinates, partial team disappearance, homography failure or ambiguous crossing correspondences. Randomly deleting input independently of labels is good leakage prevention, but real missingness can depend strongly on match state.

SkillCorner's 10-to-25-Hz processing also interpolates player positions using identities before anonymous association is evaluated ([skillcorner.py, lines 155–193](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/gap_solver/skillcorner.py#L155)). Zero prediction change under the anonymous adapter is therefore a limited compatibility result, not proof of raw anonymous-feed transfer.

**Better alternative:** use a fixed external corruption matrix covering several independent masks, long gaps, correlated channel loss, quantization, stale-coordinate bursts and identity ambiguity. Include natural failures, not only manufactured ones.

**Acceptance criterion:** report worst-group performance and support counts, without selecting a winning seed or using challenge outcomes to set corruption parameters.

## 7. P2 — The comparator family is too close to your own model to establish competitiveness

**Confidence: high about inspected comparisons; no claim that another baseline would win.**

The current four controls are incumbent, carry, agreement and agreement-plus-carry. They are informative ablations of your pipeline. The selected sequence models also reuse your frozen tactical head.

I did not find a scored, current external comparator equivalent to the official nearest-player plus majority-window baseline family. The original external baseline script calls your conservative `infer` method ([run_external_baseline.py, lines 18–25](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/run_external_baseline.py#L18)). Beating that baseline does not establish that the learned head is needed.

The official [evaluation document](https://github.com/metrica-sports/more-than-a-hack-2027/blob/f8f2629ff1e0985f81d7e59d8413678514ee1530/EVALUATION.md) itself demonstrates that smoothing alone can materially change spell quality. Its challenge scores cannot be compared numerically with your external scores.

**Better alternative:** include externally selected nearest-team-plus-hysteresis/majority baselines and a simple live/dead rule as explicit competitors. Equalize input quality, timing, missingness handling and scoring. Keep their parameter selection on external development data.

**Acceptance criterion:** the proposed model should show an advantage over the strongest fair simple comparator, not merely over a more conservative generation of itself.

## 8. P2 — You have invested heavily in evidence preservation without finishing evidence portability

**Confidence: high. Reproducibility limitation, not an integrity accusation.**

The source freezes, exclusive publication, per-case seals and preserved failed experiments are valuable. They prove which artifact produced the retained evidence. Exact replay still depends on the original local score archives and caches at recorded sibling locations, as the [reproduction instructions](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/docs/ball-gap-results.md#L44) explain.

A competitor can reasonably ask whether an evaluator with a clean checkout and legally obtainable public external data can reproduce the comparison without your workspace. That is a different requirement from rerunning inference on the challenge inputs. I am not alleging that inference requires private reference arrays.

There is also unnecessary operational coupling: the selected weight-zero route still loads the temporal model and computes four comparator CSVs ([runtime, lines 38–43](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/ball_gap_runtime.py#L38)). This keeps comparisons aligned, but gives the final predictor more dependencies and work than its selected decision rule needs.

**Better alternative:** provide a clean acquisition-to-report recipe with portable logical paths and immutable public inputs; keep protected challenge assets out. Separate optional comparison generation from the selected inference path, while retaining a reproducible all-comparators mode.

**Acceptance criterion:** reproduce the external report in a new workspace; run selected inference without the unused motion/comparison machinery; show exact prediction parity and measured time/memory changes.

## 9. P2 — The release surface makes it too easy to run the wrong generation

**Confidence: high. Delivery and maintainability issue.**

Your latest progress is in an open PR while default `main` remains older. The headline “Run one file” command uses the earlier tactical route, while the newer selected experiments have separate checkout entry points. The standalone reports version `2026.11.06-temporal-research`; [build_standalone.py, lines 65–78](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/build_standalone.py#L65) does not expose the new top-level candidate route.

Those boundaries are documented, so this is not false advertising. But an evaluator should not have to infer which preserved generation is the intended deliverable.

Legacy camera/manual options and the disputed fixed-D path also remain reachable. I found no basis to claim that the latest explicit candidate uses that shortcut: its report says otherwise and its runtime follows the separate route. The risk is operational ambiguity, not demonstrated rule-breaking.

**Better alternative:** select and name one eligible release entry point, expose its exact policy/version and artifact identity, and make historical experiments explicit opt-ins. Keep historical source for auditability without putting every route on the main usage path.

**Acceptance criterion:** a fresh user follows one short command sequence and obtains the intended artifact, with the intended policy, without discovering an unpublished local dependency or choosing among competing “current” commands.

## What I would do next if I were trying to beat you

1. Freeze the current experimental result and stop treating another seen-cohort improvement as the main research milestone.
2. Obtain independent external full-state evidence, or document a rights-cleared external annotation protocol and keep evaluation blinded.
3. Put a strong simple comparator and a small symmetric state/ownership model against your current head. Test native missingness, stale observations and short changes.
4. Improve missing-ball identification and boundary uncertainty before reopening broad camera fusion. Your automatic camera work produced no bounded links; adding more fusion scaffolding currently offers no measured possession benefit.
5. Promote exactly one validated route and run it from a clean checkout. Preserve comparator generation as an optional audit operation.

I would retain the original-index contract, strict input/reference separation, explicit materialization flags, reproducible artifacts and documented rejections. Removing those safeguards would not create a better competitor. The opportunity is to shift the next unit of effort toward new information about correctness.

## Verification and limits

Fresh verification ran **341 tests in 19.760 seconds: OK, 19 skipped**. That means 322 tests executed successfully; it does not mean all 341 exercised their assertions. Skips cover unavailable OCR/FFmpeg/Pillow integration, two training-only sklearn checks, two private local-delivery fixtures, one opt-in full-index fixture and one Windows symlink-privilege case. The hardlink and junction tests passed after running outside the restrictive sandbox. Earlier TEMP/link failures are environment artifacts, not findings against the repository.

The independently reproducible probes and the exploratory bootstrap are in `root-probes.py` and `root-probes.json`, beside this report. They use committed source and aggregate external receipts only. I did not re-score raw external labels or measure hidden challenge accuracy. No project source was modified.


