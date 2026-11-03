# Progress record

Snapshot prepared on 3 November 2026. Current implementation: `2026.11.02-restart-audit`.

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

## 7. Pending

The participant's post-repair controlled real-run report has not yet been provided. No post-repair real-match coverage or accuracy improvement is claimed.

Next, inspect the controlled stage changes, detailed verification reasons and the eligible missing-ball denominator. Then evaluate sequence-based replay/current-view checks, timing-offset robustness, general stoppage detection and longer-gap inference on permitted other-match labels. Do not widen thresholds merely to increase assignments, and do not use the competition game's public labels for model selection.
