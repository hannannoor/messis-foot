# Temporal neural-network pilot (9 November 2026)

This directory archives the first **TCN** possession experiment on permitted external DFL/Sportec matches. It does not alter the frozen submission pipeline.

## Files

- `nn_pilot.py`: supervised PyTorch temporal CNN trained on external geometry-derived features; saves locally to `C:\football-nn\nn-experiment\tcn_pilot_best.pt`.
- `nn_compare.py`: compares the frozen tactical tree, raw TCN, and TCN plus the incumbent decision policy using `gap_solver.official_metrics.evaluate`.

Execute from the repository root in the `football-nn` environment:

```bat
python -m experiments.tcn_pilot.nn_pilot
python -m experiments.tcn_pilot.nn_compare
```

These scripts use the local external-reference caches in `C:\football-nn\external-reference\cache` and require numpy, PyTorch and the project's existing modules. The paths reflect the original Windows experiment and may need adjustment on another machine. The training and comparison scripts are archived from the locally tested versions; the copies on GitHub have not been re-run here.

## Experiment protocol

- Training matches: `J03WOH`, `J03WOY`, `J03WPY`, `J03WMX`
- Checkpoint-selection validation match: `J03WQQ`
- Prior-used external comparison matches: `J03WR9`, `J03WN1`
- Targets: 0=home, 1=away, 2=dead; 3=unknown/excluded.
- Feature inputs: 18 engineered geometry features from `gap_solver.tactical.feature_rows`. No provider labels in prediction features.
- Network: five Conv1D+ReLU layers, channels=32, dilations 1/2/4/8/16, kernel=3; 3-class head.
- Optimization: cross-entropy, Adam learning rate 0.001; 8 epochs; window length 256 frames, batch size 64; selection by frame macro-F1 on validation.
- Training-only standardization; windows do not cross periods or source-frame gaps.

## Observed results (copied from local console output)

Training used CUDA. Best validation **frame macro-F1**: **0.9212**.

| External comparison match | Model | Frame macro-F1 | Spell-F1 mean | Transition-F1 (12 frames) | Predicted / true spells |
| --- | --- | ---: | ---: | ---: | ---: |
| J03WR9 | Frozen tree | 0.8753 | 0.5043 | 0.4559 | 401 / 370 |
| J03WR9 | Raw TCN | 0.9193 | 0.4857 | 0.4929 | 428 / 370 |
| J03WR9 | TCN + existing policy | 0.9020 | 0.5257 | 0.4871 | 413 / 370 |
| J03WN1 | Frozen tree | 0.8455 | 0.5060 | 0.5052 | 436 / 500 |
| J03WN1 | Raw TCN | 0.8933 | 0.5010 | 0.5107 | 458 / 500 |
| J03WN1 | TCN + existing policy | 0.8666 | 0.5254 | 0.5181 | 447 / 500 |

These are **external provider-reference agreement**, not challenge scores. The TCN plus policy exceeded the frozen tree by about 0.02 Spell-F1 on each comparison match. This is below the scorer's documented ~0.04 Spell-F1 noise band, so the evidence is inconclusive. The raw TCN's higher frame F1 did not produce higher spell F1 than the tree.

## Important limitations

1. The two comparison matches had previously influenced the team's research; they are **not independent untouched final tests**. Stop model selection on those matches. New architectures should use training/validation data and later additional external matches.
2. The external provider often holds ball coordinates fixed during inactive play; extremely high D agreement may exploit this dataset-specific convention and may fail to transfer.
3. Inference uses non-overlapping windows, which can cause boundary discontinuities. The Conv1D receptive field is only 63 frames.
4. The current pilot is a classifier, **not** a world model. Rich individual-player trajectories and masked predictive training are proposed future work, not implemented here.
5. The trained checkpoint is **not included in this GitHub branch**; it remains at `C:\football-nn\nn-experiment\tcn_pilot_best.pt` on the original machine unless separately committed.
6. Don't train, tune, manually annotate, verify against challenge video, or upload provided competition footage/tracking to AI services. Only allowed external datasets should be used for training/tuning.

## Next research direction

Recover permitted **full player trajectories** from external raw data, then compare a player-interaction / masked-prediction representation model plus possession head against this TCN. Evaluate robustness to masked ball observations and measure spell-level quality before any submission integration.
