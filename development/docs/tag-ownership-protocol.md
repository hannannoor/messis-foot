# Tag-ownership protocol, 10 November 2026

Branch `codex/tag-ownership-2026-11-10`, from head `46b516e`. This note restates the fixed design and the three runs before run 6.1.

## Design (no changes after any result)

1. Tag owner track: instances with code in {BUILD UP, PROGRESSION, CREATING CHANCES, ATTACKING TRANSITION, LONG BALL} and a `Team` label other than N/A. An instance covers frames `round(start*25)` up to but not including `round(end*25)`. A frame's owner is the single team whose windows cover it; none if zero or both. Graded periods only.
2. Mapping and reliability measured from the match: confident frames are graded, ball-observed frames the control labelled H or A whose margin (emission of its label minus the other owner's) is at or above the 75th percentile of that margin over all such frames (nearest rank, `ceil(0.75 n)`-th smallest). Among confident frames with an owner, `a` is the share where "first sorted team name = H, second = A" agrees with the control. First name maps to H if `a >= 0.5`, else A. `p = max(a, 1-a)` capped at 0.95. Tags are disabled when fewer than 2,000 such frames, `p < 0.65`, or the tags do not name exactly two teams.
3. Fusion: on frames with an owner add `ln(2p)` to the mapped side and `ln(2(1-p))` to the other side; D is unchanged. Decode with `decode_soft` at switch cost 32 over the control's own usable mask, then materialise as the control does.
4. Then `apply_gap_rule` and the kickoff patch, as `gap_release.py` does.

## Runs, once each, in this order

- **6.1** 15 external matches, natural tracking: reproduce the control's primary spell F1 0.551816, then report the share of confident frames whose control label equals the reference label (frames with known reference), per provider and as the equal-provider primary mean over the 13 fitting-disjoint matches. Gate: primary mean at least 0.75, otherwise stop.
- **6.2** Simulated tags from the reference labels (a mechanism test, not a prediction for the provided match). 440-frame windows over each graded period, indexed by one running `k` from 0 across periods (so that the two halves do not share hash keys); selected when `int(sha256(f"{match_id}:{k}").hexdigest(),16) % 100 < 42`; team = strict majority reference owner among H/A frames (a tie or none gives no tag); flipped when `int(sha256(f"flip:{match_id}:{k}").hexdigest(),16) % 1000 >= 1000*q`, for q in {0.9, 0.7}. Team names are neutral labels assigned by a hash of the match id, so the mapping is not trivially sorted. Fused labels (before the gap rule) are scored. Gates on the primary mean: q=0.9 fused not below control; q=0.7 fused not more than 0.005 below. Budget 15 control and 30 fused scores.
- **6.3** The provided match, one run, aggregates only, with the stop conditions of the brief.

No tuning; a rerun only for a demonstrated code defect, which is reported.
