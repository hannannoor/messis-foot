# Team Shape protocol and execution record

Status: frozen prospective protocol. The companion freeze receipt and this document
must be committed together before preflight or fitting. Progress after freezing is recorded
in aggregate receipts, not by editing this document.
The 12 November worker brief below supplies the experiment specification.

## Section 5 clarification authorised by the user, 12 November 2026

Derive the midpoint for every provider in the same way: the canonical x that its own
loader maps its native pitch centre to. WCSF uses `wcsf_geometry._canonical(0, 0)[0]`.
DFL and SkillCorner both use `(native_x / native_length + .5) * canonical_length`;
at the native centre, native_x/native_length is exactly 0, so this is
`(0.0 + .5) * notes['canonical_pitch_m'][0]`, evaluated before float32 track storage.
Assert that all three equal exactly **52.65**, with no tolerance, and stop if any differs.
This midpoint is used only for the both-teams-on-the-same-side stop check, never to
choose direction or change a feature constant. A synthetic test asserts exactly
`wcsf_geometry._canonical(0, 0) == (52.65, 34.0)`.

## Implementation plan and current progress

- [x] Verify clean starting checkout, both specified branch heads and pinned environments.
- [x] Create sibling worktree on experiment/team-shape from 01aea05.
- [x] Write failing synthetic feature tests; implement the four appended columns.
- [x] Write synthetic matched training/parity/exporter tests; adapt the existing training machinery.
- [x] Write failing budget/pipeline tests; adapt the orchestration with supplied 22-column supports.
- [x] Complete the CLI, including post-verdict geometry-only coverage, stop receipts and Singapore-time calendar enforcement.
- [x] Run the full existing suite and record its outcome and targeted environment/setup diagnostics.
- [x] Resolve the loader midpoint requirement and finalise the protocol.
- [ ] Write the freeze receipt and commit it with this protocol before any fit.
- [ ] Preflight all pinned inputs, masks, support and natural/masked training-frame parity.
- [ ] Exactly two matched fits, with the frozen control identities checked before candidate fitting.
- [ ] Exporter/release parity and historical reconciliation; stage 1; stress only on a pass.
- [ ] Commit verdict before the one aggregate-only transfer coverage check, then commit coverage.

The Experiment A regime, assembly and metric modules are reused unchanged. The new
adapter uses the existing geometry-validity helper without changing it. The 22-column
candidate is evaluated locally and passed into the unchanged assembly as an explicit
SupportSet, because its from_matrix convenience method assumes Experiment A's 20 columns.
Training masks use mask_motion_frames; the cache control continues to use prepare_training.
The pinned training installation is reused from competition-release-work; no environment
is copied or installed in this worktree. Synthetic sklearn tests do not consume scientific fits.

## Scoring and parity accounting

Feature-prefix, training-frame, exporter and release parity produce no score bundles and
use the separate parity ledger. Historical reconciliation, as in Experiment A section 6,
uses fifteen explicitly claimed science score bundles to reproduce the historical
intermediate control mean 0.551816. Those are reconciliation scores, not parity scores.
No candidate is scored in reconciliation. All downstream policy, scorer constants and
gates remain unmodified. If a preflight or parity stop occurs, no stress inference,
scientific verdict or target coverage is improvised. The stop is reported as operational
failure with the scientific hypothesis untested.

## Prospective feature interpretations

- Per-period team mean x averages the centroids of shape-valid rows with equal row weights.
- Closing counts individually matched players. Unlike features 19 and 20, its exact definition
  does not impose a seven-player threshold at both endpoints. Geometry and period continuity,
  finite coordinates, observed current ball and identity requirements still apply.
- A single team mean exactly on the pitch midpoint is permitted if the teams' means differ.
  Same-side means or exactly tied means stop direction assignment. A tie cannot identify a lower team.
- Training preparation claims sixteen feature passes before entry (control and candidate, four
  matches, natural and mask30). Prefix/training/release verification remains separate parity.
- The live-gap mechanism reports strict team correctness on the sealed hidden-live mask within
  the existing score bundle, then pools row counts per primary provider. It never substitutes
  the broader naturally-missing-ball stratum, and adds no extra case prediction or score bundle.
- The unchanged downstream assembly neutralises emissions on unobserved-ball rows. Shape
  features 19, 20 and 22 remain available in the adapter in live gaps, but the experiment must
  not claim that their emissions influence the release decoder while the ball is missing.

## Review record

