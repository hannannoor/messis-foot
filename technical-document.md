# MESSI's FOOT: possession labelling for BAR–ATH (technical document)

## 1. Summary

We label all 199,319 frames of BAR–ATH as H, A, D or X with a fully automatic pipeline. Nothing about BAR–ATH was hand-labelled, and no model saw BAR–ATH before inference.

1. **Features:** 241 label-free geometry features per frame, computed from the provided tactical tracking.
2. **Evidence:** per-frame H/A/D evidence from sequence models (bidirectional GRUs plus gradient-boosted trees) trained only on other matches.
3. **Decoder:** a 3-state Viterbi decoder whose switch cost drops at detected ball contacts and at predicted possession boundaries.
4. **Gap rule:** a label-free rule that turns long, slow ball-tracking gaps into dead ball.
5. **Kickoff patch:** graded frames before each half's automatic kickoff tag become dead ball.
6. **Ball-out rule (v10):** a ball tracked more than 1 m outside the lines is dead, through the tracking gap that follows.

Reproduce the submitted file from the repository (`$prefix` is the local tactical filename prefix; `$out` must be a new directory):

```powershell
pip install -r requirements.txt
python strong_release.py --prefix "$prefix" --tags "${prefix}_smart_tagging.xml" --out "$out"
```

Expected output: `submission.csv` with 199,319 rows, SHA-256 `c86cf7ee8b04dec4dfb5fee3c2eea01e6ed76f6a2733ce3398a97e9fc2fb7fe7`. Independent CPU runs are byte-identical, and the official `validate_submission.py` passes.

Code: https://github.com/hannannoor/messis-foot, branch `main`. The submission was built at commit `cd07b0e`. On 17 November the repository was reorganised (submission files at the root, all other code in `development/`, no change in behaviour); a fresh clone of `main` reproduces the same file.

**Results in brief.** The submission is v10. On external matches the models were never trained on, spellF1 is 0.783 on our five locked holdout matches (v8 models; v9 adds the gap rule, v10 the ball-out rule), against 0.536 for our first release (§6). The ball-out rule, the last change, raised spellF1 on all 17 SkillCorner matches (+0.022) and on WCSF (+0.004), and cost 0.002 on DFL. A late check on 17 SkillCorner matches, with dead-ball labels derived from SkillCorner's own public stoppage events, supports the gap rule: it raised spellF1 on every one of them (+0.017 on average). The same check shows our largest remaining weakness: the models label only about half of the stoppage frames there as dead ball (§6, §7). The organisers' published baseline on BAR–ATH is 0.2433.

## 2. Approach and why

**Why possession objects, not frames.** spellF1 matches whole possessions, so a pipeline must neither fragment a possession (spurious switches) nor merge two (missed switches). We therefore produce smooth per-frame *evidence* and leave the segmentation to a decoder that pays for every switch.

**Why learned evidence rather than rules.** The baseline family (nearest player to the ball, then smoothing) has no answer on the 41% of graded frames where the ball is missing, and it cannot tell a controlled touch from a deflection. Open datasets with possession and ball-status labels exist for other matches, so we learn the evidence there and keep the temporal logic in an explicit decoder that can be inspected and tuned separately. Our previous release was a 31-node decision tree on similar geometry; the sequence models beat it by 0.19 to 0.25 spellF1 on every external check (§6).

**Why not our own ball tracking from video.** We had no labelled video of other matches to train and validate a ball detector on, and BAR–ATH itself may not be labelled. We chose to make the possession model robust to the missing ball instead.

**Features** ([`se_features.py`](development/se_features.py)). All computed from positions alone, with no labels:

