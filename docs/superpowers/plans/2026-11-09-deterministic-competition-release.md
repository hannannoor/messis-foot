# Deterministic Frozen-Control Competition Release Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. These are future tasks, not completed implementation.

**Goal:** Release the unchanged `w0-c32-neutral-missing` control as one reproducible artifact, demonstrate exact final-file regeneration, and perform one frozen public-window correctness check.

**Architecture:** A new selected-only runtime reuses the immutable geometry/tree/decoder/materialization sources directly. A deterministic builder embeds an explicit source closure and manifest into `competition_release.py`. Private raw-input runs and the official evaluator are separate from inference and publish only bounded receipts.

**Tech Stack:** CPython 3.14.5 Windows x64, standard library for inference/build/tests, unittest; separate existing official-check environment NumPy 2.5.1 and pandas 3.0.5. No training, new runtime package or model download.

**Spec:** `docs/superpowers/specs/2026-11-09-deterministic-competition-release-design.md`. Written under the handoff's delegated planning scope; one fresh builder check returned “nothing important left.” This does not assert a human has approved an unseen design or that any execution gate has passed.

## Global Constraints

- Source base: `aaa5ba8f938545f77d8e2cb084bea561ef09c680`; refresh remote head before execution and reconcile drift rather than silently switching sources.
- Original model digest: `363c45c70838b398cd87aee7474d7e281fd392f059a31b85712e312058aaab4d`; motion weight `0.0`, switch cost `32.0`, emission floor `1e-6`, tie order H,A,D.
- Preserve `feature_rows`, float32 tree comparisons, geometry/association, eligibility, neutral gaps, unsupported latent X and original materialization. No label change is accepted as an improvement here.
- Keep 25 Hz, output 199319 rows indexed 0..199318, canonical pitch 105.3x68, inclusive structural periods `(1,11185,90651)` and `(2,110808,190197)`, period-zero X. No fixed pre-kickoff D shortcut.
- CSV is UTF-8 without BOM, header `frame,label`, uppercase H/A/D/X, CRLF including the last row. This matches historical candidate bytes.
- Output requires a new nonexistent directory and exclusive completion protocol; incomplete outputs are preserved and cannot be reused.
- Never modify any of the 443 starting tracked blobs except a leading README current-release pointer and precise `.gitignore` additions. No editing historical results, source manifests, freezes, candidate sources or approved ownership documents.
- No challenge assets, raw/reference/prediction arrays, event locations or reconstruction-capable derivatives in tool output/chat/GitHub. No target data access until Task 5's private handling freeze. Public GT access belongs only to Task 5's final check.
- No extra WCSF inference/scoring, new dataset acquisition, refit, grid, owner messages or public-window model selection. WCSF remains used evidence.
- Official code is pinned to `f8f2629ff1e0985f81d7e59d8413678514ee1530`. No official scorer modification to obtain a favorable result.
- GitHub writes require live verified `The-leonjr` / `277591257`, matching author/committer and credentials kept out of stdout/files/argv. No merge, default-branch change or submission-form action.

## Review Focus

1. Invalid-geometry and missing-ball frames: preserve the incumbent's clearing/eligibility path; missingness alone must not acquire new D semantics. Task 1 pins complete latent/final arrays.
2. Float32 thresholds, neutral ties and period resets: preserve exact tree and decoder choices; no cross-half carry. Task 1 adds independent small expected-output tests.
3. Existing paths, input aliases, races and interrupted writes: preserve user files and identify incomplete generations. Task 2 tests exclusive claim and completion.
4. Clean artifact outside the checkout: deferred research imports must never run; unrelated receipt edits cannot break or change inference. Task 3 tests isolated `-I -S` execution and build identity.
5. Full tactical index versus short/public data: the CLI must reject short inputs, the exact selected CSV must validate, and the public check must be frozen and single-candidate. Tasks 4 and 5 test/gate these separately.

## Execution layout and status

