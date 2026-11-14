# Live/dead sequence model Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fit one player-only temporal live/dead forest and one matched instantaneous forest, substitute their dead score into the frozen release's D-versus-live allocation on supported visible-ball rows, and evaluate the three streams externally against the fixed gates.

**Architecture:** A new isolated worktree branched from Experiment E (`player-stillness-work`, commit `83b203e`), which already holds the pinned training loader, the emission-supplied release assembly (`recent_geometry_assembly.assemble_research`, release-parity verified 15/15) and the ledger/freeze/parity harness pattern. New `live_dead_*` modules add the features, forests, integration, stress regimes, gates and the command runner. Existing files are never modified.

**Tech Stack:** Python 3.12, numpy 1.26.4, scikit-learn 1.5.1 (pinned training interpreter), the existing pinned scoring interpreter, and pytest.

**Spec:** `C:/Users/leonj/Documents/ChatGPT/MESSI's FOOT/competition-release-work/docs/superpowers/specs/2026-11-14-live-dead-sequence-design.md`, approved by the user on 2026-11-14 ("build"). It is copied into the worktree in Task 1.

## Global Constraints

- Worktree `C:/Users/leonj/Documents/ChatGPT/MESSI's FOOT/live-dead-work`, branch `experiment/live-dead-sequence`, base commit `83b203e` (Experiment E). Private root `C:/Users/leonj/Documents/ChatGPT/MESSI's FOOT/live-dead-reference`. Public reports `reports/live-dead/<run-id>/`.
- Add new files only (`live_dead_*`, `tests/test_live_dead_*`, `docs/live-dead-protocol.md`, `docs/superpowers/**`, `reports/live-dead/**`). `check_repository` must reject any other diff against the base.
- No dependency installation, provided match, public-window evaluation, hosted upload, push, merge, PR, release installation or submission change.
- Budget: 24 elapsed hours from the first implementation action (Task 1 step 1), recorded in Asia/Singapore (UTC+8). Every science command calls `enforce_deadline()` on entry and before each case.
- The feature function never reads ball fields, ball availability, ownership predictions, tags, reference, provider, match id, absolute frame/time or half number. Period is used only as a barrier.
- Forest: `RandomForestClassifier(n_estimators=32, max_depth=6, min_samples_leaf=125, max_features=1.0, bootstrap=True, criterion='gini', class_weight=None, random_state=1729, n_jobs=1)`. Exactly two fits: `instant`, then `temporal`.
- Exporter parity: dead-score absolute error ≤ `1e-12` on all fitting rows and the synthetic edge cases.
- Gate slack `1e-6` (EPS) and comparison round-off `1e-12`. Thresholds: natural gain `.010`, provider `≥ -EPS`, case `≥ -.020-EPS`, temporal over instant `> EPS`, WCSF D-recall rise `≥ .030`, D precision/recall loss `≤ .010+EPS`, false-D rise `≤ .005+EPS`, short spells (≤25 rows, IoU .5): with ≥20 spells recall loss `≤ .020+EPS`; with 1–19 no lost matched count; with 0 non-applicable. Stress: primary loss `≤ .005+EPS`, case loss `≤ .020+EPS`.
- Support floors: training match ≥1,000 selected rows, ≥125 D and ≥125 live. Primary evaluation case: ≥1,000 integration-eligible rows and ≥10% of the denominator; ≥125 known-live; DFL/WCSF also ≥125 known-D. A shortfall stops the run as UNRESOLVED.
- Science caps (cumulative, claim-on-entry, never refunded): `fit=2`, `prediction=123`, `score=123`, `decoder_pass=246`, `feature_pass=213` (41 bundles × (liveness + frozen-feature + 3 tree passes) + 8 training preparations). Parity is a separate category capped at 36 identities: `exporter/<run>/{instant,temporal}` (2), `training-alignment/<run>/<match>` (4), `release/<run>/<case>` (15) and `disabled/<run>/<case>` (15). Historical reconciliation scoring happens inside `release/…` parity and produces no science score.
- Stress seed prefix `live-dead-sequence-v1:1729:`.
- Verdicts: `PASS` (supports a separate release investigation), `NO_ADVANCEMENT` (scientific failure), `UNRESOLVED`/`INVALID` (support, integrity, incompleteness or timeout).

