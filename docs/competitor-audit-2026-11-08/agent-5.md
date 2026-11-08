# Independent competitor audit — reviewer 5

## 1. Scope and adversarial position

I audited the latest supplied PR state, commit `cee674190775e9356745f461ba1561e9f2a46f7e`, rather than the older default branch. I inspected the verified source tree, inference adapters, frozen tactical model, sequence decoder, input contract, external scoring implementation, experimental protocols and published aggregate results. I did not consult the other council reports, earlier neutral/strategy audits or prior code-review reports. I did not inspect challenge video, ground truth, unpublished local work or reconstruction-capable challenge outputs. No source was modified, acquisition performed or model trained. The parent reviewer is running the main suite; my additional execution comprised small, read-only synthetic probes under `python -B`.

My competitor's argument would be: **you have established disciplined execution and some useful external improvements, but have not established a reliable solution to the target's hardest inference problem.** The latest correction removes a harmful source of invented evidence. It does not add observations of hidden possessions, solve stale observations, or demonstrate transferable stoppage detection. That distinction should determine where the next week goes.

Severity below measures competitive importance, not security exposure. “Demonstrated” refers to code or reproduced synthetic behavior; it does not imply an observed target error. Every linked file is pinned to the audited commit.

## 2. Priority 1: the evaluation has exhausted its independence before the strongest claims are established

**Severity: high. Confidence: high. Classification: demonstrated evidence limitation.**

