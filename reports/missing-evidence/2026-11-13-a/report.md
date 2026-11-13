# Experiment F — dead-ball evidence on missing-ball rows, run 2026-11-13-a: stage 1 FAIL, stress not run

## 1. Verdict

**FAIL at stage 1.** Half-weight (λ = 0.5) dead-ball evidence from Experiment E's stillness tree on missing-ball rows does not raise spell F1. Primary provider-weighted natural spell F1 is .5509537 for the control and .5507623 for the candidate, a change of **−0.00019** against a required +0.010. Stage 2 (noise, live-gap, stoppage) was not run.

## 2. Question

Does letting the stillness tree's dead-ball evidence act on missing-ball rows, at a fixed half weight, raise natural provider-weighted spell F1 by ≥ 0.010 without unacceptable losses? The protocol is `docs/missing-evidence-protocol.md`, frozen at `b76709f` before any score.

## 3. Provider results (natural, primary cases)

| Provider | Control | Candidate | Change |
|---|---|---|---|
| DFL | .5536652 | .5536652 | 0 |
| SkillCorner | .5939796 | .5934054 | −0.00057 |
| WCSF | .5052164 | .5052164 | 0 |
| **Primary** | **.5509537** | **.5507623** | **−0.00019** |

## 4. Where F acted

| Provider | Graded missing-ball rows | Rows turned to D | Of which reference D |
|---|---|---|---|
| DFL (4 matches) | 0 | 0 | 0 |
| SkillCorner (10) | 591,645 | 1,084 | 0 |
| WCSF (1) | 0 | 0 | 0 |

- The DFL and WCSF inputs have no missing-ball rows in the graded periods, so F cannot change anything there. This was not recorded among the limits before the run.
- On SkillCorner, F turned 1,084 rows (0.18% of missing rows) into D on 7 of 10 matches, and none of them is reference D.
- Two SkillCorner matches lost spell F1: 2010085 (−0.0020, 650 rows) and 2015213 (−0.0038, 90 rows). The rest are unchanged.

## 5. Gates (stage 1)

- **Failing:** gate 1 on all three parts:
  - spell gain −0.00019 (needs ≥ +0.010);
  - provider non-regression (SkillCorner −0.00057);
  - strict interior accuracy change exactly 0 (needs > 1e-6).
- **Passing:**
  - gate 2 per-match loss (worst −0.0038 against the −0.020 limit);
  - gate 3 (D precision and recall, false D, owner presence);
  - gate 4 short spells.
- No unresolved or non-applicable checks.

## 6. Integrity

- **Commits:** code `ce67ba9` (rule and assembly) and `b97d0bc` (harness and protocol); freeze `b76709f`; preflight `d7bffe2`; parity `0566c97`; natural `26609a3`; summary `b5532d5`.
- **Scratch dry run before the freeze:** preflight ready; parity passed at 0.5518160817; projected 150 of 200 feature/tree passes; the real ledger was untouched.
- **Parity, 15/15 each:**
  - release replica equals `restart_release.assemble`;
  - λ = 0 equivalence with the replica;
  - E-tree supports equal E's stored natural candidate supports;
  - feature prefix identical.
  The primary reconciliation reproduced .5518160817. That figure scores the first-decode labels against history; the .5509537 control above scores the final labels, so the two differ by design.
- **Budget used:** 30 case runs, 45 score bundles, 45 feature/tree passes, 60 decoder passes, 0 fits, 60 parity checks. All are within the caps of 100, 115, 200, 300 and 0.
- **Models:** E's committed trees, pinned by artifact and semantic SHA-256; no fit.
- **Public files:** these carry aggregates, case IDs and hashes only.

## 7. Interpretation and limits

- Under the release's input contract, missing-ball rows exist only in SkillCorner broadcast tracking. Their reference has no D, so any added D there can only be wrong. On DFL and WCSF, where D matters, the ball is never missing in graded periods, so F has nothing to act on.
- F's mechanism is therefore inert where it could help and harmful where it acts. Changing λ cannot fix this.
- This is consistent with Experiments D and E and the ownership-only check: the remaining spell-F1 loss lies in boundary placement on visible-ball rows, not in missing-ball rows.
- This report does not change the submission. No push, merge, release installation or challenge run is made from this report.
