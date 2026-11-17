# Independent competitor audit — reviewer 3

## 1. Scope, position and limits

I reviewed the latest progress at open PR #1, commit `cee674190775e9356745f461ba1561e9f2a46f7e`, rather than judging the older default branch. The supplied audit workspace is reported to match all 309 tracked GitHub blob hashes. My evidence comes from the current rules, actual adapters and inference code, frozen model, experiment protocol, aggregate receipts and primary results. I did not read other council outputs or earlier neutral/strategy/code-review audits, change project source, acquire data, train models, inspect challenge footage or consult challenge ground truth.

I ran two small, standard-library synthetic probes against the actual selected inference components: long neutral-gap decoding and team-swap consistency. These establish implementation behavior, not football accuracy. I also inspected the published numerical receipts. I did not rerun the full suite, independently regenerate the external benchmarks from raw inputs, or validate their provider labels. The parent reviewer is handling the main suite.

My competitor's argument would be: **this is a careful experimental software package, but its strongest reproducible property is preserving and explaining its own experiments; its weakest property is proving that the chosen possession decisions transfer to the competition.** That criticism survives the honest caveats. However, the caveats mean it would be unfair to accuse the authors of claiming measured target accuracy, using forbidden target labels, or presenting rejected temporal research as a successful deployment.

Severity below concerns competitive consequence, rather than security or data-loss risk.

## 2. High severity / high confidence: the evaluation runway has been consumed

**Type: demonstrated evidence limitation.**

