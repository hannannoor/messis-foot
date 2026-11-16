# MESSI's FOOT: possession labelling for BAR–ATH (technical document)

## 1. Summary

We label all 199,319 frames of BAR–ATH as H, A, D or X with a fully automatic pipeline.

1. **Features:** label-free geometry features computed from the provided tactical tracking.
2. **Evidence:** per-frame H/A/D evidence from sequence models (bidirectional GRUs plus gradient-boosted trees) trained only on external matches.
3. **Decoder:** a 3-state Viterbi decoder whose switch cost drops at detected ball contacts and at predicted possession boundaries.
4. **Gap rule:** a label-free rule that turns long, slow ball-tracking gaps into dead ball.
5. **Kickoff patch:** an automatic patch from the Smart Tagging kickoff tags.

Reproduce the submitted file from the repository (`$prefix` is the local tactical filename prefix; `$out` must be a new directory):

```powershell
python strong_release.py --prefix "$prefix" --tags "${prefix}_smart_tagging.xml" --out "$out"
```

Expected output: `submission.csv` with 199,319 rows, SHA-256 `ed97ae735a57e81dbd788f94c40de210dcbcb5aed40bc94d9552f1dade2897cd`. Two independent CPU runs are byte-identical, and the official `validate_submission.py` passes.

Code: https://github.com/hannannoor/messis-foot/tree/experiment/strong-emissions (submission built at commit `cd07b0e`).

## 2. Approach and why

**Why possession objects, not frames.** spellF1 matches whole possessions, so a pipeline must neither fragment a possession (spurious switches) nor merge two (missed switches). We therefore produce smooth per-frame *evidence* and leave the segmentation to a decoder that pays for every switch.

**Features** ([`se_features.py`](../se_features.py)). 241 per-frame features, all computed from positions alone, with no labels:

- **Ball–player geometry:** nearest-player distances per team, players within 2/5/10 m, closing speeds, ball velocity in each team's attacking direction.
- **Ball contacts:** a contact is a peak in the ball's velocity change with a player within 2 m. Features cover the last and next contact (which team, how long ago or until), with a reliability flag for contacts at the edge of a tracking gap.
- **Player-only team shape:** each team described in its own attacking direction: centroid depth, defensive line, length and width, forward and backward runners, and marking distance, plus ±2/5/15 s window means.
  - These matter because the ball is missing on 41% of graded frames.
  - Example: the team in possession is about 9 m wider and moves forward rather than back.
- **Missing-ball timing:** time since and until the ball was last and next observed.

**Evidence models** ([`se_gru.py`](../se_gru.py), [`se_train.py`](../se_train.py)). Two model sets, combined as a geometric blend (0.15 × set A + 0.85 × set B), then squared and renormalised.

- **Each set:** two bidirectional GRUs (2 layers, 128 hidden units, 60 s training chunks) plus a pair of HistGradientBoosting heads (ownership and live/dead).
- **Home/away swap augmentation** and swap-averaged inference make both models team-symmetric.
- **Loss:** short possessions are up-weighted, because spellF1 counts each possession equally.
- **Set A** (171 features, no team shape) protects clean-tracking accuracy.
- **Set B** (241 features) is trained with copies of the D-labelled matches in which the ball *and* some players are removed. The removal follows the provided tracking's rates: about 10.1 tracked players per team, with the ball missing in runs.
- **Set B's GRUs also predict possession boundaries** as an auxiliary output. This multi-task signal improved every evaluation view.

**Decoder** ([`se_assembly.py`](../se_assembly.py), [`strong_runtime.py`](../strong_runtime.py)). A 3-state Viterbi over the evidence, decoding offline within each half:

- **Switch cost 20.** It drops to 10 within ±6 frames of a detected ball contact, and towards 8 where the boundary output fires.
- Changes of possession therefore need sustained evidence, except at moments where a real contact or a learned boundary makes a change plausible.

**Gap rule** ([`gap_liveness.py`](../gap_liveness.py)). A ball-tracking gap longer than 3 s becomes D when the median player speed inside it is below the match's typical speed outside long gaps. The rule uses no labels and no constants tied to this match's frames.

**Kickoff patch** ([`kickoff_patch.py`](../kickoff_patch.py)). Graded frames before each half's automatic `Kick Off (Start)` tag are set to D.

**Why the gap rule is in, after we had removed it.** We removed it because it hurts when the ball is dropped at random, which is how we first simulated ball loss. BAR–ATH's inputs show, label-free, that its ball loss is not random:

