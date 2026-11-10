# Gap liveness design — addendum 2, 10 November 2026

Status: approved for implementation; both requested clarifications were answered in chat. User authorized applying both addenda in chat. Base a5d5aa3c7da86837ec0f0a750f8e1996b66e639a. All files already present at base, including the rejected touch experiment and frozen release, are preserved byte-for-byte. This is a new experiment with a new registry; no old budget is reset.

## Approved source brief

# Addendum 2 — long-gap dead-ball rule, 10 November 2026

This adds one goal to `TOUCH-EVIDENCE-HANDOFF-2026-11-10.md` and `TOUCH-EVIDENCE-ADDENDUM-1.md`. The user approved this design in chat on 10 November. All guardrails in section 3 of the handoff apply unchanged, including: aggregates only from the challenge match, no tuning on the public window, frozen release untouched, no push or merge without the user.

**Priority: do this goal before the touch experiment's evaluation (handoff Stages 3–4).** If touch code is already in progress, finish the current test-first step, commit, and switch. The two goals are independent: this rule acts only on missing-ball frames, touches act only on observed-ball frames.

## 1. Why

Measured on the challenge match with local scripts, aggregates only, no ground truth (full numbers in `probe-results.json` beside this file):

- The ball is missing in 150 gaps on graded frames; 85% of missing frames are in gaps longer than 10 s.
- The frozen control predicts D on about 4% of long-gap frames and about 2% of other graded frames.
- Of 133 gaps longer than 3 s, 127 receive a single owner label equal to the label on both sides. If the gap is a stoppage, that merges two possessions and the stoppage into one spell.
- Typical player speed is lower inside gaps (median of per-gap medians 1.03 m/s for gaps the automatic Smart Tagging links to a set piece, 1.26 m/s for other gaps) than on frames outside gaps (median 1.65 m/s). 98% of tagged gaps and 72% of untagged gaps are below 1.5 m/s, against 41% of frames outside gaps.

Reading: most long gaps look like stoppages; roughly a quarter of untagged gaps look like live play. This is label-free evidence from one match, not a measured accuracy.

## 2. The rule

New module, suggested `gap_liveness.py`. Standard library only, deterministic, pure functions. It runs after the control's decoding and before or as part of materialisation; choose the insertion point that keeps the control's own code unedited, and state it in the spec.

Definitions (frame rate 25 fps):

1. **Player speed statistic.** For frame i and the frame 25 frames earlier in the same period, take every associated player id present in both, compute displacement in metres over that second, discard values of 12 m/s or more, and take the median if at least 10 players remain; otherwise the statistic is undefined for that frame. Evaluate on every 5th frame index.
2. **Long gap.** A maximal run of consecutive frames in one graded period with the ball not observed, longer than 75 frames. A gap may start at the first frame of a period.
3. **Match reference speed.** The median of the statistic over all graded frames that are not inside a long gap. It is computed from the match being labelled, by code. Do not hard-code its value.
4. **Stoppage gap.** A long gap whose median statistic (over its frames where the statistic is defined) is strictly below the match reference speed. A long gap with no defined statistic is not a stoppage gap.
5. **Labels.** Every frame of a stoppage gap is labelled D. Other long gaps keep the control's labels.
6. **Restart extension.** After a stoppage gap ends, frames stay D while the ball is observed and its speed (displacement from the previous observed frame × 25) is at most 0.5 m/s, for at most 250 frames, stopping at the first frame that breaks the condition, at the next missing frame, or at the period end. The 0.5 m/s value is the control's existing slow-ball constant in `feature_rows`.

Fixed constants: 75 frames, 25-frame speed baseline, every-5th-frame sampling, 12 m/s cap, 10-player minimum, 0.5 m/s, 250 frames. They are design choices made before any scoring. **There is no grid and nothing to tune.**

Not included, on purpose: moving the start of D earlier than the gap, using Smart Tagging inside the rule, any learned classifier, any use of ball position near boundaries.

## 3. Tests (write first, watch fail)

Synthetic fixtures with exact expectations:

