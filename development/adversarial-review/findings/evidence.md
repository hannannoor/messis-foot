# Independent verification: evaluation, history and comparators

Reviewed 8 November 2026. This report validates claims in the complete six-reviewer adversarial audit against primary code, committed aggregate receipts and reachable Git history. It does not treat agreement among reviewers as empirical confirmation.

The audit's central scientific criticism survives: the latest candidate has useful measured improvements on already used provider references, but no fresh full-state transfer result. Several stronger interpretations do not survive. The natural incremental gain is conditionally positive, the project has already evaluated simple alternatives and multiple corruptions, and uncertainty analysis predates the council. The missing official baseline family is a specific remaining comparison, not an absence of baseline research.

## Scope and evidence standard

The current source is cee674190775e9356745f461ba1561e9f2a46f7e, under snapshots/current-cee6741. I read the complete FULL-COUNCIL-AUDIT.md, examined evaluation/adaptation/acquisition/selection/training sources, relevant tests and primary experiment documents, and searched all 21 reachable commits in mirror.git. Git history confirms main at 3a1c860 has 38 files; c4643e7 introduces the external tactical benchmark, 79a467a the temporal experiment, 0cbf415 the feasibility/ungated work, 1d723cb ensembles/carry, 9bd11dc the input-contract candidate, b43327c soft sequence selection, and cee6741 missing-ball neutralization. The f426c0e audit head changes nine audit/evidence documents only relative to cee6741.

I independently aggregated the 20 current regression receipts, checked their declared denominators, and calculated the old model's confidence ceilings and an exact empirical paired bootstrap using small trusted arithmetic scripts. I did not execute acquisition, training, root-probes, or the full suite, and did not inspect target assets, GT, video, prediction CSVs, or frame-level derivatives. Root is independently handling fresh external-cache score recomputation and the suite; numbers here are receipt checks unless explicitly identified as independent arithmetic. No other verification reviewer's findings or unpublished sibling research were read.

All repository links below are pinned to cee6741 unless a historical commit is named. File:line references identify evidence, not merely a report repeating the claim. VALID means the stated, bounded claim is supported; PARTLY VALID or OVERSTATED marks an important scope correction; REFUTED denotes contrary primary evidence; UNSUPPORTED means the inspected evidence cannot decide it. Priorities apply to the next change, not to a security incident.

## Claim dispositions

| Material audit claim | Disposition | Consequence |
| --- | --- | --- |
| Three seen validation matches and ten seen regressions; adaptive reuse prevents a fresh-generalization claim | VALID, with “exhausted” rhetoric OVERSTATED | P1 scientific limitation, not detected label leakage |
| Latest natural equal-provider spellF1 gain is about .001786; masked gain is much larger | VALID | Preserve both regimes and their distinct questions |
| Small gain is unestablished or mere noise because below the official .04 band | REFUTED as a numerical inference | Conditional paired evidence is positive; freshness remains unresolved |
| No historical uncertainty evidence / no baseline or corruption work | REFUTED if interpreted project-wide | Several such experiments already exist |
| SkillCorner cannot independently validate D recall; DFL geometry may encode provider state conventions | VALID | P1 transfer limitation |
| The selected model is proven to be recognizing only a provider habit, or that this dominates target errors | UNSUPPORTED | No causal attribution or target error prevalence was measured |
| Original gated 27-policy temporal grid could never emit a new label | VALID | Historical architectural error, already diagnosed and guarded |
| Rejecting that grid proves player motion is useless | REFUTED | Ungated outputs are nontrivial; current zero weight is a bounded selection result |
| Current controls are related ablations; a scored external official nearest-player/majority family is missing | VALID | P2 comparator gap |
| Smoothing increases missed boundaries and can erase strongly supported short synthetic islands | VALID | P2 measurable tradeoff |
| Current real-data extra misses are specifically erased short/hidden possessions | PARTLY VALID / unmeasured duration and mechanism | Add duration/gap strata before that claim |
| One-seed ball deletion does not establish general observation robustness | VALID for the current experiment | Reuse existing corruption drivers for the current winner |
| Provider identities assist SkillCorner interpolation before anonymous association | VALID | Transfer limitation, not direct label leakage |
| Exact current report replay needs excluded local caches/score archives | VALID | P2 evidence portability limit; target inference does not need them |
| Current selected route uses a hard-coded pre-kickoff D interval | REFUTED | Distinguish historical manual shortcut from learned stationarity cue |
| A rival is better, the candidate fails hidden challenge accuracy, or more complex alternatives will win | UNSUPPORTED | Proposed experiments cannot be reported as measured rankings |

