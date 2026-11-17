# Four tactical goals: reasoning, measured results and limits

5 November 2026. The frozen tactical model improves agreement with the complete external provider scoring target and reduces undecided output on the local match. It is an **opt-in experiment**, not a promoted default. Local correctness was not measured. The final suite ran 183 tests successfully with two documented skips. The source, output and reports were installed and all 30 delivered file hashes verified, with the previous source backed up.

**Critical reference limitation:** a raw-data audit found that provider ball coordinates repeat the preceding contiguous frame on 449,536/449,539 inactive frames (99.9993%), versus 4,534/553,105 active frames (0.8197%). Finite coordinates therefore represent available numeric provider positions, not necessarily fresh observations. The tree's motion features can exploit this dead-ball coordinate freezing. Strong external D results may reflect that provider artifact; they do not establish robust transferable stoppage detection. The generation mechanism is undocumented in the checked primary paper.

H means home possession, A away possession, D dead ball and X undecided. A possession “spell” is one uninterrupted stretch belonging to one team. Reducing X creates more answers; it does not, by itself, show that those answers are correct.

| Requested goal | Result and completion boundary |
|---|---|
| Licensed external benchmark with exact official spell metric | Established with seven whole matches, recorded provenance, fixed splits and unchanged official scoring. |
| Diagnose dominant errors | External baseline exposes missing dead-ball detection and unsupported intervals; local aggregate diagnostics expose missing-ball and weak-support limits. Some flight/restart semantics remain unresolved. |
| Freeze an externally validated improvement | Selected using development/validation only, frozen before two final test matches, and improved both provider-reference tests. The coordinate artifact limits interpretation; challenge accuracy gain remains unverified. |
| Reduce high local X | X fell from 69.19% to 56.15% on the same declared match-frame scope, with no manual D interval. This measures coverage; local correctness remains unknown. |

## 1. Build a benchmark that measures the intended problem

