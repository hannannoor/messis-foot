# Independent runtime and invariant verification

## 1. Scope, method and verdict

Reviewed commit **`cee674190775e9356745f461ba1561e9f2a46f7e`** (latest PR snapshot), with historical checks against `3a1c8608e050e2f812826719e1af882d87cf2f67` (main), `c4643e7d7680284776ad4a3789d920ba489dc408` (first tactical route), `79a467aa93f1e9f4fe996890fefe214db127c255` (temporal research), `9bd11dc847f71973782ea268045609f6a8c6bffd` (input contract) and `b43327c101a8e33cadd5cf4f8a892910bad24c42` (soft decoder). I read the full council report and inspected the published input, geometry, anonymous matching, core, tactical, temporal, sequence, materialization, selected runtime and seal paths and relevant tests. I did not read sibling reviewers' findings, run the audit's probes, execute the full suite, acquire/train, or inspect target tracking/video/GT/predictions. Only committed aggregate input diagnostics were read.

The council's central runtime mechanisms are reproducible. Its strongest claims are structural limitations and synthetic counterexamples, not demonstrated target errors. One additional failure regime deserves higher priority than another decoder grid: **intermittently missing moving-ball samples can manufacture stationary-ball evidence on retained observations, changing the complete selected pipeline from H on all 180 frames to D on all 180 frames.** Neutralizing absent rows does not neutralize this reacquisition effect.

All my executable probes use the standard library and published inference components under `python -B`; TEMP/TMP were workspace-local. Synthetic fixtures, an independently written probe and result JSONs are under `adversarial-review/.tmp/`. No source snapshot was edited. The primary probe is [runtime_verify.py](../.tmp/runtime_verify.py); its completed second run is [results.json](../.tmp/runtime-temp-v2/results.json). Additional targeted results are [extra-results.json](../.tmp/runtime-temp-v2/extra-results.json) and [older-policy-results.json](../.tmp/runtime-temp-v2/older-policy-results.json). These contain synthetic data only.

## 2. Checked-claim classification

| Council claim | Classification | Tested conclusion and practical priority |
|---|---|---|
| Missing rows supply zero H/A/D emissions; there is no duration horizon inside a supported usable segment | **VALID** | Exact policy behavior; a single observed preference extends through 2,501 missing frames. P2 uncertainty/capability issue; ordinary continuity can still be the correct baseline. |
| Neutral opposing-anchor gaps favor H (or A over D) | **VALID** | All six ordered state-pair probes reproduce label-order preference. This is an equal-score boundary convention, distinct from head asymmetry. P2 diagnostic/invariant issue. |
| The complete selected model breaks team-swap equivariance | **VALID** | Direct head plus full EPTS/quality/association/runtime both return H180 after physically exchanging unequal team point sets. P1 bounded model experiment; match prevalence unknown. |
| c32 erases strongly supported short interior bursts | **VALID** | With .90/.05 supports, 22 frames disappear and 23 survive; independent exhaustive path scoring confirms the decoder is optimizing its stated objective. P2 calibration/duration evaluation. |
| Smoothing deletes genuine short football possessions at a demonstrated rate | **PARTLY VALID** | Published missed-boundary counts rise, but support-level synthetic thresholds do not identify which real spells were short or quantify target prevalence. Duration-stratified real evaluation is still needed. |
| Finite stationary/stale coordinates can yield D; provenance does not protect the head | **VALID** | Stationary fixture yields D100; changing freshness/native/interpolation/time flags changes no supports. This demonstrates identifiability/quality limitations, not actual stale target observations. P1 external observation-quality evaluation. |
| The selected route recovers hidden opposing spells or stoppages from missing rows | **UNSUPPORTED** | Selected motion weight is zero. It can carry the correct endpoint owner, but has no ownership emissions inside the gap. The actual release documents this limit rather than claiming universal recovery. |
| A precise label in every neutral row is necessarily a hallucination/error | **OVERSTATED** | A prior-based estimate is not independently observed, but may be correct and useful. Hidden-event absence is not itself evidence that an event occurred. Preserve uncertainty without treating every carried row as a measured failure. |
| Ball-gap masking establishes broad observation robustness | **PARTLY VALID** | It establishes one deleted-coordinate stress result. Stale/false coordinates, joint dropout, fragmented detections and state-dependent missingness remain different regimes. |
| The latest route unnecessarily requires comparator and research artifacts | **VALID** | Whole-runtime execution loads the temporal artifact and four controls; unrelated pinned source/report modifications are rejected. No excessive latency/memory was measured. P2 packaging, after scientific qualification. |
| The tested behavior proves the Viterbi algorithm is broken, source speed units corrupt selected inference, or legacy fixed-D enters the current candidate | **REFUTED** for these inspected paths | Sixty independent exhaustive optimizer checks pass; ATD speed is validated but unused; selected input/runtime path has no tags or fixed-D application. These are guardrails against overreading the audit, not accusations the council actually made. |

