# Round 10: fixes from the 16 November audit

## Why
- The audit found that the Metrica sample games cannot tell us what round 9 used them for.
  - Their ball is an in-play flag: it disappears one frame after the dead-ball start in 80–90% of stoppages and returns on the restart frame in 84–99%. All 22 players are tracked on every frame.
  - The event-derived reference (`metrica_event_reference.py`) is wrong in both directions.
    - It keeps H/A through 11, 20 and 22 stoppages per game (3–10% of frames), because only ball-out and foul events count as stops.
    - It keeps D through 14–17 long stretches per game where the ball is in view and passes are being played (5,000–13,000 frames; the longest is 160 s), because a foul with advantage never gets a restart.
- The dev tooling still scores the `nogap` decoder stage, not the submitted `gapko`.
- One home/away swap bug is confirmed (`se_sym.py`, the 8 `nearH_*` window features).

## Goal
1. A Metrica reference whose dead-ball labels come from the ball flag, and a rescoring of every release against it, in full and ownership-only.
2. Dev tooling that scores the submitted decoder.
3. Then (separate steps, each reported before the next): a retrain with state-dependent degradation and the swap fix; leave-one-game-out with Metrica as ownership-only supervision; D-start timing on WCSF.

## Non-goals
- Changing the submission in this step. Steps 1 and 2 change scoring and tooling only.
- Hand labels, video, or anything from BAR–ATH ground truth.

## Anti-goals
- Choosing the reference's thresholds by which release they favour. They are fixed below from gap structure alone, before any rescoring.
- Reading the new full-metric Metrica score as evidence about dead-ball detection. With D taken from the ball flag, any missing-ball rule is right there by construction. Only the ownership-only score is evidence.
- Using the public 5 minutes to test whether dead ball equals ball gap on BAR–ATH.

## Holdouts
- The three Metrica games stay evaluation-only in steps 1 and 2. The old locked five are not used.

## Approaches
1. **(Picked) New ball-flag reference beside the old one** (`metrica_ball_reference.py`). The old builder stays untouched so round 9 numbers remain reproducible.
2. Patch the event reference with more stop subtypes: rejected. It fixes missed stoppages case by case and does nothing about false D after an advantage.
3. Drop Metrica as evidence altogether: rejected. It is the organiser's own event convention and the only fresh data for ownership.

## The reference (fixed before rescoring)
- Ball-missing runs, from the structure of the three games (48–56 runs of 12 frames or fewer per game, none at a set piece; 90–99 runs of 75 frames or more, most ending on a set-piece start):
  - 25 frames or more: dead ball (D).
  - 13–24 frames: unknown (X). There are 2–7 per game.
  - 12 frames or fewer: tracking glitch; the current owner carries.
- Owners come from events exactly as before (pass, carry, recovery, shot, ball lost, ball out at their start; a decided challenge at its end; a set piece at its start).
- Entering a dead-ball run clears the owner. It is set again by the next set piece or owner event.
- An event stop (ball out, foul, goal) while the ball is still in view is D only if a dead-ball run or a set piece follows before the next owner event. If play goes on instead, those frames become X.

## Scores reported
- **Full:** official spell F1 against the new reference. Reported for completeness; see the anti-goal.
- **Ownership-only:** the prediction takes the reference's D frames as D, and abstains (X, forward-filled by the scorer) wherever it said D on a reference-live frame. This measures H/A possessions under Metrica's event convention with dead-ball detection taken out.
- Old-reference scores are reprinted to confirm the pipeline reproduces round 9.

## Left to the builder
- Module and test layout; how the rescoring script reuses the saved round 9 predictions and supports.

## Result of steps 1 and 2 (16 November)
- **Code:** `metrica_ball_reference.py` (8 unit tests), `se_load.load(cid, reference='ball')`, `se_metrica_rescore.py`. No inference was re-run: saved round 9 label arrays, plus the saved v8 supports decoded with `gapko` for v9.
- **Pipeline check:** the old event reference reproduces every round 9 number exactly, and the saved v8 labels are reproduced from the saved v8 supports.
- **How much the reference moved:** 15,881, 19,238 and 15,446 frames per game changed label (11%, 14% and 11% of frames).