Proposed method: implement sequentially in this chat using `superpowers:executing-plans`, then one fresh whole-change review. This is a planner recommendation; do not record it as a user-selected execution method. Keep one bounded active implementation goal. The later all-state diagnosis is a new goal only after this one succeeds.

The current `wcsf-work` is a byte-verified source copy, not Git. At execution use `superpowers:using-git-worktrees` to create/verify a clean normal clone of the public research branch in a new sibling `competition-release-work`; prefer an ordinary isolated branch if native worktree setup rejects this non-Git root. Never reuse/reset the older bare mirror. Copy only the two planning Markdown files and safe state receipt into the checkout, not entire scratch/ledger folders.

- [ ] Refresh the four branch heads, both PRs and the official head; if unchanged, record the same pins. If changed, inspect only the delta before updating this plan.
- [ ] Verify checkout HEAD/clean state and all original tracked blob identities; preserve the existing copies/ledgers. Create `codex/frozen-control-release-2026-11-09` or a collision-free new name without overwriting an existing branch.
- [ ] Create a local implementation checklist/goal from Tasks 1–5 only when execution begins. Retain the planning receipt and original 443-path baseline for the final preservation check.

### Task 1: Selected-only ingestion and frozen prediction

**Files:**
- Create: `release_runtime.py`, `tests/release_fixtures.py`, `tests/test_release_runtime.py`.
- Read unchanged: `ball_gap_policy.py`, `gap_solver/input_contract.py`, `anonymous_motion.py`, `tactical.py`, `tactical_model.py`, `soft_sequence.py`, `materialization_control.py`, `tests/test_ball_gap_candidate.py` and `tests/test_input_contract.py`.

**Interfaces:**
- Consumes: existing `MotionFrame`, `read_epts_contract(path)`, `iter_records(contract,path,blocks=None)`, `quality_mask(path,rows)`, `associate_anonymous(frames)`, `PortableTree(model).predict(row)`, `feature_rows(frames)`, `sequence_usable(frame)`, `decode_ball_gap(supports,periods,usable,observed)`, `materialize_abstentions(labels,periods)`.
- Produces: `ReleasePrediction(latent: tuple[str,...], labels: tuple[str,...], counts: dict[str,int])`; `load_source(meta: Path, raw: Path, quality: Path, *, scope: str='tactical') -> tuple[list[MotionFrame],dict]`; `predict_selected(frames: Sequence[MotionFrame]) -> ReleasePrediction`; `semantic_sha256(frames: Sequence[MotionFrame]) -> str`.
- Produces synthetic helpers: `release_fixture(root: Path, case: str) -> tuple[Path,Path,Path]` for named short cases, and `tactical_fixture(root: Path) -> tuple[Path,Path,Path]` for Task 4's full-index case. Short fixtures use the existing positive-fixture register structure, not target-derived values.

- [ ] **Step 1: Write synthetic parity and independent-behavior tests.** `test_selected_runtime_matches_incumbent_complete_arrays` runs `ball_gap_candidate.run_source(...,scope='synthetic')` only on generated cases, then compares every final label with `predict_selected(load_source(...,scope='synthetic')[0]).labels`. Cases: positive H/A/D with 100-row neutral gap; invalid homography interval; wholly unsupported block; separate periods with period-zero interruption. Obtain incumbent latent labels locally from its exact unchanged helper chain, not from final CSV carry guesses. No new model selection.

```python
self.assertEqual(new.labels, tuple(old_labels))
self.assertEqual(new.latent, tuple(old_latent))
self.assertEqual(len(new.labels), len(frames))
self.assertEqual(set(new.labels) - set('HADX'), set())
```

`test_float32_branch_semantics` constructs a valid two-leaf toy tree at a float64 threshold whose nearby input rounds to float32; assert the same stored-threshold branch as the current `PortableTree`. `test_neutral_tie_order_and_period_reset` checks tied usable emissions select H, unsupported segments stay latent X, all-unsupported active materialization is D, period-zero remains X and one half never supplies the other's carry. `test_reference_hints_rejected` adds each of tag_team/restart_hint/dead_evidence/dead_source and expects rejection.

