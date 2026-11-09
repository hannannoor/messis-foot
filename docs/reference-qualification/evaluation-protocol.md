# WCSF acquisition and one-shot transfer-audit protocol proposal

Review begun 8 November; proposal frozen 9 November 2026. This is a prospective proposal from documentation, not an executed adapter or scoring receipt. No assets or reference outcomes were opened during qualification. A concrete implementation design/plan and its check must precede ingestion. The user has authorized sequential planning/execution; create the next goal only after the current qualification goal is achieved.

## Source, rights and access

- Source: MatKempeGroningen/WCSF_SolutionRoom at `1c9ba798f98a9fffb16081a5d3965774d4e5662c`; exactly the two pinned half ZIPs in source-qualification.json, about 46.45 MB combined. Free direct public archive route; no account/form/contact/payment.
- Permission evidence: repository owner's 6 November 2026 [dataset clarification](https://github.com/MatKempeGroningen/WCSF_SolutionRoom/issues/5#issuecomment-6681182193). Preserve anonymity, source attribution, declared MIT status and the fact that no LICENSE file is present. Attribute the University of Groningen, Matthias Kempe, Floris Goes-Smit's project and SciSports as described by the guide; link the repo and owner statement. Do not redistribute raw assets as part of MESSI's FOOT.
- Store assets/reference/features outside the source checkout, in a new dedicated `wcsf-reference` sibling with no-clobber generation IDs. Verify ZIP Git blob SHA before extraction; inspect safe member names, uncompressed sizes and compression ratios first. Resource proposal: compressed transfer under 50 MB; stop for review if declared extracted data exceed 2 GB or available workspace headroom is inadequate. No ZIPs/CSV/NPZ/SQLite/raw rows/video belong in GitHub or model-visible output.

## Input-only structural qualification, before outcomes

1. Bind all original consumed wrapper/scorer/input modules as well as new sources; the original cadence freeze's four-wrapper omission is not repeated. Keep source, adapter, role/time/mapping and reference-loader identities separately visible. Use a complete prospective source inventory and a separate original-release verification.
2. Parse only expected named columns into independent geometry and reference stores. Predictor inputs are player/ball geometry, declared team roles, periods/timing and quality/provenance. AliveFlag, PossessionFlag, team_game_phase and derived state summaries never become features or inference barriers.
3. Preserve two source-file periods and native monotone timestamps. Reject duplicate player/time conflicts and unexplained clock discontinuities. Determine timestamp origin from source clocks/file structure, never from labels or predicted boundaries.
4. Resolve mirrored/team-relative ball coordinates with documentation and duplicated **input geometry** consistency. Test the documented absolute-team-frame and player-offset interpretations and possible per-team reflection; require a unique justified reconstruction up to a harmless common pitch reflection. If no interpretation is supported, stop and report the unresolved contract; do not select one by possession accuracy or infer private match identity.
5. Verify stable anonymous player membership and duplicated ball consensus; retain missing/invalid geometry honestly. No source-status or reference-dependent interpolation. Do not pretend finite repeated coordinates certify fresh observations.
6. The existing head operates at 25 Hz. Specify the canonical-grid transform before model outcomes: interpolate player/ball positions only between adjacent valid 10 Hz observations within one period, using source IDs where needed and labelling interpolation. Do not cross absent native samples, extrapolate gaps or imply extra independent measurements. Scale the documented 105x68 m source to the existing canonical 105.3x68 geometry explicitly. Keep native times and uncertainty separate; no 20 ms truth claim from 100 ms annotations.

These are requirements for the future adapter design, not a licence to guess unresolved numerical details. Exact header/dialect, reconstruction tests and tolerances must be settled from documentation/input-only structure before outcome scoring. Structural failure completes a qualification report, not a hidden retry with a more favorable match.

## Separate reference contract

