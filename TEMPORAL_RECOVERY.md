# Independent-provider motion experiment

6 November2026. This is a research result; the existing Desktop tactical output and default policy are preserved.

The independent-provider development check found that the old model reduced unknown output considerably without a corresponding large improvement in team spells. Across eight SkillCorner development matches, mean known-play spellF1 moved from0.524729 to0.527643 while mean unknown fraction fell from48.9788% to23.0074%. These are provider-reference, known-in-play results. They do not measure challenge accuracy or independent stoppage recognition.

The next candidate used player geometry even when the ball was missing: team positions/counts, shape, motion, continuity and both-sided control anchors. Forty depth-two boosted trees were fitted to357964 augmented external rows, with separate calibration matches. Team swaps/reflections were augmented and portable scores explicitly symmetrized. Input masking removes ball coordinates and derived distances before feature extraction. Prediction has no phase labels or event outcomes, and deleting all phase annotations leaves a nontrivial decoded prediction unchanged in a regression test.

The predeclared27-policy validation search rejected every candidate. The selected diagnostic challenger added zero H/A labels on both natural validation matches. Its policy is confidence0.975, full control-anchor gap cap2s and switch-prior multiplier0.5. Selection is recorded as `rejected_before_final_test`; it cannot become deployable through a lucky later score. No gates are relaxed to reach zero unknown output.

## Why the model emitted nothing

A source-only feasibility calculation found a design error after freezing: posterior temperature calibration and the decoder's finite switch penalty make every declared confidence threshold unreachable on an undecided row. This is an architectural mismatch, not evidence that player motion contains no possession information. The grid should have been checked for feasibility before its expensive evaluation.

For the symmetrized ensemble, half the summed leaf-value ranges times the learning rate bounds the absolute emission logit by2.858519. Each neighbouring two-state transition message has absolute log-odds at most the switch cost. Therefore an undecided row's calibrated posterior logit is bounded by `(2.858519 + 2 * switch_cost) / temperature`. Hard baseline anchors do not remove this finite transition-message bound on a neighbouring unknown row.

The confidence ceilings are0.899440,0.866936 and0.852669 for switch multipliers0.5,1 and2, respectively. The minimum declared threshold is0.90. Thus all27 policies are incapable of adding a label, independently of match data. This explains their identical outputs. A new feasibility guard is the first contained follow-on development task; any redesigned calibration/decoder would need a separate preregistered evaluation. The frozen experiment and held-out results will not be retuned or rebranded as a useful model improvement. Hidden-turnover reference support is also insufficient, independently of this design error.

The model was trained on eight matches, calibrated on two and selected on two from the pinned20-match SkillCorner source. Eight further matches are reserved for one frozen final diagnostic evaluation. The reference is half-open provider team-possession phases, with absence/conflict left unknown. Phase durations/clocks are reconciled, contradictions quarantined, and retained source support reported. Detected-only input is primary; extrapolated availability is a separately labelled ablation. Canonical25Hz interpolation preserves native10Hz provenance and does not cross missing native detections.

## Frozen diagnostic result

Artifact `396a05f28d0493492af118682453dbf489d1cc867a6136420c3de3a3783bbf48` was frozen before final scores, with34 prediction/evaluation source hashes, fixed split, calibration, validation rejection and review receipts. All16 held-out match/regime cases, seven seen DFL regressions, two four-case stress receipts and two available-position ablations completed. Final summary verifies their identities and exact membership before reporting completion.

Across the eight natural held-out matches, mean spellF1 is **0.468999 before and after**, and mean known-reference unknown fraction is **25.6736% before and after**. The model adds zero H/A frames, including outside reference support. The paired match-bootstrap lower bound is0 because every paired change is0; this is a vacuous non-regression, not evidence of an improvement. Final acceptance fails coverage, per-class recovery/support, hidden recovery/support, endpoint superiority and pre-test eligibility.

| Match | Baseline = candidate spellF1 | Known-reference X |
|---|---:|---:|
|2007448|0.494158|25.7420%|
|2007721|0.475000|22.4632%|
|2010085|0.461049|20.7071%|
|2011166|0.433018|26.1247%|
|2013725|0.478803|27.1710%|
|2015213|0.471928|26.5251%|
|2016236|0.494710|29.1685%|
|2017461|0.443329|27.4869%|

