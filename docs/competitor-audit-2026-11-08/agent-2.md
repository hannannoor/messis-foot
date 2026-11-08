# Council reviewer 2 — competitor audit

## 1. Scope, evidence and verdict

I audited the latest PR progress at commit `cee674190775e9356745f461ba1561e9f2a46f7e`, using the supplied source copy whose 309 tracked blobs were verified against GitHub. This is the PR branch, not the older default branch. I inspected the selected runtime, tactical features/model, decoder, input adapters, evaluation protocol, published receipts and project rules. I did not read other council reports or earlier strategy/code-review audits. I changed no project source, used no challenge assets, and performed no acquisition or training. My independent execution was a small standard-library decoder probe; the coordinating reviewer handles the full suite. I cannot independently reproduce the provider scores without the excluded external caches and scoring archives.

My competitive attack would be: **you have built a careful experimental apparatus around a model whose transfer to the actual problem remains largely unproven.** Your best recent change removes false evidence from missing observations; it does not add information about the football occurring inside those gaps. A rival with a genuinely independent full-state benchmark and a stronger observation model could challenge the central proposition without disputing your substantial implementation work.

The repository is unusually candid about these limitations. I am not alleging fabricated results, challenge-GT leakage, or forbidden target fitting. The selected route explicitly excludes video checks, smart tags and the disputed fixed-D interval. Honest caveats reduce the risk of misleading readers; they do not remove the competitive weaknesses.

## 2. High severity, high confidence: the project has exhausted its independent evaluation evidence

The current method is selected and accepted using previously examined matches. The original split separated model fitting from validation/test, but later project decisions have repeatedly consumed those datasets. The current protocol correctly renames the old tests “seen regressions.” That does not make them independent again. See [method, lines 7–18][method] and [current results, lines 30–40][results-tradeoffs].

The latest natural equal-provider spell-F1 change is only **0.564642 → 0.566428**, versus a much larger improvement on the simulated mask stress. Two DFL matches provide the full-state regression evidence. There are no reported paired uncertainty intervals establishing that the small natural gain survives match/possession variation. The official scorer itself warns that frames are correlated and recommends segment/block uncertainty estimates; its illustrative noise bands are not a substitute for an actual paired interval here. See [results, line 22][results] and [scorer discussion, lines 15–21][metric].

A competitor can reasonably say: “You know your development corpus better than you know your generalization.” Freezing the next experiment after the previous findings prevents direct reselection within that experiment, but cannot undo cumulative research overfitting.

**Better alternative and acceptance:** prioritize a rights-cleared, genuinely unopened full H/A/D cohort before another decoder grid. Keep acquisition/licence verification separate from outcome inspection, preregister the comparison and evaluate once. On existing data, add paired match/block-bootstrap intervals and worst-match results as exploratory diagnostics. Accept a stronger claim only when the independent primary score improves with an appropriately uncertain estimate and no material provider/class collapse. If fresh data remains unavailable, retain “exploratory” status rather than treating seven passed gates as seven independent confirmations.

## 3. High severity, high confidence: stoppage competence remains entangled with a provider convention

The frozen tactical tree's first split is `recent_speed`, at approximately **0.0104 m/s**, and several subsequent branches use slow-ball age/history. The artifact records that inactive DFL ball coordinates repeat the previous frame on **99.9993%** of contiguous inactive frames. It also acknowledges that the original pooled newly resolved agreement was dominated by D and that active-only spell-F1 regressed on both original held-out matches. See [tree root and thresholds][tree] and [artifact limitations, lines 229–238][artifact-limits].

That is a serious shortcut vulnerability. It does not mean BallStatus is literally passed into inference; I found the adapter keeping reference fields separate. It means the feature distribution can indirectly encode the provider's annotation convention. The newer missing-ball-neutral correction only neutralizes absent coordinates. **Finite frozen coordinates remain observed coordinates**, so stale numerical values can still create highly persuasive D emissions.

SkillCorner does not close this hole: its reference contains known-play H/A, not independently labelled stoppages. A fall in false D on known-live SkillCorner is useful, but cannot establish sensitivity to genuine D there. This limitation is expressly recorded in [the reference contract][method] and [current results, lines 24–40][results-tradeoffs].

**Better alternative and acceptance:** compare the current head with externally trained alternatives that cannot rely so heavily on ball stationarity alone, including player-motion context and separate live/dead inference. Perform provider-artifact interventions on external data: perturb frozen inactive coordinates, introduce stationary live-ball episodes, and corrupt stale active coordinates without changing reference labels. Retain natural full-state evaluations alongside these synthetic interventions. Require the live/dead advantage to persist on another provider with verified reference semantics. Do not invent a target freshness threshold or declare every repeated position stale.

## 4. High severity as a capability gap, high confidence: “ball-gap recovery” currently means neutralization plus continuity

