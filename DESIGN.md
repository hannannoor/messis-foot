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


## Stoppage-regime test and observed-touch candidate (10 November)

**Why.** On the provided match the ball is missing on 41% of graded frames in long blocks, which label-free evidence ties to stoppages. External matches do not look like that (DFL keeps a frozen ball during dead ball), so the gap rule had never been scored where it could help or hurt. `stoppage_regime.py` removes the ball from five labelled matches (`dfl-J03WN1`, `dfl-J03WR9`, `wcsf-used-match` primary; `dfl-J03WOH`, `dfl-J03WOY` secondary) from their own reference labels: selected dead runs of 76 or more frames lose the ball from up to 2 s after play stops until up to 2 s after the restart, plus 268-frame live blocks. Regimes: `natural`, `stop100` (all long dead runs), `stop75` (75% of them plus live blocks equal to one third of the removed dead frames; the primary challenge-like regime), `stop50`, `stop75-jitter`. Protocol: [docs/stoppage-regime-protocol.md](docs/stoppage-regime-protocol.md). Results: `reports/stoppage-regime/results.json`. 75 scores, one run.

**Results** (spell F1, primary mean of the two primary DFL matches and the WCSF match):

| Regime | control | candidate (gap rule) | candidate + touch | candidate - control | touch - candidate |
|---|---|---|---|---|---|
| natural | 0.5294 | 0.5294 | 0.6381 | +0.0000 | +0.1087 |
| stop100 | 0.4813 | 0.5360 | 0.6280 | +0.0547 | +0.0920 |
| stop75 | 0.4443 | 0.4552 | 0.5362 | +0.0110 | +0.0810 |
| stop50 | 0.4013 | 0.4018 | 0.4697 | +0.0005 | +0.0679 |
| stop75-jitter | 0.3438 | 0.4013 | 0.4777 | +0.0575 | +0.0764 |

In `stop75` dead-ball recall is 0.576 (control), 0.898 (candidate), 0.890 (candidate + touch). The gap rule relabelled 98% of long gaps in `stop100`, 70% in `stop75` (95% of gaps from dead blocks, 33% of gaps from live blocks) and 41% in `stop50`; the provided match's own rate is 85%, between `stop75` and `stop100`. The gap rule was safe in every regime (no loss against the control).

**Decisions fixed in advance.** 7.1 (candidate must not lose more than 0.005 to the control in `stop75`): passed. 7.2 (touch evidence replaces the candidate only if +0.04 in `stop75`, not negative in `stop75-jitter`, not below -0.005 in `natural`, dead-ball recall within 0.02, no primary match losing more than 0.02 in `stop75`): all five conditions passed.

**Provided match (aggregates only).** 698 touches detected; 39.3% of graded frames carry a touch bonus; 9,137 frames (5.8% of graded) differ from the current candidate (`A->H` 4,652, `H->A` 4,340, `D->A` 127, `D->H` 18); spells 434 -> 383, median spell 124 -> 135 frames, spells under 25 frames 29 -> 32. CSV SHA-256 `1de96acb8ac2198c960637f6b20c2438c9ff142e76a9ab463c384b52814b8d14`; two runs byte-identical; the official validator passes. Public five-minute window (run once, pipeline-defect check only): spell F1 0.430, macro F1 0.683, accuracy 0.743, 23 predicted against 17 reference spells (current candidate: 0.362 / 0.677 / 0.734, 25 predicted).

**Limits.** These matches have been scored before; `dfl-J03WN1` was in the development set that selected the touch setting (3, 2, 8); the primary set is three matches; re-testing touch evidence after an earlier rejection is post-hoc; the regimes are built from reference labels and are a model of the provided match, not a measurement of it; the touch gain is also large with the ball present (`natural`, +0.109), so it is not specific to stoppages; the earlier version of touch evidence lost on SkillCorner, whose reference is least like the challenge's, and SkillCorner was not part of this test; the public window holds 17 reference spells, so its numbers carry large uncertainty.

**Reproduce.** `python -I touch_release.py --prefix <prefix> --tags <prefix>_smart_tagging.xml --out <new dir>`; CSV SHA-256 as above. With touches disabled the pipeline reproduces the current candidate (`31b947d3…f963`).