## 3. Additional isolated failure: missing samples become false stationarity at reacquisition

**Classification: VALID, demonstrated pipeline vulnerability. Priority P1; high confidence in mechanism, unknown target frequency/score cost.**

Construct 180 frames at 25 Hz. Ball position is `(25 + .08*i, 34)`, a constant 2 m/s path. Home points are `(ball_x+1,34)`, `(10,10)`, `(15,15)`; away points are `(ball_x+10,34)`, `(70,55)`, `(75,60)`. All coordinates remain on the pitch, both teams have three points, homographies are identity with valid flag 1 and reprojection error 1. EPTS declarations deliberately differ from register order, so the complete test also exercises reference-based role resolution.

| Ball observations retained | Component labels | Complete selected EPTS runtime | Final observed support H/A/D |
|---|---|---|---|
| Every frame | H180 | H180 | `.935979 / .056147 / .007873` |
| Every second frame | D180 | D180 | `.318805 / .247357 / .433839` |
| Every third frame | D180 | Not separately run | Same sparse support |
| Every fifth frame | D180 | Not separately run | Same sparse support |

For strides 2/3/5, **every retained observation has `recent_speed == 0`**, even though the retained coordinates visibly move over time. [tactical.py:40–51][tactical-speed] initializes speed to zero, clears `previous_ball` when a row is missing, then appends that zero to the speed history. Thus a reacquisition without an immediately preceding observation is encoded as stationary rather than velocity unknown. The current policy neutralizes missing rows only; the retained rows still accumulate D-favoring scores through [ball_gap_policy.py:14–24][gap-policy]. This combines a feature mismatch with unbounded accumulation of moderate, uncalibrated leaf support.

A narrowly controlled counterfactual changed **only** the two speed features on observed sparse rows to their fixture's known 2 m/s value, leaving all other features and missing-row neutrality unchanged. The same selected decoder returned **H180**, with last observed support `.687875 / .310736 / .001389`. This is causal evidence that the speed encoding is sufficient to produce the demonstrated reversal, rather than merely a correlation with lost control-history flags. It is not a proposed production repair: velocity across a real gap is uncertain and cannot simply be hardcoded or assumed to follow a straight line.

The feature behavior dates to [c4643e7 tactical.py:40–51][old-speed]. The old gated tactical policy on this exact dense/sparse pair returned **H180 / X180**, while the latest soft sequence returns **H180 / D180**. The recent correction therefore fixes missing-row emissions without solving their indirect effect on future observed features; this is not evidence that every historical route had the same false-D output. The current docs acknowledge unchanged first-after-gap/history features, but the council did not isolate this fragmented-observation failure.

**Concrete next work:** preserve this fixture, add irregular and alternating sample patterns to an externally defined corruption matrix, and compare explicit velocity availability/source-time features against the frozen baseline. Report stationary-live false D and genuine-dead recall separately. Retraining or changing feature semantics must be externally selected and frozen; blindly replacing missing speeds or lowering c32 could damage actual stoppage recognition. The demonstrated mechanism warrants a bounded experiment now; a claim of prevalent challenge failure remains unsupported.

## 4. Neutral ties, continuity and materialization are different mechanisms

**Classification: VALID mechanisms; target error interpretation limited.**

