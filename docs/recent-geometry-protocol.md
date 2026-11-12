# Experiment A — support-aware recent geometry: frozen protocol

Status: frozen before any fit. The controlling document is the worker brief of 11 November 2026
(`recent-geometry-brief-2026-11-11.md`) plus the two clarifications of 12 November 2026 recorded in §10 and §11.
This file adds only the operational interpretations that the brief left open; where it is silent the existing
control-memory ablation machinery (`memory_ablation*.py`) is followed. Nothing here is tuned to any outcome.

## 1. Question

Does adding two features to the frozen geometry tree — a 12-row mean of the signed team-distance margin and the
fraction of that window that was observed — improve natural provider-weighted spell F1 by at least 0.010 and improve
strict observed-interior ownership accuracy, without unacceptable losses elsewhere? 0.010 is a practical hurdle for
accepting extra complexity, not a significance claim or a predicted gain. A FAIL rejects this two-feature
representation with this matched tree recipe on the declared reused cohort only.

## 2. Starting point

Repository `competition-release-work`, base `a3b5b0a07ddc561db6aafcce26dcc56d31ef2bb2`, work on branch
`experiment/recent-geometry`. Frozen model SHA-256 `363c45c70838b398cd87aee7474d7e281fd392f059a31b85712e312058aaab4d`;
control training semantic SHA-256 `2730cd91f67ceef88548a0fe65bf3bd899a5bc0526b6a92f937d08b2e37c55fd`.
Pinned environments: training Python 3.12.13 (numpy 1.26.4, pandas 2.2.2, scikit-learn 1.5.1, scipy 1.13.1, joblib 1.6.0,
threadpoolctl 3.8.0, one thread); scoring Python 3.14.5 (numpy 2.5.1, pandas 3.0.5). Both verified against
`reports/memory-ablation/2026-11-09-v3/freeze.json` (versions and executable hashes). Nothing is installed.
No existing file changes except append-only `.gitignore` lines.

## 3. Features (`recent_geometry_features.py`)

Columns 1–18 are `gap_solver.tactical.feature_rows`, unmodified and bit-identical. Appended:

* `recent_distance_margin` — mean of existing column 5 (`a − h`, both clipped at 30 m) over *qualifying* rows of the
  trailing window of 12 canonical rows including the current one; empty set gives 0.0. The mean is `math.fsum` so it does
  not depend on the interpreter's `sum`.
* `recent_distance_support` — qualifying rows ÷ 12, including at a period start.

A row qualifies when period ∈ {1, 2}, geometry is valid, the ball is observed and both distances are finite and ≥ 0. Rows
that fail to qualify for any other reason occupy a window slot as unsupported (they are not zero-margin observations).
Only this window is cleared: on a period change, at period 0 and on explicit invalid geometry; an invalid-geometry row
contributes nothing. Plain `Frame` records without `geometry_valid` are valid; a `MotionFrame` or any record declaring the
field must supply a real `bool`, else preparation stops. No label, status or tag field is read.

## 4. Fitting (exactly two fits)

Same recipe as `memory_ablation_training.prepare_training` (matches J03WOH, J03WOY, J03WPY, J03WMX in order; natural plus
30 % masks via `ball_mask(periods, .3, 1729 + group_index)`; full history before selecting `index % 5 == 0` known H/A/D
rows; unit-total weight per match/regime). Expected selected rows 228,776, else stop. Tree: depth 4, min leaf 125,
`random_state` 1729, export format and class order as `fit_pair`; no search, no validation-match use, no augmentation.
The control matrix is the historical `prepare_training` output itself. Fit 1 (18 columns) must reproduce the training
semantic SHA-256 and the frozen model SHA-256, otherwise stop before the candidate fit; the training identity is also
checked before any fit is claimed. Fit 2 (20 columns) uses the same rows, labels, weights and identities, and the first
18 columns' semantic digest must equal the control matrix's. If neither appended column is used in any split: stop,
"representation unused, no advancement". The 20-column exporter/evaluator uses float32 comparisons; its supports must equal
scikit-learn's `predict_proba` within 1e-12 on all fitting rows (implementation verification, not scoring).
The candidate may restructure the whole tree, including D emissions; no ownership-only or D-preserved claim is made.

## 5. Cases and regimes

Primary (13, fitting-disjoint, already-used): DFL J03WR9, J03WN1; WCSF used match (halves pooled); SkillCorner
1874553, 1886347, 2007448, 2007721, 2010085, 2011166, 2013725, 2015213, 2016236, 2017461. Secondary (visible separately,
never in a primary mean, gate or denominator): DFL J03WOH, J03WOY. J03WQQ and Metrica are not used. Inputs are loaded as in
`memory_ablation_run.load_evaluation` and hash-verified against `memory_ablation_protocol.input_bindings`.

