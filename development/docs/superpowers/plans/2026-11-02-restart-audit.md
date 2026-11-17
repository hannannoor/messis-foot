# Restart repair and controlled comparison implementation plan

> For agentic workers: use superpowers:executing-plans inline, with TDD and one fresh final review.

Goal: execute the Council's first controlled experiment using cached alignment and local tracking, delivering the same single Python file.

Architecture: keep legacy restart behavior available only for comparison; correct soft restart precedence, separately apply the organiser-published dead interval, and compare baseline stages with fusion. Report actual opportunities and scorer-expanded changes without requiring ground truth.

Tech stack: Python standard library, existing bundled modules. Spec: the Council proposal approved in this conversation, plus DESIGN.md and TWO_CAMERA_DESIGN.md.

## Constraints
- One user-facing football_pipeline.py, same output folders, no new scan or model download.
- Preserve original frame indices and 25 fps; graded blocks remain unchanged.
- No manual competition-match labels, public-GT tuning, or cloud asset uploads.
- Known published D interval is [110808,113742); general dead-play detection remains unvalidated and is not inferred from absence or stationary proximity.
- Later replay/temporal models require separate evaluation; this controlled experiment must not silently change those gates.

## Review focus
- Strong proximity during a tagged phase remains heuristic; preserve explicit dead precedence and block bridging.
- Confirmation cannot accumulate across restart phase edges, occlusions or halves.
- Original, restart-repaired, published-context and fused effects must be isolated.
- Missing-ball opportunity counts distinguish no eligible evidence from a failed recovery algorithm.
- Scorer expansion must backfill heads, forward-fill only within graded blocks, and leave all-X blocks X.

## Tasks
1. [x] Restart semantics: RED→GREEN tests for observed control during hints, phase boundaries, legacy reproduction and dead precedence. Existing bridge veto remains.
2. [x] Published metadata: RED→GREEN exact half-open boundary/provenance tests; tactical match/fusion entry points retain raw frames for ablation.
3. [x] Controlled reporting: RED→GREEN scorer expansion, change counts, context sharing, funnel, CSV and CLI tests. --audit-baseline runs all stages on cached alignment.
4. [x] Verified routine suite and full-index integration, fresh review, embedded guide, exact source parity and isolated standalone execution. Persist the same script identity as the final writeback step.

## Ledger
- Workspace is a standalone non-git scratch project; no worktree/commits are applicable. Native execution is implied by approval to follow the audited proposal; no repeat approval needed.
- Scope is the first controlled run. Later replay inference and general possession/dead-state models must not be represented as implemented or validated by this repair.
- Tests: 96 routine tests passed, one optional full-index test skipped by default; that integration passed separately with FOOTBALL_SLOW_TESTS=1 (40.8s). It exercises actual loaders over 199319 tactical and 164488 broadcast synthetic frames without video or ground truth.
- Fresh final review: no actionable blockers. Reviewer additionally reproduced all legacy Decision fields over 1000 randomized 100-frame inputs using the prior bundled core and matched the scorer's published expansion semantics.
- Standalone integration: FOOTBALL_SLOW_TESTS=1 FOOTBALL_STANDALONE=<workspace>/football_pipeline.py python3 -m unittest discover -s tests -p test_controlled_cli.py passed (30.0s). Isolated standalone demo/help/version, no module extraction and Python 3.9 syntax checks also passed. Bundle has exact parity with all 10 source modules.