I used 100 anchor rows with support `.98` for one state and `.01` for each other state, 1,000 unavailable but usable rows, then 100 opposite anchors. All six ordered pairs were tested. H↔A and H↔D gaps were entirely H; A↔D gaps were entirely A. With H then A the cut was at index 1100; with A then H it was at 100. Missing-row support values were irrelevant because they are replaced with `(0,0,0)`. [soft_sequence.py:38,43][soft-ties] selects earlier state indices in exact predecessor/final ties. Every possible single-switch location inside a neutral gap has the same emissions and transition cost: this shows an arbitrary boundary point estimate, not evidence the physical transition occurred at either end.

This is separate from a unique-preference tactical head returning H after team exchange. Fixing tie placement cannot restore head symmetry. Nor should a symmetric tie convention be advertised as discovering a hidden transition; an uncertainty interval is a more accurate diagnostic.

With one observed `.99/.005/.005` H preference followed by missing rows, lengths 27, 252 and 2502 yielded H everywhere. Rejection applies only to a whole usable segment with no observations at all. Three points per team can satisfy [sequence_usable:6–9][usable], while selected state emissions still contain no player geometry signal on missing rows. That continuity assignment is reasonable when possession actually persists. There is no evidence allowing the selected route to distinguish that world from a completely hidden H→A→H spell.

A full runtime fixture with 100 observed rows, 1,000 missing rows and 100 observed rows produced H1200, `neutral_active_usable_rows=1000`, `latent_unknown_active=0`, `materialized_active=0`. All 1,000 missing rows were explicitly marked neutralized. Consequently latent-X counts are not totals of epistemic uncertainty; the release does expose the separate flag in [ball_gap_runtime.py:61–62][runtime-flags].

Quality barriers work at the latent stage. A direct five-row case returned `HHXXX` with an unusable middle barrier and no later observation. Materialization returned `HHHHH`. In a complete 180-row runtime case, marking homography rows 50–99 invalid created **50 latent X rows**, then **50 H materializations**. Entire unsupported half-periods become D while period-0 stays X (`XX X XX` across `[1,1,0,2,2]` became `DDXDD`). This is precisely [materialization_control.py:8–18][materialize], which resets at structural periods and explicitly labels all-unknown D as a scoring convention. It is not evidence that geometry rejection was bypassed during inference or that a dead-ball detector fired.

**Action:** retain neutralization, latent uncertainty and materialization separately; add anchor age and equally optimal boundary windows. A new horizon or unknown-state policy needs external score comparison. Do not classify every extended neutral interval as an actual error without labels.

## 5. Tactical team asymmetry survives the full current pipeline

**Classification: VALID. Priority P1 for a bounded symmetric-model comparison; no aggregate bias estimate.**

On 180 observed frames, ball `(25+.08*i,34)`, home nearest point 0.5 m away and away nearest point 1 m away, the head's final support was **`.6878752076/.3107362087/.0013885836`**. Exchanging complete home/away point sets gave the identical support at every frame and H180 again. The two distances differ, so this is not a symmetric physical-input tie. I then ran two independently generated six-player EPTS fixtures through `ball_gap_candidate.run_source(..., scope='synthetic')`. Both produced **H180**, zero materializations and contiguous original output indices. Therefore this is not an artifact of skipping the parser, geometry gate or anonymous association.

The head has separate team-distance/control-history features and no enforced exchange symmetry; the selected runtime uses it directly at [ball_gap_runtime.py:40–43][runtime]. Decoder-only unique-optimum swap tests cannot establish end-to-end symmetry. Conversely this counterexample does not identify the true possessor of a synthetic scene or prove every real away-team prediction is disadvantaged.

**Action:** compare symmetrized emissions, symmetric features or exchange augmentation on external development evidence, keeping D unchanged. Require whole-input exchange tests on unique-preference cases, with ambiguous ties assessed separately, and per-team held-out spell results before promotion.

## 6. Short bursts: optimizer verified, prevalence unmeasured

**Classification: VALID support threshold; PARTLY VALID real-event interpretation.**

I independently enumerated all `3**n` paths for 60 random sequences of lengths 1–6 with switch costs 0, .75, 2 or 32. Every returned path attained the independently computed maximum objective. This supports correctness of the Viterbi implementation for these cases; the smoothing critique concerns its selected objective/score scale.

