# MESSI's FOOT — possession labelling for More Than a Hack 2027

Every frame of the provided match (FC Barcelona – Athletic Club, 199,319 frames) labelled H, A, D or X by a fully
automatic pipeline. No model saw the provided match before inference, and nothing about it was labelled by hand.

## Submission

| File | What it is |
|---|---|
| [`technical-document.pdf`](technical-document.pdf) ([Markdown](technical-document.md)) | Approach, data, possession rules, evidence, limitations, reproduction |
| [`strong_release.py`](strong_release.py) | The command that regenerates the submitted `submission.csv` |
| [`strong_model/`](strong_model) | Model weights used by the submission (`gru.npz`/`gbm.npz` set A, `gru8.npz`/`gbm8.npz` set B) |
| [`requirements.txt`](requirements.txt) | Pinned inference dependencies (CPython 3.14.5, numpy 2.5.1) |
| [`development/`](development) | All other code, tests, design notes and reports (see below) |

Reproduce the submitted file. `$prefix` is the local prefix of the provided tactical files (for example
`.../BAR-ATH_tactical`) and `$out` a new output directory:

```powershell
pip install -r requirements.txt
python strong_release.py --prefix "$prefix" --tags "${prefix}_smart_tagging.xml" --out "$out"
```

Expected `submission.csv`: 199,319 rows, SHA-256 `ed97ae735a57e81dbd788f94c40de210dcbcb5aed40bc94d9552f1dade2897cd`.
Inference is deterministic plain numpy on CPU and takes under 10 minutes on a laptop. Then, from the challenge
repository: `python evaluation/validate_submission.py "$out/submission.csv"`.

## Approach in brief

Label-free geometry features (241 per frame) feed two sets of sequence models (bidirectional GRUs plus
gradient-boosted trees) trained only on public matches from other providers: 7 DFL, 10 SkillCorner and 1 WCSF match.
Their per-frame H/A/D evidence is decoded by a 3-state Viterbi decoder whose switch cost drops at detected ball
contacts and predicted possession boundaries. A label-free gap rule then turns long ball-tracking gaps with slow
players into dead ball, and graded frames before each half's kickoff tag become dead ball.

On external matches the models were never trained on, spell F1 is 0.783 on our five locked holdout matches
(against 0.536 for our first release); the organisers' published baseline on the provided match is 0.2433. Details, all
external checks and their limits are in the [technical document](technical-document.pdf).

## Repository layout

```
README.md, technical-document.*, requirements.txt, strong_release.py, strong_model/   the submission
development/
  *.py, gap_solver/     all modules: the release imports its runtime modules from here,
                        plus training (se_*.py) and earlier experiments
  tests/                unit tests (run from development/: python -m unittest discover tests)
  docs/                 results, design notes (docs/superpowers/specs/), earlier technical documents
  docs/history/         former README, changelog and project notes
  benchmark/, reports/  frozen protocols and published aggregate reports
  licenses/             third-party licences (official metric, baselines, datasets)
```

Training and research scripts are run from `development/`. They expect the downloaded external datasets in folders
next to `development/` (for example `strong-emissions-reference/`, `external-reference/`); those folders are ignored
by git. No match data, provided or external, is in this repository.

Earlier submitted versions (v1–v8 and the original decision-tree release) are listed with their hashes and commits in
[`development/docs/history/README-history.md`](development/docs/history/README-history.md).
