# Stage2 factual inventory

Prepared7 November2026. This packet records actions, settings and outcomes. It intentionally omits the authors' reasons, preferred direction, earlier audits and research recommendations. It is not a request to defend any decision. The user's stated ambition included ideally zero undecided output.

## Implemented inputs and camera processing

- Local game exports have199319 original tactical rows; the declared scoring/match scope used in local aggregate reports contains158857 rows. Local accuracy has not been measured against provided GT/video.
- The source contains legacy manual ROI/clock options and a fixed2934-row D interval. The separate selected tactical route excludes the fixed interval and does not use Smart Tagging as prediction features.
- Automatic camera discovery, OCR crops/windows and dense clock processing were implemented. Dense synchronization produced zero qualified bounded links between cameras. OCR defaults included.7 confidence, stride5 and.25s combined timing limits. No camera fusion from that run was applied.
- The ATD loader originally returned early when the ball was missing. A new loader preserves available player coordinates/IDs in those rows. Homography rejection clears all geometry; its existing reprojection-error gate is3. Local ATD finite-coordinate freshness is unverified; home/away role mapping retains an unverified ordinal assumption.
- A local automatic aggregate audit counted65545 unresolved model-input missing-ball rows,59821 with at least three players available per side.56016 missing-X rows belonged to gaps longer than10s. No challenge-derived labels were created.

## External data and first frozen model

- Seven DFL/IDSSE matches, about2.63GB of licensed XML, were acquired/checksummed under CC BY4.0. Split4 development/1 validation/2 test.
- A31-node, depth4,18-feature geometry/history tree was selected with.8 leaf-support threshold,12-frame stable runs and2s retention/bridge. Inference is standard-library Python. The original six frozen source files and artifact remain unchanged.
- Two-match full-provider test mean spellF1: geometry.373607 → selected.505132. Mean X60.47% →9.86%. Newly resolved H/A/D pooled agreement96.32%; H86.36%, A88.95%, D99.78%. Inactive ball coordinates repeated previous values on99.9993% of contiguous inactive frames. Active-only spellF1 changed.53842→.53403 and.53548→.53490.
- That opt-in model was run locally. X within declared local scope changed109917→89200 (69.192%→56.151%), with unresolved intervals1045→509. No local correctness score was produced.

## Independent provider and motion candidate

- Twenty SkillCorner Open Data matches were pinned at revision4340d274572876239c154c90bc507a9b3250a656, under the repository MIT licence contract. About1.82GB of tracking; split8 development/2 calibration/2 validation/8 test before new-model scores.
- Input native rate10Hz was mapped to25Hz. Interpolation occurs only between consecutive detected records in the same period; isolated native samples can snap within20ms. Native/interpolated/extrapolated/unknown provenance is retained. Detected-only input is primary; available/extrapolated input is a separate ablation.
- Reference is provider team-in-possession phases joined half-open by native frame. Phase absence/conflict is X, never D. Duration/time/period checks quarantine contradictions; retained reference support is reported. No inference-time phase masks are supplied.
- On eight development matches, the old frozen model versus geometry had mean spellF1.527643 versus.524729, and mean X23.0074% versus48.9788%.
- New inputs contain39 team geometry/count/motion/continuity and previous/next-control features. Forty depth-two boosted trees, minleaf150, learningrate.1, seed1729, were trained on357964 augmented rows from the8 development matches. Rows were known H/A on baseline X, sampled every fifth canonical frame; cases/matches had equal total weight. Augmentation: identity, team swap, reflection, both. Scores are symmetrized under team swap.
- A two-state H/A forward/backward decoder uses hard baseline H/A anchors, D/period/quality boundaries, and a training-derived switch cost6.35927754. Temperature fits on the2 calibration matches returned4.20708786/8.31162177/16.11656795 for switch multipliers.5/1/2.
- Validation grid: confidence.90/.95/.975; full anchor-gap caps2/5/10s; switch multipliers.5/1/2; at least3 available players each side. Supplemental masking:30%, contiguous.2/.6/2/5/10s, fixed seeds, labels not supplied to masking.
- Engineering selection gates included≥5pp coverage gain,≥90% new H and A agreement separately with support, no validation match spell decline, hidden-opponent support≥20 across≥2 matches, and superiority over a matched-budget endpoint comparator. These were project-selected criteria, not stated competition requirements.
- All27 gated policies added zero H/A labels. A source-only calculation later found confidence ceilings.8994398/.8669356/.8526685 below the minimum.90 threshold. The selected diagnostic artifact was recorded rejected before test, at confidence.975/cap2s/multiplier.5.
- The frozen8-match natural test produced unchanged mean spellF1.468999 and X25.6736%. There were zero qualifying natural hidden opposing spells and2 masked ones. Minimum reconciled reference retention99.695%. Seven seen DFL regression pairs, two four-case mechanism-stress receipts and two available-position ablations completed. No new local prediction was run.