1. No long gap anywhere → output identical to the control's labels (parity).
2. One 200-frame gap with all players stationary, inside play where the reference speed is 2 m/s → every gap frame D; frames outside unchanged.
3. Same gap with players moving at 4 m/s → gap frames unchanged from the control.
4. Gap of exactly 75 frames → not a long gap, unchanged. Gap of 76 frames with slow players → D.
5. Gap at the first frame of a period with slow players → D.
6. Gap spanning a period boundary is two gaps, classified separately.
7. Restart extension: after a stoppage gap the ball is observed stationary for 40 frames then moves → those 40 frames D, the moving frame unchanged. Stationary for 400 frames → only the first 250 are D.
8. No extension after a non-stoppage gap.
9. Fewer than 10 players with a defined displacement throughout a gap → not a stoppage, unchanged.
10. Period 0 frames are never changed.
11. Mirror symmetry: swapping home and away changes no D decision.
12. Scale invariance of the decision: multiplying all player speeds in the match by the same factor leaves every stoppage decision unchanged.
13. Determinism: same input twice → same label SHA-256.
14. Static check: module imports no reference-label reader, no official metric, no third-party package, and contains no integer literal above 1,000 (guards against hard-coded frame numbers).
15. Existing suite and release preservation tests still pass; frozen artifact hash unchanged.

## 4. Checks before it can ship

There is no clean labelled validation for this rule. None of the external matches has this gap pattern. Say so in the write-up. The checks below can catch harm; they cannot prove the gain.

**4a. External harm check (gating).** On the 15-match cohort, natural regime, same weighting as the handoff: reproduce the control's 0.551816 first. With the rule applied, equal-provider primary spell F1 must not fall by more than 0.005, and no provider mean may fall by more than 0.01. Also report, per provider: number of long gaps, number classed as stoppage, frames relabelled. Report the `mask30-seed1729` regime too, but it does not gate: random masks are unrelated to stoppages. One run; no changes to the rule afterwards.

**4b. Metrica sample matches (reported, gating only on clear harm).** Source: https://github.com/metrica-sports/sample-data (public; no formal licence, the README asks for responsible use and acknowledgement). Write the event-to-possession reference rule and commit it before scoring: same-team on-ball events chain into a spell; a `BALL OUT` event, a goal, or a foul starts D until the next `SET PIECE`. Score control and control-plus-rule with the official metric. Caveat to print in the results: that data is manually corrected and drops the ball mostly during dead play, so this check is partly circular. Gate: stop and report if the rule lowers mean spell F1 on these matches.

**4c. Challenge-match self-consistency (reported, not tuned).** Aggregates only, one run: D share of graded frames before and after; predicted spell count before and after; long gaps total, classed stoppage, classed live; share of graded `SET PIECES` tag starts that fall on a predicted-D frame or within 3 s after one, before and after; label counts between the start of the graded second-half block and the first observed-ball frame of that half. Do not adjust the rule in response to these numbers. If something looks broken (for example D share above 60%, or zero stoppage gaps), stop and tell the user.

**4d. Public window.** As in the handoff: record the ship decision first, run once, correctness only.

## 5. Decision

- 4a passes and 4b shows no harm → recommend shipping control plus gap rule, and say plainly that the expected gain is argued from label-free evidence, not measured.
- 4a fails → do not ship the rule; report the provider that regressed.
- Whatever happens, the frozen control remains available as the fallback.

If the touch experiment later ends in Accept, add one combined-parity test: on frames outside stoppage gaps and restart extensions the combined output equals the touch candidate's; inside them it is D.

## 6. Budget

One implementation, one external run (4a), one Metrica run (4b), one challenge aggregate run (4c), then the release steps of handoff Stage 5. No reruns after seeing results except for a demonstrated code defect, which must be preserved and reported.

## Implementation decisions proposed before scoring

