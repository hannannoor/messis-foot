# Controlled Memory Ablation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans inline, task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. The user explicitly approved implementation and draft PR publication after reviewing the design; continue without another permission loop for the same scope.

**Goal:** Build and run one controlled retained-owner block ablation, reporting the fixed experiment's pass/fail/unresolved result without changing the release.

**Architecture:** A reference-free input/feature transform and portable predictor serve matched training and evaluation. Separate training, metrics/gates and execution-protocol modules enforce the exact recipe, two-fit/sixty-evaluation budget, prospective seals, owned schemas and read-only verification. All real arrays remain private; only portable models and bounded receipts are public candidates.

**Tech Stack:** CPython 3.14.5/NumPy 2.5.1 scoring and unittest; workspace-local Python 3.12 x64 training with the historical pinned core dependencies, fully locked before fitting; existing official metrics/adapters. New source grammar remains Python 3.9 compatible.

**Spec:** `docs/superpowers/specs/2026-11-09-control-memory-ablation-design.md`, approved by the user's explicit “Approve implementation and draft PR publication” response. One fresh builder check returned “nothing important left.”

## Global Constraints

- Branch `codex/control-memory-ablation-2026-11-09`, base b5878dd, approved design commit fccaa04. Use the existing clean isolated clone sequentially; preserve PRs 1–4 and all prior files/ledgers/results/CSV generations. No challenge/public-window outcomes, new data acquisition, target inference, installation into Desktop, default change or merge.
- Exactly one feature block: indices 15/16/17 become (0.,0.,10.) for candidate training and inference; every other column stays bit-identical. Original generator, 18-column schema, source periods/eligibility, w=0, c=32, floor1e-6, ties, neutral missing rows, unsupported X and materialization stay fixed.
- Four DFL fitting matches in order J03WOH/J03WOY/J03WPY/J03WMX. Natural then original 30% training mask with seeds 1729+index; original modulo-five known-H/A/D row selection and per-match/regime weights. Depth4, leaf125, seed1729, float32 features, float64 weights, existing exporter; no search/calibration.
- Reconstructed control canonical model SHA must equal 363c45c70838b398cd87aee7474d7e281fd392f059a31b85712e312058aaab4d before candidate fit. Each export must match sklearn supports on all prepared training rows at atol1e-12, rtol0.
- Two real estimator fits maximum for this experiment; 30 fixed cases × two variants =60 real inference/scoring attempts maximum. New run IDs do not reset consumed budgets. Preserve incomplete attempts; stop on drift/failure rather than silently retrying.
- Fifteen fixed used matches and two regimes exactly as the spec. Thirteen fit-disjoint matches determine primary equal-provider/equal-match natural mean spell F1; two overlapping DFL diagnostics never rescue it. All evidence remains used, never fresh validation.
- Gates: natural primary gain >1e-6; natural provider nonregression and masked primary nonregression; at most .01 per fit-disjoint case spell loss, .01 D precision/recall or SC false-D loss, short-spell .02 recall loss at >=20 support/otherwise no matched-count loss; reject owner collapse. Other scalar loss gates get1e-6 slack; count/support equality is exact. Zero-short-spell cases are non-applicable; missing required D/primary support is unresolved.
- Public code/models/aggregate receipts only. Per-frame features/targets/weights/predictions/references/masks/events/input paths remain private. Owned schemas + existing publication guard; canonical bytes and trusted hash-key sets. Verify never constructs features, fits, infers or scores.
- Approved publication: new draft PR in hannannoor/messis-foot as live-verified The-leonjr/277591257, code/tests/docs/fitted portable-model arrays/metadata/bounded derived aggregates, no raw/per-frame data. Preserve main/older PRs; no merge.

## Review Focus

