# Cadence and strong-baseline findings

8 November 2026. **Decision: do not promote the velocity-only candidate. Keep the existing frozen experimental candidate.** The bounded experiment and publication verification are complete; fresh model qualification is not.

## What was actually applied

Implemented and ran one fixed short-gap reacquisition-speed contrast, eight nearest-player/majority comparators, velocity-availability diagnostics, duration-stratified spell recall, pair-typed H/A event diagnostics, exact continuation gates and source/input-bound aggregate reporting. This was applied code and a completed external comparison, not a theory-only exercise.

The contrast kept the old tree and all inference settings: motion weight 0, cost 32, neutral missing emissions and separate materialization. It changed only eligible reacquisition ball_speed and the derived 12-row recent_speed, with a fixed five-row/.20s endpoint-pair bound. Unavailable velocities can still retain legacy zeros. The old 309-file release and previous candidate outputs remain intact; no new target inference or model fitting occurred.

Exactly four previously examined development matches, five regimes and ten variants were scored: 20 cases / 200 completed variant comparisons. DFL J03WOH/J03WOY were fitting matches for the original tactical head. SkillCorner 1874553/1886347 were previously used development cases. These are exploratory results, not independent qualification.

## Control versus the one proposed correction

Spell F1 and frame accuracy below are equal-provider means of unweighted match means. Provider references cover different state support; this is not a challenge accuracy percentage. Retain-k keeps one ball observation every k canonical rows while preserving player inputs.

| Regime | Spell F1 control | Spell F1 contrast | Frame accuracy control | Frame accuracy contrast |
|---|---:|---:|---:|---:|
| natural | 0.613914 | 0.613914 | 90.83% | 90.83% |
| retain-2 | 0.000000 | 0.182286 | 23.51% | 58.02% |
| retain-3 | 0.000000 | 0.167919 | 23.51% | 55.58% |
| retain-5 | 0.000000 | 0.161577 | 23.51% | 53.74% |
| mask30-seed1729 | 0.525525 | 0.525525 | 85.83% | 85.83% |

The synthetic mechanism is repaired: dense input is H180 under both policies, while retain-2/3/5 changes D180 to H180 in the moving-home-ball fixture. External cadence false-D rate on known-live support falls from 100% to 0.9714% averaged under the declared match/provider hierarchy. Cadence mean spell F1 rises from 0 to 0.170594. Those are real improvements in a constructed failure regime, not proof of useful ownership recovery.

**The contrast emits zero A predictions on known reference rows in all twelve cadence cases.** It produces no direct H-to-A or A-to-H predicted events in the supplementary pair-typed diagnostic, despite positive true-event support. D-mediated transitions are a different event type; zero direct events does not prove that the label is constant throughout a half. The speed fix alone fails to restore two-team possession behavior.

Source-level follow-up hypothesis: the unchanged control-memory features require six consecutive near-player support frames. Isolated retain-2/3/5 ball observations cannot satisfy that counter. This establishes another cadence-sensitive feature contract, not independent causal attribution of every measured error. Do not patch that counter against these visible outcomes without a new bounded design.

## The stoppage safeguard correctly blocks advancement

| DFL regime | Control D recall | Contrast D recall |
|---|---:|---:|
| natural | 99.12% | 99.12% |
| retain-2 | 100.00% | 88.70% |
| retain-3 | 100.00% | 78.32% |
| retain-5 | 100.00% | 70.53% |
| mask30-seed1729 | 95.60% | 95.60% |

All seven aggregate checks pass. The per-match veto nevertheless fires: D recall falls on both DFL matches at every artificial stride, by 11.15–32.64 percentage points. The original all-D cadence control trivially has 100% D recall while failing all live rows. Escaping that degenerate control is insufficient: the proposed contrast also fails the required per-match protection. `automatic_continuation_allowed` is false. No default/runtime promotion follows.

## Natural and block-mask parity did not exercise the correction

| Regime | Corrected speed rows, all four matches | Changed rolling-speed rows |
|---|---:|---:|
| natural | 0 | 0 |
| retain-2 | 227,581 | 329,804 |
| retain-3 | 151,589 | 328,980 |
| retain-5 | 90,866 | 327,659 |
| mask30-seed1729 | 0 | 0 |

All eight natural/contiguous-mask cases have zero eligible repairs. Their identical scores are expected and do not test the safety of an active correction on real natural gaps. The .20s mechanism was exercised by the artificial-cadence cases only. The mask samples lengths 5/15/50/125/250, with possible truncation and overlap. No eligible pair was repaired in these four realized mask cases. This observed lack of activity limits what their score parity can establish.

## Every fixed simple comparator is visible

Official-convention uses missing/no-player-to-D and H/A-only majority votes. Matched-input uses current quality barriers and structural carry after no-vote X. Both disclose input-period resets and canonical home-first raw distance ties; upstream raw ties instead follow track-slot order. No window was selected using these results.