- **Ball–player geometry:** nearest-player distances per team, players within 2/5/10 m, closing speeds, ball velocity in each team's attacking direction.
- **Ball contacts:** a contact is a peak in the ball's velocity change with a player within 2 m. Features cover the last and next contact (which team, how long ago or until), with a reliability flag for contacts at the edge of a tracking gap.
- **Player-only team shape:** each team described in its own attacking direction: centroid depth, defensive line, length and width, forward and backward runners, and marking distance, plus ±2/5/15 s window means. Example: the team in possession is about 9 m wider and moves forward rather than back.
- **Missing-ball timing:** time since and until the ball was last and next observed.

**Evidence models** ([`se_gru.py`](development/se_gru.py), [`se_train.py`](development/se_train.py)). Two model sets, combined as a geometric blend (0.15 × set A + 0.85 × set B), then squared and renormalised.

- **Each set:** two bidirectional GRUs (2 layers, 128 hidden units, 60 s training chunks) plus a pair of HistGradientBoosting heads (ownership and live/dead).
- **Home/away swap augmentation** and swap-averaged inference make both models team-symmetric.
- **Loss:** short possessions are up-weighted, because spellF1 counts each possession equally.
- **Set A** (171 features, no team shape) protects accuracy when tracking is clean.
- **Set B** (241 features) is trained with degraded copies of the matches (see below), and its GRUs also predict possession boundaries as an auxiliary output.

**Decoder** ([`se_assembly.py`](development/se_assembly.py), [`strong_runtime.py`](development/strong_runtime.py)). A 3-state Viterbi over the evidence, decoding offline within each half:

- **Switch cost 20.** It drops to 10 within ±6 frames of a detected ball contact, and towards 8 where the boundary output fires.
- Changes of possession therefore need sustained evidence, except at moments where a real contact or a learned boundary makes a change plausible.

**Gap rule** ([`gap_liveness.py`](development/gap_liveness.py)). A ball-tracking gap longer than 3 s becomes D when the median player speed inside it is below the match's typical speed outside long gaps. D then continues past the end of the gap for as long as the reappeared ball is nearly still (under 0.5 m/s, at most 10 s). The rule uses no labels and no constants tied to this match's frames.

