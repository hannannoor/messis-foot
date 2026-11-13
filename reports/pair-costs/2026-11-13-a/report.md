# Experiment G — pair switch costs, run 2026-11-13-a: stage 1 FAIL, stress not run

## 1. Verdict

**FAIL at stage 1.** Replacing the single switch cost 32 with the 3×3 pair-cost table from training transitions lowers spell F1. Primary provider-weighted natural spell F1 is .5509537 for the control and .5458075 for the candidate, a change of **−0.0051** against a required +0.010. Stage 2 was not run.

## 2. Question

Does a 3×3 pair-cost table derived from training-match transition rates, with mean off-diagonal cost 32, raise natural provider-weighted spell F1 by ≥ 0.010 without unacceptable losses? The protocol is `docs/pair-costs-protocol.md`, frozen at `8e4a3ce` before any score.

## 3. The frozen cost table (computed in preflight, training data only)

| From \ to | H | A | D |
|---|---|---|---|
| H | 0 | 27.46 | 33.27 |
| A | 26.83 | 0 | 33.06 |
| D | 35.53 | 35.85 | 0 |

- **Transition counts:**
  - H→A 688, H→D 215;
  - A→H 689, A→D 198;
  - D→H 210, D→A 197.
- **Stays:** H 166,338, A 146,932, D 256,453.
- **Mean off-diagonal cost:** 32.
- The table equals the prior recorded in the protocol.

## 4. Provider results (natural, primary cases)

| Provider | Control | Candidate | Change |
|---|---|---|---|
| DFL | .5536652 | .5561918 | **+0.0025** |
| SkillCorner | .5939796 | .5760830 | **−0.0179** |
| WCSF | .5052164 | .5051479 | −0.00007 |
| **Primary** | **.5509537** | **.5458075** | **−0.0051** |

- **SkillCorner:** all 10 matches fall (−0.008 to −0.033).
- **DFL:** J03WN1 +0.0094, J03WR9 −0.0043. The two secondary training matches rise (+0.0055, +0.0045).
- **Strict interior accuracy falls on every provider:**

  | Provider | Change |
  |---|---|
  | DFL | −0.0037 |
  | SkillCorner | −0.0032 |
  | WCSF | −0.0008 |
  | All | −0.0026 |

## 5. Spell counts (final labels, primary cases)

| Provider | Spells, control → candidate | Shorter than 23 rows, control → candidate |
|---|---|---|
| DFL | 828 → 875 | 14 → 17 |
| SkillCorner | 3,963 → 4,169 | 39 → 45 |
| WCSF | 524 → 534 | 13 → 12 |

Cheaper team switches (54 instead of 64 for a round trip) add spells, and those extra spells are mostly wrong.

## 6. Gates (stage 1)

- **Failing:**
  - gate 1 spell gain (−0.0051);
  - gate 1 provider non-regression (SkillCorner and WCSF);
  - gate 1 strict interior accuracy (−0.0026);
  - gate 2 per-match loss: 4 matches beyond −0.020 (SkillCorner 1874553 −0.027, 1886347 −0.021, 2010085 −0.020, 2011166 −0.033).
- **Passing:** gate 3 (D precision and recall, false D, owner presence) and gate 4 short spells.

## 7. Integrity

- **Commits:** code `a6cea9f`, `59f121a` and `6b2573a` (decoder, rule and assembly, harness); freeze `8e4a3ce`; preflight `e2eda72`; parity `b737de5`; natural `18969a7`; summary `1bdf8bf`.
- **Scratch dry run before the freeze:** the table equalled the prior; parity passed at 0.5518160817; the real ledger was untouched.
- **Parity, 15/15 each:**
  - release replica equals `restart_release.assemble`;
  - uniform-32 matrix equivalence with the replica;
  - mask seals equal Experiment A's.
  The primary reconciliation reproduced .5518160817.
- **Budget used:** 30 case runs, 45 score bundles, 45 feature/tree passes, 60 decoder passes, 0 fits, 31 parity checks.
- **Public files:** these carry aggregates, case IDs and hashes only.

## 8. Interpretation and limits

- Training-rate pair costs make team switches cheaper. That helps one DFL match and the two DFL training matches (both used to derive the table, so in-sample), but it over-switches on SkillCorner broadcast tracking.
- Equal entry costs (the release) are better on this cohort. This agrees with Experiments D and E and the ownership-only check: the release's boundary costs are not too high.
- This report does not change the submission. No push, merge, release installation or challenge run is made from this report.
