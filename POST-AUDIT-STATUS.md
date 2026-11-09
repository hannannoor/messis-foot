# Post-audit checkpoint: new-provider result

The frozen control has now completed a previously unused WCSF one-match transfer audit: **spell F1 0.505216, macro F1 0.707246, accuracy 70.9517%**. Both fixed w50 baselines score spell F1 0.384073 on that same reference. The challenge score is unmeasured. [Full results and limits](docs/wcsf-transfer-results.md), [independent review and fixes](docs/wcsf-transfer-review.md).

Missed dead frames account for 81.095% of frame mistakes; dead recall is 49.6198%, despite 99.5385% precision. There are zero predicted X rows. Official ranking uses spell objects, so diagnose liveness and handover effects on spell misses/splits/merges before selecting an intervention. No new model was fitted or promoted. WCSF is now used evidence, not a future holdout.

The earlier cadence-only velocity contrast remains rejected. [Cadence/strong-baseline results](docs/cadence-and-baselines-results.md), [verified adversarial audit](adversarial-review/VERIFIED-AUDIT-RESPONSE.md), [ownership Council](docs/ownership-council/README.md). All original 309 release files, 100 cadence-frozen sources and approved C design/plan are preserved. The dated WCSF design is an additive roadmap amendment; historical frozen documents stay intact.

The source/implementation freezes were committed before acquisition/CSV ingestion. A retained packaging failure and narrow metadata-only amendment preceded the completed audit. Post-run review fixed replay/concurrency/log/diagnostic guards without rescoring; original evidence and code at2abd remain available. Public verification checks numeric/hash-chain evidence with no private data; fresh replays use an explicit run ID. Exact raw-to-identical-challenge submission regeneration and broad full-state qualification remain outstanding.

The user additionally requested a dedicated assessment against the current official EVALUATION.md after this task. The source is pinned and the metric code matches; that assessment will determine the next diagnostic priority after this implementation/evidence goal is completed and published.

Final WCSF code verification: 462 tests, 19 skips, zero failures/errors; all 56 new tests execute. The stronger post-run checks preserve the original 3+3 scientific attempts and immutable result bytes.