- the ball is missing in about 150 blocks, 133 of them longer than 3 s;
- it is missing on 77% of frames where most players stand still, against 19% where they move.

Long gaps there overwhelmingly look like stoppages, so the rule is back. We have no external measurement of its benefit (see §6 and §7).

## 3. Assets used and dropped

**Used:**
- tactical tracking (`_atd.xml`, `_atd.txt`);
- homography (geometry validity);
- from Smart Tagging, only `Kick Off (Start)`.

Everything runs locally on the provided files.

| Tried and dropped | Why |
|---|---|
| Broadcast video and broadcast tracking | No reliable automatic alignment to the tactical timeline. |
| Smart Tagging phases as ownership evidence | Failed an external ownership test (earlier phase). |
| 31-node decision tree (previous release) | Replaced by the sequence models (+0.19 spellF1 on external holdout matches). |
| Decoder-only tweaks: costs, power, separate dead-ball cost | Within noise. |
| Wider GRU; stronger augmentation dose; 5 rather than 3 dropout copies | No gain, or the gain didn't generalise across evaluation views. |
| Restart and set-piece features (stillness, box crowding, corners) | Signal already captured by existing speed features; within noise. |
| Longer (±30 s) team-shape windows | Clean accuracy dropped. |

## 4. Training and evaluation data

No label, annotation or human-produced data about BAR–ATH was used for training, tuning or selection. BAR–ATH enters only at inference. The repository's public 5-minute ground truth was used once, only as a pipeline-correctness check on the final file (orientation, frame alignment, label meaning), never to compare or choose versions.

