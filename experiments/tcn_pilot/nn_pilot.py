"""First TCN experiment on licensed external football tracking caches only.

Reproduces the local November 9 pilot. Do not use competition-match data here.
Run from the repository root:
    python -m experiments.tcn_pilot.nn_pilot
"""
from pathlib import Path
import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from gap_solver.core import Frame
from gap_solver.tactical import feature_rows, FEATURE_NAMES

TRAIN = ["J03WOH", "J03WOY", "J03WPY", "J03WMX"]
VALID = ["J03WQQ"]
TEST = ["J03WR9", "J03WN1"]

ROOT = Path(r"C:\football-nn\external-reference\cache")
OUTPUT = Path(r"C:\football-nn\nn-experiment")
OUTPUT.mkdir(exist_ok=True)

WINDOW = 256
EPOCHS = 8
BATCH_SIZE = 64

torch.manual_seed(42)
np.random.seed(42)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("Training device:", device)


def number(value):
    return float(value) if np.isfinite(value) else None


def distance(value):
    v = number(value)
    return v if v is not None and v >= 0 else None


def load_match(name):
    with np.load(ROOT / f"{name}.features.npz") as data:
        periods = data["periods"].copy()
        source_frames = data["source_frames"].copy()
        ball = data["ball_xy"].copy()
        distances = data["distances"].copy()

    with np.load(ROOT / f"{name}.reference.npz") as data:
        labels = data["reference"].astype(np.int64)
        assert np.array_equal(periods, data["periods"])
        assert np.array_equal(source_frames, data["source_frames"])

    # Same physical features used by the frozen tree; labels never enter features.
    frames = (
        Frame(
            period=int(periods[i]),
            ball_x=number(ball[i, 0]),
            ball_y=number(ball[i, 1]),
            home_distance=distance(distances[i, 0]),
            away_distance=distance(distances[i, 1]),
        )
        for i in range(len(periods))
    )
    x = np.asarray(list(feature_rows(frames)), dtype=np.float32)
    assert x.shape == (len(labels), len(FEATURE_NAMES))
    assert np.isfinite(x).all()

    # Class 3 (unknown) and ungraded frames must not contribute to loss.
    y = np.where((periods > 0) & (labels < 3), labels, -100)
    print(name, "loaded:", len(labels), "frames")
    return dict(x=x, y=y, periods=periods, frames=source_frames)


names = TRAIN + VALID + TEST
matches = {name: load_match(name) for name in names}

training_x = np.concatenate([
    matches[name]["x"][matches[name]["periods"] > 0]
    for name in TRAIN
])
mean = training_x.mean(axis=0)
std = training_x.std(axis=0)
std = np.maximum(std, 1e-6)
del training_x

for match in matches.values():
    match["x"] = np.clip(
        (match["x"] - mean) / std, -8, 8
    ).astype(np.float32)


def make_loader(selected, shuffle=False):
    xs, ys = [], []
    for name in selected:
        m = matches[name]
        p, f = m["periods"], m["frames"]
        start = 0
        n = len(p)
        for end in range(1, n + 1):
            boundary = (
                end == n
                or p[end] != p[end - 1]
                or f[end] != f[end - 1] + 1
            )
            if not boundary:
                continue
            if p[start] in (1, 2):
                for s in range(start, end, WINDOW):
                    e = min(s + WINDOW, end)
                    length = e - s
                    wx = np.zeros(
                        (len(FEATURE_NAMES), WINDOW), np.float32
                    )
                    wy = np.full(WINDOW, -100, np.int64)
                    wx[:, :length] = m["x"][s:e].T
                    wy[:length] = m["y"][s:e]
                    xs.append(wx)
                    ys.append(wy)
            start = end

    if not xs:
        raise ValueError("No valid training windows found")

    dataset = TensorDataset(
        torch.from_numpy(np.stack(xs)),
        torch.from_numpy(np.stack(ys)),
    )
    return DataLoader(
        dataset, batch_size=BATCH_SIZE, shuffle=shuffle
    )


train_loader = make_loader(TRAIN, shuffle=True)
valid_loader = make_loader(VALID)


class SmallTCN(nn.Module):
    def __init__(self, features):
        super().__init__()
        layers = []
        channels = features
        for dilation in [1, 2, 4, 8, 16]:
            layers += [
                nn.Conv1d(
                    channels, 32, kernel_size=3,
                    padding=dilation, dilation=dilation
                ),
                nn.ReLU(),
            ]
            channels = 32
        layers.append(nn.Conv1d(32, 3, kernel_size=1))
        self.network = nn.Sequential(*layers)

    def forward(self, x):
        return self.network(x)


model = SmallTCN(len(FEATURE_NAMES)).to(device)
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
criterion = nn.CrossEntropyLoss(ignore_index=-100)


def evaluate(loader):
    model.eval()
    confusion = np.zeros((3, 3), dtype=np.int64)
    with torch.no_grad():
        for x, y in loader:
            logits = model(x.to(device))
            predictions = logits.argmax(dim=1).cpu().numpy()
            targets = y.numpy()
            valid = targets != -100
            np.add.at(
                confusion,
                (targets[valid], predictions[valid]),
                1,
            )

    f1 = []
    for cls in range(3):
        tp = confusion[cls, cls]
        fp = confusion[:, cls].sum() - tp
        fn = confusion[cls, :].sum() - tp
        f1.append(2 * tp / max(2 * tp + fp + fn, 1))

    accuracy = np.trace(confusion) / max(confusion.sum(), 1)
    return float(np.mean(f1)), float(accuracy), f1


best_score = -1.0
best_weights = None

for epoch in range(1, EPOCHS + 1):
    model.train()
    loss_sum = 0.0
    for x, y in train_loader:
        x, y = x.to(device), y.to(device)
        optimizer.zero_grad()
        logits = model(x)
        loss = criterion(logits, y)
        loss.backward()
        optimizer.step()
        loss_sum += loss.item()

    macro_f1, accuracy, class_f1 = evaluate(valid_loader)
    print(
        f"Epoch {epoch}/{EPOCHS} | "
        f"Loss {loss_sum / len(train_loader):.4f} | "
        f"Val Macro-F1 {macro_f1:.4f} | "
        f"Val Accuracy {accuracy:.4f}"
    )
    if macro_f1 > best_score:
        best_score = macro_f1
        best_weights = {
            key: value.detach().cpu().clone()
            for key, value in model.state_dict().items()
        }

model.load_state_dict(best_weights)
checkpoint = OUTPUT / "tcn_pilot_best.pt"
torch.save(
    {
        "model_state": best_weights,
        "feature_names": FEATURE_NAMES,
        "mean": mean,
        "std": std,
        "train_matches": TRAIN,
        "validation_matches": VALID,
        "test_matches": TEST,
        "window": WINDOW,
    },
    checkpoint,
)
print("\nBest validation Macro-F1:", round(best_score, 4))
print("Saved:", checkpoint)

# Existing comparison matches; they were not a wholly fresh external test.
for name in TEST:
    macro_f1, accuracy, class_f1 = evaluate(make_loader([name]))
    print(
        f"TEST {name} | Macro-F1 {macro_f1:.4f} | "
        f"Accuracy {accuracy:.4f} | "
        f"H/A/D F1 {[round(v, 4) for v in class_f1]}"
    )
