# Post-audit design builder check

8 November 2026. One fresh independent engineering reviewer read the roadmap and both plans. No experiment or product code ran during the check.

## Important question raised

Task 3 originally instructed freezing and running the external cases before Task 4 implemented diagnostics and decision gates. Following that order would change source after freeze, require rewriting immutable receipts, or exceed the declared scoring budget. The reviewer requested that Task 3 stop after synthetic verification and the complete metric/schema implementation precede the single external run.

## Resolution

Accepted as a technical ordering defect. Task 3 now implements and verifies inference/provenance on synthetic fixtures only. Task 4 completes and synthetically tests diagnostics, acceptance rules and the final receipt schema. Task 5 freezes every consumed source, input and rule together, then executes the sole 20-case/200-scoring external run. Reports cannot be retroactively extended by rewriting the original receipts. No user preference was needed to settle this correctness requirement.

Planner self-review also made period/reset behavior explicit, and separated a 1e-9 s duration arithmetic tolerance from exact model-acceptance comparisons. The prior approved whole-path design and plan remain unchanged.
