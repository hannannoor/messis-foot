# MESSI's FOOT

An experimental local football-possession pipeline for More Than a Hack 2027.

**7 November update:** the [accuracy-first experiment](docs/accuracy-first-results.md) selected a finite H/A/D sequence decoder using the frozen tactical head (motion weight 0, switch cost 32). Natural seen-regression possession-spell F1 improves from 0.4977 to 0.5646; frame accuracy improves modestly on observed tracking but declines under the SkillCorner ball-gap stress. This is an experimental opt-in route, not fresh or target accuracy validation. The original pipeline, four-policy candidate and Desktop output are preserved. Software verification: 317 tests OK, 6 skipped.

Existing standalone source version: `2026.11.06-temporal-research`. The existing **opt-in tactical route** retains its frozen model and behavior. New motion adapters and an independent-provider experiment are documented in [TEMPORAL_RECOVERY.md](TEMPORAL_RECOVERY.md). The temporal candidate was rejected on validation; no new local inference policy is installed. This remains provider-reference research, with challenge accuracy unmeasured.

Read [RULES.md](RULES.md) before processing competition inputs. [CHANGELOG.md](CHANGELOG.md) explains what changed and why; [FOUR_GOALS.md](FOUR_GOALS.md) records reasoning, results, regressions and limitations.

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
