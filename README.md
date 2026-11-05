# MESSI's FOOT

An experimental local football possession pipeline for More Than a Hack 2027. It combines tactical tracking, short-gap handling, clock OCR, candidate camera alignment and quality-gated broadcast evidence.

Current source version: `2026.11.05-clock-discovery`. Automatic clock-region discovery is now implemented. Possession inference remains the restart-audit version: restart repair raised resolved coverage from 22.00% to 30.81%; the earlier published D context raised it to 32.25%. Fusion added 13 raw labels but changed no scorer-expanded labels. Accuracy improvement has not been established.

Read [RULES.md](RULES.md) first. The latest organiser clarification supersedes earlier experiment guidance. Manual clock setup, the historical OCR-cutoff trial and the fixed D context must not be assumed eligible for a final entry. External training is required only if training is undertaken; it is not a mandatory project stage. The discovery addition changes no possession or fusion thresholds.

## Run one file

End users only need `football_pipeline.py`. Its modules load in memory; it does not extract a package or call a hosted model.

```powershell
python football_pipeline.py --version
python football_pipeline.py demo
python football_pipeline.py camera demo
python football_pipeline.py --guide
```

Python 3.9+ is required. Core inference and fusion use the standard library. Local video OCR additionally requires FFmpeg/ffprobe and Tesseract with English language data. This project does not require a GPU, TensorFlow or PyTorch.

For the previously used conda environment:

```powershell
conda activate football
```

## Automatic clock discovery

Scan each complete recording locally without drawing a clock box, choosing a half or finding a playback anchor:

```powershell
python football_pipeline.py camera discover-clock --video "C:\football-data\tactical cam\BAR-ATH_tactical.mp4" --out "outputs/tactical-discovery.json"
python football_pipeline.py camera discover-clock --video "C:\football-data\broadcast cam\BAR-ATH_broadcast.mp4" --out "outputs/broadcast-discovery.json"
```

The default samples every 30 seconds, searches the whole image using existing pretrained Tesseract and groups spatially stable progressing-clock observations. Images stream through memory and are discarded. Each command overwrites one small JSON report; it does not save a frame collection. Runtime depends on video decoding and OCR; no real-match runtime has been measured.

Blank prefixes/halftime, unreadable samples and multiple clocks remain automatic diagnostic states. Keep the detailed reports local. Discovery is the first automatic setup stage: **it does not yet create a dense alignment CSV, assign halves, verify live footage or change possession predictions**. Do not pass its JSON to `camera fuse`. Later dense synchronization and temporal replay checks are separate work. Defaults are engineering settings, not calibrated accuracy claims; any parameter tuning requires external data.

## Historical controlled comparison with existing alignment

This reproduces an engineering experiment, not a certified challenge-entry workflow. Existing alignment may depend on earlier manual setup, and the executable still applies the earlier organiser-answer D interval. See [RULES.md](RULES.md) before reusing these results.

Put the organiser-provided files on your own computer. Under `C:\football-data`, either `tactical/` and `broadcast/` or `tactical cam/` and `broadcast cam/` are supported by fusion. Each camera needs its `BAR-ATH_<source>_atd.xml`, `_atd.txt` and `_homography.csv`. Tactical Smart Tagging XML is optional.

From the folder containing the Python file and your existing `outputs/alignment.csv`:

```powershell
python football_pipeline.py camera fuse --data-dir "C:\football-data" --alignment "outputs/alignment.csv" --audit-baseline --out "outputs/ensemble"
```

This reuses cached alignment and opens no crop-selection window. It compares legacy tactical inference, repaired restart handling, the earlier organiser-answer pre-kickoff dead interval, and final broadcast fusion. The output folder is reused. [TWO_CAMERA.md](TWO_CAMERA.md) records the historical implementation; its manual setup is not the route for a final run under the new clarification.

## What is implemented

- Metre-scaled tracking adapters with original frame-index checks.
- Sustained team-control candidates and bounded same-team gap bridging.
- Soft restart-phase handling, explicit uncertainty and dead-evidence precedence.
- The published 2934-frame pre-second-kickoff D interval with separate provenance.
- Local clock OCR, saved clock crops, retries for weak readings and uncertainty-bounded timing.
- Candidate cross-camera matching, distinct-player geometry checks and heuristic weighted fusion.
- Shared mapped restart/dead context, detailed rejection reasons and missing-ball opportunity counts.
- Controlled baseline comparisons, including changes after the scorer expands X labels.

The modules in `gap_solver/` and tests are retained for development; their code matches the modules embedded in the standalone file.

## Verification

From a repository checkout:

```powershell
python -m unittest discover -s tests
```

The current suite ran 124 tests: 123 passed and the opt-in full-index test was skipped. The 27 discovery tests include real local FFmpeg/Tesseract execution on generated video and regressions from independent review. The earlier restart version also passed the opt-in full-index synthetic integration. Optional OCR integration uses Pillow, FFmpeg/ffprobe and Tesseract and is skipped when dependencies are unavailable. The full-index test generates complete synthetic camera exports and needs no match assets:

```powershell
$env:FOOTBALL_SLOW_TESTS = "1"
python -m unittest discover -s tests -p test_controlled_cli.py
Remove-Item Env:FOOTBALL_SLOW_TESTS
```

To exercise the standalone entry point in that integration as well, set `FOOTBALL_STANDALONE` to the absolute path of `football_pipeline.py`. See [VERIFICATION.md](VERIFICATION.md) for the development record.

## Status and evidence

- [PROGRESS.md](PROGRESS.md): development history, measured pilot coverage and pending work.
- [COUNCIL_AUDIT.md](COUNCIL_AUDIT.md): audit conclusions and implementation priorities.
- [DESIGN.md](DESIGN.md): tactical inference design.
- [TWO_CAMERA_DESIGN.md](TWO_CAMERA_DESIGN.md): alignment and fusion design.

The current system is a heuristic prototype. A nearest-player control candidate is not verified possession, OCR scores are not calibrated correctness probabilities, and a matching clock does not prove the pictures are live. Dedicated replay detection, general stoppage detection and validated longer-gap inference remain unfinished.

## Data boundaries

Only code, documentation, configuration and generated synthetic test fixtures belong in this repository. Obtain competition assets separately and keep videos, crops, tracking, tagging, homography, alignment maps, predictions and frame-level diagnostics local. Do not commit match data or reconstruction-capable derivatives.

Do not check predictions against the provided video, create manual game data or upload provided data to AI services. Training, fitting, calibration and tuning require permitted external data, never provided ground truth or video. Earlier manual clock setup and video-informed OCR experiments are historical, not a compliance claim. See [RULES.md](RULES.md). Coverage and synthetic test success are not accuracy measurements.