## Review Focus

1. **Ambiguous or missing player IDs**: a duplicated ID within a team, or a `None` ID, is excluded from both the spatial count and speeds; it is never matched to "the first" occurrence. Pinned by `test_duplicate_and_null_ids_excluded` (Task 2).
2. **Windows at period edges, recording edges and invalid-geometry rows**: those positions are zero with zero masks, never edge-padded, and a single invalid row between centre and offset breaks support. Pinned by `test_window_barriers_never_pad` (Task 2).
3. **A support row with `h+a == 0`**: the substitution uses `r=.5`, and the output triple still sums to 1. Pinned by `test_zero_live_support_uses_half` (Task 4).
4. **A team with no players left after degradation**: the nearest-player distance becomes `None` exactly as the loader would produce it, and frozen features still compute. Pinned by `test_degrade_empty_team_distance_none` (Task 5).
5. **A head that covers no rows on a case**: the case reproduces frozen supports, labels and CSV bytes exactly, rather than erroring or silently altering anything. Pinned by `test_empty_mask_reproduces_frozen` (Task 4) and the per-case `disabled/` parity (Task 7).

---

### Task 1: Worktree, pinned inputs and the timing record

**Files:**
- Create: `docs/superpowers/specs/2026-11-14-live-dead-sequence-design.md` (copied byte for byte)
- Create: `docs/superpowers/plans/2026-11-14-live-dead-sequence.md` (this file, copied)
- Create: `docs/live-dead-protocol.md`
- Create: `live_dead_protocol.py`
- Test: `tests/test_live_dead_protocol.py`

**Interfaces:**
- Produces: `live_dead_protocol.START_LOCAL: str`, `DEADLINE_LOCAL: str` (ISO with `+08:00`), `enforce_deadline(at: datetime | None = None) -> None` (raises `ValueError('Budget deadline passed')`), `SEED_PREFIX = 'live-dead-sequence-v1:1729:'`, `PRIMARY: tuple[str, ...]` (13 ids), `SECONDARY = ('dfl-J03WOH', 'dfl-J03WOY')`, `CASES = PRIMARY + SECONDARY`, `TRAIN_MATCHES = ('J03WOH', 'J03WOY', 'J03WPY', 'J03WMX')`, `provider_of(cid) -> str`, `FROZEN_MODEL_PATH` = Experiment E's `reports/player-stillness/2026-11-12-a/models/control.json`, and `load_frozen_model() -> dict`, which raises unless `model_digest(model) == memory_ablation.MODEL_SHA`.

- [ ] **Step 1: Record the start.** Run `python -c "from datetime import datetime,timezone,timedelta; print(datetime.now(timezone(timedelta(hours=8))).isoformat(timespec='seconds'))"`. That value is `START_LOCAL`, and `DEADLINE_LOCAL` = start + 24 h.
- [ ] **Step 2: Create the worktree.** From `competition-release-work` run `git worktree add "../live-dead-work" -b experiment/live-dead-sequence 83b203e`, then copy the spec and this plan into it.
- [ ] **Step 3: Pin the interpreters.** Read `player-stillness-reference/2026-11-12-a/environment-map.json` and use its `scoring_python` as `$PY` for every test command (prefix `-I`), and its `training_python` for fits only. Expected: both paths exist, and `$TRAIN -c "import sklearn;print(sklearn.__version__)"` prints `1.5.1`.
- [ ] **Step 4: Write `docs/live-dead-protocol.md`.** Include the start and deadline, the plan and spec SHA-256 values, the parity cap list, the stress mechanics from Task 5 and the gates, copied from Global Constraints.
- [ ] **Step 5: Write the failing tests.**

