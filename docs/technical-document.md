# MESSI's FOOT â€” possession submission

## 1. Summary

We submit one H/A/D/X label per original video frame. The pipeline is the frozen control, a missing-ball gap rule, decoder restart across selected stoppage gaps, then an automatic kickoff patch. Run from the checkout, with `$prefix` set to the tactical filename prefix and `$out` to a new absolute output directory:

```powershell
python -I restart_release.py --prefix "$prefix" --tags "${prefix}_smart_tagging.xml" --out "$out"
```

The CSV has 199,319 rows. SHA-256: `15756bcb57f184d717a5bc8f30b15a8777227165dd4973edbbaf69ba6a02a685`.

## 2. Approach and why

The ranking metric matches whole possession spells, so fragmented labels are expensive. The [frozen control](https://github.com/hannannoor/messis-foot/blob/30a7ace010e3fc1ece23c440e54151058dbf8b19/release_runtime.py) uses 18 geometry and recent-control features, a fixed 31-node decision tree, and H/A/D log-emissions. State changes cost 32. The motion-head weight is zero. Decoding is offline within usable stretches and halves; later evidence can resolve earlier uncertainty. Outside graded periods labels are X.

The [gap rule](https://github.com/hannannoor/messis-foot/blob/30a7ace010e3fc1ece23c440e54151058dbf8b19/gap_liveness.py) considers consecutive missing-ball blocks longer than 75 frames. This three-second definition was chosen from the provided track's label-free long-gap investigation, not fitted to ground truth. Every fifth frame, associated players' one-second displacement speeds are filtered below 12 m/s; at least ten pairs are needed for a defined sample. A gap becomes D when its median defined sample is below the match median outside long gaps.

The [release wrapper](https://github.com/hannannoor/messis-foot/blob/30a7ace010e3fc1ece23c440e54151058dbf8b19/restart_release.py) decodes again with those stoppage-gap frames unusable, using identical emissions and switch costs. The [official definition](https://github.com/metrica-sports/more-than-a-hack-2027/blob/f8f2629ff1e0985f81d7e59d8413678514ee1530/CHALLENGE.md) says a restart has a clear possessor. The reset removes cross-gap decoder continuity; it does not rebuild the existing features. The gap rule is applied again, then the [kickoff patch](https://github.com/hannannoor/messis-foot/blob/30a7ace010e3fc1ece23c440e54151058dbf8b19/kickoff_patch.py) marks graded frames before each half's unique automatic kickoff tag D. Decoder parity and unchanged stoppage gaps are checked.

## 3. Assets used and dropped

Used: tactical `_atd.xml`, `_atd.txt`, `_homography.csv`; from Smart Tagging, only `Kick Off (Start)` enters prediction. Homography quality gates geometry. Anonymous player association is automatic. The entry point processes provided inputs locally.

| Tried and dropped | Reason |
|---|---|
| Broadcast camera and clock synchronisation | No usable automatic alignment links. |
| Learned motion model | External confidence-policy experiment failed its gates; selected weight is zero. |
| Velocity repair | Failed external liveness safeguards. |
| Smart Tagging attacking-phase ownership | Failed its external ownership test. |
| Ball-velocity touch evidence | Clean-track gains vanished at provided-like touch density. |
| Higher/lower switch cost | Helps one provider's labelling convention and harms another's. |

## 4. Training and evaluation data

According to the committed experiment records, no label of any kind from the provided match was used to train, tune or select. The public five minutes were used only for pipeline checks. Individual annotators and annotation error rates were not independently audited.

| Dataset, source and licence | Labels and amount | Use |
|---|---|---|
| [DFL / Sportec Solutions](https://doi.org/10.6084/m9.figshare.28196177.v1), CC BY 4.0; Bassek, Rein, Weber et al. | Provider BallStatus/BallPossession. Four fitting matches: J03WOH, J03WOY, J03WPY, J03WMX; J03WQQ validation; J03WR9/J03WN1 original test. | Tree fitting with original/fixed 30% masking; validation, selection and repeated evaluation. |
| [SkillCorner / PySport](https://github.com/SkillCorner/opendata/tree/4340d274572876239c154c90bc507a9b3250a656), MIT repository licence | Provider possession phases, H/A on known play; unannotated regions X, no D reference. Twenty exports: eight development, two calibration, two validation, eight diagnostic/test. | Research motion-model fitting, selection and evaluation; selected tree fitted on DFL. Ten reused in latest tests. |
| [WCSF SolutionRoom](https://github.com/MatKempeGroningen/WCSF_SolutionRoom/tree/1c9ba798f98a9fffb16081a5d3965774d4e5662c), MIT dataset terms per recorded source-owner clarification | One anonymous Dutch match, two halves; manual SciSports Alive/Possession annotations; smoothed 10 Hz tracking resampled to 25 Hz. | Transfer/evaluation only for the control; subsequently reused. |
| [Metrica Sports Sample Data](https://github.com/metrica-sports/sample-data/tree/e706dd506b360d69d9d123d5b8026e7294b13996) | Three sample matches; possession reference derived from provider events. Pinned README requests responsible use and source acknowledgement; no formal dataset licence stated there. | Evaluation only. Credit: Metrica Sports. Manually corrected tracks and event-reference conventions limit independence. |

## 5. Possession rules implemented

State changes need sustained evidence because of the switch cost: single touches, deflections and brief challenges do not normally flip ownership. Loose or contested balls tend to retain the last team through recent-control features and sequence decoding. Short missing-ball stretches have neutral emissions; the decoder uses both sides, so the previous owner is not always carried.

D comes from the tree, gap rule and kickoff patch. After a selected stoppage gap, the decoder starts a fresh sequence using post-gap emission rows, with no cross-gap decoder state. The unchanged rows still contain recent-control features whose history can predate the gap; that feature memory is not reset. The inherited abstention materialisation forward-fills then head-backfills within each period; an entirely unknown active period defaults to D. These conventions are not adjudicated possession truth.

## 6. Evidence

Spell F1 is averaged over temporal IoU thresholds 0.3â€“0.7. DFL/WCSF primary means weight the two primary DFL matches one quarter each and WCSF one half. [Committed evidence](https://github.com/hannannoor/messis-foot/tree/codex/restart-release-2026-11-11/reports) contains counts and protocols.

| Check | Result | Caveat |
|---|---|---|
| Fifteen external matches, natural | Control .551816 â†’ gap .550876. | Equal-provider mean on 13 fitting-disjoint primary matches; two fitting overlaps secondary. Reused matches, little labelled natural-gap support. |
| Same, random 30% masking | .469149 â†’ .438025; SkillCorner .555155 â†’ .479297. | Gap rule harms when missingness is unrelated to stoppages. |
| Three Metrica samples | .446712 â†’ .545105. | Partly circular tracking/reference construction. |
| Stoppage regimes: control â†’ gap | Natural .529441 â†’ .529441; stop100 .481276 â†’ .535956; stop75 .444251 â†’ .455214; stop50 .401310 â†’ .401842; stop75-jitter .343783 â†’ .401270. | No primary-mean loss; WR9 loses .011672 in stop75 and .026738 in stop50. Reference-built masks model, rather than measure, provided missingness. |
| Touch transfer / restart | Touch failed B/C: thinned SC confirmation âˆ’.014216; primary gain âˆ’.002969. Restart passed E/F/G; gains WN1 +.009363, WR9 +.016101, WCSF +.021546, WOH +.011955, WOY +.011527; SC confirmation .000000. | Post-hoc, reused evidence; two reset-gating matches establish consistency, not population benefit. |
| Provided, label-free | Final D 41.458%; 113 of 133 long gaps relabelled; 434 → 415 spells; 388 changed frames (0.244%); 29 → 9 spells under 25 frames; 19 gaps change first owner. | Coverage and fewer spells do not measure correctness. |
| Public five minutes, once after decision | Spell F1 0.360976, macro F1 0.677701, accuracy 0.734667; 24 predicted / 17 reference spells. Previous candidate: .362 / .677 / .734, 25 / 17 spells. | Pipeline check only; 17 reference spells cannot rank these files. Numbers chose nothing. |

The organisers' published full-match baseline is .2433. Our full-match score is unknown.

## 7. Limitations

Neither the gap rule nor restart has labelled validation on tracking with this exact gap pattern. The rule relabels an entire gap and can erase live play. It has no minimum count of defined speed samples inside a gap: the 113 relabelled gaps have minimum/10th-percentile/median support 24/30/64 samples, none below five; 3 of 20 unclassified gaps have no defined sample. 11 selected gaps are within 10% below the speed threshold, accounting for 4.967% of relabelled frames.

Restart gains are about .01â€“.02 on DFL-type references and zero on the SkillCorner confirmation mean. Tagged set-piece match/mismatch/no-transition counts are 15/9/3 before and 14/10/3 after restart. Corner agreement fell 10/12 → 6/12; goal kicks improved 2/7 → 4/7 among those with a transition, and free kicks 3/5 → 4/5. At corners, the pre-stoppage team usually also takes the restart, so removing continuity can hurt; this is an interpretation, not an independently measured cause.

The gap rule's restart extension is inactive. The kickoff tag starts a few seconds before play; the remaining short interval keeps its earlier labels. The team-role mapping in `gap_solver/input_contract.py` recognises this match's two team names; another match needs its names added. Geometry can be noisy, identities mistaken, or observations stale. All external matches were reused; none is a fresh holdout, and several ideas followed earlier rejections. With more time, we would obtain independent labelled long-gap tracking and test restart ownership by restart type before changing the rule.

Team to confirm: registration/form access, registered team name, and any use or disclosure of provided material outside the recorded local workflow.

## 8. Reproduction

Use CPython 3.14.5; inference is standard library only and uses no network. Acquire the permitted provided assets locally. Clone after the branch has been published:

```powershell
git clone https://github.com/hannannoor/messis-foot.git messis-foot
cd messis-foot
git checkout 30a7ace010e3fc1ece23c440e54151058dbf8b19
```

For format validation, obtain the pinned official code and its separate check dependencies before working offline:

```powershell
git clone https://github.com/metrica-sports/more-than-a-hack-2027.git official
git -C official checkout f8f2629ff1e0985f81d7e59d8413678514ee1530
python -m pip install numpy==2.5.1 pandas==3.0.5
```

These packages are for the official validator/scorer, not inference. Inference itself needs no package installation or network. Set `$official` to that checkout's absolute path.

Set `$prefix` to the local tactical filename prefix, `$out` to a nonexistent absolute folder, and `$official` to the local official repository folder. Run the command in section 1. Expected SHA-256 is `15756bcb57f184d717a5bc8f30b15a8777227165dd4973edbbaf69ba6a02a685`; compare the receipt and validate the exact CSV:

```powershell
python "$official/evaluation/validate_submission.py" "$out/submission.csv"
```

[Release tests](https://github.com/hannannoor/messis-foot/blob/30a7ace010e3fc1ece23c440e54151058dbf8b19/tests/test_restart_release.py) cover disabled-path parity, restart behaviour and deterministic output. Code links resolve after this branch is pushed.
