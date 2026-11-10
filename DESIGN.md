# Missing-ball handling prototype

The user authorised implementation of missing-observation handling first. This is a local Python prototype, not a validated competition entry.

## Approach

Use bounded, two-sided team continuity first. A probabilistic sequence model needs an independent validation source; full video retracking is deferred until unresolved intervals identify where it is useful. These are implementation choices, not measured performance findings.

1. Convert tracking to nearest home/away distances in metres. Track slots are temporary, never persistent player IDs.
2. Confirm control only after consecutive close, unambiguous observations. Backdate a confirmed run to its start; never let evidence accumulate across missing frames.
3. Leave missing/contested observations unknown initially. Bridge a short gap only when both confirmed anchors agree. Restart hints block bridging. Longer gaps additionally require consistent automatic possession-phase evidence throughout.
4. Retain explicit algorithmic dead-ball evidence supplied by an upstream component. The reference-match adapter also applies the organiser-published pre-second-kickoff interval [110808,113742) as D with separate provenance. This prototype does NOT infer D from missing tracking, a stationary ball, or a set-piece interval. A match-ready live/dead detector remains separate work.
5. Estimate short missing ball coordinates only for diagnostics when displacement is plausible; never use these invented coordinates to decide a hidden turnover.
6. Export unresolved intervals as a queue for a future local video algorithm. Never use manual corrections on the competition match.

## Constraints

The newer organiser clarification in [RULES.md](RULES.md) takes precedence: no output-versus-video checking, manually created game data or AI-service uploads of provided data. Training, fitting, calibration and tuning require external data, never challenge ground truth or video. The earlier fixed D exception must not be assumed eligible.

No gated assets leave the local machine. No public-ground-truth training, tuning, or model selection. Reset at half boundaries. Preserve X for unresolved intervals. Heuristic evidence levels are not calibrated probabilities. A same-team gap can still contain a hidden turnover or stoppage: bounded bridging is a hypothesis, not proof.

## Defaults chosen for synthetic development

25 fps; control distance 2 m; opposing distance advantage 0.75 m; 0.24 s confirmation; 0.6 s short continuity; 2 s tag-supported continuity; 0.4 s coordinate interpolation; 35 m/s displacement cap. All are provisional and exposed in config. Synthetic examples cannot tune real-match accuracy.

## Deliverables

Standard-library Python package, raw ATD/Smart Tagging adapter, evidence CSV interface, deterministic demo, tests, submission-shaped CSV, frame diagnostics, unresolved-interval JSON and coverage report. Default match adapter has no D classifier, so its output is explicitly experimental.


## 10 November release candidate: control + gap rule + kickoff patch

**Approach, in plain words.** (1) The frozen control predicts every frame from player geometry with a fixed decision tree and a sequence decoder. (2) On this match the ball is untracked on about 41% of graded frames, in long blocks; the control carries the previous owner through each block. The gap rule relabels a missing-ball block longer than 75 frames as dead ball when the median player speed inside it is below the match's own median player speed outside such blocks. Nothing is tuned. (3) The organisers state that the second-half graded block starts well before the second-half kickoff and that every graded frame before the kickoff is dead ball. The kickoff patch reads the two `Kick Off (Start)` instances in the Smart Tagging XML (seconds x 25 = video frame, the time base documented in the organisers' DATA.md and used by the repository's earlier tag code), and for each half that contains exactly one such instance, labels every frame of that half before it `D`. A half with zero or several instances, or whose instance lies outside the half, is left alone.

**Inputs.** Tracking, metadata and homography (as the control); Smart Tagging for the kickoff start times only. No video, pose, labels or public ground truth.

**Considered and dropped.** Pose estimation (players are roughly 20-50 px tall in the tactical view by two different estimates, far below what limb keypoints need); a learned world model; ensembles; the touch-evidence experiment (rejected: it gained on fully tracked data but lost on dead-ball recall and on the noisiest provider; `observed_touch.py` is kept, unevaluated and unused); the temporal network pilot.

**Evidence** (all label-free or on other data; none measures this match against its truth):

| Check | Result |
|---|---|
| 15 external matches, natural tracking, equal-provider spell F1 | 0.551816 -> 0.550876 (-0.0009; limit -0.005). Pass |
| Same, random 30% ball masking (reported only) | 0.469149 -> 0.438025 (-0.031) |
| 3 Metrica sample matches | 0.4467 -> 0.5451 (+0.098). Pass; partly circular |
| Provided match, aggregates only | D share 3.0% -> 39.8%; spells 327 -> 435; 113 of 133 long gaps relabelled; set-piece tags starting on or just after D: 1 of 58 -> 45 of 58 |

**Limitations.** There is no labelled validation of the gap rule on this kind of data. The random-mask result shows that the rule relabels live play when gaps are unrelated to stoppages. 20 long gaps keep the control's labels. The rule's "restart extension" (keep `D` while a reappeared ball is stationary) is inactive: it compares the first reappeared frame with the last pre-gap position, a large jump, so it produced 0 frames in every run; it was left unchanged so the checks above stay valid. Smart Tagging is automatic and can be wrong; a tag window starts before the true kickoff, so the patch can leave up to the tag's lead (82 frames on the second half) with the candidate's labels. The first-half tag lies before the graded block, so the first half is unchanged.

**Reproduce.** See the README command; expected CSV SHA-256 `31b947d3b250b6267a7d8f0aac0c4e4eafd82a4fc873c82759806e676b1bf963`. Label hashes (frame labels concatenated, SHA-256): control `8d233ff1...a847`, control + gap rule `17bad133...a5c4`.