- [ ] **Step 2: Run RED.** From the execution checkout: `python -m unittest discover -s tests -p test_release_runtime.py -v`. Expected failure is missing new runtime interfaces; the incumbent synthetic setup must itself succeed. Preserve a bounded test log, not per-frame output.
- [ ] **Step 3: Implement ingestion/prediction/identity.** Use precisely the frozen chain and source schema in the spec. Validate the model digest with canonical sorted compact JSON and `allow_nan=False`. The input audit contains raw hashes/row/schema and bounded counts only. Semantic hashing begins `release-input-v1\n`, then sorted compact JSON `dataclasses.asdict(frame)` plus LF per prepared frame. Do not call `audit_source` just to perform a second unused research pass or load an external temporal artifact.
- [ ] **Step 4: Run GREEN plus existing relevant guard tests.** Run the new module, then `python -m unittest discover -s tests -p test_ball_gap_policy.py -v` and `python -m unittest discover -s tests -p test_input_contract.py -v`. All must pass; array differences stop the task.
- [ ] **Step 5: Commit only the three new files.** Message: `feat: add frozen selected-only release runtime`.

### Task 2: Exact export and protected output generations

**Files:**
- Modify: `release_runtime.py`.
- Create: `tests/test_release_export.py`.

**Interfaces:**
- Consumes: Task 1 ingestion, prediction and semantic digest.
- Produces: `submission_bytes(labels: Sequence[str]) -> bytes`; `run_source(meta: Path,raw: Path,quality: Path,directory: Path,*,scope: str='tactical') -> dict`; `main(argv: Sequence[str] | None=None) -> int`.
- CLI: `python competition_release.py --prefix <local-prefix> --out <new-directory>` plus `--version`/`--help`; no tuning/model/reference/video switches and no public synthetic flag. Source-mode main is also runnable for development.

- [ ] **Step 1: Write export tests with exact bytes and meaningful failure assertions.** `test_csv_bytes_and_incumbent_parity` includes `submission_bytes(('H','A','D','X')) == b'frame,label\r\n0,H\r\n1,A\r\n2,D\r\n3,X\r\n'` and compares a complete synthetic incumbent `submission.csv` byte-for-byte. `test_same_source_different_directories_same_hashes` requires equal semantic/label/CSV hashes and deterministic receipt bytes across two new folders; no paths/times/UUIDs may enter the receipt. `test_existing_empty_populated_and_input_aliases_preserved` rejects each path without mutation. `test_concurrent_claim_only_one_winner` uses two workers racing for the same new output. `test_mutation_and_interruption_leave_incomplete` injects an input-hash change or write failure and requires marker retained, no valid completion, no overwrites and a new directory for retry. Include output symlink/junction/hardlink aliases where supported; document a platform-permission skip, do not weaken ordinary collision tests.
- [ ] **Step 2: Run RED.** `python -m unittest discover -s tests -p test_release_export.py -v`. Expect absent exporter/runner or exact-byte mismatch, not incidental fixture errors.
- [ ] **Step 3: Implement explicit CRLF export and exclusive completion.** Prevalidate output ancestors/aliases, exclusively claim the new directory, create `.incomplete`, exclusively write CSV, check input identity again, exclusively write allowlisted deterministic `release-receipt.json`, remove marker last. `run_source` returns the receipt. Keep failed generations. The receipt's schema includes policy/model/source identity, raw/semantic/label/CSV hashes, `rows`, label counts and policy counts; never include arrays, paths, event indices or accuracy claims. In source mode derive owned-source identity from the explicit source map; the bundle will supply its embedded manifest identity. Keep that distinction explicit in the receipt.
- [ ] **Step 4: Run GREEN and Task 1 tests.** `python -m unittest discover -s tests -p 'test_release_*.py' -v`. Sanitize CLI structural errors and verify stdout exposes only status, setting, row count and CSV hash.
- [ ] **Step 5: Commit.** Message: `feat: export deterministic protected submission generations`.

