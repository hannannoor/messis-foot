# Audit request: possession labelling for the "More Than a Hack 2027" challenge

You are an experienced sports-analytics / ML reviewer. Please **audit our solution and look for concrete improvements** to the ranking metric. Be skeptical: we want bugs, leakage, rule risks and weak evidence found, not praise.

## Links
- **Our code (audit this):** https://github.com/hannannoor/messis-foot/tree/experiment/strong-emissions. Branch `experiment/strong-emissions`, current submission at commit `cd07b0e`.
- **Official challenge repo** (task, rules, metric, scorer): https://github.com/metrica-sports/more-than-a-hack-2027. Read `CHALLENGE.md`, `RULES.md`, `EVALUATION.md` and `evaluation/possession_metrics.py`.

## The task (short)
- For every video frame of one match (BAR–ATH, 199,319 frames), output H (home possession, ball alive), A (away possession), D (dead ball) or X (no answer).
- Inputs: automatic tactical-camera tracking (players + ball), Smart Tagging and homography.
- **Ranking metric: spellF1.** Possessions are maximal H or A runs, matched one-to-one by temporal IoU, with F1 averaged over IoU 0.3–0.7. X is forward-filled before scoring. Differences under about 0.04 are noise on the full match.

## Rules that matter for your review
- No hand labels on the provided game.
- No use of private ground truth, or of any human-produced data about the provided game.
- The repo's **public 5-minute ground truth may only be used to check pipeline correctness**, never to choose between versions, to tune, or to train.
- The submission must be exactly reproducible from the repo.
- External data about other games is allowed.
- Match data must not be redistributed. **You do not have, and should not ask for, the match data.** Review the code and docs only.

## What our pipeline does (v9, the current submission)
Code: `strong_release.py` → `strong_runtime.py` (deterministic numpy inference) → `se_assembly.py` (decoder).

1. **Features** (`se_features.py`): 241 geometry features per frame, all label-free.
   - ball–player distances and margins;
   - ball-velocity "impulse" contacts plus a reliability flag;
   - player-only **team shape** in each team's attacking frame (width, depth, defensive line, forward runners, marking), with ±2/5/15 s windows.
2. **Evidence:** a geometric blend, 0.15 × v4 model set + 0.85 × v8 model set, then squared and renormalised.
   - Each set = 2 bidirectional GRUs (`se_gru.py`) + HistGradientBoosting own/live heads (`se_train.py`), with home/away swap augmentation and swap test-time averaging.
   - The v8 GRUs also have a 4th output that predicts **possession boundaries** (multi-task, λ = 0.3).
   - Training uses copies of the D-labelled matches with the **ball and some players removed** (`se_degrade.py`).
3. **Decoder:** a 3-state Viterbi.
   - Switch cost 20; 10 within ±6 frames of an impulse contact; and down towards 8 where the boundary channel fires.
   - Then the **label-free gap rule** (`gap_liveness.py`): a ball gap over 3 s with below-typical player speed becomes D.
   - Then the automatic kickoff patch.
4. **Training data:** 18 external matches: 7 DFL (H/A/D labels), 10 SkillCorner (H/A only), 1 WCSF. BAR–ATH is used for inference only.

## Evidence so far (details in `docs/strong-emissions-results.md`, `docs/strong-emissions-brief.md`, `docs/superpowers/specs/2026-11-16-round9-metrica-design.md`)

| Version | Holdout (5 external matches) | Dev CV (13) | Metrica public sample games (3, never fitted) |
|---|---:|---:|---:|
| Old release (decision tree) | 0.536 | 0.584 | 0.568 |
| v4 | 0.759 | 0.798 | 0.739 |
| v6 | 0.767 | 0.800 | 0.747 |
| v8 | 0.783 | 0.809 | 0.752 |
| **v9 (submitted)** | – | 0.808 | **0.794** |

## Key lessons and open doubts (please probe these)
- **Simulated against real ball loss.** BAR–ATH sees the ball on 58% of frames.
  - From v3 to v8 we stress-tested with *random* ball gaps, and that is why the gap rule was removed in v3.
  - The 3 Metrica public games (same vendor as BAR–ATH) showed real ball loss is *state-dependent*: 79–89% of dead frames have no ball, against 7–16% of live frames.
  - BAR–ATH's inputs show the same pattern: the ball is missing on 77% of "players still" frames against 19% of "moving" frames.
  - Reinstating the gap rule gave +0.042 on Metrica, with clean dev flat.
  - **Question:** which earlier decisions did the random-gap simulation distort, and how should ball-loss augmentation be redesigned?
- **Metrica labels are derived from the event log** (`metrica_event_reference.py`), not the competition's Smart-Tagging-based definition. Is that a fair proxy? What systematic offsets (boundary timing, D start/end) might bias conclusions?
- **The locked holdout has been looked at 8 times.** How much should we trust it now?
- **Player dropout:** BAR–ATH tracks about 10.1 players per team (DFL always 11). We simulate run-based removal of the most extreme players. Is that realistic?
- **Known weak spots:**
  - dead-ball recall when the ball is missing (Metrica D recall 0.68–0.80 before the gap rule);
  - short possessions under 2 s (about 50% found even with the ball visible);
  - long possessions with the ball missing.
- **Paused experiment:** adding the Metrica games to training (leave-one-game-out). The baseline is trained; the three held-out runs are not. Is this worth finishing, and how should Metrica's different label convention be handled if we train on it?

## What we want from you
1. **Correctness:** bugs in feature computation, swap symmetry (`se_sym.py`), the decoder, frame alignment, X handling, or the release path (`strong_release.py` must regenerate the exact CSV).
2. **Leakage and rule compliance:** anything that uses BAR–ATH labels or video, tuning on the public 5 minutes, or test-set information reaching training or selection (CV folds, holdout reuse, Metrica).
3. **Evaluation validity:** is our evidence enough to trust v9 over v8? What would a better proxy for BAR–ATH look like?
4. **Improvements, ranked by expected spellF1 gain against effort.** For each, give the idea, why it should help spellF1 specifically (possession objects, not frames), how to test it without touching BAR–ATH labels, and the risk.
5. **Quick wins vs. bigger bets:** separate what fits in a few hours from what needs days.

Please cite files, functions and line numbers where you can. If something is ambiguous, say what you would check rather than guessing.
