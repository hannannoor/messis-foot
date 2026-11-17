# Round 11: self-training on the target match

17 November 2026. Branch `experiment/self-training`. The submitted file (v9, `ed97ae73…`) is not touched by this work.

## Why

Round 10 showed that the models are provider-specific. Adding two Metrica games to training raised the third game's
ownership score by 0.030, and did nothing for any other provider. BAR–ATH comes from a provider that is in none of
our training data, so the same gap probably applies to it, and we have no labelled match from that provider to close
it with.

The organisers' rules allow one way to learn from the provided match itself: "pseudo-labels produced by an
algorithm, provided no person decided any of them" (RULES.md, training and validation data).

## Goal

Find out whether training on a match's own decoded labels improves the labels for that match, measured on matches
where we have a reference. If it does, apply the same procedure to BAR–ATH and produce a candidate file.

## Non-goals

- No new features, no new decoder, no new training data.
- No change to the submitted file without the user's decision.

## Anti-goals

- No use of the BAR–ATH ground truth, the public 5 minutes included, to decide anything here.
- No hand-made label, threshold or constant tied to frames of the provided match.
- No BAR–ATH data or pseudo-label file in the public repository. Only model weights are exported.

## Holdouts

The locked four-match holdout is not scored in this round. The check matches are the three Metrica sample games and
the WCSF match. None of them is in the training set of its own baseline model.

## Approach

1. Decode the target match with the baseline models (the release decoder, `gapko` stage).
2. Save the match's features with those labels as a training case, `pl-<match>` (`se_pseudo.py`).
3. Retrain the same recipe on the external matches plus that case. A `pl-` case is supervised for ownership only
   (H against A on frames the decoder called H or A), and is sampled three times as often as one external match
   (`pl_repeat`).
4. Predict the target match again and decode it the same way.

Check, per target match, self-trained against baseline, same decoder:

- Metrica games 1–3: ownership-only spell F1 against the ball-flag reference (baseline tags `lgbase*`).
- WCSF: full and ownership-only spell F1 (baseline tags `H_r8b*`, `H_g8p`).

First pass uses one GRU per arm (seed a), because four trainings fit in under an hour. Pass rule, fixed before the
runs: mean paired ownership gain above zero by at least two standard errors, with at least three of the four matches
up. If it passes, confirm with the full model set (two GRUs and the trees) before building the BAR–ATH candidate.

## Considered and not done

- Pseudo-labelling the dead-ball class as well. On Metrica and on BAR–ATH the decoder's dead ball is mostly the gap
  rule, so the model would learn "missing ball means dead" from its own rule. That is what failed in round 10.
- Confidence filtering of the pseudo-labels (`se_pseudo.py` has a `margin` option). Left for a second pass if the
  first one is positive.
- More external training data. Round 10's lesson is that another provider helps that provider only.

## Result: self-training (17 November, 16:35) — rejected

One GRU per arm, release decoder. Ownership-only spell F1 +0.0078 ± 0.0041, 3 of 4 matches up (Metrica 1–3, WCSF):
just under the 2-SE bar. WCSF full spell F1 fell 0.795 → 0.759. The pseudo-labels carry v9's own H/A labels
through stoppages it missed, so training on them teaches the model to miss dead ball even more.

## Second direction: SkillCorner dead-ball labels (added 16:20, after the self-training runs started)

SkillCorner's public dynamic events mark restarts (`game_interruption_before`: throw-in, free kick, goal kick, corner,
kick-off after a goal). `se_sc_dead.py ref` turns each into a stoppage running from the end of the previous on-ball
event to the restart, and writes a reference with those frames as D (`sc_deadref/`). 67–94 stoppages per match,
35–51% of playing time. The ball is detected 23% of the time inside stoppages and 75% outside (one match counted),
so SkillCorner loses the ball the way BAR–ATH does. Edges are approximate: the last event ends before the ball goes
out.

Measured with models that never trained on the match (v8 recipe: CV folds for the 7 dev matches, dev-only models for
the 10 added matches), release decoder, 17 matches:

| Decoder | Spell F1 vs dead-ball labels | Dead recall | Dead precision |
|---|---:|---:|---:|
| no gap rule | 0.553 | 0.38 | 0.989 |
| v9 (gap rule) | 0.571 | 0.47 | 0.975 |
| best of 60 gap-rule settings | 0.573 | 0.50 | 0.962 |
| dead ball exactly right | 0.813 | 1 | 1 |

The gap rule helps on all 17 matches. Its constants are not worth retuning (+0.002). v9 misses half the dead frames.

