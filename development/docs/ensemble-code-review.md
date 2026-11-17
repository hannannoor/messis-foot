# Ensemble code review and disposition

7 November2026. The existing reviewer inspected this distinct additive feature read-only, without raw inputs/reference caches, media, GT or per-frame outputs. Four original synthetic tests passed; an exhaustive512-combination check preserved baseline labels/structural unknowns. All frozen34 and previously published Python sources matched. No critical findings were reported.

The important finding was accepted: a generic unknown-reference counter inherited an H/A-only metric and omitted D fallback assignments. The new driver counts H/A/D separately and retains the original frozen metric source unchanged. The synthetic `[H,X]` reference with an X→D prediction now reports one unmeasured D, without claiming correctness.

Two findings labelled minor were regraded important by user-facing effect. An incomplete receipt could silently omit comparisons from a supposedly complete summary, so exact variant/field membership is now required. An inconsistent caller could make the supported rule exceed the unsupported agreement set, so explicit temporal/supported/raw agreement is now enforced. Three regressions failed before this fix pass and passed afterward; seven ensemble tests pass.

The original15 reports and prediction files were preserved. Receipt refresh verifies unchanged prior source/input identities and prediction hashes, re-executes the strengthened rule on every saved row, and requires exact output equality. Missing counts are calculated from unchanged external reference arrays. New report-generation identity and original prediction-generation identity are both recorded. Measured metrics remain exactly equal to the pre-review reports. This avoids presenting a metadata/count correction as a new trained-model result.

The author ran the full273-test suite with5 skips. Declined scopes remain explicit: reviewer did not inspect data, execute/validate external model accuracy, certify remote uploads or non-source artifacts, or re-review the earlier confidence-bound code. The parent separately verifies cohort completeness, receipt hashes, preserved sources and publication content. No repeated review cycle was requested.
