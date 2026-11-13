# Experiment F protocol — dead-ball evidence on missing-ball rows (frozen before any score)

Design: `docs/superpowers/specs/2026-11-12-missing-evidence-and-pair-costs-design.md` (outside this repository), approved 12 November 2026. Go-ahead to freeze and run given by the user on 13 November 2026 with the gate-1 expectation below recorded. Base: `experiment/player-stillness` at `83b203e`; branch `experiment/missing-evidence`.

## Question

Does letting Experiment E's stillness tree's dead-ball evidence act on missing-ball rows, at a fixed half weight, raise natural provider-weighted spell F1 by ≥ 0.010 without unacceptable losses?

## The one change

- Visible-ball rows: the release emission of E's committed `control.json` (artifact SHA-256 `061780ef57a57e663ef1770ba5e38d97b320550b1ff622c8222ed8c0060e7a47`, model SHA-256 `363c45c70838b398cd87aee7474d7e281fd392f059a31b85712e312058aaab4d` = release model), unchanged.
- Missing-ball rows (`ball_observed == False`), which the release scores `(0, 0, 0)`, instead receive, from E's committed `candidate.json` (artifact SHA-256 `36f78e793e3ad295551743653f43362f51c5cc9dc2d6e7eac130dedff8357ef4`, model SHA-256 `4c5467062e327d11b38f7c34117a9bb33ef853c2faba0ba3efcd9acc2fd69f0e`) on E's 20 columns (`player_stillness_features.stillness_matrix`), with support `(p_H, p_A, p_D)`:

  `row = (0, 0, λ · max(0, log max(p_D, 1e-6) − log max((p_H + p_A) / 2, 1e-6)))`, **λ = 0.5**.

- The clamp makes the change one-sided: missing rows can gain D evidence, never team evidence.
- Everything else unchanged: usability, the unsupported-segment rule, switch cost 32, abstention materialisation, gap rule, decoder restart (both decode passes use the new rows), kickoff patch (empty starts for both methods).
- No fit. A model artifact or semantic hash mismatch stops the run. λ is not tuned; no other value is run.

## Checks before any science score

- Release parity 15/15: the research replica equals `restart_release.assemble`.
- Equivalence 15/15: with λ = 0 the F assembly equals the replica on every field (latent, control, gapped, restarted, final, stoppage gaps, gap summary, kickoff changes).
- Still-tree parity 15/15: E-tree supports on the preflight matrix equal E's stored natural candidate supports.
- Reconciliation: provider-weighted primary natural mean 0.551816 (1e-6) and the historical summary (1e-9).

## Shared protocol (as Experiments A–E)

- 15 cases (13 primary; DFL J03WOH and J03WOY secondary); providers weighted 1/3 each.
- Regimes: natural; noise (seed prefix `missing-evidence-jitter-v1:1729:`), live-gap, stoppage.
- Gates 1–6 as in `docs/recent-geometry-protocol.md`:
  1. spell-F1 gain ≥ +0.010, each provider ≥ 0, strict interior accuracy > 1e-6;
  2. robustness, per-match natural loss ≤ 0.020;
  3. D precision/recall/false-D/owner presence;
  4. short spells;
  5. noise visible-evidence;
  6. support/restart.
- Stage 2 only after a stage-1 pass.
- Budget, claimed on entry, never refunded: fits 0, ≤ 100 predictions, ≤ 115 score bundles, ≤ 200 feature/tree passes, ≤ 300 decoder passes; parity separate with run-scoped identities (`release/`, `equivalence/`, `still-supports/`, `prefix/` + run + case).
- One scratch dry run of preflight and parity before the real freeze; one real run.
- Cut-offs (local, UTC+8): stage-1 decision by 23:59 on 15 November 2026; full verdict by 12:00 on 16 November 2026.

## Recorded limits (before any result)

- Final labels depend only on the restart pass; long stoppage gaps (> 75 rows with slow players) are already D by the gap rule and masked out of that pass.
- In the E tree, `missing_ball_age > 0.46 s` and `recent_speed ≤ 0.01` are first met at about row 12 of a gap; earlier rows reach leaves with D 0.0007–0.016 (clamped to 0 by the rule). So F can add D only in gaps longer than about 62 rows that the gap rule leaves live.
- Fully unseen usable segments stay unusable, so F cannot act there.
- Gate 1 is likely out of reach: strict interior accuracy counts only visible-ball rows with reference H/A, which F changes only through decoder side effects; DFL D recall is already ≈ 0.99 and SkillCorner has no D recall check, so WCSF alone would need about +0.03.

## Interpretation

A FAIL rejects this mechanism with λ = 0.5 on this reused cohort. A PASS qualifies only for a separate release decision by the user; no combined F+G run unless both pass. No provided-match material to hosted models; no public ground truth for selection; no hand labels; match data and CSVs never committed; public files carry aggregates only.
