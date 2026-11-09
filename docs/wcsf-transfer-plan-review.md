# WCSF design builder check and plan self-review

9 November 2026. Planning only; no archive, reference outcome or model score was opened. The previous bounded source-qualification goal is published at `364e7ec097f0e6793a85d0ade76ffb4bbc379055`.

A fresh scientific-data-engineering builder checked the proposed design. Five questions needed answers before implementation:

| Question | Frozen resolution and planned check |
|---|---|
| Common reconstruction cohort and one ball coordinate | All candidates use identical finite player/ball rows and per-team support; agreeing distinct-player pairs reduce by coordinate-wise median. Task 2 tests all four hypotheses, missing-player eligibility and the reducer. |
| Exact native annotation before a missing interval | Exact native consensus takes precedence at every represented source instant; intervening missing intervals remain X. Task 3 tests 0/100/200/500 ms explicitly. |
| Geometry duplicates with conflicting reference flags | Geometry collapses identical typed keys; reference keeps every source row under an ordinal key. Reference differences cannot reject geometry. Tasks 1/3 test order-invariant conflicts. |
| Entirely ungraded half and undefined rates/deltas | Bypass old empty-half rejection. Explicit TP/FP/FN null rules distinguish absent events from predicted-only events. Preserve named official macro convention alongside supported macro; null operands yield null deltas. Task 4 covers these cases. |
| Unbounded clock/grid expansion | Source timestamps at most 86,400,000 ms; per-half span at most 5,400,000 ms/135,001 canonical rows. Tasks 1/2 reject invalid extents before allocation. |

The author self-reviewed the complete implementation plan against the corrected design: each interface has a producing task, every listed review risk has named synthetic tests, all implementation/test/schema work precedes the only real acquisition/audit task, and whole-match scores pool both periods rather than averaging half F1s. Actual archive schema, geometry, label fidelity and model performance cannot be verified by a design review; execution must qualify them or stop.

The planner explicitly amends the roadmap to prioritize this conditional provider-transfer measurement before C, based on the new primary owner evidence. The user authorized sequential planning/execution; the thresholds and order are planner decisions, not separately approved user selections. The earlier approved C design and plan retain their original hashes. No C1 promotion, fit, source-specific tuning or target access is introduced.

The plan uses native inline implementation and one fresh-context final review. The existing Windows isolated exact-byte copy fallback is retained if native worktrees are unavailable. Source/hash checkpoints and receipts must be preserved; deleting them would destroy recovery evidence. No repeated code suite is warranted for this documentation-only checkpoint.
