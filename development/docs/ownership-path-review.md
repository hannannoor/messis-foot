# All-state diagnosis review and resolution

9 November 2026. One fresh-context `gpt-6-astra` review examined `8c7be9d..e9f6474` using the Superpowers whole-change reviewer template. This was a separate agent/model review, not an independent provider council. It read source, synthetic tests and bounded receipts, without opening private arrays, challenge data or public-window outcomes. Its verdict was **With fixes**; no Critical issues, five Important issues and four Minor issues. All material fixes were made in one RED-to-GREEN pass; there was no re-review.

## Important findings resolved

1. **Summary egress and hash-key validation.** Deterministic canonical summary bytes now must match exactly; duplicate-key shadow arrays and Boolean/integer equality cannot pass. Case schema validation takes the trusted expected input-hash map instead of deriving allowed keys from the untrusted receipt. `test_summary_shadow_arrays_and_boolean_counts_are_rejected` and `test_case_hash_keys_and_prefreeze_release_runtime_drift` demonstrated the failures before the fix.
2. **Observed-interior evidence and memory denominators.** Every fixed stratum now reports supported errors by family and local emission sign, usable/unusable support and reference-state denominators. Memory association is counted only on H/A ownership swaps with an evaluable H/A memory. It no longer counts every retained owner as opposed to reference D. `test_observed_interior_emission_and_swap_memory_cross_tabs` pins twenty literal interior swap rows and excludes D errors from the memory denominator.
3. **Original H/A queries and agreements.** The original reference-owner versus opposite-owner query now covers every supported known-live row, including rows actually predicted D. Actual-state H/A/D attribution remains separate. Both legacy queries and H/A/D agreement rows retain prefix-before/local/future/emission/switch/full components and explicit relative-tolerance numerical-tie counts. Absolute `near_zero` bins remain distinct. `test_legacy_HA_queries_include_false_D_and_agreements_retain_decomposition_ties` covers false D, end-attached forced runs and relative ties outside the absolute bin.
4. **All-state boundaries.** Destination-matched all-state boundaries and supplementary pair-matched H/A boundaries both report counts and conditional latency at 12/25 frames. Each valid period/run is matched separately before pooling counts and latency samples. `test_all_state_boundary_destination_matching_and_run_separation` pins a literal three-reference/one-predicted/one-matched example and official per-run helper parity.
5. **Complete replay identity.** All five historical WCSF IoU counts/F1s and mean F1 are checked before deeper queries/repairs. Executed component bytes must match the manifest embedded in the pinned release artifact, including persistent edits made before freeze. Actual runtime metadata must equal the frozen environment at run/verification. The historical-IoU and component/runtime drift tests reproduced the gaps before the fixes.

All 27 ownership tests pass after the fix pass. The first full suite was 510 tests, 19 environment skips; the final suite after these six added tests passes 516 tests with 19 environment skips (497 executed), including all 27 release tests, as recorded in the [verification receipt](../reports/ownership-path/verification.json). It uses native Windows link permissions, local temporary storage and the pinned official code-only fixture. It does not reopen the public reference window.

## Preserved generations

`2026-11-09-natural-v1` remains byte-for-byte intact and is superseded for diagnostic interpretation. Its original read-only verification passed before the fixes. Its code checkpoint is `f7c802b`, with source freeze committed at `d0d2811`; verification of that generation requires those frozen sources in a sibling checkout sharing the original retained stores. The current runner deliberately rejects old-source drift rather than pretending v1 was produced by current code.

`2026-11-09-natural-v2` prospectively freezes the corrected source checkpoint `e93d86e`; freeze commit `986fc94` precedes its computation. Each generation has five reconstructions, five baseline reconciliations and ten reference-only repair evaluations. Across this work that is ten reconstructions, ten baselines and twenty repairs. The second generation repeats the same fixed arrays/methods to supply missing measurements; it adds no candidate, parameter search or oracle variant. Both access logs, traces, receipts and freezes are retained. No historical WCSF attempts/access log was appended.

## Deferred minor findings

- More explicit all-D zero-denominator documentation/tests: the current official spell and boundary convention yields zero for known no-spell/no-boundary support; all-X spell support yields null. The retained WCSF reporting wrapper uses null for some unsupported ratios. None of the five baseline spell denominators is zero.
- Precision at enormous common offsets in the generic path helper: reconstructing absolute scores can lose small differences near `1e16`. This task uses the frozen model's bounded log-emissions. Arbitrary finite magnitudes are not certified.
- Additional literal negative-delta/unequal-half tests: the reviewer independently checked a deliberately unequal-half example and obtained pooled F1 .4. Existing toy matching/count checks and the recorded negative signed repair remain, but further literal test polish is deferred.
- Reference-access flag authentication: verification checks event order, case membership and method counts. It logs reference-access flags honestly but does not independently authenticate those flags. Do not read its chronology claim as stronger physical-isolation proof.

## Review exclusions and parent rulings

- Private contents/direct replay were excluded from independent review. The parent checks actual frozen replay and private container/semantic hashes. Cost: this is author verification rather than independent annotation adjudication.
- Public-window outcomes/hidden challenge performance remain excluded. Cost: hidden performance is unknown.
- Physical-control truth, causal memory effects and future predictor gains remain unresolved. Cost: the next hypothesis may fail.
- The parent completes preservation, final regression, publication and this record. Cost: these operational checks are author verification rather than a second independent review.
- Cross-platform certification and an attacker controlling the checkout and all private anchors remain outside the stated Windows replay guarantee. Cost: those environments/threats are not assured.

Earlier planner rulings also stand: reuse the existing isolated clone sequentially (no concurrent editing isolation); exclude latent-X carry from both repairs (unsupported headroom is unmeasured); retain cache loaders that parse reference containers before inference (physical acquisition isolation is limited while pure inference functions remain reference-free). The private ledger preserves every ruling and every failed/passing test log.
