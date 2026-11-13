# Experiment G protocol — pair switch costs (frozen before any score)

Design: `docs/superpowers/specs/2026-11-12-missing-evidence-and-pair-costs-design.md` (outside this repository), approved 12 November 2026. Go-ahead to freeze and run given by the user on 13 November 2026 with the prior below recorded. Base: `experiment/decoder-duration` at `495bb01`; branch `experiment/pair-costs`.

## Question

Does replacing the single switch cost 32 with a 3×3 pair-cost table derived from training-match transition rates, keeping the mean off-diagonal cost at 32, raise natural provider-weighted spell F1 by ≥ 0.010 without unacceptable losses?

## The one change

- **Decoder.** `pair_decoder.decode_matrix(emissions, periods, usable, matrix)`: the `touch_decoder.decode_variable` recursion with the cost of moving from state i to state j ≠ i equal to `matrix[i][j]` (diagonal 0).
  - Validation, period/usability segmentation, per-row normalisation, argmax order (H, A, D; first maximum wins) and backtrace are unchanged.
  - With every off-diagonal entry 32 it equals `decode_variable` with uniform costs 32, label for label.
- **Cost rule (fixed, training data only).**
  1. From the reference labels of the four pinned DFL training matches (J03WOH, J03WOY, J03WPY, J03WMX; hash-verified caches; codes 0/1/2 = H/A/D; periods 1–2), count consecutive-row pairs within one period with both codes valid: `n_ij`.
  2. `p_ij = n_ij / Σ_k n_ik`.
  3. For i ≠ j, `q_ij = −log p_ij`; a pair with `n_ij = 0` gets the largest observed off-diagonal `q`.
  4. `C_ij = 32 · q_ij / mean_{i≠j}(q_ij)`, so the mean off-diagonal cost is exactly 32.
  The rule runs in `preflight`. The table, counts and `q` (aggregate counts only) are stored in `preflight.json` and the ledger.
- **Assembly.** Both decode passes (the first decode and the restart decode) use `decode_matrix` with C. Everything else is unchanged: the frozen tree's supports, neutral missing-ball rows, unsupported segments, abstention materialisation, gap rule, restart masking, and the kickoff patch (empty starts for both methods).
- No fit. No other table is run.

## Prior (computed from training-cache aggregates before any score)

| Pair | Count | Cost |
|---|---|---|
| H→A | 688 | 27.5 |
| H→D | 215 | 33.3 |
| A→H | 689 | 26.8 |
| A→D | 198 | 33.1 |
| D→H | 210 | 35.5 |
| D→A | 197 | 35.9 |

Row totals: H 167,241; A 147,819; D 256,860.

- A team round trip costs 54 instead of 64 (−15%).
- A D excursion costs 69 instead of 64 (+7%).
- G therefore mainly makes team switches cheaper and D slightly dearer, which works against the D-recall motivation. Its realistic hope is recovering missed direct H↔A changes (WCSF direct-boundary recall 84/237).
- No pair has zero count.
- Two training matches (J03WOH, J03WOY) are also scored as secondary cases; primary scoring excludes them.

## Checks before any science score

- Release parity 15/15: the research replica equals `restart_release.assemble`.
- Equivalence 15/15: with the uniform-32 matrix the G assembly equals the replica on every field (latent, control, gapped, restarted, final, stoppage gaps, gap summary).
- Mask seals equal Experiment A's.
- Reconciliation: provider-weighted primary natural mean 0.551816 (1e-6) and the historical summary (1e-9).

## Shared protocol (as Experiments A–E)

- 15 cases (13 primary; DFL J03WOH and J03WOY secondary); providers weighted 1/3 each.
- Regimes: natural; noise (seed prefix `pair-costs-jitter-v1:1729:`), live-gap, stoppage.
- Gates 1–6 as in `docs/recent-geometry-protocol.md`:
  1. spell-F1 gain ≥ +0.010, each provider ≥ 0, strict interior accuracy > 1e-6;
  2. robustness, per-match natural loss ≤ 0.020;
  3. D precision/recall/false-D/owner presence;
  4. short spells;
  5. noise visible-evidence;
  6. support/restart.
- Receipts also report per-method spell counts and spells shorter than 23 rows (Experiment D's frozen L, a fixed threshold).
- Stage 2 only after a stage-1 pass.
- Budget, claimed on entry, never refunded: fits 0, ≤ 100 predictions, ≤ 115 score bundles, ≤ 200 feature/tree passes, ≤ 300 decoder passes; parity separate with run-scoped identities (`release/`, `equivalence/` + run + case; `training-rule/` + run).
- One scratch dry run of preflight and parity before the real freeze; one real run.
- Cut-offs (local, UTC+8): stage-1 decision by 23:59 on 15 November 2026; full verdict by 12:00 on 16 November 2026.

## Interpretation

A FAIL rejects this mechanism with this fixed table on this reused cohort. A PASS qualifies only for a separate release decision by the user; no combined F+G run unless both pass. No provided-match material to hosted models; no public ground truth for selection; no hand labels; match data and CSVs never committed; public files carry aggregates only.
