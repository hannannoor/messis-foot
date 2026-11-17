# Frozen-control all-state path findings

9 November 2026. This implements the planned diagnosis of the unchanged control. **It does not improve or promote a predictor.** The subjective readiness rating is not a measured prediction score; hidden challenge performance remains unknown. No challenge inputs, public-window outcomes, new acquisition, parameter search or fitting entered this diagnosis.

## Decision

Prioritize one separately planned observation/control-memory feature experiment over a generic reduction of switching cost. All five used cases show that supported ownership errors usually have episode emission sums favoring the wrong owner. Correcting only supported ownership swaps changes spell F1 more than the D-involving repair in every case, including WCSF. The exact replacement feature remains unresolved: memory association shares geometry with the head and does not prove memory causes the mistakes. This report does not authorize an automatic refit or select a threshold.

The next experiment should isolate one input-evidence hypothesis, hold the decoder fixed, use mean spell F1 as its primary objective, and retain per-case D safeguards. The rejected velocity-only repair and its failure to retain D remain relevant historical constraints. Additional fitting, feature combinations or a cost grid require their own prospective plan.

## Fixed results

These are natural-input results on already-used external evidence. SkillCorner has known H/A reference support and no known D; its D recall is therefore unmeasured. DFL and WCSF include D. WCSF remains one separate two-half match, permanently used evidence. Do not average these rows into a fresh validation estimate.

| Original four cases | Known frames | Baseline mean spell F1 | Supported liveness repair, signed delta | Supported ownership repair, signed delta |
|---|---:|---:|---:|---:|
| SkillCorner 1874553 | 81,805 | .661565 | -.000454 | +.282281 |
| SkillCorner 1886347 | 79,980 | .670567 | .000000 | +.248633 |
| DFL J03WOH | 137,214 | .579972 | +.012119 | +.387989 |
| DFL J03WOY | 142,536 | .543550 | +.007911 | +.430156 |

| Separate used case | Known frames | Baseline mean spell F1 | Supported liveness repair, signed delta | Supported ownership repair, signed delta |
|---|---:|---:|---:|---:|
| WCSF, both halves | 143,165 | .505216 | +.158763 | +.266809 |

Both repairs use reference labels, leave GT-X and latent-X/materialized rows unchanged, and are diagnostic arrays rather than feasible models. Deltas can be negative and cannot be added or interpreted as independent causal loss fractions or guaranteed upper bounds. The small negative SkillCorner liveness delta is an observed example of this non-monotonic spell metric.

For the original four only, the arithmetic equal-provider/equal-case mean is .613914 baseline, .618807 under the liveness repair and .951179 under the ownership repair. The verification receipt keeps each provider's two-case mean visible and WCSF separate. These summaries do not replace per-match F1 or turn the repairs into achievable gains.

The [five case receipts and summary](../reports/ownership-path/2026-11-09-natural-v2/summary.json) contain all five IoU thresholds, baseline/repair TP/FP/FN, confusion, support, error episodes and strata. The [verification receipt](../reports/ownership-path/verification.json) also records signed TP/FP/FN/F1 changes derived arithmetically from those receipts, without rescoring.

## What the objective explains

Complete source/period/usable segments retain H/A/D and include unknown-reference rows. Reference masks only select later queries. The instrument exactly reconstructs frozen labels and checks constrained score, forward/local/backward decomposition and fixed-episode patch algebra. Positive margins favor the selected wrong state. One tied decomposition is not a unique causal explanation.

| Case | Supported ownership-swap frames | Frames in episodes favoring wrong-owner emissions | Frames in episodes with reference-favoring emissions blocked by extra switches | Carried errors, all states |
|---|---:|---:|---:|---:|
| SkillCorner 1874553 | 7,261 | 7,118 | 143 | 502 |
| SkillCorner 1886347 | 6,555 | 6,307 | 148 | 2,491 |
| DFL J03WOH | 9,512 | 9,272 | 240 | 0 |
| DFL J03WOY | 11,349 | 10,765 | 584 | 0 |
| WCSF | 7,708 | 7,456 | 252 | 0 |

The classifications apply to complete constant-reference/prediction error episodes, not to every local frame. In SkillCorner 1886347 another 100 supported swap frames belong to the residual mixed/nonlocal category. Some individual frames favor the reference locally or reverse under future evidence; those counts and complete margins remain in the receipts. This does not prove every decoder intervention would fail. It argues against choosing a blanket cost reduction from this evidence.

