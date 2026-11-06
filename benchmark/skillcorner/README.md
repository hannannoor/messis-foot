# Independent-provider temporal benchmark

Source: [SkillCorner/PySport Open Data](https://github.com/SkillCorner/opendata/tree/4340d274572876239c154c90bc507a9b3250a656), pinned revision4340d274572876239c154c90bc507a9b3250a656. Preserve its MIT licence and attribution. The pinned README says10 matches, but its tree contains20 tracking exports. `protocol.json` records every selected public object, checksum, licence and the split fixed before scoring. No raw tracking or per-frame targets/predictions belong here.

Use Python3.12 with `requirements-training.txt` for development. The scripts place raw/cached data in `independent-reference`, a sibling of the checkout. Downloads comprise20 tracking files plus match metadata/phases and licence documents, about1.82GB of tracking. No dynamic event outcomes, videos or body-pose inputs are used.

```powershell
python acquire_skillcorner.py
python prepare_skillcorner.py --split all --regime detected
python prepare_skillcorner.py --split validation --regime available
```

The prior frozen DFL model is the baseline. Reproduce its licensed source directory using `../README.md`, including the archived `benchmark/frozen` artifact and provenance, before the independent comparison. Its six protected source hashes remain unchanged.

For a new untouched development run (never reselection from final scores):

```powershell
python run_skillcorner_baseline.py
python select_temporal_recovery.py prepare
python select_temporal_recovery.py train
python select_temporal_recovery.py validate
python select_temporal_recovery.py select
```

Feature/mask inputs are independent of reference phases. Known H/A phases are scoring/supervision targets; phase absence/conflicts are X, not D. Detected-only positions are primary. Available/extrapolated positions are an explicitly labelled ablation. The25Hz scorer timeline retains native10Hz provenance; interpolation never bridges missing native detections. Unknown target intervals remain holes in the unchanged official scoring timeline.

The published candidate is rejected before testing. To reproduce its **frozen diagnostic evaluation**, restore the archived model and freeze, prepare verified detected caches, and keep its exact policy. Source identities and stable raw-input/adapter contracts must match; cache generations verify their own paired array hashes, and score checkpoints bind the actual generation. Do not refit from final scores or claim its diagnostic report validates local use.

```powershell
$researchRoot = Join-Path (Split-Path -Parent (Get-Location)) 'independent-reference'
$temporalRoot = Join-Path $researchRoot 'temporal'
New-Item -ItemType Directory -Path $temporalRoot -Force
Copy-Item benchmark/skillcorner/trained-draft.json (Join-Path $temporalRoot 'trained-draft.json')
Copy-Item -Recurse benchmark/skillcorner/frozen (Join-Path $temporalRoot 'frozen')
```

```powershell
python evaluate_temporal_final.py test
python evaluate_temporal_final.py available
python evaluate_temporal_final.py stresses
python evaluate_temporal_final.py seen-dfl
python evaluate_temporal_final.py summarize
```

Only a fresh complete review permits creation of a new freeze with `freeze_temporal.py --review <receipt>`. Final evaluation gives one worker ownership of both regimes per match, preserves identical completed checkpoints and refuses stale identities. Summary requires all declared test/stress/ablation/seen-regression receipts. A validation rejection remains rejected after final testing. See [TEMPORAL_RECOVERY.md](../../TEMPORAL_RECOVERY.md) for actual results, reasoning and limitations.
