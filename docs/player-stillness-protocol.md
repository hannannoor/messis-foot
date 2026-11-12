# Experiment E protocol — player stillness as dead-ball evidence (12 November 2026)

Frozen before any fit or score. Design approved by the user on 12 November 2026; source spec `C:\Users\leonj\Desktop\dlor\projects\docs\superpowers\specs\2026-11-12-decoder-structure-design.md` (sections 2, 4, 6, 7 reproduced here).

## 1. Question

Does adding two player-stillness features to the 18 release features, with the matched tree recipe, raise natural provider-weighted spell F1 by at least 0.010 without unacceptable losses? Target: missed stoppages (WCSF dead-ball recall about 0.50) and the possession merges they cause (DFL predicts too few spells).

## 2. Features (columns 19–20)

A player's speed on row t: distance from their position on row t − 5 (same period, same player id on the same team, both positions finite, id unique within its team on both rows) ÷ 0.2 s.
- **`still_share`:** per row, the share of players with a speed whose speed is < 1.0 m/s, over both teams; averaged over the trailing 50 rows (including the current row) on which at least 14 players have a speed; 0.0 if none.
- **`still_support`:** 1.0 if the current row has at least 14 players with a speed, else 0.0.

History and window clear at a period change, period 0 and invalid geometry. No ball, reference, status or tag field enters either feature. Constants (5 rows, 1.0 m/s, 50 rows, 14 players) fixed here.

## 3. Training and fits

Exactly Experiment B run `2026-11-12-d` (amendments 1–2): columns 1–18 from the pinned training caches as `memory_ablation_training.prepare_training` builds them; player tracks from `load_dfl_motion` for columns 19–20 only; training alignment gate (`team_shape_training.alignment_check`, 1e-4 m); 228,776 rows; `DecisionTreeClassifier(max_depth=4, min_samples_leaf=125, random_state=1729)` in the pinned training interpreter. Fit 1 control must reproduce training SHA `2730cd91…` and model SHA `363c45c7…`; fit 2 candidate on 20 columns. If neither new column is split on: stop, "representation unused".

## 4. Cohort, regimes, gates, parity, budget

Exactly Experiment A / B: 15 cases (13 primary), natural/noise (prefix `player-stillness-jitter-v1:1729:`)/live-gap/stoppage regimes, gates 1–6, staging, round-off 1e-12. Parity (run-scoped ledger identities): training alignment 4/4 both regimes, feature prefix 15/15 bit-exact, exporter ≤ 1e-12, release parity 15/15, reconciliation 0.551816. Budget: 2 fits, ≤ 100 predictions, ≤ 115 score bundles, ≤ 200 feature/tree passes, ≤ 300 decoder passes; parity separate.

## 5. Recorded limits

Missing-ball rows keep neutral emissions in the unchanged assembly, so stillness can act only on visible-ball rows (long missing stoppages are already handled by the gap rule). SkillCorner broadcast tracking often lacks 14 tracked players; `still_support` share per case is reported in preflight.

## 6. Order and cut-offs

Commit code and protocol → `freeze` → commit → `preflight` → `fit` → `parity` → `natural` → (`stress` only on a stage-1 pass) → `summarise` → report. Stage-1 decision by 23:59 local 14 November 2026; full verdict by 12:00 local 15 November 2026.

## 7. Interpretation and hard rules

A FAIL rejects these two features with this recipe on this reused cohort. A PASS qualifies only for a separate release decision. No provided-match material, no public ground truth, no provided-match constants, no hand labels; existing files byte-identical except append-only `.gitignore`; commits as The-leonjr; no push, merge, PR, submission or upload.