```python
def test_deadline_is_start_plus_24h():
    assert datetime.fromisoformat(DEADLINE_LOCAL) - datetime.fromisoformat(START_LOCAL) == timedelta(hours=24)

def test_enforce_deadline_raises_after():
    with pytest.raises(ValueError, match='deadline'):
        enforce_deadline(datetime.fromisoformat(DEADLINE_LOCAL) + timedelta(seconds=1))

def test_cases_are_13_primary_2_secondary():
    assert len(PRIMARY) == 13 and not set(PRIMARY) & set(SECONDARY)
    assert {provider_of(c) for c in PRIMARY} == {'skillcorner', 'dfl', 'wcsf'}

def test_frozen_model_digest():
    assert model_digest(load_frozen_model()) == MODEL_SHA
```

- [ ] **Step 6:** Run `$PY -I -m pytest tests/test_live_dead_protocol.py -q`. It should FAIL with an import error. Implement the module, then rerun. Expected: 4 passed.
- [ ] **Step 7: Commit** with the message `Start live/dead sequence experiment: worktree, spec, plan, timing record`.

### Task 2: Player-only liveness features and ordered windows

**Files:**
- Create: `live_dead_features.py`
- Test: `tests/test_live_dead_features.py`

**Interfaces:**
- Consumes: `recent_geometry_features.geometry_valid(frame)` and `MotionFrame` fields `period, home_xy, away_xy, home_ids, away_ids, geometry_valid`.
- Produces:
  - `FRAME_COLUMNS = 10`, `OFFSETS = tuple(range(-50, 51, 5))` (21), `WINDOW_COLUMNS = 210`
  - `frame_vectors(frames, pitch: tuple[float, float]) -> np.ndarray` float32 `(n, 10)`
  - `barrier_ids(frames) -> np.ndarray` int64 `(n,)`: a run id that changes at every period change and at every invalid-geometry row (an invalid row gets its own unique id and is never inside a run)
  - `window_matrix(vectors, barriers) -> np.ndarray` float32 `(n, 210)`
  - `eligibility(vectors, barriers) -> np.ndarray` bool `(n,)`
  - `liveness_inputs(frames, pitch) -> LivenessInputs(instant: (n,10) float32, temporal: (n,210) float32, eligible: (n,) bool)`

Column order per row (index 0–9): `count/22`, `pairs/22`, `q25/12`, `q50/12`, `q75/12`, `frac<1`, `frac>3`, `rms/diag`, `spatial_mask`, `motion_mask`, where `diag = hypot(*pitch)`.

Rules, as in the spec:
- A spatial player at row t has a non-null ID that appears exactly once within its team at t, and finite x and y. The count is capped at 22.
- A usable speed at t needs the same (team, id) spatial-qualified at both t and t−5, rows t−5…t all `geometry_valid` with the same nonzero period, and a speed of `dist / 0.2` below 12. A speed ≥ 12 is dropped, not clipped.
- Spatial support needs ≥10 players. Motion support needs ≥10 speeds.
- Quantiles use `np.quantile(speeds_float64, (.25,.5,.75), method='linear')`. Fractions use `< 1.0` and `> 3.0`. RMS is the square root of the mean squared distance to the pooled centroid of both teams. Values are computed in float64 and cast to float32 last.
- Unsupported groups are zero: columns 0 and 7 with spatial, columns 1–6 with motion.
- A window position `t+k` is supported only if `0 ≤ t+k < n` and `barriers[t+k] == barriers[t]`; otherwise all 10 columns are zero. Columns are ordered offset by offset, chronologically.
- `eligibility` requires centre spatial and motion masks, ≥5 motion-supported positions with k<0 and ≥5 with k>0, and a valid centre (`geometry_valid`, period in (1,2)).

- [ ] **Step 1: Write the failing tests**, using `gap_solver.motion.motion_frame` to build 25 Hz fixtures.

