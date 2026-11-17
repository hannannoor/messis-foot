# WCSF: frozen model transfer result

9 November 2026. The unchanged experimental control scored **spell F1 0.505216, macro F1 0.707246 and accuracy 70.9517%** on one previously unused anonymous Dutch match. Both fixed w50 comparators scored spell F1 0.384073. The control's descriptive gain is **0.121144** on the same reference. This is agreement with this external provider's labels; the challenge score remains unmeasured.

| Frozen method | Spell F1 | Official macro F1 | Accuracy | Dead recall |
|---|---:|---:|---:|---:|
| w0-c32-neutral-missing | 0.505216 | 0.707246 | 70.9517% | 49.6198% |
| official-convention-w50 | 0.384073 | 0.389824 | 45.2876% | 0% |
| matched-input-w50 | 0.384073 | 0.389824 | 45.2876% | 0% |

The comparator arrays are identical here because the source has complete usable geometry; their missing-input conventions do not diverge. Both halves are pooled as one match, not averaged as independent samples. Control half spell F1s are 0.550838 and 0.475138 (descriptive diagnostics). No new predictor, fit or target output was produced, and the rejected cadence contrast is excluded.

## What remains wrong

The reference contains 411 team-possession spells; the control emits 490. On 143,165 graded canonical rows, it makes 41,587 errors. **33,725 are dead frames called H/A: 81.095% of all wrong frames.** It labels only 154 live frames D, giving dead precision 99.5385% but recall 49.6198%. Dead-interval mean F1 is 0.301695. Correct team identity on known-live frames is 89.6857%.

Direct H/A boundary recall within 12 canonical frames is 84/237 (35.4430%), with 162 spurious boundaries. The 3.226-frame mean absolute latency describes only those 84 matched boundaries and is limited by the source's 100 ms reference precision. It is not timing accuracy for all transitions.

There are zero predicted X rows. Removing abstentions therefore does not remove errors. The strongest observed frame-error concentration is missed stoppages; it is not yet a causal attribution of ranking loss. Diagnose missed/split/merged spell objects and all-state path evidence before choosing a liveness or handover intervention.

## Official metric and rule alignment