| Regime | Cases | Definition |
|---|---:|---|
| Natural | 15 | pinned external tracking, unchanged |
| Visible-ball noise | 15 | σ = 0.25 m Gaussian on each visible ball coordinate; CPython 3.14.5 `random.Random(seed).gauss(0, .25)`, fresh generator per case, `seed = int(sha256("recent-geometry-jitter-v1:1729:" + case_id)[:8], 16)`, rows ascending, x then y, no draws on missing rows, no clipping; distances recomputed from player positions |
| Pure live gaps | 15 | per period, complete 250-frame windows tiled from the period's first frame; eligible if every frame is reference H/A, ≥ 200 of 250 frames naturally visible, and the frames immediately before and after are naturally visible in the same period; ordered by SHA-256 of `case_id:live250-v1:period:window_index`; windows are taken in that order while `250 · k · 10 < known live frames of the period` and `k < 10`; ball observation, provenance and distances cleared, players kept |
| Stoppage and reacquisition | 5 | DFL WR9, WN1, WOH, WOY + WCSF; every maximal reference-D run plus its first 25 post-D frames, stopping at a reference-X frame or period edge; overlaps merge; no live blocks, no jitter |

`stoppage_regime.py` constants are not used; nothing derives from the provided match, which is never loaded, predicted or
scored, nor from the public five-minute ground truth. Masks are generated from the reference and sealed (hash recorded) in
preflight, before any prediction; only transformed geometry reaches inference.

## 6. Scoring and gates

Pinned official metric (`gap_solver.official_metrics`). Weights: natural, noise and live-gap 1/3 per provider (SkillCorner,
DFL, WCSF), matches equal within a provider; stoppage 1/2 DFL (WR9, WN1) and 1/2 WCSF. WCSF half-level TP/FP/FN are pooled
before F1 by the scorer's run-level aggregation (confirmed by the historical reconciliation). Loss checks allow 1e-6 slack;
counts are exact; no bootstrap and no confidence claims. All gates are conjunctive.

1. **Natural benefit:** primary spell-F1 gain ≥ 0.010 and every provider's mean change ≥ 0; strict team accuracy on
   observed reference-H/A interior frames improves, provider-weighted, by more than 1e-6 (per-provider effects reported).
2. **Robustness:** primary loss ≤ 0.005 in each stress regime; every primary match/regime loses ≤ 0.020 (natural included).
3. **D and owner integrity:** DFL/WCSF D precision and recall each lose ≤ 0.010; known-live false-D rate rises ≤ 0.005
   (SkillCorner included); both owners still predicted wherever each has reference support; undefined required D support is
   unresolved and not a pass — all per primary match/regime.
4. **Short spells** (IoU 0.5, reference possessions ≤ 25 frames): ≥ 20 spells → recall loss ≤ 0.020; 1–19 → no loss in matched
   count; 0 → non-applicable, stated.
5. **Visible-evidence mechanism:** under noise, observed-interior strict team accuracy does not regress; corrections and newly
   introduced errors reported by class (wrong team, false D, carried/unsupported = rows whose first-decode label was latent X).
6. **Support and restart:** ≥ 5 selected live-gap windows per primary provider; ≥ 20 eligible restart events for masked
   DFL (WR9 + WN1) and WCSF; an eligible event is a maximal reference-D run with known H/A immediately before and after, in the
   same period. A restart is correct when the post-D reference team holds strictly more than half of all predictions in the
   first 25 reference-live frames after D, ending sooner at the next reference change (D and X count in the denominator; ties
   fail). The correct count must not fall within any provider × same/changed subgroup that has support. Missing required
   support blocks advancement. First-frame correctness and first-H/A recovery within 50 frames are reported.

Staging: stage 1 = natural only (30 final bundles + 15 reconciliation bundles): gates 1, 3, 4, owner presence and the
0.020 natural per-match bound; on failure stop, with no stress inference or scoring. Stage 2 only after a stage-1 pass.
Verdict "PASS — qualifies for a separate release decision" only if every check passes; otherwise "FAIL" naming every
failing check. A pass authorises nothing else.

## 7. Operational interpretations (fixed here, before any fit)

* **Interior frame:** reference H/A, ball observed in the transformed input, and more than 50 frames from the first and last
  frame of its constant (period, reference-code) run; period edges and every state or annotation change are boundaries.
* **Provider-level support counts** (live-gap windows, restart events) are pooled over the provider's primary cases.
* **Gates 3, 4 and owner presence** are evaluated per primary match in every regime that is run; spell-F1 checks use the
  regime's provider weights.