The selected policy sets all three emissions to zero whenever the ball is unavailable and uses motion weight zero. In those spans, player geometry supplies an eligibility gate, not ownership evidence: three available points on each side can keep the segment usable, but their arrangement does not distinguish H, A or D in the selected emissions. The runtime reports `selected_motion_head_used=False`. See [selected policy, lines 14–24][policy], [usability gate, lines 6–9][decoder] and [runtime, lines 38–49][runtime].

There is no duration-dependent uncertainty or hazard of an unseen switch in that decoder. A long neutral gap between same-team anchors is cheapest to fill with that team even if multiple possessions and stoppages occurred inside. The output can be stable and wrong. An entirely unobserved usable segment is first X and subsequently materialized by the general carry convention; that convention can copy across arbitrarily long within-period gaps and uses D when a whole period is unknown. See [carry implementation, lines 10–18][carry].

The local receipt counts **60,321 neutral active usable rows**, plus **8,059 latent-X rows materialized**. These counts are execution diagnostics, not labelled errors, but they show that the information deficit is central rather than an edge case. The current report correctly says so. See [results, line 82][results-execution].

**Better alternative and acceptance:** distinguish (a) removal of a harmful missingness shortcut, (b) ordinary continuity imputation and (c) actual evidence-driven recovery. Develop a player-motion or other allowed observation model externally, and compare it against the same decoder with no added observation evidence. Measure completely hidden opponent spells and hidden stoppages by gap duration, including same-owner endpoints. Accept a recovery claim only if it detects events that continuity cannot, at matched input coverage. Preserving the rejected motion model's rejection was correct; its failure is a reason to improve features/data, not a reason to pretend neutralization solves the missing-information problem.

## 5. Medium severity, demonstrated behavior: neutral ties systematically prefer home ownership

The decoder chooses state index 0/H on exact ties in both predecessor and final-state selection. The documentation acknowledges deterministic tie behavior; I independently established its concrete consequence. See [decoder, lines 35–44][decoder] and [results, line 38][results-tradeoffs].

With 100 strongly H-supporting frames, 100 missing-ball frames, and 100 strongly A-supporting frames, the whole missing span becomes H and the transition occurs at frame 200. Swap the H/A evidence: the whole span still becomes H, and the transition moves to frame 100. Reproduction from the source checkout:

```python
from ball_gap_policy import decode_ball_gap
for left, right in (([.98,.01,.01], [.01,.98,.01]),
                    ([.01,.98,.01], [.98,.01,.01])):
    p = [left]*100 + [[.33,.33,.34]]*100 + [right]*100
    y, _ = decode_ball_gap(p, [1]*300, [True]*300,
                           [True]*100 + [False]*100 + [True]*100)
    print(y[100:200].count('H'),
          [i for i in range(1,300) if y[i] != y[i-1]])
# 100 [200]
# 100 [100]
```

This is not evidence about where a real hidden transition happened. It is evidence that the arbitrary point estimate assigns ambiguity systematically to one team. A competitor can attack end-to-end team symmetry and possession-share reliability even before addressing the already asymmetric tactical head.

**Better alternative and acceptance:** adopt an externally fixed, team-neutral temporal convention for tied boundary placements, or retain the set/range of equally optimal transitions in diagnostics. A convention cannot recover unknowable timing, but need not prefer home. Add swapped-team metamorphic tests covering tied neutral spans, H/D and A/D ties, period edges and all-neutral segments. Require the convention's outputs to swap consistently, and assess its official-score tradeoff externally before promotion.

## 6. Medium severity, high confidence: smoothing is buying spell quality partly by deleting genuine events

The primary metric rewards interval quality, so reducing false cuts is legitimate. Nevertheless, **more missed changes is a real loss of capability**, not a cosmetic secondary metric. The latest correction reduces masked SkillCorner spurious boundaries from 1,812 to 1,043 while missed changes increase **921 → 953**. Masked DFL missed changes increase **632 → 645**. Even natural SkillCorner misses rise **752 → 758**. See [results, line 34][results-tradeoffs].

The mechanism is explicit: every switch costs 32. A short island requires two switches, so its cumulative emission advantage must exceed 64. With hypothetical support 0.6 versus 0.4 and negligible D, that is approximately 158 frames, over six seconds at 25 Hz. This calculation illustrates the decoder's behavior, not a measured real-match failure frequency. The emissions are log leaf supports, although the artifact expressly says these are not calibrated correctness probabilities. See [emission/transition implementation][decoder] and [model metadata, line 188][model-metadata].

A rival with accurate brief turnovers could beat you on short spells while you report improved average spell-F1. Also, matched-boundary latency excludes missed boundaries, so its improvement cannot rescue an erased event.

**Better alternative and acceptance:** report recall stratified by reference spell duration and hidden/observed transition status; preregister short-spell and missed-boundary safeguards. Compare a duration-aware decoder or externally calibrated evidence against the fixed-switch baseline. Preserve primary official-score gains, but require that they do not depend on unacceptable loss of a predeclared short-spell category. Do not select that threshold from the challenge match.

