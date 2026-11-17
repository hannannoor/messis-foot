# MESSI's FOOT — full six-reviewer adversarial council audit

Prepared 8 November 2026, Asia/Singapore.

**This document contains all five agent reports and the coordinator's report in full, verbatim.** Repetition, disagreements, examples, recommendations and limitations are retained. Nothing inside an individual report has been merged into another review or shortened.

## Scope and council method

The reviewed repository is [hannannoor/messis-foot](https://github.com/hannannoor/messis-foot). Current progress was in [open PR #1](https://github.com/hannannoor/messis-foot/pull/1), branch `codex/tactical-validation-and-coverage`, pinned to [cee674190775e9356745f461ba1561e9f2a46f7e](https://github.com/hannannoor/messis-foot/tree/cee674190775e9356745f461ba1561e9f2a46f7e). Default `main` was the older `3a1c8608e050e2f812826719e1af882d87cf2f67`.

All 309 tracked source/evidence files in the local reviewed tree were checked against GitHub's blob hashes, before the reviews and after verification. None changed. Unpublished sibling work was excluded.

Five independent reviewer agents received the user's identical original prompt and the same common audit brief, reproduced in the appendix. Only their report filenames differed. No agent received a specialty, another agent's findings or another agent's report. They reviewed independently in batches because the environment permits three simultaneous child agents. The coordinator inspected the project separately, received agent progress messages, wrote a separate report, and then checked the full outputs. This is an adversarial multi-agent council, **not a council of six different model providers**: the five child reviewers all used `gpt-6.1-sol` at high reasoning effort; the coordinator used the current chat model. Agreement therefore is correlated evidence, not six independent empirical validations.

No project code was changed, no PR was posted, and no challenge video, GT, raw tracking, predictions or frame-level derivatives were inspected. Committed automatic aggregate diagnostics were allowed evidence. No assets were acquired or models trained.

## Verification and how to interpret the criticism

- The fresh full suite ran **341 tests: 322 executed successfully, 19 skipped**. Final output: `OK (skipped=19)`, 19.760 seconds. OCR/tool availability, optional training checks, private delivery fixtures, an opt-in integration test and a Windows symlink privilege account for the skips. Initial sandbox TEMP/hardlink/junction errors were environment restrictions; the link tests passed outside that sandbox. Reviewer shorthand about a passing 341-test suite should be read with this exact count.
- The coordinator independently reproduced short-burst deletion, long neutral-gap/team-order behavior, whole-head team-swap asymmetry and observation-provenance invariance using committed code. Synthetic supports and constructed geometry establish behavior, **not football ground truth or the prevalence of target errors**.
- The natural incremental spellF1 gain from the missing-ball correction is +0.00178627 on the seen regression cohort. A new exploratory paired match bootstrap, resampling within provider and then weighting providers equally, gives a conditional 95% percentile interval of about [+0.00048952, +0.00328566] (20,000 draws, seed 1729). This is positive within that cohort. It does not restore freshness, account for project-wide adaptive reuse or establish target transfer. The reviews' call for stronger uncertainty evidence should not be read as proof the observed gain is zero.
- Finite stale-coordinate behavior is a transfer vulnerability, not a demonstrated dominant target failure: one reviewer notes the committed target input audit counted only 78 adjacent exact ball-coordinate repeats.
- No reviewer measured a rival's score or hidden challenge accuracy. Severity reflects a strict competitor's priorities. Recommendations are proposed experiments, not measured winning alternatives.
- Pinned source links were checked for file existence and valid line bounds. Raw external benchmark scores were inspected as published receipts; the council did not replay their excluded original score archives.

The reports below are the deliverable, not an executive-summary substitute.

## Full reports

1. [Agent 1 — complete report](#agent-1)
2. [Agent 2 — complete report](#agent-2)
3. [Agent 3 — complete report](#agent-3)
4. [Agent 4 — complete report](#agent-4)
5. [Agent 5 — complete report](#agent-5)
6. [Coordinator — complete report](#coordinator)
7. [Exact shared prompt and common brief](#shared-brief)


---

<a id="agent-1"></a>

# Independent competitor audit — reviewer 1

## 1. Scope, method and limits

I audited the latest published progress at commit `cee674190775e9356745f461ba1561e9f2a46f7e` on the open PR branch, using the supplied GitHub-verified source copy. This is not an audit of the older default branch or unpublished sibling directories. I inspected the current missing-ball candidate, feature generation, sequence decoding, ingestion, materialization, experiment selection and published results. I did not read other council reports or previous review reports, change source, inspect challenge footage/labels, acquire data or train anything.

I ran isolated, standard-library synthetic probes through the actual frozen tree and current decoder. I did not duplicate the main test suite. External raw inputs and private evaluation arrays were unavailable, so I cannot independently recompute the reported real-match scores. Numerical benchmark findings below refer to committed reports, while explicitly identified synthetic findings are my reproductions.

My adversarial position is that this project has become much better at preserving experimental evidence than at proving transferable possession recognition. That is a strategic criticism, not an accusation of dishonest reporting. The documentation repeatedly acknowledges the limitations. There is no demonstrated challenge-accuracy result, and I make no claim about a competitor's actual score.

## 2. Competitive assessment

The strongest progress is real: the project uses the official possession-spell objective, whole-match splits, preserved baselines, explicit data boundaries and a sensible correction that stops missing observations accumulating false dead-ball evidence. Rejecting the earlier motion candidate was also appropriate.

The weak point is the remaining information model. The selected prediction uses the old geometry/history tree, disables the motion contribution and applies a powerful continuity prior. During a missing-ball interval it contributes **no new state evidence**, even if player movement is available. Repeated provider conventions and reused references are carrying much of the credibility burden. A competitor could attack this by demonstrating reliable live/dead and ownership transitions under realistic occlusion on a genuinely independent full-state provider. More output files, hashes or synthetic scenarios would not answer that attack.

## 3. Prioritized findings

### 3.1 High — The validation resource is exhausted; the latest improvement is not an independent generalization result

**Confidence: high. Type: demonstrated evidence limitation.**

The current experiment selects on one DFL and two SkillCorner matches, then evaluates on two DFL and eight SkillCorner previously examined matches. The split is explicit in [accuracy_protocol.py:7–10](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/gap_solver/accuracy_protocol.py#L7). The latest report confirms that all references have appeared earlier in project development [ball-gap-results.md:38–40](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/docs/ball-gap-results.md#L38).

Freezing each individual experiment prevents within-cycle reselection. It does not restore independence after the development strategy has responded to earlier test failures. The missing-ball intervention specifically follows a failure observed in the preceding experiment. Its successful regression is useful repair evidence, but cannot quantify unseen-provider reliability.

The natural equal-provider spellF1 gain is only `.564642 → .566428`; the much larger masked gain addresses a deliberately simulated failure mode [results:17–28](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/docs/ball-gap-results.md#L17). Neither magnitude establishes statistical reliability across new matches. A million correlated frames do not turn two full-state regression matches into a large independent sample.

**Why a competitor cares:** I would challenge any claim that the latest release is meaningfully more accurate on the competition game. You currently cannot answer that challenge with independent evidence, although your wording correctly avoids claiming it.

**Better alternative and acceptance:** Spend the next research cycle on legally usable, untouched full H/A/D references. Lock one candidate and the evaluation protocol before opening labels. Publish paired match deltas, uncertainty across matches, per-class results and short-spell recall. If adequate fresh data cannot be obtained, explicitly stop treating further improvements on this cohort as release qualification; retain them as exploratory regression repairs.

### 3.2 High — Dead-ball recognition is still entangled with a provider's coordinate-freezing convention

**Confidence: high for the dependence and transfer gap; unmeasured for target error. Type: evidence-backed limitation.**

The frozen model records nearly universal repeated inactive-ball coordinates in its own limitations [tactical_model.py](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/gap_solver/tactical_model.py#L231). The feature code derives velocity directly from adjacent positions, appends zero when unavailable and tracks slow-ball duration [tactical.py:39–63](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/gap_solver/tactical.py#L39). The latest fix neutralizes **missing** ball rows; finite repeated coordinates remain full evidence [ball_gap_policy.py:14–24](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/ball_gap_policy.py#L14).

My synthetic probe repeated a finite midfield ball for 100 frames, with a home point 1m away and away point 10m away. The actual frozen head finished at support approximately `(H .05724, A 0, D .94276)`, and the decoder emitted D on all 100 frames. This is not proof those frames should be live: the point is that a true stationary ball and a stale carried coordinate can generate the same input, while the model treats it as strong D evidence.

DFL's impressive D recall therefore remains insufficient reassurance. SkillCorner's near-zero false-D result covers known-live intervals and cannot test missed stoppages [results:24–26](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/docs/ball-gap-results.md#L24). Both halves of the cross-provider live/dead claim are not independently measured.

**Better alternative and acceptance:** Add externally evaluated corruption regimes for held coordinates, irregular samples, jitter and dropped/reappearing observations; report stationary-live and genuine-dead strata separately. A coordinate repetition rule alone is not a valid freshness detector. Develop observation provenance and a joint live/dead model with player/context evidence where rights permit. Require improvement on a second full-state provider and robustness when the easy frozen-coordinate cue is removed.

### 3.3 High — The continuity penalty demonstrably erases strongly supported short possessions

**Confidence: high. Type: reproduced algorithm behavior, with supporting real-data tradeoff.**

Each switch costs 32, regardless of whether it is H↔A or live↔dead [soft_sequence.py:24–44](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/gap_solver/soft_sequence.py#L24). I passed the current policy 100 H-support frames, 20 A-support frames, then 100 H-support frames. Supports were `(.9,.05,.05)` for H and `(.05,.9,.05)` for A, with every frame observed and usable. Output was H for all 220 frames. Increasing the A interval to 23 frames preserved all 23 A labels.

The mechanism is transparent: creating the intervening possession costs two switches, or 64 log-score units. Twenty frames with a likelihood ratio of 18 provide only `20 × log(18) ≈ 57.8`. The decoder can therefore erase 0.8 seconds of consistently strong opposing evidence. This is an intended optimization tradeoff, not a broken Viterbi implementation.

The real-data receipts show its practical direction: after the ball-gap fix, masked SkillCorner missed boundaries rise `921 → 953`, while spurious cuts decline `1812 → 1043` [results:32–36](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/docs/ball-gap-results.md#L32). The acceptance gate checks aggregate accuracy/spellF1 and D recall, without a short-spell or boundary-recall constraint [ball_gap_experiment.py:108–116](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/ball_gap_experiment.py#L108).

**Why it matters:** Possession spells are the actual objective. A smoothing gain that comes partly from deleting real turnovers is exploitable, especially around tackles, interceptions and brief recoveries.

**Better alternative and acceptance:** Predeclare duration-stratified spell recall and boundary precision/recall. Compare transition-specific costs or an externally fitted duration model, rather than assuming every transition needs the same penalty. Select externally on the official primary score while bounding short-spell regression. Do not infer that the rejected motion model should simply be switched back on.

### 3.4 High — Missing-ball recovery is chiefly continuation, not recovery of hidden changes

**Confidence: high. Type: demonstrated information limitation.**

For every unavailable ball row, the policy replaces the entire emission vector with zero. It checks whether a whole usable segment has any observed ball, but places no maximum distance to evidence or internal-gap duration bound [ball_gap_policy.py:15–24](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/ball_gap_policy.py#L15). Three players per side can keep an otherwise ball-missing sequence usable [soft_sequence.py:6–9](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/gap_solver/soft_sequence.py#L6).

Player movement inside such a gap cannot change the selected state's emission; motion weight is zero. Same-state endpoints favor continuing that state regardless of hidden events. Different endpoints leave some boundary locations tied. This corrects fabricated D evidence, but provides no direct mechanism for detecting a hidden A possession between H endpoints or a hidden stoppage.

The later materializer is also unbounded within structural periods: it forwards the previous label, backfills leading uncertainty and uses D for a wholly unknown period [materialization_control.py:4–19](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/gap_solver/materialization_control.py#L4). That can be defensible as a submission/scorer convention. It should not be confused with additional perception.

**Better alternative and acceptance:** Evaluate gaps by length, endpoint agreement, hidden team changes and hidden D intervals. Use external references to compare simple carry, endpoint interpolation and genuinely informative motion/context inference. Require positive hidden-change recovery at bounded false-spell cost, not merely higher aggregate missing-frame accuracy. Preserve uncertainty for unsupported decisions in downstream analysis even when a scoring file must contain a materialized label.

### 3.5 Medium–high — Team identity changes predictions even when physical evidence is exchanged

**Confidence: high. Type: reproduced end-to-end model limitation.**

The report acknowledges tactical-head asymmetry [results:38](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/docs/ball-gap-results.md#L38), but its magnitude deserves an explicit invariant test.

I created 180 valid, observed frames with ball `(25 + .08i, 34)`, a home point 0.5m to its right and an away point 1m to its right. I then exchanged the two team point sets. The current tree plus ball-gap decoder emitted **180 H frames in both versions**. Final leaf support in both was approximately `(.68788,.31074,.00139)`. This was not a symmetric-input tie: the nearest-team distances differed and were exchanged. The deterministic model's support favored H strongly in both runs.

A synthetic example does not establish aggregate away-team bias on real games. It does establish that the system can encode label preference instead of reversing its conclusion when team evidence reverses. Decoder-only emission-swap tests cannot validate this property of the whole pipeline.

**Better alternative and acceptance:** Add end-to-end team-swap tests and report the disagreement rate on external inputs. Train with swapped examples or evaluate an average of original and swapped predictions, restoring columns before combining. Accept a change only after external official-score and per-team checks; enforce exact equivariance for unique-optimum synthetic cases and document ties separately.

### 3.6 Medium — The missingness stress is narrower than the target input uncertainty

**Confidence: high for protocol scope; target impact unmeasured. Type: evidence-backed coverage gap.**

The input masker chooses random starts and lengths from `5,15,50,125,250` frames [temporal_selection.py:37–49](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/gap_solver/temporal_selection.py#L37). The latest experiment reuses a 30% mask and one seed. This tests a useful intervention, but not whether missingness depends on turnovers, ball location, crowding, camera motion or simultaneous player loss. Overlapping masks can make longer gaps, so 250 frames is not an absolute maximum; the distribution is nevertheless synthetic.

The adapter equates finite source coordinates with availability and assigns a frame-based sample time [input_contract.py:114–125](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/gap_solver/input_contract.py#L114). A good homography is explicitly not independent validation of those observations. External SkillCorner resampling also uses provider identities for player interpolation, unlike anonymous target detections.

**Better alternative and acceptance:** Predeclare several corruption families and seeds, including state-dependent gaps, player loss and stale finite observations. Derive distributions from licensed external sensor behavior, not target prediction outcomes. Publish robustness curves and worst-match deltas. Preserve the existing fixed mask as a regression check rather than replacing it with a favorable new one.

### 3.7 Medium — The latest deliverable depends on substantial experimental machinery that its selected policy does not need

**Confidence: high. Type: demonstrated delivery/maintenance limitation.**

The newest runtime associates anonymous players, loads the temporal model and computes four comparator predictions before producing its selected geometry-only sequence [ball_gap_runtime.py:38–43](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/ball_gap_runtime.py#L38). Those comparators have research value, but the selected policy does not use the motion head. Thus failure or absence of an unrelated comparator artifact can block the desired submission.

Furthermore, exact evidence verification requires excluded local arrays and historical archives [results:44–54](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/docs/ball-gap-results.md#L44). Hashes authenticate retained bytes; they do not let a new reviewer reconstruct absent arrays. The target parser is deliberately specific to documented Barcelona/Athletic names, 25Hz and the original frame count. That is reasonable for this challenge, but not a reusable football pipeline contract.

**Better alternative and acceptance:** After externally qualifying a winner, export one minimal selected inference package. Make comparator generation optional. Keep the evidence-rich research tree separate, with a clean acquisition-to-evaluation recipe for licensed external data. Acceptance should include a fresh-directory, offline selected-only run requiring no training/comparator archives and producing the same selected CSV hash. Test the exact supported Python versions rather than treating grammar parsing as runtime compatibility.

## 4. Realistic improvement sequence

1. **First, strengthen evidence rather than add another decoder variant.** Acquire or resolve rights/provenance for untouched full-state external references. Freeze a limited protocol and the current candidate. If that remains impossible, state the resulting research ceiling explicitly.
2. **Immediately add cheap diagnostic probes.** Preserve the short-possession, team-swap and stale-coordinate examples above. Expand external reporting to short-spell recall, hidden-gap changes, stationary-live/dead strata and multiple missingness regimes. These checks do not require touching challenge labels.
3. **Then address the information deficit.** Externally evaluate a missingness-aware, team-symmetric joint state model, or a simpler model with transition-specific temporal structure. Compare against carry and endpoint baselines. Reuse the rejected motion model only as a comparator unless new evidence qualifies it.
4. **Qualify on untouched data once.** Require meaningful paired improvements on the official objective, with explicit bounds on short-spell and per-team regressions. Keep DFL shortcut stress and known-live SkillCorner results separate from full-state generalization claims.
5. **Package one route for delivery.** Preserve research artifacts, but ship a minimal selected-only inference path with a precise input contract and reproducible output. Keep historical/manual/fixed-D routes clearly outside that default handoff.

The core competitive weakness is not lack of implementation effort. It is that the selected system still uses continuity and provider-specific geometric cues where the task requires evidence of hidden ownership and live/dead changes. The next defensible advance needs to close that gap and demonstrate it externally.


---

<a id="agent-2"></a>

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

---

<a id="agent-3"></a>

# Independent competitor audit — reviewer 3

## 1. Scope, position and limits

I reviewed the latest progress at open PR #1, commit `cee674190775e9356745f461ba1561e9f2a46f7e`, rather than judging the older default branch. The supplied audit workspace is reported to match all 309 tracked GitHub blob hashes. My evidence comes from the current rules, actual adapters and inference code, frozen model, experiment protocol, aggregate receipts and primary results. I did not read other council outputs or earlier neutral/strategy/code-review audits, change project source, acquire data, train models, inspect challenge footage or consult challenge ground truth.

I ran two small, standard-library synthetic probes against the actual selected inference components: long neutral-gap decoding and team-swap consistency. These establish implementation behavior, not football accuracy. I also inspected the published numerical receipts. I did not rerun the full suite, independently regenerate the external benchmarks from raw inputs, or validate their provider labels. The parent reviewer is handling the main suite.

My competitor's argument would be: **this is a careful experimental software package, but its strongest reproducible property is preserving and explaining its own experiments; its weakest property is proving that the chosen possession decisions transfer to the competition.** That criticism survives the honest caveats. However, the caveats mean it would be unfair to accuse the authors of claiming measured target accuracy, using forbidden target labels, or presenting rejected temporal research as a successful deployment.

Severity below concerns competitive consequence, rather than security or data-loss risk.

## 2. High severity / high confidence: the evaluation runway has been consumed

**Type: demonstrated evidence limitation.**

The current selection uses one DFL and two SkillCorner matches; regression uses two DFL and eight SkillCorner matches. Their identities are hard-coded in [accuracy_protocol.py:7–11](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/gap_solver/accuracy_protocol.py#L7). All were previously examined. The current report explicitly acknowledges that repeated development can overfit project decisions without refitting a head: [ball-gap-results.md:38–40](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/docs/ball-gap-results.md#L38).

Freezing the next patch before rescoring the same matches protects against changing that patch after seeing its score. It does not erase the fact that those matches helped reveal which patch to propose. Repeated diagnoses, reference searches and selection criteria adapt the project to the cohort at the project level.

The latest incremental natural-input result is also much smaller than the dramatic missing-ball headline: equal-provider spell F1 moves **.564642 → .566428**, DFL is unchanged, and SkillCorner accuracy moves **85.82% → 85.93%**. The masked gain is substantial, but it answers a different question. See the actual [results table and means:13–22](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/docs/ball-gap-results.md#L13).

**Competitive consequence:** I would challenge every inference from “passed all checks” to “likely wins on unseen input.” Your fresh external evidence budget is effectively empty; test counts and hashes cannot replenish it.

**Better alternative and acceptance:** stop promoting new empirical accuracy claims from this cohort. Obtain a licensed, untouched cohort and freeze the complete pipeline and analysis before opening its labels. Report paired match-level uncertainty, all per-match deltas and relevant missingness strata; avoid treating hundreds of thousands of adjacent frames as independent observations. Require a predeclared primary improvement with uncertainty narrow enough to support the claim. If fresh data remain unavailable, retain “experimental” status and prioritize structural correctness over another score-driven selection cycle.

## 3. High severity / high confidence: neither provider independently tests your full intended problem

**Type: evidence-backed transfer limitation, not direct label leakage.**

The model's most decisive tree split is on recent ball speed, and its artifact records that inactive DFL ball coordinates repeat on **99.9993%** of contiguous inactive frames. It also records that the old active-only diagnostic spell score regressed on both held-out matches: [tactical_model.py:229–238](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/gap_solver/tactical_model.py#L229).

SkillCorner supplies known-play H/A phases, with missing annotation preserved as X, rather than a complete independent D reference. The adapter's contract makes this explicit: [skillcorner.py:195–200](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/gap_solver/skillcorner.py#L195). Its near-zero false-D result measures avoiding D during known live play; it cannot establish recognition of real stoppages in unlabelled regions.

This is not inference code reading BallStatus or reference possession. The problem is **provider convention acting as an easier surrogate for the physical event**. Two providers do not automatically produce two independent full-state validations. Equal weighting averages different evidence gaps; it does not close them.

**Competitive consequence:** a competitor with a less impressive DFL score but independently verified stoppage recognition could have a more transferable system. You cannot establish that your excellent D recall is measuring the same mechanism needed on ATD.

**Better alternative and acceptance:** separate live/dead validation from team-owner validation. Use fresh external full-state labels for both, or explicitly leave the unsupported claim open. Run frozen-coordinate removal, plausible stationary-live-ball, moving-dead-ball and stale-coordinate stresses externally. A credible live/dead improvement should survive removing the provider's coordinate-freeze convention while preserving team-spell quality. Do not replace this with manual challenge-game annotation; [RULES.md:7–22](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/RULES.md#L7) forbids the relevant target-ground-truth shortcuts.

## 4. High severity / high confidence: neutralizing a gap does not recover its possession history

**Type: demonstrated algorithmic limitation; target frequency and accuracy impact unmeasured.**

The new fix correctly removes spurious evidence: missing-ball emissions become equal zeros. But a usable segment is rejected as wholly unsupported only when **none** of its rows has a ball observation. There is no maximum neutral-gap duration within an otherwise supported segment: [ball_gap_policy.py:14–24](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/ball_gap_policy.py#L14). Three available player points on each team can make a missing-ball frame usable, even though the selected policy has motion weight zero: [soft_sequence.py:6–9](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/gap_solver/soft_sequence.py#L6).

I passed the real decoder 20 strongly H observations, **2,500 neutral missing rows**, then 20 strongly A observations, all within one usable period. It returned **2,520 H rows followed by 20 A rows**, with the switch exactly at reacquisition. Unsupported-segment counts were zero. That 100-second gap could contain turnovers and stoppages; the inputs provide no information locating them. The selected method therefore supplies a precise boundary through deterministic path/tie behavior, rather than recovered events.

This differs from ordinary latent-X materialization. Those neutral rows already receive latent H, so `latent_unknown_active` and `materialized_active` do not count them as unknown or carried. The dedicated `neutralized` column does expose them; I acknowledge that transparency: [ball_gap_runtime.py:52–62](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/ball_gap_runtime.py#L52).

A second probe confirmed that a wholly unknown period materializes entirely as D, exactly as documented in [materialization_control.py:12–18](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/gap_solver/materialization_control.py#L12). This can be a legitimate scorer convention; it is not an independent stoppage detector.

**Competitive consequence:** I would target “hidden recovery” claims with gaps containing opposing possession between identical endpoints, or several changes between different endpoints. Your current zero-motion correction cannot infer those events from nothing.

**Better alternative and acceptance:** preserve evidence-age and boundary-location uncertainty separately from final scorer-compatible labels. Externally compare duration-limited propagation, explicit unknown intervals and a motion-informed or duration-aware alternative. Require gap-stratified hidden-spell recall and false-spell counts; include gaps longer than ten seconds and distinguish inferred ownership from merely serialized ownership. Keep a deterministic baseline when new evidence is absent, but describe it as a prior.

## 5. Medium severity / high confidence: the selected pipeline has avoidable home/away bias

**Type: demonstrated symmetry failure; real-world error magnitude unmeasured.**

The decoder can be equivariant when scores are swapped and its optimum is unique, but the frozen tactical head is asymmetric. The repository admits this in [accuracy-first-results.md:36–38](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/docs/accuracy-first-results.md#L36). The issue remains in the latest candidate because it uses that same head.

I constructed 120 observed frames with a ball moving at 1 m/s, home nearest distance 2.5 m and away nearest distance 4 m. The selected core path returned H for all 120 rows. Swapping the two distances and rerunning returned **H for all 120 again**. The final support vector was identical in both cases: approximately **(.687875, .310736, .001389)**. This is a repeatable metamorphic failure, not a measured match accuracy estimate.

For this geometry, the feature history has no confirmed close owner. The head nevertheless assigns a strong preference to one team role. The tree uses team-specific histories and distances: [tactical.py:35–63](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/gap_solver/tactical.py#L35).

**Competitive consequence:** a challenger can ask whether successful ownership recognition follows geometry or provider/team-role priors. You currently cannot guarantee consistent behavior under simple role exchange.

**Better alternative and acceptance:** test the complete pipeline under team exchange, using physically valid external sequences. Compare symmetric training augmentation, a relative-feature head, or averaging original and reversed head supports before decoding. Preserve a separate policy for exact ties rather than silently assuming unique optima. Acceptance should include end-to-end label exchange on unique-optimum fixtures and no material degradation on fresh per-team spell scores. Do not tune a compensating home/away bias on the challenge match.

## 6. Medium severity / high confidence: current gates reward smoother possessions while allowing more genuine changes to disappear

**Type: demonstrated tradeoff plus objective-governance limitation.**

The latest policy increases missed changes:

- Natural SkillCorner: **752 → 758**.
- Masked SkillCorner: **921 → 953**.
- Masked DFL: **632 → 645**.

Boundary F1 improves because false cuts fall faster. Those are legitimate primary-score tradeoffs, disclosed in [ball-gap-results.md:32–36](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/docs/ball-gap-results.md#L32). The acceptance function, however, has no missed-transition, short-possession or worst-match constraint; it checks aggregate primary/frame metrics and selected D measures: [ball_gap_experiment.py:97–116](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/ball_gap_experiment.py#L97).

One masked DFL match loses about .00998 spell F1 versus the previous candidate, while aggregate checks still pass: [post-review-diagnostics.json:117–124](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/reports/ball-gap/post-review-diagnostics.json#L117).

**Competitive consequence:** “better possession” remains ambiguous. The official metric rewards complete team spells, so optimizing it is rational; calling fewer spurious cuts “better recovery” would overstate the result when hidden or short real possessions increasingly vanish.

**Better alternative and acceptance:** retain the ranking metric as primary, but predeclare secondary diagnostics by possession duration, missingness and team. Compare duration-aware transition models with the uniform 32-point switch penalty. Require a justified cap on hidden/short-spell recall losses, or explicitly accept and name the tradeoff. Never add a veto retrospectively to reject an inconvenient outcome; freeze it for the next independent experiment.

## 7. Medium severity / high confidence: the main stress test is easier to characterize than the actual observation failure

**Type: evidence-backed robustness gap.**

The current intervention is tested with one deterministic 30% contiguous mask using seed 1729. Mask lengths are drawn from **5, 15, 50, 125 and 250 frames**: [temporal_selection.py:37–48](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/gap_solver/temporal_selection.py#L37). This tests deleted coordinates. It does not make a surviving finite coordinate wrong, stale or delayed.

Actual input freshness is explicitly unverified; the target audit records 85,831 player-without-ball rows and 7,823 rejected homographies: [tactical-audit.json:26–45](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/reports/input-contract/tactical-audit.json#L26). Those are automatic input diagnostics, not permission to select thresholds on this match.

SkillCorner interpolation also uses provider player identities before anonymous matching: [skillcorner.py:171–193](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/gap_solver/skillcorner.py#L171). Anonymous association afterwards does not undo that smoother upstream information.

**Competitive consequence:** your method may look robust to absence while remaining brittle to false presence—the dangerous case for a speed-driven head.

**Better alternative and acceptance:** add externally designed stale/frozen detections, time shifts, sparse opposition, coordinate jumps and long-gap regimes, with multiple fixed seeds. Evaluate a native-rate or identity-free resampling ablation. Report paired score distributions and coverage by corruption type. Require survival of these tests before treating the current ball-gap correction as general observation robustness.

## 8. Lower severity / high confidence: release complexity now exceeds what the selected method needs

**Type: demonstrated delivery/reproducibility limitation, not a broken inference claim.**

The README foregrounds a single-file tactical route while the latest experimental policy has a separate entry point and checkout dependencies. Its runtime always loads the temporal artifact and generates four comparators before selected zero-motion inference: [ball_gap_runtime.py:38–43](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/ball_gap_runtime.py#L38). Scientific comparison justifies preserving these outputs; mandatory comparator work need not be a permanent deployment dependency.

Exact benchmark replay requires private intermediate archives under recorded sibling paths and instructions for a clean copy: [ball-gap-results.md:44–66](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/docs/ball-gap-results.md#L44). Public hashes prove identity once those artifacts exist; they do not regenerate missing intermediates.

**Competitive consequence:** another team can deliver a smaller, clearer final route and demonstrate fresh-clone reproducibility with less operator knowledge. Your documentation's preservation discipline also imposes cognitive cost.

**Better alternative and acceptance:** after scientifically choosing a final policy, package one documented production inference path and make comparators optional. Provide a clean external-data rebuild recipe from licensed sources through final receipts, plus time/memory measurements. Verify in an isolated fresh checkout without unpublished folders. Keep the historical package available for audit.

## 9. Prioritized improvement sequence

1. **Immediately:** add the long-gap and whole-pipeline team-swap probes to the scientific checklist; correct any interpretation that treats all latent H/A/D as equally evidenced. Keep the present artifact frozen.
2. **Before more tuning:** secure fresh full-state external evidence and freeze the next decision protocol. If unavailable, state that the empirical promotion question remains unresolved.
3. **Next bounded engineering experiment:** address team symmetry and stale/long-gap handling, with feasibility checks before costly grids. The earlier 27-policy temporal grid was structurally unable to add labels; that documented lesson in [TEMPORAL_RECOVERY.md:13–17](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/TEMPORAL_RECOVERY.md#L13) should become a general preflight requirement.
4. **Independent evaluation:** report official spell scores, complete live/dead validity, hidden/short-spell behavior and uncertainty together. Do not infer superiority from higher assignment coverage.
5. **Finally:** consolidate delivery, benchmark runtime and perform a fresh-clone reproduction.

I would not start by expanding OCR, adding another ensemble, or forcing zero unknown output. Those may eventually help, but your immediate competitive weakness is the gap between precise, reproducible labels and independently supported possession recovery.


---

<a id="agent-4"></a>

# Council reviewer 4 — adversarial audit of MESSI's FOOT

## 1. Scope, posture and limits

I reviewed the latest open-PR snapshot, commit `cee674190775e9356745f461ba1561e9f2a46f7e`, rather than treating older `main` as current progress. My evidence is the verified 309-file publication checkout, principally the latest ball-gap policy/runtime, sequence decoder, tactical model/features, input adapters, experiment protocols and published results. I did not read other council outputs or earlier neutral/strategy/code-review audits. I did not inspect challenge footage, labels, private prediction arrays or unpublished neighboring work, acquire data, train anything, or modify project source.

I ran small read-only Python probes of the actual decoder and frozen tree. Those establish implementation behavior, not football accuracy. The coordinator separately reported 341 unit tests passing with 19 environment-dependent skips; I did not duplicate that suite or independently replay external scoring, whose original archives are absent from this public snapshot.

My competitor's argument is straightforward: you have built unusually careful evidence bookkeeping around an ownership model whose transferable football understanding is still weakly demonstrated. The neutral-missing fix is sensible and its stress results are useful. Nevertheless, the current engine can extend almost no evidence over an arbitrarily long interval, suppress strong short possessions, and change its answer when the same scene's teams are renamed. Those are stronger competitive vulnerabilities than cosmetic repository defects.

Severity below concerns competitive impact. “Demonstrated” means source or a reproducible probe establishes the behavior; it does not mean hidden-target failure has been measured.

## 2. High severity / high confidence: the benchmark cannot establish the capability that matters most

**Evidence-backed evaluation limitation.** The latest improvement is evaluated on references already examined during earlier research. Its natural equal-provider spellF1 gain is only `.564642 → .566428`; its larger gain, `.460077 → .491821`, is under the synthetic mask. DFL contributes only two regression matches with full H/A/D state, while SkillCorner contributes eight matches with known-play H/A only. These distinctions are correctly disclosed in [ball-gap-results.md:13–40](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/docs/ball-gap-results.md#L13-L40).

The DFL provider repeats inactive ball coordinates almost universally. The frozen model itself records both this limitation and active-only spellF1 regressions on its original two held-out matches in [tactical_model.py:229–238](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/gap_solver/tactical_model.py#L229-L238). SkillCorner's other-provider evidence does not independently repair that missing test: it cannot measure missed stoppages, while DFL's stoppage performance can exploit a provider convention. A near-zero SkillCorner false-D rate and excellent DFL D recall therefore do not jointly constitute an independent full-state validation.

**Why a competitor cares:** I can accept every reported number and still reject the inference that your missing-ball and dead-ball reasoning transfers to the challenge. Freezing the latest experiment prevents within-experiment reselection; it cannot undo earlier knowledge of the same matches. No new head fitting is required for research decisions to overfit a familiar benchmark. Your own disclosures make this criticism fair, not obsolete.

**Better alternative and acceptance:** spend the next research budget on a genuinely untouched, licensed H/A/D cohort with an observation regime that does not encode D through frozen coordinates. Record all intended uses and seal it before scoring. Use existing data for development; run one final frozen comparison against the current candidate and simple carry/distance baselines. Require improvement in official spellF1, report every match, and prospectively bound regressions in short-spell recall and dead-ball precision/recall. If that reference cannot be obtained, retain the experimental designation and stop treating successive seen-data gains as accumulating independent evidence.

## 3. High severity / high confidence: one observation can authorize unlimited “recovery”

**Demonstrated structural limitation.** [ball_gap_policy.py:15–24](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/ball_gap_policy.py#L15-L24) neutralizes missing-ball emissions but only rejects a usable segment when *none* of its rows has an observed ball. One observation anywhere in the segment defeats that rejection. There is no anchor-distance limit, evidence-age decay or maximum neutral-span length. Usability can continue with three player points on each team even without the ball ([soft_sequence.py:6–9](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/gap_solver/soft_sequence.py#L6-L9)); selected motion weight is zero, so those players do not supply ownership emissions.

My probe called `decode_ball_gap` with one period, all rows usable, support `(0.99, 0.005, 0.005)`, and `observed=[True, False, ...]`. At segment lengths 27, 252 and 2,502, every latent output was H. The last case extends a single observed H preference over roughly 100 seconds without another ball observation. The score assigned to missing rows is neutral, but the *inferred state* is still extrapolated without a horizon. Reversing the location of the anchor can similarly backfill earlier uncertainty offline.

Separately, [materialization_control.py:10–18](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/gap_solver/materialization_control.py#L10-L18) fills latent X across an entire structural period regardless of internal quality barriers. `H + 250 X + A` becomes 251 H followed by A. An entirely unknown period becomes D by convention. The latest local report records 60,321 neutral usable rows and 8,059 latent-X rows subsequently materialized ([results:82](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/docs/ball-gap-results.md#L82)). These counts are honestly labelled, but they show the practical scale of inference and convention.

**Why a competitor cares:** the new fix stops hallucinating *D evidence* from absence, yet can still hallucinate *continuity* over absence. Hidden turnovers and stoppages cannot be discovered from zero emissions. Latent-X totals also miss the enormous set of neutral rows assigned a state by the decoder itself; the uncertainty CSV does expose neutralization, so the issue is interpretation rather than concealed data.

**Better alternative and acceptance:** keep submission carry separate, but report evidence age, distance to both anchors, neutral-run duration, and whether opposite-anchor alternatives have equal score. Externally compare finite-horizon continuity, explicit unknown-gap states, and interval posterior alternatives. Synthetic acceptance should include one-anchor gaps of increasing duration, internal quality barriers, opposite anchors and entirely hidden H→D→A sequences. A 100-second one-anchor gap must not receive the same evidential status as sustained observed control. Select any horizon externally, never from challenge coverage.

## 4. High severity / high confidence: smoothing buys spell quality by deleting real short events

**Demonstrated mechanism and observed tradeoff.** The decoder subtracts the same switch cost on every change and sums frame log-supports ([soft_sequence.py:24–44](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/gap_solver/soft_sequence.py#L24-L44)). With c32, an interior H→A→H excursion must earn roughly 64 log-score units to pay for its two boundaries. For A supports `(0.005,0.99,0.005)` against H, each frame supplies about `log(198)=5.29` units: ten nearly certain A frames still cannot pay for the excursion.

I tested 100 strong-H frames, then 5/10/20/50 strong-A frames, then 100 strong-H frames, with every observation present and usable. The five- and ten-frame A possessions vanished entirely; the 20- and 50-frame versions survived. This is neither an implementation accident nor proof every short spike should survive. It demonstrates the architectural price imposed on genuine short control sequences.

The published evidence shows the same direction: masked SkillCorner spurious cuts decrease 1,812→1,043 while missed changes increase 921→953; masked DFL misses increase 632→645. Natural SkillCorner misses also increase ([results:32–36](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/docs/ball-gap-results.md#L32-L36)). Reporting lower matched-boundary latency cannot recover transitions that were never matched.

**Why a competitor cares:** I would target rapid turnovers, contested control and short possessions, and demonstrate that a consistent-looking timeline is not necessarily an accurate one. Official spellF1 is the correct competition objective; the criticism is that one global penalty is a blunt optimization mechanism, particularly when its input supports are uncalibrated leaf frequencies and adjacent frames are highly correlated.

**Better alternative and acceptance:** externally compare state-specific/duration-aware transition models and a boundary head that can override persistence when observed evidence is strong. Calibrate or temper accumulated support on development data rather than treating every correlated frame as independent confirmation. Predeclare short-spell recall strata and missed-transition limits alongside spellF1. Do not merely lower c32 until existing regression scores look nicer.

## 5. Medium-high severity / high confidence: team identity affects answers beyond physical evidence

**Demonstrated model limitation.** The tactical head uses separate home/away distances and remembered ownership flags ([tactical.py:11–14,59–63](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/gap_solver/tactical.py#L11-L14)). A conventional asymmetric tree is then used directly for selected emissions ([ball_gap_runtime.py:40–43](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/ball_gap_runtime.py#L40-L43)). The documentation acknowledges asymmetry, but does not establish its size or its competitive cost.

I generated 100-frame moving-ball scenes with a player on each side, then exchanged complete home/away point sets. Across six speeds and seven distances per team, 63 of 294 final-row argmax decisions failed the expected H/A exchange. This grid is synthetic, includes symmetric/contested cases, and is not an estimate of match error frequency. A concrete asymmetric-distance case used speed 1 m/s, home distance 3 m and away distance 8 m: after swapping the teams, the head still preferred H. In both orientations the support was approximately `(0.687875,0.310736,0.001389)`. This is a sizeable preference, not numerical tie noise.

**Why a competitor cares:** naming a team home should not itself establish who controls the ball. A four-match training cohort can bake in ownership and team-style priors that fail on another fixture. The decoder's symmetry under exchanged emissions does not make the complete pipeline symmetric when its emissions are not.

**Better alternative and acceptance:** benchmark mirrored-data augmentation, symmetric feature construction, or averaging original supports with reversed supports from the fully exchanged feature stream. Treat this as a new externally selected model/policy, preserving the current artifact. Require exact equivariance for unique-optimum synthetic scenes and report original-versus-exchanged whole-match metrics plus per-team errors. Do not promise symmetry will improve scores before testing it.

## 6. Medium severity / high confidence: the stress test is narrower than the missing-evidence failure modes

**Evidence-backed limitation with unverified transfer risk.** The mask generator chooses uniformly from active indices and lengths 5, 15, 50, 125 or 250 frames ([temporal_selection.py:37–49](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/gap_solver/temporal_selection.py#L37-L49)). That is a useful controlled missing-coordinate test. It does not reproduce correlated player disappearance, mistaken ball observations, stale finite coordinates, camera motion, or failure clustered around turnovers. Natural inputs already contain some real defects, but no evidence shows the synthetic intervention matches challenge missingness.

SkillCorner also resamples 10 Hz tracking to 25 Hz, including identity-assisted player interpolation and interpolated ball coordinates ([skillcorner.py:163–200](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/gap_solver/skillcorner.py#L163-L200)). The selected policy's observed flag is ordinary coordinate availability, not native-detection freshness. Thus an interpolated point can receive the same emission weight as a physical source observation, while a stale but finite target coordinate is not neutralized. This is not direct label leakage; it is observation-quality mismatch.

**Better alternative and acceptance:** add externally designed stresses for joint player/ball loss, frozen finite ball runs, decoys, geometry failures, long correlated gaps and transition-centered loss. Evaluate by gap duration and endpoint relationship, and include a native-source-time sensitivity check so interpolation does not silently multiply confidence. Reserve at least one missingness regime for final evaluation. A competitor with fewer architectural layers but a broader externally tested observation model could be more robust; current evidence cannot rank that hypothetical competitor.

## 7. Medium severity / high confidence: release complexity is advancing faster than delivery simplicity

The latest selected runtime loads the old temporal model and computes all four comparators before producing the winner, even though selected motion weight is zero ([ball_gap_runtime.py:38–43](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/ball_gap_runtime.py#L38-L43)). Replaying the published evidence requires original local caches, score archives and a carefully prepared separate copy retaining older receipts ([results:44–66](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/docs/ball-gap-results.md#L44-L66)). Source seals are valuable integrity controls; they do not by themselves provide a clean-room reproduction path for an outside reviewer.

This is a delivery limitation, not a demonstrated inference failure. The repository has real isolated-runtime and format checks. But the strongest route is a multi-file research entry point, while the historical single-file route remains preserved separately. A competitor could offer one clear frozen entry, minimal runtime dependencies, and a documented replay from licensed raw inputs.

**Better alternative and acceptance:** retain research comparators and immutable receipts, but add a release export containing only selected inference dependencies, one command and explicit version/model identity. Provide a clean-room raw-to-score recipe with resource estimates and no dependence on unavailable historical caches. Verify output parity on synthetic fixtures and licensed external fixtures. Measure elapsed time and peak memory before claiming comparator computation is materially expensive; I did not benchmark it.

## 8. Prioritized improvement sequence

1. **Protect validity first.** Define the untouched full-state evaluation acquisition plan and stop consuming it opportunistically. Maintain the current frozen candidate as baseline; do not use challenge video, labels or coverage to choose parameters.
2. **Expose the actual missing-evidence boundary.** Add evidence-age/neutral-span diagnostics and the one-anchor, barrier and hidden-transition probes. Preserve scorer materialization while making decoder extrapolation separately countable.
3. **Fix model invariants on development evidence.** Compare a symmetric tactical head and quality-aware emissions, including stale finite coordinates and source-time weighting. Select externally and retain the original artifacts.
4. **Improve transitions deliberately.** Compare duration-aware decoding with declared short-spell and missed-boundary safeguards. Optimize official spellF1 while keeping the causal tradeoff visible.
5. **Broaden stresses, then freeze once.** Cover correlated observation failures, not only ball-coordinate erasure. Run the genuinely fresh evaluation once and report negative outcomes in full.
6. **Package the chosen route.** Export a compact runtime and demonstrate clean-room execution/reproduction. Further review seals and coverage improvements should follow this evidence, not substitute for it.

The strongest defense of this project is its candor and its refusal to promote a rejected motion experiment. Preserve both. The strongest competitor attack is that the latest policy remains a sticky asymmetric classifier over provider-derived geometry, with an excellent audit trail but no fresh independent demonstration of full-state football understanding.


---

<a id="agent-5"></a>

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

---

<a id="coordinator"></a>

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


---

<a id="shared-brief"></a>

# Appendix — exact common council brief

# Independent adversarial council audit

## Exact user prompt (shared by all five agents and root)

[https://github.com/hannannoor/messis-foot](https://github.com/hannannoor/messis-foot), so right this is our progress rn can u um audit this but i want u to frame it as if ure a competitor against ours and i want u to try dissect our project as if ure trying to prove why we are worse/not good. so basically u look at our progress and u point out maybe things we did that were bad or things that we tunnel visioned on and couldve done in a different better way. be strict as if ure really really trying to find flaws and as such find improvements that can be made. i want u to use llm council also but each of the agents get this same prompt along with urself so u get a total of 6 different povs when done i want output to contain all 5 agents output + yours, dont condense cuz i wnana keep full context

## Common context and audit rules

- Repository: https://github.com/hannannoor/messis-foot . Latest current progress is open PR #1, branch codex/tactical-validation-and-coverage, pinned commit cee674190775e9356745f461ba1561e9f2a46f7e. Default main is older commit 3a1c8608e050e2f812826719e1af882d87cf2f67. Audit latest progress, distinguish default branch if relevant.
- Verified source root: C:/Users/leonj/Documents/ChatGPT/MESSI's FOOT/ball-gap-publication . All 309 tracked files match GitHub blob hashes at pinned PR commit. Source manifest at ../competitor-audit-2026-11-08/source-manifest.json. Local folders outside this source root contain unpublished work and should not be treated as current repository evidence.
- You are an independent reviewer. Root is producing a sixth independent report. Do not spawn more agents. Do not read other reviewers' outputs, COUNCIL_AUDIT.md, or prior neutral/strategy/code-review audits before forming your own findings. You may use primary progress, rules, experiment methodology, code, tests, reports and benchmark artifacts. No preassigned specialty: choose your own priorities from this same brief.
- Audit only. Do not alter project source, run acquisition/training, modify external systems, or publish anything. Read-only inspection and isolated temporary tests are permitted. Root runs main unittest suite, so avoid duplicating full expensive tests.
- Be strict, adversarial and specific, but distinguish demonstrated bug, evidence-backed limitation, and unverified hypothesis. Do not invent competitor results, hidden-test failures, data, model diversity, or performance. Honor the repo's actual competition rules when proposing alternatives. Existing honest caveats do not invalidate a critique, but acknowledge them fairly.
- Inspect actual code and evidence, not only README. Check objective alignment, strategic tunnel vision, inference validity, inputs/labels/provider leakage, evaluation, generalization, runtime/delivery, reproducibility, and high-return alternatives as relevant. Explain what a competitor could exploit.
- Your full standalone report must include scope and limitations; prioritized findings with severity/confidence, concrete evidence and file:line references; why each matters; a better alternative and test or acceptance criterion; plus a realistic prioritized improvement sequence. Preserve nuance and dissent. Do not pad to manufacture six different opinions. Aim for a thorough report of roughly 1,500-2,500 words if warranted; no summary-only response.
- Write your complete report as UTF-8 Markdown at the output path supplied in your spawn instruction. Use permanent GitHub links pinned to cee674190775e9356745f461ba1561e9f2a46f7e with #L anchors, or absolute local file links. Use numbered headings within the report for readability. It will be included VERBATIM in the full council deliverable, so do not include tool chatter or an abridged substitute. Return the report path and a brief completion note after writing it.


