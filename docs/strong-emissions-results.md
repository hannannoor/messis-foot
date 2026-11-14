# Strong emission model: results (14 November 2026)

## Headline
On **locked external holdout matches**, chosen before any modelling and scored once, the provider-weighted spell F1 went from **0.536 to 0.726 (+0.190)**. Every one of the 5 holdout matches improved:

| Holdout match | Release | New | Δ |
|---|---:|---:|---:|
| DFL J03WN1 | 0.529 | 0.736 | +0.207 |
| SkillCorner 2013725 | 0.597 | 0.787 | +0.191 |
| SkillCorner 2016236 | 0.591 | 0.743 | +0.152 |
| SkillCorner 2017461 | 0.536 | 0.736 | +0.199 |
| WCSF (closest analogue) | 0.505 | 0.687 | +0.182 |
| **Provider-weighted** | **0.536** | **0.726** | **+0.190** |

On the dev matches (grouped 4-fold, held-out folds only), the score went from 0.584 to 0.772, and all 13 matches improved.

## What changed
- **Before:** a 31-node decision tree with 18 features, fitted on 4 DFL matches. It feeds per-frame H/A/D evidence into the release decoder chain.
- **After:** the same unchanged decoder chain (decode → gap rule → restart → gap rule → kickoff patch), fed by a much stronger evidence model:
  - **155 geometry features per frame:** k-nearest ball distances per team, players within 2/5/10 m, ball velocity in each team's attacking frame, closing speeds, player speeds, last and next "touch" team and timing, missing-ball timing, and past/future window summaries out to ±15 s.
  - **Bidirectional GRU** (GPU, 2 layers, 128 hidden), 2 seeds. SkillCorner rows supervise H vs A only, because SkillCorner has no D labels; DFL/WCSF rows supervise H/A/D.
  - **Gradient-boosted trees:** two heads, ownership and live/dead.
  - **Home/away swap augmentation** with swap-averaged inference, so the model is team-symmetric.
  - **Combination:** equal-weight geometric blend, squared before decoding (`power 2`). That's the same as halving the switch cost, chosen on dev.
- **Training data:** external only. Fourteen matches go into the holdout model (dev set; WCSF and the other holdout matches excluded). The final submission model uses all 18 external matches (7 DFL, 10 SkillCorner, 1 WCSF).

## Rule compliance
- No fitting, tuning or selection used BAR–ATH ground truth or video. BAR–ATH is used only for inference.
- The only checks on BAR–ATH are aggregate input-shift statistics and a label-mix comparison with the old release.
- Nothing was uploaded anywhere.

## Why it works (diagnosis)
- The old tree missed most short possessions on DFL: 35 of 41 true spells under 1 s. It also over-fragmented SkillCorner, with 318 predicted spells against 250 true.
- The GRU sees exact timing around touches and fixes both.
- Dead-ball detection on DFL was already about 99% and stays there.

## Submission (swapped in 14 November 2026, on the user's go-ahead)
- One command: `python strong_release.py --prefix <BAR-ATH_tactical> --tags <..._smart_tagging.xml> --out <new dir>`. Runs on CPython 3.14 + numpy with deterministic CPU inference.
- Output SHA-256: `853d4e7c13de10e920fa6ded3225fedac03763b600c8e4552d27ee56847fea01`. Two independent runs are byte-identical, and they match the GPU-built CSV. The official `validate_submission.py` returns OK.
- Installed at `MESSI's FOOT/final-submission/submission.csv` with its receipt. The previous release CSV (SHA `15756bcb...`) is kept in `final-submission/previous-release/` for rollback.
- Exported weights match the trained models: boosted trees exactly (≤ 2e-16); the GRU to 8e-4 in probability, with 99.998% of frames getting the same top label.
- Code: branch `experiment/strong-emissions` (worktree `MESSI's FOOT/strong-emissions-work`). It is not pushed or merged.

## Caveats
- External matches are not BAR–ATH. Its tracking is from a tactical camera, with the ball observed in 58% of active frames. Input features sit within about 1 SD of the external data.
- The decoder still treats missing-ball rows as neutral, the release's policy. That is a possible next gain.
