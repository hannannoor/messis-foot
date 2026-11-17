# Four tactical-only goals

The user explicitly approved completing external evaluation, dominant-error analysis, one validated tactical improvement, and a fourth goal addressing the very high undecided share. They requested reasoning, solutions and limitations. This is authorization to execute the agreed approach without another approval round.

## Goals and completion evidence

1. Establish a reproducible external benchmark using the exact MIT-licensed competition metric code and independent licensed non-challenge matches. Store acquisition provenance, checksums, labels and feature separation, whole-match splits and baseline reports.
2. Diagnose possession, live/dead, boundary, missing-ball and restart-proximity errors externally. Report per-match errors and genuinely unresolved challenge evidence separately from scored external errors.
3. Implement a contained improvement chosen using external development/validation data, freeze it before opening final test scores, and demonstrate its actual held-out effect. Report regressions as well as gains. A rejected candidate is not a validated improvement.
4. Reduce abstention using justified evidence and external validation; report raw X share, correctness on newly resolved frames, scorer-expanded changes and spellF1. On the challenge, run frozen inference once and report coverage without accuracy claims, video checks or GT access.

## Agreed direction and builder choices

Continue the tactical-only system; leave camera OCR/fusion paused. Alternatives are conservative trajectory/interval rules and a small externally fitted geometry/state model. A blanket forward fill or relaxed challenge-selected cutoffs does not solve uncertainty and will not be a candidate. Start with an external baseline and diagnose errors before selecting between the two legitimate improvement families.

The builder may fit a compact decision-tree model using already installed sklearn in the base Anaconda environment if the external diagnosis supports it. Production inference must remain Python 3.9+ standard library, with exported model data embedded in the one-file program; training libraries are development-only. Any fitting or selection uses external matches exclusively. Existing tactical inference remains available as an explicit baseline.

## External reference

IDSSE / Sportec Open DFL: https://doi.org/10.6084/m9.figshare.28196177 (CC BY 4.0, verified from the primary Figshare API and paper). Tracking includes BallPossession and BallStatus. Raw mappings: 1 home, 2 away; status 0 inactive, 1 active. Unknown codes remain unknown. Provider reference is not independently verified competition gold; flight semantics are not fully documented. Source: https://pmc.ncbi.nlm.nih.gov/articles/PMC11787359/ . Preserve attribution and distinguish this limitation in every performance claim.

Split fixed before results: development J03WOH, J03WOY, J03WPY, J03WMX; validation J03WQQ; final held-out tests J03WR9, J03WN1. No frame-random split. The repeated Fortuna team limits team independence. Do not tune on held-out tests or challenge summaries.

Coordinates, team membership and deterministic geometry/kinematics are input features. BallStatus, BallPossession, event outcomes, official net time and target-derived filtering are excluded from features. Do not filter to only_alive. Preserve original external IDs, canonical 25 Hz time and unknown labels; validate ordering, frame gaps and period boundaries. Unknown reference frames are excluded by the official mask.

## Evaluation and selection

Use exact official spellF1 averaged over IoU .3/.4/.5/.6/.7, raw macroF1, per-class H/A/D metrics, transition F1/latency, fragmentation, coverage and selective correctness. Evaluate halves with independent runs, inserting evaluation-only X separators longer than the largest transition tolerance for pooled reporting; never add those pads to inference or challenge submissions.

Predeclare deterministic external-only masking stress tests for missing ball/player observations; masks alter features, never labels, and never follow target classes. Natural and masked results must remain separate. No mask rates/durations are fitted to challenge missingness statistics.

Prefer a candidate that improves validation spellF1 while reducing raw X, with macroF1 and newly resolved correctness as safeguards. Freeze selected model/thresholds/temporal policy and its checksum before final tests. Require held-out reporting on both test matches and their match-macro average. If transfer is uneven, document it and do not silently retune. A large X reduction without acceptable correctness is not success.

Numeric validation gates, fixed before baseline scores: spellF1 strictly above baseline, raw X strictly below baseline, macroF1 no worse, and at least 90% correctness on newly resolved graded frames. Report newly resolved H/A and D support/correctness separately. Search a small declared external-only grid rather than arbitrary sweeps. Unknown status/ownership remains X; inactive status=0 is D irrespective of possession. Challenge-only Smart Tagging semantics are not validated by this geometry-only reference; keep selected learned inference geometry-only and report tags separately.

Apply the declared validation safeguards to natural validation and its independently generated 30% missing-ball stress case. A class-D prediction needs observed ball and available observations of both teams; missing ball/opponent alone cannot establish D. The new local tactical route masks coordinates at invalid/nondegenerate homographies or reprojection error above the existing 3-unit reliability gate, without fitting that gate on this match. Record quality-masked coverage separately.

## Challenge boundary

Use tracking and automatic Smart Tagging locally only, no videos needed. No possession GT, public or private, may be read or scored. No manually published pre-kickoff D labels in the new tactical route. Missing ball alone is not D. Missing player observations are not infinite opponent distance. Keep existing outputs and the currently installed source recoverable. Write a separate tactical output folder with explicit model/parameter provenance and coverage-only metrics.

## Deliverables

New external adapter/benchmark CLI, tests, fixed exported policy/model, tactical CLI, updated single-file bundle, external baseline/diagnosis/comparison results, one frozen challenge inference report and a readable four-goal explanation. Mark unachieved criteria clearly. Preserve the existing camera modules and legacy inference for reproducibility; do not launch another camera scan.

## Known risks

Provider-label semantics and dense calibrated Bundesliga tracking differ from noisy tactical ATD. Repeated teams and few matches limit generalization. Artificial masking is a stress test, not realistic annotation. Correctness and coverage can conflict; some X should remain. External improvement is not measured challenge improvement. A lightweight model can overfit, so keep whole-match validation and final tests isolated.
