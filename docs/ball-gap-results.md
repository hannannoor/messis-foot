# Ball-gap evidence results — 7 November 2026

The single fixed missing-ball-neutral policy passed all seven predeclared checks in both seen validation and seen regression. It is accepted as a **separate experimental opt-in**, `w0-c32-neutral-missing`. The previous w0-c32 candidate, four-policy outputs and Desktop installation remain preserved. There is no measured target accuracy or fresh full-state holdout.

## What changed and why

The [read-only diagnosis](ball-gap-diagnosis.md) found that missing ball observations inserted zero speed into the tactical tree's recent-speed feature. A low-speed/stale-control branch could then produce strong D support, which accumulated through the decoder. Missing observation was being treated as positive state evidence.

The fixed correction replaces the whole H/A/D log-emission triple with equal zero scores when ball coordinates are missing. Observed-ball scores, the frozen tree, motion weight0, switch cost32, periods, eligibility and carry remain unchanged. D is still possible from surrounding observed evidence. An entirely unsupported usable segment remains latent X; any later carry is explicitly materialization rather than new evidence. There was one candidate and no parameter search/refitting.

## Results against w0-c32

These are **per-match means** on ten previously examined regression matches, not target accuracy or pooled fractions. DFL has2 matches and full-state provider labels; SkillCorner has8 and known-play H/A only.

| Seen regression | Input | Frame accuracy, previous → new | Official team-spell F1, previous → new |
| --- | --- | ---: | ---: |
| DFL | Natural | 92.83% → 92.83% | .553665 → .553665 |
| SkillCorner | Natural | 85.82% → 85.93% | .575619 → .579192 |
| DFL | Masked ball | 84.40% → 87.46% | .432684 → .441154 |
| SkillCorner | Masked ball | 75.78% → 82.27% | .487471 → .542489 |

Equal-provider mean official spellF1 changes **.564642 → .566428 naturally**, and **.460077 → .491821 under masking**. The earlier agreement-plus-carry masked SkillCorner accuracy was80.95%; the new82.27% recovers that loss while retaining stronger spell quality. The candidate remains far from perfect ownership recovery.

SkillCorner masked false D falls from57278 to321 among612173 known-live frames: **9.3565% → .0524% pooled**. Its per-match mean false-D fraction is9.3671% → .0546%. Natural pooled false D falls2557 →72. These zero/near-zero false-D measurements say nothing about missed genuine D in SkillCorner, whose reference does not cover stoppages.

DFL masked mean D recall improves **92.64% →95.72%**, and supplementary dead-interval F1 improves **.673236 →.875627**. Pooled missed-D frames fall9981 →5809; false-D frames fall14183 →6573 among153693 live frames. The older agreement-plus-carry route has fewer masked DFL false D (4987) but misses more genuine D (20288). Natural DFL D recall remains99.44%. The new policy therefore did not win this comparison simply by refusing to emit D.

Seen validation used exactly DFL J03WQQ and SkillCorner2006229/2006363. Its natural equal-provider spellF1 improves.627686 →.630419; all seven checks passed before regression began. Validation disposition and stage receipts were sealed before regression; regression cannot revise the policy or its gates. Full per-case confusions, observed/missing strata, false/missed D, D-interval counts at each IoU and boundary metrics are in `reports/ball-gap/validation/` and `regression/`. The [approved design](superpowers/specs/2026-11-07-ball-gap-evidence-design.md) defines denominators and acceptance exactly.

## Tradeoffs that remain

Aggregate gains do not mean every match improved. Natural SkillCorner frame accuracy declines on2016236 and2017461, and spellF1 declines on2007448. Masked DFL spellF1 declines onJ03WN1. Natural SkillCorner macroF1 decreases slightly, .571668 →.571261, despite higher frame accuracy and spellF1. No per-match veto or macroF1 gate was added after observing these results.

At the unchanged25-frame (1s) boundary tolerance, natural SkillCorner boundary F1 improves.3436 →.3479, but missed changes increase752 →758 while spurious cuts fall1424 →1355. Masked SkillCorner improves.2268 →.2701 with fewer spurious cuts1812 →1043, yet more missed changes921 →953. Masked DFL improves.4381 →.4796 with spurious483 →271 and missed632 →645. Fewer false cuts can coexist with more erased genuine transitions.

Mean absolute latency among matched boundaries improves slightly for masked DFL (.205s →.197s) and SkillCorner (.371s →.364s). This is conditional on successful matching, not timing accuracy for missed boundaries. Both12- and25-frame diagnostics and support counts are retained.

Neutral evidence cannot reveal a stoppage or team switch wholly hidden in a gap. Equal-cost boundary locations inside neutral spans retain deterministic H/A/D tie behavior. First-after-gap emissions and history features are unchanged; offline decoded states at those observations can still change when neighboring evidence is neutralized. Finite coordinates do not verify freshness; repeated stationary coordinates may still be stale. The existing tactical head is asymmetric. Entirely unsupported spans still need explicit carry conventions.

All references have been used earlier in this project. Repeated development can overfit project decisions without fitting a new head. DFL has frozen inactive-ball coordinates, which can inflate stoppage performance; SkillCorner cannot independently validate D, and some player coordinates are identity-assisted interpolation. Input masks are simulated missingness. Fresh licensed full-state evaluation remains the next evidence gap.

