# External benchmark archive

This folder contains the primary Figshare manifest, acquisition provenance and the immutable selected artifact/freeze manifest. It contains no raw match tracking, label cache or challenge output.

Dataset: Bassek, Rein, Weber and Memmert (2025), *An integrated dataset of spatiotemporal and event data in elite soccer*, Scientific Data 12, 195; DFL / Sportec Solutions. [Primary release](https://doi.org/10.6084/m9.figshare.28196177), [paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC11787359/), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Transformations include coordinate/time normalization, separate feature/reference caches and synthetic observation masks. The exported model is derived from these external data; preserve this attribution.

The fixed split is development J03WOH/J03WOY/J03WPY/J03WMX, validation J03WQQ, test J03WR9/J03WN1. Provider labels are not independently verified competition gold. Frozen inactive coordinates can inflate stoppage performance; see [FOUR_GOALS.md](../FOUR_GOALS.md).

The scripts use `external-reference` and `analysis` as **siblings of the checkout**. For a fresh Python 3.12 environment with `requirements-training.txt`, prepare the external directory from PowerShell:

```powershell
$externalRoot = Join-Path (Split-Path -Parent (Get-Location)) 'external-reference'
New-Item -ItemType Directory -Path $externalRoot -Force
Copy-Item benchmark/figshare-manifest.json (Join-Path $externalRoot 'figshare-manifest.json')
python acquire_external_reference.py
python prepare_external_benchmark.py
python run_external_baseline.py
```

Downloads comprise 21 licensed XML files, about 2.63 GB. Acquisition verifies their recorded checksums. Keep completed raw files/caches local. To evaluate the already frozen candidate without fitting:

```powershell
# Use a fresh external directory with no existing frozen/ or final-heldout report.
Copy-Item -Recurse benchmark/frozen (Join-Path $externalRoot 'frozen')
python evaluate_final_external.py
python export_frozen_runtime.py
python build_standalone.py
```

The manifest verifies six source hashes as well as the artifact. Preserve source bytes using the committed `.gitattributes`. `evaluate_final_external.py` checks validation reproduction before opening test results and caches its completed terminal report. The archived artifact ID is `be756fce3c52d21fda0b10d8a6026f78f9b7d599298d467d2d6ebc59efe9fd38`.

To reproduce selection itself, use a separate untouched workspace: after acquisition, caching and baseline scoring, run `select_external_improvement.py` instead of restoring the freeze, then final evaluation. Selection deliberately refuses an existing freeze. Never refit from held-out scores or challenge summaries.

Two development-tool interruption limits remain documented in the [review disposition](../docs/four-goal-final-review.md): checksum-invalid EOF partial downloads may need preservation/renaming before a clean retry, and interrupted held-out JSON checkpoints may need the same treatment. Neither affected the verified archived result. Do not overwrite a completed final report or use retries to reselect a model.