For H100–A(n)–H100, all observed/usable, supports H=`(.90,.05,.05)` and A=`(.05,.90,.05)`, n=10/20/22 disappear and n=23 survives exactly. Two switches cost 64, while each A row provides `log(18)` advantage. With `.99/.005/.005`, 10 disappears and 20 survives. With `.6/.4/0`, 157 disappears and 158 survives. Thus **there is no universal minimum possession duration**: it depends on support ratio, neighbors, position in the segment and number of required switches. Interior and edge events have different thresholds.

The [published tradeoff diagnostics][tradeoffs] report more missed boundaries despite fewer spurious cuts. Those receipts support a real aggregate tradeoff; I did not rescore their excluded arrays. They do not show that all new misses are short spells, nor establish the synthetic 23-frame cutoff as a real-match recall statistic. The [acceptance gate:97–116][gate] indeed lacks a short-spell or missed-boundary veto. Choosing the official objective is valid; additional safeguards should be prospective rather than retroactively selected.

**Action:** evaluate duration-stratified true-spell recall and gap-stratified boundary recall before replacing the constant cost. Compare a small predeclared duration/transition alternative; do not assume added complexity wins or simply lower c32 against seen outcomes.

## 7. Stale finite coordinates, provenance and input compatibility

**Classification: VALID identifiability limitation; dominant target failure UNSUPPORTED.**

One hundred stationary ball frames at `(52.65,34)`, home point 1 m away and away point 10 m away, yielded **D100**, final support `.0572415669/0/.9427584331`. Actual stationary live play, a genuine stoppage and a stale carried ball coordinate can coincide numerically; coordinates alone cannot disambiguate these worlds. Changing all 180 moving-fixture native-detection, interpolation, provenance and sample-time flags left every tactical support and decoded label identical. These fields are retained in records but absent from [the tactical feature schema][feature-schema]. That is a limitation where reliable metadata exists; unavailable target freshness flags cannot be conjured from repetition.

The committed target [aggregate input audit][target-audit] counts only **78 adjacent exact ball repeats**, says freshness is unverified and explicitly denies that repetition proves staleness. That neither establishes dominant stale-ball failure nor rules out held/jittered/delayed coordinates. The finite-stationary probe must not be described as an observed target episode.

The EPTS parser correctly resolved H/A through channel references in my reversed-declaration fixture and rejected noncontiguous indices, partial XY, infinity and malformed speed values. It deliberately validates but does not use source speed; the kph/m/s declaration conflict is therefore not a demonstrated selected-inference speed bug. Coordinates scale to 105.3×68 m while the metadata contract expects 105×68, explicitly reported by [input_contract.py:190–197][input-report]; this is a documented canonical convention, not automatic evidence of a calibration failure. Bounds and role/25 Hz/frame-count specificity limit portability but are reasonable for the named input contract.

Anonymous matching is deterministic mutual unique nearest with a .8 m adjacent-frame bound, resets at period/quality failures and invents new correspondences on ambiguity. My slot-order permutation left associated records unchanged. A crossing example retained spatial-side IDs rather than recovering physical crossing identities, illustrating the explicitly unverified correspondence contract, not a hidden identity guarantee. Selected w0 tactical features do not use those identities; the comparator motion features do. [SkillCorner:163–193][skillcorner] really does interpolate players using provider IDs before anonymous association, so anonymous compatibility is narrower than raw-anonymous equivalence. It is not direct reference-label leakage.

## 8. Runtime guards, historical routes and delivery

**Classification: VALID coupling; no broken current runtime shown. Priority P2.**

A clean copied selection/source/evidence set passed `selected_artifact()`. Appending a newline separately to the copied runtime, policy, summary receipt or even `gap_solver/multicam.py` caused `ValueError: Consumed source/input identity changed`. These probes changed only disposable copies under `.tmp`. [ball_gap_candidate.py:12–17][selected] pins the selected ID, model/settings, sources and evidence. Current runtime runs that validation again before publication and checks input hashes. Reusing a populated output folder was rejected, preserving the prior generation. Relevant late-arrival/publication and source-seal tests are present; I did not claim to have exhaustively adversarially tested every filesystem race.