**Ball-out rule** ([`ball_out_rule.py`](development/ball_out_rule.py), v10). A ball tracked more than 1 m outside a touchline or goal line is dead, and D continues through the ball-tracking gap that directly follows (the ball went out, then left the camera's view). When the ball comes back onto the pitch while still tracked (a throw-in or a kick taken from outside the line), D is released 0.4 s before it re-enters, because play restarts while the ball is just outside. It changes 841 of BAR–ATH's 199,319 labels, all from H/A to D.

**Kickoff patch** ([`kickoff_patch.py`](development/kickoff_patch.py)). Graded frames before each half's automatic `Kick Off (Start)` tag are set to D. The halves themselves come from the period field of the tracking file.

**How missing and noisy tracking is handled.**

- **No player identities, fragmented tracks, identity switches:** every feature is an identity-free aggregate per team (nearest distances, counts, team shape), so track swaps within a team do not matter.
- **Missing players** (about 10.1 tracked per team on BAR–ATH): set B is trained on copies of the D-labelled matches with players removed at that rate.
- **Missing ball inside play:** the same copies also remove the ball in runs. The models keep producing evidence on missing-ball frames from team shape, missing-ball timing and the contacts either side of the gap.
- **Long ball gaps:** handled by the gap rule. We had removed it because it hurts when the ball is dropped at random, which is how we first simulated ball loss. BAR–ATH's inputs show, label-free, that its ball loss is not random:
  - the ball is missing in about 150 blocks, 133 of them longer than 3 s;
  - it is missing on 77% of frames where most players stand still, against 19% where they move.

  Long gaps there overwhelmingly look like stoppages, so the rule is back. We have no external measurement of its benefit (see §6 and §7).

## 3. Assets used and dropped

**Used:**
- tactical tracking (`_atd.xml`, `_atd.txt`);
- tactical homography (only as a per-frame geometry validity check);
- from Smart Tagging, only `Kick Off (Start)`.

Everything runs locally on the provided files.

| Tried and dropped | Why |
|---|---|
| Tactical video | Not used. We had no labelled video of other matches to build and validate our own ball detection. |
| Broadcast video and broadcast tracking | No reliable automatic alignment to the tactical timeline. |
| Smart Tagging phases as ownership evidence | Failed an external ownership test (earlier phase). |
| 31-node decision tree (previous release) | Replaced by the sequence models (+0.19 spellF1 on external holdout matches). |
| Decoder-only tweaks: costs, power, separate dead-ball cost | Within noise. |
| Wider GRU; stronger augmentation dose; 5 rather than 3 dropout copies | No gain, or the gain didn't generalise across evaluation views. |
| Restart and set-piece features (stillness, box crowding, corners) | Signal already captured by existing speed features; within noise. |
| Longer (±30 s) team-shape windows | Clean accuracy dropped. |
| Training on ball loss that follows the state of play (after v9) | The models relearn what the gap rule already does. No gain with the rule on, and −0.03 on WCSF. |
| Metrica sample games as extra training data (after v9) | +0.03 on Metrica itself, but −0.004 on the holdout and −0.01 on WCSF. |
| Self-training on each match's own decoded labels (pseudo-labels, after v9) | Ownership +0.008 ± 0.004 (below our 2-SE bar), and WCSF −0.037: it reinforces dead ball the models already miss. |
| SkillCorner stoppages as dead-ball training labels (after v9) | +0.125 on SkillCorner, but −0.012 on WCSF and −0.006 on DFL, where dead ball comes from tracking. |

## 4. Training and evaluation data

No label, annotation or human-produced data about BAR–ATH was used for training, tuning or selection. BAR–ATH enters only at inference. The organisers' public 5-minute ground truth was used only as a pipeline-correctness check (orientation, frame alignment, label meaning), never to compare or choose versions.

All four datasets are public. We added no hand labels of our own; the SkillCorner stoppage labels are derived by code from the provider's public events.

| Dataset (source, licence) | Labels: who and how | Amount | Use |
|---|---|---|---|
| [DFL / Sportec Solutions open data](https://doi.org/10.6084/m9.figshare.28196177.v1) (Bassek, Rein, Weber, Memmert 2025), CC BY 4.0 | Provider `BallPossession`/`BallStatus` from official DFL data (Sportec; trained analysts with quality control, per the paper) | 7 matches (J03WMX, J03WN1, J03WOH, J03WOY, J03WPY, J03WQQ, J03WR9), about 145,000 frames each | H/A/D training and evaluation |
| [SkillCorner open data](https://github.com/SkillCorner/opendata), MIT | Provider possession phases; H/A on known play, no dead-ball labels. For the dead-ball check (§6) we derived stoppages algorithmically from the provider's public dynamic events (`game_interruption_before`: throw-in, free kick, goal kick, corner, kick-off) | 10 matches; 10 more for evaluation only | H vs A training (conditional loss) and evaluation |
| [WCSF SolutionRoom](https://github.com/MatKempeGroningen/WCSF_SolutionRoom), MIT | Manual SciSports alive/possession annotations; 10 Hz tracking resampled to 25 Hz | 1 match | H/A/D training (final model) and evaluation |
| [Metrica Sports sample data](https://github.com/metrica-sports/sample-data) | Owners derived algorithmically from the public event data; dead ball taken from the ball coordinates, which are blank while play is stopped ([`metrica_ball_reference.py`](development/metrica_ball_reference.py)) | 3 matches | Evaluation only (ownership) |

**Splits.**
- Development: 13 matches with grouped 4-fold cross-validation.
- Locked holdout: 5 matches (WCSF, DFL J03WN1, SkillCorner 2013725/2016236/2017461), fixed before modelling.
- The submitted models are retrained on all 18 labelled matches (7 DFL, 10 SkillCorner, 1 WCSF).
- Training copies with ball and player dropout are generated algorithmically from the DFL and WCSF matches ([`se_degrade.py`](development/se_degrade.py)).

## 5. Possession rules implemented

- **Ball in play vs dead.**
  - D comes from four sources: the models' live/dead evidence, the gap rule (long ball gaps with slow players), the ball-out rule (ball tracked outside the lines), and the kickoff patch.
  - We never assign dead-ball ownership.
- **Change of possession = sustained control.** Because every switch costs something, a single touch, a deflection or a won aerial duel does not flip ownership unless the evidence afterwards keeps favouring the other team. Switches are cheaper exactly where a ball contact is detected or the boundary output fires, which is where controlled changes happen.
- **Loose and contested balls** keep the last team's possession: the decoder carries the current state unless the evidence pays for a switch.
- **Missing ball inside play:** evidence comes from team shape and from the nearest contacts before and after the gap. Short gaps rarely change ownership; long, slow gaps become D.
- **Restarts:** after a D stretch, possession starts with whichever team the evidence supports. There is no carry-over rule across a stoppage.
- **Before kickoff:** graded frames before each half's kickoff are D. This covers the second half, which is graded from before its kickoff.
- **X:** only outside the two halves (before the match, halftime, after the final whistle). Inside them every frame gets H, A or D.

## 6. Evidence

Spell F1 throughout, scored on external data only. BAR–ATH's full-match ground truth is private, so none of these figures is a BAR–ATH score; the organisers' published floor there is 0.2433.

| Version | Change | Locked holdout (5) | Dev CV (13) | Metrica samples, ownership only (3) |
|---|---|---:|---:|---:|
| Previous release | Decision tree + gap rule | 0.536 | 0.584 | 0.631 |
| v4 | Sequence models + ball contacts | 0.759 | 0.798 | 0.870 |
| v6 | + team shape, 3 ball-dropout copies | 0.767 | 0.800 | 0.867 |
| v8 | + player dropout, boundary output | 0.783 | 0.809 | 0.878 |
| v9 | + gap rule reinstated | – | 0.808 | 0.878 |
| **v10 (submitted)** | **+ ball-out rule** | see below | see below | – |

- **Holdout:** the locked holdout was looked at 9 times over the project, so we treat it as confirmation only.
- **Metrica** gives three matches from the same tracking vendor that no submitted model was trained on.
  - Their ball coordinates are blank exactly while play is stopped, so dead-ball detection cannot be tested there: any missing-ball rule is right by construction.
  - We therefore score ownership only. The reference's dead-ball frames are imposed on every prediction, and the score measures whether the H/A possessions are right.
  - v9 equals v8 in this column because the gap rule only changes dead-ball calls.
- **Ball-out rule (v10):** same models and decoder, rule applied afterwards, rules for passing fixed before the run. SkillCorner (17 matches, dead-ball labels derived from the provider's public stoppage events) +0.022 ± 0.002, all 17 up; SkillCorner holdout +0.018, +0.032, +0.040; WCSF +0.004; DFL dev −0.0019 and DFL holdout −0.0017, because DFL marks a throw-in live a moment before the ball re-enters. It was the sixth rule variant tried, so its pass is narrow.
- **Gap rule (v9):** it rests on BAR–ATH's label-free input statistics (§2), not on a measured gain.
- **Version choices (v4–v8):** these were made on dev cross-validation over several simulated ball-loss views, with paired per-match differences and two training seeds. Those views removed the ball at random with respect to play, which BAR–ATH does not do, so they say less about BAR–ATH than we first assumed.
- **Checks after v9:** two further retrains were tested against v9's recipe and rejected (§3). WCSF was moved out of the holdout for the first of them. The second was checked on the four remaining holdout matches: 0.785 without the extra games against 0.781 with them.
- **Gap rule on SkillCorner (17 November).** SkillCorner's ball is detected 23% of the time inside stoppages and 75% outside, the same pattern as BAR–ATH. We derived dead-ball labels from its public stoppage events (from the end of the last on-ball event to the restart; edges are approximate) and scored v8-recipe models that never trained on the match, with the release decoder, on 17 matches (7 dev, cross-validated; 10 further public matches). spellF1: 0.553 without the gap rule, 0.571 with it (better on all 17); the best of 60 alternative gap-rule settings gained only 0.002, so the submitted constants were kept. Dead-ball recall is 0.47 at precision 0.975; dead ball taken from the reference would give 0.813.
- **Full history:** [development/docs/strong-emissions-results.md](development/docs/strong-emissions-results.md).

## 7. Limitations

- **Proxy labels.** External labels follow other providers' conventions: SkillCorner has no dead-ball labels, and Metrica's owners are derived from events. The challenge's ground truth comes from corrected tracking, so boundary timing and dead-ball edges may differ systematically from what our models learned.
- **Gap rule assumption.** It assumes BAR–ATH's long ball gaps mean stopped play, as its input statistics suggest. SkillCorner, where the ball also disappears mostly in stoppages, supports this (§6), but its dead-ball labels come from events with approximate edges, and its broadcast camera differs from BAR–ATH's tactical one. The submission labels about 95% of BAR–ATH's missing-ball frames as D, so this remains our largest single unknown.
- **Missed dead ball.** On SkillCorner the models label only about half of the stoppage frames as D. Training on the event-derived stoppages fixed that on SkillCorner (+0.125 spellF1) but lowered WCSF (−0.012) and DFL (−0.006), our checks with tracking-derived dead ball, so it was not adopted (§3).
- **Weak spots:**
  - possessions shorter than 2 s (about half found, even with the ball visible);
  - long possessions with the ball missing;
  - dead-ball timing when the ball stays in view. On WCSF, the one external match where the ball is neither frozen nor blanked in stoppages, dead-ball handling costs v8 about 0.09 spellF1 (0.764 as predicted, 0.853 with dead ball taken from the reference).
- **Simulated degradation.** Ball and player loss in training are simulated from aggregate rates and placed at random with respect to play, whereas BAR–ATH loses the ball mainly in long blocks. We cannot measure BAR–ATH's real error modes without its labels.
- **With more time:**
  - training data in which the ball stays visible and moving through stoppages, to fix dead-ball timing (WCSF is our only such match);
  - a decoder that scores whole possessions, aimed at the short ones we miss;
  - ball re-detection from the tactical video inside tracking gaps, validated on other matches.

## 8. Reproduction

- **Inference** (what produces the submission): CPython 3.14.5 + numpy 2.5.1, pinned in `requirements.txt`. The models run as plain numpy, deterministically on CPU, in under 10 minutes on a laptop. Weights are committed in `strong_model/` (`gru.npz`, `gbm.npz` for set A; `gru8.npz`, `gbm8.npz` for set B). Run the commands in §1, then from the challenge repository:

  ```powershell
  python evaluation/validate_submission.py <out>/submission.csv
  ```

- **Training** (to rebuild the weights):
  - GRUs: PyTorch 2.8 (CUDA).
  - Boosted trees: Python 3.12 with scikit-learn 1.5.1 (`requirements-training.txt`).
  - Pipeline, run from `development/`: `se_extract.py` and `se_append.py` (features), `se_degrade.py` (dropout copies), `se_gru.py <tag> all` and `se_train.py <tag> all` (models), then `se_export_gru.py` / `se_export_gbm.py` (weights, copied to `strong_model/`).
  - The checks added after v9 (self-training, SkillCorner dead-ball labels: `se_sc_dead.py`, `se_pseudo.py`) are on branch `experiment/self-training`.
  - The external datasets must be downloaded separately from the sources in §4.
  - GPU training is not bit-reproducible across hardware. The submission is reproducible exactly from the committed weights.
- **Data:** no match data is in the repository.