The current selection uses one DFL and two SkillCorner matches; regression uses two DFL and eight SkillCorner matches. Their identities are hard-coded in [accuracy_protocol.py:7–11](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/gap_solver/accuracy_protocol.py#L7). All were previously examined. The current report explicitly acknowledges that repeated development can overfit project decisions without refitting a head: [ball-gap-results.md:38–40](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/docs/ball-gap-results.md#L38).

Freezing the next patch before rescoring the same matches protects against changing that patch after seeing its score. It does not erase the fact that those matches helped reveal which patch to propose. Repeated diagnoses, reference searches and selection criteria adapt the project to the cohort at the project level.

The latest incremental natural-input result is also much smaller than the dramatic missing-ball headline: equal-provider spell F1 moves **.564642 → .566428**, DFL is unchanged, and SkillCorner accuracy moves **85.82% → 85.93%**. The masked gain is substantial, but it answers a different question. See the actual [results table and means:13–22](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/docs/ball-gap-results.md#L13).

**Competitive consequence:** I would challenge every inference from “passed all checks” to “likely wins on unseen input.” Your fresh external evidence budget is effectively empty; test counts and hashes cannot replenish it.

**Better alternative and acceptance:** stop promoting new empirical accuracy claims from this cohort. Obtain a licensed, untouched cohort and freeze the complete pipeline and analysis before opening its labels. Report paired match-level uncertainty, all per-match deltas and relevant missingness strata; avoid treating hundreds of thousands of adjacent frames as independent observations. Require a predeclared primary improvement with uncertainty narrow enough to support the claim. If fresh data remain unavailable, retain “experimental” status and prioritize structural correctness over another score-driven selection cycle.

## 3. High severity / high confidence: neither provider independently tests your full intended problem

**Type: evidence-backed transfer limitation, not direct label leakage.**

The model's most decisive tree split is on recent ball speed, and its artifact records that inactive DFL ball coordinates repeat on **99.9993%** of contiguous inactive frames. It also records that the old active-only diagnostic spell score regressed on both held-out matches: [tactical_model.py:229–238](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/gap_solver/tactical_model.py#L229).

SkillCorner supplies known-play H/A phases, with missing annotation preserved as X, rather than a complete independent D reference. The adapter's contract makes this explicit: [skillcorner.py:195–200](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/gap_solver/skillcorner.py#L195). Its near-zero false-D result measures avoiding D during known live play; it cannot establish recognition of real stoppages in unlabelled regions.

This is not inference code reading BallStatus or reference possession. The problem is **provider convention acting as an easier surrogate for the physical event**. Two providers do not automatically produce two independent full-state validations. Equal weighting averages different evidence gaps; it does not close them.

**Competitive consequence:** a competitor with a less impressive DFL score but independently verified stoppage recognition could have a more transferable system. You cannot establish that your excellent D recall is measuring the same mechanism needed on ATD.

**Better alternative and acceptance:** separate live/dead validation from team-owner validation. Use fresh external full-state labels for both, or explicitly leave the unsupported claim open. Run frozen-coordinate removal, plausible stationary-live-ball, moving-dead-ball and stale-coordinate stresses externally. A credible live/dead improvement should survive removing the provider's coordinate-freeze convention while preserving team-spell quality. Do not replace this with manual challenge-game annotation; [RULES.md:7–22](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/RULES.md#L7) forbids the relevant target-ground-truth shortcuts.

## 4. High severity / high confidence: neutralizing a gap does not recover its possession history

**Type: demonstrated algorithmic limitation; target frequency and accuracy impact unmeasured.**

The new fix correctly removes spurious evidence: missing-ball emissions become equal zeros. But a usable segment is rejected as wholly unsupported only when **none** of its rows has a ball observation. There is no maximum neutral-gap duration within an otherwise supported segment: [ball_gap_policy.py:14–24](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/ball_gap_policy.py#L14). Three available player points on each team can make a missing-ball frame usable, even though the selected policy has motion weight zero: [soft_sequence.py:6–9](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/gap_solver/soft_sequence.py#L6).

I passed the real decoder 20 strongly H observations, **2,500 neutral missing rows**, then 20 strongly A observations, all within one usable period. It returned **2,520 H rows followed by 20 A rows**, with the switch exactly at reacquisition. Unsupported-segment counts were zero. That 100-second gap could contain turnovers and stoppages; the inputs provide no information locating them. The selected method therefore supplies a precise boundary through deterministic path/tie behavior, rather than recovered events.

This differs from ordinary latent-X materialization. Those neutral rows already receive latent H, so `latent_unknown_active` and `materialized_active` do not count them as unknown or carried. The dedicated `neutralized` column does expose them; I acknowledge that transparency: [ball_gap_runtime.py:52–62](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/ball_gap_runtime.py#L52).

A second probe confirmed that a wholly unknown period materializes entirely as D, exactly as documented in [materialization_control.py:12–18](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/gap_solver/materialization_control.py#L12). This can be a legitimate scorer convention; it is not an independent stoppage detector.

**Competitive consequence:** I would target “hidden recovery” claims with gaps containing opposing possession between identical endpoints, or several changes between different endpoints. Your current zero-motion correction cannot infer those events from nothing.

**Better alternative and acceptance:** preserve evidence-age and boundary-location uncertainty separately from final scorer-compatible labels. Externally compare duration-limited propagation, explicit unknown intervals and a motion-informed or duration-aware alternative. Require gap-stratified hidden-spell recall and false-spell counts; include gaps longer than ten seconds and distinguish inferred ownership from merely serialized ownership. Keep a deterministic baseline when new evidence is absent, but describe it as a prior.

## 5. Medium severity / high confidence: the selected pipeline has avoidable home/away bias

**Type: demonstrated symmetry failure; real-world error magnitude unmeasured.**

The decoder can be equivariant when scores are swapped and its optimum is unique, but the frozen tactical head is asymmetric. The repository admits this in [accuracy-first-results.md:36–38](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/docs/accuracy-first-results.md#L36). The issue remains in the latest candidate because it uses that same head.

I constructed 120 observed frames with a ball moving at 1 m/s, home nearest distance 2.5 m and away nearest distance 4 m. The selected core path returned H for all 120 rows. Swapping the two distances and rerunning returned **H for all 120 again**. The final support vector was identical in both cases: approximately **(.687875, .310736, .001389)**. This is a repeatable metamorphic failure, not a measured match accuracy estimate.

For this geometry, the feature history has no confirmed close owner. The head nevertheless assigns a strong preference to one team role. The tree uses team-specific histories and distances: [tactical.py:35–63](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/gap_solver/tactical.py#L35).

**Competitive consequence:** a challenger can ask whether successful ownership recognition follows geometry or provider/team-role priors. You currently cannot guarantee consistent behavior under simple role exchange.

**Better alternative and acceptance:** test the complete pipeline under team exchange, using physically valid external sequences. Compare symmetric training augmentation, a relative-feature head, or averaging original and reversed head supports before decoding. Preserve a separate policy for exact ties rather than silently assuming unique optima. Acceptance should include end-to-end label exchange on unique-optimum fixtures and no material degradation on fresh per-team spell scores. Do not tune a compensating home/away bias on the challenge match.

## 6. Medium severity / high confidence: current gates reward smoother possessions while allowing more genuine changes to disappear

**Type: demonstrated tradeoff plus objective-governance limitation.**

The latest policy increases missed changes:

- Natural SkillCorner: **752 → 758**.
- Masked SkillCorner: **921 → 953**.
- Masked DFL: **632 → 645**.

Boundary F1 improves because false cuts fall faster. Those are legitimate primary-score tradeoffs, disclosed in [ball-gap-results.md:32–36](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/docs/ball-gap-results.md#L32). The acceptance function, however, has no missed-transition, short-possession or worst-match constraint; it checks aggregate primary/frame metrics and selected D measures: [ball_gap_experiment.py:97–116](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/ball_gap_experiment.py#L97).

One masked DFL match loses about .00998 spell F1 versus the previous candidate, while aggregate checks still pass: [post-review-diagnostics.json:117–124](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/reports/ball-gap/post-review-diagnostics.json#L117).

**Competitive consequence:** “better possession” remains ambiguous. The official metric rewards complete team spells, so optimizing it is rational; calling fewer spurious cuts “better recovery” would overstate the result when hidden or short real possessions increasingly vanish.

**Better alternative and acceptance:** retain the ranking metric as primary, but predeclare secondary diagnostics by possession duration, missingness and team. Compare duration-aware transition models with the uniform 32-point switch penalty. Require a justified cap on hidden/short-spell recall losses, or explicitly accept and name the tradeoff. Never add a veto retrospectively to reject an inconvenient outcome; freeze it for the next independent experiment.

## 7. Medium severity / high confidence: the main stress test is easier to characterize than the actual observation failure

**Type: evidence-backed robustness gap.**

The current intervention is tested with one deterministic 30% contiguous mask using seed 1729. Mask lengths are drawn from **5, 15, 50, 125 and 250 frames**: [temporal_selection.py:37–48](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/gap_solver/temporal_selection.py#L37). This tests deleted coordinates. It does not make a surviving finite coordinate wrong, stale or delayed.

Actual input freshness is explicitly unverified; the target audit records 85,831 player-without-ball rows and 7,823 rejected homographies: [tactical-audit.json:26–45](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/reports/input-contract/tactical-audit.json#L26). Those are automatic input diagnostics, not permission to select thresholds on this match.

SkillCorner interpolation also uses provider player identities before anonymous matching: [skillcorner.py:171–193](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/gap_solver/skillcorner.py#L171). Anonymous association afterwards does not undo that smoother upstream information.

**Competitive consequence:** your method may look robust to absence while remaining brittle to false presence—the dangerous case for a speed-driven head.

**Better alternative and acceptance:** add externally designed stale/frozen detections, time shifts, sparse opposition, coordinate jumps and long-gap regimes, with multiple fixed seeds. Evaluate a native-rate or identity-free resampling ablation. Report paired score distributions and coverage by corruption type. Require survival of these tests before treating the current ball-gap correction as general observation robustness.

## 8. Lower severity / high confidence: release complexity now exceeds what the selected method needs

**Type: demonstrated delivery/reproducibility limitation, not a broken inference claim.**

The README foregrounds a single-file tactical route while the latest experimental policy has a separate entry point and checkout dependencies. Its runtime always loads the temporal artifact and generates four comparators before selected zero-motion inference: [ball_gap_runtime.py:38–43](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/ball_gap_runtime.py#L38). Scientific comparison justifies preserving these outputs; mandatory comparator work need not be a permanent deployment dependency.

Exact benchmark replay requires private intermediate archives under recorded sibling paths and instructions for a clean copy: [ball-gap-results.md:44–66](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/docs/ball-gap-results.md#L44). Public hashes prove identity once those artifacts exist; they do not regenerate missing intermediates.

**Competitive consequence:** another team can deliver a smaller, clearer final route and demonstrate fresh-clone reproducibility with less operator knowledge. Your documentation's preservation discipline also imposes cognitive cost.

**Better alternative and acceptance:** after scientifically choosing a final policy, package one documented production inference path and make comparators optional. Provide a clean external-data rebuild recipe from licensed sources through final receipts, plus time/memory measurements. Verify in an isolated fresh checkout without unpublished folders. Keep the historical package available for audit.

## 9. Prioritized improvement sequence

1. **Immediately:** add the long-gap and whole-pipeline team-swap probes to the scientific checklist; correct any interpretation that treats all latent H/A/D as equally evidenced. Keep the present artifact frozen.
2. **Before more tuning:** secure fresh full-state external evidence and freeze the next decision protocol. If unavailable, state that the empirical promotion question remains unresolved.
3. **Next bounded engineering experiment:** address team symmetry and stale/long-gap handling, with feasibility checks before costly grids. The earlier 27-policy temporal grid was structurally unable to add labels; that documented lesson in [TEMPORAL_RECOVERY.md:13–17](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/TEMPORAL_RECOVERY.md#L13) should become a general preflight requirement.
4. **Independent evaluation:** report official spell scores, complete live/dead validity, hidden/short-spell behavior and uncertainty together. Do not infer superiority from higher assignment coverage.
5. **Finally:** consolidate delivery, benchmark runtime and perform a fresh-clone reproduction.

I would not start by expanding OCR, adding another ensemble, or forcing zero unknown output. Those may eventually help, but your immediate competitive weakness is the gap between precise, reproducible labels and independently supported possession recovery.


