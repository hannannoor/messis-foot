# Official evaluation assessment — 9 November 2026

**We have a tested research prototype with a useful new-provider result, but no measured challenge score or demonstrated final-submission rebuild. My competition-readiness grade is 45/100.** That is a subjective delivery/maturity judgment, not accuracy or percentage of the project completed.

| Dimension | Grade | Evidence and remaining gap |
|---|---:|---|
| Engineering maturity | 75/100 | 462 tests, 19 skips (443 executed), 56 new tests; strict input/reference separation, prospective source freezes, independent review and corrected replay/log guards. The newest control still needs a clear competition release entry point. |
| Independent performance evidence | 45/100 | One genuinely unused full-state provider match was evaluated once with fixed methods. It is now used evidence. One match, smoothed 10 Hz inputs and unadjudicated provider labels do not establish broad generalization. |
| Competition readiness | 45/100 | Current scorer alignment and a public repository are supported. The chosen target CSV, exact raw-to-identical-file regeneration, integrated release and final technical packet are not verified here. |

## Measured model result

On the single WCSF match, the frozen control achieved **spell F1 0.505216, macro F1 0.707246 and accuracy 70.9517%**. Both preselected w50 comparators achieved spell F1 0.384073: a descriptive same-match difference of 0.121144. This is not the organiser's match or its leaderboard. [Results, support and limits](wcsf-transfer-results.md), [sealed aggregates](../reports/wcsf-transfer-v2/results.json).

Dead recall is 49.6198%, with precision 99.5385%. Missed dead frames account for 33,725 of 41,587 errors (81.095%); correct team identity on known-live frames is 89.6857%. Direct H/A boundary recall within 12 canonical frames is 84/237. Zero predicted X rows did not make these decisions correct.

That error concentration warrants an all-state diagnosis. It does **not** prove that missed D contributes 81% of ranking loss: a long missed stoppage and many short broken possessions have different spell consequences. The next analysis should attribute missed/split/merged spells and distinguish weak emissions, retained-control features and decoder costs before choosing a fix.

## What the organiser actually rewards

The board ranks mean possession-spell F1 at temporal IoUs 0.3/0.4/0.5/0.6/0.7. Frame accuracy is not the ranking objective. Macro F1 remains a useful class-balanced diagnostic. Prediction X is penalized framewise and filled for temporal scoring; eliminating it is not an objective by itself. The public window is a pipeline check, not a tuning set. The organiser's baseline floor/noise calibration cannot be transferred to WCSF. [EVALUATION.md](https://github.com/metrica-sports/more-than-a-hack-2027/blob/f8f2629ff1e0985f81d7e59d8413678514ee1530/EVALUATION.md).

The runner breaks exact ranking ties by macro F1, transition F1 at the loose tolerance, lower matched mean absolute latency, then filename. The local metric source matches every official executable statement; its only addition is the licence string. [Runner specification](https://github.com/metrica-sports/more-than-a-hack-2027/blob/f8f2629ff1e0985f81d7e59d8413678514ee1530/evaluation/run_evaluation.py), [parity receipt](../reports/wcsf-transfer-v2/official-metric-parity.json).

## Submission gates

The required CSV has 199,319 data rows on the 25 fps tactical-video index, ordered frame 0..199318, header `frame,label`, H/A/D/X labels and no blanks. The broadcast source has a different index. The three deliverables are that file, a public reproducible code repository with pinned setup/run instructions, and a short technical document covering method, assets/training, possession conventions, limits and reproduction. The published deadline is **17 November 2026**; the document does not specify the closing time/timezone. [SUBMISSION.md](https://github.com/metrica-sports/more-than-a-hack-2027/blob/f8f2629ff1e0985f81d7e59d8413678514ee1530/SUBMISSION.md), [game registry](https://github.com/metrica-sports/more-than-a-hack-2027/blob/f8f2629ff1e0985f81d7e59d8413678514ee1530/games.py).

| Gate | Current finding |
|---|---|
| Official scorer | Aligned. Exact current metric source, explicit external period/X wrapper and source precision disclosures. |
| Public repository | **Satisfied at the latest check.** Earlier it was private; the API at 05:57:40 UTC on 9 November reports public. This agent did not change visibility. |
| Version organisers will run | Needs resolution. Default `main` is `3a1c860`; the latest assessed checkpoint is `3211339` on `codex/cadence-baselines-2026-11-08`. PR1 and draft PR2 are open. Link/name the exact final release, not an ambiguous older default route. |
| Exact selected CSV validity | Unverified. No current target prediction CSV was opened by this assessment. Code-level row/alphabet guards and synthetic tests do not prove the selected file itself passes the organiser's validator. |
| Exact regeneration | Unverified. Earlier audit demonstrated UUID-dependent cache-byte seals despite equal semantic arrays. A new reconstruction lineage must separate semantic identity from container-generation hashes. Historical seals remain unchanged. |
| Single current release | Incomplete. The preserved standalone/README describe older routes; the experimental candidate still validates research evidence and computes unused controls. WCSF replay improvements do not close the challenge-export gap. |
| Technical packet/team | Not finalized or verified here. Assemble one concise document for the chosen method and confirm registration/team requirements. |

The current API inventory covers four branch heads and both open PRs; all heads are ancestors in the latest branch's 27-commit history at the recorded snapshot. The earlier full adversarial response supplies source/history findings; the seven later implementation/evidence commits are preserved rather than substituting a report summary for code. [Verified audit](../adversarial-review/VERIFIED-AUDIT-RESPONSE.md), [assessment contract/state record](../reports/official-evaluation/contract-check.json).

External labelled games are allowed when accessible and explained; hand labels or human-produced data about the supplied game cannot train/validate the model. Private GT is prohibited. Team size is 3–5, with under-three teams ineligible for the specified innovation/final-pitch tracks. Registration details were not inspected. [RULES.md](https://github.com/metrica-sports/more-than-a-hack-2027/blob/f8f2629ff1e0985f81d7e59d8413678514ee1530/RULES.md).

## Next work, in order

1. **Plan a minimal deterministic release of the current frozen control.** Name one entry point/artifact, remove inference dependence on unused research machinery, pin the runtime and prove stable semantic reconstruction plus exact export on controlled fixtures. Keep historical experiments intact. Prepare the final-file validation/rebuild command and a concrete integration/release decision.
2. **Bound the ranking-directed diagnosis.** Reuse the approved whole-path work, but write a separate all-state addendum addressing D as well as H/A and this now-used WCSF case. Quantify spell-object failure attribution before changing thresholds, costs or features. Preserve the original approved design/plan.
3. **Allow at most one justified intervention, then freeze.** Test on explicitly used development/regression sources; do not rename WCSF fresh again. Require spell quality and liveness/boundary safeguards. No broad grid, blind D threshold relaxation or renewed camera fusion without evidence of added usable information.
4. **Close delivery gates before the deadline.** Integrate/name the chosen release, validate the exact selected file, demonstrate identical regeneration, finish the short technical document and confirm team/submission logistics. Those actions are distinct from this read-only assessment.

There are eight calendar days from this assessment date to the published deadline. That favors one defensible method and a reproducible submission over another open-ended architecture search. No new model comparison, target access, tuning, merge or visibility change occurred during this assessment. Per the user's request, the next goal is left for a new chat using the continuation handoff.
