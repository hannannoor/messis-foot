# Read-only ball-gap diagnosis — 7 November 2026

The existing frozen tactical tree and w0-c32 decoder were replayed on two already-used SkillCorner development matches (1874553 and 1886347), scored against their external known-play reference. No alternative candidate was scored, no model was fitted, and no challenge inputs, challenge GT or video were used. The design's validation and regression sets were not used for this reproduction.

| Inputs | Known-live frames, pooled | False D | False-D rate | False D with missing ball |
| --- | ---: | ---: | ---: | ---: |
| Natural | 161785 | 475 | 0.2936% | 399 |
| Frozen 30% ball mask, seed 1729 | 161785 | 15402 | 9.5200% | 15221 |

In the masked runs, 98.8248% of false D frames had a missing ball coordinate. These are pooled development counts, not per-match mean accuracy. The missing-ball subset includes natural gaps as well as the added mask. Some false D occurs on observed-ball frames too, so removing missing-slot evidence cannot be assumed to eliminate all false stops.

The source trace identifies a direct mechanism: missing observations append zero speed, and the 12-frame recent-speed window eventually becomes zero. The tactical tree sends that feature value down its low-speed branch. Once remembered possession is stale, a reachable leaf assigns approximately .835 support to D. Repeated leaf scores then accumulate in the temporal objective despite there being no new ball observation. Leaf support is not calibrated correctness probability.

This is evidence for testing neutral missing-slot emissions; it is not yet evidence that the proposed correction improves accuracy. Neutralization can miss a real stoppage wholly hidden in a gap, preserve an incorrect surrounding state, or leave an ambiguous transition time. SkillCorner provides known-play H/A reference only and cannot measure recovery of genuine D. The proposed comparison therefore includes the existing full-state DFL reference, with its known inactive-coordinate shortcut disclosed.

Reproduction used `load_motion_cache`, the unchanged `feature_rows` and portable tree's float32 split convention, the existing `contiguous_mask`/`mask_motion_frames`, `sequence_usable`, `soft_emissions(weight=0)`, `decode_soft(switch_cost=32)` and the unchanged structural carry. Player association is unnecessary for this diagnostic: the tactical features and eligibility point counts do not use player IDs. The consumed cache/source SHA256 identities, per-match/regime counts and bounded leaf-count summaries are in `reports/ball-gap/diagnosis.json`. Its public shape passed the existing strict aggregate validator. No coordinates, per-frame labels, masks or event locations are included.

The single proposed intervention and prospective acceptance rules are in `docs/superpowers/specs/2026-11-07-ball-gap-evidence-design.md`. The fresh read-only builder check returned “nothing important left.” Implementation is pending approval of that design; existing candidates and Desktop files remain preserved.