| Fixed method | Natural | Retain-2 | Retain-3 | Retain-5 | Block mask |
|---|---:|---:|---:|---:|---:|
| frozen-control | 0.613914 | 0.000000 | 0.000000 | 0.000000 | 0.525525 |
| bounded-reacquisition-speed-v1 | 0.613914 | 0.182286 | 0.167919 | 0.161577 | 0.525525 |
| official-convention-w0 | 0.081468 | 0.000009 | 0.000011 | 0.000011 | 0.054942 |
| official-convention-w25 | 0.323290 | 0.252798 | 0.323697 | 0.236830 | 0.227703 |
| official-convention-w50 | 0.402543 | 0.324265 | 0.341731 | 0.313694 | 0.281406 |
| official-convention-w125 | 0.404471 | 0.376832 | 0.377939 | 0.366658 | 0.332212 |
| matched-input-w0 | 0.089671 | 0.092051 | 0.095088 | 0.102368 | 0.110888 |
| matched-input-w25 | 0.344005 | 0.267116 | 0.343571 | 0.252016 | 0.304028 |
| matched-input-w50 | 0.422214 | 0.338184 | 0.355664 | 0.325987 | 0.347570 |
| matched-input-w125 | 0.409423 | 0.384493 | 0.380097 | 0.369135 | 0.336534 |

The frozen learned route beats all eight simple comparators on natural and block-mask mean spell F1 in this pilot. Conversely, every smoothed simple comparator beats the velocity-only contrast at each artificial stride in equal-provider spell F1. Neither observation ranks unseen challenge performance. The result supports preserving the old natural-input control and using strong simple baselines in every later comparison.

## Review, correction and reproducibility limits

- Original formatter preflight: one control score was computed before report construction incorrectly rejected a nonzero diagnostic truth-X confusion row. No complete case/comparison receipt was saved. V1 freeze, all 100 source files, log and attempt are preserved locally. V2 uses the unchanged official scored_confusion helper. Report 200 completed comparisons plus one aborted formatter invocation: 201 total external variant-scoring invocations, with no model/settings/cohort reselection.
- Independent review reproduced the summary and all case hashes, reconciled the 200 numeric reports and passed 61 focused tests. Its extra synthetic probes checked 1,440 tree rows and upstream baseline parity. No external arrays were rescored by the reviewer.
- The explicit V2 map omitted four executed original wrappers. Both reviewer and author found their current bytes identical to the pinned cee6741 base; the original copy was also hash-verified before implementation. The additive post-review attestation binds their current bytes. It does not retroactively prove every historical transient execution state or make the original explicit map complete.
- The historical receipt validator allowed containers under scalar fields and contradictory null/support metrics. Required publication entry point postrun_cadence_verify.py now rejects exact-shape/type violations, duplicate JSON keys, undefined non-null recall and ratios inconsistent with counts. Historical frozen source and receipts are preserved. This strengthens publication checks without new model scoring.
- Endpoint interpolation/provenance flags were not retained in CadenceRow. Timing-basis counts are marginal and include some rejected pairs; they are not valid-native-velocity or freshness counts. This distinction remains unmet and must be represented explicitly in a future feature contract.
- Only supplementary.HA_boundaries is run-local/pair-typed. Legacy boundary_metrics retains the original destination matching and can match across short reference-X holes. Retain both names and definitions.
- Whole-unknown-period subtype counts can undercount interrupted same-number blocks. Ordinary materialized counts remain valid. A zero subtype is not proof of absent fallback D.
- Historical resume is no-clobber plus final detection of incomplete/wrong-regime stages; it is not a transactional publication guarantee. The stricter publication guard validates the actual raw JSON bytes.
- No fresh full-state reference, target accuracy, physical-control truth, native freshness or raw-to-current-report reconstruction was established. SkillCorner cannot measure positive-D recall. Preserve those limitations alongside any percentage.

Final synthetic/unit verification after the single review fix pass: **406 tests, zero failures/errors, 19 skips (387 executed)**. All 65 newly added focused tests execute. The original 309 blobs still match the base. The additive verifier checks 20 strict receipts / 200 numeric reports and four omitted current wrapper identities; no new external prediction/official-score computation is required.

Reproduction with the preserved licensed external inputs and committed source/evidence:

```text
python cadence_experiment.py verify
python postrun_cadence_verify.py
```

Do not delete the published freeze or relabel a regenerated cache as its original generation. Original archives are not included. A fresh raw rebuild and selected-only export remain separate roadmap tasks.

## Progress grade and next work

Subjective readiness grades: **engineering 7/10; independent performance evidence 3/10; competition readiness 4/10**. These are judgments about maturity, not percentages of target accuracy. We have a tested research pipeline and a reproducible negative/partial experiment; we do not yet have a robust, independently qualified full-match model.

This phase completes two investigation deliverables: isolate/test the cadence mechanism and score the missing strong baseline family. It does not complete an accuracy improvement on natural inputs, a safe new selected candidate, independent H/A/D qualification, the approved whole-path instrument, raw reconstruction or final delivery.

Next goal, only after this experiment is verified and published: bounded independent source qualification from the existing scouts. Then execute the approved frozen-control whole-segment diagnosis. Use that evidence to choose at most one subsequent observation/control-memory, symmetric-head or temporal intervention. The current speed-only candidate receives no automatic regression expansion or target run.

Evidence: [sealed summary](../reports/cadence-v2/summary.json), [original source/input and score verification](../reports/cadence-v2/verification.json), [post-review attestation](../reports/cadence-v2/post-review-attestation.json), [required publication verifier](../postrun_cadence_verify.py), [roadmap](superpowers/specs/2026-11-08-post-audit-roadmap-design.md).
