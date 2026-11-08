# Progress record

Updated on 5 November 2026. Current source: `2026.11.05-tactical-validated`. Automatic camera synchronization was completed as an experiment and paused after zero bounded links. An opt-in externally frozen tactical model reduces local X from 69.192% to 56.151%; local correctness remains unmeasured. [CHANGELOG.md](CHANGELOG.md) explains the transition and [FOUR_GOALS.md](FOUR_GOALS.md) gives full evidence and limitations. Earlier sections are a chronological record, not current eligibility or accuracy claims. [RULES.md](RULES.md) controls all work.

## 1. Tactical missing-observation prototype

Implemented original-frame tracking adapters, metre-scaled nearest-team distances, sustained control confirmation, short two-sided same-team bridges, automatic phase support, explicit X outputs and a queue of unresolved intervals. Missing ball alone never becomes D. Diagnostic coordinate interpolation does not determine possession.

The original eight-scenario synthetic fixture had 482 graded synthetic frames, 147 unresolved frames before bridging and 100 afterwards, with 47 inferred frames. These are fixture behavior counts, not real-match recovery estimates.

## 2. Two-camera experiment

Added local clock OCR, camera-specific clock selection, saved ROI files, fractional tick-based alignment, timing uncertainty, homography checks, distinct same-team point matching and weighted fusion. The tactical and broadcast frame numbers remain separate.

The synthetic camera demo starts with 40 unresolved tactical frames. Broadcast evidence fills 20; an unreliable homography blocks the other 20. No neural ensemble was trained.

## 3. OCR debugging and local pilot

Initial crops missed digits or included the score. Added a local clock-box selector and explicit Tesseract TSV output. Checked both original and preprocessed clock crops; processing can help or hurt depending on the installed model. Added an explicit 0.5 OCR-score trial cutoff, all-sample confidence reporting, local alternate-treatment retries, conflict rejection and support for an isolated bounded OCR miss.

One tactical pilot reported 136 clock-shaped readings from 150 samples, 130 eligible at cutoff 0.5 and 14 unreadable. Its confidence median was 0.888 but the first percentile was zero. It produced 375 bounded clock estimates over a 750-frame selected interval. Those confidence and coverage counts did not establish timing accuracy.

## 4. Initial real fusion result

The participant ran the first real selected-clip fusion locally. Its aggregate report covered 199319 tactical frames, of which 158857 are in the published grading windows. Of those, 64643 had missing tactical ball coordinates (40.69%).

| Aggregate result | Before fusion | After fusion |
|---|---:|---:|
| Home assignments | 21105 | 21154 |
| Away assignments | 13847 | 13847 |
| Dead assignments | 0 | 0 |
| Undecided assignments | 123905 | 123856 |
| Resolved graded-frame coverage | 22.002% | 22.033% |
| Missing-ball frames assigned a team | 0 | 0 |

Only 700 frames reached camera comparison, equivalent to 28 seconds of footage. Outcomes: 345 not verified, 137 without direct broadcast control, 123 below the broadcast-weight threshold, 49 rescues, 40 agreements and 6 conflicts retaining tactical. Most frames outside this short pilot had no eligible clock correspondence.

All 49 new assignments came from restart-ambiguous frames; none demonstrated recovery when the tactical ball was missing. This established an executable data path, not improved accuracy.

## 5. Problems identified

- Every frame in an automatic set-piece phase was forced to X before observed evidence was considered. That rule produced 43899 restart-ambiguous graded frames in the initial report. This is an affected-frame count, not a recovery forecast.
- Tactical received restart tags while broadcast did not, confounding apparent broadcast rescues.
- Replays may retain the current live clock while showing earlier action. A plausible single-frame formation can pass geometry checks.
- The allowed 0.25-second alignment uncertainty spans about six frames, comparable to the control-confirmation duration.
- The ranking scorer expands X within each half. More raw assignments may leave the scored sequence unchanged or change a larger interval through forward/backfill.
- Zero missing-ball rescues cannot be interpreted without counting actual usable missing-ball opportunities.

## 6. Council audit and implemented first repair

Five independent AI advisor roles proposed changes; five anonymous peer reviews challenged them. The selected order was baseline repair, detailed diagnostics, stronger temporal broadcast validation, interval-based missing-observation inference and general stoppage detection. See COUNCIL_AUDIT.md.

Implemented the first controlled stage:

- Soft restart phases allow sustained observed control candidates, retain bridge restrictions and reset confirmation at phase edges.
- Explicit dead evidence has precedence.
- The organiser-published pre-second-kickoff interval [110808,113742) is D with separate metadata provenance. General stoppage detection is still absent.
- Mapped restart/dead context constrains both cameras.
- `--audit-baseline` isolates legacy baseline, restart repair, published context and fusion.
- Reports include raw and scorer-expanded changes, predicted spell counts, detailed verification reasons, bridge diagnostics and a missing-ball opportunity funnel.
- Existing CSV diagnostics gain evidence and stage labels; baseline variants do not create duplicate prediction files.

Verification passed 96 routine tests and the full-index synthetic integration through both modular and standalone entry points. Independent code review found no actionable blockers and reproduced legacy Decision fields on 1000 randomized inputs. The standalone bundle passed source-parity and isolated execution checks.

## 7. Controlled local result received, 5 November 2026

The participant supplied an aggregate `ensemble_report.json`. No predictions were checked against video or ground truth in this analysis.

| Stage | H | A | D | X | Resolved graded coverage |
|---|---:|---:|---:|---:|---:|
| Legacy tactical | 21105 | 13847 | 0 | 123905 | 22.002% |
| Restart repaired | 30475 | 18465 | 0 | 109917 | 30.808% |
| Earlier published D context | 29841 | 18458 | 2934 | 107624 | 32.251% |
| Broadcast fusion | 29854 | 18458 | 2934 | 107611 | 32.259% |

