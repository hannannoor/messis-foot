# Touch evidence pre-score review

One fresh-context gpt-6-astra reviewer inspected all five new modules, synthetic tests, spec and plan at 579f467. It did not inspect per-frame match material or run scientific scoring. No freeze or scientific claim existed during review.

Critical: scoring passed string labels to the existing integer-code metric interface. Fixed by encoding H/A/D/X with the existing canonical helper; a perfect synthetic H/A/D test failed before correction and passes afterward.

Important: mutable summary/selection gates and incomplete aggregate inventory. Fixed using exclusive private phase seals over exact receipt/claim inventories and summary hashes; control/selection are recomputed before dependent phases. Tamper and missing/duplicate/extra inventory tests failed before correction and pass afterward.

Important: binary rounding could reject exact inclusive gain/ratio boundaries. Dead recall and provider spell ratios now use integer-count fractions. Inclusive gain uses four-ULP rounding treatment fixed before scoring. Exact .46→.50 and .9/1.1 ratio tests failed before correction and pass afterward.

Important: a committed freeze could name uncommitted source bytes; input checks occurred only at phase entry. Git object source hashes are now required to equal the current source and freeze; exact input inventories/hashes are checked per match before load and after computation before persistence. A missing source-identity helper test failed before implementation; input mutation/inventory tests also pass.

Important: development rejection lacked a terminal decision file. A Reject decision with zero confirmation scores is now emitted without entering confirmation; its regression test failed before implementation and passes afterward.

Minor coverage notes were addressed with a binary-exact surprise plateau and a direct assertion that jitter receives the historical masked sequence. The first plateau fixture used decimal .02 and was not numerically flat; .03125 produces a binary-exact plateau. No detector threshold or scientific parameter was altered.

All 43 targeted tests pass after this single pre-score fix pass. The reviewer was not rerun. The subsequent fixed-source full suite passed: 608 tests, 21 environment skips, 587 executed, zero failures/errors; all 43 new tests execute. Scientific results remain pending.

## Verification process correction

The first baseline command was interrupted after providing no detailed progress. A verbose diagnostic run later observed errors in historical source-hash audit tests while new Python files were being added concurrently. That run is invalid as a clean baseline and was interrupted, not called passing. An isolated unchanged WCSF test subsequently passed in 96.327 seconds. Original logs are retained under .superpowers/touch-*.log. The stable full-suite run separates the 565 original tests from the new tests and runs without source mutation. This process mistake did not consume a scientific fit, inference or score.

The restricted fixed-source run encountered an existing Windows folder-link permission failure. The isolated test passed with normal permissions, as did the complete suite. Its 565 original tests retain the recorded 21 skips and zero failures. This environment correction changed no source or scientific protocol.
