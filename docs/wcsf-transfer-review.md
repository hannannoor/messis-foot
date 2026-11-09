# Independent WCSF review and post-run corrections

9 November 2026. One fresh-context read-only reviewer inspected the complete source/tests/spec/plan/amendment and bounded public/private evidence. It found no critical error in the headline WCSF numbers. It reconstructed the 409/424/428-file Git trees, verified the two prospective source freezes/publications, all four private input and six output hashes, exact attempts/access order, grid/provenance, official parity and actual diagnostic pooling. It independently recovered spell F1 0.505216 vs 0.384073 from 411 reference spells.

Four important findings received one test-backed fix pass; none caused a scientific rescore:

| Finding | Correction | Regression evidence |
|---|---|---|
| Fresh clone reuses committed receipts but lacks private files; original environment gates public checks | New read-only public verifier; explicit replay run ID and isolated scratch reports/private inputs with a new environment freeze | Fresh-clone CLI freeze/public verification, unchanged published receipts, absent private sibling and mismatched-environment public checks |
| Idempotent scoring marker lets concurrent callers both compute; first score event precedes reference load | Exclusive marker claim; all method-attempt events emitted at actual callback entry | Deterministic concurrent callers RED→GREEN; reference-load failure has zero method attempts; actual entered/aborted method remains counted |
| Validator admits contradictory short-spell and pooled boundary diagnostics | Check duration/total matches, every half-pooled diagnostic count and matched-count-weighted latency | Four independent in-memory contradictions RED→GREEN; original retained reports satisfy the stronger checks |
| Access log not prospectively sealed; unknown stages/duplicate JSON keys pass | Future score seal binds access log; strict complete event/protocol/time/order and attempt prefix parsing | Deleted machine event, wrong protocol, unknown stage and duplicate-key cases RED→GREEN |

The historical v2 sources remain at Git `2abd83b` and an exact local 175-file snapshot. Its original access log was not included in the prospective score seal. Its first score event was stage entry before reference loading. Current post-run verification checks the complete retained log and preserved artifact hashes, and labels those limits honestly. Future replays use the stronger guards. The prior historical verifier is not relabelled as equivalent to these new checks.

Reviewer declined annotation truth, sensor freshness, physical alignment beyond structure, population superiority, challenge score/rank, target submission validity and final publication not yet performed. Ruling: none is established here. Source/provider-transfer and numerical consistency claims remain narrow; no new challenge output or head promotion follows.

The minor draft-document finding was resolved by completing the already planned final results report: measured findings lead and historical checkpoints are dated. Full local test logs are hash-identified in preflight/post-review receipts but not delivered as remote CI. The final suite result and no-rescore artifact identities are recorded separately at completion.

Final verification: 462 total tests, 19 skips, zero failures/errors; all 56 new tests execute. Each important regression was observed RED before its fix and GREEN afterward, including deterministic duplicate scoring, false method logging on reference-load failure, all four log mutations, diagnostic contradictions, private-free public verification and fresh-clone commands. Original results/private artifacts remain hash-identical; scientific attempt counts remain 3+3. No re-review or rescore was performed.
