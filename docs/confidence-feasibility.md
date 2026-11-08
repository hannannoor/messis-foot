# Confidence feasibility preflight

This additive diagnostic answers one narrow question: can the configured model/decoder/temperature possibly reach its confidence threshold on a baseline-X row? It does **not** test prediction correctness. A configuration can be numerically possible and still be wrong. Correctness needs external reference evaluation, including an ungated comparison when appropriate.

The original frozen source, model, selector, standalone bundle and Desktop output are preserved. The existing selector does not automatically call this new tool. A new experiment runner should run the strict preflight before an expensive grid evaluation.

```powershell
python inspect_temporal_feasibility.py benchmark/skillcorner/frozen/temporal-selected.json
python inspect_temporal_feasibility.py benchmark/skillcorner/trained-draft.json --grid --fail-on-impossible
```

The command writes JSON to stdout. Normal inspection exits0; strict mode exits1 when at least one policy is proved impossible; invalid input exits2 with a JSON error. `--grid` inspects the original fixed27-policy draft grid, not a new policy search. There are no network calls, dependencies, model fitting, frame inputs or output-file writes.

## Derivation and a floating-point trap

For a real-arithmetic ensemble score f, the symmetric emission is `(f(x)-f(swap(x)))/2`. Half the summed leaf ranges times learning rate bounds its magnitude. Internal-node training values do not contribute. Initial log-odds cancel in real arithmetic.

They need care in actual floating arithmetic: initial1e16 with learning rate1 and leaves0/3 has real bound1.5, but the runtime symmetric score can be2.0 because addition rounds before subtraction. The tool therefore also walks outward-rounded intervals through the actual score-accumulation order. It encloses both runtime scores, then their subtraction/division. Incompatible leaf choices can make this bound loose, which is safe for disproving a gate. Nonfinite/overflowing enclosures decline proof rather than claim impossibility.

For the two-state chain, each neighbouring transition message has log-odds bounded by the switch cost. An X-row posterior is bounded by the emission plus **both** messages. Two hard A neighbours around a zero-emission X give posterior logit `2*cost`; an emission-only or one-message bound fails this synthetic case. Hard H/A rows themselves are outside the X-row claim.

The order matters: emission clip50, two messages, decoder posterior clip50, divide by temperature, then policy clip50 before sigmoid. Both positive and negative confidence branches are enclosed. A numerical allowance covers ordinary normalized-message roundoff, and equality remains conservative. Extreme scales, nonstandard floating formats and unsafe divisions return `not_ruled_out` with ceiling1. This is not a formal verification of every platform's libm; the supported binary64 behavior is falsified with synthetic/path-enumeration tests and checked under the stated Python environments.

## Meaning of the result

- `provably_impossible`: the conservative supported-runtime confidence ceiling is below the threshold on baseline X. No row satisfying those model/arithmetic assumptions can pass confidence.
- `not_ruled_out`: this bound cannot disprove the threshold. It does not show that a feature combination, eligible interval, useful prediction or accuracy target is attainable.

Player counts, valid geometry, structural periods, existing D, control anchors and gap caps can further restrict output. The bound does not establish those conditions or remove them. Source-only numerical feasibility cannot establish local live/dead correctness or hidden-turnover recall.

The published rejected artifact has real symmetric bound2.8585186402. After its transition cost and temperature, the conservative runtime ceiling remains below0.90; its selected threshold is0.975. All27 original draft policies are ruled out. The original unsuccessful experiment remains frozen; this tool neither lowers its gates nor turns it into an accepted policy.

## Verification and lineage

The agent independently derived the bound and recorded14 missing-feature failures, then hit a service usage limit. The parent completed implementation from that checkpoint. The final focused API suite includes15 cases: synthetic leaf/swap bounds, random ensembles/decoder chains, independent tiny-path enumeration, hard anchors, clipping order, cancellation, overflow, malformed models/scales and the published artifact. Four CLI cases cover strict/grid behavior, invalid JSON, input immutability and isolated stdlib execution. The separate confidence-removal experiment has its own tests and evidence receipts.

Research reports and the follow-on code live in an isolated copy of commit79a467aa. A complete hash receipt verifies the138 original files and34 frozen sources remain unchanged. No third-party code or weights were copied. [GitHub research summary](github-research-summary.md) explains the next method leads and their limitations. [Confidence-removal results](confidence-ablation.md) records the user's empirical question separately from this mathematical preflight.