Restart repair newly assigned 13988 frames, an 8.805 percentage-point coverage change. Its scorer-expanded sequence changed at 21626 frames through both direct changes and propagation. These are behavior changes, not verified improvements. The earlier D context changed 2935 raw labels: 2934 explicit D assignments and one boundary-state change. Its eligibility under the newer clarification remains unresolved.

Fusion added 13 H assignments, equivalent to 0.52 seconds at 25 fps, all from restart-ambiguous frames. All 13 had no effect on the scorer-expanded sequence; predicted possession spells remained 467. The earlier 49-rescue result was confounded by the old restart policy and unequal source context.

Only 700 graded frames reached comparison: 0.441% of 158857 graded frames, or 28 seconds of comparison frames. Geometry was consistent in 355, ball geometry disagreed in 131 and homographies were unreliable in 214. These categories do not identify known replays. The other 158157 graded frames lacked an eligible tactical-clock link; alignment cannot separate unscanned ranges from unreadable OCR.

Of 284 compared frames with an unresolved missing tactical ball, **none had an observed broadcast ball**. Every later missing-ball recovery gate consequently received zero opportunities. This does not show that broadcast cannot help elsewhere; it shows no usable secondary ball observations in this subset. The tactical baseline still has 64079 unresolved missing-ball frames.

The baseline's 107624 X frames were grouped automatically into 58804 frames in restart/dead-context gaps, 20663 with opposing anchors, 15270 with conflicting tags, 10962 limited by duration/tag support and 1925 in unbounded gaps. These are bridge-rule categories, not established physical explanations. They describe the baseline before the final 13 fusion assignments.

Aggregate checks passed for graded label/reason totals, complete fusion-status totals, verification-reason totals and baseline gap totals. Accuracy, spellF1, alignment correctness and possession correctness were not measured.

## 8. Current boundaries and pending work

The newer organiser clarification controls all subsequent work; see [RULES.md](RULES.md). No inference weights, distances, timing gates, bridge durations or existing OCR cutoffs were adjusted from this report. New training is optional; any training/tuning must use external data. The executable needs a complete route without match-specific manual clock setup before it can be treated as a final-entry candidate. Validate automatic setup, temporal replay checks, longer-gap inference and general stoppage detection externally. Do not relax gates or select models to increase this match's assignment count.

## 9. Automatic clock discovery

Added `camera discover-clock` as the first replacement for manual camera setup. It samples the entire recording, locates full-frame clock text through local pretrained Tesseract and groups spatially stable progressing observations. It requires no human ROI, half or playback anchor. Decoded grayscale images stream through memory; no collection of frame files is created. Two camera runs overwrite their respective small JSON reports.

Synthetic tests exercise clock detection away from old presets, a blank opening, exclusion of score text, split tokens, invalid boxes/confidence, freezes/resets, short versus long missing stretches, moved overlays, multiple clocks, original-index preservation and corrupt decoder output. This is implementation verification only. No challenge assets or possession ground truth were processed, and no parameters were selected from the controlled match report.

The output explicitly remains candidate discovery: no dense timing map, half assignment, replay/live verification or new possession decisions. These later stages remain pending. The discovery feature does not resolve the earlier fixed-D exception's eligibility.

## 10. Automatic dense synchronization and camera pause

Added automatic window/clock-region selection from sparse discovery, local dense OCR, original-index validation and safe generation publication. The unchanged .7 confidence, stride 5 and .25-second timing settings produced 1,704 dense OCR samples per camera. Tactical 117 and broadcast 229 samples passed OCR eligibility, but neither stream produced bounded clock estimates; usable alignment links were zero. No possession changes followed. Original broadcast video versus tracking row-count disagreement was reported, not silently repaired. Detailed outputs remain local. See [AUTOMATIC_SYNC.md](AUTOMATIC_SYNC.md).

## 11. Four tactical workstreams

Established a strict seven-match external benchmark from licensed DFL/Sportec data, using whole-match splits and unchanged official scoring functions. Diagnosed missing dead-ball segmentation, ambiguous owner intervals and restart/boundary errors. Selected a 31-node depth-four geometry/history tree on external development/validation only, then froze its model/policy/source identity before final tests.

The complete provider-target mean test spellF1 improved .37361 -> .50513, macroF1 .38871 -> .86041 and X 60.47% -> 9.86%. Both matches improved under all declared ball-mask regimes. A post-freeze audit then exposed nearly universal inactive-coordinate carry-forward; the D results cannot establish transferable stoppage detection. Active-only spellF1 slightly regressed on both tests, and per-label H/A newly resolved agreement was 86.36/88.95%. The candidate remains opt-in and was not retuned after this discovery.

One frozen local run, with no provided video/GT checks or fitting, preserved 199,319 original rows. On the same 158,857-frame scope, X fell 109,917 ->89,200; unresolved intervals 1,045 ->509. The baseline excludes the disputed D interval. Of remaining X, 59,788 lack ball/recent owner, 26,572 fail model support and 2,840 have other quality/conflict limits. These are coverage and automatic diagnostic counts, not correctness measurements. Full reasoning, regressions, licence/provenance and reproduction are in [FOUR_GOALS.md](FOUR_GOALS.md).

## 12. Next proposed milestone

Check the frozen candidate on an independent licensed provider, then develop validated interval inference for missing-ball periods. Fewer X should accompany stronger team-spell quality and per-class correctness. No additional missing-ball model, cross-provider result or promise of zero reliable uncertainty is included in this release.
