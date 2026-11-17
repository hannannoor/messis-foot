# Informed follow-up and disposition

5 November2026. After its independent initial memo was frozen, the same auditor read only the approved design and `io.py`, `tactical.py`, `motion.py`, `skillcorner.py`. It did not inspect chat history, results, challenge assets or GT. This is a separate informed phase; the initial blind recommendation remains immutable in `strategy-blind-audit-v1.md`.

## Important findings

1. Odd native10Hz samples could mark a synthetic25Hz blend as a native detection; isolated copied samples also inherited a frame-wide interpolation flag. Fix: independent ball provenance, original sample time, native/unknown distinction and native-grid availability arrays. Consecutive/isolated odd-tick tests and ATD unknown-freshness test were observed failing, then passed.
2. Phase duration/time consistency and population reconciliation were missing. Fix: cross-check against the tracking clock, quarantine contradictory annotations without fitting a shift, report requested/out-of-range/missing/conflicted/retained support. A deliberately shifted phase fixture failed before the fix. The initial real development source also exposed41 native frames of halftime conflict, now unknown.
3. Regime-mixed cache generations could share frame vectors and evade old checks. Fix: source/input identity, generation IDs embedded in both arrays, match/regime identity and content hashes, with metadata published last. Mixing an available-position feature file into a detected-position cache failed before the fix and is now rejected. Derived caches are rebuilt before any fitting.
4. Zero hidden-turnover recall could tie zero and pass a nondecrease gate. Tighten before model scores: positive incremental recovery versus two-sided filling at matched coverage, bounded additional false opposing spells, explicit support, and repetition on final evaluation. Natural-gap claims require natural support; masked support does not substitute for it.
5. Known-phase scoring can hide H/A assignments during unlabelled stoppages. Retain the explicit experimental-only local scope, report assignments outside reference support, and ensure deleting/permuting phase references cannot change inference. Structural period/quality boundaries are independent inputs; annotation holes may only affect scoring.
6. Report gap/match-weighted agreement and native counts, not only adjacent interpolated frames. Compare methods on the same population and at matched coverage. The old frozen comparator cannot infer hidden opposing possession from current player movement; it is a comparator, not evidence that the new mechanism works.
7. Masking must remove ball coordinates and all ball-derived distances/provenance BEFORE anchors, features or baseline inference are derived. Add this contract to selection tests.

## Retained limits

The ATD schema used here supplies team IDs/list order but no verified home/away role in the original adapter contract. Do not silently certify that assumption. Retain the published baseline mapping for comparability, expose the role provenance/team names in local reports, and add explicit-role/reversed-order handling if authoritative role metadata is present. This is a mapping limitation requiring schema/organiser evidence, not a reason to align labels against provided GT.

The legacy tag adapter assumes a clock origin. The new candidate omits tags entirely; keep that exclusion until the clock is qualified. No tag-derived possession or interruption fields become model inputs.

No independent full-state reference for the new capture source has been established. A clean result can support experimental known-live owner recovery, not full-timeline stoppage accuracy or correctness on the supplied game. These limits stay visible even if coverage improves.
