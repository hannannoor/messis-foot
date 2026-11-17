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

## v2 (15 November 2026)
Changes, each tested on dev cross-validation (13 matches) against the v1 recipe (0.7723):
- **Short-possession weighting:** GRU ownership loss weight is `clip(50 / spell frames, 1, 4)`. In a matched single-model comparison (same seed and steps) it moved dev from 0.7587 to 0.7675.
- **Missing-ball rows:** the decoder now keeps model evidence there (weight 1; the release used 0). This adds roughly +0.001 to +0.003.
- **Switch cost:** 32 → 20.
- **Blend result:** dev 0.7723 → 0.7827 (+0.010). Nine matches are better and four worse; the worst is −0.010.
- **Rejected:** cost 10 (dev +0.012, but a worse tail and DFL-only gain), H/A-only missing-ball evidence (no better), a separate dead-ball switch cost (no gain), and a wider GRU (too slow). Training-budget scaling was deferred at the user's request.
- **Holdout (second look, so supporting evidence only):** 0.7262 → 0.7420 (+0.016). WCSF went 0.687 → 0.709 and DFL J03WN1 0.736 → 0.760; 4 of 5 matches improved, and the worst is −0.008.
- **Submission:** SHA-256 `edc50685…`. Two CPU runs are byte-identical, it agrees with the GPU path on all but 1 of 199,319 frames, and the official validator says OK. 98.3% of frames are the same as v1.

## v3 (15 November 2026): robustness to missing ball
- **Finding:** BAR–ATH sees the ball on only 58% of active frames. Every D-labelled training match sees it on about 100%, WCSF included. To simulate BAR–ATH, we dropped the ball on DFL dev matches (about 42% missing, gap lengths sampled from SkillCorner dev) and recomputed all features.
  - Under that degradation, v2 fell from 0.78 to **0.48**, and the old release to 0.35.
  - Cause: the models had learned "ball missing ⇒ dead ball" (99% of missing-ball live frames were predicted D).
- **Fix:**
  - Train with ball-dropout copies of the D-labelled matches, using different masks from evaluation, applied to 50% of GRU chunks and as extra GBM rows.
  - Drop the gap rule, which now hurts: degraded 0.587 before it runs and 0.552 after.
- **Dev:** clean 0.7812 (v2 0.7827, within noise). Degraded DFL **0.590** (v2 0.483).
- **Holdout:** clean 0.7463 (v2 0.7420). Degraded WCSF **0.591** (release 0.395); degraded DFL J03WN1 **0.526** (release 0.349).
- **Rejected this round:**
  - short D breaks at touch flips (council idea): every setting was flat or worse, because false splits dominate;
  - a stronger augmentation dose (80%): no better.
- **Submission:** SHA-256 `27b4e25c…`. CPU runs are byte-identical, it is identical to the GPU path, and the official validator says OK. The D share of non-X frames on BAR–ATH falls from 45% (v2) to 38.5%.

## v4 (15 November 2026): ball-impulse contact features
- **New contact detector:** a touch is a local peak of ball-velocity change over ±2 frames, at least 4 m/s, with a player within 2 m, computed on 5-frame smoothed ball positions.
  - It finds about 1,600 contacts per DFL match.
  - The touch team agrees with the true owner 0.2 s later 96% of the time.
  - The old proximity proxy marked 52,000 "near" frames.
- **16 new features:** last and next contact team, timing and confidence; a team flip; impulse size; and per-team contact counts in ±0.5 s and ±1 s.
- **Dev:** clean 0.7812 → **0.7980**. DFL rose 0.777 → 0.813 (all 6 matches up); SkillCorner was flat (0.785 → 0.784). Degraded DFL 0.590 → **0.599** (5 of 6 up).
- **Holdout (confirmation):** clean 0.7463 → **0.7587**. DFL J03WN1 went 0.759 → 0.796 and WCSF 0.721 → 0.724; SkillCorner moved −0.004 on average. Degraded: WCSF 0.597, DFL J03WN1 0.556.
- **Submission:** SHA-256 `a2761b6a…`. CPU runs are byte-identical, it differs from the GPU path on 1 frame, and the official validator says OK.

