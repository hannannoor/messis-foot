# Missing-ball handling prototype

## Status

Submitted: `restart_release.py`, frozen control → gap rule → decoder restart → gap rule → kickoff patch. Command: `python -I restart_release.py --prefix "$prefix" --tags "${prefix}_smart_tagging.xml" --out "$out"`. Expected CSV SHA-256 `15756bcb57f184d717a5bc8f30b15a8777227165dd4973edbbaf69ba6a02a685` (199,319 rows). The previous gap candidate, frozen-control fallback and touch alternative are not submitted. [Submission technical document](docs/technical-document.md).

## Decoder restart after stoppage gaps

The old decoder could carry the pre-stoppage owner into restarted play. The release marks the gap rule's stoppage gaps unusable and decodes the same rows/costs again, then applies the gap rule and kickoff patch. It checks parity with the unchanged control and unchanged gap selection. No setting was tuned. Touch evidence stays rejected.

Restart gates E/F/G passed: WR9/WCSF mean spell gain +0.018823, both positive; SkillCorner confirmation change 0.000000; dead-ball recall change 0.000000. Expected transfer remains uncertain on reused, reference-masked data.

Provided-match aggregates: 388 graded frames changed (0.244%); H→A 346, A→H 41, D→H 1. Spells 434 → 415; median length 124 → 137; spells under 25 frames 29 → 9, under 50 frames 94 → 74. First owner differs after 19 of 113 stoppage gaps.

Reporting-only set-piece match/mismatch/no-transition counts: 15/9/3 → 14/10/3. Corners 10/12 → 6/12; goal kicks 2/7 → 4/7 with transitions; free kicks 3/5 → 4/5. Agreement did not improve. These automatic tags do not control restart prediction. Evidence: [restart aggregates](reports/submission/restart-provided.json), [gap support](reports/submission/gap-support.json), [fixed decision](reports/submission/release-decision.json).

## Historical design and experiments




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

**Limitations.** There is no labelled validation of the gap rule on this kind of data. The random-mask result shows that the rule relabels live play when gaps are unrelated to stoppages. 20 long gaps keep the control's labels. The rule's "restart extension" (keep `D` while a reappeared ball is stationary) is inactive: it compares the first reappeared frame with the last pre-gap position, a large jump, so it produced 0 frames in every run; it was left unchanged so the checks above stay valid. Smart Tagging is automatic and can be wrong; a tag window starts before the true kickoff, so a short stretch before play keeps its earlier labels. The first-half tag lies before the graded block, so the first half is unchanged.

**Historical reproduction: previous gap candidate, not submitted.** Run `python -I gap_release.py --prefix <prefix> --tags <prefix>_smart_tagging.xml --out <new-dir>`; expected CSV SHA-256 `31b947d3b250b6267a7d8f0aac0c4e4eafd82a4fc873c82759806e676b1bf963`. Label hashes (frame labels concatenated, SHA-256): control `8d233ff1...a847`, control + gap rule `17bad133...a5c4`.


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

In `stop75` dead-ball recall is 0.576 (control), 0.898 (candidate), 0.890 (candidate + touch). The gap rule relabelled 98% of long gaps in `stop100`, 70% in `stop75` (95% of gaps from dead blocks, 33% of gaps from live blocks) and 41% in `stop50`; the provided match's own rate is 85%, between `stop75` and `stop100`. The gap rule had no loss on the primary mean in any regime. On dfl-J03WR9 it lost 0.011672 in stop75 and 0.026738 in stop50.

**Decisions fixed in advance.** 7.1 (candidate must not lose more than 0.005 to the control in `stop75`): passed. 7.2 (touch evidence replaces the candidate only if +0.04 in `stop75`, not negative in `stop75-jitter`, not below -0.005 in `natural`, dead-ball recall within 0.02, no primary match losing more than 0.02 in `stop75`): all five conditions passed.

**Provided match (aggregates only).** 698 touches detected; 39.3% of graded frames carry a touch bonus; 9,137 frames (5.8% of graded) differ from the current candidate (`A->H` 4,652, `H->A` 4,340, `D->A` 127, `D->H` 18); spells 434 -> 383, median spell 124 -> 135 frames, spells under 25 frames 29 -> 32. CSV SHA-256 `1de96acb8ac2198c960637f6b20c2438c9ff142e76a9ab463c384b52814b8d14`; two runs byte-identical; the official validator passes. Public five-minute window (run once, pipeline-defect check only): spell F1 0.430, macro F1 0.683, accuracy 0.743, 23 predicted against 17 reference spells (current candidate: 0.362 / 0.677 / 0.734, 25 predicted).