| Dataset (source, licence) | Labels: who and how | Amount | Use |
|---|---|---|---|
| [DFL / Sportec Solutions open data](https://doi.org/10.6084/m9.figshare.28196177.v1) (Bassek, Rein, Weber, Memmert 2025), CC BY 4.0 | Provider `BallPossession`/`BallStatus` from official DFL data (Sportec; trained analysts with quality control, per the paper) | 7 matches (J03WMX, J03WN1, J03WOH, J03WOY, J03WPY, J03WQQ, J03WR9), about 145,000 frames each | H/A/D training and evaluation |
| [SkillCorner open data](https://github.com/SkillCorner/opendata), MIT | Provider possession phases; H/A on known play, no dead-ball labels | 10 matches | H vs A training (conditional loss) and evaluation |
| [WCSF SolutionRoom](https://github.com/MatKempeGroningen/WCSF_SolutionRoom), MIT | Manual SciSports alive/possession annotations; 10 Hz tracking resampled to 25 Hz | 1 match | H/A/D training (final model) and holdout evaluation |
| [Metrica Sports sample data](https://github.com/metrica-sports/sample-data) | Owners derived algorithmically from the public event data; dead ball taken from the ball coordinates, which are blank while play is stopped ([`metrica_ball_reference.py`](../metrica_ball_reference.py)) | 3 matches | Evaluation only (ownership) |

**Splits.**
- Development: 13 matches with grouped 4-fold cross-validation.
- Locked holdout: 5 matches (WCSF, DFL J03WN1, SkillCorner 2013725/2016236/2017461), fixed before modelling.
- The submitted models are retrained on all 18 labelled matches.
- Training copies with ball and player dropout are generated algorithmically from the DFL and WCSF matches ([`se_degrade.py`](../se_degrade.py)).

## 5. Possession rules implemented

- **Ball in play vs dead.**
  - D comes from three sources: the models' live/dead evidence, the gap rule (long ball gaps with slow players), and the kickoff patch.
  - We never assign dead-ball ownership.
- **Change of possession = sustained control.** Because every switch costs something, a single touch, a deflection or a brief challenge does not flip ownership unless the evidence afterwards keeps favouring the other team. Switches are cheaper exactly where a ball contact is detected or the boundary output fires, which is where controlled changes happen.
- **Loose and contested balls** keep the last team's possession: the decoder carries the current state unless the evidence pays for a switch.
- **Missing ball inside play:** evidence comes from team shape (width, runners, defensive line) and from the nearest contacts before and after the gap. Short gaps rarely change ownership; long, slow gaps become D.
- **Restarts:** after a D stretch, possession starts with whichever team the evidence supports. There is no carry-over rule across a stoppage.
- **X:** only outside the graded periods (before kickoff, halftime, after the final whistle). Inside play every frame gets H, A or D.

## 6. Evidence

Spell F1 throughout, scored on external data only.

| Version | Change | Locked holdout (5) | Dev CV (13) | Metrica samples, ownership only (3) |
|---|---|---:|---:|---:|
| Previous release | Decision tree + gap rule | 0.536 | 0.584 | 0.631 |
| v4 | Sequence models + ball contacts | 0.759 | 0.798 | 0.870 |
| v6 | + team shape, 3 ball-dropout copies | 0.767 | 0.800 | 0.867 |
| v8 | + player dropout, boundary output | 0.783 | 0.809 | 0.878 |
| **v9 (submitted)** | **+ gap rule reinstated** | – | **0.808** | **0.878** |

- **Holdout:** the locked holdout was looked at 8 times over the project, so we treat it as confirmation only.
- **Metrica** gives three matches from the same tracking vendor that no model was trained on.
  - Their ball coordinates are blank exactly while play is stopped, so dead-ball detection cannot be tested there: any missing-ball rule is right by construction.
  - We therefore score ownership only. The reference's dead-ball frames are imposed on every prediction, and the score measures whether the H/A possessions are right.
  - v9 equals v8 in this column because the gap rule only changes dead-ball calls.
- **Withdrawn figure:** an earlier version of this document quoted 0.794 for v9 on the Metrica games, as evidence for the gap rule. It used an event-derived reference that mislabelled 11–14% of frames, the gap-rule stage was chosen on those games, and the gain was true by construction. We no longer quote it.
- **Gap rule (v9):** it rests on BAR–ATH's label-free input statistics (§2), not on a measured gain.
- **Version choices (v4–v8):** these were made on dev cross-validation over several simulated ball-loss views, with paired per-match differences and two training seeds. Those views removed the ball at random with respect to play, which BAR–ATH does not do, so they say less about BAR–ATH than we first assumed.
- **Full history:** [docs/strong-emissions-results.md](strong-emissions-results.md).

## 7. Limitations

- **Proxy labels.** External labels follow other providers' conventions:
  - SkillCorner has no dead-ball labels;
  - Metrica's owners are derived from events, and its dead ball from blanked ball coordinates;
  - the challenge's ground truth comes from corrected tracking.

  Boundary timing and dead-ball edges may differ systematically from BAR–ATH's reference.
- **Gap rule assumption.** It assumes BAR–ATH's long ball gaps mean stopped play, as its input statistics suggest. No external data tests this:
  - DFL freezes the ball during stoppages;
  - Metrica blanks it;
  - SkillCorner has no dead-ball labels.

  Long, slow gaps inside live play would be mislabelled D, and the timing of dead ball at the edges of a gap is unvalidated.
- **Weak spots:**
  - possessions shorter than 2 s (about half found, even with the ball visible);
  - long possessions with the ball missing;
  - dead-ball timing when the ball stays in view. On WCSF, the one external match where the ball is neither frozen nor blanked in stoppages, dead-ball handling costs v8 about 0.09 spellF1 (0.764 as predicted, 0.853 with dead ball taken from the reference).
- **Simulated degradation.** Ball and player loss in training are simulated from aggregate rates and placed at random with respect to play, whereas BAR–ATH loses the ball mainly in long blocks. We cannot measure BAR–ATH's real error modes without its labels.
- **With more time:** model ball and player loss that follows the state of play instead of random gaps, and add training data in which the ball stays visible and moving through stoppages.

## 8. Reproduction

- **Inference** (what produces the submission): CPython 3.14.5 + numpy 2.5.1. The models run as plain numpy, deterministically on CPU, in about 4 minutes. Weights are committed in `strong_model/` (`gru.npz`, `gbm.npz` for set A; `gru8.npz`, `gbm8.npz` for set B). Run the command in §1, then:

  ```powershell
  python evaluation/validate_submission.py <out>/submission.csv
  ```

  (from the challenge repository).
- **Training** (to rebuild the weights):
  - GRUs: PyTorch 2.8 (CUDA).
  - Boosted trees: Python 3.12 with scikit-learn 1.5.1 (`requirements-training.txt`).
  - Pipeline:
    1. `se_extract.py` (features), then `se_append.py` (feature groups);
    2. `se_degrade.py` (dropout copies);
    3. `se_gru.py <tag> all` and `se_train.py <tag> all`;
    4. `se_export_gru.py` / `se_export_gbm.py`.
  - The external datasets must be downloaded separately from the sources above.
  - GPU training is not bit-reproducible across hardware. The submission is reproducible exactly from the committed weights.
- **Data:** no match data is in the repository.
