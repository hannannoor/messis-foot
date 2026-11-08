# Observed swap diagnosis â€”8November2026

Current candidate and all source/model/output bytes remain unchanged. This is a read-only four-match development replay, not a new accuracy claim. Council conclusions are separately distinguished from measurements.

| Provider/match | Known-live frames | H/A swaps | Swap rate | Raw-correct/final-wrong | Raw-wrong/final-correct |
|---|---:|---:|---:|---:|---:|
| skillcorner/1874553 | 81805 | 7763 | 9.49% | 206 | 1313 |
| skillcorner/1886347 | 79980 | 9046 | 11.31% | 225 | 1407 |
| dfl/J03WOH | 71945 | 9512 | 13.22% | 683 | 1010 |
| dfl/J03WOY | 76286 | 11349 | 14.88% | 978 | 818 |

Raw/final comparison columns use observed, usable known-live rows only. They include decisions involving D and do not imply whole-path causal attribution.

## Evidence that narrows hypotheses

- Input availability affects error rates. On the two SkillCorner development matches, swaps are3383/10257without coordinates versus13426/151528with coordinates. Absolute counts and conditional risk answer different questions. DFL has no missing known-live inputs in this natural sample.
- Boundary proximity matters: swaps are enriched within2sof known state changes. Nevertheless,5602SkillCorner and2883DFLswap frames remain in observed reference interiors beyond2sfrom known state boundaries and annotation/period-run edges. These are provider-label interiors, not independently settled physical-control intervals.
- Remembered automatic control opposes the reference on94.16%of SkillCorner swap frames and92.03%of DFL swap frames. This is a conditional association, not an independent cause: memory is computed from the same geometry and used by the head.
- Decoding is not uniformly harmful: it corrects2720raw decisions while spoiling431on SkillCorner, and1828versus1661on DFL, on observed usable known-live rows. One DFL match reverses that net comparison. Raw/final frame counts do not distinguish future evidence from switch penalties.
- Input team exchange demonstrates limited non-equivariance in this sample:690/161785and1194/148231known-live outputs differ after swapping identities back. This does not establish a general upper bound on symmetry-based improvements.
- Cached/source clock and team-ID checks establish mechanical consistency, with contradictory phase frames excluded. They do not independently validate provider possession semantics or prove control. No global clock/identity correction was discovered or fitted.

## What has not been diagnosed yet

Local traces cannot identify why offline Viterbi preferred a whole path. Forward/backward constrained path scores, cumulative emission versus switch-cost terms and future-context differences have not been computed in this pilot. Provider semantic disagreement and physical truth also remain unresolved. A broad new ownership model is therefore a hypothesis, not an already justified fix.

## Council outcome

All five fresh reviewers favored the Executorâ€™s identifiable trace and warned against bundling new supervision, motion context and symmetry in one training change. Four independently flagged nonlocal future evidence; the fifth suggested paired natural/masked propagation analysis. All used one model family, so peer agreement is not independent empirical validation. The separate chairman selected a single whole-segment competing-path diagnosis as the next experiment. The full protocol and all responses are in active/council-transcript-2026-11-08-ownership-swaps.md.

## Deliverable state

Completed: five-advisor/five-reviewer/chairman Council, four natural development replays, input/source identity checks, aggregate invariants, source-contract inspection and reviewed diagnostic design. Completed after user design approval: concrete Superpowers plan at ball-gap-work/docs/superpowers/plans/2026-11-08-ownership-path-diagnosis.md. Its execution is deferred until the queued adversarial audit is reviewed. No production refit, predictor implementation, new target output or publication has occurred in this task. The userâ€™s full adversarial repository audit is queued to start after this task is complete.