### Task 3: Deterministic standalone artifact and owned manifest

**Files:**
- Create: `build_competition_release.py`, `competition_release.py` (generated), `release/manifest.json`, `tests/test_release_bundle.py`.
- Modify: precise `.gitignore` exception `!release/manifest.json` only; keep global private data exclusions.
- Read unchanged: selected source map from the spec, `build_standalone.py` as a pattern only. Never invoke the old builder or overwrite `football_pipeline.py`.

**Interfaces:**
- Consumes: Task 2 `release_runtime.main` and the explicit 13-module map (runtime, top-level ball-gap policy, package init and ten package modules).
- Produces: `build_release(root: Path) -> bytes`; `python build_competition_release.py --check` exits 0 only when generated artifact/manifest match committed bytes, and normal builder writes only its own two generated paths. A manifest helper may be internal but must sort paths, include every embedded source hash and omit circular/self/output hashes.

- [ ] **Step 1: Write bundle tests.** `test_repeated_builds_exact_and_owned_sources_pinned` asserts two calls return identical bytes, embedded source map matches the actual selected modules and manifest/settings/model pins match. `test_clean_isolated_artifact` copies only the artifact to a new directory and launches `sys.executable -I -S` from another directory: `--version`, help, full CLI failure on short input, then synthetic Python-API inference via `runpy.run_path` must work with no checkout on sys.path. `test_unrelated_research_mutation_has_no_effect` changes a copied research receipt/unused model and requires identical build bytes and successful selected inference. `test_owned_source_tamper_detected_or_new_identity` requires any selected-source edit to fail pinned validation or produce a different manifest/build identity; never reuse the old release identity. `test_missing_research_imports_never_executed` installs an import blocker for evidence/protocol/ML modules while running the synthetic selected path.
- [ ] **Step 2: Run RED.** `python -m unittest discover -s tests -p test_release_bundle.py -v`. Expected: builder/artifact absent.
- [ ] **Step 3: Implement builder/private import loader/manifest.** Read sources as exact UTF-8, sort module names, use deterministic Python literals and LF artifact text, embed manifest and verify source hashes before imports, register modules normally for dataclasses/relative imports. Execute only the new main. Runtime receipt identifies the exact executing artifact externally, without embedding that artifact's own hash into itself. Deferred historical imports outside the selected call graph are not bundled merely to make static imports exhaustive.
- [ ] **Step 4: Run GREEN.** Build twice in separate clean source copies, compare artifact bytes, run `python build_competition_release.py --check`, then all new release tests. Record actual reference interpreter; broader Python/OS support is uncertified unless separately exercised. No new package installation.
- [ ] **Step 5: Commit safe generated outputs and builder/tests.** Message: `build: package deterministic frozen-control competition artifact`.

### Task 4: Full-index contract gate and reviewable delivery packet

**Files:**
- Create: `tests/test_release_contract.py`, `docs/competition-release.md`, `docs/competition-technical.md`, `docs/competition-release-decision.md`, `requirements-release-check.txt`, `reports/competition-release/contract.json`.
- Modify: leading README release pointer; exact safe exception `!reports/competition-release/contract.json` as needed. Preserve historical README sections and all old commands/artifacts.
- Private-only: `.superpowers/release/official-code/` and `.superpowers/release/` validation logs; no GT or match files at this task.

**Interfaces:**
- Consumes: generated standalone, full-index synthetic fixture and pinned official `possession_metrics.py`, validator, runner and `games.py` code plus only their required code dependencies.
- Produces: exact validator pass on the new synthetic CSV, official code-hash receipt, explicit supported environment/reproduction command, a short technical Markdown document and candidate release decision with target gates still PENDING.

