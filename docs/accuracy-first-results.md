# Accuracy-first results —7 November2026

The approved 16-setting experiment found an experimental improvement in possession-spell quality. The selected setting is **motion weight 0, switch cost 32**, using the existing tactical head with finite three-state temporal decoding. The motion head did not improve the winning setting in this bounded grid; this does not prove that motion information is generally useless.

The current four-policy route and Desktop baseline remain preserved. A separate standard-library `soft_candidate.py` is the experimental opt-in route. There is no fresh full-state holdout and no measured target accuracy.

## Predeclared selection and frozen regression

The16 settings, code/model/input identities and input-only missing-ball stress were frozen before candidate scoring. Selection used only the three previously examined validation matches. After selecting the winner, one frozen comparison used ten previously examined old test matches as **seen regressions**, with no further search. Each provider receives equal weight, then matches within provider receive equal weight. The primary objective is official team-possession spellF1; macroF1 breaks ties.

| Stage / input regime | Agreement + carry spellF1 | Soft sequence spellF1 | Change |
| --- | ---: | ---: | ---: |
| Seen validation / natural | 0.527184 | 0.627686 | +0.100502 |
| Seen regression / natural | 0.497704 | 0.564642 | +0.066938 |
| Seen regression / masked | 0.432350 | 0.460077 | +0.027727 |

| Seen regression / provider | Input | Existing frame accuracy | Soft frame accuracy | Existing spellF1 | Soft spellF1 |
| --- | --- | ---: | ---: | ---: | ---: |
| dfl | natural | 92.47% | 92.83% | 0.524728 | 0.553665 |
| skillcorner | natural | 85.03% | 85.82% | 0.470680 | 0.575619 |
| dfl | masked | 83.08% | 84.40% | 0.404160 | 0.432684 |
| skillcorner | masked | 80.95% | 75.78% | 0.460539 | 0.487471 |

The largest documented tradeoff is the SkillCorner ball-gap stress: mean frame accuracy falls from80.95% to75.78%, although spellF1 improves. Fewer fragmented possessions can improve the primary score while mislabelling more individual frames. This is not a universal accuracy upgrade and is not a reason to hide that stress result.

On natural seen regression, the candidate corrected2332 previously decided wrong DFL labels while regressing1572 correct ones; SkillCorner counts were10428 corrections versus6475 regressions. These counts concern previously decided incumbent rows only. They do not cover all changes to previously uncertain rows. Per-class confusions, overlap-based split/merge diagnostics and all per-IoU matched/spurious/missed counts remain in the aggregate case receipts.

## Why it changed the result

Gap-only aggregation cannot repair an existing wrong H/A/D label. Finite soft evidence can reconsider it, while the state-switch cost discourages short contradictory runs. This bounded experiment points to sequence consistency as useful with the existing raw tactical head. It does not establish optimality of32 or exclude better models outside the grid.

No head was refitted. The original confidence-gated temporal artifact remains rejected under its original protocol. The winning new method uses no motion-head contribution for selected predictions; the older head remains available for the original four comparator outputs. Leaf support is not calibrated correctness probability.

## Applicability and evidence limits

All reference matches in this cycle were already used in earlier project analyses. These are exploratory seen-data results, not a new holdout or evidence of target correctness. DFL includes a frozen-inactive-ball-coordinate shortcut; SkillCorner labels known-play H/A only and cannot independently test D. Some external25Hz player coordinates were interpolated using provider identities. Fresh full H/A/D reference acquisition remains unresolved.

The decoder is H/A-equivariant when its emission columns are exchanged in a unique-optimum case. The retained tactical model itself is asymmetric, so the complete pipeline is not guaranteed to reverse labels when team identities are exchanged. Per-team confusions and results are retained rather than claiming end-to-end symmetry.

## Commands

```powershell
python accuracy_experiment.py freeze
python accuracy_experiment.py prepare --workers 2
python accuracy_experiment.py validate --workers 2
python accuracy_experiment.py select
python accuracy_experiment.py regress --workers 2
python accuracy_experiment.py summarize

python soft_candidate.py --prefix "C:/football-data/tactical cam/BAR-ATH_tactical" --out "../soft-sequence-new-run"
```

Use a fresh dedicated output folder for each soft-candidate run. The new route preserves all original indices and the four comparator CSVs. `submission.csv` contains the selected soft sequence after explicit structural-period carry. `uncertainty.csv` keeps latent X/barrier and materialization flags; a carried D in a wholly unknown period is a convention, not observed dead ball. Outside structural half windows remains X. Sources, models and current Desktop outputs are preserved.

External intermediate archives and per-frame predictions remain local under `accuracy-reference/`. Published results contain only scalar/count diagnostics, bounded confusion matrices and input/source hashes. The [method](accuracy-first-method.md), approved design, implementation plan and review response explain the scope and reproducibility constraints.

## Boundary timing and missed transitions

The fixed-winner supplemental check uses the unchanged official 25-frame (1s) tolerance here; the receipt also includes12 frames (0.48s). On natural DFL seen regression, mean boundary F1 changes0.6323→0.6160 while spurious boundaries fall399→242 and missed boundaries rise387→483. On SkillCorner, mean boundary F1 changes0.3209→0.3436, spurious boundaries fall2332→1424 and missed boundaries rise623→752. Smoothing removes false cuts but can erase genuine short changes. These tradeoffs accompany the possession-spell gain.

Mean absolute timing error among matched boundaries changes0.237s→0.177s for DFL and0.366s→0.338s for SkillCorner. These are means of per-match errors conditional on matching, not timing accuracy for missed boundaries; the counts and F1 must be read alongside them. No event locations or new hyperparameter choice are published.

## Evidence re-entry after review

The exact scored engine is preserved as `accuracy_experiment_frozen.py`. The public `accuracy_experiment.py` now adds strict source/model/input/archive checks and verifies the existing selection from the original natural validation receipts without rewriting it. Portable logical-key comparison preserves the original Windows-spelled freeze and digest. `verification-source.json` seals this additive guard and the original evidence. Use the public wrapper; the preserved engine is an audit artifact.

```powershell
python accuracy_experiment.py verify
python accuracy_experiment.py boundaries --workers 2
```

Exact warm-evidence verification needs the original intermediate score archives referenced by the receipts; those private/local arrays are excluded from publication. The target-inference command uses committed frozen models and settings and does not require those external evaluation archives.

The soft route requires a fresh/empty output directory and rejects original four-policy generations byte-for-byte. Latent X records input inapplicability, not every kind of model uncertainty; an emitted H/A/D score is not calibrated confidence. The review's source-binding, publication-shape and ownership regressions passed. One minor positive-path CLI unit-fixture extension remains deferred and is documented in the review response.

## Final execution checks

The full suite passed 317 tests with 6 documented skips. Two clean target runs produced identical hashes for all 6 CSV files and both selected 199319-row files passed the unchanged official format-only validator. All four comparator CSVs exactly match the prior candidate, which remains byte-for-byte intact;34 frozen sources/models and the Desktop pipeline are unchanged.

Selected target CSV SHA256: `7014e1acff292e9f726b720bddc8ab10e98d0321a08ea5271b6047771a113d5a`. There are 5735 latent input-inapplicable active rows, explicitly materialized in the final file. This is an execution/format diagnostic, not a measurement of target correctness or calibrated uncertainty. No target labels/video were checked. Isolated Python3.11 `-I -S` standard-library synthetic runs match; the added sources also parse under Python3.9 grammar. Python3.9 grammar compatibility is not an execution test on that interpreter.
