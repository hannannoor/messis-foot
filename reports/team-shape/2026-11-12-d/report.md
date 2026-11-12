# Team Shape (Experiment B), run 2026-11-12-d — stage 1 FAIL, stress not run

Run under protocol amendments 1–2 (`docs/team-shape-protocol.md`). Earlier runs `2026-11-12-b` (training bit-parity stop) and `2026-11-12-c` (harness defect, no data read) stay committed as stopped.

1. **Start check.** Worktree `team-shape-work`, branch `experiment/team-shape`, base `01aea05`. Pinned training and scoring interpreters verified at freeze. Nothing installed.
2. **Commits for this run, in order.** `4316cf6` amendment 1 code; `53315de` whitelist c; `9ae42f2` freeze c (stopped); `9ea2da0` amendment 2 and harness fixes; `546e3ee` stopped-run record; **`ec79abd` freeze d**; `730cc4c` preflight; `2589898` fits; `12006c6` parity; `06f3294` stage 1. Existing-file diff against `01aea05` is empty; `.gitignore` has 200 additions, 0 deletions. No push, merge, PR, submission or upload.
3. **Tests.** 64 new tests pass under the pinned training interpreter (all) and the scoring interpreter (4 training-only skips). The full existing suite was run once by the earlier worker for run b (clean after creating the ignored `.tmp` folder); it was not rerun after amendments 1–2, which touch only new files.
4. **Freeze.** Run d freeze SHA-256 `f9a0b428f378d1a7d813ea31de0cc7e96aed7e06d0214436f66c29fbaa637937`, recorded head `546e3ee`. Seeds: training 1729, masks 1729 + group index, noise prefix `team-shape-jitter-v1:1729:`.
5. **Fits.** Rows 228,776. Control training semantic SHA `2730cd91…` and model SHA `363c45c7…` both reproduced exactly. Candidate model SHA `f34067a9…31ea`, 31 nodes, depth 4. Appended columns used: `shape_advance_diff ≤ 2.859` (node 13) and `shape_spread_diff ≤ −2.763` (node 18); `shape_closing_diff` and `shape_support` unused. Exporter parity max difference 6.0e-14.
6. **Parity.** Training alignment 4/4 matches, both regimes (largest difference 3.1e-6 m, tolerance 1e-4 m). Feature prefix 15/15 bit-identical. Release parity 15/15 against the real `restart_release.assemble`. Reconciliation 15/15; primary natural mean 0.5518160817 reproduced.
7. **Support.** Live-gap windows: SkillCorner 200, DFL 40, WCSF 20. Restart events: DFL 194, WCSF 71. Shape support: 100% of rows on DFL and WCSF, 11–34% on SkillCorner.
8. **Stage 1 (control → candidate).**

| Case | Spell F1 | Strict interior acc | Short spells matched | D recall |
|---|---|---|---|---|
| SkillCorner 1874553 | .6570 → .6564 | .9484 → .9467 | 10 → 11 of 26 | n/a |
| SkillCorner 1886347 | .6773 → .6578 | .9520 → .9511 | 3 → 3 of 11 | n/a |
| SkillCorner 2007448 | .5944 → .5965 | .9401 → .9413 | 5 → 5 of 15 | n/a |
| SkillCorner 2007721 | .5954 → .5958 | .9397 → .9390 | 4 → 4 of 15 | n/a |
| SkillCorner 2010085 | .5790 → .5783 | .9428 → .9433 | 6 → 6 of 17 | n/a |
| SkillCorner 2011166 | .5344 → .5258 | .9136 → .9116 | 9 → 9 of 24 | n/a |
| SkillCorner 2013725 | .5967 → .5851 | .9128 → .9128 | 9 → 9 of 19 | n/a |
| SkillCorner 2015213 | .5782 → .5932 | .9106 → .9129 | 6 → 6 of 21 | n/a |
| SkillCorner 2016236 | .5909 → .5914 | .9200 → .9197 | 4 → 4 of 19 | n/a |
| SkillCorner 2017461 | .5364 → .5168 | .9010 → .8986 | 5 → 5 of 18 | n/a |
| DFL J03WR9 | .5785 → .5859 | .9742 → .9756 | 8 → 7 of 44 | .9937 → .9936 |
| DFL J03WN1 | .5289 → .5150 | .9651 → .9661 | 3 → 3 of 77 | .9950 → .9950 |
| WCSF | .5052 → .4992 | .9683 → .9684 | 9 → 9 of 55 | .4962 → .4962 |
| *Secondary* DFL J03WOH | .5800 → .5773 | .9667 → .9688 | 5 → 5 of 49 | .9912 → .9912 |
| *Secondary* DFL J03WOY | .5436 → .5448 | .9650 → .9689 | 2 → 2 of 44 | .9912 → .9912 |

Provider means: SkillCorner .5940 → .5897; DFL .5537 → .5504; WCSF .5052 → .4992. Primary weighted .55095 → .54645 (−0.0045).

| Gate | Value | Threshold | Result |
|---|---|---|---|
| 1: spell-F1 gain | −0.0045 | ≥ +0.010 | **fail** |
| 1: each provider ≥ 0 | all three negative | ≥ −1e-6 | **fail** |
| 1: strict interior accuracy | +0.00030 | > 1e-6 | pass |
| 2: per-match natural loss | 13 assessed, 0 failures | ≥ −0.020 | pass |
| 3: D precision, D recall, false-D, owner presence | 0 failures | | pass |
| 4: short spells | DFL J03WR9 recall loss 1/44 = 0.0227 | ≤ 0.020 | **fail** |

9. **Stage 2.** Not run, by design.
10. **Verdict: FAIL** — spell-F1 gain, provider non-regression, short spells.
11. **Budget.** Fits 2/2; case runs 30/100; score bundles 45/115; feature/tree passes 61/200; decoder passes 60/300; parity checks 44 (separate). No science reruns.
12. **Timing.** Stage-1 decision on 12 November 2026, before the 14 November cut-off.
13. **Transfer coverage.** Not run: the study stopped at stage 1, and the coverage check could not change the verdict.
14. **Limits.** A FAIL rejects these four features with this tree recipe on this reused cohort, not team shape in general. Missing-ball rows get neutral emissions in the unchanged assembly, so the features could act on visible-ball rows only. SkillCorner gave the features a weak test (11–34% support). As in Experiments A and C, frame-level ownership accuracy rose slightly while spell F1 fell.
