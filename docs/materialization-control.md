# The missing zero-X carry control

7 November2026. The independent audit identified a cheap comparator we should have implemented before the expensive confidence search. The official scorer expands predicted X inside each known-reference run before scoring possessions. Explicitly carrying/backfilling X can therefore change the output presentation without recovering another possession.

The implemented function takes **labels and structural periods only**. Within each contiguous period it backfills leading X from the first decision, then carries the last H/A/D through later X. A wholly unknown block becomes D, preserving zero predicted H/A spells; that D is a scoring convention, not observed dead-ball evidence. Period0 is untouched. It never receives a reference mask.

For fully graded structural blocks, this produces zero graded X with identical official spellF1. Five synthetic tests exercise this, including random known H/A/D sequences, D anchors, period reset, all-X blocks and immutable inputs. A separate counterexample proves that the guarantee does **not** extend to unknown reference holes or a scoring slice starting inside a longer structural block. Such holes can change the scorer's leading-X backfill. We do not feed GT holes into inference to manufacture invariance.

## Actual post-hoc external comparison

| Eight SkillCorner matches | X | Frame accuracy | SpellF1 |
|---|---:|---:|---:|
|Incumbent|25.67%|66.40%|0.4690|
|Incumbent + carry|0%|84.54%|0.4657|
|Two-head agreement|7.37%|81.04%|0.4785|
|Agreement + carry|0%|85.03%|0.4707|

SkillCorner phase-reference holes break exact score equivalence in all8 matches, as anticipated. Agreement remains better than the plain carry control, but its fully materialized version loses some measured spell score relative to its latent-X form. Both filled outputs add478964 labels outside phase reference, with unmeasured correctness.

| Seven seen DFL matches | X | Frame accuracy | SpellF1 |
|---|---:|---:|---:|
|Incumbent|10.21%|85.16%|0.5091|
|Incumbent + carry|0%|90.87%|0.5091|
|Two-head agreement|1.27%|91.65%|0.5260|
|Agreement + carry|0%|92.14%|0.5260|

All7 DFL comparisons preserve each input sequence's spell score exactly. Carry adds no observations or new temporal evidence. The agreement model changes the possession sequence; materialization decides how to write remaining uncertainty. Those are distinct claims. A zero-X CSV alone is not an improvement in football inference.

```powershell
python ablate_materialization.py --source baseline
python ablate_materialization.py --source head_agreement_on_X
```

Both30 match/source cases use verified cached decisions and structural periods, not a new model run. Reference labels enter scoring only. Source/reference/prediction/receipt hashes and source-variant identity guard reuse. Reports remain post-hoc on already-opened cohorts. The full suite passes278 tests with5 documented skips. No local submission/output is replaced; an output materializer should retain latent uncertainty as diagnostics if later used in a selected entry.
