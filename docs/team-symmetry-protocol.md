# Experiment C — team-symmetric emissions: frozen protocol

Status: frozen before any scoring. The controlling document is the worker brief of 12 November 2026
(`home-bias-symmetry-brief-2026-11-12.md`). This file records only the operational interpretations the brief left open;
where the brief is silent, Experiment A's committed protocol (`docs/recent-geometry-protocol.md`) and harness
(`recent_geometry_*.py`) at commit `01aea05` are followed exactly, and each such place is marked **[A §n]**. Nothing here is
tuned to any outcome. There are no fits and no parameters.

## 1. Question

Does replacing the frozen tree's supports with their team-symmetrised version — same tree, no refit, everything downstream
unchanged — improve natural provider-weighted spell F1 by at least 0.010, without unacceptable losses in D, short possessions
or stress conditions? 0.010 is a prospective practical threshold, not a significance claim.

Honest prior, stated before scoring: in the provided match the home team is FC Barcelona, which probably holds more of the
ball, so a home lean may currently help there by luck. The provided match is never loaded, predicted or scored, so this
experiment cannot measure that.

## 2. Starting point

Main checkout `competition-release-work`, branch `experiment/recent-geometry`, head `01aea05f545cc366d5112f153f678399a5268dac`
(the base of this work). Release branch `codex/restart-release-2026-11-11` at `a3b5b0a07ddc561db6aafcce26dcc56d31ef2bb2`. Work
branch `experiment/team-symmetry` in the worktree `symmetry-work` directly inside the `MESSI's FOOT` folder. Frozen model
SHA-256 `363c45c70838b398cd87aee7474d7e281fd392f059a31b85712e312058aaab4d` (`memory_ablation.MODEL_SHA`), verified against the
hash of `gap_solver.tactical_model.FROZEN_MODEL['model']` and `release_runtime.MODEL_SHA256` before every stage. Scoring
environment: Python 3.14.5, numpy 2.5.1, pandas 3.0.5, required to equal the scoring block of Experiment A's committed freeze
receipt exactly (versions, platform, executable and library hashes). Nothing is installed; no training environment is used.
No existing file changes except append-only `.gitignore` lines; Experiment A's modules are imported, never edited or
monkeypatched. Protected release modules are imported, never edited or monkeypatched.

## 3. Method (exact)

Swap map on an 18-column `gap_solver.tactical.feature_rows` row (zero-based):

| Index | Feature | Under team swap |
|---|---|---|
| 0 | ball_observed | unchanged |
| 1 ↔ 2 | home_observed ↔ away_observed | exchanged |
| 3 ↔ 4 | home_distance ↔ away_distance | exchanged |
| 5 | distance_margin (`a − h`) | negated |
| 6 | min_distance | unchanged |
| 7, 8 | ball_edge_x, ball_edge_y (absolute offsets) | unchanged |
| 9–12 | ball_speed, recent_speed, slow_ball_age, missing_ball_age | unchanged |
| 13 ↔ 14 | last_home_distance ↔ last_away_distance | exchanged |
| 15 ↔ 16 | last_control_home ↔ last_control_away | exchanged |
| 17 | last_control_age | unchanged |

`team_symmetry.check_schema()` compares the table to `FEATURE_NAMES` by name and stops on any difference (import fails).
Reading `gap_solver/tactical.py` and `gap_solver/core._candidate` before the freeze confirmed that every role in the table is
as stated and that the control candidate rule (`home < away` after an explicit tie exclusion of `|h − a| < 0.75`) is team-symmetric.

Symmetrised supports. For each row `x`, `p = (pH, pA, pD) = tree(x)` and `q = tree(swap(x))`, using the release's tree and the
same float32 split comparisons (`memory_ablation.predict_supports`):

    sH = (pH + qA) / 2,   sA = (pA + qH) / 2,   sD = (pD + qD) / 2.

The candidate uses `s` everywhere the control uses `p` (first decode and restart decode, both inside
`recent_geometry_assembly.assemble_research`). Log floor 1e-6, switch cost 32, missing-row neutrality, abstention filling, gap
rule, decoder restart, second gap rule and empty kickoff starts are unchanged **[A §7]**. The control is the frozen tree's own
supports. Candidate and control supports travel in separate `SupportSet` objects checked by method before every assembly.

## 4. Cases and regimes **[A §5]**

