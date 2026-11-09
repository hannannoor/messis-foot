# Verified response to the MESSI's FOOT adversarial audit

Reviewed 8 November 2026. This is a review and prioritization deliverable. It does not implement a new predictor, refit a model, generate new challenge outputs, or publish changes to GitHub.

## Decision

Keep `w0-c32-neutral-missing` as the frozen **experimental baseline**. The reported improvements are numerically reproducible from the retained external caches, but the evidence does not establish unseen challenge accuracy. The audit's central scientific criticism is valid; its repetition across reviewers is not additional experimental evidence.

The next engineering experiment should address **ball-observation cadence and velocity validity**, before another decoder/model search. A new controlled fixture demonstrates a failure the audit did not isolate: the same constantly moving ball produces H on every frame when observed densely, but D on every frame when observed every second frame. Missing observations reset the previous ball, so reacquisition is represented as zero velocity. Neutralizing missing rows leaves these misleading *observed-row* features intact. This is a source-demonstrated mechanism, not a measured prevalence of errors on the challenge match.

Run that bounded comparison against a fair nearest-player/majority baseline and preserve current predictions as the control. In parallel, qualify one genuinely unused, licensed full H/A/D reference source. More seen-data improvement cannot substitute for that scientific gate. Do not immediately bundle motion refitting, team symmetrization, duration modeling and a new decoder into one intervention.

## Exact repository state and coverage

| Item | Verified state |
|---|---|
| Audit branch | `codex/competitor-audit-2026-11-08`, `f426c0e542c1ffdab1296531bdcf5ff0af9d7405` |
| Candidate branch | `codex/tactical-validation-and-coverage`, `cee674190775e9356745f461ba1561e9f2a46f7e` |
| Default main | `3a1c8608e050e2f812826719e1af882d87cf2f67` |
| PR #1 | Open, unmerged; candidate head above, main base above; 280 changed files; no reviews or comments |
| Other refs | One synthetic PR merge ref, `61e32f3`; its tree equals the candidate tree. This is not a completed merge. |
| Reachable history | 21 commits, three branches, zero tags, zero recorded GitHub workflow runs |
| Candidate inventory | 309 tracked files: 132 Python, 102 JSON, 69 Markdown, two text, one PowerShell, three extensionless |
| Audit delta | Nine added audit/result documents on top of the candidate; no predictor/source correction |
| Final refresh | GitHub branch heads and PR state unchanged during this review; GET-only access as `The-leonjr` |

The complete 780-line combined audit was read, including all five individual reviews, the coordinator review and common brief. The review inventoried every tracked path at all three branch tips, indexed every reachable commit and its changed paths, and checked all 309/38/318 tip blobs against their Git object identities. Source, tests, adapters, scorers, model artifacts, experiment protocols, recipes, route/build/install code and material published evidence were inspected across that history. Generated bundles and historical numerical archives were assessed as artifacts, not counted as independent implementations. This is not a claim to have manually read every repeated line of every generated blob.

Three independent verification agents examined evaluation/history, runtime mechanisms, and history/delivery. Their reports distinguish source proof, receipt arithmetic, controlled synthetic behavior and unmeasured real-world effects. They are independent reviews with different scopes, not three independent datasets or model vendors.

No challenge GT, videos, raw tracking, target prediction CSVs or new target per-frame derivatives were opened. Existing public target *aggregate* diagnostics were read as claims, not treated as error labels. Local computation used synthetic fixtures and previously acquired licensed **external** caches; only bounded aggregates were surfaced.