One fresh reviewer (same model family, not an independent model provider) checked the feature,
training and orchestration code before freezing. Two medium findings were reproduced in synthetic
checks and fixed: the missing hidden-live mechanism counts, and the eight-versus-sixteen training
pass accounting. Closing support and the midpoint equality edge were aligned with the literal
feature definitions and tested. The CLI now includes geometry-only transfer coverage with a committed-verdict guard,
explicit Singapore-time cutoffs and stop receipts. Full-suite verification must complete
without edits to any Python source: WCSF's existing tests freeze a recursive Python source
inventory, so edits during that suite invalidate the checks. The initial run overlapped new source edits and returned 33 errors plus a restricted-
environment junction failure; its complete temporary log was not retained. A stable-source
rerun executed 1,002 tests with no assertion failures and 29 setup errors, all caused by
this new worktree lacking the existing tests' required .tmp directory. After creating that
ignored directory, all 29 affected tests passed. All 56 WCSF tests passed with stable sources,
and the junction checks passed when temporary junction creation was permitted. The first
attempt to select the 29 tests duplicated the method name and loaded no real tests; the
corrected selection ran and passed all 29. These software retries consume no science budget.
The two final review findings (stop enforcement and the final-verdict deadline) were then
fixed and checked by the complete new synthetic suite. No scientific run was retried.

## Supplied experimental specification

# Worker brief â€” Experiment B: team-shape possession evidence (12 November 2026)

Read all of this before doing anything. This brief is the controlling protocol. Where it is silent, follow Experiment A's committed protocol and harness exactly (`docs/recent-geometry-protocol.md` and `recent_geometry_*.py` at commit `01aea05`), and say in your report where you did so. Two other workers are running other experiments at the same time in other worktrees; never touch their worktrees, branches or private folders.

---

## 1. Project and why

We are a three-person team in **More Than a Hack 2027** (Metrica Sports / FC Barcelona Innovation Hub), football possession challenge. One provided match, 199,319 frames at 25 fps; one label per frame: `H`, `A`, `D` (dead ball), `X`. Ranking: **spell F1** (maximal H/A intervals matched one-to-one by same-team temporal IoU, F1 averaged over IoU 0.3â€“0.7). Deadline **17 November 2026**.

**Current release** (`restart_release.py`): 18 geometry/recent-control features â†’ frozen 31-node decision tree (fitted on four DFL matches) â†’ H/A/D log-emissions â†’ sequence decoding at switch cost 32 â†’ gap rule â†’ decoder restart across stoppage gaps â†’ gap rule â†’ kickoff patch.

**The problem.** Most remaining errors are wrong-team calls during visible play, and in about 96.5% of those episodes the tree's own evidence favours the wrong team (`docs/ownership-path-findings.md`). Every one of the 18 features is about the ball and the nearest player of each team. Re-weighting that same information has failed twice: control-memory ablation (`docs/control-memory-ablation-results.md`) and Experiment A, recent geometry (`reports/recent-geometry/2026-11-12-a/`, stage-1 FAIL, âˆ’0.0022). The model needs **new information**.

**Hypothesis.** The team in possession spreads out and moves towards the opponent's goal; the defending team contracts and closes down the ball. Adding four whole-team shape features computed from all tracked players â€” keeping every original feature, fitting row, label, weight, tree hyperparameter and downstream policy â€” improves natural provider-weighted spell F1 by at least 0.010 without unacceptable losses in D, short possessions or stress conditions.

The 0.010 hurdle is a prospective practical threshold for accepting extra complexity, not a significance claim.

---

## 2. Starting point (verify; stop if different)