**Limits.** These matches have been scored before; `dfl-J03WN1` was in the development set that selected the touch setting (3, 2, 8); the primary set is three matches; re-testing touch evidence after an earlier rejection is post-hoc; the regimes are built from reference labels and are a model of the provided match, not a measurement of it; the touch gain is also large with the ball present (`natural`, +0.109), so it is not specific to stoppages; the earlier version of touch evidence lost on SkillCorner, whose reference is least like the challenge's, and SkillCorner was not part of this test; the public window holds 17 reference spells, so its numbers carry large uncertainty.

**Historical reproduction: rejected touch alternative, not submitted.** `python -I touch_release.py --prefix <prefix> --tags <prefix>_smart_tagging.xml --out <new dir>`; CSV SHA-256 as above. With touches disabled the pipeline reproduces the current candidate (`31b947d3…f963`).

## Touch-transfer and decoder-restart test (11 November 2026)

This test supersedes the earlier touch recommendation. [Full results](reports/touch-transfer/report.md), [fixed protocol](docs/touch-transfer-protocol.md), and aggregate JSON receipts under `reports/touch-transfer/`.

Ten SkillCorner matches use natural tracking as a harm check; five DFL/WCSF matches use stop75-jitter plus deterministic touch thinning to the provided track’s owned-touch rate as a gain check. Six variants also test resetting the existing decoder across gap-rule stoppages. Settings and gates were fixed before the single 90-case run; five additional natural-control scores serve reproduction only.

Provider ranges below use natural tracks. All provided-track information is bounded aggregates.

| Track | Observed share | Speed m/s | Surprise m/s | Owned/min visible | Surprise ≥3 share | Remote peak share | Bonus frames/owned touch |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Provided | 0.584179 | 5.108300 | 1.126769 | 10.457861 | 0.155712 | 0.297080 | 96.377125 |
| skillcorner (n=10) | 0.525990–0.643804 | 4.708561–5.217943 | 1.062871–1.201334 | 18.007388–21.637317 | 0.150967–0.175843 | 0.197628–0.231284 | 55.313980–61.575855 |
| dfl (n=4) | 1.000000–1.000000 | 0.000000–1.585172 | 0.000000–0.200539 | 17.501858–19.617192 | 0.089603–0.111106 | 0.090788–0.136697 | 45.627598–49.993754 |
| wcsf (n=1) | 1.000000–1.000000 | 1.592804–1.592804 | 0.112062–0.112062 | 21.271552–21.271552 | 0.121253–0.121253 | 0.129058–0.129058 | 43.945428–43.945428 |

S* = 1.126768830; R* = 10.457861445. All profile stop checks passed.

| DFL/WCSF scored track | Median surprise m/s |
| --- | --- |
| dfl-J03WN1 | 1.066647 |
| dfl-J03WOH | 1.062326 |
| dfl-J03WOY | 1.039035 |
| dfl-J03WR9 | 1.081570 |
| wcsf-used-match | 1.146687 |

| Group | Control | Candidate | Touch | Thin | Reset | Touch+reset |
|---|---|---|---|---|---|---|
| dfl_wcsf_primary | 0.343783 | 0.401270 | 0.477651 | 0.398301 | 0.418409 | 0.490677 |
| skillcorner_confirmation | 0.586912 | 0.584341 | 0.583469 | 0.570125 | 0.584341 | 0.583469 |
| skillcorner_development | 0.606222 | 0.603152 | 0.616479 | 0.600876 | 0.603618 | 0.616766 |

| Gate | Value | Pass |
|---|---|---|
| A | -0.000871 | True |
| B | -0.014216 | False |
| C | -0.002969 | False |
| D | +0.000000 | True |
| E | +0.018823 | True |
| F | +0.000000 | True |
| G | +0.000000 | True |

Recommended existing file: **candidate**, SHA-256 `31b947d3b250b6267a7d8f0aac0c4e4eafd82a4fc873c82759806e676b1bf963`. Decoder restart qualifies: **True**. The user chooses the submission; no file was regenerated. A qualified reset needs a separate release brief. All reproduction checks passed within 1e-9.

**Limits.** Every match has been scored before; touch settings were selected on five development SkillCorner matches and dfl-J03WN1. This is the third test of touch evidence and is post-hoc. SkillCorner references have no dead ball and longer possessions than the challenge. White noise and random thinning match two tracking statistics, not the causes of missing touches; real misses may be nonrandom. Touch gating sets contain five and three matches. Expected reset gain is about 0.01, below what two matches can confirm; gate E is a consistency check, not proof. The reset idea was chosen after a probe on nongating matches. The regime hides the ball up to two seconds after a restart, which may not match the provided track reacquisition delay.

The full report contains every match’s spell/macro scores, dead recall, spell counts, touch rates and bonus shares, reset changed shares and owner agreement, and the comparison with the earlier nongating probe. No public truth was opened or existing predictor changed. Both Desktop submission hashes are unchanged.
