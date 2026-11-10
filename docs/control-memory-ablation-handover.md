# Context handover — this chat only

You asked us to review the branch and prior logs, brainstorm improvements around the subjective ~49/100 readiness rating, plan with Superpowers, define tests first, and implement the agreed improvement. That rating was not treated as a measured prediction score.

## Work and reasoning

We preserved the [frozen release (draft PR3)](https://github.com/hannannoor/messis-foot/pull/3) and published the [all-state path diagnosis (draft PR4)](https://github.com/hannannoor/messis-foot/pull/4). Supported wrong-owner episodes usually had emissions favoring the wrong owner. That supported testing input evidence before lowering decoder switching cost. The association with retained memory did not establish causality.

You chose and approved one controlled experiment: neutralize only retained-owner feature columns15/16/17 to(0,0,10), in both training and inference. The other15 inputs, decoder and released predictor stay fixed. You approved implementation and a new draft PR containing code, tests, fitted portable models and bounded aggregates, without new raw/per-frame data.

Five additive modules implement the transform, matched training, metrics/gates and bounded execution/auditing. The original control was reproduced exactly before fitting one candidate. Both trees used the same228,776 selected rows, targets, weights, order and parameters; both portable exports matched sklearn on every training row.

Two preparation bugs were fixed and preserved: cross-runtime checking, then the historical training-frame interface. Neither consumed a fit/inference/score. You explicitly approved the final restart amendment. No previous owner, log, marker or freeze was deleted, and no budget was reset.

## Result: reject the ablation

| Primary spell F1 | Control | Ablation | Change |
|---|---:|---:|---:|
| Natural | .551816 | .486279 | −6.55 percentage points |
| Masked | .469149 | .427250 | −4.19 percentage points |

Exactly two fits and60 variant evaluations completed across15 already-used matches/two regimes. Thirteen fitting-disjoint matches determine the equal-provider primary; two overlap matches remain secondary. All natural provider means declined.14/26 per-case losses, two WCSF dead-state recall comparisons and19/30 short-spell safeguards failed. False-D and both-owner presence passed; no required support is unresolved.

Keep the control. Removing these three inputs wholesale hurts this comparison. This does not prove the memory mechanism is optimal, establish hidden challenge performance or justify raising the subjective rating. No next feature experiment was attempted.

## Verification and current state

One fresh-context gpt-6-astra review independently confirmed the result from bounded count tables. Six material audit issues were fixed in one failing-first test pass, without another scientific run: shared registry, strict receipts, count reconciliation, gate edges, installed-file integrity and read-only audit failures. The explicit historical audit binds the old scientific source to Git; current checks do not retroactively certify an unsaved full historical binary tree.

All49 experiment tests pass in pinned Python3.12 with zero skips. The full main suite passes565 tests with21 environment skips (544 executed), including all27 release tests. The release artifact,491 prior files, four scientific logs and four saved CSV generations retain their original bytes. Nothing is merged or promoted.

Branch: `codex/control-memory-ablation-2026-11-09`, based on diagnosis commitb5878dd. Scientific source: aa5a2f8; prospective final freeze:2209849; corrected auditor:96e168d. The original experiment budget is exhausted. Another hypothesis needs a new prospective plan and authorization.

Read-only check with the retained local stores:

```powershell
python memory_ablation_run.py audit --run-id 2026-11-09-v3 --source-commit aa5a2f8d16a42254e5b9fed1cd55a253ae8d61e8
```

[Findings](control-memory-ablation-results.md), [review and decisions](control-memory-ablation-review.md), [verification receipt](../reports/memory-ablation/verification.json).