- Main checkout: `C:\Users\leonj\Documents\ChatGPT\MESSI's FOOT\competition-release-work`. Branch `experiment/recent-geometry` exists with head `01aea05` (Experiment A, complete). Release branch `codex/restart-release-2026-11-11` is at `a3b5b0a07ddc561db6aafcce26dcc56d31ef2bb2`.
- **Do not change the main checkout's branch or files.** Create your own worktree **directly inside the `MESSI's FOOT` folder** (the input bindings resolve data from the checkout's parent folder, so the worktree must be a sibling of `competition-release-work`):
  `git worktree add "C:\Users\leonj\Documents\ChatGPT\MESSI's FOOT\team-shape-work" -b experiment/team-shape 01aea05`
- Frozen model SHA-256 `363c45c70838b398cd87aee7474d7e281fd392f059a31b85712e312058aaab4d`; control training semantic SHA-256 `2730cd91f67ceef88548a0fe65bf3bd899a5bc0526b6a92f937d08b2e37c55fd`.
- Pinned environments exactly as Experiment A recorded them (`reports/recent-geometry/2026-11-12-a/freeze.json`): training Python 3.12.13 / numpy 1.26.4 / pandas 2.2.2 / scikit-learn 1.5.1 / scipy 1.13.1 / joblib 1.6.0 / threadpoolctl 3.8.0 with single-thread BLAS; scoring Python 3.14.5 / numpy 2.5.1 / pandas 3.0.5. Verify versions and executable hashes. **Install nothing.**
- For tests that need `FOOTBALL_OFFICIAL_CODE`, point it (as a Windows path) at the main checkout's `.superpowers\release\official-code`.
- If anything differs, **stop and report**.

---

## 3. Calendar cut-off (fixed in advance)

- Stage-1 decision (section 9) by **23:59 local, 14 November 2026**; full verdict by **12:00 local, 15 November 2026**. Missing either: stop and report what is complete. The current release is submitted unchanged. Do not compress, skip or reorder steps to meet the cut-off.

---

## 4. Files you may create or change (in your worktree only)

**New files only:**
- `team_shape_features.py` â€” the 22-column research feature adapter.
- `team_shape_training.py` â€” training-frame loading with player positions, matched control/candidate fitting, 22-column exporter and evaluator.
- `team_shape_run.py` â€” CLI: preflight / freeze / fit / parity / natural / stress / summarise / transfer-coverage, with budget ledger.
- `tests/test_team_shape_*.py`
- `docs/team-shape-protocol.md` â€” this protocol, frozen before any fit.
- `reports/team-shape/<run-id>/` â€” aggregate receipts only.
- Append-only lines to `.gitignore` for the new aggregate reports.

**Reuse:** import `recent_geometry_regimes`, `recent_geometry_assembly` and `recent_geometry_metrics` **unchanged** (they are generic: regimes, supplied-support assembly with release parity, scoring and gates). Where an Experiment A module is column-specific (`recent_geometry_training`, `recent_geometry_features`, parts of `recent_geometry_run`), copy what you need into the new `team_shape_*` files and adapt there. **No existing file may change**, including every `recent_geometry_*` file. End check: `git diff --stat 01aea05 -- . ':!team_shape_*.py' ':!tests/test_team_shape_*' ':!docs/team-shape-protocol.md' ':!reports/team-shape' ':!.gitignore'` is empty, and `git diff 01aea05 -- .gitignore` is additions only.

**Private outputs:** `Path.home()/"Documents/ChatGPT/MESSI's FOOT/team-shape-reference"/<run-id>/`, outside Git.

Protected release modules (`restart_release.py`, `release_runtime.py`, `gap_liveness.py`, `kickoff_patch.py`, `touch_decoder.py`, `touch_evidence.py`, `gap_solver/tactical*.py`, `gap_solver/selection.py`, `gap_solver/motion.py`) are imported, never edited or monkeypatched.

---

## 5. The four new features (exact definitions)

The adapter produces 22 columns per row. **Columns 1â€“18 must be bit-identical to `gap_solver.tactical.feature_rows`** on every row of every case. Inputs are `MotionFrame.home_xy` / `away_xy` (metres, canonical 25 Hz rows); confirm units and coordinate frame per provider from the loaders and stop if any provider is not metres in one absolute pitch frame.

**Player selection.** A player counts on a row when both coordinates are finite. A team is **shape-valid** on a row when it has at least 7 counted players and the row's geometry is valid (same geometry contract as Experiment A section 5). No goalkeeper identification.

**Attacking direction (algorithmic, per team per period).** For each period, compute each team's mean x over all its shape-valid rows in that period. The team whose mean is lower attacks towards +x; the other towards âˆ’x. Define team-relative x as `x` for a +x team and `âˆ’x` for a âˆ’x team. **Stop** if both teams' period means fall on the same side of the pitch's x midpoint (taken from the loader's pitch metadata, not hard-coded), or if a period has no shape-valid rows for a team. This uses whole-period tracking, which is legitimate offline input, never labels.

**Features** (all are home minus away, so a team swap flips the sign):

19. **`shape_spread_diff`**: for each team, the root-mean-square distance of its counted players from their centroid; feature = home âˆ’ away, averaged over the trailing 25 rows (including current) on which **both** teams are shape-valid.
20. **`shape_advance_diff`**: for each team, its centroid's team-relative x now minus 25 rows earlier, in m/s (divide by 1.0 s); both rows must be shape-valid for both teams and in the same period, else unsupported. Feature = home âˆ’ away.
21. **`shape_closing_diff`**: only on rows where the ball is observed: for each team, the count of counted players within 15 m of the ball whose velocity (position now minus 5 rows earlier, Ã· 0.2 s, same period, player identity matched via `home_ids`/`away_ids`; a player without a matching id 5 rows earlier does not count; if a provider supplies no ids at all, feature 21 is unsupported for that whole provider and you say so â€” no anonymous matching) has a component towards the ball greater than 1.0 m/s. Feature = home âˆ’ away. Ball missing or any requirement unmet â†’ unsupported.
22. **`shape_support`**: 1.0 when features 19 and 20 are both supported on this row, else 0.0.

**Unsupported values are 0.0.** Windows clear at a period change, at period 0 and on invalid geometry, exactly like Experiment A's window. Never clear or alter any original feature state. No reference, status or tag field enters any new feature. The constants (7 players, 25 rows, 5 rows, 15 m, 1.0 m/s) are fixed here and were not chosen from any target aggregate.

---

## 6. Fitting (exactly two fits)

- **Training frames need player positions.** `memory_ablation_run.load_training` uses feature caches without player tracks. Load each training match (`J03WOH, J03WOY, J03WPY, J03WMX`, in that order) with `gap_solver.dfl_motion.load_dfl_motion` from the pinned training bindings (`matchinformation` + `positions_raw_observed` files plus the cache base), verifying every input hash.
- **Training-frame parity (stop if it fails):** for each training match, `feature_rows` on the motion-loaded frames must be bit-identical to `feature_rows` on the cache frames that `load_training` uses, row for row, and the reference/period arrays identical. Check this in **both** training regimes: natural, and the 30% mask applied via `gap_solver.temporal.mask_motion_frames` to motion frames versus `gap_solver.selection.mask_frames` to cache frames. Log as parity.
- **Recipe:** otherwise exactly Experiment A section 6 / `memory_ablation_training.prepare_training`: natural + 30% masks via `gap_solver.selection.ball_mask(periods, .3, 1729 + group_index)` applied to the motion frames with `gap_solver.temporal.mask_motion_frames` (removes ball and distances; player tracks stay); full feature history before selecting known H/A/D rows at `index % 5 == 0`; unit-total weight per match/regime. Expected rows **228,776**; stop if different.
- **Tree:** `DecisionTreeClassifier(max_depth=4, min_samples_leaf=125, random_state=1729)`, every other setting, class order and export format as `fit_pair`. No search, no augmentation, no other data.
- **Fit 1 â€” control:** 18 columns; training semantic SHA and model SHA must equal the values in section 2. Stop before fit 2 if either differs.
- **Fit 2 â€” candidate:** same rows, labels, weights, 22 columns; first-18 digest equals control's.
- If no appended column is used in any split: stop, "representation unused, no advancement".
- 22-column exporter parity with `predict_proba` within 1e-12 on all fitting rows (parity, not scoring).

---

## 7. Evaluation cases and regimes

Exactly Experiment A section 7: the same 15 cases (13 primary, `J03WOH`/`J03WOY` secondary), the same four regimes, the same noise generator **with a new prefix `team-shape-jitter-v1:1729:`**, the same live-gap and stoppage masks, the same hygiene rules (no provided-match constants, masks sealed before prediction). In the noise regime only the ball is perturbed; player tracks are unchanged; recompute all features. In the live-gap regime the ball is cleared; player tracks stay, so features 19, 20 and 22 remain available â€” this is the point of the experiment, report it.

---

## 8. Assembly and parity

Use `recent_geometry_assembly` unchanged. Parity gates before any candidate scoring:
1. **Feature prefix:** first 18 columns bit-identical to `feature_rows` on all 15 natural cases.
2. **Release parity:** with the reproduced control, research final labels equal the real, unmodified `restart_release.assemble(frames, (), use_restart=True).final` on all 15 natural cases.
3. **Historical reconciliation:** primary natural control mean reproduces 0.551816 (to 1e-6), per Experiment A.
4. **Training-frame parity** (section 6).

Log all parity runs in a separate `parity` ledger category: no scores, not counted against science caps. Any failure stops the study.

---

## 9. Gates, staging, budget

**Gates and staging:** exactly Experiment A section 9 (gates 1â€“6; stage 1 natural with gates 1, 3, 4, owner presence and the 0.020 per-match natural bound; stage 2 stress only after a stage-1 pass), using `recent_geometry_metrics` constants unchanged. Comparison tolerance 1e-12 for round-off only.

**Additional mechanism report (descriptive, no gate):** in the live-gap regime, strict team accuracy on hidden live frames, control vs candidate, per provider.

**Budget:** 2 fits; â‰¤ 100 case predictions; â‰¤ 115 score bundles; â‰¤ 200 feature/tree passes; â‰¤ 300 decoder passes; parity separate. Ledger claim-on-entry. A bug grants no free run.

**Transfer coverage check (after the verdict is written and committed, aggregates only):** load the provided match once with `release_runtime.load_source` (prefix from `.superpowers/release/target-handling.json` `input_prefix`; never print it) and report only: share of graded rows where each team is shape-valid, quantiles (p10/p50/p90) of counted players per team, and share of graded rows with `shape_support = 1`. Report the same three numbers for each external provider. **No prediction, no scoring, no labels, no tag times.** This is descriptive only and changes nothing.

---

## 10. Order of work

1. Start check; worktree and branch.
2. Tests first, synthetic only: every feature (spread, advance, closing, support), attacking-direction assignment and both stop conditions, 7-player threshold, window clearing, unsupported â†’ 0.0, swap symmetry (swapping teams flips the sign of 19â€“21 and leaves 22 unchanged), first 18 columns identical to `feature_rows`; training-frame parity check; matched rows; unused-column stop; exporter parity; budget refusal at each cap.
3. Full existing suite once; record result.
4. Protocol doc + freeze receipt; **commit both before any fit.**
5. Preflight (environments, input hashes, masks sealed, support, feature-prefix parity, training-frame parity).
6. Fit 1 â†’ checks â†’ fit 2 â†’ unused-column check â†’ exporter parity.
7. Release parity, reconciliation.
8. Stage 1 â†’ decision; stage 2 only on a pass.
9. Summary, verdict commit, then the transfer coverage check and its commit.

---

## 11. Hard rules

1. No provided-match material except the single aggregate-only coverage check in section 9, run after the verdict. Nothing per-frame from it goes anywhere, including to you or any hosted model.
2. The public five-minute ground truth is not used in any way.
3. No hand labels, no match-specific exceptions, no constants from the provided match.
4. Pass marks, seeds, windows, constants and budgets fixed by this brief. One run. Reruns only for a demonstrated code defect, documented with the fix and a test, inside the budget.
5. Never commit match data, arrays, predictions, CSVs or anything that reconstructs them. Aggregates only.
6. Existing files stay byte-identical (`.gitignore` append-only excepted).
7. **No push, merge, PR, submission generation or upload.** Local commits on `experiment/team-shape` only, authored and committed as `The-leonjr <277591257+The-leonjr@users.noreply.github.com>`.
8. On any stop condition: stop, preserve everything, report. Do not improvise a variant.

---

## 12. Interpretation (state in the report)

- **FAIL** rejects these four features with this recipe on this reused cohort, not team shape in general.
- **PASS** qualifies only for a separate release decision. It authorises nothing else. Name the transfer risks: SkillCorner broadcast tracking sees only part of each team; the provided tactical-camera tracking's player coverage is only described by the coverage check; the provided match lacks the ball on 42% of graded rows.
- Another experiment (home-bias symmetry) is running in parallel on the same cohort. If both pass, neither is combined with the other without a new test; that choice belongs to the user.

---

## 13. Report format (paste back exactly this)

1. Start check: worktree path, branch, base commit, environments.
2. Commits in order (freeze commit marked), new files, both diff checks.
3. Tests: new (count, pass/fail); existing suite.
4. Freeze: protocol digest, freeze commit, seeds, mask seals.
5. Fits: rows (expect 228,776); control SHAs match yes/no; candidate model SHA; which appended columns are used and where; nodes, depth; exporter parity max difference.
6. Parity: feature prefix 15/15; training-frame parity 4/4; release parity 15/15; reconciliation (0.551816 reproduced yes/no).
7. Support: live-gap windows per provider; restart events per provider Ã— same/changed; share of rows with `shape_support = 1` per provider.
8. Stage 1 table per case (spell F1, macro F1, strict interior accuracy, D precision/recall, false-D, short spells, predicted/true spells), provider means, primary delta, each gate value/threshold/pass-fail.
9. Stage 2 (if run): same per regime, gates 2, 5, 6, restart diagnostics, live-gap mechanism report.
10. Verdict: PASS/FAIL, every failing gate named.
11. Budget used; reruns.
12. Timing; cut-offs met yes/no.
13. Transfer coverage check (aggregates).
14. Limits, stated plainly (section 12 at minimum).