Primary audit: [full report at the reviewed audit commit](https://github.com/hannannoor/messis-foot/blob/f426c0e542c1ffdab1296531bdcf5ff0af9d7405/docs/competitor-audit-2026-11-08/FULL-COUNCIL-AUDIT.md).

## What the numbers establish

The latest one-change comparison is neutral missing-ball emissions versus the previous soft sequence policy, with the same frozen tactical head, zero motion weight and switch cost 32. These are **seen external regression results**, not a challenge score or a single overall model-accuracy percentage.

| Provider / input regime | Frame accuracy, old → current | Official spell F1, old → current |
|---|---:|---:|
| DFL natural, two regression matches | 92.8279% → 92.8279% | .553665 → .553665 |
| SkillCorner natural, eight | 85.8161% → 85.9302% | .575619 → .579192 |
| DFL masked | 84.4043% → 87.4640% | .432684 → .441154 |
| SkillCorner masked | 75.7783% → 82.2666% | .487471 → .542489 |

Equal-provider mean spell F1 is **.564642 → .566428 naturally**, and **.460077 → .491821 under the fixed 30% mask**. Natural gain is +.00178627 score units, or +.178627 percentage points if displayed on a 0–100 scale; it is not +.178627 points of frame accuracy. Masked DFL mean stoppage recall is 92.6420% → 95.7164%. Masked SkillCorner false D falls 57,278 → 321 over 612,173 known-live rows, but SkillCorner supplies no positive D reference, so it cannot measure missed stoppages.

Root freshly rescored **26 match/regime cases × three variants = 78 scorings** from the retained external caches and score archives. All published aggregate official scores, supplementary dead-interval counts, boundary metrics, input strata and change/latent counts matched. This verifies arithmetic and cached-score replay, not raw acquisition, semantic truth or fresh-match generalization. See `external-score-replay.json` and its trusted replay script/log.

The exact empirical paired, provider-stratified bootstrap calculated by the evaluation verifier and independently repeated by root gives a conditional 95% interval of **[+.00047605, +.00328916]** for the natural equal-provider mean increment. It agrees with the audit's Monte Carlo interval. It resamples these same reused matches, has zero DFL deltas, and does not correct for the project's adaptive reuse. The result supports a small positive *conditional* increment; it cannot supply fresh validation. The official illustrative .04 uncertainty band is not a universal rejection threshold for a different paired statistic. `conditional-interval-verification.json` specifies the estimator, exhaustive resampling and quantile convention.

The seven acceptance checks are aggregate requirements, not seven independent replications. Current SkillCorner natural macro F1 slightly declines; one masked DFL match loses spell F1 despite aggregate acceptance. Keep those results visible. The official ranking objective is spell F1, while frame accuracy and stoppage/boundary metrics answer different questions. [Official evaluation definition](https://github.com/metrica-sports/more-than-a-hack-2027/blob/f8f2629ff1e0985f81d7e59d8413678514ee1530/EVALUATION.md).

## Material claim ledger

“Valid” below supports the bounded claim, not every rhetorical extrapolation. Several overstatements are unsafe readings of the audit rather than accusations made by all its authors; its coordinator is often appropriately careful.

| Claim / criticism | Disposition and actual consequence |
|---|---|
| Repeatedly used validation/regression matches cannot establish fresh generalization | **Valid.** Three seen validation and ten seen regression matches, with earlier uses in history. Keep them for development; do not relabel them fresh. “Exhausted” overstates matters if it means they are useless for regression. |
| Current numbers are wrong or the natural increment is necessarily noise | **Not supported; that stronger inference is contradicted by replay and conditional arithmetic.** Small gain and weak transfer evidence are different issues. |
| DFL stoppage competence may exploit coordinate freezing | **Valid vulnerability; prevalence unmeasured.** The published aggregate says 449,536/449,539 inactive coordinates repeat. Stationarity is a strong tree feature. This does not show the model recognizes *only* a provider artifact or quantify challenge failure. |
| Two providers independently validate the full H/A/D problem | **False.** SkillCorner phases cover live H/A only. DFL state labels and its observation convention do not independently settle transfer to a new source. |
| A neutral ball gap recovers hidden ownership changes | **False as a capability claim.** Missing emissions contain no team/state information at zero motion weight; continuity can be useful, but cannot identify an entirely hidden H→A→H spell. |
| A single anchor can authorize an arbitrarily long usable neutral gap | **Valid.** Eligibility is not an evidence-age limit. Latent X does not enumerate every unsupported point estimate. Maintain neutralization and evidence-age diagnostics separately. |
| Neutral ties prefer earlier state order | **Valid.** Controlled H/A/D anchor tests confirm H before A before D in tied path selection. A boundary can have many equally optimal locations. Tie policy is separate from head asymmetry. |
| The full model is not team-exchange equivariant | **Valid.** Unique-distance, complete EPTS fixtures return H before and after team exchange. Four development cases also show .43%/.81% known-live changes by provider. Neither proves the fix's score benefit or aggregate away-team error prevalence. |
| Cost 32 erases short supported interior islands | **Valid mechanism.** Two switches cost 64; the support ratio determines required duration. There is no universal 23-frame minimum. |
| All additional missed real boundaries are short or hidden possessions | **Overstated.** Published missed counts rise while spurious counts fall, but aggregates do not distinguish deletion, shift, merge, duration or gap mechanism. Add duration/gap/transition strata first. |
| Viterbi implementation is broken | **Refuted as an interpretation.** Sixty independent exhaustive checks of all paths at lengths 1–6 attained the optimum. The concern is the chosen objective and support scale. |
| One-seed deletion establishes general robustness | **False.** The latest stress is seed 1729, 30% ball deletion. It does not cover cadence, stale finite observations, false balls or correlated player loss. |
| The project never tried baseline rules, corruption tests or uncertainty | **Refuted project-wide.** Earlier endpoint/last-owner rules, ungated heads, carry, four corruption drivers and bootstrap routines are preserved. Their existence does not qualify the latest winner on those stresses. |
| A strong scored official nearest-player/majority comparator is missing | **Valid.** The conservative geometric core and related head ablations are not that family. No external equivalent was found across all 21 commits. Its published challenge score cannot be compared directly with external scores here. |
| Anonymous compatibility is equivalent to raw anonymous observations | **Overstated.** SkillCorner interpolates players using provider IDs before anonymous association. This is an input-transfer advantage, not direct label leakage. Current zero-motion head does not use associated IDs. |
| The old 27-policy confidence grid was structurally incapable of recovery | **Valid historical design error, already diagnosed.** Maximum bounds .89944/.86694/.85267 were below the minimum .90 gate. Feasibility code now exists; it is not a confidence barrier in the selected current policy. |
| That rejection proves motion is useless | **Refuted.** The impossible gate says nothing general about the information in motion; later ungated variants were actually tested. Current zero weight is a bounded selection result. |
| Current inference secretly uses the fixed pre-kickoff D shortcut | **Refuted.** Legacy `match` retains it; selected strict input is geometry-only and never invokes it. Structural half windows are separately published official timeline metadata. |
| Current inference requires private external score/reference arrays | **Refuted.** Clean selected artifact validation and full synthetic runtime work with committed evidence. Exact scientific replay has additional local archive requirements. |
| Runtime is coupled to unused research/control machinery | **Valid.** It validates historical source/evidence seals and computes four controls despite selected motion weight zero. Mutation of unrelated research source blocks execution. This is coupling, not a measured latency claim. |
| There is no acquisition or reproduction recipe | **Overstated.** Recipes and licensed sources exist. The latest exact sealed lineage is not freshly reproducible from raw inputs alone; see the UUID defect below. |
| Main/standalone already contain the newest route | **False.** Main is older; the preserved standalone serves an older explicit tactical route. README distinguishes them. Release confusion is real, but the newer route is not falsely promised as bundled. |
| A rival is better or the hidden challenge accuracy is known to fail | **Unsupported.** No rival was scored and no challenge correctness reference was inspected. More complex alternatives remain hypotheses. |
| The audit's delivered probes and byte manifest are complete | **False.** Missing source/log, renamed coordinator path and seven two-byte hash mismatches were independently verified. This does not invalidate separately reproduced mechanisms. |

Source-level evidence and pinned line links for these dispositions are in `findings/evidence.md`, `findings/runtime.md`, and `findings/history-delivery.md`.

## New concrete defects found during verification

### 1. Fragmented observations become false stationarity

A 180-frame, 25 Hz synthetic fixture moves the ball at exactly 2 m/s near the home team, retaining valid geometry and three players on each side. Dense input yields **H180**. Keeping ball observations every second frame yields **D180**, including through the complete selected EPTS runtime. Every-third/every-fifth component cases also yield D180.

`tactical.py:40–51` initializes speed to zero and clears `previous_ball` on a missing frame. Each isolated reacquisition therefore appends a zero to speed history even though successive retained coordinates move. The sparse observed rows accumulate support approximately H .318805 / A .247357 / D .433839. The current neutralizer affects the *missing* rows only. Replacing only the two speed features on observed rows with the fixture's known speed restores H180; it does not change the decoder, geometry or missing-row policy. [Feature code](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/gap_solver/tactical.py#L39-L63), [neutral policy](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/ball_gap_policy.py#L14-L24).

This feature behavior dates to the original tactical head. On this fixture the older gated route produced sparse X rather than current sparse D, so do not retroactively attribute the same output to every generation. The tree's learned meaning depends on its feature semantics: a repair needs an explicit velocity-availability/source-time contract and an external comparison. Do not hardcode 2 m/s, carry velocity through arbitrary gaps, or send missing values into the old tree as though it had been trained for them. Synthetic labels here describe controlled model behavior, not independently annotated physical possession.

### 2. Fresh cache generation conflicts with later byte-frozen evidence

Root independently saved the same synthetic SkillCorner match twice. Both generations load correctly; stable `input_identity` and **25 semantic arrays** are equal. Only the two `generation_id` arrays differ, yet both NPZ hashes and the metadata hash differ. `save_motion_cache` uses a random UUID; later accuracy/ball-gap experiments freeze whole cache/archive bytes. The earlier temporal evaluator deliberately accepted a rebuilt generation with stable raw identity, but the newer lineage does not. [Cache writer](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/gap_solver/skillcorner.py#L215-L253), [later byte seals](https://github.com/hannannoor/messis-foot/blob/cee674190775e9356745f461ba1561e9f2a46f7e/accuracy_experiment_frozen.py#L89-L145).

Fix with a **new reconstruction lineage**: stable raw source + adapter/model/policy/scorer identities and canonical semantic-array digests, alongside generation-specific container hashes. Preserve all existing historical seals. A newly generated equivalent cache must not be relabeled as the original archive. This is an evidence-portability defect, not a demonstrated scoring or inference defect. Root proof: `delivery-and-rebuild-verification.json` / `verify_delivery_and_rebuild.py`.

### 3. Historical installer validates a stale version after copying

`install_four_goal_results.ps1:142` expects `2026.11.05-tactical-validated`; the current preserved bundle has reported `2026.11.06-temporal-research` since `79a467a`. This check happens after file copies. A current handover using otherwise valid legacy fixtures can mutate the destination and then fail its version gate. The installer is documented as a local historical utility, not required for current inference. Archive it to its intended generation or validate an explicitly chosen current artifact/interpreter/version before copying; test that compatibility with synthetic fixtures. Do not conflate this with a broken latest candidate.

### 4. The audit has its own publication defects

The audit branch contains `root-probes.json`, but no `root-probes.py` or `unittest-final.log` anywhere in its tracked tree. The manifest names `root-review.md`, while the actual report is `coordinator.md`. All seven report hashes/lengths describe bytes before one additional trailing CRLF; removing exactly that two-byte suffix reproduces every declared hash. All six logical reports are contained in the combined report after newline normalization. This is a bounded publication mismatch, not evidence of substantive tampering or fabricated findings.

Repair the paths and final-byte manifest, and publish the claimed probe source/log or mark them unavailable. No predictor change is needed. Proof is independently checked against raw Git blobs, avoiding Windows newline conversion. [Delivered manifest](https://github.com/hannannoor/messis-foot/blob/f426c0e542c1ffdab1296531bdcf5ff0af9d7405/docs/competitor-audit-2026-11-08/delivery-manifest.json).

## Actual priority order and acceptance conditions

| Order / track | Concrete change | What must establish value | Main limitation |
|---|---|---|---|
| **Next bounded engineering experiment** | Preserve the cadence fixture; define velocity validity and source timing explicitly; compare one narrow observation-feature correction with the frozen candidate | Natural and fragmented-cadence external scores, stationary-live false D, true-D recall, spell/boundary/duration results; no deterioration hidden by an overall mean | Current external labels remain seen and provider-dependent; changing feature semantics may require a new fitted head |
| **Parallel scientific gate** | Qualify one unused full H/A/D source from the existing scouts; resolve rights, ontology and team/time non-overlap, or define external annotation/adjudication | A frozen comparator/candidate protocol before outcomes are opened; independent full-state results | No already-qualified source exists; licensing/access/annotation are real work, not a rename of current test data |
| **Comparator in that protocol** | Implement literal official nearest-player + H/A-only centered-majority windows, plus explicitly matched missingness/D handling | Same inputs, timing, periods, masks and scorer; external development selection; all variants reported, no implied win | Literal official missing→D can be weak under ball masks; a straw-man implementation would answer the wrong question |
| **Diagnostics before more temporal complexity** | Reuse current corruption drivers; add fragmented cadence, finite stale/false observations, joint player loss and multiple fixed masks; report short spells, gaps, worst matches and transition types | Current winner measured under each condition, evidence-age/neutral flags and tied boundary ranges retained | Synthetic stress is not a calibrated sensor-failure distribution; it cannot supply hidden truth |
| **Conditional model comparison** | Test team-exchange invariance and, if justified, one symmetric emission/head alternative | Whole-input unique-preference exchange tests; per-team external spell results and D safeguards | Algebraic symmetry improvement does not guarantee accuracy; tie ambiguity is a separate issue |
| **Evidence portability** | Add a new raw-to-report rebuild with stable semantic identity, retaining old archival replay | Fresh workspace, public licensed raw preparation, fixed equality rules and aggregate numerical agreement | Does not make old seen matches independent; resource/access requirements must be declared |
| **Delivery** | Add a separately versioned selected-only export and optional all-controls research mode; publish a route/commit matrix; fix/archive historical installer and repair audit manifest | Exact selected-output parity on synthetic/external examples; minimal declared dependencies; pre-copy version checks; valid final-byte manifests | Packaging cannot certify unseen accuracy or final competition eligibility |

The official baseline has half-widths 0/25/50/125 (up to 1/51/101/251 centered frames), H/A votes and H ties; D is not a generic third majority class. Port the semantics explicitly rather than using a differently defined filter. [Pinned official baseline source](https://github.com/metrica-sports/more-than-a-hack-2027/blob/f8f2629ff1e0985f81d7e59d8413678514ee1530/starter/baseline.py).

These are prospective changes, not an implementation claim. Promote no new predictor merely for reducing X, passing synthetic checks or improving the reused cohort. State which evidence level each result supports; preserve the current controls and negative results.

## What history tells us to stop repeating

- **Do not rerun confidence removal or endpoint carry as novel discoveries.** Their outcomes and limitations already exist in `0cbf415` / `1d723cb` and earlier temporal comparisons. Require feasibility preflight on any future gated search.
- **Do not just lower cost 32 against the same visible outcomes.** Establish whether errors arise in observations, head support or path objective; measure deleted/shifted/merged events and genuine short-spell recall.
- **Do not restart broad OCR/fusion work yet.** The controlled pilot added no missing-ball rescue, and the full automatic stage found zero usable synchronization links. A future camera milestone must first show reliable automatic timing/live correspondence and genuinely additional evidence. These results do not prove cameras can never help.
- **Do not erase history to simplify delivery.** Keep frozen source/evidence in Git and introduce a clear separate export. Do not automatically merge PR #1 because Git reports a clean merge.
- **Do not infer a rules violation from public structural period constants.** The official DATA.md publishes the same windows and indexing. The legacy fixed-D special case is separate and is not traversed by the selected route. [Official structural alignment contract](https://github.com/metrica-sports/more-than-a-hack-2027/blob/f8f2629ff1e0985f81d7e59d8413678514ee1530/DATA.md#L208-L235).

## Status of the preceding Council and approved plan

The requested five-advisor Council, five anonymous peer reviews and chairman synthesis are complete. A real aggregate pilot ran on four licensed external development matches; it was not theory alone. It found frequent opposite remembered control during ownership swaps and a mixture of raw-head and decoder errors. It cannot causally assign those errors from a one-frame comparison.

The approved whole-segment path-score **design and implementation plan are written**. The deeper forward/backward constrained-path diagnostic has **not been implemented**, no predictor was refitted, and no new target output was authorized by that plan-only task. See `../active/council-transcript-2026-11-08-ownership-swaps.md`, `../next-phase-notes/ownership-council/observed-diagnosis.md`, and `../ball-gap-work/docs/superpowers/plans/2026-11-08-ownership-path-diagnosis.md`.

The path audit remains useful for separating emissions from nonlocal smoothing. The adversarial verification changes the immediate order: isolate cadence/velocity validity and establish the missing strong comparator first, then use the bounded path diagnostic to explain remaining errors. This avoids spending another large experiment optimizing a decoder around misleading observed features. No old plan or published model was silently overwritten.

## Verification record and limits

- Fresh suite at exact candidate source: **341 tests, zero failures/errors, six skips** (335 executed), `full-suite.log`. The audit's 19 skips reflect its different environment; its report already disclosed them. Optional dependency/asset skips are not target-accuracy evidence.
- Fresh external cached-score replay: **78 scorings across 26 cases**, all expected aggregate checks true, `external-score-replay.json` / `.log` / `recompute_published_evidence.py`.
- Exact conditional interval independently recomputed from published match receipts: 6,435 multinomial compositions representing 16,777,216 ordered SkillCorner resamples; `conditional-interval-verification.json` / `verify_conditional_interval.py`. This remains reused-data evidence.
- Runtime verifier: complete EPTS cadence/exchange/barrier cases, neutral tie/anchor probes and 60 exhaustive tiny-path optimizer checks; `findings/runtime.md` and synthetic `.tmp` results. These establish mechanisms, not real-match prevalence.
- Root Git-byte and cache check: 309 current + 38 main + 318 audit blobs exact; two valid synthetic cache generations with equal semantic arrays but different byte seals; seven stale audit manifest hashes and missing script/log confirmed, `delivery-and-rebuild-verification.json`.
- Repository/PR API state independently refreshed at the end, read-only as the requested account, `repository-inventory.json`; initial inventory retained separately. All reachable history and tip inventories are indexed in `history-index.json`.
- No acquisition, training, production source edit, new challenge inference, branch change, commit, push, merge or message to another person occurred in this review. The local review scripts, reports and proof receipts are the new deliverables.

The defensible conclusion is that the project made real, reproducible exploratory progress, while its observation model and evidence boundary now matter more than another broad strategy search. The immediate engineering target is **unknown velocity being encoded as zero velocity**, and the scientific release gate is genuinely independent full-state validation.
