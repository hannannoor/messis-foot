"""Comparison of frozen decision tree, raw TCN and TCN with existing policy.

External comparison data only. Requires the locally saved pilot checkpoint.
Run from the repository root:
    python -m experiments.tcn_pilot.nn_compare
"""
from pathlib import Path
import numpy as np
import torch
from torch import nn

from gap_solver import official_metrics as metrics
from gap_solver.external import load_cache
from gap_solver.tactical import (
    FEATURE_NAMES, Policy, infer_tactical,
    feature_rows, apply_policy
)
from gap_solver.tactical_model import FROZEN_MODEL

ROOT = Path(r"C:\football-nn\external-reference\cache")
CHECKPOINT = Path(
    r"C:\football-nn\nn-experiment\tcn_pilot_best.pt"
)

TEST_MATCHES = ["J03WR9", "J03WN1"]
device = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)
print("Device:", device)

# Load only a locally produced, trusted checkpoint.
ckpt = torch.load(
    CHECKPOINT, map_location="cpu", weights_only=False
)

assert tuple(ckpt["feature_names"]) == FEATURE_NAMES
WINDOW = int(ckpt["window"])
mean = np.asarray(ckpt["mean"], dtype=np.float32)
std = np.asarray(ckpt["std"], dtype=np.float32)


class SmallTCN(nn.Module):
    def __init__(self, features):
        super().__init__()
        layers = []
        channels = features
        for dilation in [1, 2, 4, 8, 16]:
            layers += [
                nn.Conv1d(
                    channels, 32,
                    kernel_size=3,
                    padding=dilation,
                    dilation=dilation
                ),
                nn.ReLU()
            ]
            channels = 32
        layers.append(nn.Conv1d(32, 3, kernel_size=1))
        self.network = nn.Sequential(*layers)

    def forward(self, x):
        return self.network(x)


model = SmallTCN(len(FEATURE_NAMES))
model.load_state_dict(ckpt["model_state"])
model = model.to(device)
model.eval()

code_map = {"H": 0, "A": 1, "D": 2, "X": 3}


def decision_codes(decisions):
    return np.array(
        [code_map[d.label] for d in decisions],
        dtype=np.int8
    )


def boundaries(periods, source_frames):
    cuts = np.flatnonzero(
        (periods[1:] != periods[:-1]) |
        (source_frames[1:] != source_frames[:-1] + 1)
    ) + 1
    ends = np.concatenate((
        [0], cuts, [len(periods)]
    ))
    return list(zip(ends[:-1], ends[1:])), cuts


@torch.no_grad()
def tcn_probabilities(raw_x, periods, source_frames):
    x = np.clip(
        (raw_x - mean) / std, -8, 8
    ).astype(np.float32)

    probabilities = np.zeros(
        (len(x), 3), dtype=np.float32
    )
    blocks, _ = boundaries(periods, source_frames)
    windows = []
    locations = []

    # Match the training script's non-overlapping windows.
    for start, stop in blocks:
        if periods[start] not in (1, 2):
            continue
        for s in range(start, stop, WINDOW):
            e = min(s + WINDOW, stop)
            window = np.zeros(
                (len(FEATURE_NAMES), WINDOW),
                dtype=np.float32
            )
            window[:, :e-s] = x[s:e].T
            windows.append(window)
            locations.append((s, e))

    for start in range(0, len(windows), 64):
        batch = np.stack(windows[start:start+64])
        tensor = torch.from_numpy(batch).to(device)
        result = torch.softmax(
            model(tensor), dim=1
        ).permute(0, 2, 1).cpu().numpy()
        for j, (s, e) in enumerate(
            locations[start:start+64]
        ):
            probabilities[s:e] = result[j, :e-s]
    return probabilities


def evaluate_method(gt, pred, cuts):
    # Add ungraded separators at period/frame discontinuities.
    gt_scored = np.insert(gt, cuts, metrics.X)
    pred_scored = np.insert(pred, cuts, metrics.X)
    return metrics.evaluate(
        gt_scored, pred_scored, bootstrap_n=0
    )


def print_result(name, result):
    print(
        f"{name:22s} | "
        f"Spell-F1: {result['spell_f1_mean']:.4f} | "
        f"Macro-F1: {result['macro_f1']:.4f} | "
        f"Spells: {result['n_pred_spells']}"
        f"/{result['n_gt_spells']} | "
        f"Transition-F1: "
        f"{result['transitions'][12]['f1']:.4f}"
    )


policy = Policy(**FROZEN_MODEL["policy"])

for match_id in TEST_MATCHES:
    print(f"\n{'=' * 75}")
    print("MATCH:", match_id)
    match = load_cache(ROOT / match_id)
    frames = match.frames()

    periods = np.asarray(match.periods)
    source_frames = np.asarray(match.source_frames)
    gt = np.asarray(match.reference, dtype=np.int8)
    assert np.isin(gt, [0, 1, 2, 3]).all()
    gt[~np.isin(periods, [1, 2])] = metrics.X

    raw_x = np.asarray(
        list(feature_rows(frames)), dtype=np.float32
    )
    probs = tcn_probabilities(
        raw_x, periods, source_frames
    )

    # Model A: existing frozen tree and selected decision policy.
    tree_decisions = infer_tactical(
        frames, FROZEN_MODEL["model"], policy
    )
    tree_pred = decision_codes(tree_decisions)

    # Model B: direct TCN predictions.
    raw_pred = np.full(
        len(periods), metrics.X, dtype=np.int8
    )
    active = np.isin(periods, [1, 2])
    raw_pred[active] = np.argmax(
        probs[active], axis=1
    ).astype(np.int8)

    # Model C: TCN with exactly the existing decision policy.
    tcn_decisions = apply_policy(
        frames, zip(raw_x, probs), policy
    )
    policy_pred = decision_codes(tcn_decisions)

    _, cuts = boundaries(periods, source_frames)
    for name, pred in [
        ("Frozen decision tree", tree_pred),
        ("Raw neural network", raw_pred),
        ("Neural net + policy", policy_pred),
    ]:
        result = evaluate_method(gt, pred, cuts)
        print_result(name, result)
    print("Finished:", match_id)

print("\nCOMPARISON COMPLETE")
print("No challenge data was used.")