## 7. Medium severity, high confidence: the stress benchmark is narrower than the target failure modes

The masking protocol chooses random active starts and lengths from **5, 15, 50, 125 and 250 frames**, to mask 30% of the active timeline with seed 1729. That is controlled and label-independent, which is good experimental practice. It primarily tests missing-ball intervals up to ten seconds before overlaps; it does not establish robustness to semantically correlated missingness, simultaneous opponent loss, camera-specific detection bias, finite stale positions or long outages. See [mask generator, lines 37–49][mask] and [method, line 7][method].

SkillCorner's 10→25 Hz adapter interpolates player positions by real provider identity before anonymous correspondence is estimated. Therefore “anonymous” evaluation retains an upstream advantage absent from raw anonymous detections. The source explicitly implements this interpolation. See [adapter, lines 155–193][adapter].

**Better alternative and acceptance:** freeze a small external corruption matrix spanning several seeds, missingness durations, team-visibility asymmetries, identity churn, stale coordinates and native-detection-only variants. Keep these separate from natural evaluation. Require improvement against the same simple carry/neutral baseline across the intended failure categories, publishing failures rather than averaging them away. No target-video inspection or hand labelling is necessary or permitted for this work.

## 8. Medium severity, high confidence: the research release and the practical delivery are diverging

The README's “Run one file” command invokes the older frozen tactical route. The latest ball-gap result requires a separate checkout-based command. Its entry point verifies historical source/evidence artifacts, and its runtime always loads the temporal artifact and computes four comparator routes, even though the selected prediction has motion weight zero. See [README, lines 23–30][readme-run], [latest command, line 74][readme-latest], [entry point, lines 12–17][entry] and [runtime, lines 38–43][runtime].

These choices preserve valuable comparisons, but they also make unrelated research artifacts part of the delivery dependency graph. A user following the prominent single-file promise receives a different method from the headline result. I have not measured excessive latency or memory, so I am not claiming a performance failure. The demonstrated issue is release ambiguity and avoidable coupling. Exact evaluation replay additionally requires excluded private/local archives, as the documentation openly explains.

**Better alternative and acceptance:** publish one explicitly designated candidate package with model, runtime and required attribution; make comparator generation and research-evidence verification separate commands. Preserve the old package by version. On a clean directory, verify that the designated command produces the expected selected synthetic CSV, validates original indexing, needs no training/cache artifacts, and reports its version/hash and limitations unambiguously. Record end-to-end runtime and peak memory before making operational claims.

## 9. Prioritized improvement sequence

1. **Immediately:** maintain the current freeze and experimental status; fix release naming/docs and add the exact neutral-tie regression. Preserve every existing receipt and candidate output. Do not silently reselect on the now familiar corpus.
2. **Next evidence milestone:** obtain and seal an independent licensed full-state cohort. In parallel, add paired uncertainty estimates and duration/gap-stratified diagnostics on the existing references, explicitly exploratory.
3. **Next model milestone:** compare a provider-resistant live/dead head and genuine missing-ball observation evidence against the current neutral/carry baseline. Include the external corruption matrix and team-swap checks. Spend effort here before another broad camera/OCR investment or decoder parameter grid.
4. **Next release milestone:** evaluate the frozen proposal once on the unopened cohort; either reject it or publish one clean selected runtime with reproducible inputs/outputs and measured operational requirements.

The most defensible competitive advantage today is disciplined provenance and reproducible software. The weakest point is still evidence that the selected method understands possessions and stoppages beyond the providers and conventions that shaped it. Strengthen that before treating more assignments, more receipts or more tests as progress on accuracy.

[method]: https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/docs/accuracy-first-method.md#L7-L18
[results]: https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/docs/ball-gap-results.md#L14-L28
[results-tradeoffs]: https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/docs/ball-gap-results.md#L30-L40
[results-execution]: https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/docs/ball-gap-results.md#L78-L84
[metric]: https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/gap_solver/official_metrics.py#L15-L21
[tree]: https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/gap_solver/tactical_model.py#L84-L119
[artifact-limits]: https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/gap_solver/tactical_model.py#L229-L238
[model-metadata]: https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/gap_solver/tactical_model.py#L180-L188
[policy]: https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/ball_gap_policy.py#L14-L24
[decoder]: https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/gap_solver/soft_sequence.py#L6-L44
[runtime]: https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/ball_gap_runtime.py#L38-L49
[carry]: https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/gap_solver/materialization_control.py#L10-L18
[mask]: https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/gap_solver/temporal_selection.py#L37-L49
[adapter]: https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/gap_solver/skillcorner.py#L155-L193
[readme-run]: https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/README.md#L23-L30
[readme-latest]: https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/README.md#L74
[entry]: https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/ball_gap_candidate.py#L12-L17

