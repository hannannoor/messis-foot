# Frozen-control release decision — 9 November 2026

Status: **verified frozen release candidate**, unchanged `w0-c32-neutral-missing`. No model promotion, merge or submission has occurred. Default main remains older; PR1 is open and PR2 draft. Integration decision: keep this on `codex/frozen-control-release-2026-11-09` for draft review against the current research branch, without merging or changing defaults.

Executable code checkpoint: `0a6b92f8829622a71912c9f353a1cbc772da3f56`. Later documentation/receipt commits preserve the same executable bytes. Standalone SHA-256: `e8d35e15be9524270bed82352791dc2849087b49b4c2b59c191023954b19eddb`.

| Gate | Evidence/status |
|---|---|
| Selected-path parity | Complete synthetic arrays and exact CSV bytes match the preserved incumbent. |
| Standalone/build | 13 selected modules; isolated `-I -S` inference; deterministic builds; no research receipts, unused model files or third-party inference dependencies. |
| Output protection | New-directory exclusive claim, input mutation check, incomplete marker, validation before completion, race/hardlink/junction tests. |
| Full-index synthetic contract | Passed on a generated 199319-row fixture, including original-index/structural endpoints and the unchanged official validator. [Receipt](../reports/competition-release/contract.json). |
| Whole-change review / suite | One fresh review found five Important guard issues; one RED→GREEN fix pass addressed them and a coherent-build-snapshot issue. Final suite: 489 total, 19 environment skips, 470 executed; all 27 new release tests execute. [Review/fix record](competition-release-review.md). |
| Two real raw-to-identical-file runs | Passed: two clean raw-input generations produce identical semantic/label/CSV hashes and byte-identical files. Both also match the two preserved historical selected CSVs. [Reproduction](../reports/competition-release/reproduction.json). |
| Exact selected-file official validation | Passed with the unchanged pinned validator on the exact 199319-row file; hashes verified before/after. |
| One frozen public-window correctness check | Completed once, one candidate: 7500 graded frames, 17 reference/23 predicted spells, spell F1 .3800, macro F1 .494200, accuracy 66.8%. No tuning/selection or time-shift search. [Scoped receipt](../reports/competition-release/public-window-check.json). |
| Technical packet / team logistics | [Technical document](competition-technical.md) drafted; registered team name/form logistics unverified. |

Packaging does not increase predictive quality. The earlier subjective 45/100 readiness grade is not accuracy; this record replaces an arbitrary regrade with specific achieved/pending delivery gates. The hidden full-match score remains unmeasured.

Selected CSV SHA-256: `4074cc046500e3d54668a81baf5e46f6d90aeb40a0a247fcefbfa8ee1bd226a5`. The file and all raw/reference/per-event outputs stay private. Only bounded receipts are published. The one public check has narrow support and is not a hidden-match score/rank estimate or a reason to choose a different candidate.

All 443 original blobs were checked; only the planned README and precise .gitignore additions differ. Original scientific results and both approved ownership documents retain their exact hashes. [Preservation receipt](../reports/competition-release/preservation.json). No WCSF comparison was repeated. [Implementation design](superpowers/specs/2026-11-09-deterministic-competition-release-design.md), [plan](superpowers/plans/2026-11-09-deterministic-competition-release.md), [performance history and next work](performance-history-and-next-step.md).
