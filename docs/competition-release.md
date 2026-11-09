# Frozen-control competition release

This entry point packages `w0-c32-neutral-missing` without changing its predictions. It requires local tactical EPTS exports and the Python standard library. The older `football_pipeline.py` and experimental candidates remain historical routes. The exact candidate revision and achieved delivery gates are recorded in [the release decision](competition-release-decision.md).

## Reproduce the artifact

The verified reference runtime is **CPython 3.14.5, Windows x64**. No pip packages, research receipts, training caches, unused temporal model or video tools are required for inference. Other platforms/versions are not certified by this release.

Use an exact-byte checkout so historical evidence checks are unaffected by Windows newline conversion:

```powershell
git -c core.autocrlf=false clone --branch codex/frozen-control-release-2026-11-09 https://github.com/hannannoor/messis-foot.git
cd messis-foot
python build_competition_release.py --check
python competition_release.py --version
```

Use the exact executable revision listed in the release decision when reproducing the candidate. The builder reads an explicit 13-module source map and emits deterministic artifact/manifest bytes. The manifest identifies selected sources and the frozen model; runtime does not verify unrelated research history. The new release reads raw inputs directly, so its identity does not depend on random research-cache UUIDs. Old cache seals remain unchanged.

## Generate the selected CSV

```powershell
python competition_release.py --prefix "C:/football-data/tactical cam/BAR-ATH_tactical" --out "C:/football-data/submissions/new-frozen-control-run"
```

The prefix must identify the original `_atd.xml`, `_atd.txt` and `_homography.csv` files. The output directory must not exist, including as an empty directory. The command writes only:

- `submission.csv`: exactly 199319 rows, original tactical frames 0..199318, `frame,label`, uppercase H/A/D/X, UTF-8 without BOM and CRLF line endings.
- `release-receipt.json`: input/source/model/semantic/label/CSV identities and bounded counts.

An `.incomplete` marker remains if a claimed generation fails. Keep it for diagnosis and use a new output path for retry. A complete generation has a valid receipt with matching CSV/label hashes and no marker. Outputs and raw inputs remain private. Rename a verified copy to the registered team's filename for submission; renaming does not change its bytes. Validate the exact file to upload.

## Verification

Synthetic fixtures check selected-path parity, missing/invalid inputs, unsupported blocks, float32 decisions, original indexing, deterministic build/CSV identity and overwrite/race protection. The full 199319-row fixture is generated data, not the challenge match. It proves a format contract, not possession correctness.

The official validator/scorer are pinned to `metrica-sports/more-than-a-hack-2027@f8f2629ff1e0985f81d7e59d8413678514ee1530`. For tests, stage only `games.py`, `LICENSE`, and `evaluation/{possession_metrics,validate_submission,run_evaluation}.py` at that revision in a local code-only directory. No GT, baselines or match assets are needed. The separate validator environment uses [requirements-release-check.txt](../requirements-release-check.txt): NumPy 2.5.1 and pandas 3.0.5. Inference does not use them.

```powershell
$env:FOOTBALL_OFFICIAL_CODE = "C:/local-tools/mtah-official-code"
$env:TEMP = Join-Path (Get-Location) '.tmp'
$env:TMP = $env:TEMP
$env:FOOTBALL_STANDALONE = Join-Path (Get-Location) 'football_pipeline.py'
New-Item -ItemType Directory -Force $env:TEMP | Out-Null
python -m unittest discover -s tests -p 'test_*.py'
python "$env:FOOTBALL_OFFICIAL_CODE/evaluation/validate_submission.py" "C:/football-data/submissions/new-frozen-control-run/submission.csv"
```

Windows filesystem-link tests require native link permissions. The release decision distinguishes code/synthetic verification, two real raw-to-identical-file generations, exact-file format validation and the single frozen public-window check. None substitutes for the others. A public-window result is a five-minute pipeline check; it must not select or tune models and does not estimate the hidden full-match score.

See the [technical document](competition-technical.md) for method, external training sources, possession conventions and limitations. Official [rules](https://github.com/metrica-sports/more-than-a-hack-2027/blob/f8f2629ff1e0985f81d7e59d8413678514ee1530/RULES.md) and [submission requirements](https://github.com/metrica-sports/more-than-a-hack-2027/blob/f8f2629ff1e0985f81d7e59d8413678514ee1530/SUBMISSION.md) govern final delivery.
