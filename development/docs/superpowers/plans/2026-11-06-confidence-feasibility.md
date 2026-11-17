# Confidence Feasibility Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. No delegated subagents; the coordinator performs the later review.

**Goal:** Add a standard-library preflight that can prove a configured temporal confidence gate unreachable on baseline X rows.

**Architecture:** An additive pure module validates portable ensembles and policies, derives a symmetric emission range and two-message posterior ceiling, and returns only impossibility or not ruled out. A standalone CLI reads one artifact or the existing draft and its fixed 27-policy grid without importing training or reading frame/reference data.

**Tech Stack:** Python standard library, unittest; original Python 3.14 full suite and Python 3.11 isolated portability check.

**Spec:** `../../confidence-feasibility.md`; originally assigned through the contained local development brief. User subsequently requested the empirical confidence-off/direct-argmax comparison, implemented as a separate post-hoc diagnostic.

## Global Constraints

- Work only in feasibility-work; preserve all 138 copied original files byte for byte.
- No dependencies, training, retuning, challenge/reference/cache inputs, local inference, push, or subagents.
- A ceiling proves only unreachable confidence; otherwise say not ruled out.
- Frozen model, source, selector, default, and bundle stay unchanged.

## Review Focus

- Floating-point cancellation can defeat an unguarded exact-real emission bound: enclose actual score arithmetic too.
- Hard H/A anchor posterior logits need not obey the X-row emission bound: explicitly exclude anchors.
- Decoder clipping before temperature differs from output clipping after temperature.
- Boolean, nonfinite, cyclic, unreachable, half-leaf and nonintegral tree fields must reject cleanly.
- Equality and sigmoid saturation must never produce a false impossibility result.

## Task 1: Pure ceiling API

Files: create `gap_solver/temporal_feasibility.py`, `tests/test_temporal_feasibility.py`, `docs/confidence-feasibility-baseline.json` (initial hash receipt).

Interfaces: `symmetric_logit_bound(model) -> dict`; `confidence_feasibility(model, transition_cost, temperature, policy) -> dict`.

- [ ] Write synthetic score/swap, tight two-anchor, randomized decoder, clipping, weak-bound, malformed-input and published-model tests.
- [ ] Run focused unittest and observe missing-feature assertion failures before implementation.
- [ ] Implement strict validation, outward score-range arithmetic, analytic message bound, conservative numerical allowances and the two permitted outcomes.
- [ ] Run focused tests; inspect every failure and correct its root cause.

## Task 2: Artifact/grid CLI and explanation

Files: create `inspect_temporal_feasibility.py`, `docs/confidence-feasibility.md`; extend the new tests only.

Interfaces: `inspect_artifact(artifact, grid=False) -> dict`; CLI `[artifact] [--grid] [--fail-on-impossible]` outputs one JSON object, exits 0 normally, 1 on strict impossibility, 2 on malformed input.

- [ ] Write subprocess tests for artifact/grid JSON, strict exit, invalid JSON/model, independent stdlib-only execution and read-only behavior.
- [ ] Observe CLI tests fail because the tool is absent.
- [ ] Implement the artifact/grid adapter and CLI without importing training/selection modules.
- [ ] Run focused tests, isolated Python 3.11 checks and original suite; report skips/failures by name.
- [ ] Document derivation, falsification cases, numerical assumptions, usage, exact scope and limitations.
- [ ] Rehash 138 original files and record results in `docs/confidence-feasibility-progress.md`.