**Check C (`scd_chain.sh`).** The v8 recipe with SkillCorner supervised for H/A/D on these labels (opts `sc_dead`),
one GRU, against the same recipe without it (`r8ba` / `H_r8ba`). Pass rule, written before the scores:

1. WCSF full spell F1 (real tracking dead ball, independent of the event labels): no worse than −0.005.
2. DFL dev, clean: mean paired change no worse than −0.005.
3. SkillCorner with dead-ball labels (7 CV matches + 10 added matches scored with the dev-only model): mean gain of
   at least 2 SE, with most matches up.

If all three pass, the candidate is set B retrained this way (two GRUs + trees, `all` mode, `cand_chain.sh`), set A
unchanged. The submission is swapped only with the user's decision.

## Left to the builder

- The value of `pl_repeat` and whether the trees get the pseudo-labelled match too.
- For BAR–ATH: which model sets to retrain. Set B carries 0.85 of the blend.

## Result: check C (17 November, 17:35) — fails rules 1 and 2

One GRU (`scda` / `H_scda`) against the same recipe without SkillCorner dead-ball labels (`r8ba` / `H_r8ba`), release
decoder:

| Check | Without | With | Change |
|---|---:|---:|---:|
| SkillCorner dev, dead-ball labels (7, CV) | | | +0.125 ± 0.011, 7 of 7 up; dead recall 0.65 → 0.94, precision 0.97 → 0.94 |
| WCSF full spell F1 | 0.7954 | 0.7837 | −0.0117 |
| DFL dev, clean (6) | 0.8110 | 0.8046 | −0.0064 |

The model learns SkillCorner's stoppage convention, but on the two checks whose dead ball comes from tracking it loses.
Likely cause: the event-derived stoppage starts at the last touch, before the ball goes out, so the model learns to
call dead ball early. Variant `scma` (`sc_deadref_m20`: the first 2 s of each stoppage left unlabelled) is checked
with the same rule (`scm_chain.sh`).

## Result: check C2, 2 s margin (19:36) — fails too

`scma`: SkillCorner dev +0.115 ± 0.012 (7/7); WCSF 0.7954 → 0.7764; DFL 0.8110 → 0.8044. Training dead ball on the
event-derived SkillCorner stoppages is dropped.

**Why v9 misses half of SkillCorner's stoppages.** 60% of the missed frames have no ball, and most of those sit in
long ball gaps (over 10 s) with slow players, which the gap rule should catch. It cannot: inside long gaps the broadcast
camera shows on average 1.7 players (replays, close-ups), so 46% of long-gap frames have no player-speed sample and the
rule skips them (75% of those frames are dead). BAR–ATH's tactical camera keeps about 19 players tracked when the ball
is missing, so this miss is mostly a broadcast artefact, not a BAR–ATH estimate.

## Label-free ball rules after the decoder (`se_rule_dead.py`, 19:45–20:10)

Pass rule, fixed before the run: WCSF and the DFL dev mean each no worse than −0.002, SkillCorner gain at least 2 SE;
then one look at the locked holdout. Models never trained on the match; release decoder; rule applied afterwards.

| Rule | DFL dev (6) | WCSF | SkillCorner (17) |
|---|---:|---:|---:|
| ball > 0.5 m out | −0.005 (0/6) | +0.005 | +0.007 |
| ball > 1 m out | −0.002 (0/6) | +0.004 | +0.002 |
| ball > 0.5 m out + following gap | −0.005 | +0.005 | +0.031 (17/17) |
| ball > 1 m out + following gap | −0.0022 | +0.004 | +0.019 (17/17) |
| ball still 2 s / 4 s | −0.010 / −0.004 | +0.009 / +0.009 | −0.001 / 0.000 |
| **ball > 1 m out + following gap, released 0.4 s before a tracked re-entry (`outgapt1`)** | **−0.0019 (0/6)** | **+0.004** | **+0.022 ± 0.002 (17/17)** |

DFL's losses come from restarts: in all 227 of its ball-out runs the frames DFL calls live are the last few (median
4 per run), a throw-in or kick taken while the ball is still just outside. Releasing D 0.4 s before re-entry addresses
that; the trimmed variant was the sixth tried, so the pass is narrow and selected.

Holdout, one look (dev-only models): DFL J03WN1 −0.0017; SkillCorner 2013725 +0.018, 2016236 +0.032, 2017461 +0.040.

On BAR–ATH (counts only): the ball is observed more than 1 m outside the lines on 2,207 frames in 56 runs; the rule
changes 841 submission frames, all H/A → D. Candidate v10 = v9 + this rule (`ball_out_rule.py`, branch
`candidate/ball-out-rule`), expected SHA-256 `c86cf7ee…`. Swapping it in is the user's decision.