```python
def test_team_swap_invariant():          # swapping home/away lists and ids -> identical frame_vectors bytes
def test_ignores_ball_and_status():      # changing ball xy/observed/tags/reference fields -> identical liveness_inputs bytes
def test_duplicate_and_null_ids_excluded():  # one duplicated id + one None id among 12 -> count == 10/22, both absent from speeds
def test_speed_outlier_rejected():       # a 3.0 m move in 0.2 s (15 m/s) -> pairs drops by 1, q75 < 12/12
def test_speed_requires_six_valid_rows():# geometry_valid False at t-3 -> motion_mask 0 at t
def test_sparse_support_zeroes_group():  # 9 players -> cols 0,7,8 == 0; 9 speeds -> cols 1..6,9 == 0
def test_quantiles_linear():             # speeds [0,1,2,3,...] -> q25/q50/q75 equal np.quantile(..., method='linear')/12
def test_window_order_and_offsets():     # temporal[t, 10*j:10*j+10] == instant[t+OFFSETS[j]] for supported positions; j=10 is centre
def test_window_barriers_never_pad():    # t near period change, start/end of recording and next to an invalid row -> those slots all zero
def test_eligibility_needs_five_each_side(): # 4 supported before -> False; 5 and 5 -> True
def test_instant_is_window_centre():     # instant == temporal[:, 100:110]
```

- [ ] **Step 2:** Run `$PY -I -m pytest tests/test_live_dead_features.py -q`. Expected: FAIL (module missing).
- [ ] **Step 3: Implement `live_dead_features.py`** with the signatures above. Use a vectorised `window_matrix` (shifted copies multiplied by a barrier-equality mask), with no Python loop over centres.
- [ ] **Step 4:** Run the same command. Expected: 11 passed.
- [ ] **Step 5: Commit** with the message `Add player-only liveness features and ordered windows`.

### Task 3: Training rows, forests and the portable exporter

**Files:**
- Create: `live_dead_training.py`
- Test: `tests/test_live_dead_training.py`

**Interfaces:**
- Consumes: `player_stillness_training.load_training_groups(input_map, expected)` (yields `match, frames, reference, periods, cache_*` per DFL match), `team_shape_training.alignment_check(group, i)`, `memory_ablation_training.semantic_digest` and `model_digest`, and `live_dead_features.liveness_inputs`.
- Produces:
  - `TrainingSet(instant, temporal, target uint8, weights float64, row_identity int64 (n,2) [group, row], counts tuple[dict])`, frozen and read-only
  - `select_training(groups, pitch) -> TrainingSet`: windows are built on full natural motion frames first; a row is kept when `row % 5 == 0`, `reference < 3` and it is eligible; target is `reference == 2`; each match's weights sum to 1
  - `check_floors(ts) -> list[str]`: shortfall messages against the 1,000 / 125 / 125 floors (empty when OK)
  - `PARAMETERS` (the exact dict from Global Constraints)
  - `fit_pair(ts, on_fit_entry) -> dict(instant=..., temporal=...)`: exactly two fits in order `instant`, `temporal`, each calling `on_fit_entry(mode)` before `.fit`
  - `export_forest(clf, n_features) -> dict(feature_count, n_estimators, trees=[dict(children_left, children_right, feature, threshold, dead)])`, where `dead` is the per-node class-1 fraction from `tree_.value` normalised per row
  - `dead_scores(matrix, model) -> np.ndarray` float64: X is cast to float32, compared `<=` to the float64 threshold, and the per-tree leaf `dead` values are summed in tree order then divided by `n_estimators`
  - `validate_forest(model, n_features)`: rejects cyclic or unreachable nodes, a bad dimension or a non-finite or out-of-range `dead`

- [ ] **Step 1: Write the failing tests.**

```python
def test_selection_every_fifth_known_eligible():  # synthetic groups: kept rows ⊆ {r%5==0, ref<3, eligible}; X excluded
def test_unit_weight_per_match():                 # sum(weights[group==g]) == 1.0 for every g (abs 1e-12)
def test_floors_report_shortfalls():              # match with 124 D -> message names match and 'D'
def test_both_models_share_rows():                # fit_pair sees identical target/weights/row_identity digests
def test_fit_order_and_count():                   # on_fit_entry calls == ['instant', 'temporal']
def test_exporter_parity_fitting_rows():          # small synthetic fit (min_samples_leaf overridden only in test helper): |dead_scores - predict_proba[:,1]| <= 1e-12
def test_exporter_parity_threshold_edges():       # rows equal to float32(threshold) and nextafter both sides route as sklearn
def test_validate_rejects_cycle_and_bad_dead():
```

`test_exporter_parity_fitting_rows` calls a test-only helper `_fit_one(X, y, w, **override)`. Production `fit_pair` accepts no overrides.