Pooled existing H/A precision/recall/F1 are87.76/73.28/79.87% and91.61/59.51/72.15%, respectively, identical before/after. These count abstention against recall. They describe the existing baseline, not correctness of new labels. There are zero natural qualifying hidden spells and only two masked ones, below the declared20 across two matches. No useful hidden-turnover mechanism claim can be made. The eight inputs contain188429 missing native ball samples in1510 native intervals; resampling does not multiply that support. Minimum retained reconciled reference support is99.695%, above the95% source-quality floor.

## Simple alternatives and remaining uncertainty

The matched-budget endpoint comparison is retained, but its budget is zero for this candidate. Full eligible simple rules were therefore evaluated independently on validation. Every rule failed applicable eligibility, including the90% new-H/A agreement and hidden-support requirements.

| Rule / cap | Coverage gain | Mean spellF1 | New H agreement | New A agreement |
|---|---:|---:|---:|---:|
|Baseline|0|0.491096|—|—|
|Last owner /2s|3.78pp|0.490693|60.68%|60.88%|
|Last owner /5s|10.38pp|0.491836|75.04%|68.02%|
|Last owner /10s|13.14pp|0.488604|74.78%|69.90%|
|Two sided /2s|3.78pp|0.485968|52.57%|66.86%|
|Two sided /5s|10.38pp|0.483319|64.83%|72.99%|
|Two sided /10s|13.14pp|0.485254|66.12%|74.13%|

This is why filling more X is insufficient: it can add many incorrect team labels while barely improving, or worsening, whole possessions. On the first validation input, the reference-free audit found54699 of75416 raw X rows lacked three available players on each side. At the2s cap,3275 raw rows were eligible before confidence, compared with12689 at10s. Many raw rows have no phase reference, so these counts are not measured correctness or a local recovery forecast.

The declared available/extrapolated-position ablation changes the baseline's input availability, but the candidate still adds nothing. Four mechanism stresses per validation match cover opponent loss, identity discontinuity, false ball coordinates and ball timing shifts. Seven DFL natural/masked regression pairs preserve complete-target spell/macro scores. These non-regressions are also vacuous for an inactive candidate; they do not establish robust new recovery or independent live/dead detection. One-native-sample boundary-sensitivity metrics and transition counts/latencies are retained in licensed aggregate reports. Raw mechanism spans treat X as a miss; the unchanged official scorer's expanded metrics remain separate.

## Verification and delivery decision

A fresh whole-change review found six important execution/scientific/integrity defects. All were addressed in one reproducing-test fix pass, including raw hidden-spell IoU, nonregression/superiority gates, independent simple alternatives, preparation ownership, evidence dependency checks and stale regression receipts. The separate [review disposition](docs/temporal-final-review.md) preserves findings, fixes and reviewer limits.

The final source suite passed243 tests with5 documented skips. Five temporal training/export/calibration/gate checks passed separately under Python3.12. Real40-tree export parity had maximum logit error0 on1000 training rows. The exact31-module bundle parses as Python3.9 and ran its synthetic motion/tree/decoder probe under isolated Python3.11 with no NumPy, pandas, SciPy or sklearn runtime imports.

**No new local inference was performed, no candidate was promoted, and the existing Desktop output is preserved.** Local accuracy and full-state transfer remain unmeasured. The negative experiment, structural confidence error, unsuccessful simple rules and test receipts are retained so the next phase can address actual failure causes. Source/docs, licensed model parameters and aggregate external metrics are the publication allowlist; raw assets, per-frame outputs and transition locations remain local.

## Limits and next direction

Known-play H/A reference cannot establish the correctness of extra team assignments during unknown stoppages. Repeated teams and one competition limit independence. Provider phases are not an independently adjudicated video study. Native samples, intervals and matches are the support units; resampling creates no new observations. ATD local input has unverified freshness and an ordinal team-role assumption. Challenge footage/ground truth, manual game labels and challenge-driven calibration are excluded.

The strategy-blind audit warned that same-team endpoints can hide an opposing spell. Lowering unknown output by filling those gaps can erase turnovers. We therefore retain abstention where evidence fails, report supported new H/A separately, and require useful team-spell/hidden-turnover evidence before any new local experiment. Public GitHub research and a contained follow-on development task are queued after this phase; their job is to find worthwhile missing evidence or methods, not add complexity merely to reduce an uncertainty count.

Attribution: SkillCorner/PySport Open Data, pinned revision4340d274572876239c154c90bc507a9b3250a656, repository MIT licence. Earlier seen DFL data: Bassek, Rein, Weber et al., Scientific Data12,195(2025), doi:10.1038/s41597-025-04505-y, DFL/Sportec Solutions, CC BY4.0. Source licence texts and immutable acquisition receipts remain local; source/docs/licensed metadata are the publication allowlist.