The reference is *An integrated dataset of spatiotemporal and event data in elite soccer*, attributed to Bassek, Rein, Weber and colleagues, DFL / Sportec Solutions, Scientific Data 12, 195 (2025). Its [Figshare release](https://doi.org/10.6084/m9.figshare.28196177) uses [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/); the [primary paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC11787359/) documents collection and release. The acquisition record lists checksums and source URLs for 21 files. Transformations comprise coordinate/time normalization, separate feature/reference caches, and artificial observation masks for stress tests.

These are **provider reference labels**, not challenge gold or a separate video-verified possession study. Raw BallPossession 1/2 maps to H/A; inactive BallStatus 0 maps to D. Unknown codes remain unknown. Provider labels, event outcomes and target-derived availability never become inference inputs. The loader does not filter frames using the true live/dead state.

The split was fixed before scoring: train J03WOH/J03WOY/J03WPY/J03WMX; validate J03WQQ; final test J03WR9/J03WN1. Whole matches stay together. This avoids training on one part of a match and testing on nearly identical neighboring frames. Seven matches and recurring teams still provide limited evidence of generalization.

The benchmark uses the audited MIT-licensed official metric. The original upstream file's SHA256 is `341bad48904b489d6e875397b27687f5d6a4d22a397f3dc8af3a00d48f16874d`; this is not the hash of the vendored file with its appended license. Its ranking measure, `spell_f1_mean`, averages same-team spell matching F1 at interval-overlap thresholds .3/.4/.5/.6/.7. It uses greedy overlap matching. D is excluded from team spells. MacroF1 separately averages H/A/D frame F1.

Crucially, frame metrics penalize prediction X, while temporal metrics first fill X within valid reference runs. Merely assigning more raw frames can leave the effective spell prediction unchanged. Evaluation-only 26-frame X separators prevent filling or transition matching across halftime; they never enter production output. This preserves both the official implementation and original match indices.

## 2. Diagnose before choosing the improvement

On the four training matches, baseline spellF1 was approximately .342–.385 and X was 61.02–65.64%. Its most consequential structural weakness was that it never predicted D without separate supplied dead-ball evidence. Between 8,768 and 12,779 already-decided frames per training match incorrectly assigned H/A when the provider said D. Stationary proximity around a restart therefore could look like team control before play resumed.

Unsupported duration intervals and intervals with opposing team anchors dominated baseline X. This motivated a compact joint H/A/D model plus bounded continuity. Blanket filling could carry an owner across a turnover. Missing ball alone cannot establish possession or stoppage. The external natural data has continuously available finite ball coordinates, so masking tests examined numeric absence. The raw audit found no zero-coordinate sentinels; the XML `M` field means minute, not observation validity. Inactive coordinates can remain fixed while speed `S` stays nonzero, so neither finite XY nor supplied speed proves freshness.

The local camera aggregate explains why transfer is difficult: 64,643 of 158,857 declared match frames lack a raw tactical ball observation. Geometry-quality masking increases missing model-input ball frames to 66,056. The existing camera audit found no usable automatic tactical-to-broadcast clock alignment and made no possession changes. Camera fusion remains paused; no challenge video was checked for this work.

## 3. Select externally, freeze, then test

The selected decision tree has 31 nodes, depth four and a minimum training leaf size of 125. Its 18 inputs describe observed ball/teams, distances, ball speed and edge position, and recent control history. It uses neither Smart Tagging nor reference labels during selected inference. Training included natural data and deterministic 30% ball masking, with mask selection independent of reference classes.

Validation searched 24 predeclared combinations. The chosen policy requires leaf support at least .8 and a stable 12-frame run, with retained-owner gaps and same-owner bridges bounded to two seconds. Leaf support is a training-data proportion, **not a calibrated probability of correctness**. D requires available ball coordinates and both teams; external coordinate availability does not establish freshness. Stability confirmation can use later frames, so this is offline inference.

Selection required better validation spellF1, no worse macroF1, less X, sufficient newly resolved support and at least 90% pooled newly resolved correctness on natural and 30%-masked validation. The pooled correctness safeguard has a class-composition weakness described below. Model and policy were frozen at 08:45:13 UTC; final scoring began at 08:52:21 UTC. The report records no refitting after final tests.

| Natural held-out match | SpellF1 baseline → selected | MacroF1 baseline → selected | X baseline → selected |
|---|---:|---:|---:|
| J03WR9 | .38213 → .50428 | .41461 → .87529 | 58.46% → 8.86% |
| J03WN1 | .36509 → .50598 | .36282 → .84553 | 62.49% → 10.85% |
| Unweighted match mean | **.37361 → .50513** | **.38871 → .86041** | **60.47% → 9.86%** |

Both matches also improved spellF1, macroF1 and X under every declared 10%, 30% and 50% ball-mask regime. Mean selected spellF1 under those regimes was .46500, .40276 and .33147, versus .34313, .30681 and .24820 baseline. Artificial masking tests missing observations; it does not recreate realistic detection, calibration or identity errors.

The pooled 96.32% correctness on newly resolved natural-test frames is dominated by D and must not be read as general team-possession accuracy or artifact-independent detection:

| Newly assigned label | Frames | Agreement with provider |
|---|---:|---:|
| H | 30,613 | 86.36% |
| A | 8,653 | 88.95% |
| D | 106,644 | 99.78% |

There are regressions. Accuracy conditional on both sides calling play alive decreased from 93.75% to 92.11% on J03WR9 and 90.25% to 89.21% on J03WN1, while coverage-sensitive team accuracy improved. J03WR9 home-share error increased from .00505 to .07198. Previously decided predictions gained 27,317 corrections but incurred 92 regressions across the two tests. Improved headline metrics do not mean every tactical statistic improved. Within-match bootstraps are available, but do not establish generalization across unseen matches.

Post-freeze diagnosis excluded provider-inactive reference frames without changing predictions. Active-only spellF1 slightly **decreased**: .53842 → .53403 on J03WR9 and .53548 → .53490 on J03WN1. These scores do not establish improved H/A spell boundaries independent of D segmentation. A separate 30% whole-team-distance dropout stress test still improved complete-target spellF1 (.3492 → .4527 and .2823 → .3977), but it simulates missing geometry, not identity swaps or partial-player errors. These are diagnostics, not new selection criteria; no weights or thresholds changed.

Validation boundary diagnostics also show where work remains. Within one second of team changes, selected raw correctness was only 48.19%; around restarts it was 58.08%, and around stoppages 57.56%. These use provider-state boundaries. Ball-flight and stationary-ball groupings are observable proxies, not independently annotated physical events. The main delivered improvement is complete-target segmentation and coverage, with team-only boundary quality still unresolved.

## 4. Reduce local uncertainty without calling it accuracy

Frozen inference preserved all 199,319 original rows. Coverage uses the same 158,857 declared match-frame denominator before and after; “graded” in aggregate file keys is a frame scope, not evidence that local labels were scored.

| Local measure | Before | After |
|---|---:|---:|
| X frames | 109,917 | 89,200 |
| X share | 69.192% | 56.151% |
| Unresolved intervals | 1,045 | 509 |
| D predictions | 0 | 2,120 |

This is 20,717 net additional assignments, an 18.85% relative reduction in X. The earlier 67.74% figure included disputed manual-D/camera behavior; 69.19% is the comparable baseline excluding that shortcut. The selected route also applies quality masking and excludes unvalidated tags, so this operational comparison includes those changes. On identical model inputs, baseline X was 114,977; selected X remained 89,200.

Only 511 model-input missing-ball frames received team assignments. Remaining X is explained by 59,788 missing-ball/no-recent-owner frames, 26,572 below-support frames, 2,125 geometry-quality rejections, 685 unstable/conflicting frames and 30 missing-ball frames that cannot justify D. These sum to 89,200. Residual uncertainty is substantial and should remain visible.

Reference-free expansion changes 5,977 effective labels and team-spell count from 469 to 477. Those are behavior changes, not measured improvements. Neither challenge possession GT nor video was used for training, tuning, checking or scoring. Local X is higher and D prediction frequency differs; D correctness transfer cannot be measured without a local reference. No challenge accuracy or official challenge-score gain is claimed.

## Reproduction, evidence and delivery status

From the repository root (`pipeline-work` in the original local workspace), a fresh untouched reproduction workspace runs `acquire_external_reference.py`, `prepare_external_benchmark.py`, `run_external_baseline.py`, then `select_external_improvement.py`, followed by `evaluate_final_external.py`. Selection uses base Anaconda Python with `PYTHONPATH` set to the absolute `.training-deps` overlay; final evaluation uses `C:\Python314\python.exe`. Do not rerun selection against the existing freeze: it deliberately refuses. Preserve completed final reports rather than replacing them.

`export_frozen_runtime.py` and `build_standalone.py` export the selected tree into `football_pipeline.py`. Production inference is Python 3.9+ standard-library code; sklearn is development-only. The intended installed command is:

```powershell
conda activate football
python football_pipeline.py tactical run --data-dir "C:\football-data" --out outputs/tactical-validated
```

The aggregate verification command is `python verify_tactical_results.py`. The final full suite ran 183 tests successfully with two skips: opt-in full-index coverage and unavailable sklearn under Python 3.14. Three training/export tests passed separately with the isolated overlay, and all six CLI tests passed in the football environment with isolated standalone child processes. The bundle has exact parity across 20 modules and Python 3.9 syntax. The suite command is `C:\Python314\python.exe -m unittest discover -s tests`; training tests use base Anaconda Python, the overlay and `-p test_selection.py`. Windows fixture/OCR tests additionally need workspace TEMP/TMP, football `Library/bin` on PATH, its tessdata directory and an absolute `FOOTBALL_STANDALONE` path. `verify_four_goal_delivery.py` rechecks all 21 raw external file checksums, the freeze/source identity, bundle parity, output checksum, completed test log and each requested goal's evidence; it writes the completion audit without scoring challenge labels.

Fresh review found and fixed three input safeguards with failing-then-passing regression tests: negative homography error must be rejected; geometry evidence must reject injected dead labels; and the identical-input baseline must remove tags consistently. The actual local run had no negative errors and used the tracking route, so these fixes do not change its predictions. The final reviewer supports delivery only as an opt-in provider-validated experiment. No post-test physical-D gate was invented, and no default was promoted.

Authoritative development evidence: `../external-reference/provenance.json`; `reports/baseline-development-validation.json`, `reports/validation-selection.json`, `reports/final-heldout.json` and `frozen/{freeze-manifest,tactical-selected}.json` under `../external-reference`; and `../analysis/{tactical-validated/tactical_report,four-goal-coverage-verification,camera-analysis}.json`. The frozen artifact SHA256 is `be756fce3c52d21fda0b10d8a6026f78f9b7d599298d467d2d6ebc59efe9fd38`. The metric and external-reference audits in `docs/` explain semantics and leakage controls. No challenge assets or per-frame outputs were opened to write this report.

Installed in `C:\football-data\run files`: `football_pipeline.py`, `FOUR_GOALS.md`, `OFFICIAL_METRIC_LICENSE.txt`, the preserved `football_pipeline.pre_tactical.py`, five inference outputs in `outputs/tactical-validated`, and the provenance, frozen model, aggregate diagnostics, completion audit, figure and review/test evidence in `outputs/tactical-validation`. `delivery-verification.json` records installed hashes; `install_four_goal_results.ps1 -VerifyOnly` rechecks them from the development folder. Earlier pilot, camera and automatic-sync outputs remain in place. The single-file version is `2026.11.05-tactical-validated`; the new route requires the explicit `tactical run` command above.

The four requested workstreams are delivered with the boundaries in the first table. A separate blind test from another licensed provider is the next useful quality milestone. It should test team spells and physical dead-ball evidence before further reducing X or promoting this candidate. Lowering support thresholds on this match would not supply that missing evidence.

## Repository publication

This is the narrative record of the completed local work. Local evidence paths above refer to the original development layout; provided assets and per-frame outputs are intentionally absent from GitHub. The pinned external manifest, provenance and frozen artifact are archived in `benchmark/`; its README explains clean reproduction. `CHANGELOG.md` summarizes the direction change and proposed next work. The publication checkout additionally skips two delivery integration tests when their protected local fixtures are unavailable; the full local-delivery result remains 183 tests with 2 skips.