The current selection protocol chooses among 16 settings using three already examined validation matches: one DFL match and two SkillCorner matches. Providers receive equal weight, so the single DFL match supplies half of the selection objective. See [accuracy_protocol.py:7–10 and 43–62](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/gap_solver/accuracy_protocol.py#L7). The later missing-ball correction is tested against the same established validation/regression cohorts. The project explicitly acknowledges that all reference matches have appeared in earlier analyses: [accuracy-first method:16](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/docs/accuracy-first-method.md#L16), [ball-gap results:40](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/docs/ball-gap-results.md#L40).

Freezing each experiment before running it is good practice. It prevents within-experiment opportunism; it cannot make previously observed matches independent of later architectural decisions. The absence of new head fitting does not remove adaptive overfitting through feature interpretation, decoder choice, policy formulation and acceptance-gate design.

The final neutralization adds only **0.001786** natural equal-provider spell F1 over w0-c32, versus a much larger masked improvement: [ball-gap results:22](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/docs/ball-gap-results.md#L22). That is useful exploratory evidence, but insufficient to distinguish a broad natural-input gain from cohort-specific fluctuation. The general benchmark explicitly disables the official bootstrap, [benchmark.py:33–37](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/gap_solver/benchmark.py#L33); more fundamentally, two full-state regression matches cannot describe much between-match variation.

**Competitor leverage:** I could present a smaller system with an untouched, rights-cleared full H/A/D holdout and make a stronger reliability claim despite a lower development score. Your receipts would not refute that advantage.

**Better alternative and acceptance:** stop using the existing cohorts to authorize increasingly general correctness claims. Acquire a qualified independent full-state cohort, or explicitly retain exploratory status if no suitable rights/labels exist. Freeze the complete candidate and rejection criteria before opening it. Report paired match-level deltas, provider-specific results and uncertainty, including dead/live and short-spell strata. Do not rename old tests or unidentified labels “fresh.” Challenge video checking and target tuning remain excluded by the controlling rules.

## 3. Priority 1: finite stationary coordinates still trigger the provider's dead-ball shortcut

**Severity: high. Confidence: high for the mechanism; unknown prevalence on the target. Classification: reproduced synthetic weakness plus documented transfer risk.**

The latest correction neutralizes emissions only when `observed` is false: [ball_gap_policy.py:14–15](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/ball_gap_policy.py#L14). Runtime observation is simply `f.ball_observed`, [ball_gap_runtime.py:41–43](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/ball_gap_runtime.py#L41), whose core definition tests finite XY, not freshness: [core.py:22–26](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/gap_solver/core.py#L22).

The frozen tree's root depends on recent speed, with a threshold near 0.0104 m/s, and subsequent branches exploit slow-ball history: [tactical_model.py:83–115](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/gap_solver/tactical_model.py#L83). Feature generation sets first-observation speed to zero and derives history directly from available coordinates: [tactical.py:39–63](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/gap_solver/tactical.py#L39).

I constructed 250 valid frames with the ball stationary at pitch centre, one team having a player exactly at the ball plus two other players, and the opposing team approximately 22 metres away. I passed them through anonymous association, the actual frozen features/tree and the current missing-ball decoder. **All 250 labels were D**, for both the home-controlled and away-controlled versions. Final raw support was approximately `[0.05724, 0, 0.94276]` for H/A/D. This is a synthetic counterexample to treating stationary proximity as sufficient live-control evidence; it is not proof that this exact episode occurred in the match.

It exposes the surviving mechanism: an observed frozen coordinate can accumulate dead-state evidence even though observation persistence is not validated. The project acknowledges DFL's inactive-coordinate carry and unverified freshness. Fairly, the target audit counts only 78 adjacent repeated ball positions across the recording, so this exact constant-coordinate mechanism is **not established as a dominant target failure**: [tactical-audit.json:42](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/reports/input-contract/tactical-audit.json#L42).

**Competitor leverage:** a provider with carried coordinates, a standing player waiting during live play, or stale tracking can defeat the same head that looks excellent on DFL stoppages. Near-perfect DFL D recall cannot settle which explanation the model learned.

**Better alternative and acceptance:** develop externally evaluated observation-quality and live/dead evidence, keeping freshness unknown when no flags exist. Test missing, frozen, jittered, intermittently updated and genuinely stationary live observations separately. A qualified external full-state evaluation should show acceptable false-D rates on stationary live intervals and maintained stoppage recall. Do not install a repetition filter solely because the target's counts suggest one, and do not infer that every stationary ball must be live.

## 4. Priority 2: neutral gaps receive label-order bias and false temporal precision

**Severity: medium to high. Confidence: high. Classification: reproduced deterministic behavior; task-level impact unmeasured.**

Neutralizing missing emissions correctly removes a false observation. But the decoder then chooses one path through a potentially long region with no ball-state evidence. Its equal-score predecessor rule prefers H, then A, then D: [soft_sequence.py:34–44](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/gap_solver/soft_sequence.py#L34). Entire usable segments without any observed ball are withdrawn; missing spans inside a segment containing anchors are still decoded: [ball_gap_policy.py:16–24](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/ball_gap_policy.py#L16).

I supplied 20 strong H emissions, 25 neutral missing frames and 20 strong A emissions, using `.999` support for the anchor label and `.0005` for the other labels. All neutral frames became H; the switch occurred at the first observed A. Reverse the labels and **the same 25 neutral frames remain H**, with the switch now occurring at the first missing frame. H→D and D→H likewise assign the gap H; A↔D assigns it A. A 250-frame gap reproduces the same H/A behavior.

This is label-order preference, not inferred transition timing. Because those frames already have latent H/A/D, `materialized` remains false; the separate neutralization flag is therefore essential. The documentation honestly discloses deterministic ties and that uncertainty flags do not cover all epistemic uncertainty: [ball-gap results:38](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/docs/ball-gap-results.md#L38).

**Competitor leverage:** I would challenge any claim that a precise missing-span possession boundary was recovered. Swapping otherwise equivalent team evidence changes the timing convention, even when there is no evidence justifying a home/away preference.

**Better alternative and acceptance:** retain an explicit ambiguous-boundary interval and indicate whether multiple optimal paths disagree, alongside any required single submission sequence. Add a team-swap invariance test on symmetric evidence. If a tie convention changes, freeze and evaluate it externally; no alternative tie alone is guaranteed to improve the official score. Player counts make these frames usable but, with selected motion weight zero, do not supply a new ownership signal within the neutral span.

## 5. Priority 2: smoothing improves the ranked objective while deleting real changes

**Severity: medium. Confidence: high. Classification: measured tradeoff, not an invalid metric.**

Using official team-spell F1 as primary is appropriate. The weakness is treating its improvement as enough for a broadly useful possession timeline. The selected cost of 32 sums log leaf supports, including a `1e-6` floor, and penalizes every switch equally: [soft_sequence.py:18 and 35–37](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/gap_solver/soft_sequence.py#L18). Those supports are explicitly uncalibrated: [tactical_model.py:188](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/gap_solver/tactical_model.py#L188).

The published evidence already demonstrates the cost. w0-c32 reduces natural DFL boundary F1 from .6323 to .6160 while missed boundaries increase 387→483. On SkillCorner, missed changes increase 623→752 despite improved aggregate boundary F1: [accuracy-first results:59](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/docs/accuracy-first-results.md#L59). Neutralization subsequently reduces masked SkillCorner spurious cuts 1812→1043 while missed changes rise 921→953: [ball-gap results:34](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/docs/ball-gap-results.md#L34).

**Competitor leverage:** short turnovers, interceptions and rapid exchanges are exactly where oversmoothing can make a clean-looking output strategically wrong. Better matched-boundary latency does not compensate for boundaries that disappear entirely.

**Better alternative and acceptance:** evaluate a small externally predeclared alternative using duration or state-specific transition structure, with short-spell recall and dead/live boundary checks alongside official F1. Present a Pareto comparison rather than assuming a single universal “accuracy” improvement. Acceptance should require the official objective to improve and explicitly bound any short-spell or transition-recall loss. Do not change the official metric or tune these bounds against the challenge match.

## 6. Priority 2: stress success does not cover the target's observation contract

**Severity: medium to high. Confidence: high for the gap; uncertain performance consequence. Classification: evidence-backed generalization limitation.**

The current stress mask samples uniformly located blocks of 5, 15, 50, 125 or 250 frames: [temporal_selection.py:37–49](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/gap_solver/temporal_selection.py#L37). That tests deletion under retained player context. It does not reproduce state-dependent camera framing, correlated ball/player loss, false finite ball detections, systematic geometry errors, or match-specific long gaps. Overlaps can create longer deletions, but there is no demonstrated match to the target missingness distribution.

SkillCorner player positions are interpolated using actual identities when resampled from 10 Hz to 25 Hz: [skillcorner.py:156–193](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/gap_solver/skillcorner.py#L156). Target identities and freshness are unverified. The homography gate rejects 7,823 target rows, while its own contract says pitch-to-pixel transform quality is not independent ATD observation validation: [tactical-audit.json:29–33](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/reports/input-contract/tactical-audit.json#L29), [input_contract.py:130–150](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/gap_solver/input_contract.py#L130).

**Better alternative and acceptance:** create an externally designed robustness matrix with missing/stale/false observations, joint player dropout, geometry corruption and long gaps; report recovery versus gap length and anchor configuration. Include native-sample versus resampled comparisons. Keep perturbation parameters independent of challenge correctness. A selected-only model should beat simple carry and nearest-team baselines across relevant regimes, with failure limits stated instead of promising zero uncertainty.

## 7. Priority 3: research preservation has become runtime and handover complexity

**Severity: medium. Confidence: high. Classification: demonstrated delivery limitation.**

The README advertises a single-file pipeline, but its newest candidate is a checkout-based separate entry point; the older bundle remains unchanged: [README:23–34, 50 and 74](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/README.md#L23). The new runtime still loads the temporal model and computes all four older comparators even though selected motion weight is zero: [ball_gap_runtime.py:38–43](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/ball_gap_runtime.py#L38). Entry-point validation requires hashes of research sources and aggregate evidence files as well as actual inference dependencies: [ball_gap_candidate.py:12–17](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/ball_gap_candidate.py#L12).

These checks strengthen provenance. They also mean an unrelated report/source change or missing comparator artifact can prevent selected inference. Multiple generations and legacy options increase the chance of handing over the wrong executable. Exact external replay additionally requires original local caches and archives outside the checkout: [ball-gap results:50–66](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/docs/ball-gap-results.md#L50). This is not evidence that current published receipts are wrong; it limits independent reproduction from GitHub alone.

**Better alternative and acceptance:** preserve research history, but build a minimal, explicitly versioned selected-inference package with comparator generation optional. Keep its provenance manifest and evaluator separate. Require byte-identical selected output against the current route on synthetic fixtures and available local inputs, then smoke-test the documented Python version in a clean environment with only declared package contents. Provide one clearly designated entry command and a reproducible external cache-building recipe. Do not silently promote experimental accuracy claims merely by packaging them better.

## 8. Realistic improvement sequence and dissent

1. **Immediately:** add the stationary-observation and neutral-gap team-swap probes to the research acceptance inventory; document the mechanisms as unresolved, without changing challenge parameters.
2. **Next:** prioritize independent full-state evaluation and externally specified observation-corruption tests. This has higher information value than another seen-data threshold grid or another layer of evidence sealing.
3. **Then:** compare a small, justified live/dead and transition-duration alternative. Retain official spell F1, but inspect short spells, genuine missed transitions and stationary-live false D before acceptance.
4. **Before delivery:** package the chosen frozen route, verify output parity and preserve the diagnostic uncertainty channel. Keep legacy workflows discoverable as historical tools rather than competing default entry points.

I would not revive broadcast fusion immediately: the published automatic run produced zero bounded links, and this review found no evidence that fusion currently supplies a usable missing-ball recovery signal. Nor would I call the rejected motion experiment wasted simply because the selected weight is zero; rejecting a measured loser is sound research. Finally, the documented rules isolation, explicit seen-data caveats, source pinning and output protection are real strengths. They make the evidence auditable. They do not answer the unresolved competitive question: **does this model distinguish possession from the tracking provider's habits when the familiar reference conditions disappear?**

