# Round 9: Metrica public sample games as fresh evidence (16 November 2026)

(Earlier round notes lived in `Desktop/dlor/projects/docs`, which was cleared on 16 November. Their results are summarised in `docs/strong-emissions-results.md`.)

## Why
- The locked holdout has been looked at 8 times, and every dev decision uses the same 13 matches. We need untouched evidence.
- Metrica's 3 public sample games (`metrica-sports/sample-data`) were already acquired, hashes pinned, by an earlier phase (`gap-liveness-private/2026-11-10/metrica/source`, 175 MB). Nothing new is downloaded.
- It's the same tracking vendor as BAR–ATH, and the ball is visible on about 61% of frames (BAR–ATH: 58%).
- **Labels:** event-derived (`metrica_event_reference.py`).
  - The owner is set at each pass, carry, recovery or shot, and when a challenge is won or lost.
  - D runs from a ball-out or foul until the next set piece.
  - Coverage is about 98% of frames, with 24–48 conflicting frames per game.
  - This approximates the competition's convention; it is not identical to it.

## Goal
- A fresh score for each released version.
- A check that the label convention is consistent with dev rankings.
- Then decide: training data or test set.

## Non-goals
- Changing the label definition. No hand labels, no video, nothing from BAR–ATH.

## Anti-goals
- Tuning before the fresh read is recorded.
- Fitting to Metrica label quirks.
- Masks derived from BAR–ATH sequences. Only aggregate input statistics are used.

## Holdouts
- The 3 Metrica games, used for this round. The old locked five are not used.

## Approaches
1. **(Picked) Score every release with its exact numpy runtime and decoder.** All-data models, none of which saw these games.
2. Train on them immediately: rejected, because it spends the only fresh test.
3. Fit label offsets: rejected, because that is tuning on the test.

## Findings (single pre-declared read)

| Version | Game 1 | Game 2 | Game 3 | Mean |
|---|---:|---:|---:|---:|
| Old release | 0.586 | 0.557 | 0.561 | 0.568 |
| v2 (pre-dropout models, gap rule) | **0.776** | 0.734 | **0.786** | **0.765** |
| v4 | 0.731 | 0.728 | 0.759 | 0.739 |
| v5 | 0.734 | 0.740 | 0.748 | 0.741 |
| v6 | 0.744 | 0.741 | 0.757 | 0.747 |
| v8 | 0.746 | 0.741 | 0.769 | 0.752 |

- **v4 → v8 matches dev:** v8 is the best of v4–v8 on all 3 games.
- **v2 beats all of them.** v2 is the last version before ball-dropout training and before the gap rule was removed.
- **Why: real ball loss is not random.**
  - In Metrica, 79–89% of dead frames have no ball, against 7–16% of live frames.
  - BAR–ATH's inputs (no labels) show the same pattern: the ball is missing on 77% of frames when ≥ 50% of players are still, against 19% when they're moving (ratio 4.0; Metrica 6–14).
  - Our random-dropout simulation has a ratio of 1.0, and SkillCorner 0.3.
  - So "ball missing ⇒ dead", which v3 trained out of the models, is largely true on Metrica and probably on BAR–ATH.
  - Every ball-loss test since v3 used random gaps and penalised exactly the cue that real data rewards.
- **v8's errors:** 97–98% accuracy on live frames with the ball visible. On live frames with the ball missing (7–16% of live frames) it predicts D about 80% of the time; D recall is 0.68–0.80.

## Next experiments
1. Gap-rule ablation for v2 and v8 (same supports, with and without the gap rule).
2. Leave-one-game-out training with Metrica: the v8 recipe, 2 seeds + boosted trees, against the same recipe without Metrica.
3. State-dependent ball dropout (missing more likely when play is stopped) to replace random dropout in training and in the ball-loss tests.

## Result 1: the gap rule is right for real ball loss (v9)
- **Same v8 supports, three decode stages:**

| Stage | Metrica games 1 / 2 / 3 | Mean | Clean dev | Random-loss views |
|---|---|---:|---:|---:|
| `nogap` (v3–v8 release) | 0.746 / 0.741 / 0.769 | 0.752 | 0.8089 | 0.685 / 0.719 / 0.668 |
| `final` (full release chain) | 0.783 / 0.774 / 0.810 | 0.789 | 0.8044 | 0.630 / 0.672 / 0.617 |
| **`gapko` (gap rule on the main decode + kickoff patch)** | **0.785 / 0.778 / 0.819** | **0.794** | **0.8076** | 0.630 / 0.674 / 0.618 |

- **The gap rule** (label-free): a ball gap over 3 s whose median player speed is below the match's typical speed becomes dead ball.
  - On Metrica it changes 2.8–5.3% of active frames, and 83–90% of those changes are correct (before: 6–8%).
  - On BAR–ATH (inputs and our own predictions only) it changes 4.5% of active frames, and 113 of 133 long gaps are judged stoppages. That's inside Metrica's range.
- It was removed in v3 because random-gap tests said it hurt. With real, state-dependent ball loss it helps.
- **v9 = v8 models + `gapko`.**
  - SHA-256 `ed97ae73…`, two CPU builds byte-identical, validator OK.
  - Exactly 7,193 frames differ from v8, all live → D.
  - Not installed yet; that's the user's call.

## Result 2: leave-one-game-out training with Metrica
- Running (about 25 minutes per model; 8 models).
