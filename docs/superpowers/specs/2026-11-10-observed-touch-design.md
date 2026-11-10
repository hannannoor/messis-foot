# Observed-only touch evidence — addendum 1, 10 November 2026

Status: new design brief; no new touch scoring authorized to precede the gap-rule checks. The user authorized applying both addenda. Preserve the complete prior experiment at a5d5aa3, including all source, frozen protocols, results and seals. Use separate additive modules and a new run registry for this amended hypothesis.

# Addendum 1 to the touch-evidence handoff — 10 November 2026

This amends `TOUCH-EVIDENCE-HANDOFF-2026-11-10.md`. Where the two disagree, this file wins.
If you have already written code or frozen a protocol under the original text, stop and tell the user before changing anything; do not silently amend.

## A. Stage 0 is done — do not rerun it

The orchestrating chat ran both probes locally on the challenge tactical tracking and homography, reading back aggregates only. Sanity check: the observed-ball share on graded frames came out at 59.31%, matching the organisers' published 59.3%.

Apparent size (homography scale at tracked positions, every 5th graded frame, 620,122 player samples):

| Quantile | 5% | 25% | 50% | 75% | 95% |
|---|---:|---:|---:|---:|---:|
| Estimated standing player height, px | 39 | 46 | 51 | 59 | 72 |
| Estimated ball diameter, px | 4.6 | 5.4 | 6.3 | 7.6 | 9.2 |

These are upper-leaning estimates (they ignore camera elevation).
**Pose decision: dropped.** Median player height is about 51 px, under the 100 px rule fixed in the handoff. Record it in the technical document as considered and dropped.

Ball-track shape on graded frames:

- 149 observed-ball runs and 150 gaps. Median run 345 frames (about 14 s); no run shorter than 11 frames.
- Median gap 268 frames (about 11 s); 95th percentile 1,278 frames (about 51 s).
- Of the 64,643 missing-ball frames, **85.2% lie in gaps longer than 10 s**, 14.6% in gaps of 3–10 s, and 0.1% in gaps of 1 s or less.
- A tracked player is within 2.5 m of the ball on 59.1% of observed frames.

Label-free comparison with the automatic Smart Tagging (an allowed input; no ground truth was used):

- "Gap zone" = inside a gap longer than 3 s, or within 3 s after it ends. It covers 46.6% of graded frames.
- 79% of the 58 graded `SET PIECES` tags start inside the gap zone, and 3 of 4 `GOALS`.
- Clear open-play phases start there far less often than chance: `PROGRESSION`, `ATTACKING TRANSITION`, `DEFENSIVE TRANSITION` and `DEFENDING IN MIDDLE THIRD` are each at about 17%.
- `BALL IN THE BOX` and `BALL IN FINAL THIRD` start there about as often as chance (46–47%).
- Only 34% of long gaps contain a set-piece tag; the tags are incomplete, so this does not bound how many gaps are stoppages.

Reading: on this match the ball does not flicker in and out. It disappears in long blocks that are disproportionately stoppages and restarts, with some live play near goal mixed in. This is an association from automatic tags, not a measurement against labels.

## B. Changes to the design

The handoff assumed short occlusion gaps. That assumption is wrong for the challenge match, so three rules change:

1. **No bonus on missing-ball frames.** The last-toucher bonus ends at the first missing-ball frame after the touch (as well as at the next touch, the period end, or 10 s). Missing-ball rows keep exactly the control's neutral emissions. Reason: carrying an owner for up to 10 s into a gap that is probably a stoppage would lengthen and merge spells.
2. **Drop the `reacquire` touch kind.** Extrapolating a pre-gap velocity across an 11-second gap is meaningless. After the ball reappears, touches are detected only by the ordinary kink rule once 5 observed frames exist on both sides.
3. **Touch state resets at every gap** of any length, as it already does at period boundaries.

Test changes:
- Test 7 becomes: a gap followed by reappearance anywhere emits no touch at the reappearance frame; a kink at least 5 frames after reappearance is detected normally.
- Test 13 becomes: the bonus is absent on every missing-ball frame and does not resume after the gap without a new touch.
- Add test 13b: on a sequence where every touch is followed by a gap, candidate emissions on missing-ball rows are bit-identical to the control's.
- Parity tests 11 and 12 are unchanged.

The `jitter` regime, grid, split, gates and budget are unchanged.

## C. Not in scope: how to label long gaps

The control gives neutral evidence inside gaps, so the decoder carries whatever label preceded the gap. If most long gaps are stoppages, that is a large error source on this match, and possibly the largest. Do **not** act on it in this goal:

- There is no clean external test. The DFL, SkillCorner and WCSF matches do not have this gap structure, the random-mask regime is unrelated to stoppages, and the Metrica sample matches drop the ball partly by convention during dead play.
- Checking the idea against the public 5-minute ground truth would be tuning on it, which the rules forbid.

Report anything you notice about gap behaviour to the user. A gap-labelling rule needs its own plan and the user's approval.

## Additive implementation route

Use a new observed-touch module beside the historical touch modules. It may reuse the historical detector's within-run kink events, excluding every reacquisition event; kinks already require five observed intervals on both sides. Build bonuses in a new function that receives observed flags, clears the active owner at every missing row, enforces exact neutral missing emissions and never resumes without a new attributed kink. Reuse the existing constant/variable-cost decoder and frozen feature generator. No prior source file is edited, and no old scores are reused as new scientific outcomes.

The old budget is exhausted; the approved amendment requires a separately committed grid/split/seeds/gates before any new touch scoring. The gap goal takes precedence. Do not rerun the challenge probes. The supplied size estimate (~51 px) and earlier planar-width proxy (~22 px) have distinct measurement conventions; both drop pose under 100 px, and neither receipt is to be rewritten.
