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