| Version | Event reference (round 9) | Ball-flag reference, full | **Ownership-only** (games 1 / 2 / 3) | Ownership-only mean |
|---|---:|---:|---|---:|
| Old release | 0.568 | 0.609 | 0.632 / 0.638 / 0.624 | 0.631 |
| v2 | 0.765 | 0.816 | 0.838 / 0.799 / 0.866 | 0.835 |
| v4 | 0.739 | 0.776 | 0.865 / 0.856 / 0.889 | 0.870 |
| v5 | 0.741 | 0.788 | 0.863 / 0.852 / 0.883 | 0.866 |
| v6 | 0.747 | 0.792 | 0.866 / 0.852 / 0.884 | 0.867 |
| v8 | 0.752 | 0.799 | 0.870 / 0.864 / 0.901 | **0.878** |
| v9 | 0.794 | 0.853 | 0.870 / 0.864 / 0.901 | **0.878** |

- **Ownership-only is the evidence.** With dead-ball calls taken out, v8 is the best release on all three games, v2 drops to fifth, and the order matches dev CV. v2's round 9 lead came only from calling D where the ball flag was off.
- **v9 equals v8 on ownership** by design: every frame the gap rule changes lies inside a ball gap, which this reference calls D.
- **The full ball-flag column is not evidence for the gap rule** (see the anti-goal). It shows v9's D recall against the flag is 0.97–0.98, against 0.82–0.90 for v8.
- **Still weak:** possessions of 1 s or less are found 33–46% of the time by v8, and v8 predicts 3–6% fewer possessions than the reference (359/380, 341/363, 400/410).
- **Tooling:** `se_noise.py` and `se_summ.py` now default to the `gapko` stage, `se_score2.py` prints and saves it, and the random-loss views are marked legacy. Dev score files written before v9 have no `gapko` entry and need one `se_score2.py` pass before the next comparison.
- **Release unchanged:** only docstrings were edited in `strong_release.py` and `strong_runtime.py`; a rebuild from the working tree gives the same CSV hash (`ed97ae73…`).

## Step 3 result: dead-ball timing on WCSF (16 November)
- **Holdout change:** the user released `wcsf-used-match` from the locked holdout to dev on 16 November. The holdout is now the other four matches.
- **Saved labels, no new inference:** `H_v8@2` for WCSF (v8), and dev CV `F8r15@2` for two DFL matches (the restart-feature variant of v8, within noise of it; the frozen-ball result does not depend on which):

| | WCSF | DFL J03WR9 | DFL J03WOH |
|---|---:|---:|---:|
| Ball exactly still on dead frames | 19% | 100% | 100% |
| Stoppages of 2 s or more never called D | 14 of 101 | 0 of 92 | 2 of 100 |
| D starts more than 0.5 s late | 26% | 0% | 0% |
| D ends more than 1 s early | 25% | 0% | 0% |
| Spell F1 as predicted | 0.764 | 0.821 | 0.861 |
| … with D start fixed | 0.792 | 0.821 | 0.861 |
| … with D end fixed | 0.798 | 0.821 | 0.861 |
| … with both edges fixed | 0.826 | 0.821 | 0.861 |
| … with all reference D imposed | 0.851 | 0.821 | 0.867 |
| Ownership-only | 0.853 | 0.824 | 0.868 |

- **DFL teaches nothing about stoppages.** Its ball is frozen on every dead frame, so D edges are predicted to the exact frame.
- **On WCSF, dead-ball handling costs 0.09 spell F1:** 0.06 from edges (late starts, early ends) and 0.03 from stoppages never called. Late starts are the previous possession running on (76 of 78), and v8 predicts 465 possessions against 411.
- **Caveat:** WCSF's ball is not frozen but it is nearly still from the first two seconds of a stoppage (median 0.18 m/s), so it is an easier case than a ball that keeps rolling.
- **Ownership-only is 0.82–0.88 everywhere** (WCSF, DFL, Metrica). What separates the datasets is dead-ball handling, and that is the part no clean proxy for BAR–ATH covers.