- [ ] **Step 2:** Run `$TRAIN -I -m pytest tests/test_live_dead_training.py -q`. Expected: FAIL.
- [ ] **Step 3: Implement** the interfaces above. `fit_pair` snapshots the semantic digests of all inputs before and after fitting and raises if anything changed. It also computes `parity = max|dead_scores - predict_proba[:,1]|` and raises if it exceeds `1e-12`.
- [ ] **Step 4:** Run the same command. Expected: 8 passed.
- [ ] **Step 5: Commit** with the message `Add live/dead forest training and portable exporter`.

### Task 4: Integration with the frozen release supports

**Files:**
- Create: `live_dead_assembly.py`
- Test: `tests/test_live_dead_assembly.py`

**Interfaces:**
- Consumes: `memory_ablation.predict_supports(matrix18, model)`, `gap_solver.tactical.feature_rows`, `recent_geometry_assembly.SupportSet` and `assemble_research`, and `release_runtime.submission_bytes`.
- Produces:
  - `STREAMS = ('release', 'instant', 'temporal')`
  - `frozen_supports(frames, frozen_model) -> (n,3) float64`: `predict_supports(np.asarray(list(feature_rows(frames)), np.float32), frozen_model)`
  - `integration_mask(frames, eligible) -> bool (n,)`: `eligible & ball_observed & geometry_valid & period in (1,2)`
  - `denominator_mask(frames) -> bool (n,)`: the same without `eligible`
  - `integrate(frozen, q, mask) -> (n,3)`: on masked rows q is clipped to `[1e-6, 1-1e-6]`, `r = h/(h+a)` if `h+a>0` else `.5`, and the row becomes `((1-q)r, (1-q)(1-r), q)`; other rows are copied bit for bit
  - `StreamSupportSet(SupportSet)`, which overrides `__post_init__` to accept `STREAMS` with the same finite `(n,3)` validation
  - `assemble_stream(frames, stream, supports) -> ResearchAssembly` (delegates to `assemble_research`)
  - `require_same_gaps(assemblies: dict) -> None`, which raises if `stoppage_gaps` differ across streams

- [ ] **Step 1: Write the failing tests.**

```python
def test_substitution_values():          # h,a,d=(.6,.2,.2), q=.5 -> (.375,.125,.5)
def test_ratio_preserved_and_normalised(): # random supports/q: rows sum to 1 (1e-12); h'/(h'+a') == h/(h+a) where h+a>0
def test_zero_live_support_uses_half():  # (0,0,1), q=.4 -> (.3,.3,.4)
def test_q_clipped():                    # q=0 -> d'=1e-6; q=1 -> d'=1-1e-6
def test_unmasked_rows_bitwise_copied(): # frozen[~mask].tobytes() == out[~mask].tobytes()
def test_empty_mask_reproduces_frozen(): # synthetic frames: assemble_stream('temporal', integrate(f, q, zeros)) equals assemble_stream('release', f) in every Assembly field and submission_bytes
def test_mask_requires_observed_ball():  # eligible row with ball_observed False is never in integration_mask
def test_rejects_unknown_stream_and_bad_shapes():
```

- [ ] **Step 2:** Run `$PY -I -m pytest tests/test_live_dead_assembly.py -q`. Expected: FAIL.
- [ ] **Step 3: Implement** the interfaces above. The module reads no reference.
- [ ] **Step 4:** Run the same command. Expected: 8 passed.
- [ ] **Step 5: Commit** with the message `Add live/dead integration into frozen supports`.

### Task 5: Stress regimes

**Files:**
- Create: `live_dead_regimes.py`
- Test: `tests/test_live_dead_regimes.py`

**Interfaces:**
- Consumes: `recent_geometry_regimes.JITTER_SIGMA` (.25), `_nearest`, `distance_recompute_audit`, and `live_dead_protocol.SEED_PREFIX`.
- Produces:
  - `jitter_ball(frames, cid) -> list`: the existing visible-ball jitter (identical code path to `player_stillness_run.add_visible_ball_noise`) with seed `int(sha256((SEED_PREFIX + 'jitter:' + cid).encode()).hexdigest()[:8], 16)`
  - `degrade_players(frames, cid) -> list`
  - `removal_keys(frames, cid) -> set[tuple]` (exposed for tests)

