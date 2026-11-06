# SDD ledger — plan: docs/superpowers/plans/2026-11-06-confidence-feasibility.md

Spec: confidence-feasibility.md, originally assigned through the contained local brief. Execute inline as assigned; no commits in this copied workspace. Coordinator owns fresh review and integration.

Ruling: Use the pre-existing isolated 138-file copy and additive hash receipts rather than git helper scripts — this workspace intentionally has no local git and frozen originals cannot change — risk if wrong: insufficient isolation, checked by the initial/final complete file hash comparison.

Ruling: Continue after recording the concrete plan because the coordinator explicitly assigned implementation and later review — no new plan approval is needed — risk if wrong: an unreviewed design, mitigated by the contained scope and later coordinator review.

Pre-flight: Task 2 consumes Task 1 confidence_feasibility results; exact statuses are provably_impossible and not_ruled_out. Model/policy errors are ValueError, serialized as CLI JSON with exit 2.

Investigation: PortableBoosted.symmetric_score=(f(x)-f(swap(x)))/2; the initial term cancels in exact arithmetic. Internal tree values are irrelevant to leaf ranges. Decoder uses per-row [-50,50] emissions, normalized forward/backward messages, then [-50,50] posterior clipping. infer_temporal divides this posterior by temperature; apply_temporal_policy clips again before sigmoid. Hard baseline H/A anchors are outside the X-row claim.

Hypothesis to falsify: B = learning_rate*sum(leaf_max-leaf_min)/2; each incoming two-state message contributes at most switch_cost, so X posterior <= min(50,min(B,50)+2*switch_cost). Published B=2.8585186401957086. Guard actual score cancellation and decoder/probability roundoff; treat equality conservatively.

Parent takeover: agent independently derived the bound, found the binary64 initial1e16 counterexample and recorded14 failing tests, then hit a service usage limit. Parent resumed from that checkpoint and watched14 missing-feature failures before implementation.

Task1 complete: outward runtime score enclosure, strict finite model/policy checks, two-message/clipping bounds, inconclusive extreme arithmetic. Fifteen API tests pass, including an additional RED->GREEN fsum-overflow regression.

Task2 complete: source-only artifact/grid CLI, strict exit1 for impossible policies, JSON input errors exit2, no file writes/dependencies. Four CLI tests RED->GREEN; Python3.11 -I -S fixed grid confirms27 impossible policies, maximum ceiling.8994398253372329.

User steering: the confidence rule is not an accuracy test; run confidence-off and direct choices empirically. Added three explicit variants on eight already-opened SkillCorner and seven seen DFL matches, with no retraining, retuning, challenge checking or local inference. These are post-hoc diagnostics, never a fresh untouched holdout claim.

Fresh review:18 API/ablation checks and34 frozen hashes independently verified. One Important missing input-receipt dependency accepted; synthetic case/cache changes reproduced stale reuse/summary acceptance, then failed closed after the fix. First complete run preserved; all15 matches rescored and aggregate results reproduced exactly under full consumed-input identities. No critical/minor findings. Declined scopes retained in confidence-additions-review.md.

Final code verification:266 tests OK,5 documented skips. All138 original publication files, original model/selector/bundle and34 frozen sources remain byte-identical. The additive preflight does not change existing prediction behavior or certify correctness. Research reports are source-only; no external code/weights imported. Publication and remote-hash verification follow separately.