The coupling criticism is concrete: selected w0 inference still loads the temporal artifact, computes four controls and requires unrelated historical research source/evidence identities. This can block selected inference after changes that do not mathematically affect it. The successful complete synthetic runs show the **published clean checkout does work**; coupling is not proof it presently requires unpublished raw arrays for inference. Exact external score replay is a separate, more demanding operation.

The old temporal decoder is a two-state forward/backward posterior with hard incumbent anchors, not the latest three-state Viterbi. It can express hidden opposing states in principle, but has eligibility/quality/gap barriers and its trained candidate was rejected. [temporal.py:184–245][temporal] and [temporal_protocol.py:18–41][temporal-seal] preserve this distinction. Treating the current w0 missing policy as use of the rejected motion head would be incorrect.

History matters: main `3a1c860` predates the tactical/input/soft/ball-gap generations. Its core control and multicam inference differ little from current beyond later routes/diagnostics; after ignoring line-ending noise, core inference itself is unchanged. The legacy multicam path admits alignment/tag/shared-dead context only through its explicit route. Current ball-gap input construction supplies geometry only and invokes no fixed-D or tag application. [README:5,9,23–50,72–74][readme] explicitly distinguishes the current experimental candidate, preserved single-file tactical route and legacy history. There is a real multi-command handoff cost, but “the release silently runs the wrong candidate” is stronger than the documentation supports.

**Action:** after scientific qualification, export one explicitly named selected-only runtime with parity checks, keeping optional comparators and scientific evidence verification available. Measure time/memory before claiming material runtime cost. Preserve current guards and history rather than deleting provenance to simplify delivery.

## 9. Concrete order of work

1. **First bounded engineering experiment:** address fragmented-sample/reacquisition features with explicit velocity availability and source timing, preserving the frozen baseline and testing stationary-live/dead strata externally. This is a demonstrated missingness-induced mechanism that the existing block mask does not adequately isolate.
2. **In the same development protocol:** compare a team-symmetric head/emission construction; add complete-input exchange tests and neutral-boundary uncertainty diagnostics. Keep ties distinct from asymmetric unique preferences.
3. **Before any broad accuracy claim:** obtain independent full-state evidence and run a predeclared corruption matrix, including fragmented samples, stale finite coordinates, correlated player loss and hidden changes; report short-spell and boundary recall alongside official spell F1. No synthetic fixture alone resolves generalization.
4. **Then compare temporal alternatives and package the winner.** Keep continuity/carry as serious baselines. Qualification, packaging and evidence portability answer different questions; a cleaner executable does not validate unseen accuracy, and more seals do not repair the observation model.

[tactical-speed]: https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/gap_solver/tactical.py#L40-L51
[old-speed]: https://github.com/hannannoor/messis-foot/blob/c4643e7d7680284776ad4a3789d920ba489dc408/gap_solver/tactical.py#L40-L51
[gap-policy]: https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/ball_gap_policy.py#L14-L24
[soft-ties]: https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/gap_solver/soft_sequence.py#L38-L44
[usable]: https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/gap_solver/soft_sequence.py#L6-L9
[runtime]: https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/ball_gap_runtime.py#L38-L43
[runtime-flags]: https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/ball_gap_runtime.py#L61-L62
[materialize]: https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/gap_solver/materialization_control.py#L8-L18
[tradeoffs]: https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/docs/ball-gap-results.md#L30-L40
[gate]: https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/ball_gap_experiment.py#L97-L116
[feature-schema]: https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/gap_solver/tactical.py#L11-L14
[target-audit]: https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/reports/input-contract/tactical-audit.json#L26-L45
[input-report]: https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/gap_solver/input_contract.py#L190-L197
[skillcorner]: https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/gap_solver/skillcorner.py#L163-L193
[selected]: https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/ball_gap_candidate.py#L12-L17
[temporal]: https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/gap_solver/temporal.py#L184-L245
[temporal-seal]: https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/gap_solver/temporal_protocol.py#L18-L41
[readme]: https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/README.md#L23-L50
