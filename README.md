# MESSI's FOOT

An experimental local football possession pipeline for More Than a Hack 2027. It combines tactical tracking, short-gap handling, clock OCR, candidate camera alignment and quality-gated broadcast evidence.

Current source version: `2026.11.02-restart-audit`. The real pilot completed; the updated controlled restart comparison is ready for a local run. Accuracy improvement has not been established.

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

## Run the controlled comparison with existing alignment

Put the organiser-provided files on your own computer. Under `C:\football-data`, either `tactical/` and `broadcast/` or `tactical cam/` and `broadcast cam/` are supported by fusion. Each camera needs its `BAR-ATH_<source>_atd.xml`, `_atd.txt` and `_homography.csv`. Tactical Smart Tagging XML is optional.

From the folder containing the Python file and your existing `outputs/alignment.csv`:

```powershell
python football_pipeline.py camera fuse --data-dir "C:\football-data" --alignment "outputs/alignment.csv" --audit-baseline --out "outputs/ensemble"
```

This reuses cached alignment and opens no crop-selection window. It compares legacy tactical inference, repaired restart handling, the organiser-published pre-kickoff dead interval, and final broadcast fusion. The output folder is reused on later runs. For initial clock extraction, ROI selection and alignment, read [TWO_CAMERA.md](TWO_CAMERA.md).

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

The last implementation verification passed 96 routine tests plus the opt-in full-index synthetic integration. Optional OCR integration uses Pillow, FFmpeg/ffprobe and Tesseract and is skipped when those dependencies are unavailable. The full-index test generates complete synthetic camera exports and needs no match assets:

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

No competition-game manual labels or corrections are used. The public five-minute labels are for pipeline sanity checks, not training, tuning or model selection. Changes to inference quality require independent evaluation on permitted other-match data. Coverage and synthetic test success are not accuracy measurements.
