# Deterministic frozen-control competition release — design

9 November 2026. **Planning document; implementation and challenge checks have not run.** This is a new release lineage for the existing `w0-c32-neutral-missing` control, not a new predictor. It follows the supplied continuation handoff and the official assessment. Engineering choices below are the planner's decisions, not invented user approvals.

## Intent and verified starting point

Make the selected method straightforward for organisers to run and prove that the repository regenerates the exact submitted CSV. Preserve the research history and its limits. The external WCSF result remains spell F1 .505216426 / accuracy 70.951699%; no challenge correctness result is available.

The current research branch is `codex/cadence-baselines-2026-11-08` at `aaa5ba8f938545f77d8e2cb084bea561ef09c680`. A fresh remote tree check matched all 443 tracked blobs to the local `wcsf-work` bytes. There are no changes since the handoff. PR1 is open; PR2 is draft; both are unmerged. The repository is public and default `main` remains `3a1c860`. These workspace copies are not Git checkouts. [Current state receipt](../../../reports/release-planning-2026-11-09/state-check.json).

The competition still points to `f8f2629ff1e0985f81d7e59d8413678514ee1530`. All six requested documentation/scorer files were fetched and read at that revision; there is no revision delta. The submission deadline remains 17 November 2026, with no specified closing time/timezone. [Official submission requirements](https://github.com/metrica-sports/more-than-a-hack-2027/blob/f8f2629ff1e0985f81d7e59d8413678514ee1530/SUBMISSION.md).

## Approaches and scope decision

1. **Build a dedicated standalone artifact from exact selected source modules.** A small new runtime runs the frozen path and an explicit builder embeds its source closure. It removes runtime dependence on research receipts, unused models, controls and old command routing. This is the planner's selected approach under the handoff's delegated planning scope.
2. Extend `football_pipeline.py` and its existing builder. This adds another route to a bundle containing legacy camera/default behavior and broad research dependencies; it also risks changing an artifact that must be preserved. Reject for this bounded goal.
3. Wrap `ball_gap_candidate.py`. Cheapest initially, but it retains evidence-file checks and four unused comparator predictions. It does not resolve the identified release problem. Reject.

The dedicated artifact is `competition_release.py`. The existing `football_pipeline.py`, builders, selected artifacts, predictors, research results, freezes and approved ownership documents remain byte-identical. A change to any selected label is a release-parity failure; it cannot be accepted as an improvement in this goal.

## Goals, non-goals and failure conditions

- One standard-library inference command, one selected CSV, one bounded receipt; a deterministic builder and explicit runtime version.
- Exact selected-path parity on synthetic fixtures, original tactical indexing, deterministic semantic identity, and exact CSV bytes across clean raw-input runs.
- Explicit local-only target handling, followed by one frozen public-window correctness/alignment check. That check is never a comparison or selection exercise.
- An exact release revision, clear reproduction instructions and a short technical Markdown packet. A branch URL is acceptable for this candidate; no silent merge or default-branch change.
- No refitting, threshold/cost changes, cadence repair, team symmetrization, new reference acquisition, broad grid, extra WCSF scoring or retrospective strengthening of old seals.
- Failure conditions: labels diverge from the control; a required runtime import needs research evidence or an unused model; partial/overwritten output is described as complete; public-window outcomes influence method settings; protected data enters tools/chat/GitHub.

## Frozen behavior contract

Use the original 31-node tactical tree, whose canonical model digest is `363c45c70838b398cd87aee7474d7e281fd392f059a31b85712e312058aaab4d`. Preserve `feature_rows`, float32 tree comparisons, emission floor `1e-6`, motion weight `0.0`, switch cost `32.0`, predecessor/final tie order H,A,D, missing-ball neutral emissions and wholly unsupported-segment latent X.

Preserve the exact geometry path: `read_epts_contract` -> `iter_records` -> `quality_mask` -> invalid-geometry replacement -> `associate_anonymous` -> `feature_rows`/`PortableTree` -> `decode_ball_gap` -> `materialize_abstentions`. Retain anonymous association, including invalid-frame clearing, although verified IDs are not selected features. No reference mask segments inference.

Keep 25 Hz, original ATD registers 1..199319 mapped to output frames 0..199318, metadata pitch 105x68 and existing conversion to 105.3x68 metres. Preserve structural inclusive periods `(1,11185,90651)` and `(2,110808,190197)`. Period-zero labels remain X. Do not invoke `apply_published_dead`, tags, restarts, broadcast/video processing or the unused temporal head. Entirely unsupported active blocks still materialize as D by convention, not observed stoppage evidence.

## File boundaries and interfaces

Create `release_runtime.py` for selected ingestion, pure prediction, semantic identity and export. It imports selected modules directly; it never imports `soft_candidate`, `ball_gap_candidate`, `ball_gap_runtime`, `candidate_cli`, protocol/evidence loaders, training or metric modules.

Its public interfaces are:

```python
@dataclass(frozen=True)
class ReleasePrediction:
    latent: tuple[str, ...]
    labels: tuple[str, ...]
    counts: dict[str, int]

def load_source(meta: Path, raw: Path, quality: Path, *, scope: str = 'tactical') -> tuple[list[MotionFrame], dict]: ...
def predict_selected(frames: Sequence[MotionFrame]) -> ReleasePrediction: ...
def semantic_sha256(frames: Sequence[MotionFrame]) -> str: ...
def submission_bytes(labels: Sequence[str]) -> bytes: ...
def run_source(meta: Path, raw: Path, quality: Path, directory: Path, *, scope: str = 'tactical') -> dict: ...
def main(argv: Sequence[str] | None = None) -> int: ...
```

`load_source` accepts `synthetic` only through the Python API for short test fixtures; the public CLI always requires the tactical row count. `predict_selected` rejects tag/restart/dead hint fields, validates model identity and delegates to the frozen helpers. Its input contains no reference labels or reference support. Counts include neutral rows, unsupported segments/rows and materialized rows; do not import the research carry report just to count them.

Create `build_competition_release.py`, with `build_release(root: Path) -> bytes`, to generate the standalone bytes without executing the selected sources. An explicit source map embeds `release_runtime`, `ball_gap_policy`, `gap_solver` and these ten package modules: `core`, `io`, `motion`, `input_contract`, `anonymous_motion`, `tactical`, `tactical_model`, `temporal`, `soft_sequence`, `materialization_control`. Include their exact UTF-8 source in a private import loader; use standard `importlib` module registration so dataclasses and relative imports work. Deferred imports in unused historical helper functions are not exposed as commands and must never execute. The artifact executes only `release_runtime.main`.

This retains some unused helper definitions inside immutable source modules, but no unused research files, external model artifacts or evidence are required to run. Do not manually extract or rewrite the frozen functions to shrink the bundle.

Create `release/manifest.json` with source-path/SHA-256 mapping, source-base commit, policy/model identity, builder version, reference runtime and CSV/semantic schemas. The builder embeds the manifest; runtime checks embedded source hashes and model identity before inference. The manifest does not contain its own hash or the generated artifact's hash. Build verification and run receipts compute those externally, avoiding circular identities.

Create focused tests `tests/test_release_runtime.py`, `tests/test_release_export.py`, `tests/test_release_bundle.py`, `tests/test_release_contract.py`; use `tests/release_fixtures.py` for explicitly synthetic cases. Create `docs/competition-release.md`, `docs/competition-technical.md`, `docs/competition-release-decision.md` and a local handling record under `.superpowers/release/`. Amend only README's leading current-release instructions and precise `.gitignore` exceptions for safe new manifests/receipts. Existing historical documents are preserved.

## Determinism and output protocol

The reference environment is **CPython 3.14.5, Windows x64**, observed in this workspace. Inference requires no pip packages. Broader platforms/versions are not certified until exercised; document this scope. The separate official validator/check environment pins NumPy 2.5.1 and pandas 3.0.5, which are already installed here. Do not install another environment during planning.

`semantic_sha256` hashes UTF-8 bytes beginning with `release-input-v1\n`, followed by one JSON line per fully prepared `MotionFrame`: `dataclasses.asdict`, sorted keys, compact separators, `allow_nan=False`, and LF terminator. No path, UUID, timestamp, cache container hash or reference field is added. The canonical labels digest is SHA-256 of the ASCII concatenation of all final labels. Hashes are identities, not independent correctness evidence.

`submission_bytes` uses UTF-8 without BOM, exact header `frame,label`, CRLF after every line including the last, sequential decimal indices, uppercase H/A/D/X and no extra columns. CRLF deliberately matches the historical candidate's default `csv.writer` bytes. The official contract accepts CRLF. Do not rewrite a preserved CSV to make a comparison pass.

Output must be a **new, nonexistent directory**, not an existing empty directory. Reject linked/reparse ancestors and input aliases. Claim it with exclusive `mkdir`; an existing path always fails. Create an exclusive `.incomplete` marker, then `submission.csv` with binary exclusive creation. Verify pre/post input hashes before exclusively writing `release-receipt.json`. Remove `.incomplete` only after successful validation and receipt write. On failure/crash retain the incomplete directory; retries require a new directory. This is an exclusive completion protocol, not a claim of atomic directory publication. A consumer accepts a generation only with a valid receipt, matching hashes and no marker.

The deterministic receipt contains only schema/release/model/source identities, raw-input hashes keyed metadata/tracking/homography, semantic/label/CSV hashes, row count, label counts and bounded policy counts. No absolute paths, times, coordinates, arrays, event locations, target score or reference labels. Operational logs remain private. CLI stdout is limited to status, policy ID, row count and CSV hash; structural errors are sanitized and must not echo raw input rows.

## Verification gates

1. Characterize selected behavior with the incumbent research route on synthetic data only. Assert complete label arrays and CSV bytes against the new runtime, including H/A/D, neutral gaps, invalid geometry, period resets, all-unsupported blocks and deterministic ties. Add an independent float32 threshold/decoder/carry expectation so agreement is not the sole oracle.
2. Isolated standalone tests copy only the artifact into a clean directory and run Python `-I -S`, including a different current directory. It must require no repository, research receipts, model directory, NumPy or pandas. Repeated builds are byte-identical and changing an unrelated research receipt cannot affect artifact bytes or inference. Modifying selected source must change its manifest/build identity.
3. One fully synthetic 199319-row tactical fixture tests all endpoints and period boundaries. The exact generated CSV passes the pinned unchanged official format validator; malformed index/count/label fixtures are rejected. This is format/alignment-by-construction evidence only.
4. Once the code/build/fixtures pass and are reviewed, freeze source, manifest, artifact, environment and handling plan **before opening target inputs or the public reference**. Run two isolated generations directly from identical local raw inputs. Require identical semantic/label/CSV hashes and byte comparison. Validate the exact selected file. If a preserved incumbent selected target CSV exists and can be identified from its receipt without data exploration, compare locally; otherwise do not claim historical target-byte parity.
5. Run exactly one scoped public-window check of the frozen selected file using the pinned official scorer. Only the one selected CSV is in its private results directory. The scorer/reference/output files remain local; suppress the official per-event transition export from chat/publication. Report bounded aggregate metrics and the narrow purpose, with no full-match score/rank claim. No shifted-label sweep, alternate candidate or setting selection. A suspected alignment bug stops release; any repair needs a new documented lineage and explicit reassessment of public-window exposure.

For gate 3, a contract test loads only explicitly listed official code files from a locally staged evaluator: `evaluation/possession_metrics.py`, `evaluation/validate_submission.py`, `evaluation/run_evaluation.py`, `games.py` and code dependencies actually needed. It must not clone/download public GT, baseline predictions or assets as a side effect. Record exact source hashes and preserve the official licence. Public GT acquisition belongs only to gate 5.

No completed WCSF comparison is rerun. The preserved public/local verification commands may be used read-only only if a new integrity concern justifies them. Prose-only planning does not require rerunning the 462-test suite. Implementation runs the new focused tests and the required full suite once after final changes; repeat only for fixes or unresolved failures.

## Target data and release handling

The current planning phase reads source/docs only. At execution, first write a private handling record listing the exact three target input paths and hashes, new output locations outside the checkout, artifact identity, two-run reproduction purpose, and the later one-window check. Resolve known paths from existing local receipts; do not enumerate/read arbitrary challenge assets. Do not open video, tags, private GT, existing per-frame outputs for visual review, or raw challenge content through an AI tool. Local scripts consume the permitted files and print bounded aggregates/hashes only. Never commit raw inputs, derived arrays, target CSVs, public GT or per-event scorer exports.

A normal clone of the public research branch is the preferred execution workspace, under a fresh sibling directory. Use the worktree skill to verify isolation; preserve all existing source copies, bare mirror and `.superpowers` ledgers. No reset/deletion or stale fixed-parent publishing script. Before any GitHub write, verify live authentication as `The-leonjr`, numeric ID `277591257`; use the same author/committer and keep credentials out of stdout/files/argv.

Create candidate branch `codex/frozen-control-release-2026-11-09` from the freshly verified research head, or a new collision-free name if it already exists. The release decision records the exact new commit/artifact hash, candidate status, remaining gates and that `main` remains older. A draft PR against the research branch may be prepared under the inherited publication authorization, but no merge, default-branch switch, model promotion or submission-form action occurs automatically. Team name/registration/form logistics remain unverified; never invent them.

## Subsequent bounded work

Only after the release/rebuild/check gate is achieved, create the next goal: an additive D/all-state, ranking-directed diagnosis. Preserve the approved ownership design SHA `bddff762f6539b5d0966cd467ea39417f254bf3f1511ced8146f199e072122c9` and plan SHA `54e3465bba5bb822b4e6f478b484c3caf52f6f780900a3c8c42960c720fcd65a`.

That later design must attribute missed/split/merged H/A spell objects at official IoUs .3/.4/.5/.6/.7 and separate emissions, switch cost, source barriers and materialization. It uses already-used external evidence, including WCSF as development/regression evidence; no target/public-window cases. The 81.095% missed-D share of frame errors does not quantify ranking-loss contribution. It may recommend at most one justified intervention, followed by a separate freeze/release decision. No all-state implementation or intervention is authorized by merely writing this release plan.

## Acceptance and remaining builder choices

Accept only after selected parity, clean standalone execution, deterministic build/semantic/CSV identities, output protection, exact target rebuild/validation, narrowly reported public check and a concrete release decision are evidenced. The technical document explains original external training sources, assets tried/dropped, continuity/loose-ball/restart conventions, inactive-coordinate/velocity/missingness/tie limitations and exact reproduction. It must distinguish the external result from the public-window check and hidden challenge result.

The builder may choose internal helper names, fixture generation internals and import-loader implementation without changing the interfaces, artifact contract or frozen behavior. Report a blocked gate honestly; do not replace a real-file check with synthetic evidence or certify untested platforms. This design and its implementation plan are planning outputs, with execution status left explicit.
