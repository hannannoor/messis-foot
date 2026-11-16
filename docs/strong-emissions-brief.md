# Strong-emission model: brief (15 November 2026)

## The task
- Label every frame of BAR–ATH as home possession (H), away possession (A), dead ball (D) or not scored (X). The score is spell F1: whole possession runs matched by overlap, averaged over IoU 0.3–0.7.
- **Rules followed:**
  - BAR–ATH is used for inference only. Nothing is fitted, tuned or selected on its ground truth or video, and nothing is uploaded.
  - All training uses 18 external matches: 7 DFL, 10 SkillCorner and 1 WCSF.

## Submitted: v9
- File: `final-submission/submission.csv`, 199,319 rows, SHA-256 `ed97ae735a57e81dbd788f94c40de210dcbcb5aed40bc94d9552f1dade2897cd`.
- Rebuild: `python strong_release.py --prefix <BAR-ATH_tactical> --tags <..._smart_tagging.xml> --out <new dir>` (CPython + numpy, deterministic, a few minutes).
- **Pipeline:**
  - 241 per-frame geometry features: ball and player distances, ball-impulse contacts, contact reliability, and player-only team shape.
  - Two model sets (each 2 bidirectional GRUs + boosted trees), blended 0.15 (v4 set) / 0.85 (v8 set). The v8 set is trained on three copies per D-labelled match with both the ball and some players removed (BAR–ATH tracks about 10.1 players per team), and its GRUs also predict possession boundaries.
  - A 3-state Viterbi decoder with switch cost 20: 10 near a ball contact, and down towards 8 where the boundary channel fires.
  - Then the label-free gap rule: a ball gap over 3 s with slow players becomes dead ball.
  - Then the automatic kickoff patch.

## Results (provider-weighted spell F1)

| Version | Main idea | Holdout (5 locked matches) | Dev CV (13) | Ball-loss view* |
|---|---|---:|---:|---:|
| old release | 31-node tree, 18 features | 0.536 | 0.584 | 0.40 |
| v1 | GRU + boosted trees, 155 features | 0.726 | 0.772 | – |
| v2 | short-possession weighting; evidence on missing-ball rows | 0.742 | 0.783 | 0.48 |
| v3 | ball-dropout training; gap rule removed | 0.746 | 0.781 | 0.59 |
| v4 | ball-impulse contact features | 0.759 | 0.798 | 0.60 |
| v5 | player-only team shape for long ball gaps; touch-aware cost | 0.765 | 0.803 | 0.679 (5-view avg) |
| v6 | three dropout views per match | 0.767 | 0.800 | 0.691 (5-view avg) |
| v8 | player-dropout training + possession-boundary head | 0.783 | 0.809 | 0.700 (5-view avg); 0.684 with player loss |
| **v9 (submitted)** | **v8 models + gap rule reinstated** | – | **0.808** | **Metrica (real ball loss): 0.794 (v8 0.752)** |

\*Ball-loss view: about 42% of the ball removed with SkillCorner-like gaps. BAR–ATH sees the ball on only 58% of frames, so this is the closest proxy. Holdout WCSF is shown for v3 onwards; earlier rows use dev DFL or holdout WCSF where available.

## What mattered most
1. **A real sequence model instead of a small tree:** +0.19 on its own.
2. **Ball-missing robustness:** the models had learned "no ball means dead ball". Training on ball-dropout copies fixed it. Clean scores hid this completely.
3. **Team shape when the ball is gone:** the team in possession is wider, moves forward and has more forward runners. This moved the ball-loss view from 0.60 to 0.67.

## The Metrica finding (round 9)
- On 3 fresh public Metrica games (same vendor as BAR–ATH, real ball loss), a missing ball mostly means stopped play: 79–89% of dead frames have no ball, against 7–16% of live frames.
- BAR–ATH's inputs show the same pattern: the ball is missing on 77% of frames when players are still, against 19% when they're moving.
- Our earlier ball-loss simulation used random gaps, which is why the gap rule was wrongly dropped in v3. Reinstating it adds +0.042 on Metrica, with clean dev flat.
- The repo's public 5-minute ground truth is never used to choose versions (RULES.md); it may only be used as a pipeline-correctness check.

## What did not work
- Decoder-only tweaks to the old model: 10 variants, all flat.
- Wider GRU; separate dead-ball cost; touch-flip dead-ball breaks; stronger augmentation dose.
- v3/v4 blend; ±30 s team-shape windows.
- Round 7 on top of v6 (blend weights, switch cost, power, 5 dropout copies, SkillCorner copies): all within noise.
- Round 8 restart / set-piece features: within noise (existing stillness features already carry the signal).

## Caveats
- Simulated ball loss shares one generator between training and evaluation, so it can flatter changes that adapt to that generator.
- Expected BAR–ATH performance: there is no clean proxy. The round 10 audit showed the Metrica ball is an in-play flag, so v9's 0.794 there is true by construction and is not an estimate. With dead-ball calls taken out and a corrected reference, v8 and v9 score 0.878 on Metrica ownership (v4 0.870, v2 0.835). How well D is timed at BAR–ATH's ball-gap edges is untested.
- The holdout has now been looked at eight times.
- v6's ball-loss gain over v5 held on real SkillCorner gap layouts (+0.010 to +0.013) but not on the 2-match degraded holdout (−0.0015), most likely small-sample noise.

## Timeline
- 14 November: about 20:15 start; 22:59 v1.
- 15 November: 00:04 v2, 01:52 v3, 02:59 v4, 10:14 v5, 12:39 v6 (experiment), about 13:10 v5 restored as the submission. The v6 investigation and round 7 ran that afternoon; v6 was made the submission in the evening. 16 November: round 8 (player-tracking robustness, boundary head); v8 submitted. Round 9: fresh Metrica evaluation; v9 (gap rule reinstated) submitted.
- Code is on branch `experiment/strong-emissions`. Private arrays are in `strong-emissions-reference/`, outside Git.