## Verify published evidence

The published tree already has frozen sources, runner seal and completed scored receipts. With the original external caches and score archives available at their recorded sibling paths, run:

```powershell
python ball_gap_post_review.py verify
```

This checks the independently pinned release artifact, substantive runtime adapter, actual approved design bytes, exact stage-file inventory, runner seal, all score receipts and dispositions. It also replays all26 unchanged-policy carry diagnostics and rederives signed candidate-minus-w0-c32 deltas for frame accuracy, macroF1 and spellF1. They are published in `reports/ball-gap/post-review-diagnostics.json`. Private evaluation archives are needed for exact replay; target inference uses the committed artifacts without those archives.

## Replay in a separate clean copy

Never remove evidence from the existing workspace. Make a separate sibling copy of the software with the same original frozen `reports/accuracy-first/`, model artifacts, original external inputs/caches and `accuracy-reference/cases/` available under their recorded relative paths. Preserve the exact new source bytes and the existing `reports/ball-gap/comparison-freeze.json` and `runner-source.json`. In **that new copy only**, start without `reports/ball-gap/validation/`, `regression/`, `validation-seal.json`, `validation-disposition.json`, `regression-seal.json` or `summary.json`; these are the outputs to recreate. Original26 accuracy-first receipts remain required and unchanged. The prior acquisition/provenance documents describe the licensed DFL/SkillCorner inputs; caches and per-frame score archives are local assets excluded from GitHub.

Then run the fixed sequence below. Do not run `seal` on a completed published tree; it intentionally refuses a new seal after scoring starts. The initial `ball_gap_experiment.py freeze` and `ball_gap_run.py seal` commands were only for original setup before the first receipt and are not warm-verification steps.

```powershell
python ball_gap_run.py validate --workers 2
python ball_gap_run.py decide
python ball_gap_run.py regress --workers 2
python ball_gap_run.py summarize
python ball_gap_run.py verify
```

The initial attempt stopped before writing any score receipt: live metric dictionaries use numeric IoU keys while saved JSON has string keys. The additive public runner normalizes that representation for equality, without changing any score, prediction or setting. The original frozen engine/policy bytes and freeze remain intact. `runner-source.json` was sealed before all26 completed score receipts. Use `ball_gap_run.py` for fixed scoring in the separate replay copy; its final command checks internal consistency. The stronger released-evidence command above is the supported verification entry point for the published tree. Direct engine commands and their less strict legacy re-entry helpers remain audit artifacts.

## Experimental local inference

```powershell
python ball_gap_candidate.py --prefix "C:/football-data/tactical cam/BAR-ATH_tactical" --out "../ball-gap-new-run"
```

Use a fresh/empty dedicated directory. A small entry point pins the substantive `ball_gap_runtime.py` adapter before importing it. Standard-library inference verifies source/model/evidence identities, uses strict channel-referenced EPTS input and preserves all original frame indices. It emits the unchanged4 comparator CSVs, selected `submission.csv` and local `uncertainty.csv` with availability/neutralization/unsupported-segment/materialization flags. Final directory promotion cannot replace a populated destination, even if another writer arrives after the last preflight check. The report distinguishes wholly latent-X periods and their fallback-D rows from ordinary gap carry and counts all latent-X rows materialized as D/H/A. It does not read target GT/video or use tagging, a fixed D interval, broadcast fusion or target parameter tuning. A positive500-frame synthetic CLI fixture emits H/A/D and carries a neutral missing span, matches all prior comparator hashes and rejects both older candidate generations as overwrite destinations.

## Final verification

The full suite passed341tests with6documented skips after one fresh review and one substantive fix pass. The [review response](ball-gap-code-review.md) records the fixes and two deferred evaluation-harness minors. Positive CLI fixtures also pass under isolated Python3.11 `-I -S` without third-party imports; all6added runtime sources parse with Python3.9 grammar. Grammar compatibility is not execution on that interpreter.

Two fresh reviewed-code local runs under Python3.11 `-I -S` produced identical hashes for all6CSVs. Both199319-row selected files pass the unchanged official format-only validator, preserve active/outside structural rows, and retain all4prior comparator hashes. Their CSV hashes also exactly match the two preserved pre-fix runs: review changed publication safety and diagnostics, not predictions. Prior candidate generations, all255old non-README published files and the Desktop pipeline remain unchanged.

Selected CSV SHA256: `4074cc046500e3d54668a81baf5e46f6d90aeb40a0a247fcefbfa8ee1bd226a5`. Local diagnostics count60321neutral active usable rows,18fully unsupported usable segments containing2324rows, and8059latent-X active rows subsequently materialized. There are0wholly latent-X-period fallback-D rows; ordinary carry materializes1477latent-X rows asD,1803asH and4779asA. These flags describe evidence/materialization, not correctness or all epistemic uncertainty. Target GT/video were not consulted and target accuracy remains unmeasured.

The released verifier checks the actual design,47pinned source/adapter files,34pinned evidence files, exact26-case inventory, original provider/archive bindings and sealed dispositions; all26additive carry/delta replays match. `reports/ball-gap/local-reproducibility.json` records safe execution aggregates. Raw inputs, frame-level predictions/uncertainty, NPZ caches and event locations remain local and are excluded from publication.
