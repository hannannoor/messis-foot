# Gated and ungated aggregation —7 November2026

The user's proposal was implemented as three explicit combinations, with the learned models unchanged. The strongest tested combination keeps existing H/A/D decisions and fills X only when the motion H/A prediction and older H/A/D head agree on the same team. Agreement is a rule, not a calibrated probability or evidence of independent errors.

| Eight SkillCorner matches | Mean X | Frame accuracy | Team-spell F1 |
|---|---:|---:|---:|
|Existing baseline|25.67%|66.40%|0.4690|
|Direct temporal H/A fill, previous experiment|0%|85.33%|0.4491|
|Keep baseline + raw older H/A/D fallback|0%|83.28%|0.4122|
|Keep baseline + two-head H/A agreement|7.37%|81.04%|0.4785|
|Agreement plus original support/anchor/2s guards|22.56%|68.78%|0.4692|

The agreement rule improves both frame accuracy and mean possession-spell quality while retaining uncertainty. SpellF1 improves on7 of8 matches; the remaining change is−0.003277. Newly emitted H/A agreement is80.85%/79.73%, so it is not a90%-precision recovery method. It adds111960 measured team labels and110133 labels outside known phase reference, whose correctness is unmeasured.

On seven **seen** DFL matches, the same agreement rule changes mean spellF1 from0.5091 to0.5260, X from10.21% to1.27%, and frame accuracy from85.16% to91.65%. Newly emitted H/A agreement is67.02%/74.56%. These data include the known frozen-inactive-coordinate shortcut.

These are post-hoc comparisons on already-opened cohorts, not fresh validation. SkillCorner reference supports known-play H/A, not independent full-state/stoppage correctness. Both heads share tracking features and can agree while wrong. No local predictions or default were replaced. The result identifies a candidate for a new evaluation, not a validated final submission.

## What changed based on the findings

- The failed calibrated candidate led to a source-only feasibility preflight. It detects impossible gates; it does not test correctness or alter the frozen selector.
- The user's confidence-removal proposal led to an actual three-variant external diagnostic. Raw frame accuracy improved markedly while spell quality could decline. Those metrics are now reported together.
- The user's aggregation proposal led to the three rules above. Existing decided labels are preserved; X is not treated as an agreeing vote, and label codes are never averaged as numbers.
- A fresh code review found missing unmeasured-D counts. The driver now counts new H/A/D outside reference separately. Raw fallback adds317877 D assignments outside SkillCorner phase support; none is silently called correct.
- Receipt completeness and supported-subset behavior were also tightened with reproducing tests. The supported rule explicitly requires all three supplied votes to agree. Reuse/summary requires exactly the three comparisons and all-label outside-reference fields.
- Saved external predictions remain local. After the review fix, all15 cached outputs were recomputed through the strengthened combination function and matched exactly. Added counts were recomputed from unchanged reference inputs. Original prediction-code identities and archived receipts are retained; no model rerun or metric change is claimed.

## Execution and verification

```powershell
python ablate_ensemble.py run --workers 2
python ablate_ensemble.py summarize
```

The driver uses the verified external directories and writes separate reports/prediction caches outside the checkout. Its receipts bind consumed inputs, source/model identities and prediction-file hashes. Per-frame caches and transition locations are excluded from publication.

Seven ensemble tests cover agreement, abstention, baseline/period preservation, invalid inputs, all-label unknown-reference counts, exact comparison membership and the supported-subset invariant. Each new behavior/finding was observed RED before its implementation/fix. The full suite passes273 tests with5 documented skips. All34 frozen sources/model/bundle remain unchanged; the new module and experiment driver are additive. The reviewer's executed evidence is separate: four tests plus an exhaustive512-case preservation check.

## Next decision

Keep the ungated model as a benchmark and freeze the agreement rule before obtaining fresh evaluation. Check the primary spell objective, raw-frame accuracy, newly emitted team precision and full-state scope together. Inspect remaining *classes of failure* through permitted automatic/external diagnostics rather than chasing zero X alone. The existing GitHub research identifies input-only crowded/identity-fragmented stress tests, joint state/boundary/contact learning and observation-recovery projects; no third-party code/weights have been adopted.

The participant also requested a separate fresh audit: competition details first, then our actions/results without our reasoning. Its two stage memos and the response are recorded separately, with stage1 hashed before stage2 delivery. [Prior confidence-removal comparison](docs/confidence-ablation.md), [research synthesis](docs/github-research-summary.md).