Use native timestamp consensus across duplicated player rows. AliveFlag 0 maps to D. AliveFlag 1 plus possession group 1/2 maps to H/A. Missing, contradictory or invalid reference values map to evaluation X; missing events are not D. No label forward fill across missing native timestamps, lag fitting or hand corrections. At a valid native interval, carry its declared state only under a fixed 10-to-25 Hz reference mapping chosen before outcomes; preserve the 100 ms source precision. Neither X support nor reference boundaries alter inference segmentation or source quality.

Require nonzero independently supplied H, A and D support and report every exclusion/coverage count before interpreting full-state metrics. No class absence may become perfect recall. If the reference does not support this contract, publish that finding and do not invent state truth.

The maintainer describes manual SciSports labels. Detailed control-through-flight/contest conventions and adjudication error rates remain unknown. The audit measures agreement with this provider reference, not physical-control certainty or target accuracy.

## Frozen methods and decision

- Primary: released `w0-c32-neutral-missing`, tree and input-only inference settings unchanged.
- Comparators: `official-convention-w50` and `matched-input-w50`, definitions from the completed four-match development pilot. The w50 matched family had the best natural equal-provider spell F1 among that fixed family in those already seen data. The literal variant uses the same width for a transparent convention comparison. This selection is frozen before any WCSF outcome; no challenge score is used.
- The rejected velocity-only candidate is not automatically promoted or added to a new search. No fitting, horizon/window/cost grid, source-specific retuning, target run or new label creation.
- Both halves constitute **one match**. Pool official per-IoU TP/FP/FN for the primary match score rather than treating halves as independent replicates or averaging their F1s without disclosure. Respect input periods and evaluation-only separators. Report raw frame confusion/accuracy/macro F1, D PRF/interval metrics, per-half and match spell counts, short-spell recall and run-local pair-typed H/A boundary support/latency. Keep denominator and timing precision clear.
- At most three fixed method comparisons on the one match, with complete source/input/reference/protocol freeze before scoring. No match selection based on score. No population confidence interval from two halves. A poor result is retained; it does not authorize rewriting labels or finding a new threshold on this match.
- Report all three methods and signed paired differences against the control, with the frozen official spell score as the primary descriptive endpoint and all other metrics explicitly secondary. There is no favorable-result threshold, superiority claim or advancement permission in this one-match audit. Describe agreement with this provider's reference and its observed failures only. After opening outcomes the source becomes used evidence; every later adaptation must call it development/regression, never fresh again.

## Support and power rationale

The source offers one match, not a sample chosen to meet a population power target. Two halves and thousands of correlated frames do not increase the number of independent matches. This audit is deliberately not powered for a population superiority/noninferiority claim or a percentage estimate of competition accuracy. Its useful question is narrower: does the fixed method transfer to a previously unused provider's complete sample, and where does it fail?

Before interpreting outcomes, report native/canonical evaluated duration, X exclusions, H/A/D seconds and spell counts, every official IoU denominator, short-spell counts using the existing frozen scorer's bins, and direct H/A boundary support. If any state is absent, the full-state audit is incomplete. If a diagnostic has zero support, report null with its denominator; do not call it perfect or use it to pass an advancement gate. Sparse event/short-spell cells remain descriptive and cannot justify subgroup claims. Do not acquire a replacement match because support or results are inconvenient. A later generalization study needs a separately scoped multi-match/provider sampling and detectable-effect analysis, using this audit only as already-used development evidence.

## Access/use ledger and annotation fallback

Current state: documentation and existing-cohort metadata reviewed; new WCSF ZIPs, rows, reference labels, model outputs and videos unopened. Retain their eventual acquisition, reference-access, protocol-freeze and outcome-opening timestamps/hashes separately. A source can be lawful yet structurally unsuitable.

If WCSF fails structural qualification, do not silently replace it. The larger SoccerTrack fallback would require ball-observation construction, an external-only H/A/D annotation manual, annotators blinded to predictions and BAS shortcuts, independent adjudication, ambiguity X, rights/attribution, access-gate acceptance, a non-overlap check and an explicit resource quote. No hiring, annotations, account acceptance or acquisition is authorized by this qualification-planning package itself. Continue useful approved whole-path diagnosis while that separate dependency is resolved.