Degradation mechanics, fixed here:
- Blocks are 125 rows counted from each period's first row (`block = (row - period_start) // 125`). Period-0 rows pass through unchanged.
- Within each (period, block), collect the distinct `(team, id)` pairs with a non-null ID present on any row. Rank them by `sha256(f'{SEED_PREFIX}{cid}:{period}:{block}:{team}:{id}')` hex, ascending, and remove the first `n // 4` from every row of that block. A null-ID player is never removed.
- Noise follows removal: `random.Random(int(sha256((SEED_PREFIX + 'degrade-noise:' + cid).encode()).hexdigest()[:8], 16))` draws in the order rows ascending → home then away → stored player order → `gauss(0,.25)` for x then y. Non-finite players draw nothing.
- After removal and noise, `home_distance`/`away_distance` are recomputed with `_nearest` against the unchanged ball (or `None` if the ball is unobserved or the team is empty). The ball, periods, flags and references are unchanged. IDs are taken as already associated by the adapter, so association happens before degradation.

- [ ] **Step 1: Write the failing tests.**

```python
def test_jitter_leaves_players_identical():   # liveness_inputs(jitter_ball(f)) bytes == liveness_inputs(f) bytes
def test_degrade_deterministic():             # two calls -> identical frames
def test_degrade_quarter_per_block():         # 22 ids per block -> exactly 5 removed per block; keyed by sha256 order
def test_degrade_independent_of_reference():  # function signature has no reference; changing reference-only fields leaves output identical
def test_degrade_leaves_ball_and_periods():
def test_degrade_distances_recomputed():      # distance_recompute_audit(degraded) reports 0 mismatches
def test_degrade_empty_team_distance_none():  # block where all home ids removed -> home_distance is None, feature_rows succeeds
```

- [ ] **Step 2:** Run `$PY -I -m pytest tests/test_live_dead_regimes.py -q`. Expected: FAIL.
- [ ] **Step 3: Implement** the interfaces above.
- [ ] **Step 4:** Run the same command. Expected: 7 passed.
- [ ] **Step 5: Commit** with the message `Add live/dead stress regimes`.

### Task 6: Three-stream metrics and gates

**Files:**
- Create: `live_dead_metrics.py`
- Test: `tests/test_live_dead_metrics.py`

**Interfaces:**
- Consumes: `recent_geometry_metrics.score_bundle` and `flatten` (scalars `spell_f1, dead_precision, dead_recall, false_d, short_n_gt, short_matched, short_recall, pred_H, pred_A, sup_H, sup_A, interior_acc`).
- Produces (flats shape: `{cid: {stream: flat}}`):
  - `weighted(values: {cid: float}) -> (float|None, {provider: float|None})`, taken over `PRIMARY` with 1/3 per provider and equal match weight
  - `gate_natural(flats) -> dict`, with checks `spell_gain`, `provider_nonregression`, `case_loss`, `temporal_over_instant`, `wcsf_dead_recall_rise`, `dead_precision`, `dead_recall`, `false_d`, `owner_presence`, `short_spells`. It also reports `interior_accuracy` but never makes it a requirement.
  - `gate_stress(flats) -> dict`, with checks `primary_loss`, `case_loss`, `dead_precision`, `dead_recall`, `false_d`, `owner_presence` and `short_spells`
  - `coverage_floors(case_counts: {cid: dict(denominator, integration, known_live, known_d)}) -> list[str]`
  - `verdict(gates: dict, problems: list[str]) -> str`: any problem or `None`/unresolved check gives `'UNRESOLVED'`; otherwise any fail gives `'NO_ADVANCEMENT'`; otherwise `'PASS'`

All comparisons are temporal against release, except `temporal_over_instant`, using the thresholds in Global Constraints. Every check value is `None` when required support is missing; that counts as unresolved, never as a pass.

- [ ] **Step 1: Write the failing tests** on hand-built flats.

