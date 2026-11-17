# Performance history and the next bounded step

9 November 2026. This source/log review accompanies the frozen release. It makes no new model comparison. **The release addresses delivery and reproduction; its label-parity contract forbids claiming predictive improvement.** The recorded 45/100 competition-readiness grade is subjective, not accuracy. The measured 70.9517% accuracy belongs to the external WCSF match; hidden challenge performance is unknown.

## Work already completed

| Approach | Observed result and decision |
|---|---|
| Camera synchronization/fusion | Zero usable automatic alignment links; no demonstrated added possession evidence. Paused. [Progress](../PROGRESS.md). |
| Frozen tactical tree | Original two-DFL-match mean spell F1 .37361 to .50513. Inactive-coordinate freezing can inflate D; active-only spell quality slightly regressed. [Original evidence](../FOUR_GOALS.md). |
| Motion head and 27 confidence policies | Rejected; later feasibility work showed unreachable gates. This rejects that design, not motion information generally. [Temporal recovery](../TEMPORAL_RECOVERY.md). |
| Remove confidence/direct H/A fill | SkillCorner accuracy 66.40% to 85.33%, but spell F1 .4690 to .4491. More filled/correct frames can worsen possessions. [Ablation](confidence-ablation.md). |
| Two-head agreement | SkillCorner spell F1 .4690 to .4785 on reused evidence; preserves existing wrong decisions and is not independent confidence. [Agreement findings](../ENSEMBLE_FINDINGS.md). |
| Soft three-state sequence, 16 fixed settings | Selected w=0,c=32. Natural seen-regression equal-provider spell F1 .497704 to .564642. More missed changes accompanied fewer spurious cuts. [Results](accuracy-first-results.md). |
| Neutral missing-ball emissions | Current policy. Natural .564642 to .566428; masked .460077 to .491821. Masked SkillCorner false D 57278 to 321, with some per-match regressions. [Results](ball-gap-results.md). |
| Bounded cadence/velocity repair and eight strong comparators | Velocity-only contrast failed per-match D safeguards and produced zero A in sparse cadence cases. Rejected; natural/mask cases had zero active repairs. [Results](cadence-and-baselines-results.md). |
| Frozen WCSF transfer | Control spell F1 .505216 versus fixed w50 .384073 on one previously unused match. No new predictor fitted; WCSF is now permanently used evidence. [Results](wcsf-transfer-results.md). |

These results come from different cohorts/protocols and must not be chained into one overall improvement percentage. Earlier council/adversarial reviews are completed analysis, not extra independent validation datasets. No council or old experiment was repeated for this review.

## The unresolved performance question

WCSF has 411 reference spells and 490 predicted. Its IoU .5 result has 233 matched, 178 missed and 257 spurious spells. Missed D accounts for 33725 of 41587 frame errors, while direct H/A boundary recall is 84/237 within 12 frames. Those counts make both liveness and ownership relevant; they do not identify the cause of lost ranking score. [Sealed aggregates](../reports/wcsf-transfer-v2/results.json), [assessment](official-evaluation-assessment.md).

The four-match ownership pilot found wrong remembered control strongly associated with swaps, but memory and the tree share geometry. It also found decoding corrects more raw decisions than it spoils in aggregate. Team-exchange asymmetry exists without evidence that it explains most errors. The deeper complete-segment path instrument was designed and planned but never implemented. [Observed diagnosis](ownership-council/observed-diagnosis.md), [preserved design](superpowers/specs/2026-11-08-ownership-path-diagnosis-design.md).

## Grounded alternatives

1. **Repair observation/control-memory evidence**, if the fixed diagnostic shows wrong emissions dominate. Test one feature-contract hypothesis; do not revive the rejected velocity-only intervention or bundle several features/refitting/symmetry.
2. **Change one decoder or boundary rule**, if locally reference-favoring evidence consistently loses to switching penalties/future context. Lowering cost without attribution risks replacing missed changes with fragmented spells.
3. **Fit a symmetric ownership head**, if observed interior errors remain and a specific head asymmetry is supported. This is a separate lower-priority hypothesis; symmetry alone does not solve D or hidden changes.

The recommended next goal is an unchanged-control whole-segment diagnosis plus a **separate D/all-state addendum**, after this release's reproduction/public-check gate. Preserve the original four-case scope and approved documents; specify the extra now-used WCSF case separately. Attribute misses, splits and merges at all five official IoUs, separating local/prefix/future emissions, switch costs, source barriers, tied optima and materialization. Reference masks never segment inference.

Stop after the fixed cases and recommend at most one mechanism-supported intervention. Any new outcome on WCSF is development/regression evidence. The challenge public window stays outside this diagnosis and outside all training/selection. A broad grid, another council, camera revival or blind D-threshold relaxation is not the next experiment.