- The new pure gap rule is part of a new materialisation wrapper: obtain exactly the incumbent's fully materialised labels, then replace only the classified gap/extension frames with D. Do not materialise again afterward. This guarantees parity everywhere outside the explicit D mask and leaves the incumbent decoder/materialiser unedited.
- One associated player is a (team, associated id) pair. Match ids at i and i-25, within the same contiguous period. Missing/insufficient identities produce an undefined statistic, never fabricated correspondences. Samples use canonical global indices divisible by five.
- If no match reference statistic is defined, classify no stoppage gaps. If a gap has no defined samples, classify it as non-stoppage. Strict below-reference comparison; exact 75-frame runs excluded.
- The restart formula is implemented literally: first reappearance compares with the last observed ball in the same contiguous period, multiplied by 25; without such an observation no extension starts. A large displacement across the gap therefore prevents extension, even if the newly visible ball is subsequently stationary. This consequence is reported rather than silently substituting a new speed definition.
- Metrica cohort: all three public Sample Games described by the source README; source revision and file hashes must be pinned before acquisition/scoring. The event-to-possession rule and uncertain/uncovered spans must be declared before scores. No sample can be silently omitted because it is inconvenient.
- No Stage 0 rerun. Supplied addendum aggregate claims are provenance-distinct from our earlier all-frame planar-width proxy probe; the earlier measured receipt is not overwritten.
- The official competition repository was rechecked: HEAD remains f8f2629ff1e0985f81d7e59d8413678514ee1530.

## Resolved clarifications — user replies recorded before implementation

1. Test 12's unrestricted scale invariance conflicts with the fixed 12 m/s exclusion. Synthetic counterexample: reference players 2 m/s, gap players 1 m/s => stoppage; multiply all by ten => all 20 m/s reference values are discarded while 10 m/s gap values remain, so no defined reference and no stoppage. Approved resolution: keep the fixed cap; limit invariance to positive common multipliers that preserve cap eligibility.
2. The named probe-results.json is absent beside the addenda and no matching file was found below that supplied folder. The user explicitly approved using the written aggregates. Their missing underlying receipt is not claimed verified and the probes will not be rerun.

## Sequential experiment gates

First implement/test both independent pure inference changes, then freeze and run gap-rule 4a before any amended-touch candidate evaluation. 4a has exactly 30 control evaluations (15 matches × natural/masked) and 30 paired gap-rule evaluations. Reproduce natural primary .551816 before any gap-rule score; control masked .469149 is also checked. These are a new experiment, not reuse or restart of the exhausted old touch budget. Equal-provider primary uses 13 fitting-disjoint cases; two DFL overlaps are secondary. Natural nonregression limits are inclusive -.005 primary and -.01 per provider. Masked is reported and never gates. No new grid.

Gate failure is terminal for this gap experiment: retain controls, report and stop dependent Metrica/challenge/release execution. The observed-touch code amendment can be completed independently, but its new evaluation is deferred at the gap gate for the user's next direction.

Each later source-acquisition/evaluation stage has a separate prospective source/input seal and exclusive phase claims. Rule source/settings remain immutable after 4a. Metrica event-reference rule is committed before sample scoring: action team owns from an on-ball event until the next action team's change or a stop; same-team on-ball events chain. BALL OUT, a goal, or a foul starts D until the next SET PIECE. Before first supported action, after the covered event span, and across unsupported/ambiguous mappings use X, never inferred human labels. Exact source-type normalization/alignment is specified from the public documentation and tested before 4b scoring; no score informs mapping choices.

4c only follows successful harm gates and returns aggregates, not arrays. 4d/release require the handoff's separate user go-ahead and prospective ship decision. No submission or publication is authorized.

Inclusive harm limits use a four-ULP score-level rounding allowance only at the numerical boundary, not a scientific slack. The fixed cutoff values remain .005 primary and .01 provider. Control labels are stored privately and hash-bound, so rule comparisons do not repeat control inference. Archived source preservation compares exact Git blob identities at a5d5aa3, including the completed touch records.

Pre-score integrity requirements: a private exclusive identity binds original freeze SHA, source commit and input-map SHA; all mapped cache sidecars must be actual neighboring files consumed by the adapter. Check committed documents, source ancestry/inventory and complete old archive before phase entry. Verify all30 private labels before any rule entry/claim and retain per-use checks. Each completed aggregate is immediately written privately as an exclusive provisional receipt, retained on failure and reconciled before phase sealing. Unidentified players are excluded from the statistic; known duplicate ids remain invalid.