1. The candidate must not receive original memory during inference or mutate the control matrix; scalar/matrix transforms and the fifteen untouched columns need literal tests.
2. A plausible but different training reconstruction must not become an accepted control; original order/masks/weights and exact model digest gate must precede candidate fitting.
3. Reusing a run ID, changing roots or restarting after failure must not grant extra scientific attempts; global ownership/claims and cross-run tests enforce the cap.
4. An overall gain can conceal D, short-spell, masked or single-provider regressions; literal threshold/denominator/provider-weight tests must fail those cases.
5. Verification and publication must reject hidden event arrays, duplicate-key summaries, arbitrary identity-map keys or stale runtime/source/model bindings without executing computations.

---

## Files and task boundaries

- `memory_ablation.py`: constants, pure feature transformation, input-only prepared arrays and model-parameterized portable inference.
- `memory_ablation_training.py`: exact training preparation and matched fitting/export; sklearn imported only at fit boundaries.
- `memory_ablation_metrics.py`: bounded metric schema, pure per-variant scoring and prespecified arithmetic gate summary.
- `memory_ablation_protocol.py`: explicit cohort/input/source bindings, global attempt ownership, model/receipt schemas, seals and persistence.
- `memory_ablation_run.py`: CLI and sequential lifecycle; no old experiment commands are invoked.
- `tests/test_memory_ablation*.py`: synthetic-only unit/protocol tests; pinned-environment training tests run explicitly.
- `requirements-memory-ablation.lock`: complete resolved wheel-hash lock, retaining the historical core pins. Local interpreter/venv/download cache stay under ignored `.superpowers/memory-ablation/`.
- Public candidate outputs: `reports/memory-ablation/2026-11-09-v1/`; private generation and global experiment budget under sibling `memory-ablation-reference/`. Findings/review docs are separate. Add only exact report/model path exceptions to .gitignore.

### Task 1: Reference-free feature and inference contract

**Create:** `memory_ablation.py`, `tests/test_memory_ablation.py`.

**Interfaces:** `transform_row(row,mode) -> tuple`; `transform_matrix(matrix,mode) -> float32 ndarray`; `prepare_inputs(frames) -> PreparedInputs(matrix,periods,observed,usable)`; `predict_supports(matrix,model) -> float64 ndarray`; `infer_prepared(inputs,model,mode) -> Prediction(supports,latent,final,policy_counts)`. Modes are exactly `control` and `memory-ablated`; no mutable global head replacement.

- [ ] Write literal tests: row range(18) yields unchanged0..14 plus(0,0,10); control is unchanged; source data never mutates; scalar/matrix agreement, invalid dimensions/modes/nonfinite values, period/barrier/unsupported carry and reference-independent inputs. Compare control latent/final arrays to released pure prediction on full synthetic geometry. Check candidate inputs reach its model with the declared neutral block, including masked rows.
- [ ] Run `python -m unittest discover -s tests -p test_memory_ablation.py -v`; expect RED missing module/functions.
- [ ] Implement the declared functions using original feature generator, PortableTree validation, verified float32/float64 vectorized traversal, unchanged decode_ball_gap/materialization. No reference argument, hints rejected.
- [ ] Run GREEN plus `test_soft_sequence.py`/`test_ball_gap_policy.py`; expect all pass. Commit `feat: add isolated retained-owner ablation inference`.

### Task 2: Reproducible training preparation and guarded paired fit

**Create:** `memory_ablation_training.py`, `tests/test_memory_ablation_training.py`, `requirements-memory-ablation.lock`.

**Interfaces:** consumes Task1 matrix transform/support traversal. `prepare_training(groups) -> TrainingData(matrix,target,weights,row_identity,group_counts)` where groups are ordered match/frame/reference/period records; `fit_pair(data,on_fit_entry,expected_control_sha=FROZEN_SHA) -> dict` with control/candidate portable artifacts and bounded receipts. `on_fit_entry(mode)` executes immediately before estimator.fit and cannot be bypassed by the CLI. Synthetic tests use independent fixtures/callbacks, never the real budget.