The corrected v2 directly measures the original decision criterion on ball-observed, supported ownership errors more than 2s from known boundaries/annotation edges:

| Case | Supported interior swap frames | Local emissions favor wrong owner | Local emissions favor reference |
|---|---:|---:|---:|
| SkillCorner 1874553 | 2,922 | 2,862 | 60 |
| SkillCorner 1886347 | 2,673 | 2,651 | 22 |
| DFL J03WOH | 1,360 | 1,312 | 48 |
| DFL J03WOY | 1,523 | 1,456 | 67 |
| WCSF | 1,396 | 1,345 | 51 |

There are zero absolute local near-ties in these five rows. Reference-team and usable/unusable support are explicit in each stratum. Memory association uses only final H/A swaps with an evaluable H/A memory, including carried swaps when present; it is a separate denominator from supported emission queries. In particular, reference D is excluded from that memory comparison. Agreement and every supported known-live row also retain the full legacy reference-owner versus opposite-owner decomposition, including false-D predictions. Numerical ties use the declared absolute-plus-relative predicate and remain separate from fixed absolute margin bins.

WCSF has 33,725 missed-D frames. Of these, 33,701 belong to 265 episodes with emissions preferring the selected H/A path; only 24 belong to two episodes blocked by additional switches. Its 154 false-D frames also favor the wrong state in episode emissions. Thus, lowering cost alone does not address the observed episode emission preference. Provider labels are supplied annotations rather than adjudicated physical-control truth.

## Spell objects

WCSF retains exactly 411 reference and 490 predicted spells. At IoU .5: 233 matched, 178 missed and 257 spurious. The missed spells partition into 75 with no same-team overlap, 103 with overlap below threshold and zero qualifying overlaps consumed by greedy matching. Spurious spells partition into 175/82/0 respectively. At IoU .3 there are four consumed reference and two consumed prediction objects; matching collisions are present at lower thresholds.

Twelve WCSF reference spells overlap multiple predicted spells and 31 predictions overlap multiple reference spells. These are overlapping split/merge flags, not additive error categories. Each IoU's missed/spurious partitions reconcile to official greedy matching, with counts pooled over periods before F1. Both destination-matched all-state and pair-matched H/A boundaries report counts and conditional latency at 12 and 25 frames, matching within each valid period/run before pooling; no boundary lag was fitted.

## Execution and reproduction

Corrected code checkpoint `e93d86e` precedes the real diagnostic. The prospective [freeze](../reports/ownership-path/2026-11-09-natural-v2/freeze.json), committed at `986fc94`, binds source closure, model, original approved documents, selection metadata, input hashes, retained pilot and WCSF evidence, and runtime. Its SHA-256 is `136899f8d6c10207e2914784b6568c12f592422038c2ff76a1096f572122b017`.

In corrected v2, exactly five input-only head/decoder reconstructions, five baseline metric reconciliations and ten reference-only repair evaluations completed in this new lineage. The four-case pilot's known-live/swap/raw-final counts match exactly; WCSF's canonical index and final prediction arrays equal its sealed control, and its baseline spell counts/F1 match. No comparator was rerun. Private traces and reference arrays are excluded from Git.

The original cache adapters physically parse reference containers during loading; the private access log records this. Pure inference and path-table functions accept no reference, and reference-mask perturbation tests leave input paths unchanged. This is not a claim of reference-first-access-after-inference or fresh validation. WCSF's reference codes are loaded after geometry preparation/inference through the retained read-only adapter.

With the retained local stores in their original sibling directories:

```powershell
python ownership_run.py verify --run-id 2026-11-09-natural-v2
```

Verification checks hashes, private trace semantics, receipts, exact inventory and access/evaluation chronology, with no inference or scoring. Missing private stores fail rather than silently rebuilding data. To deliberately reproduce computation, use a new run ID with `freeze`, `run`, `summarize`, then `verify`; doing so is another used-data diagnostic generation and must be logged. Existing/incomplete generations are preserved.

The preserved superseded v1 adds another five reconstructions/five baselines/ten repairs; it was repeated to fill review-identified measurement gaps, with no new variant or tuning. Current verification of v2 also checks canonical summary bytes, trusted hash-key inventory, all five historical WCSF IoUs/mean, pinned release components and actual runtime.

The [review record](ownership-path-review.md) and verification receipt provide final test and preservation evidence. The original release artifact, selected predictor sources, original approved documents, historical results/logs and selected CSV generations remain unchanged.