## 1. What is actually selected, scored and reused

The current cohort counts and provider weighting are correct. [gap_solver/accuracy_protocol.py:7–12](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/gap_solver/accuracy_protocol.py#L7) declares the 16 combinations: motion weights 0/.25/.5/1 and switch costs 0/2/8/32. Validation comprises DFL J03WQQ and SkillCorner 2006229/2006363. Regression comprises DFL J03WR9/J03WN1 and the eight listed SkillCorner matches. The selector at lines 43–62 uses natural inputs only, equal provider means, then macroF1, lower weight and lower switch cost. The one DFL validation match supplies half the objective; each SkillCorner match supplies one quarter. This is deliberate balancing, not a calculation error.

[reports/accuracy-first/selection.json:2–8](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/reports/accuracy-first/selection.json#L2) confirms w0-c32 at .627686162578772 against agreement-plus-carry .5271837892836487. [accuracy_experiment_frozen.py:162–185](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/accuracy_experiment_frozen.py#L162) scores the full grid only during validation and only the selected setting during regression. The later ball-gap experiment is one fixed policy rather than another 16-setting search: [ball_gap_experiment.py:119–124](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/ball_gap_experiment.py#L119).

The history establishes real reuse, not merely the possibility of it. c4643e7 already used the same DFL validation/test identities; 79a467a already evaluated the same SkillCorner validation/eight-test identities; confidence removal, ensembles and carry followed in 0cbf415/1d723cb. The current protocol explicitly labels them seen regressions and marks fresh_holdout false. Both heads' fitting partitions are distinct from those named current validation/regression matches: tactical training identities are in [gap_solver/tactical_model.py:180–186](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/gap_solver/tactical_model.py#L180), and the SkillCorner split is [benchmark/skillcorner/protocol.json:8–36](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/benchmark/skillcorner/protocol.json#L8).

Therefore the audit is VALID about adaptive project-level reuse. It has not demonstrated ordinary train/test row leakage or quantified the selection optimism. Calling the data “exhausted” is OVERSTATED if it means they no longer provide repair/regression evidence. They remain useful for that purpose and cannot regain unopened-holdout status. The current project already makes this distinction in [docs/accuracy-first-method.md:7–18](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/docs/accuracy-first-method.md#L7); the audit does not discover a concealed promotion.

Practical priority P1: retain the current cohort for development, freeze the next comparison before opening genuinely unused full-state references, and record every use in an evaluation ledger. This is a scientific evidence change. Another source seal or renaming the old test set cannot substitute for it.

## 2. Independent numerical check of the latest claim

I recalculated each provider mean directly from the ten match receipts per regime, rather than copying the results prose. The current table is accurate:

| Provider/regime | Frame accuracy, old → neutral | Official spellF1, old → neutral |
| --- | ---: | ---: |
| DFL natural, two matches | .9282788362 → .9282788362 | .5536652410 → .5536652410 |
| SkillCorner natural, eight matches | .8581605630 → .8593019025 | .5756191919 → .5791917292 |
| DFL masked | .8440427648 → .8746404949 | .4326835270 → .4411536992 |
| SkillCorner masked | .7577827285 → .8226657406 | .4874708919 → .5424885809 |

The independent equal-provider arithmetic is natural .5646422164308913 → .5664284850907569, delta +.0017862686598655725; masked .4600772094379824 → .4918211400542425, delta +.0317439306162602. [reports/ball-gap/summary.json:248–328](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/reports/ball-gap/summary.json#L248) and [lines 348–430](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/reports/ball-gap/summary.json#L348) agree with receipt aggregation. These are unweighted match means within each provider, not pooled frame fractions or challenge accuracy.

The D metrics also check out:

- SkillCorner masked has 612,173 known-live frames and no positive D reference. False D is 57,278 → 321, pooled 9.3565054% → .0524362%; the mean of match false-D fractions is 9.3670761% → .0545994%. Natural false D is 2,557 → 72. Pooled and match-average percentages answer different questions.
- DFL masked has 153,693 live and 134,678 D frames. False D is 14,183 → 6,573; missed D is 9,981 → 5,809. Mean per-match D recall is .9264202266 → .9571641204 and supplementary D-interval F1 .6732358059 → .8756273542.
- Agreement-plus-carry has fewer masked DFL false D, 4,987, but more missed D, 20,288. The new result is not merely suppression of all D predictions.

The implementation computes explicit live/dead denominators at [ball_gap_experiment.py:60–82](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/ball_gap_experiment.py#L60). Null recall when no D reference is appropriately distinct from perfect D recall; relevant tests are tests/test_ball_gap_experiment.py:29–44.

The acceptance description is also accurate: lines 97–116 check exactly seven aggregate conditions in each stage. There is no hidden per-match veto, short-spell gate or macroF1 safeguard. All seven true does not mean seven independent replications. SkillCorner natural macroF1 actually declines .5716681314 → .5712613010. J03WN1 masked spellF1 declines .0099794302 despite aggregate success; [reports/ball-gap/post-review-diagnostics.json:117–124](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/reports/ball-gap/post-review-diagnostics.json#L117) identifies that case.

The latest natural gain is small but valid as an incremental result. Against the earlier agreement-plus-carry route, the latest natural equal-provider difference is about +.0687247, not only +.0017863. The audit usually names its w0-c32 comparator correctly; using the small final increment to erase the earlier improvement would be OVERSTATED.

Minimal P2 change: add the paired provider/match delta table and uncertainty to the standard aggregate summary, keeping exact comparator, provider weighting, regime and seen-data status attached to every headline.

## 3. Bootstrap interpretation: the positive conditional result is real

The council's conditional interpretation is VALID. The exact 20,000-draw endpoints cannot be reconstructed from “seed 1729” alone without the RNG and draw ordering. Independent Monte Carlo implementations produce slightly different endpoints, all positive. More decisively, I enumerated all 6,435 count compositions of eight resampled SkillCorner matches, weighted by their multinomial counts, covering all 16,777,216 ordered empirical bootstrap outcomes. DFL contributes zero delta for either sampled match. For the same equal-provider statistic, exact inverse-CDF .025/.975 quantiles are:

**[+.0004760517173494558, +.0032891634823429064].**

The empirical bootstrap mass at or below zero is .00135725736618042. This is consistent with the council's approximate [+.00048952, +.00328566], and supports a positive conditional mean improvement. It is not a generalization guarantee or a post-selection-corrected p-value. Resampling these matches cannot invent new teams, providers or the missing full-state SkillCorner labels. The two DFL zero changes make this interval effectively a scaled eight-match SkillCorner interval.

The official .04 spell noise band is illustrative within-match uncertainty from the reference setting, not a universal rejection threshold for a paired mean across external matches. [gap_solver/official_metrics.py:64–75](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/gap_solver/official_metrics.py#L64) describes its setting. Claims that this increment is “just noise” merely because it is below .04 are REFUTED by the statistic being tested and by the paired arithmetic.

Historical uncertainty evidence also exists. [evaluate_final_external.py:24–33 and 68–77](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/evaluate_final_external.py#L24), present in c4643e7, turns on 1,000 official draws for natural original DFL final evaluations. [gap_solver/temporal_acceptance.py:10–18](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/gap_solver/temporal_acceptance.py#L10), present in 79a467a, uses 10,000 paired match draws and a .025 lower quantile. Its all-zero temporal change produced a vacuous zero bound, exactly disclosed in TEMPORAL_RECOVERY.md:25.

The narrower audit statement that gap_solver/benchmark.py:37 disables the official bootstrap by default is correct; a project-wide “no uncertainty evidence” interpretation is REFUTED. Official single-submission segment/spell bootstraps and a paired match bootstrap are also different estimands. P2 minimum: publish the exact resampling unit, estimator, RNG implementation, interval definition and selection caveat with the current result.

## 4. Provider reference validity and the two different D shortcuts

The provider-scope criticism is VALID. The strict DFL adapter at [gap_solver/external.py:42–47](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/gap_solver/external.py#L42) maps status 0 to D, active status 1 plus possession 1/2 to H/A, and everything else to X. It does not manufacture away labels from unknown possession. Geometry and reference are extracted separately at lines 93–102 and 127–163. ExternalMatch.frames at lines 25–30 exposes geometry, not status or ownership labels. The independent [floodlight DFL reader](https://floodlight.readthedocs.io/en/latest/_modules/floodlight/io/dfl.html#read_position_data_xml) corroborates home/away codes 1/2 and dead/alive 0/1. This validates adapter semantics; it does not establish an independently adjudicated possession gold standard.

SkillCorner's provider documentation says phases exist only in play: benchmark/skillcorner/SOURCE_README.md:128–134. [gap_solver/skillcorner.py:113–154](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/gap_solver/skillcorner.py#L113) initializes reference X, assigns only H/A, quarantines clock/period/conflicting annotations, and never infers D from annotation absence. Phase fields are separate from feature records. tests/test_skillcorner.py:66–96 changes/removes phases and checks invariant nontrivial predictions; tests/test_external.py:50–55 changes target fields without changing geometry. These are appropriate safeguards against direct leakage, not proof that provider labels match every challenge ontology.

The audit correctly says low false D on SkillCorner cannot validate missed genuine stoppages there. A second provider with H/A-only truth cannot repair that gap by averaging with DFL D recall. Priority P1: obtain an independently unused full H/A/D reference, or keep live/dead transfer explicitly unqualified. A request for new data is reasonable but has real acquisition/rights constraints; docs/fresh-had-cohort-scout.md:3–5 and 50–54 records that a candidate cohort was sought and none established. The project did not simply forget to look.

The learned coordinate cue is a separate issue from the hard-coded pre-kickoff interval. [FOUR_GOALS.md:5](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/FOUR_GOALS.md#L5) reports 449,536/449,539 repeated inactive coordinates, versus 4,534/553,105 active repeats. Independent arithmetic gives 99.99933265% and .819736% respectively. I checked the aggregate statement, feature code and model, not those excluded raw rows. The root split at tactical_model.py:84–119 uses recent_speed with threshold about .010414918. [gap_solver/tactical.py:39–63](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/gap_solver/tactical.py#L39) derives speed/history from finite XY and appends zero speed on missing rows. The current neutralizer removes missing-row emissions, not finite stationary-coordinate emissions.

This establishes a plausible, concrete provider shortcut vulnerability. It does not causally measure how much DFL score comes from an artifact instead of physically informative stationarity, and a stationary synthetic ball near a player has no supplied live/dead truth. “Can exploit the convention” is supported; “only recognizes the provider habit” or “dominant target failure” is UNSUPPORTED. The audit's opening qualification largely respects that distinction.

The historical fixed-D path remains in gap_solver/io.py:16–24, and core.py:94–97 consumes supplied dead evidence. Current geometry-only head preparation rejects dead/tag inputs at accuracy_experiment_frozen.py:34–35. [ball_gap_runtime.py:36–49](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/ball_gap_runtime.py#L36) uses the input-contract route and reports no published interval applied. Calling the latest candidate's stationarity cue the hard-coded interval is REFUTED. No competition-rule conclusion follows from their shared D output.

Minimum P2 experiment: score current and a fixed simple live/dead comparator on externally defined stationary-live, moving-dead and stale-finite corruptions, with natural full-state results alongside them. Do not turn every repeated coordinate into missing data or select a target freshness threshold from these concerns.

## 5. The 27-policy failure is valid history, already understood

The rejection and feasibility explanation are independently supported. select_temporal_recovery.py:24–25 defines confidence .90/.95/.975, caps 2/5/10 seconds and switch multipliers .5/1/2. Training at lines 117–159 uses only development matches, calibration only its two named matches, a 40-tree depth-two boosted model, and symmetric swap/reflection augmentation. TEMPORAL_RECOVERY.md correctly calls the 357,964 rows augmented external rows, not independent matches.

From the committed draft's leaf extrema I independently calculated:

B = learning_rate × sum(leaf_max − leaf_min)/2 = 2.8585186401957086.

For each unknown row, both neighboring finite transition messages contribute at most the switch cost to posterior log odds. With cost 6.359277542576393, the committed temperatures yield these maximum confidence ceilings:

| Switch multiplier | Temperature | Confidence ceiling |
| ---: | ---: | ---: |
| .5 | 4.2070878556482265 | .8994398253371932 |
| 1 | 8.311621768838762 | .8669356246195414 |
| 2 | 16.116567947647578 | .852668508055076 |

The parameters are at benchmark/skillcorner/trained-draft.json:1930–1934. All are below the grid's minimum .90 regardless of the gap cap. The decoder's finite-message/clipping structure is at gap_solver/temporal.py:184–229. Therefore all 27 policies were structurally unable to add labels, rather than merely unlucky on the scored matches.

[benchmark/skillcorner/reports/final-summary.json:4–83](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/benchmark/skillcorner/reports/final-summary.json#L4) confirms rejection before final test, eight zero paired changes, mean .4689993446 before/after, and local_inference_authorized false. The current code has a conservative floating-point-aware feasibility implementation at gap_solver/temporal_feasibility.py:45–116, added in 0cbf415; tests/test_temporal_feasibility.py includes independent tiny-path enumeration, two hard neighbors, clipping, cancellation, malformed inputs and published-artifact checks. It is not automatically wired into the deliberately preserved old selector (docs/confidence-feasibility.md:5).

This was a genuine historical design error. Treating its existence as an unresolved flaw in the current ball-gap policy is OVERSTATED: that policy uses no confidence threshold or selected motion contribution. Conversely, rejection does not prove that player motion is useless. The source-only bound disproves the gate, not feature information. Ungated variants were subsequently evaluated, rather than merely proposed. P2 minimum for the next experiment: make feasibility a required preflight for every declared grid and decline impossible policies before match scoring; preserve the failed experiment instead of rewriting it.

## 6. Comparator coverage: a specific missing family, not no alternatives

The current four controls are indeed related: [accuracy_experiment_frozen.py:48–57](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/accuracy_experiment_frozen.py#L48) builds incumbent frozen tactical, its carry, two-head agreement on X, and agreement-plus-carry. The soft variants retain the raw tactical head. [run_external_baseline.py:18–25](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/run_external_baseline.py#L18) calls conservative core.infer, rather than the official baseline. core.py:54–64 requires observed ball, both distances, nearest distance ≤2m and margin ≥.75m, then confirmation/bridging. That is a real nonlearned geometric comparator but differs materially from unconditional nearest-player majority smoothing.

I fetched the pinned primary [official baseline source](https://github.com/metrica-sports/more-than-a-hack-2027/blob/f8f2629ff1e0985f81d7e59d8413678514ee1530/starter/baseline.py). It chooses the nearest tracked player's team when ball/player evidence exists, otherwise D; centered smoothing counts H/A votes and outputs D only when the window has no team vote. The declared half-widths are 0,25,50,125, meaning centered windows up to 1,51,101,251 frames, with ties H. It is not a generic three-class majority filter. The pinned [official evaluation document](https://github.com/metrica-sports/more-than-a-hack-2027/blob/f8f2629ff1e0985f81d7e59d8413678514ee1530/EVALUATION.md) reports this family on its own challenge reference, not on these external cohorts.

I searched source across all 21 reachable commits for majority/official variant names and alternative rolling/convolution/filter implementations, inspected baseline/selection/evaluation sources and report families, and found no scored external equivalent of that official family. The narrow council comparator finding is VALID. Nothing in this verification establishes that it would beat the current head. Comparing its published challenge .2433 directly with the project's external .5664 would be invalid.

The historical baseline record is much broader than four ablations:

- c4643e7: conservative geometry versus selected tactical head, plus natural and .10/.30/.50 ball-mask conditions.
- 79a467a: matched-budget endpoint/last-owner comparisons; independently scored last-owner and two-sided rules at 2/5/10 seconds; no-decoder ablations. select_temporal_recovery.py:171–234 implements them. benchmark/skillcorner/reports/validation-selection.json contains six simple-alternative dispositions.
- Best simple last-owner 5s mean spellF1 is .4918361948 versus .4910957469 baseline, but new H/A agreement is about75.04%/68.02% and the declared recovery/support safeguards fail. The matched-budget temporal endpoint comparison had zero budget because the gated candidate added zero labels; that specific comparison is vacuous, unlike the independently run full rules.
- 0cbf415: confidence off with the same support, direct temporal H/A fill, and raw older H/A/D head, documented in docs/confidence-ablation.md:9–48.
- 1d723cb: raw fallback, agreement, guarded agreement and explicit zero-X carry controls; docs/materialization-control.md:11–27 shows carry-only spell parity on all seven DFL matches and non-parity with SkillCorner reference holes.

Thus any project-wide assertion “simple carry/endpoint baselines have not been tried” is REFUTED. The useful P2 minimal change is a small, externally selected official-family comparison on exactly the current input timing, masking, periods and scorer, retaining the original baseline's D behavior as an explicit variant. Add a stronger simple state rule separately if desired. Do not rerun rejected endpoint experiments as if they were new discoveries.

## 7. Robustness coverage and the limits of the current stress

The one-seed claim is VALID for the latest experiment. [gap_solver/temporal_selection.py:37–49](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/gap_solver/temporal_selection.py#L37) chooses active starts and lengths5/15/50/125/250, targeting30% of active rows; the latest protocol uses seed1729. Starts and masks depend on periods, not reference labels. Overlap can create runs longer than250 frames, and a fallback fills remaining mask count; ten seconds is not a hard maximum outage. This is ball-coordinate deletion, not a validated sensor-failure model.

The “not tested” wording needs historical scope. c4643e7's original final evaluation already used .10/.30/.50 masking, and FOUR_GOALS.md:62 records a whole-team-distance dropout diagnostic. 79a467a's [evaluate_temporal_final.py:104–134](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/evaluate_temporal_final.py#L104) explicitly runs opponent loss, identity discontinuity, mirrored false ball every100 frames, and a three-frame ball shift on both validation matches. Final-summary completion records two stress matches and two available-position ablations. These tests exist in source, history and receipts.

Those earlier temporal non-regressions are vacuous evidence for new recovery because that candidate was inactive. They also are not current-winner tests. A broad claim that the project never considered false observations/player loss/identity discontinuity is REFUTED; the narrower request to evaluate the selected neutralized winner under those conditions remains VALID.

SkillCorner identity-assisted interpolation is confirmed at [gap_solver/skillcorner.py:155–193](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/gap_solver/skillcorner.py#L155). Player interpolation intersects provider IDs at consecutive native observations before anonymous correspondence. It does not cross missing native detections, and isolated samples can snap≤.02s onto the25Hz grid. This advantage survives removing IDs later. It is a realistic transfer caveat, not proof of reference-label leakage. Resampling increases scored time-grid rows, not independent observations.

P2 minimum: reuse the existing four mechanism stresses for the current selected policy, add stale-finite and joint dropout conditions plus several fixed masks, and report worst-match/provider deltas. Keep natural results separate. Multiple seeds alone will not cure provider/ontology mismatch.

## 8. Boundary losses: measured, but real short-spell attribution remains open

Independent receipt sums reproduce every quoted25-frame boundary count:

| Provider/regime | Missed boundaries, old → neutral | Spurious boundaries, old → neutral | Mean boundary F1, old → neutral |
| --- | ---: | ---: | ---: |
| SkillCorner natural | 752 →758 | 1424 →1355 | .3436034 →.3478662 |
| SkillCorner masked | 921 →953 | 1812 →1043 | .2267681 →.2700940 |
| DFL masked | 632 →645 | 483 →271 | .4381024 →.4796395 |

The current source penalty is exactly32 per state change, [gap_solver/soft_sequence.py:24–44](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/gap_solver/soft_sequence.py#L24). An interior opposing island needs64 cumulative log-support advantage. At .90 versus .05 support,64/log18=22.14 frames, supporting the audit's synthetic20/22 erased versus23 preserved mechanism. Leaf supports are expressly uncalibrated at tactical_model.py:188. This is an intentional score tradeoff, not a Viterbi implementation error. Summing these scores is not itself a claim that video frames are statistically independent.

The original w0-c32 versus agreement-plus-carry boundary tradeoff is also documented and numerically consistent in docs/accuracy-first-results.md:59: DFL missed387→483 and spurious399→242; SkillCorner missed623→752 and spurious2332→1424.

However, aggregate missed-boundary counts do not identify duration or cause. A newly unmatched event can be shifted beyond tolerance, deleted, merged or affected by adjacent changes. The counts do not prove that current real-data losses are specifically short possessions or hidden turnovers. The synthetic proof is narrower and should stay separate. Matched-boundary latency is conditioned on matching, so lower latency cannot offset a missed event.

Priority P2: add externally defined duration/gap/transition-type strata and raw missed-event counts, then predeclare a justified secondary safeguard for a new evaluation. A duration-aware decoder is a proposed comparison, not a proven remedy; changing gates after the current result would not improve its evidential status.

## 9. Continuity, materialization and reproducibility

The scientific missing-information criticism is VALID from source. [ball_gap_policy.py:14–24](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/ball_gap_policy.py#L14) zeroes the full missing-ball emission triple and excludes only wholly unobserved usable segments. It places no internal-gap horizon. sequence_usable at soft_sequence.py:6–9 permits three players per side to sustain eligibility, but the selected zero-motion emissions cannot distinguish ownership or D there. Same-endpoint continuity and tied opposite-endpoint boundaries are prior assignments, not observations of hidden events. This is an inherent information limit, not a newly proven football error.

The source has a separate neutralized flag and does not pretend latent X is all uncertainty: ball_gap_runtime.py:52–62. gap_solver/materialization_control.py:10–18 fills by structural period and sets a wholly unknown period to D as a convention. It is important not to equate this with official fill, which uses GT-valid runs and leaves wholly X runs unchanged; benchmark.py:21–37 inserts26 evaluation-only X frames between periods. Existing carry tests and docs explicitly cover reference-hole counterexamples.

The local60321neutral/8059materialized counts quoted in the audit are permitted aggregate execution diagnostics, not observed errors. The full-period D fallback is possible by code but the current local reproducibility document reports zero such fallback rows. A hypothetical all-X fixture must not be presented as a demonstrated target interval.

Exact current evidence replay depends on the original local external arrays and score archives: [docs/ball-gap-results.md:44–66](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/docs/ball-gap-results.md#L44). Sources/hashes authenticate available bytes but do not provide absent NPZ archives. This criticism is VALID. It is narrower than “there is no reproducibility recipe”: benchmark/README.md:9–32 and benchmark/skillcorner/README.md:7–45 already provide licensed acquisition/preparation/frozen-evaluation commands. Latest exact replay has additional preserved-archive dependencies. ball_gap_runtime.py:38–43 also loads the temporal artifact and computes four controls even though selected motion weight is zero; that is coupling, not measured excessive latency.

P2 minimum: provide a portable raw-to-current-score rebuild mode with logical input identities and publish all aggregate outputs needed to compare regenerated scientific results, while retaining the exact-byte archival verifier. Export selected-only inference separately and verify output parity. No fresh raw acquisition or current target run was performed for this verification.

## Prioritized changes supported by this verification

1. P1 scientific evidence: freeze one next candidate and comparator protocol before opening genuinely unused, licensed full-state references. If unavailable, retain the explicit exploratory ceiling; do not label existing matches fresh.
2. P2 comparator: evaluate the exact official nearest-player/centered-majority family externally on the current grids and corruption conditions. Keep its limitations and D convention visible. There is no basis yet to predict which model wins.
3. P2 reporting: add paired provider/match deltas and a completely specified conditional interval, plus duration/gap/transition-type strata. The verified natural gain should remain visible alongside its reuse caveat.
4. P2 robustness: run the current winner through existing mechanism drivers, adding stale finite observations, joint loss and fixed multi-seed regimes. Preserve negative results and distinguish natural from synthetic evidence.
5. P2 experiment design: require feasibility checks for future gated searches; avoid rediscovering the preserved27-policy failure or treating it as evidence against all motion models.
6. P2 portability: add a clean current external rebuild path and selected-only package. Preserve archival verification and baseline generations without requiring their optional computations for selected inference.

The audit is strongest when it names these specific evidence gaps and tradeoffs. It becomes unreliable when read as proof of a superior rival, hidden-target failure, absent historical experiments, or a zero true incremental gain. None of those stronger conclusions follows from the checked record.