- [ ] Provision only the approved workspace-local Python3.12 interpreter with uv --install-dir/--no-bin/--no-registry and local cache, then local venv. Resolve/pin all transitive packages and wheel hashes from requirements-training.txt, install binary wheels from that lock. Record exact interpreter/download provenance, package/platform/BLAS settings before real fitting. No global installs. Verify sklearn1.5.1/numpy1.26.4/scipy1.13.1/pandas2.2.2 imports; no real data/fit yet.
- [ ] Write independent literal preparation tests for exact group order, natural/masked ordering, train mask seeds, whole-input feature generation before take, modulo-five/X exclusion, weights summing1 per group and separate eval-mask convention. Assert candidate differs only in the three columns and targets/weights/order do not change.
- [ ] Write synthetic fit tests for two fixed estimator configurations, export all-row parity, no split on constant block, exact control digest failure stopping before candidate entry, callback-before-fit ordering and import separation. Tests requiring sklearn must actually execute under3.12, not be treated as passed skips under3.14.
- [ ] Run both missing-feature suites RED, implement exact recipe with lazy sklearn import/PortableTree export; retain failed reconstruction artifact privately. Run GREEN under pinned3.12 plus Task1 tests. Commit `feat: reproduce and fit a bounded memory ablation pair`.

### Task 3: Bounded metrics and literal gate arithmetic

**Create:** `memory_ablation_metrics.py`, `tests/test_memory_ablation_metrics.py`.

**Interfaces:** `score_variant(reference,prediction,periods,observed) -> bounded dict`; `summarize_cases(case_receipts) -> bounded dict` using fixed cohort/roles and exactly30 cases, two variants. The scoring entry is one complete variant evaluation; helpers may compute the components without becoming extra candidate variants. Gate decisions are `pass`, `fail` or `unresolved`, with non-applicable short support explicit.

- [ ] Write RED tests with literal H/A/D/X/period sequences: confusion, five-IoU spell pooling, all-D/all-X conventions, destination/pair boundary matching within runs, <=25-frame reference spells and greedy matched flags, known/observed/missing strata. Expected integer counts and pooled F1 are independent literal values.
- [ ] Write exact gate tests: 10/2/1 equal-provider primary weighting, fitting-overlap exclusion, gain exactly1e-6 fails, permissible-loss edges with slack, provider loss hidden by mean, one bad masked/match/D group, SC cannot measure D recall, short n0/n19/n20 behavior, absent required support unresolved and both-owner prediction collapse.
- [ ] Implement only prespecified metrics/means/thresholds with no tuning or oracle arrays. Run GREEN; commit `feat: score and gate the fixed memory ablation study`.

### Task 4: Prospective freezes, input/model schemas and global budgets

**Create:** `memory_ablation_protocol.py`, `memory_ablation_run.py`, `tests/test_memory_ablation_protocol.py`; precise .gitignore exceptions.

**Interfaces:** `AblationSession(run_id,root=ROOT)` with `freeze()`, `fit()`, `seal()`, `evaluate()`, `summarize()`, `verify()`. CLI mirrors names. Fit launches the pinned training interpreter; evaluate launches existing scoring runtime. Preserve mode/runtime boundaries explicitly. Private `experiment-owner.json`/exclusive claims are rooted in a fixed experiment identity independent of run ID; at most one real generation and its bounded attempts. Fixture roots inject synthetic acquisition only.

