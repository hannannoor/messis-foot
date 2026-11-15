# Strong-emission model: brief (15 November 2026)

## The task
- Label every frame of BAR–ATH as home possession (H), away possession (A), dead ball (D) or not scored (X). The score is spell F1: whole possession runs matched by overlap, averaged over IoU 0.3–0.7.
- **Rules followed:**
  - BAR–ATH is used for inference only. Nothing is fitted, tuned or selected on its ground truth or video, and nothing is uploaded.
  - All training uses 18 external matches: 7 DFL, 10 SkillCorner and 1 WCSF.

## Submitted: v5
- File: `final-submission/submission.csv`, 199,319 rows, SHA-256 `f4d3d940561a5820b59c594156e6a7cd10a3459847e4f7487ad8786f7daf7285`.
- Rebuild: `python strong_release.py --prefix <BAR-ATH_tactical> --tags <..._smart_tagging.xml> --out <new dir>` (CPython + numpy, deterministic, a few minutes).
- **Pipeline:**
  - 241 per-frame geometry features: ball and player distances, ball-impulse contacts, contact reliability, and player-only team shape.
  - Two model sets (each 2 bidirectional GRUs + boosted trees), blended 0.3 (v4 set) / 0.7 (v5 set).
  - A 3-state Viterbi decoder with switch cost 20, or 10 near a ball contact, then the automatic kickoff patch.

## Results (provider-weighted spell F1)

| Version | Main idea | Holdout (5 locked matches) | Dev CV (13) | Ball-loss view* |
|---|---|---:|---:|---:|
| old release | 31-node tree, 18 features | 0.536 | 0.584 | 0.40 |
| v1 | GRU + boosted trees, 155 features | 0.726 | 0.772 | – |
| v2 | short-possession weighting; evidence on missing-ball rows | 0.742 | 0.783 | 0.48 |
| v3 | ball-dropout training; gap rule removed | 0.746 | 0.781 | 0.59 |
| v4 | ball-impulse contact features | 0.759 | 0.798 | 0.60 |
| **v5 (submitted)** | **player-only team shape for long ball gaps; touch-aware cost** | **0.765** | **0.803** | **0.67** |
| v6 (not submitted) | three dropout views per match | 0.767 | 0.800 | 0.67 |

\*Ball-loss view: about 42% of the ball removed with SkillCorner-like gaps. BAR–ATH sees the ball on only 58% of frames, so this is the closest proxy. Holdout WCSF is shown for v3 onwards; earlier rows use dev DFL or holdout WCSF where available.

## What mattered most
1. **A real sequence model instead of a small tree:** +0.19 on its own.
2. **Ball-missing robustness:** the models had learned "no ball means dead ball". Training on ball-dropout copies fixed it. Clean scores hid this completely.
3. **Team shape when the ball is gone:** the team in possession is wider, moves forward and has more forward runners. This moved the ball-loss view from 0.60 to 0.67.

## What did not work
- Decoder-only tweaks to the old model: 10 variants, all flat.
- Wider GRU; separate dead-ball cost; touch-flip dead-ball breaks; stronger augmentation dose.
- v3/v4 blend; ±30 s team-shape windows.
- v6 (multiple dropout views): it gained on simulated ball loss in dev, but the gain didn't replicate on the holdout. See the v6 investigation in `docs/strong-emissions-results.md`.

## Caveats
- The holdout has been looked at six times, so small holdout gains carry little weight now.
- Simulated ball loss shares one generator between training and evaluation, so it can flatter changes that adapt to that generator.
- Expected BAR–ATH performance is nearer the ball-loss view (about 0.65) than the clean numbers (about 0.77–0.80).

## Timeline
- 14 November: about 20:15 start; 22:59 v1.
- 15 November: 00:04 v2, 01:52 v3, 02:59 v4, 10:14 v5, 12:39 v6 (experiment), about 13:10 v5 restored as the submission.
- Code is on branch `experiment/strong-emissions`. Private arrays are in `strong-emissions-reference/`, outside Git.