## v5 (15 November 2026): player-only team-shape features for long ball gaps
- **Diagnosis:** in degraded DFL dev, about 89% of missing-ball errors sit in gaps longer than 10 s. No ball feature exists inside such a gap.
- **New features (241 in total):**
  - **64 team-shape features.** Each team is described in its own attacking frame:
    - Shape: centroid depth, defensive-line depth, length and width.
    - Movement: mean forward velocity, counts of forward and backward runners (> 3 m/s).
    - Marking: mean distance to the nearest opponent.
    - Windows: ±2/5/15 s means.
    - Example (one dev match): the team in possession is about 9 m wider (46.8 m against 37.6 m).
  - **6 contact-reliability features.** A contact is reliable only when the ball is observed for ±5 frames, so smoothing never straddles an observation edge. 3.7% of degraded contacts were edge artefacts; clean data has none.
- **Decoder:** switch cost 10 within ±6 frames of an impulse contact, 20 elsewhere.
- **Blend:** 0.3 × v4 set + 0.7 × v5 set (geometric). The v4 set keeps clean DFL, and the v5 set carries ball-loss robustness.
- **Dev cross-validation (13 matches):**

| Candidate | Clean | DFL | SkillCorner | Degraded DFL |
|---|---:|---:|---:|---:|
| v4 | 0.7980 | 0.8125 | 0.7836 | 0.5990 |
| v4 + touch cost | 0.7989 | 0.8150 | 0.7828 | 0.6025 |
| v3/v4 blend (rejected) | 0.7985 | 0.8095 | 0.7875 | 0.5994 |
| v5 set alone + touch cost | 0.8002 | 0.8061 | 0.7943 | 0.6643 |
| **v5: 0.3 v4 + 0.7 v5 set + touch cost** | **0.8027** | 0.8087 | 0.7968 | **0.6643** |