Exactly Experiment A's 15 cases (13 primary, 2 secondary), the same list and roles. `wcsf-used-match` is Experiment A's
already-used external cohort case; it is not the provided match, which is never loaded. Regimes: natural (15), visible-ball
noise (15), pure live gaps (15), stoppage and reacquisition (5), with Experiment A's definitions, using
`recent_geometry_regimes` unchanged. The only change is the noise seed prefix, **`team-symmetry-jitter-v1:1729:`**: because the
regimes module reads its prefix from a module constant, `team_symmetry_run.add_visible_ball_noise` carries a copy of the
function with a `prefix` argument (a test proves it equals Experiment A's function byte for byte when given Experiment A's
prefix). Masks are generated from the reference by the unchanged functions and sealed (hash recorded) in preflight, before any
prediction. Because the brief requires the same masks, preflight also compares each case's mask seal with Experiment A's
committed `preflight.json`; any difference stops the study (`stopped_mask_mismatch`). Only transformed geometry reaches inference.

## 5. Parity gates (before any candidate scoring) and the bias report

Implementation verification, ledger category `parity`, no scores, not counted against the science caps. All run on the 15
natural cases and all must pass:

1. **Swap-map validity.** `feature_rows(team-swapped frames)` equals `swap(feature_rows(frames))` bit for bit (byte
   comparison of float64 arrays) on every row. Team-swapped frames exchange `home_distance`/`away_distance` and, for
   `MotionFrame`, `home_xy`/`away_xy` and `home_ids`/`away_ids`. This also covers the six-frame control latch, period resets
   and ties. The stored float32 matrix is additionally required to equal the float32 cast of the freshly computed rows.
2. **Release parity.** Research assembly with the control supports (decoder verification on) equals the real, unmodified
   `restart_release.assemble(frames, (), use_restart=True)` field by field (`control`, `gapped`, `restarted`, `final`,
   `stoppage_gaps`, `gap_summary`, `kickoff_changed`).
3. **Historical reconciliation.** The first-decode control labels reproduce `reports/memory-ablation/2026-11-09-v3/<case>--natural.json`
   (primary scalar 1e-9, every per-IoU matched/missed/spurious count exactly) and the primary natural mean reproduces
   0.551816 to 1e-6 **[A §8]**. Reconciliation scoring spends the 15 reconciliation score bundles of the science budget, so it is
   run only after gates 1, 2 and 4 have passed on all 15 cases (a failing gate therefore wastes no score claim).
4. **Candidate symmetry.** For every natural case, the candidate's supports for `swap(x)` equal its supports for `x` with H and
   A exchanged, to 1e-12 (holds by construction; evaluated by running the candidate on the swapped matrix, i.e. an independent
   pass, so an implementation error would show).

Any parity failure stops the study.

**Descriptive bias report (no gate)**, natural regime, computed in the parity step from the same supports, pooled per provider
by adding counts and sums over every case of the provider (and also given per case): over usable rows, mean `pH − pA` of the
frozen tree; the same over rows where the ball is missing; share of usable rows reaching leaf 22; the candidate's mean
`sH − sA`; share of usable rows where the candidate's argmax class (over H, A, D; ties to the first) differs from the control's.
The tree is checked to have node 22 as the leaf described in the brief (recent_speed > 0.0104, no recent away control, control
age > 1.54, slow-ball age ≤ 0.02) before use.

Interpretive note recorded before seeing data. The brief expects the candidate's mean H−A to be "about 0". That holds only if
the set of rows is closed under the team swap; in a real match the candidate's mean reflects who is actually closer to the ball
and in control. The quantity the symmetrisation removes exactly is the swap-averaged label lean `(lean(x) + lean(swap x)) / 2`,
which equals control mean minus candidate mean and is 0 for the candidate row by row. The report therefore gives the candidate's
mean as requested **and** `label_lean_removed_mean` (control mean − candidate mean, all usable rows and ball-missing rows) as the
cleaner bias measure. This addition changes no gate.

## 6. Gates and staging **[A §6, §7, §9]**

Exactly Experiment A's gates 1–6 and staging, using `recent_geometry_metrics` unchanged (constants and gate functions are the
same module objects; a test pins every constant): gain ≥ 0.010 with every provider ≥ 0 and strict observed-interior team
accuracy improving by more than 1e-6; stress loss ≤ 0.005 and every primary match/regime loss ≤ 0.020; D precision/recall loss
≤ 0.010 (DFL/WCSF), known-live false-D rise ≤ 0.005, both owners still predicted; short spells (IoU 0.5, ≤ 25 frames) per
Experiment A; noise mechanism; ≥ 5 live-gap windows per primary provider, ≥ 20 eligible restart events for masked DFL and WCSF, and
correct restarts not falling within any supported provider × same/changed subgroup. Round-off tolerance 1e-12 on every
threshold comparison (not a slack on any hurdle); the 1e-6 loss slack as in Experiment A. Weights: natural, noise and live-gap
1/3 per provider, matches equal within a provider; stoppage ½ DFL, ½ WCSF. Interior frame, restart definitions and duration
bins as in Experiment A §7. All gates are conjunctive.