```python
def test_gain_exactly_threshold_passes():     # +0.010 primary -> spell_gain pass; +0.00999 -> fail
def test_provider_and_case_bounds():          # provider -1e-6 passes, -2e-6 fails; case -0.020 passes, -0.0201 fails
def test_temporal_must_beat_instant():        # temporal == instant + 1e-6 -> fail; +2e-6 -> pass
def test_wcsf_recall_rise():                  # +0.030 pass, +0.029 fail; missing recall -> unresolved
def test_short_spell_regimes():               # n_gt 20 loss .020 pass; n_gt 5 lost 1 fail; n_gt 0 non_applicable
def test_interior_never_required():           # interior drop alone -> PASS
def test_secondary_excluded():                # changing J03WOH flats does not change any gate
def test_skillcorner_has_no_dead_checks():
def test_coverage_floors_messages():          # 999 rows / 9.9% / 124 live / WCSF 124 D each named; skillcorner D ignored
def test_verdict_precedence():                # problems -> UNRESOLVED even if a check fails
```

- [ ] **Step 2:** Run `$PY -I -m pytest tests/test_live_dead_metrics.py -q`. Expected: FAIL.
- [ ] **Step 3: Implement** the interfaces above.
- [ ] **Step 4:** Run the same command. Expected: 10 passed.
- [ ] **Step 5: Commit** with the message `Add live/dead three-stream gates`.

### Task 7: Run harness (ledger, freeze, preflight, fit, parity, stages)

**Files:**
- Create: `live_dead_run.py`
- Test: `tests/test_live_dead_run.py`

**Interfaces:**
- Consumes: everything above, plus the patterns in `player_stillness_run.py` (`Ledger`, `run_paths`, `store_exact`, `verified_bindings`, `pinned_environments`, `adapter_load`, `save_arrays`/`load_arrays`, `reconcile_against_history`, `primary_natural_check`). Copy those helpers rather than importing them, so that the constants (`PRIVATE_ROOT`, report root, caps, parity identities, branch name `experiment/live-dead-sequence`, `BASE_COMMIT='83b203e…'` with the full hash taken from `git rev-parse 83b203e`) are this experiment's own.
- Produces the CLI `$PY -I live_dead_run.py <command> --run-id <id>`, with commands `freeze, preflight, fit, parity, natural, stress, summarise`. Each command refuses to rerun when its output exists (attempts are preserved).
  - `freeze`: hashes the sources, protocol doc, spec, plan, inputs, environments and `protocol_parameters()`, and writes `freeze.json` plus private maps. `frozen()` re-verifies all of this on every later command and requires `freeze.json` to be committed.
  - `preflight`:
    - Training: loads the groups, claims `training-alignment` parity and runs `alignment_check`, builds the `TrainingSet` (claiming `feature_pass training/{instant,temporal}/<match>`), and applies `check_floors`.
    - Pitch: the canonical pitch comes from each binding's metadata `notes['canonical_pitch_m']`; all 15 cases and 4 training caches must be identical, or it stops.
    - Evaluation: for each case it builds the liveness inputs, frozen 18-column features, the denominator and integration masks, and the reference counts on the integration set, then saves private arrays and hashes. It then applies `coverage_floors`.
    - On any shortfall it writes `status='UNRESOLVED_support'` and stops.
  - `fit`: runs in a `training_python` worker, exactly as `player_stillness_run.fit`, with ledger fit identities `instant` then `temporal`. Models go to `reports/live-dead/<id>/models/{instant,temporal}.json` and their SHAs to `fit.json`.
  - `parity`:
    - Exporter: claims `exporter/<id>/{instant,temporal}` and requires both parity values ≤ 1e-12.
    - Release: for each of the 15 cases, it claims `release/<id>/<cid>`; `restart_release.assemble(frames, ())` must equal `assemble_stream('release', frozen_supports)` in all seven fields, and the historical reconciliation must pass. The primary natural mean must be 0.551816 to 1e-6.
    - Disabled head: it claims `disabled/<id>/<cid>`; integrating with an all-false mask must reproduce the release fields and `submission_bytes` exactly.
  - `natural` and `stress`: per bundle the run claims `feature_pass` liveness + frozen, then for each stream claims `prediction`, `feature_pass .../tree`, 2× `decoder_pass` and `score`, and checks `require_same_gaps`. It writes the public per-case receipt (flats, coverage by period and visible/missing stratum, corrections and new errors in supported/fallback strata, per-IoU TP/FP/FN, possession counts and durations). Private npz files hold the supports, q, labels and hashes.
    - `stress` runs only if `stage1.json` says `PASS`. It covers the 13 primary cases × `jitter` then `degrade`, asserts that the liveness bytes are unchanged under `jitter`, and recomputes all three streams from the transformed frames (never stale frozen supports).
  - `summarise`: writes `summary.json` and `report.md` with the verdict and every shortfall, using public aggregates only.

