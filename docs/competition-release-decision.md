# Frozen-control release decision — 9 November 2026

Status: **candidate under verification**, unchanged `w0-c32-neutral-missing`. No model promotion, merge or submission has occurred. Default main remains older; PR1 is open and PR2 draft. Use the exact release branch/revision rather than assuming main includes this entry point.

| Gate | Evidence/status |
|---|---|
| Selected-path parity | Complete synthetic arrays and exact CSV bytes match the preserved incumbent. |
| Standalone/build | 13 selected modules; isolated `-I -S` inference; deterministic builds; no research receipts, unused model files or third-party inference dependencies. |
| Output protection | New-directory exclusive claim, input mutation check, incomplete marker, validation before completion, race/hardlink/junction tests. |
| Full-index synthetic contract | Passed on a generated 199319-row fixture, including original-index/structural endpoints and the unchanged official validator. [Receipt](../reports/competition-release/contract.json). |
| Whole-change review / suite | One fresh review found five Important guard issues; one RED→GREEN fix pass addressed them and a coherent-build-snapshot issue. Final suite: 489 total, 19 environment skips, 470 executed; all 27 new release tests execute. [Review/fix record](competition-release-review.md). |
| Two real raw-to-identical-file runs | Pending; no target access in implementation so far. |
| Exact selected-file official validation | Pending. |
| One frozen public-window correctness check | Pending; no tuning/comparison permitted. |
| Technical packet / team logistics | [Technical document](competition-technical.md) drafted; registered team name/form logistics unverified. |

Packaging does not increase predictive quality. The earlier subjective 45/100 readiness grade is not accuracy; this record replaces an arbitrary regrade with specific achieved/pending delivery gates. The hidden full-match score remains unmeasured.

Executable revision and final artifact/CSV hashes will be recorded after all required gates. Existing scientific freezes and approved ownership documents are preserved. [Implementation design](superpowers/specs/2026-11-09-deterministic-competition-release-design.md), [plan](superpowers/plans/2026-11-09-deterministic-competition-release.md), [performance history and next work](performance-history-and-next-step.md).
