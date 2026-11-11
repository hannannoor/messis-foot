# MESSI's FOOT

**11 November decision:** existing `candidate` file is recommended after the fixed touch-transfer test. Decoder restart qualifies: **True**; no reset release has been built. [Results and limits](reports/touch-transfer/report.md). The user makes the final submission choice.


An experimental local football-possession pipeline for More Than a Hack 2027.

**9 November frozen release candidate:** `competition_release.py` packages the unchanged `w0-c32-neutral-missing` control as a selected-only standard-library entry point. Two clean runs match both historical selected CSVs byte-for-byte; exact-file validation and one frozen public-window check are complete. Follow [reproduction instructions](docs/competition-release.md), [technical document](docs/competition-technical.md) and the [release decision/evidence](docs/competition-release-decision.md). Packaging is not a predictive improvement. The [performance history](docs/performance-history-and-next-step.md) records what was already tried and the bounded next diagnosis. Older routes below remain preserved.

**Ball-gap follow-up, 7 November:** [one fixed missing-evidence correction](docs/ball-gap-results.md) passed all predeclared checks on previously examined external validation/regression data. Masked SkillCorner frame accuracy improves75.78%→82.27%, while masked DFL stoppage recall improves92.64%→95.72%. Use the separate experimental `ball_gap_candidate.py`; the previous candidate remains preserved. These are seen-provider results, with target accuracy unmeasured. After one fresh review and fix pass:341tests OK,6skipped. The [review response](docs/ball-gap-code-review.md) records fixes, remaining limits and deferred minors.

**7 November update:** the [accuracy-first experiment](docs/accuracy-first-results.md) selected a finite H/A/D sequence decoder using the frozen tactical head (motion weight 0, switch cost 32). Natural seen-regression possession-spell F1 improves from 0.4977 to 0.5646; frame accuracy improves modestly on observed tracking but declines under the SkillCorner ball-gap stress. This is an experimental opt-in route, not fresh or target accuracy validation. The original pipeline, four-policy candidate and Desktop output are preserved. Software verification: 317 tests OK, 6 skipped.

Existing standalone source version: `2026.11.06-temporal-research`. The existing **opt-in tactical route** retains its frozen model and behavior. New motion adapters and an independent-provider experiment are documented in [TEMPORAL_RECOVERY.md](TEMPORAL_RECOVERY.md). The temporal candidate was rejected on validation; no new local inference policy is installed. This remains provider-reference research, with challenge accuracy unmeasured.

Read [RULES.md](RULES.md) before processing competition inputs. [CHANGELOG.md](CHANGELOG.md) explains what changed and why; [FOUR_GOALS.md](FOUR_GOALS.md) records reasoning, results, regressions and limitations.

## Submission candidate, 10 November: control + gap rule + kickoff patch

`gap_release.py` is the current submission entry point. It runs the unchanged frozen control (`w0-c32-neutral-missing`, artifact SHA-256 `e8d35e15be9524270bed82352791dc2849087b49b4c2b59c191023954b19eddb`, still the fallback), applies `gap_liveness.apply_gap_rule`, then `kickoff_patch.py`. Details, evidence and limitations: [DESIGN.md](DESIGN.md).

Regenerate the submission (new, nonexistent output directory; Python 3.14.5, standard library only):

```powershell
python -I gap_release.py --prefix "<dir>/BAR-ATH_tactical" --tags "<dir>/BAR-ATH_tactical_smart_tagging.xml" --out <new-dir>
```

Expected `submission.csv` SHA-256: `31b947d3b250b6267a7d8f0aac0c4e4eafd82a4fc873c82759806e676b1bf963` (199,319 rows; two independent runs were byte-identical; the official `validate_submission.py` passes).

## Alternative candidate, 10 November: observed-touch decoding (stoppage-regime test)

`touch_release.py` decodes the frozen control's emissions with observed-touch evidence (`predict_observed_touch(frames, 3, 2, 8)`), then applies the gap rule and the kickoff patch. The current candidate (`gap_release.py`, CSV `31b947d3…f963`) is unchanged and remains available. Results, regimes and limits: [DESIGN.md](DESIGN.md).

```powershell
python -I touch_release.py --prefix "<dir>/BAR-ATH_tactical" --tags "<dir>/BAR-ATH_tactical_smart_tagging.xml" --out <new-dir>
```

Expected `submission.csv` SHA-256: `1de96acb8ac2198c960637f6b20c2438c9ff142e76a9ab463c384b52814b8d14` (199,319 rows; two runs byte-identical; official validator passes). The user decides which file is submitted.

## What happened

- Full automatic camera processing produced no bounded clock alignment, so camera fusion was paused.
- Seven licensed external matches supplied a fixed split of four training, one validation and two test matches using the exact official spell metric.
- A frozen 31-node geometry/history tree improved complete provider-reference test spellF1 from **.37361 to .50513**, averaged over two matches.
- Local undecided coverage fell from **69.192% to 56.151%**, or 20,717 fewer X frames; unresolved intervals fell from 1,045 to 509. Local correctness was not measured.
- External inactive ball coordinates are almost always frozen. This can inflate D performance. Active-only spellF1 slightly declined on both held-out matches; the pooled 96.32% newly resolved agreement is dominated by D. H/A agreement was 86.36%/88.95%.

The independent-provider follow-up compared the old model on eight SkillCorner development matches: mean known-play spellF1 changed from.524729 to.527643 while unknown output fell from48.98% to23.01%. A new player-motion/temporal candidate was trained externally and rejected across the fixed27-policy validation grid. [The experiment report](TEMPORAL_RECOVERY.md) records the frozen diagnostic evaluation, simpler alternatives, review fixes and limitations. More assignments alone do not establish better possessions.

