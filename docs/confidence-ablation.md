# Removing confidence: measured diagnostic result

The user proposed taking model choices at face value rather than treating a confidence threshold as evidence of correctness. That is a useful comparison: confidence is a decision rule, while correctness is measured against reference labels. We ran it, without training, retuning, challenge GT/video checks or replacing the existing local prediction output.

These are **post-hoc comparisons on already-opened external cohorts**, not a new untouched holdout. Eight SkillCorner matches supply known-in-play H/A reference only. Seven DFL matches are explicitly seen full H/A/D provider-reference checks; their frozen inactive-ball coordinates remain a transfer confound.

## What was tested

1. Current baseline: the previously frozen tactical output. The rejected gated temporal candidate is identical to it.
2. Confidence off, same support: take the temporal H/A sign wherever the existing player, geometry, anchor, gap and D guards permit. Exact logit ties choose H.
3. Direct temporal choices: fill every baseline X in a structurally known period with the temporal H/A sign, including insufficient-player/unbounded intervals. Existing H/A/D decisions remain. This model has no D or X class; those were pipeline decisions.
4. Raw H/A/D head: take the older tree's largest H/A/D score directly, overriding its confidence, duration and continuity filters. Structural unknown periods remain X. This variant can change already-decided labels too.

No implementation or parameter from another repository was imported for these variants. The original frozen model, inference source and bundle remain unchanged; the experiment is an additive driver.

## Eight-match independent-provider cohort

Values are means over matches. Frame accuracy counts X as incorrect; spellF1 follows the unchanged official abstention-expanded temporal scorer. MacroF1 includes the scorer's three-class convention even though this cohort has no D reference, so it is not a full-state quality certificate.

| Policy | Known-reference X | Frame accuracy | MacroF1 | Team-spell F1 |
|---|---:|---:|---:|---:|
|Current baseline|25.67%|66.40%|0.5037|0.4690|
|Confidence off, same support|21.42%|69.49%|0.5155|0.4661|
|Direct temporal H/A for X|0%|85.33%|0.5670|0.4491|
|Raw older H/A/D head|0%|83.32%|0.5615|0.3983|

The user's idea improves raw frame coverage and accuracy. The tradeoff is real: forcing H/A lowers mean spellF1 by0.01994, and raw H/A/D choices lower it by0.07068. More individually correct frames need not preserve whole possession boundaries; added wrong team runs can split or merge spells. The official scorer also already expands X inside scored runs, so raw-frame and temporal metrics respond differently to abstention.

| Policy | New measured frames | New H agreement | New A agreement |
|---|---:|---:|---:|
|Confidence off, same support|25967|62.95%|76.50%|
|Direct temporal H/A for X|156784|70.97%|75.50%|
|Raw older H/A/D head|156784|74.56%|73.13%|

These are correctness among newly emitted labels, not among every existing decision. They fall below the previously declared90% per-team recovery target. The raw H/A/D head also newly emits D on16373 reference-in-play frames; D has no positive reference support in this cohort. It changes15262 already-decided frames, with7715 corrections and7499 regressions; temporal errors depend on their arrangement, not just the net count.

Direct H/A additionally assigns478964 frames outside known phase support. Their correctness is **unmeasured** and is excluded from the85.33% figure. This is why known-play frame accuracy cannot be presented as whole-match live/dead accuracy. There are no qualifying natural hidden opposing spells here, so this run cannot establish their recovery.

## Seven seen DFL matches

| Policy | X | Frame accuracy | MacroF1 | Team-spell F1 |
|---|---:|---:|---:|---:|
|Current baseline|10.21%|85.16%|0.8644|0.5091|
|Confidence off, same support|7.80%|86.91%|0.8760|0.5015|
|Direct temporal H/A for X|0%|92.32%|0.9054|0.5103|
|Raw older H/A/D head|0%|92.44%|0.9071|0.5046|

Direct temporal choices give a small +0.00119 mean spell gain on this seen provider, alongside the frame gain. That benefit does not carry over to the independent-provider cohort. Newly assigned H/A agreement is62.74%/73.44%, and152 new H/A frames occur during provider-labelled D. The data were already used previously and contain the known frozen-coordinate shortcut, so these results cannot establish generalizable stoppage recovery.

## Decision, verification and reproduction

Keep ungated choices as a benchmark rather than assuming the original confidence cutoff is correct. The next experiment should improve emissions/boundaries and select an operating rule against explicit frame and spell objectives. This comparison supports neither blindly preserving the old threshold nor automatically deploying zero-X output. No new local inference, default promotion or accuracy claim was made.

```powershell
python ablate_confidence.py run --workers 2
python ablate_confidence.py summarize
```

The script uses the verified local external caches and writes separate local reports under `independent-reference/confidence-ablation`, outside the checkout. It preserves matching checkpoints and refuses changed source/model/case/reference identities. A fresh reviewer found a missing case/cache dependency in the first receipt; a reproducing test failed before the fix and passed after. All15 matches were rescored under complete identities and exactly reproduced the initial aggregate results. Both runs are retained locally. Four ablation tests cover support-vs-direct behavior, structural rows/D preservation, raw three-class choices and stale reuse/summary rejection.

The complete source suite passes266 tests with5 documented skips; source-only CLI execution also passes under Python3.11 `-I -S`. All138 original files and34 frozen sources are byte-identical. Public exports contain source/docs, licensed model metadata and aggregate scores/counts only. Raw inputs, per-frame predictions and transition locations remain local. [Fresh review](confidence-additions-review.md), [source-only preflight](confidence-feasibility.md), [GitHub research](github-research-summary.md).
