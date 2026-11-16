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
- **Not solved by this:** DFL's ball stays frozen during the simulated lag, so the stretch between the stop and the ball vanishing is still learned from a shortcut. WCSF is the only real check on it.
