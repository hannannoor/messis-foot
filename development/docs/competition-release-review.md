# Frozen release review and fixes

9 November 2026. One fresh `gpt-6-astra` context reviewed the entire change at `62877ad`, using source and synthetic probes only. No target inputs, predictions or reference data were accessed. This was a fresh model context, not independent evidence from another model provider or another dataset.

The review found five Important issues: weak persisted-receipt verification, preloaded modules bypassing the embedded loader, executable bytes being identified after loading, parser exceptions echoing input-derived text, and builder writes following hardlinks/junctions. A sixth coherent-snapshot issue was initially graded Minor; the executor treated its mismatched artifact/manifest consequence as Important.

One fix pass reproduced the issues before changing code. Eight regression tests exercise altered receipts and bounded fields, preloaded runtime/dependency modules, source/artifact file changes, XML/CSV/numeric parser exceptions, hardlink/junction destinations and a concurrent source save. Each now passes. The runtime validates the exact persisted intended receipt and current release identity before completion. The builder takes one source snapshot and stages/replaces only owned files. Selected predictor sources, model, emissions, switch cost, tie order and materialization remain unchanged.

Final suite: **489 total, 19 environment skips, 470 executed, zero failures/errors; all 27 new release tests run**. The generated full-index synthetic CSV passes the pinned official validator. [Validation receipt](../reports/competition-release/validation.json), [synthetic contract](../reports/competition-release/contract.json).

The initial clone inherited Windows newline conversion for some hash-pinned Markdown/JSON files. A clean tracked diff was confirmed, local `core.autocrlf=false` was set, and only differing fresh-clone bytes were restored from Git blobs. Baseline link fixtures required native filesystem permissions. No legacy source was changed to make the baseline pass. The original restricted baseline failure log and all RED/GREEN/final logs are retained locally.

The reference environment is CPython 3.14.5 Windows x64. Cross-platform certification, deliberate adversarial filesystem replacement and machine-power-loss guarantees are not claimed. Process failures retain incomplete output generations. Task 5 real-file reproduction/public checking is a later operational gate, reported separately in the release decision; this review does not certify it in advance. No second code review or scientific rescore was performed.