- [ ] **Step 1: Write full-index/format tests.** `test_tactical_cli_original_index_and_periods` generates 199319 rows from scratch, runs the standalone as a subprocess, checks header/frame endpoints/count, period-zero X and the first/last inclusive frame of each half, then calls the unchanged official format validator on that exact CSV. Assert CLI rejects declared 500-row input. `test_official_rejects_invalid_exports` independently changes row count, order/duplicates, blanks and label alphabet and requires validator rejection. No public reference is used.
- [ ] **Step 2: Stage official code only and run the new gate.** Fetch explicit code paths pinned in the spec/state receipt; resolve required imports (including `games.py` code dependencies) without a full clone or GT/baseline downloads. Record blob/SHA-256 identities and license. `requirements-release-check.txt` pins `numpy==2.5.1` and `pandas==3.0.5`; use the already installed environment. Run `python -m unittest discover -s tests -p test_release_contract.py -v`; a missing staged evaluator is a failed required release gate, not a silently skipped success. Tests obtain its local path from `FOOTBALL_OFFICIAL_CODE`.
- [ ] **Step 3: Write concise reproduction and technical documents.** `docs/competition-release.md` gives exact runtime, no-pip inference setup, clean builder check, command with local prefix/new output, full-index contract, completion rule and private-data handling. `docs/competition-technical.md` covers original external training sources and amounts from current provenance, assets used/tried/dropped, geometry/tree/neutral sequence/carry conventions, limitations and reproduction. Cite WCSF only as external descriptive evidence; leave target/public check pending. Do not invent registered team name or registration status. `docs/competition-release-decision.md` names this as an unchanged candidate and records all outstanding gates; older main/PRs remain explicit.
- [ ] **Step 4: Run final pre-target code verification and fresh review.** New release tests must all execute. Then, in the execution checkout, set TEMP/TMP to its writable `.tmp`, set FOOTBALL_STANDALONE to its preserved `football_pipeline.py`, FOOTBALL_OFFICIAL_CODE to staged code, and run `python -m unittest discover -s tests -p 'test_*.py'`. Compare skip reasons with the known 19 environment skips, rather than assuming a fixed new total. Invoke the applicable Superpowers review workflow for one fresh whole-change review; fix material findings and rerun affected checks. No research rescore and no target data yet.
- [ ] **Step 5: Commit the verified code/docs/safe synthetic receipt.** Message: `docs: prepare frozen-control competition delivery packet`. Record the commit/artifact/source/environment hashes in the private pre-target freeze before Task 5. Keep source/output hash reports distinct from historical scientific seals.

### Task 5: Private exact-file reproduction, one public check and release decision

**Files:**
- Private-only: `.superpowers/release/target-handling.json`, `.superpowers/release/target-freeze.json`, `.superpowers/release/reproduction.json`, fresh outputs outside the checkout, scoped evaluator/reference/reports outside the checkout.
- Update after evidence: `docs/competition-release.md`, `docs/competition-technical.md`, `docs/competition-release-decision.md`.
- Optional safe public aggregate: `reports/competition-release/reproduction.json`, explicitly allowlisted after egress review. Do not publish source filenames/paths or any target-derived arrays/event locations.

**Interfaces:**
- Consumes: reviewed frozen artifact plus the exact original three local input files; pinned official format validator and scorer. The public-window check has only one frozen selected CSV.
- Produces: two clean raw-to-file generations with matching semantic/label/CSV identities, exact selected-file validator pass, narrow one-window aggregate result, explicit candidate release status and a reproducible exact code revision.