## Run one file

End users need only `football_pipeline.py`, Python 3.9+ and their local inputs. Tactical inference uses the standard library; it does not need sklearn, NumPy, a GPU or a hosted model.

```powershell
python football_pipeline.py --version
python football_pipeline.py tactical run --data-dir "C:\football-data" --out outputs/tactical-validated
```

The data directory may contain `tactical/` or `tactical cam/`, with tactical `_atd.xml`, `_atd.txt` and `_homography.csv` exports. Optional Smart Tagging is used only for baseline comparison, never the selected model's features. This route does not open videos, use challenge GT or apply the disputed fixed pre-kickoff D interval. It writes a separate protected output directory and reports remaining uncertainty.

The model uses a .8 leaf-support gate, 12-frame stable runs and bounded two-second owner continuity. Leaf support is not a calibrated correctness probability. Invalid, degenerate or excessive-error homographies mask the geometry. Missing ball/opponent observations cannot independently establish D. Offline confirmation can use later frames.

## Camera work and historical commands

```powershell
python football_pipeline.py camera demo
python football_pipeline.py camera auto-sync --help
python football_pipeline.py --guide
```

[AUTOMATIC_SYNC.md](AUTOMATIC_SYNC.md) documents automatic window/region selection, dense local OCR, half ambiguity and atomic output publication. Video OCR additionally requires FFmpeg/ffprobe and pretrained Tesseract English. The measured automatic run produced zero bounded links; it did not improve possession or verify replay/live status. Detailed camera exports remain local.

[TWO_CAMERA.md](TWO_CAMERA.md), [PROGRESS.md](PROGRESS.md) and older design notes preserve previous experiments, including manual setup and the disputed D shortcut. They are historical records. The explicit tactical route above excludes that shortcut; the legacy default has not been promoted or certified as a final entry.

## Development and reproducibility

The frozen inference sources match the embedded modules in the single-file program. Additional confidence/ensemble/materialization diagnostics run from the checkout and do not add prediction routes to that bundle. `build_standalone.py` uses the preserved code-only `football_pipeline.original.py` scaffold; `football_pipeline.pre_tactical.py` is the previous automatic-sync source backup.

The pinned external manifest, provenance and frozen model/policy are in [benchmark/](benchmark/README.md). Raw tracking, reference caches and frame-level predictions are obtained/generated locally outside the checkout. The external dataset is CC BY 4.0; preserve attribution and [the official metric's MIT license](OFFICIAL_METRIC_LICENSE.txt).

Training/reproduction was verified with Python 3.12, NumPy 1.26.4, SciPy 1.13.1, scikit-learn 1.5.1 and pandas 2.2.2. Use a separate environment and [requirements-training.txt](requirements-training.txt). The frozen artifact is retained; do not reselect or tune using held-out results or challenge coverage.

```powershell
python -m unittest discover -s tests
```

The6 November temporal-research milestone ran **243 tests successfully, with five skips** under Python3.14. The7 November additive diagnostics suite runs **278 tests, with the same five skips**: the opt-in full-index fixture, two training-only sklearn checks, and two local-delivery tests whose protected local artifacts are absent. Five temporal training/export/calibration/gate checks passed separately under Python3.12. The40-tree motion/decoder ran from the exact31-module frozen bundle under Python3.11 `-I -S` with no third-party runtime imports. OCR integration uses generated video and optional Pillow/FFmpeg/Tesseract; availability can change skip counts. See [VERIFICATION.md](VERIFICATION.md) and the separate diagnostic/audit reports for distinct author/reviewer checks.

`install_four_goal_results.ps1` and the delivery-verification utilities are local handover tools, not required for inference. They expect the completed local output/report layout; their integration tests skip when those private local fixtures are absent. `.gitattributes` preserves exact Python source bytes used by the frozen-source integrity checks.

## Data boundaries

Commit code, documentation, configuration, external model/provenance metadata and generated synthetic fixtures only. Keep provided footage, crops, tracking, tags, homographies, alignment maps, predictions and per-frame diagnostics local. No challenge assets or reconstruction-capable derivatives are included in this update.

Do not check predictions against provided video, create manual game labels/correspondences, upload provided assets to AI services, or train/tune/calibrate using challenge data. External provider labels are evaluation targets, not inference inputs. Aggregate coverage is not accuracy, and zero X alone does not guarantee a better official temporal score.

Experimental channel-contract candidate: see [input audit, reproducible command and limitations](docs/input-contract-candidate.md). This preserves the frozen baseline and reports carry separately from latent uncertainty.

The new opt-in sequence route uses `python soft_candidate.py --prefix "C:/football-data/tactical cam/BAR-ATH_tactical" --out "../soft-sequence-new-run"`. Use a fresh/empty output folder. See [results, commands and tradeoffs](docs/accuracy-first-results.md), [method](docs/accuracy-first-method.md) and [fresh review/fixes](docs/accuracy-first-code-review.md).

The separate missing-ball-neutral route uses `python ball_gap_candidate.py --prefix "C:/football-data/tactical cam/BAR-ATH_tactical" --out "../ball-gap-new-run"`. Preserve the earlier generation and use a fresh/empty output folder. Reproduce its fixed external comparison through `ball_gap_run.py`; the [results](docs/ball-gap-results.md) explain the serialization-only runner, remaining missed transitions and reference limitations.

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