The current organiser revision is `f8f2629ff1e0985f81d7e59d8413678514ee1530`. The local metric implementation is the exact official source prefix, with only an appended licence constant; AST parity was independently checked. [Parity receipt](../reports/wcsf-transfer-v2/official-metric-parity.json), [official metric source](https://github.com/metrica-sports/more-than-a-hack-2027/blob/f8f2629ff1e0985f81d7e59d8413678514ee1530/evaluation/possession_metrics.py).

The competition ranks possession-spell F1, while macro F1 measures frame classification. D stretches are separate from possession spells. Temporal scoring fills prediction X within evaluable runs; filling or eliminating X alone is not a quality guarantee. The organiser's baseline floor and noise examples belong to its own match and cannot establish a rank or significance threshold on WCSF. [Official evaluation](https://github.com/metrica-sports/more-than-a-hack-2027/blob/f8f2629ff1e0985f81d7e59d8413678514ee1530/EVALUATION.md).

External labelled games are an allowed method-development source when accessible and explained. No supplied-game human labels, private GT, challenge frame outputs or new target inference were accessed here. Exact raw-to-identical-challenge-submission regeneration is a separate uncompleted milestone, so this audit is not a claim of complete submission eligibility. [Rules](https://github.com/metrica-sports/more-than-a-hack-2027/blob/f8f2629ff1e0985f81d7e59d8413678514ee1530/RULES.md).

## Evidence and limits

The source/rights decision is in [reference qualification](reference-qualification/source-comparison.md), with the repository owner's manual-label/MIT clarification linked there. Anonymous match identity is preserved. The provider's manual liveness/owner semantics, annotation error rates and contested-play conventions are not independently adjudicated.

Geometry uniquely supports absolute team-frame ball coordinates with away XY rotation: all 57,374 eligible native timestamps pass; x-only passes 233 and offset hypotheses zero. The 143,431-row canonical representation contains 28,687 native-grid and 114,744 interpolated rows. Native 10 Hz means supplied preprocessed/smoothed samples, not verified sensor freshness. There are 143,165 known reference rows and 266 X rows; X evaluation masks do not segment inference. These coverage and clock conventions limit portability to irregular broadcast tracking.

One match provides a descriptive provider-transfer audit, not population power, a multi-match interval or a competition-accuracy estimate. The source became permanently used when its outcomes opened. Any future change tested on it must call it development/regression evidence.

[Original v2 freeze](../reports/wcsf-transfer-v2/freeze.json), [acquisition](../reports/wcsf-transfer-v2/acquisition.json), [geometry](../reports/wcsf-transfer-v2/geometry.json), [prediction seal](../reports/wcsf-transfer-v2/predictions-seal.json), [results](../reports/wcsf-transfer-v2/results.json), [score seal](../reports/wcsf-transfer-v2/score-seal.json), [original verification](../reports/wcsf-transfer-v2/verification.json), [post-run attestation](../reports/wcsf-transfer-v2/post-review-attestation.json), [independent review and fixes](wcsf-transfer-review.md).

## History retained without rescoring

Implementation/freeze commit `61a90e3` preceded the first archive download. V1 exactly matched the pinned archive but rejected its 163-byte matching AppleDouble sidecar before any CSV rows or model calls. [V1 failure](../reports/wcsf-transfer/failure.json). The [container-only amendment](superpowers/specs/2026-11-09-wcsf-container-amendment.md) and v2 code/freeze commit `2abd83b` preceded all CSV ingestion. Two distinct assets took three archive transfers across the retained generations. No geometry, reference, method, cost or window was selected after outcomes.

V2 made exactly three inference and three scoring attempts. Independent review verified the original numbers, source/publication identities, all private hashes and actual diagnostic pooling. Later replay/log/algebra safeguards are explicitly post-run, with no rescoring and no rewrite of v2's source freeze or result bytes. V2's first score timestamp was a stage-entry event before reference loading, rather than precise method entry, and its original score seal omitted the access log. The post-run attestation verifies the retained complete log now; it cannot retroactively strengthen what was prospectively sealed.

## Check or replay

Read-only public numeric/hash-chain verification needs no private data or original environment:

```powershell
python wcsf_postrun_verify.py public
```

Public verification cannot certify unseen private data or annotation truth. On this original workspace, `python wcsf_postrun_verify.py local` additionally checks all 175 preserved historical sources, four private input hashes, six output hashes and complete logs without inference or scoring.

A fresh replay gets its own run identity, outputs and environment freeze:

```powershell
python wcsf_audit.py freeze --run-id my-replay
python wcsf_audit.py acquire --run-id my-replay
python wcsf_audit.py qualify --run-id my-replay
# Continue only if the geometry decision passes.
python wcsf_audit.py infer --run-id my-replay
python wcsf_audit.py score --run-id my-replay
python wcsf_audit.py verify --run-id my-replay
```

Replay reports go under `.tmp/wcsf-runs/my-replay/reports`; raw/stores/arrays stay in sibling `wcsf-reference/my-replay`. Existing or incomplete generations are preserved. This command sequence is a reproduction interface, not an executed second scientific run in this work. The fresh-clone tests execute only freeze/public verification and synthetic ingestion/scoring. New environments record a new freeze; they do not overwrite historical evidence.

## Final validation checkpoint

The post-review suite passes **462 tests, 19 skips, zero failures/errors** (443 executed, all 56 new tests). The pre-data v2 test receipt remains 455/19; it is not rewritten to imply later guards existed before scoring. [Post-review validation](../reports/wcsf-transfer-v2/post-review-validation.json) and [permanent source-use ledger](../reports/wcsf-transfer-v2/use-ledger.json).

For the full Windows suite, set TEMP/TMP to a writable local `.tmp`, set FOOTBALL_STANDALONE to the checkout's `football_pipeline.py`, then run `python -m unittest discover -s tests -p 'test_*.py'`. Existing filesystem-link fixtures require native link permissions; optional dependencies account for the 19 skips in this environment. No new dependency was installed.