- **Spread across matches:** degraded data improved on all 6 DFL matches, by +0.044 to +0.061 each. On clean data the worst match is −0.011 (DFL J03WPY).
- **Ablation (single GRU, same seed and steps as v4's gru13):**
  - reliability features only: clean 0.7836, degraded 0.5911. That's noise.
  - reliability + team-shape: clean 0.7789, degraded **0.6442** (gru13: 0.7819 / 0.5991).
  - Boosted trees: degraded 0.573 → 0.644.
  - So the gain comes from team shape.
- **Holdout (fifth look, confirmation only):** clean 0.7587 → **0.7652**.
  - WCSF 0.724 → 0.738, DFL J03WN1 0.796 → 0.804, SkillCorner 0.756 → 0.754.
  - Degraded: WCSF 0.597 → **0.670**, DFL J03WN1 0.556 → **0.635**.
- **Submission:** SHA-256 `f4d3d940…`. Two CPU runs are byte-identical, the GPU path agrees on all 199,319 frames, and the official validator says OK. 96.2% of frames match v4.

## v6 (15 November 2026; submitted after the investigation): three independent ball-dropout views per match
- **Change:** each D-labelled match now has 3 dropout copies (independent masks, SkillCorner dev gap statistics) instead of 1.
  - Each GRU training chunk picks one copy; the boosted trees weight the 3 copies together like the single copy.
  - Steps, seeds and features are the same as v5.
- **Rejected:** ±30 s and shape-extent window features (64 more). GRU clean dropped −0.008; the boosted trees showed no gain.
- **Dev cross-validation:**
  - one GRU: degraded 0.644 → 0.667, clean 0.779 → 0.777;
  - full blend: clean 0.8027 → 0.8005 (SkillCorner −0.005), degraded DFL 0.6643 → **0.6762**, up on 5 of 6 matches.
- **Holdout (sixth look; go/no-go was SkillCorner no worse than −0.005):**
  - clean 0.7652 → **0.7672**; SkillCorner +0.006 (pass), WCSF +0.003, DFL −0.003.
  - degraded 0.6522 → 0.6507: WCSF 0.670 → 0.668, DFL 0.635 → 0.633.
  - The degraded gain seen on dev did not replicate on the 2 degraded holdout matches. v6 is a small, low-confidence step over v5.
- **Submission:** SHA-256 `e2ff053d…`. Two CPU runs are byte-identical, the GPU path agrees on all frames, and the official validator says OK. 98.6% of frames match v5.

- **Decision (user and Claude, 15 November):** keep **v5** as the submission.
  - v6's changes against v5 are within noise and point both ways.
  - Its one larger gain (degraded dev +0.012) comes from the simulated ball loss, the least trustworthy proxy, and it did not replicate on the holdout.
  - v6 code paths (`aug_views`, `xdrop`, `team_shape_ext_features`) stay in the repo as options. The v6 weights are in commit 480ee92, and its CSV is in `final-submission/previous-v6/`.
  - Adoption rule from now on: a change must also gain on real missing-ball data (SkillCorner) and on the holdout, not only on simulated degradation.

## Investigation: was v6 real? (15 November 2026, dev only)
- **New ball-loss evaluation views** on the 6 DFL dev matches:
  - 2 more masks from the same generator;
  - 2 real SkillCorner gap layouts transplanted onto the DFL matches (`se_degrade.py`, `evalr*`).
- **Retrained models:** v4, v5 and v6 recipes, both seeds plus boosted trees, with fold predictions on every view. Retraining reproduced the original scores exactly. Comparison tool: `se_noise.py`.
- **Full-blend result, v6 against v5:**
  - ball-loss views: +0.009 to +0.015, with the two real-layout views at +0.013 ± 0.003 and +0.010 ± 0.005;
  - clean: −0.0025 ± 0.0027.
- So the gain is not simulator-specific. The holdout's −0.0015 on 2 degraded matches is about −1.8 SE from the dev expectation: noise more likely than a defect.
- **Mask noise:** one model's ball-loss score moves 0.644–0.679 across masks, so absolute ball-loss numbers carry about ±0.015 uncertainty. Paired comparisons are much tighter.
- **Touch-aware cost:** re-checked on all views, +0.002 to +0.006. Kept.
- **Status:** v5 remains submitted pending the user's decision. v6 is fully built (commit 480ee92, CSV in `final-submission/previous-v6/`).

## Round 7: trying to improve v6 (15 November 2026, dev only, five-view protocol)
- **Re-checked v5-era settings on v6:** v4 weight {0, 0.15}, switch cost {16, 24}, power {1.5, 2.5}. All within about ±0.003 of v6's current settings; none clears the bar (every view ≥ 0 and 3 of 5 views ≥ 2 SE).
- **5 dropout copies instead of 3** (two seeds): +0.012 on the original mask but about 0 on the other four views. Diversity saturates at 3.
- **Dropout copies for SkillCorner matches** (two seeds): +0.001 to +0.004 on most views, never ≥ 2 SE.
- **Lesson:** single-seed gains of about 0.005 (clean and SkillCorner) disappeared with a second seed. Decisions at this effect size need two seeds and all five views.
- **Result:** no v7. v6 is the best-supported candidate.

## Decision: v6 submitted (15 November 2026, user's go-ahead)
- The investigation showed v6's ball-loss gain holds on real SkillCorner gap layouts, and round 7 found nothing better.
- `final-submission/submission.csv` is v6 (SHA-256 `e2ff053d…`), and v5 is kept in `final-submission/previous-v5/`.
- The branch rebuilds v6 byte-identically, and the official validator says OK.

## v8 (16 November 2026, submitted): player-dropout robustness + possession-boundary head
- **Recon (aggregate input statistics only):** BAR–ATH tracks 10.1 players per team. No player is missing on about 63% of frames per team, 1 on 21%, and 3 or more on about 6%. The missing player is usually the most extreme along the pitch. DFL and WCSF always have 11.
- **Stress test:** run-based player dropout on top of ball loss (`cases_evalp`, `cases_evalrp`) cost v6 about 0.03.
- **Changes:**
  1. Training copies with ball and player dropout (`cases_augp*`). The v4 set weight is cut to 0.15 because it is far weaker with the ball missing.
  2. A 4th GRU output trained to predict possession boundaries (λ 0.3). The decoder lowers the switch cost toward 8 where it fires.
  3. Restart / set-piece features were tested and rejected (within noise).
- **Dev, v8 against v6:**
  - clean +0.008 ± 0.004;
  - 5 ball-loss views +0.005 to +0.013 (average 0.691 → 0.700);
  - 2 ball + player views +0.022 and +0.019, 6/6 matches each (0.664 → 0.684).
- **Holdout (eighth look):** clean 0.767 → **0.783**; ball loss 0.651 → **0.669**.
- **Submission:** SHA-256 `bbc77547…`. CPU runs are byte-identical, the GPU path differs on 1 frame, and the official validator says OK. v6 is kept in `final-submission/previous-v6/`.
- **New tooling:** CV fold models are saved; `se_predict.py` scores new views without retraining.

## v9 (16 November 2026, submitted): Metrica evaluation and the gap rule
- **Fresh evaluation:** 3 public Metrica sample games, already acquired with pinned hashes, with event-derived labels. Every released version was scored once with its exact runtime:

| | Release | v2 | v4 | v5 | v6 | v8 | **v9** |
|---|---:|---:|---:|---:|---:|---:|---:|
| Metrica mean | 0.568 | 0.765 | 0.739 | 0.741 | 0.747 | 0.752 | **0.794** |

- **Why:** real ball loss is state-dependent.
  - Metrica: 79–89% of dead frames have no ball, against 7–16% of live frames.
  - BAR–ATH inputs: missing on 77% of "still" frames against 19% of "moving" frames.
  - Random-gap simulation (used since v3): 47% against 47%.
- **The gap rule** (label-free; gap > 3 s with below-typical player speed → D), applied on the main decode, then the kickoff patch:
  - on Metrica: changes 3–5% of frames, 83–90% of the changes correct, +0.042 (3/3 games);
  - clean dev −0.001;
  - on BAR–ATH: changes 4.5% of frames (7,193, all live → D), within Metrica's range.
- **Submission:** SHA-256 `ed97ae73…`. Two CPU builds byte-identical, validator OK, and the model supports are identical to v8's. v8 is kept in `final-submission/previous-v8/`.
- **Paused:** leave-one-game-out training with Metrica (baseline trained; held-out runs stopped). Do not resume as configured; see round 10.

## Round 10 (16 November 2026): audit, and a corrected Metrica yardstick
Details: `docs/superpowers/specs/2026-11-16-round10-audit-fixes-design.md`. No change to the submission.
- **The round 9 Metrica evidence for the gap rule is circular.** In the sample games the ball is an in-play flag: it disappears one frame after play stops (80–90% of stoppages) and returns on the restart frame (84–99%). All 22 players are always tracked. The +0.042 is true by construction there, so 0.794 is not an estimate for BAR–ATH.
- **The event-derived reference was wrong in both directions:** 11–22 stoppages per game kept as H/A, and 14–17 long stretches per game kept as D while play went on. 11–14% of frames change label under the corrected reference.
- **Corrected reference:** dead ball from the ball flag, owners from events (`metrica_ball_reference.py`). The honest score on it is **ownership-only** (dead-ball calls taken out):

| | Release | v2 | v4 | v5 | v6 | v8 | v9 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Metrica ownership-only | 0.631 | 0.835 | 0.870 | 0.866 | 0.867 | **0.878** | **0.878** |

- v8 is best on all three games and v2 falls to fifth, which matches dev CV. v9 equals v8 here by design.
- **BAR–ATH inputs** (no labels): 150 ball gaps, 133 over 3 s, 85% of missing frames in gaps over 10 s. But the ball is lost slow and in-field (fast when lost 6%, against 55–65% in Metrica), so its gap edges are probably not dead-ball edges. v9 keeps the gap rule on the grounds that long gaps are overwhelmingly stoppages; the timing of D at gap edges is untested on any data we hold.
- **Bug found, not yet fixed:** `se_sym.py` line 50 leaves the 8 `nearH_*` window features wrong in the swapped view on 8–27% of rows (checked against truly mirrored frames; the other 233 features are exact). The fix goes into the next retrain.
- **Tooling:** dev comparisons now score the submitted `gapko` stage by default; the random-loss views are legacy.