* **Comparison tolerance:** all threshold comparisons use a **1e-12 floating round-off tolerance** (`ROUNDOFF = 1e-12`) so an
  exact-boundary value is not decided by representation noise. It is *not* a slack on any hurdle: the brief's 1e-6 slack on
  loss checks is applied separately and unchanged; the 0.010 gain and the 1e-6 interior-accuracy improvement are tested as
  `gain ≥ 0.010 − 1e-12` and `gain > 1e-6 + 1e-12`.
* **Kickoff:** external kickoff tags do not exist; both methods use empty kickoff starts, and no label is inferred from
  reference kickoff times.
* **Duration bins** (reporting only): 1–25, 26–75, 76–250, 251+ frames.
* **Research assembly:** `recent_geometry_assembly.py` reproduces `restart_release.assemble` from one explicit per-method
  `SupportSet` (log floor 1e-6, switch cost 32, neutral missing-ball rows, usability, materialisation, gap rule, decoder
  restart, gap rule, empty kickoff). It carries its own `decode_stoppages` replica whose control-reproduction decode is
  optional and is switched on for parity runs only; candidate and frozen supports cannot mix.

## 8. Parity and reconciliation (before any candidate scoring)

1. Feature prefix: the adapter's first 18 columns equal `feature_rows` bit for bit on every row of all 15 natural cases.
2. Release parity: against the real, unmodified `restart_release.assemble(frames, (), use_restart=True).final` on all 15
   natural cases, never against the replica's own integrity check. The replica is used for scoring only after it matches the
   real function exactly on all 15.
3. Historical reconciliation: the frozen-control intermediate labels (before the gap rule) match
   `reports/memory-ablation/2026-11-09-v3/<case>--natural.json` — primary scalar to 1e-9, every per-IoU matched/missed/spurious
   count exactly, primary natural mean 0.551816 (to 1e-6).

Any parity failure stops the study.

## 9. Budget (claim-on-entry, cumulative, ledgered; no refund after a claim)

Science budget: 2 fits; ≤ 100 end-to-end case predictions; ≤ 115 score bundles (100 + 15 reconciliation); ≤ 200 feature and
tree-support passes; ≤ 300 decoder passes. Planned use: 100 predictions, 115 bundles, 150 passes, 200 decoder passes.
A separate **`parity` ledger category** records implementation verification — exporter parity, the 15 feature-prefix
comparison passes and the 15 real `restart_release.assemble` release-parity runs. Parity identities are bounded and unique,
produce no scores, and do not count against the science caps. Zero provided-match or public-window predictions, scorings,
acquisitions, sweeps, extra variants, publications or submissions. A bug grants no free run; recovery that exceeds the budget
or changes the science needs a written amendment approved by the user before more computation.

## 10. Distance-recompute parity (clarification of 12 November, evidence recorded before the freeze)

The noise regime recomputes distances from player positions. Before the freeze, recomputing distances on un-noised frames
was compared with the loaders' stored distances exactly (no tolerance), for all 15 cases:

| Provider | Rows checked | Exact | Mismatches | Max abs difference |
|---|---:|---:|---:|---:|
| SkillCorner (10 matches) | 879,315 | 879,315 | 0 | 0.0 |
| DFL (4 matches) | 568,121 | 568,121 | 0 | 0.0 |
| WCSF | 143,431 | 143,431 | 0 | 0.0 |

No unobserved-ball row carries a stored distance and no row disagrees about a missing distance (receipt
`distance-parity.json`). Had it not been exact, the study would have stopped here.

## 11. Stop conditions and calendar

Stop on: source, input, scorer, model or environment mismatch; non-finite features; changed row/label/weight identities;
feature-prefix mismatch; failed exporter, release or reconciliation parity; leakage; support mixing; budget exhaustion; any
scientific gate failure; unused appended columns; insufficient predeclared support (no other mask is tried). If the natural
decision is not reached by 23:59 local time on 13 November 2026, stop and report what is complete; the current release is
submitted unchanged. A stop is a correct outcome. No push, merge, pull request, submission or upload; local commits only.

## 12. Interpretation

A FAIL rejects this representation with this recipe on the reused cohort; it does not show that ownership history or all
temporal methods are useless, and tree restructuring, smoothing delay and availability mismatch remain distinct
explanations. A PASS qualifies only a separate release decision on reused external evidence; it authorises no challenge run,
public-window check, replacement CSV or publication. Transfer risk, stated plainly: the training data has near-complete ball
visibility, whereas the provided match is missing the ball on 42 % of graded frames, so the support feature will take values
the tree rarely saw. Full-match F1 and behaviour under that real missingness remain unknown.