- [ ] Write RED synthetic lifecycle tests for source/dependency/mask/input/model/environment inventory, exact cohort/roles, linked paths and no-clobber, concurrent/global ownership, second-run budget reuse, interruption/consumed claims, corrupt persisted artifacts/receipts, omitted/extra variants/cases, coordinate-bearing hash keys, shadow/Boolean summaries, and verify patched so any feature/fit/inference/score entry fails the test.
- [ ] Bind training caches to retained metadata/provenance/raw identities and current container hashes; bind evaluation inputs against retained scientific seals. Enumerate only fixed files, not interchangeable globs. Reuse prior protected release/model/document checks. Include the approved design/plan, lock, all local Python dependencies and owning historical receipts in source/protocol closure.
- [ ] Implement freeze-before-fit, control gate, two-fit budget, model seal-before-eval, sixty case/variant claims, canonical persisted-byte promotion and private semantic/container hashes. Hash/load existing references only where allowed; disclose cache adapter parsing. Reconcile owning control baselines before accepting candidate results. Support an honestly stopped control reconstruction with no candidate/evaluation rather than inventing complete outputs.
- [ ] Implement deep owned schemas for aggregate receipts and a distinct strict portable-model schema (arrays are models, never arbitrary report arrays). `verify` checks exact inventory/hashes/order/bindings and derives summary arithmetic only; no feature construction/fitting/inference/scoring. Preserve old WCSF logs and every historical lineage.
- [ ] Run GREEN for all new modules, targeted old evidence/release guards and explicit pinned training suite. Commit `feat: enforce prospective memory ablation execution budgets`.

### Task 5: Execute the fixed experiment and report

**Create:** exact frozen/model/case/summary/verification receipts, `docs/control-memory-ablation-results.md`, `docs/control-memory-ablation-review.md`.

- [ ] Capture preservation hashes for all base files, original scientific logs/seals and selected CSV generations without reading their labels as evidence. Confirm working tree, interpreter lock and expected sources. Freeze a new generation before real feature preparation/fitting; commit the prospective freeze.
- [ ] Run fit once: at most two estimator entries, control digest/portable parity before candidate entry. Seal only after validated completion. Stop on mismatch; report stopped status and consumed count without changing recipe or rerunning.
- [ ] If paired fit succeeds, evaluate all30 predeclared cases/two methods exactly once, preserving private semantic prediction/support/mask hashes and aggregate receipts. Stop on baseline/source/mask/period/index/egress mismatch; never exclude a case or change a threshold. Summarize prespecified gates and inspect each provider/match/regime, fitting-overlap secondary results, short/D/worst-group behavior and every unknown support.
- [ ] Run current read-only verify and preservation checks; no extra scientific computation. Write findings that distinguish candidate effect from generalization, physical truth and future promotion. A failing candidate is a valid result; no new feature family is attempted in this goal.
- [ ] Request one fresh-context whole-branch review on the most capable available allowed model, with source/spec/plan/ledger and bounded outcomes; no private arrays or extra fits/scores. Re-grade findings by effects. Make one material RED-to-GREEN fix pass, no re-review. If a finding invalidates scientific results after budgets are consumed, preserve them and request a protocol amendment before additional real attempts; do not conceal it.
- [ ] Run the final complete main-runtime suite once after final code changes, native Windows link permissions, TEMP/TMP in local.tmp, FOOTBALL_STANDALONE and existing code-only FOOTBALL_OFFICIAL_CODE. Run explicit pinned training tests after code fixes. Preserve logs/skips, review record and every Ruling/deferred minor; no cleanup deletion.
- [ ] Audit every deliverable/gate against current evidence. Commit and publish the explicitly authorized draft PR, base the diagnostic branch at b5878dd, authenticate live as The-leonjr/277591257, verify complete remote blob/author parity, attach PR to chat and preserve main/PRs1–4. Report scientific outcome, test evidence, exact counts, limitations, rulings/minors and elapsed active time.

## Pre-flight and self-review

Task1 produces immutable float32 input matrices and mode-specific inference; Task2 uses the same transform; Task3 receives codes/periods only; Task4 orchestrates identities/claims around those interfaces; Task5 consumes validated sealed artifacts. Training/evaluation mask functions remain explicitly different. Model JSON arrays are validated separately from aggregate egress. The stopped-reconstruction path is part of scope, not a substitute silently declared after failure.

All spec sections map to Tasks1–5. Every Review Focus failure has named tests. User approval covers implementation and a new draft PR; the preserved native inline execution method is used. This plan translates the approved design without adding a new intervention or requiring another review of the same authorization.