Stage 1 = natural only (30 final bundles after the 15 reconciliation bundles): gates 1, 3, 4, owner presence and the 0.020
per-match natural bound. On failure, stop with no stress inference or scoring. Stage 2 (noise, live gaps, stoppage) only after
a stage-1 pass. Verdict "PASS — qualifies for a separate release decision" only if every assessed check passes; otherwise
"FAIL" naming every failing check. A pass authorises nothing else.

## 7. Budget (claim-on-entry, cumulative, ledgered; no refund after a claim)

0 fits (a fit claim is refused: cap 0). Science caps: ≤ 100 case predictions; ≤ 115 score bundles (100 + 15 reconciliation);
≤ 200 feature/tree passes; ≤ 300 decoder passes. Per case-regime the pipeline claims 2 predictions (control, candidate), 2
scores, 4 decoder passes (2 per method: first decode and restart decode) and 4 feature/tree passes (1 preparation, 1 control tree
pass, 2 candidate tree passes). Natural preparation (15) is claimed in preflight and reused by stage 1. Totals if every stage
runs: predictions 100, scores 115, feature/tree passes 15 + 15·3 + 35·4 = 200, decoder passes 200. The tree-pass cap is therefore
used exactly; there is no slack for a rerun of the stress stage, so a defect found there would stop the study, not grant a rerun.
The `parity` ledger category holds `swap/<case>`, `symmetry/<case>` and `release/<case>` identities, each bounded to Experiment A's
15 case ids and unique; a retry suffix (`/retry1`, `/retry2`) exists only for a documented code defect with a fix and a test
(the brief's rerun rule). A bug grants no free run. Zero provided-match or public-window predictions, scorings, acquisitions,
sweeps, extra variants, partial symmetrisations, publications or submissions.

## 8. Operational interpretations (fixed here, before any scoring)

* **Margin negation** is computed as `0.0 − x`, not `−x`, so a tied margin (+0.0) stays +0.0 under the swap. With plain
  negation a tie would turn into −0.0, which is numerically equal but not bit-identical, and would make the bit-for-bit validity
  gate fail for a reason unrelated to the swap map. Tree comparisons treat ±0.0 identically either way.
* **Distance-recompute parity** for the noise regime is Experiment A's committed `distance-parity.json` (status `exact`, all
  15 cases); the evaluation input hashes must equal Experiment A's freeze receipt exactly, which makes the earlier proof
  applicable. It is referenced by hash in the freeze, not re-run.
* **Inputs.** Evaluation inputs are re-hashed against `memory_ablation_protocol.input_bindings` and against Experiment A's
  freeze before each stage. Training files are not used.
* **Kickoff:** empty starts for both methods, no label inferred from the reference **[A §7]**.
* **Research assembly:** `recent_geometry_assembly.assemble_research` unchanged; `verify_decoder` is on only for parity.
* **Freeze commit order.** Code, tests and this document are committed; `freeze` then writes `freeze.json` (head commit, protocol
  digest, source, input and environment hashes, seeds) and that receipt is committed as the freeze commit; no scoring happens
  before it. After the freeze every source file is hash-checked before each stage.

## 9. Stop conditions and calendar

Stop on: source, input, scorer, model or environment mismatch; mask-seal difference from Experiment A; non-finite features;
a team role in the swap table differing from the feature generator; swap-map validity, release, reconciliation or candidate
symmetry failure; leakage; support mixing; budget exhaustion; any scientific gate failure; insufficient predeclared support (no
other mask is tried). Stage-1 decision by 23:59 local, 14 November 2026; full verdict by 12:00 local, 15 November 2026. If
either is missed, stop and report what is complete; the current release is submitted unchanged. A stop is a correct outcome. No
push, merge, pull request, submission generation or upload; local commits on `experiment/team-symmetry` only, authored and
committed as `The-leonjr <277591257+The-leonjr@users.noreply.github.com>`. No weighted or partial symmetrisation or any other
variant is tried on a stop.

## 10. Interpretation

A FAIL rejects symmetrising this frozen tree's emissions on this reused cohort; it does not show that the tree is unbiased.
A PASS qualifies only a separate release decision and authorises nothing else. In the provided match the home team is FC
Barcelona and probably holds more of the ball, so removing a home lean could cost points there even if it helps on the cohort;
this cannot be measured without the private ground truth. Experiment B (team shape) runs in parallel on the same cohort; if
both pass, they are not combined without a new test, and that choice belongs to the user.