## Additional empirical variants

The learned models remained fixed. The following are post-hoc diagnostics on the8 already-opened SkillCorner test matches and7 already-seen DFL matches. No fresh untouched cohort was acquired.

| SkillCorner policy | Mean X | Mean frame accuracy | Mean spellF1 |
|---|---:|---:|---:|
|Existing frozen baseline|25.67%|66.40%|.4690|
|Temporal confidence off, same support/anchor/gap guards|21.42%|69.49%|.4661|
|Fill all baseline X with temporal H/A argmax in known structural periods|0%|85.33%|.4491|
|Raw older H/A/D tree argmax, including already-decided changes|0%|83.32%|.3983|
|Keep existing decisions, fill X with raw older H/A/D choices|0%|83.28%|.4122|
|Keep existing decisions, fill X only on temporal/raw H/A agreement|7.37%|81.04%|.4785|
|Same agreement with original support/anchor/2s guards|22.56%|68.78%|.4692|

- Ungated direct temporal newly emitted H/A agreement:70.97%/75.50%.478964 additional H/A assignments outside SkillCorner phase reference have unmeasured correctness.
- Agreement-only new H/A agreement:80.85%/79.73%,111960 newly measured assignments;110133 additional H/A assignments outside phase reference have unmeasured correctness. SpellF1 improved on7 of8 matches and declined by.003277 on one. Existing decided labels were preserved.
- On7 seen DFL matches, baseline mean spellF1.509097; direct temporal.510286; agreement-only.525961. Agreement-only X1.27%, frame accuracy91.65%, new H/A agreement67.02%/74.56%.
- Raw H/A/D fallback assigned317877 D rows outside SkillCorner phase reference; all-label unmeasured counts are retained separately from H/A-only metrics.
- No variant above has replaced the current local output or default.

## Software and research activity

- Source is maintained as isolated verified copies; no local git repository exists. A private GitHub PR is open/unmerged. Code/docs/licensed model parameters and aggregate external metrics are published; raw/per-frame assets remain local.
- The suite contained273 tests,5 documented skips after the latest ensemble fixes. Separate training/export and isolated stdlib CLI checks were performed. A code reviewer checked frozen source hashes and synthetic cases. New receipt tests cover changed inputs, incomplete comparison sets and all-label unmeasured counts.
- A confidence-feasibility CLI was added without modifying the frozen selector/model/bundle. Its outputs are impossibility or not-ruled-out; it does not establish prediction correctness.
- Three GitHub scouts produced pinned source/licence/evaluation inventories. No third-party implementation or checkpoint was imported, and none of their reported performance was reproduced locally.

Stage2 request: audit this work against your independent stage1 understanding. Identify wasted or redundant work, missing obvious checks/capabilities, objective mismatch, overconstraints/underconstraints, data/evaluation assumptions and alternative priorities. Do not read the authors' explanations, other audits or preferred recommendations. Separate established facts, inferences and information you would need to verify. A critical conclusion is welcome; a favorable conclusion must be earned. Write a separate stage2 memo, preserving stage1 unchanged.
