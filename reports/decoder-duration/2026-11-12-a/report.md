# Experiment D — minimum spell length in the decoder, run 2026-11-12-a: stage 1 FAIL, stress not run

1. **Start.** Worktree `decoder-duration-work`, branch `experiment/decoder-duration`, base `9302828` (Experiment C). Scoring interpreter Python 3.14.5 / numpy 2.5.1 / pandas 3.0.5, equal to Experiment A's freeze.
2. **Commits.** `be4182b` decoder; `fdd02df` rule + assembly; `49de7b0` harness + protocol; **`a673ace` freeze**; `ac85ba0` preflight; `111f634` parity; `2f209e7` stage 1 + summary. Existing-file diff against `9302828`: empty. `.gitignore`: 116 additions, 0 deletions. No push, merge, PR, submission or upload.
3. **Tests.** 19 new tests pass (decoder 8, assembly 8, harness 5 — two fixtures corrected for arithmetic, recorded). Full suite: 1,042 tests, 34 skips, 1 failure — Experiment C's own guard test that no non-C file exists since `01aea05`, which D's new files necessarily trip; D enforces its own guard in `check_repository`.
4. **Freeze.** SHA-256 `a5cd281c…b8766`, recorded head `49de7b0`. Noise prefix `decoder-duration-jitter-v1:1729:`. A scratch-ledger dry run of preflight and parity passed before the freeze.
5. **L.** 23 frames (0.92 s): nearest-rank 10th percentile of pooled reference runs in the four DFL training matches, inside [5, 50].
6. **Parity.** Release parity 15/15 against the real `restart_release.assemble`; extra = 0 equivalence 15/15 (latent, control, gapped, restarted, final, stoppage gaps, gap summary); reconciliation 0.5518160817 reproduced.
7. **Support.** Live-gap windows SkillCorner 200, DFL 40, WCSF 20; restart events DFL 194, WCSF 71; mask seals equal Experiment A's.
8. **Stage 1 (control → candidate).**

| Case | Spell F1 | Strict interior acc | Short spells matched | D recall | Predicted spells (short < L) |
|---|---|---|---|---|---|
| SkillCorner, all 10 | unchanged | unchanged | unchanged | n/a | 358–496, short 1–7 → same or −1 |
| DFL J03WR9 | .5785 → .5792 | .9742 → .9742 | 8 → 7 of 44 | .9937 → .9937 | 385 (8) → 379 (0) |
| DFL J03WN1 | .5289 → .5282 | .9651 → .9651 | 3 → 2 of 77 | .9950 → .9950 | 443 (6) → 441 (1) |
| WCSF | .5052 → .5056 | .9683 → .9683 | 9 → 8 of 55 | .4962 → .4951 | 524 (13) → 518 (0) |
| *Secondary* DFL J03WOH | .5800 → .5827 | .9667 → .9670 | 5 → 5 of 49 | .9912 → .9910 | 411 (5) → 408 (0) |
| *Secondary* DFL J03WOY | .5436 → .5449 | .9650 → .9650 | 2 → 2 of 44 | .9912 → .9912 | 439 (4) → 437 (0) |

Provider means: SkillCorner .5940 → .5940; DFL .5537 → .5537 (+0.00005); WCSF .5052 → .5056. Primary .55095 → .55109 (+0.00013).

| Gate | Value | Threshold | Result |
|---|---|---|---|
| 1: spell-F1 gain | +0.00013 | ≥ +0.010 | **fail** |
| 1: each provider ≥ 0 | all ≥ 0 | ≥ −1e-6 | pass |
| 1: strict interior accuracy | −0.000007 | > 1e-6 | **fail** |
| 2: per-match natural loss | worst −0.0006 | ≥ −0.020 | pass |
| 3: D precision, D recall, false-D, owner presence | 0 failures | | pass |
| 4: short spells | 1 failing match | | **fail** |

9. **Stage 2.** Not run. 10. **Verdict: FAIL** (spell gain, interior accuracy, short spells).
11. **Budget.** Fits 0; case runs 30/100; score bundles 45/115; feature/tree passes 45/200; decoder passes 60/300; parity 31 (separate). No reruns.
12. **Timing.** Stage-1 decision on 12 November 2026, before the 14 November cut-off.
13. **Finding.** The release decoder already produces almost no spells shorter than L: 1–13 per match out of 358–524. The over-count of predicted spells on SkillCorner and WCSF is made of longer wrong spells, which a minimum-length rule cannot touch. Where it did act (DFL, WCSF), it removed nearly every sub-L spell and moved spell F1 by less than 0.001.
14. **Limits.** A FAIL rejects this mechanism with L = 23 and extra = 32 on this reused cohort. With the penalty, the decoder pads strong short spells up to L rather than deleting them (recorded in the protocol before any result).
