# Experiment E — player stillness as dead-ball evidence, run 2026-11-12-a: stage 1 FAIL, stress not run

1. **Start.** Worktree `player-stillness-work`, branch `experiment/player-stillness`, base `d54eaf3` (Experiment B). Pinned training interpreter (Python 3.12.13, scikit-learn 1.5.1, single-thread BLAS) and scoring interpreter (Python 3.14.5) verified at freeze.
2. **Commits.** `34d5223` features; `936b270` training, harness, protocol; **`0b417c4` freeze**; `a2946ac` preflight; `51fcd92` fits; `836626f` parity; `ea22c46` stage 1 + summary. Existing-file diff against `d54eaf3`: empty. `.gitignore`: 130 additions, 0 deletions. No push, merge, PR, submission or upload.
3. **Tests.** 16 new tests pass under the training interpreter (all) and the scoring interpreter (1 scikit-learn-only skip). The full existing suite was not rerun on this branch; E adds only new files, and the guard in `check_repository` held at freeze.
4. **Freeze.** SHA-256 `31d7b2a6…165c1`, recorded head `936b270`. Noise prefix `player-stillness-jitter-v1:1729:`. A scratch-ledger preflight dry run passed before the freeze.
5. **Fits.** Rows 228,776. Control training SHA `2730cd91…` and model SHA reproduced exactly. Candidate SHA `4c546706…9f0e`, 31 nodes, depth 4, exporter parity 6.2e-14. One new split: `still_share ≤ 0.34` at node 9; `still_support` unused.
6. **Parity.** Training alignment 4/4 both regimes; feature prefix 15/15 bit-exact; release parity 15/15; reconciliation 0.5518160817.
7. **Support.** `still_support` share: DFL and WCSF 1.00; SkillCorner 0.20–0.48. Live-gap windows and restart events as Experiments A–D.
8. **Stage 1.** Candidate final labels are **identical to the control on all 2,338,457 natural rows** of the 15 cases, although its supports differ on 2,069,389 rows. Every spell-F1, accuracy and D metric is unchanged; primary .55095 → .55095.

| Gate | Value | Result |
|---|---|---|
| 1: spell-F1 gain | 0.0 (≥ +0.010) | **fail** |
| 1: strict interior accuracy | 0.0 (> 1e-6) | **fail** |
| 1: providers ≥ 0; 2; 3; 4 | all 0.0 | pass |

9. **Why nothing changed.** The only stillness split sits under `recent_speed ≤ 0.01 AND missing_ball_age > 0.46 s`, i.e. on missing-ball rows. The unchanged assembly gives those rows neutral evidence, so the split's effect is discarded — the limit recorded in the protocol (section 5) before any result. Its leaves are sensible (very still play with the ball gone → D 0.86), so stillness does carry dead-ball information; the release pipeline cannot use it where the tree put it.
10. **Stage 2.** Not run. **Verdict: FAIL** (spell gain, interior accuracy).
11. **Budget.** Fits 2/2; case runs 30/100; score bundles 45/115; feature/tree passes 61/200; decoder passes 60/300; parity 39 (separate). No reruns.
12. **Timing.** Stage-1 decision on 12 November 2026, before the 14 November cut-off.
13. **Limits.** A FAIL rejects these two features with this recipe and this assembly on this reused cohort. Using stillness on missing-ball rows would need a change to the neutral-evidence rule, a different experiment.