- [ ] **Step 1: Write the failing tests** (no real data).

```python
def test_caps_match_protocol():          # CAPS == dict(fit=2, prediction=123, score=123, decoder_pass=246, feature_pass=213); parity cap 36
def test_fit_order_enforced():           # claiming 'temporal' before 'instant' -> BudgetError
def test_no_reclaim():                   # same identity twice -> BudgetError
def test_parity_identities_whitelisted():# 'release/<run>/dfl-J03WR9' ok; 'release/<run>/provided' rejected
def test_deadline_checked_on_entry():    # monkeypatched clock past DEADLINE -> every science command raises before loading data
def test_stress_requires_stage1_pass():  # stage1 NO_ADVANCEMENT -> stress raises, no claims written
def test_check_repository_rejects_existing_file_edits(): # diff touching player_stillness_run.py -> ValueError
```

- [ ] **Step 2:** Run `$PY -I -m pytest tests/test_live_dead_run.py -q`. Expected: FAIL.
- [ ] **Step 3: Implement** `live_dead_run.py` as above.
- [ ] **Step 4:** Run `$PY -I -m pytest tests/test_live_dead_*.py -q`, then the inherited suite `$PY -I -m pytest tests -q -x`. Expected: everything passes, and the inherited suite matches its count at base `83b203e`.
- [ ] **Step 5: Commit** with the message `Add live/dead run harness`.

### Task 8: Execute the fixed experiment

Use run id `2026-11-14-a`. Run every command with the deadline active. **Stop at the first non-success and record it; do not rerun or change gates.**

- [ ] **Step 1: Freeze.** Run `$PY -I live_dead_run.py freeze --run-id 2026-11-14-a`, then commit `reports/live-dead/2026-11-14-a/freeze.json` and the protocol doc with the message `Freeze live/dead protocol`. Expected: `status frozen`.
- [ ] **Step 2: Preflight.** Run `$PY -I live_dead_run.py preflight --run-id 2026-11-14-a`. Expected: `ready`. If it reports `UNRESOLVED_support`, commit the receipt, go to Step 6 and do not fit.
- [ ] **Step 3: Fit.** Run `$PY -I live_dead_run.py fit --run-id 2026-11-14-a`. Expected: `complete`, `fits 2`. Commit `fit.json` and `models/`.
- [ ] **Step 4: Parity.** Run `$PY -I live_dead_run.py parity --run-id 2026-11-14-a`. Expected: `passed`, release parity 15/15, disabled parity 15/15, primary natural mean `0.551816`. Commit.
- [ ] **Step 5: Stage 1.** Run `$PY -I live_dead_run.py natural --run-id 2026-11-14-a` and commit `stage1.json` with the case receipts. If the result is `PASS`, run `stress` and commit `stage2.json`.
- [ ] **Step 6: Summarise.** Run `$PY -I live_dead_run.py summarise --run-id 2026-11-14-a` and commit `summary.json` and `report.md` with the message `Record live/dead outcome: <VERDICT>`.

### Task 9: Preservation check and handover

- [ ] **Step 1:** Run `git diff --name-only 83b203e HEAD`. Expected: only paths with the new-file prefixes.
- [ ] **Step 2:** Run `git -C ../competition-release-work status --short`. Expected: nothing changed except this plan file. Then hash the current submission and frozen model artifacts recorded in `competition-release-work/docs/competition-release.md` and confirm they are unchanged.
- [ ] **Step 3:** Hand over the verdict, the gate table and every shortfall to the user. Do not push, merge or promote anything.