- [ ] **Step 1: Freeze the handling plan before reading target contents.** Resolve exact metadata/tracking/homography paths from known prior aggregate receipts (the established prefix is `C:/football-data/tactical cam/BAR-ATH_tactical`, subject to local receipt verification). Record exact hashes, artifact/commit/environment identity, output locations and operations. No video, Smart Tagging, broad directory exploration, private GT or per-frame tool output. If inputs are absent, finish all unaffected release work and report the missing gate; do not fabricate a substitute.
- [ ] **Step 2: Generate two new selected outputs locally.** Run the frozen artifact twice with the same raw inputs and two newly claimed output folders, with a clean invocation each time. A local verification script consumes receipts/files and prints only `rows`, semantic/label/CSV hashes, byte-equality flags, completion state and format pass/fail. Require 199319 rows, no incomplete marker, pre/post input identity and byte-identical CSVs. Keep both original generations. These are target reproduction runs, not WCSF inference attempts.
- [ ] **Step 3: Verify incumbent preservation and validate the exact candidate.** If the known preserved `ball-gap-reviewed-run-1`/`-2` receipt identifies the corresponding selected CSV and same raw inputs, compare locally without emitting rows. A mismatch stops release. If no trustworthy preserved selected file exists, record historical byte parity as unavailable; synthetic selected-path parity and two new exact rebuilds remain separately named evidence. Do not execute another historical target route or tune settings just to fill that gap. Run the pinned official validator on the exact proposed uploaded file; record its hash before and after.
- [ ] **Step 4: Perform exactly one scoped public-window correctness check.** Acquire only the official public reference and required metadata locally after recording the frozen candidate hash. Explicitly exclude private/full-match GT and other human-derived game data. Put only this selected CSV in a new private scorer results directory, then run the unchanged pinned `run_evaluation.py --gt public --results <one-candidate-directory> --out <private-report-directory> --no-detail`. Capture stdout/reports privately; surface bounded aggregate metrics, evaluated support, source/candidate hashes and the limitation “public five-minute correctness/alignment check; no tuning or selection; no hidden full-match score.” Do not expose transition CSVs or search time shifts. Poor quality alone does not authorize adjustment. A suspected pipeline bug suspends the candidate and requires a documented new lineage/exposure decision before repair/recheck.
- [ ] **Step 5: Finalize the technical/release packet and preservation audit.** Add exact achieved/failed gate evidence and links; state public-window result separately from WCSF and full-match unknowns. Check all original 443 blobs: only the allowed README/.gitignore changes may differ. Confirm original scientific results hash, both approved C document hashes and historical candidate/source freezes remain unchanged. Inspect the intended Git diff/manifest for egress; allowlist code/docs/model metadata/synthetic tests/bounded receipts only. Never blanket-add a scratch/output directory.
- [ ] **Step 6: Publish a reviewable candidate within inherited authorization.** Verify live GitHub identity and matching author/committer, refresh expected remote head, commit the final safe docs/receipts, push the candidate branch and prepare/update a draft PR against the research branch. Verify remote commit/tree/artifact bytes after publication. The decision document names the exact executable code commit and artifact hash; a later prose-only decision commit may point to it without a circular self-reference. Do not merge PR1/PR2/new PR or change main. If publication needs a new external approval, finish the concrete local release first and report the exact blocked action/reason.
- [ ] **Step 7: Close this bounded goal only when its required gates actually pass.** Report artifact, exact revision, rebuild/validator evidence, narrow public-check result and remaining team/submission logistics. If a required target/public gate cannot run, leave it explicitly incomplete. Do not mark a release complete based on tests alone. Only after this goal is achieved begin planning the separate all-state diagnosis.

## Deferred next goal — outline only

Write a new D/all-state addendum to the preserved approved ownership documents. Attribute spell-object misses, splits and merges at official IoUs .3/.4/.5/.6/.7; distinguish emission, decoder, barriers and materialization using input-only inference segmentation. Use already-used external sources, including WCSF as development/regression evidence, and report H/A/D consequences. Allow at most one mechanism-justified intervention afterward under a separate frozen comparison. This outline does not implement the diagnostic or authorize a broad model search.

## Planning self-review

Coverage: dedicated artifact and exact selected semantics (Tasks 1–3), byte/semantic identity and output protection (Tasks 1–3), official full-index format and technical packet (Task 4), scoped target rebuild/public check/integration decision (Task 5), preservation and later diagnostic boundary (global constraints/Task 5/deferred outline). All five review-focus conditions have named tests/gates. Public interfaces are defined by their producing tasks; no scientific source or historical seal is rewritten. The plan is pending execution; no test run, model comparison, target check, clone, commit, push or merge is claimed by this planning document.