## Step 4 design: state-dependent degradation (built, not yet trained)
- **Generator:** `se_degrade.state_loss` (7 unit tests). Per stoppage of 3 s or more in the external match's own labels, the ball vanishes after a lag (30% within 0.2 s, otherwise log-normal with a 2 s median) and returns at the restart (15% up to 4 s before it, 15% up to 1 s after). 10% of long stoppages keep the ball. Live play keeps the ball apart from about 3 long gaps per half. Players lost per team: about 1.6 in a stoppage gap, about 0.25 in live play.
- **Why these numbers:** BAR–ATH inputs give only aggregates (ball missing on about 3 of 4 still frames, about 3 fewer players tracked while it is missing, 150 gaps almost all over 3 s). The lag is not observable anywhere, so it is broad by design.
- **Training copies:** `sda`, `sda2`, `sda3` for the 7 DFL matches and WCSF, replacing the random-loss copies (`augp*`).
- **Evaluation views:** `sde1` (same generator, other seed), `sde2` (ball vanishes sooner), `sde3` (later). A change must hold on all three, so it cannot win by fitting one lag guess.
- **Real-data checks, which decide:** WCSF as recorded (full score, now a dev fold), Metrica ownership-only, clean dev. The simulated views only guard against regressions.
- **Same retrain:** the `se_sym.py` swap fix, and Metrica as ownership-only training data if the leave-one-game-out passes (mean paired gain above zero with at least 2 of 3 games up; fixed before scoring).
- **Baseline:** the saved v8 fold models predict the new views through `se_predict.py`, so no baseline retrain is needed.
- **Generator check (one test case, DFL J03WR9, against BAR–ATH's input aggregates):** ball missing when players are still 0.74 (BAR–ATH 0.75), when moving 0.22 (0.29); players tracked with the ball missing 18.6 (18.7), with it seen 21.5 (21.5); share of missing frames in gaps over 10 s 0.92 (0.85). It makes fewer gaps (83 against 150) and less missing ball overall (0.34 against 0.42); not tuned further.
- **Adoption rule, fixed before training** (new model set against the v8-recipe set `r8ba` + `r8bb` + `g8p`, both decoded like the release, `gapko` stage):
  1. WCSF as recorded, full spell F1: up by at least 0.02 (v8: 0.764).
  2. Metrica ownership-only (all-external-data models, no Metrica in training): no worse than 0.005 below the baseline's 0.875.
  3. Clean dev, 13 matches, paired: mean no worse than −0.003.
  4. `sde1`, `sde2`, `sde3` on the 6 DFL dev matches: each at or above the baseline.
  If all four hold, all-data models are trained and a v10 candidate CSV is built for the user to decide on. The submission is not swapped without the user.
- **Confound to keep in mind:** the new folds also train on WCSF (it was holdout before), so in 3 of 4 folds the new models see one more D-labelled match than the baseline did.

## Step 5 result: Metrica leave-one-game-out (17 November, 00:00)
- **Setup:** v8 recipe, 2 GRUs + boosted trees per arm, decoded like the release. The Metrica arm adds the two other Metrica games with ownership-only supervision on the ball-flag labels (`HA_ONLY`); the held-out game is never trained on.

| Held-out game | Baseline (no Metrica) | + 2 Metrica games | Gain |
|---|---:|---:|---:|
| Game 1 | 0.8636 | 0.8992 | +0.0356 |
| Game 2 | 0.8648 | 0.8898 | +0.0250 |
| Game 3 | 0.8970 | 0.9272 | +0.0302 |
| **Mean, ownership-only** | **0.8751** | **0.9054** | **+0.0303 ± 0.0031** |

- **Passes the rule fixed beforehand** (mean gain above zero, at least 2 of 3 games up): 3 of 3 up.
- Possessions of 1 s or less found: 0.37 / 0.33 / 0.46 → 0.41 / 0.37 / 0.50. Team accuracy on live frames: 0.970–0.984 → 0.977–0.989.
- **Why it matters for BAR–ATH:** the organisers state the ground truth is derived from corrected tracking, with D where that tracking marks the ball dead. The Metrica samples are corrected tracking from the same vendor, so this is the nearest thing we have to the target's own labelling convention.
- **Decision:** Metrica joins the retrain as ownership-only training data (`m10`). `n10` is the same recipe without Metrica, kept so the two changes can be told apart.

## Step 6 result: the state-dependent retrain fails its rule (17 November, 04:24)
- **Arms** (each one model set of 2 GRUs + boosted trees, release decoder, `gapko` stage unless stated):
  - `B8`: the v8 recipe as trained in round 8 (`r8ba` + `r8bb` + `g8p`); `HB8` is its holdout-mode twin, used for WCSF.
  - `N10`: state-dependent copies + swap fix + WCSF in a dev fold.
  - `M10`: `N10` + the three Metrica games as ownership-only training data.
  - `c10`: the `N10` recipe on all external data, predicting Metrica (no Metrica in training).

| Check | Baseline | N10 | M10 | Rule | Verdict |
|---|---:|---:|---:|---|---|
| WCSF as recorded, full spell F1 | 0.763 | 0.733 | 0.733 | up by 0.02 | **fails (−0.030)** |
| Metrica ownership-only (`c10`) | 0.875 | 0.881 | – | no worse than −0.005 | passes (+0.006, 2 of 3 games) |
| Clean dev, 13 matches, paired | 0.802 | −0.001 ± 0.005 | −0.002 ± 0.004 | no worse than −0.003 | passes |
| `sde1` (same generator) | 0.799 | +0.001 | −0.000 | at or above | flat |
| `sde2` (ball vanishes sooner) | 0.792 | −0.000 | +0.003 | at or above | flat |
| `sde3` (ball vanishes later) | 0.796 | +0.002 | +0.004 | at or above | flat |

- **Without the gap rule** the new models are clearly better on the simulated views (+0.011 to +0.031, 5–6 of 6 matches each). They learned what the gap rule does. With the gap rule on top there is nothing left to gain, because the rule already covers it.
- **WCSF got worse.** Its ball is visible through every stoppage. Training on copies where 81% of dead frames have no ball makes the models less willing to call D while the ball is in view, which is exactly WCSF's situation. So the generator trades WCSF's regime for BAR–ATH's, and with the gap rule already in place it buys nothing in BAR–ATH's.
- **Verdict:** rule not met. No candidate is built from the state-dependent retrain. The generator, the views and the swap fix stay in the repo as options.
- **What this says about v9:** on simulated BAR–ATH-like ball loss, v8's models plus the gap rule already do as well as models trained for it. That is mild support for v9's design, from a simulation we built ourselves.

## Step 7: candidate from the change that did pass (17 November)
- **Recipe:** v9 unchanged (random-loss copies, old swap, same features, same decoder and gap rule) plus the three Metrica games as ownership-only training data. This is exactly the leave-one-game-out recipe (+0.030 on held-out Metrica games, 3 of 3).
- **Indirect dev evidence:** `M10` against `N10` isolates adding Metrica under the other recipe: clean dev −0.001, WCSF 0.000, simulated views −0.002 / +0.003 / +0.002.
- **Runs** (`night_stage_e.sh`): all-data models `A10a`/`A10b`/`A10g` → export to `strong-emissions-reference/v10-model/` → candidate CSV in `v10-candidate/`; then the same recipe in dev CV (`p10a`/`p10b`/`p10g`) for a like-for-like comparison with `B8`.
- The submission in `final-submission/` is not touched.

## Step 7 result: the candidate does not beat v9 outside Metrica (17 November, 06:20)
- **Arms:** `P10` = the recipe above in dev CV (`p10a` + `p10b` + `p10g`); `HP10` = the same recipe trained on dev + Metrica only (`night_stage_f.sh`), scored on WCSF and the four locked holdout matches (`night_stage_g.sh`). Baselines `B8` / `HB8`. Release decoder, `gapko` stage.

| Check | v8 recipe | With Metrica | Paired difference |
|---|---:|---:|---:|
| Metrica ownership-only, leave-one-game-out (step 5) | 0.875 | 0.905 | +0.030 ± 0.003, 3 of 3 |
| Clean dev, 13 matches | 0.802 | 0.803 | +0.001 ± 0.004, 5 of 13 up |
| `sde1` | 0.799 | 0.791 | −0.008 ± 0.005 |
| `sde2` | 0.792 | 0.790 | −0.002 ± 0.004 |
| `sde3` | 0.796 | 0.794 | −0.002 ± 0.004 |
| WCSF as recorded | 0.763 | 0.753 | −0.010 |
| Holdout, four matches, provider-weighted (ninth look) | 0.785 | 0.781 | −0.004, 2 of 4 up |

- **Reading:** the gain exists only on Metrica itself, where the two training games share provider, tracking system and labelling with the test game. On every other provider the change is flat to slightly negative. That is an in-provider gain, not evidence of better transfer to another provider such as BAR–ATH.
- **Candidate file** (`v10-candidate/submission.csv`, SHA `b38a4691…`): 1.54% of frames differ from v9 (3,065, in 217 runs, 22 of them 2 s or longer); 289 possessions against 295.
- **Verdict:** keep v9. The candidate stays on disk as a record; it is not recommended for submission.
- **v9 rebuild** from the working tree after tonight's code edits: `ed97ae73…`, identical to the submitted file.
- **Lesson:** adding a provider as ownership-only training data helps that provider. Don't expect it to move other providers unless a held-out provider says so.
- **Estimate and version table:** `docs/score-estimate-2026-11-17.md`.

## Swap fix (17 November)
- `se_sym.swap_plan(names, fix=True)` (opt `symfix`): the `nearH_*` window features are flipped wherever the window saw the ball at all, using the matching `obs_*` window as the support. Old models keep the old behaviour, so v9 still rebuilds exactly.
- Against truly mirrored frames (Metrica game 2, 30,000 frames): `nearH_p12` wrong on 28.3% of rows before, 0.2% after; swapping twice now restores every feature. The remainder are exact distance ties.
- **Not solved by this:** DFL's ball stays frozen during the simulated lag, so the stretch between the stop and the ball vanishing is still learned from a shortcut. WCSF is the only real check on it.
