# Ball gaps, touch evidence and the pose question — findings and plan, 10 November 2026

This folder records a planning and measurement pass. **It changes no predictor, no release artifact and no earlier evidence.** Nothing here is a competition score. The frozen control `w0-c32-neutral-missing` remains the only submission candidate until the work described below is built, checked and approved.

## What was done

1. Both repositories were re-read. The official repository is unchanged at `f8f2629`. This branch starts from `431d1ec`.
2. A direction was chosen for the remaining days: treat "what the ball should do next, and where it does something else" as evidence of touches, and feed that into the existing decoder, instead of building a second model or an ensemble.
3. Four label-free probes were run locally on the challenge tactical tracking, homography and automatic Smart Tagging. Only aggregates were read back and only aggregates are stored here. No ground truth, public or private, was used. No video frame was viewed.
4. The probes showed that the larger problem on this match is how long missing-ball gaps are labelled. A gap rule was designed and approved for implementation.

## Findings

All figures are in [probe-results.json](probe-results.json); the scripts are in [probes/](probes/).

**Pose estimation is dropped.** Estimated standing player height in the tactical image has a median of about 51 px (5th–95th percentile 39–72 px). The estimate uses the homography's local scale and ignores camera elevation, so it leans high. That is too small for reliable lower-limb keypoints. Estimated ball diameter has a median of about 6 px.

**The ball is missing in long blocks.** On graded frames there are 150 gaps. The median gap is 268 frames (about 11 s). 85% of the 64,643 missing-ball frames lie in gaps longer than 10 s and 0.1% in gaps of one second or less. The observed-ball share reproduces the organisers' published 59.3%, which checks the parsing.

**Long gaps are disproportionately stoppages.** 79% of the 58 graded `SET PIECES` tags start inside a long gap or within 3 s after it, against 47% expected by chance. Open-play phase tags (`PROGRESSION`, both transition codes, `DEFENDING IN MIDDLE THIRD`) start there about 17% of the time. Typical player speed is lower inside gaps than outside (per-gap median 1.03 m/s for tagged gaps and 1.26 m/s for untagged gaps, against a frame median of 1.65 m/s outside gaps). About a quarter of untagged gaps have players moving at ordinary match speed, and box and final-third tags start in gaps about as often as chance, so some gaps are live play.

**The frozen control paints over the gaps.** It predicts D on about 4% of long-gap frames and about 2% of other graded frames. Of 133 gaps longer than 3 s, 127 receive a single owner label equal to the label on both sides. Where the gap is a stoppage, that merges two possessions and the stoppage into one spell.

## Decisions

| Item | Decision | Document |
|---|---|---|
| Pose and skeleton features | Dropped on measured size | this file |
| Large learned world model, new neural network | Not attempted | [handoff](TOUCH-EVIDENCE-HANDOFF-2026-11-10.md) |
| Touch evidence from ball-motion surprise | Build and test on external matches under a fixed 12-setting grid and a 0.04 spell-F1 acceptance gate | [handoff](TOUCH-EVIDENCE-HANDOFF-2026-11-10.md), [addendum 1](TOUCH-EVIDENCE-ADDENDUM-1.md) |
| Long-gap dead-ball rule | Build first; fixed constants, nothing tuned; harm-checked externally | [addendum 2](GAP-RULE-ADDENDUM-2.md) |
| Video ball recovery | Parked; proposal only, after the above | [handoff](TOUCH-EVIDENCE-HANDOFF-2026-11-10.md) |
| Camera fusion, TCN pilot | Unchanged: not part of the candidate | earlier documents |

Addendum 1 corrects the handoff: the original design carried a last-toucher bonus through missing-ball frames, which the gap measurements show would be wrong on this match.

## Limits

- The gap findings are associations between automatic tracking and automatic tags on one match. They are not measured against labels and do not establish how many gaps are stoppages.
- No clean labelled validation exists for the gap rule. The external matches do not show this gap pattern; the open Metrica sample matches drop the ball mostly during dead play in manually corrected data, so a test there is partly circular. The planned checks can catch harm and cannot prove a gain.
- The public five-minute window was not consulted and will be used once, for correctness only, after the ship decision is recorded.
- Counts differ slightly between probes: `probe_gaprule.py` reads frames through the release loader and finds 65,929 frames in long gaps, more than the 64,643 raw missing-ball frames counted by the other probes. The cause was not investigated. It does not change any reading above, and the implementing work should reconcile it.
- `probe_gaps.py` returned no player-speed samples because ids are empty before association; its other outputs are unaffected and `probe_gaprule.py` measures speed after association.
- Thresholds quoted in the findings (1.5 m/s, 3 m) are descriptive cut-points for reporting. The gap rule does not use them; it compares each gap with the match's own median speed.
- Dataset and detector notes (Metrica sample data, WASB-SBDT, SoccerTrack v2) were checked on 10 November 2026 from their public pages and are recorded in the handoff and addenda only as leads.

## Reproducing the probes

The probes need the enrolled data bundle, which is not redistributable and is not in this repository. From the repository root, with the pinned interpreter of the frozen release:

```
python -I docs/gap-and-touch-2026-11-10/probes/probe_size.py . "<folder holding BAR-ATH_tactical_* files>"
python -I docs/gap-and-touch-2026-11-10/probes/probe_gaps.py . "<same folder>"
python -I docs/gap-and-touch-2026-11-10/probes/probe_sp.py . "<same folder>"
python -I docs/gap-and-touch-2026-11-10/probes/probe_gaprule.py . "<same folder>"
```

Each prints one JSON object of aggregates. None writes a file or prints per-frame data.
