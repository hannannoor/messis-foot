# Public GitHub scout: related possession solutions

Research date: 6 November 2026. Scope: public primary repositories and their source/documentation, read only. Prepared for a baseline that already has nearest-team geometry and a frozen DFL history-tree model, with a motion/temporal candidate rejected because calibration and decoder confidence did not agree, and no qualified OCR camera alignment.

## Findings and priority

**Credible same-challenge implementations were found.** Four are shortlisted below, alongside one research repository for a different, closely related task. None establishes a verified private challenge score. The best worthwhile next experiment is not another rule that fills X: it is **native-rate state-and-boundary learning with a training objective that matches the decoder**, assessed on **label-blind corrupted external observations**. Both ideas have inspectable implementations.

| Priority | Repository | Relationship | Most useful missing method | Cost estimate for a bounded experiment |
|---|---|---|---|---|
| 1 | 7dracoder / BlindSpot | Same 2027 challenge | Joint state/boundary objective; native-rate short-spell evidence; realistic training corruption | Medium/high: a small GPU sequence experiment, then independent validation |
| 2 | GTT-TalentArena | Same 2027 challenge | Label-independent degradation harness, slot fragmentation and antisymmetric collective evidence | Low/medium for harness; medium for model adaptation |
| 3 | danieltyukov / Frame Control | Same 2027 challenge | Projected interception/control history; restart-owner latent state; removal of frozen-ball shortcut | Medium; require a clean reimplementation and fresh selection |
| 4 | maxoubvd / MYA | Same 2027 challenge | Lightweight factorized heads with learned symmetric transition prior; honest short-spell diagnostics | Low/medium conceptually, but no reuse licence found |
| 5 | hyunsungkim-ds / PathCRF | Research task, not a challenge entry/tutorial | Possession as logically connected player-to-player paths rather than independent nearest-player labels | High; stable identities and richer supervision are a substantial mismatch |

Cost is my implementation estimate, not an author claim. All numerical results below are **author-reported aggregates**, not reproduced by this scout. Source existence and selected mechanisms were checked at pinned commits; no external code was executed, weights loaded, or dataset downloaded.

## 1. 7dracoder/more-than-a-hack-2027 — BlindSpot / CoreOrigin

Pinned revision: [e00af106d13b0424688a7d723d3bd7f242046958](https://github.com/7dracoder/more-than-a-hack-2027/commit/e00af106d13b0424688a7d723d3bd7f242046958).

**What exists.** A substantial same-challenge implementation with explicit external-only successors to older public-label experiments. Relevant source inspected:

- [possession/temporal.py](https://github.com/7dracoder/more-than-a-hack-2027/blob/e00af106d13b0424688a7d723d3bd7f242046958/possession/temporal.py): dilated residual TCN, BiGRU/hybrid alternatives, symmetric inference and temporal decoding.
- [possession/boundary.py](https://github.com/7dracoder/more-than-a-hack-2027/blob/e00af106d13b0424688a7d723d3bd7f242046958/possession/boundary.py): separate state and boundary heads, weighted BCE boundary training and a calibration hook.
- [possession/structured_loss.py, lines 19–53](https://github.com/7dracoder/more-than-a-hack-2027/blob/e00af106d13b0424688a7d723d3bd7f242046958/possession/structured_loss.py#L19): exact three-state chain negative log likelihood. Unary and transition scores train jointly. Its own documentation distinguishes a boundary transition potential from a weighted-BCE posterior correction; inference must use the corresponding semantics.
- [possession/spell_loss.py](https://github.com/7dracoder/more-than-a-hack-2027/blob/e00af106d13b0424688a7d723d3bd7f242046958/possession/spell_loss.py): differentiable soft-IoU over complete H/A training runs, excluding crop-censored/unknown boundaries. This is an implemented candidate objective, not proof of improvement.
- [possession/features_v19.py](https://github.com/7dracoder/more-than-a-hack-2027/blob/e00af106d13b0424688a7d723d3bd7f242046958/possession/features_v19.py): local relative geometry and contact-related features beyond nearest distance.

**Why it may add evidence.** A native-rate boundary model can distinguish a brief controlled recovery from smoothing flicker using several frames of coordinated ball/player motion. Joint training avoids treating a selected path's confidence as if it were a calibrated marginal. This directly addresses our rejected candidate's confidence/decoder mismatch, but it requires a new model/evaluation contract rather than attaching its scores to the old decoder.

**Evaluation evidence.** [LOCAL_V07.md](https://github.com/7dracoder/more-than-a-hack-2027/blob/e00af106d13b0424688a7d723d3bd7f242046958/LOCAL_V07.md) reports an earlier frozen clean ensemble on two external held-out DFL matches: spellF1 0.73174 versus 0.64297 for its reference, +0.08877. The newer gap-trained model was not independently tested. [CoreOrigin.md](https://github.com/7dracoder/more-than-a-hack-2027/blob/e00af106d13b0424688a7d723d3bd7f242046958/CoreOrigin.md) reports 0.85700 on a repeatedly used development match, explicitly without a current independent cohort. That number is not an unseen-match result.

A later [realistic-gaps research README](https://github.com/7dracoder/more-than-a-hack-2027/blob/e00af106d13b0424688a7d723d3bd7f242046958/scripts/research/realistic_gaps/README.md) describes unfreezing DFL's parked stoppage ball and state-tied training gaps. Its proxy spellF1 rises 0.688 → 0.730 while clean spellF1 falls 0.847 → 0.837. This is a useful transfer tradeoff, not independently confirmed natural-gap accuracy. State-tied corruption uses external labels; it should not be our sole evaluation view.

**Reproduction and dependencies.** The local workflow is in [scripts/run_local.py](https://github.com/7dracoder/more-than-a-hack-2027/blob/e00af106d13b0424688a7d723d3bd7f242046958/scripts/run_local.py) and [requirements-local-gpu.txt](https://github.com/7dracoder/more-than-a-hack-2027/blob/e00af106d13b0424688a7d723d3bd7f242046958/requirements-local-gpu.txt). The earlier workflow uses Python/PyTorch, CUDA, NumPy, SciPy and scikit-learn; the author reports a 12 GB laptop GPU. There is a committed 3.6 MB checkpoint under models/coreorigin-v10/, but its relationship to each historical report must be established before use. The realistic-gap README and older requirements mention different runtime versions; a fresh pinned environment and source/config/checkpoint audit are needed. Do not combine historical commands blindly.

**Rights and exclusions.** The pinned [LICENSE](https://github.com/7dracoder/more-than-a-hack-2027/blob/e00af106d13b0424688a7d723d3bd7f242046958/LICENSE) is the inherited MIT repository licence. DFL/IDSSE is attributed as CC BY 4.0; competition assets are separate. An unrelated YOLO checkpoint is also present, with no role established in the inspected possession method; do not assume the MIT file grants rights to third-party detector weights. Older public-label runners are explicitly historical. No match-specific correction script, hand annotation, anchor constant, challenge prediction or checkpoint was imported here.

**What is missing in ours / risk.** We lack a tested learned transition-evidence objective and native-rate brief-spell experiment. The main risks are reusing the same seven DFL matches as if they were fresh validation, repeated development selection, provider-label mismatch and overconfident results on synthetic gaps. Start with one modest TCN plus a matched decoder, not the entire multi-stage residual research stack.

## 2. GTT-TalentArena/more-than-a-hack-2027

Pinned revision: [bf4f994c9711a56c1432fbe71d1a554040af600c](https://github.com/GTT-TalentArena/more-than-a-hack-2027/commit/bf4f994c9711a56c1432fbe71d1a554040af600c).

**What exists.** Multiple same-challenge candidates, a common data contract, synthetic tests and an external evaluation service. The strongest contribution for us is [heldout/README.md](https://github.com/GTT-TalentArena/more-than-a-hack-2027/blob/bf4f994c9711a56c1432fbe71d1a554040af600c/heldout/README.md) and [heldout/degrade.py](https://github.com/GTT-TalentArena/more-than-a-hack-2027/blob/bf4f994c9711a56c1432fbe71d1a554040af600c/heldout/degrade.py): clean/short-gap/long-gap/crowded/full profiles, deterministic seeds, crowd-weighted missing-ball intervals, coordinate noise and reassignment into anonymous team slots. Corruption is a function of positions, not possession labels. The documented tests check that removing/shuffling targets leaves model observations byte-identical.

[solution/a_dfl/model.py](https://github.com/GTT-TalentArena/more-than-a-hack-2027/blob/bf4f994c9711a56c1432fbe71d1a554040af600c/solution/a_dfl/model.py) uses odd H-minus-A collective features with no intercept, so swapping teams negates its logit. A source hash guards feature/weight compatibility. [solution/a_opus/decode.py](https://github.com/GTT-TalentArena/more-than-a-hack-2027/blob/bf4f994c9711a56c1432fbe71d1a554040af600c/solution/a_opus/decode.py) contains Viterbi, hysteresis and contact/restart dating alternatives.

**Why it matters.** Our frozen external model needs tests that reproduce long missing-ball spells and unstable slots, without leaking targets into the observations. This harness tests whether collective dynamics genuinely recover ownership and whether decoder gains survive degraded evidence. It is more useful than reproducing another nearest-team baseline.

**Evaluation evidence.** [solution/a_dfl/README.md](https://github.com/GTT-TalentArena/more-than-a-hack-2027/blob/bf4f994c9711a56c1432fbe71d1a554040af600c/solution/a_dfl/README.md) reports five-match leave-one-match-out development across degraded views: mean spellF1 0.4382 versus 0.4247 for candidate A. It candidly attributes most gain to cases where A failed to fit its own ball-free model; when A has a model in both halves the variant effectively ties. The reserved comparison is documented as not run. Thus this is stronger evidence for the harness and fixed model discipline than for a large missing model gain.

**Reproduction and dependencies.** Documented external commands are heldout fetch/convert/run/report, with 21 DFL files (~2.6 GB), kloppy and Docker optional orchestration. Runtime candidate A is CPU NumPy with pandas for evaluation, pinned in [solution/a_opus/requirements.txt](https://github.com/GTT-TalentArena/more-than-a-hack-2027/blob/bf4f994c9711a56c1432fbe71d1a554040af600c/solution/a_opus/requirements.txt). The DFL replacement has public coefficients in solution/a_dfl/weights.py; no binary weight download is required. Source/config/runtime hashes invalidate stale runs.

**Rights and exclusions.** [MIT licence](https://github.com/GTT-TalentArena/more-than-a-hack-2027/blob/bf4f994c9711a56c1432fbe71d1a554040af600c/LICENSE), with competition assets excluded; DFL CC BY 4.0 attribution required. Candidate A includes match-local pseudo-supervision and self-calibration; the DFL replacement freezes only its collective submodel, not the entire pipeline. Our adaptation should isolate the evaluation harness and externally learned symmetric evidence, not inherit all per-match fitting or dating heuristics.

The exact file is the inherited **MIT License, copyright 2026–2027 Metrica Sports**, with an explicit scope paragraph covering repository source/documentation and excluding competition video, tracking, tagging and homography. Source reuse must retain its copyright/permission notice. The file grants no access or redistribution rights to the excluded assets; DFL rights come from DFL's own licence. No source or coefficient was copied by this scout. Before later adoption, retain file-level provenance and check any additional dependency/third-party notices rather than treating the top-level licence as a grant for every external component.

The inspected degradation fixes a missing-share target per half, samples truncated exponential gaps, weights some gap starts by players near the clean external ball, and optionally fragments tracks into free same-team slots with small coordinate noise. These are explicit simulator assumptions. It does not simulate whistle semantics, broadcast edits, aerial projection or every provider error, and it can retain the clean provider's frozen-stoppage shortcut. Its original reserved matches are reserved for that team, not automatically for our workspace. Adopt the position-only observation/target separation and paired-view design; choose a bounded range of generic profiles before our runs and keep label-conditioned augmentation in a separate training-only branch.

**What is missing in ours / risk.** A matched, label-blind stress benchmark with identity fragmentation and explicit cache identity. The simulator's chosen missing share and durations are assumptions, not validated natural-gap ground truth. Use several plausible profiles and require gains across them, including no-ball periods, without selecting a challenge-specific possession count.

## 3. danieltyukov/more-than-a-hack-2027 — Frame Control

Pinned revision: [3ef24dc2b15fc560fe1d3f05f75b842b8606e8e6](https://github.com/danieltyukov/more-than-a-hack-2027/commit/3ef24dc2b15fc560fe1d3f05f75b842b8606e8e6).

**What exists.** A CPU boosted-tree pipeline described in [docs/technical-report.md](https://github.com/danieltyukov/more-than-a-hack-2027/blob/3ef24dc2b15fc560fe1d3f05f75b842b8606e8e6/docs/technical-report.md). Three classifiers model dead/alive, live team and dead-ball restarter. [possession/framefeatures.py](https://github.com/danieltyukov/more-than-a-hack-2027/blob/3ef24dc2b15fc560fe1d3f05f75b842b8606e8e6/possession/framefeatures.py) supplies projected ball interception distances, relative speed, sustained-control history and team-shape trends. [possession/segment.py](https://github.com/danieltyukov/more-than-a-hack-2027/blob/3ef24dc2b15fc560fe1d3f05f75b842b8606e8e6/possession/segment.py) was inspected: the state space is H, A, D-home-restarter and D-away-restarter. A restart can only enter its predicted owner's live state.

[Possession degradation](https://github.com/danieltyukov/more-than-a-hack-2027/blob/3ef24dc2b15fc560fe1d3f05f75b842b8606e8e6/possession/degrade.py) explicitly replaces DFL's frozen stoppage-ball trajectories with rolling/carrying trajectories, adds correlated noise, player dropout and aerial ground-plane projection error. This targets a concrete shortcut that a clean DFL tree can learn.

**Why it matters.** Nearest distance is not an interception or control model. A few projected-distance and relative-motion features can distinguish a ball passing close to an opponent from a plausible controlled reception. Restart-owner memory could resolve the first live owner after a gap using evidence accumulated during the stoppage. These are bounded additions to our tree baseline.

**Evaluation evidence and disqualification of parts.** The report gives seven-match leave-one-match-out spellF1 0.610 and macroF1 0.914; this scout did not reproduce it. Crucially, the same report states that final broadcast weights and a systematic timing correction were fitted on public challenge labels; it also selected some variants using that window. Those final settings and public-window results are unsuitable evidence for our clean next phase. Its degradation accepts external labels to choose stoppage/live corruption. That is a possible training augmentation, not a label-blind evaluation simulator.

**Reproduction and dependencies.** Python 3.11 with NumPy, pandas, SciPy, scikit-learn, Numba and lxml, pinned in [requirements-possession.txt](https://github.com/danieltyukov/more-than-a-hack-2027/blob/3ef24dc2b15fc560fe1d3f05f75b842b8606e8e6/requirements-possession.txt). Six tree-model pickles are committed. The report documents scripts/train.py --cv-only and two swapped/unswapped full training runs, about half an hour each on the author's 32-core machine. Prefer retraining in an isolated environment rather than loading third-party pickle files.

**Rights and adaptation.** [MIT repository licence](https://github.com/danieltyukov/more-than-a-hack-2027/blob/3ef24dc2b15fc560fe1d3f05f75b842b8606e8e6/LICENSE); DFL CC BY 4.0; challenge assets separate. Adapt only generic geometry, training augmentation and latent-state ideas with externally selected parameters. Do not transfer broadcast offsets, public-fitted weights, timing shifts or fixture-specific anchors. No OCR is required by the generic trajectory-alignment idea, but alignment must pass our own automatic validation before using any broadcast feature.

**What is missing in ours / risk.** Projected contact geometry and a clean audit of frozen-ball shortcuts may be missing; ordinary history/context trees may already cover part of this. Add one group at a time. Restarter constraints can lock in an incorrect owner; aerial projection can make a confident nearest-player decision physically wrong.

## 4. maxoubvd/MYA-more-than-a-hack-2027 — MYA

Pinned revision: [a913db3248a13b355690f4b521a3dd2e5c01c820](https://github.com/maxoubvd/MYA-more-than-a-hack-2027/commit/a913db3248a13b355690f4b521a3dd2e5c01c820).

**What exists.** [MYA.md](https://github.com/maxoubvd/MYA-more-than-a-hack-2027/blob/a913db3248a13b355690f4b521a3dd2e5c01c820/MYA.md) describes three small logistic heads: live/dead, visible-ball team, and collective fallback. [src/models/observations.py](https://github.com/maxoubvd/MYA-more-than-a-hack-2027/blob/a913db3248a13b355690f4b521a3dd2e5c01c820/src/models/observations.py) and [src/sequential/viterbi.py](https://github.com/maxoubvd/MYA-more-than-a-hack-2027/blob/a913db3248a13b355690f4b521a3dd2e5c01c820/src/sequential/viterbi.py) were inspected. The state head excludes player-ball control evidence, avoiding the shortcut that a player near a stationary ball means play is live. Odd team-difference inputs have symmetric scaling and no intercept. Learned H/A-pooled transitions provide soft persistence without a minimum-duration deletion rule.

**Evidence and negative result.** The declared protocol has four train, two confirmation and one post-freeze final-test DFL match. The author reports final external mean spellF1 0.4064 versus baseline 0.2399 over 19 corruption conditions on one held-out match. Those are 19 views of one match, not 19 independent tests. [Sequential documentation](https://github.com/maxoubvd/MYA-more-than-a-hack-2027/blob/a913db3248a13b355690f4b521a3dd2e5c01c820/docs/SEQUENTIAL_DECODING.md) explains score margins and conditional boundary profiles without calling them confidence intervals. Dynamic physical transition cues did not beat the static reference; short-possession recall remained low. That is a useful reason not to assume a more elaborate decoder fixes missing observations.

**Reproduction and dependencies.** The final inference command is mya.py --verify, followed by mya.py with an authorized ATD bundle. [release/README.md](https://github.com/maxoubvd/MYA-more-than-a-hack-2027/blob/a913db3248a13b355690f4b521a3dd2e5c01c820/release/README.md) documents small JSON weights and a source/model manifest. Runtime is CPU Python 3.12.6 plus pinned NumPy/pandas dependencies in [requirements-inference.txt](https://github.com/maxoubvd/MYA-more-than-a-hack-2027/blob/a913db3248a13b355690f4b521a3dd2e5c01c820/requirements-inference.txt). We did not run reproduction or inspect challenge outputs.

**Rights and adaptation.** No LICENSE/COPYING file was found in the inspected recursive tree. Public visibility is not permission to copy its implementation or shipped weights. Treat this as an architectural/experimental reference and write our own implementation if useful; no code or weights were copied. DFL data is documented as CC BY 4.0, which does not by itself license this repository's authored code.

**What is missing in ours / risk.** A simple factorized state head and honest short-spell guardrails may be useful, but much overlaps our current frozen tree and rejected temporal experiment. Lower priority than new contact/boundary evidence. The final package also incorporates published fixture constraints; do not import those as new evidence or match-specific setup.

## 5. hyunsungkim-ds/pathcrf — related research, not a challenge solution

Pinned revision: [1b7c6f85a6b78c92e4543fde72ca2b86a933f997](https://github.com/hyunsungkim-ds/pathcrf/commit/1b7c6f85a6b78c92e4543fde72ca2b86a933f997).

**What exists.** Official implementation of [PathCRF: Ball-Free Soccer Event Detection via Possession Path Inference from Player Trajectories](https://arxiv.org/abs/2602.12080), linked by its [README](https://github.com/hyunsungkim-ds/pathcrf/blob/1b7c6f85a6b78c92e4543fde72ca2b86a933f997/README.md). It represents a player holding the ball as a self-loop, and a traveling ball as a directed player-to-player edge. A CRF enforces connected transitions between these edge states. That is more expressive than independent H/A/D frame classification.

Inspected [models/dynamic_sparse_crf.py, lines 60–128](https://github.com/hyunsungkim-ds/pathcrf/blob/1b7c6f85a6b78c92e4543fde72ca2b86a933f997/models/dynamic_sparse_crf.py#L60), [models/set_lstm.py](https://github.com/hyunsungkim-ds/pathcrf/blob/1b7c6f85a6b78c92e4543fde72ca2b86a933f997/models/set_lstm.py) and [evaluate.py](https://github.com/hyunsungkim-ds/pathcrf/blob/1b7c6f85a6b78c92e4543fde72ca2b86a933f997/evaluate.py) confirm that the logical transition graph, trainable scoring and evaluation entry point exist.

**What could transfer.** An explicit control-versus-transfer latent state gives a plausible mechanism for preserving the last controlled team through an airborne pass or duel while requiring a coherent reception to create turnover. An identity-free team-level simplification might be a research fork. This is not a drop-in gap filler.

**Evaluation/reproduction.** The README documents Sportec/DFL preprocessing, event synchronization with the authors' ELASTIC code, training scripts and an inference/evaluation notebook. Five saved model families are present, including dynamic masked CRF checkpoints. [scripts/ballradar_crf.sh](https://github.com/hyunsungkim-ds/pathcrf/blob/1b7c6f85a6b78c92e4543fde72ca2b86a933f997/scripts/ballradar_crf.sh) selects a 5 Hz model, set/sequence attention and sparse dynamic CRF. No quantitative paper advantage was independently checked here and no result is claimed on this challenge. Do not compare event-tolerance metrics with possession spellF1.

**Dependencies and rights.** [MPL 2.0 licence](https://github.com/hyunsungkim-ds/pathcrf/blob/1b7c6f85a6b78c92e4543fde72ca2b86a933f997/LICENSE), with its source-file obligations relevant if code is adapted/distributed. No separate weight licence was found in the inspected documentation; confirm scope before redistribution. [requirements.txt](https://github.com/hyunsungkim-ds/pathcrf/blob/1b7c6f85a6b78c92e4543fde72ca2b86a933f997/requirements.txt) is unpinned and omits PyTorch despite code importing it, and preprocessing additionally requires kloppy. A reproducible environment must be completed. DFL training/event data has its own attribution requirements.

**Mismatch / cost.** Its states assume stable player indices and 11-player team partitions, unlike anonymous fragmented ATD slots. It uses aligned events to build supervision; data from other games can be permissible, but challenge events cannot be substituted. Its public weights were trained on the same small DFL pool used by several challenge entries and possibly our baseline. Those matches cannot become fresh validation just because the model comes from another repository. Adapting the full player graph is high cost; projected control/transfer features are the nearer-term idea.

## Recommended clean experiment sequence

1. **Audit the baseline's external shortcut exposure.** On already permitted external data, compare native inputs, label-blind long/crowded gaps and slot fragmentation; keep true targets unchanged. Add a separate training-only state-tied/unfrozen-ball augmentation ablation. Never use label-dependent corruption as the sole claimed natural-gap test.
2. **Run one native-rate state/boundary model.** Use existing coordinates/masks and a small TCN. Compare matched unary-only training against joint chain training, with one predeclared decoding scale. Record how conditional confidence, transition potentials and decoded decisions are defined; do not reuse the rejected candidate's mismatched calibration.
3. **Test contact evidence before enlarging the model.** Add relative ball/player motion, projected interception and sustained opponent-control context. Score actual turnover/stoppage boundaries, short spells and false splits, not coverage or the percentage of X filled.
4. **Require a real gain on frozen external matches and several degradation profiles.** A model needs enough new evidence to recover spells, including short recoveries, without more false splits. Preserve any cohort already opened in this workspace as development; a repository's “held out” split is not automatically independent for us.
5. **Keep camera work gated on alignment.** No result here justifies using our unqualified OCR alignment. Trajectory-set alignment is an optional future algorithm to validate, not a source of borrowed offsets or fixture constants.

## Search log and rejected leads

Search used the GitHub connector's public repository search, public GET/file fetch and repository tree metadata, supplemented by web search. All shortlist links above are commit-pinned. No authors were contacted; no private source, challenge ground-truth file, match video/tracking asset, framewise prediction or manual label was fetched. Source/docs sometimes discuss historical challenge diagnostics; those were screened for contamination and were not used to choose settings here.

Queries:

- GitHub repository search: `"More Than a Hack"` (100 results returned), `Metrica possession`, `football possession tracking`.
- Web: `github "Metrica" "More Than a Hack"`; `github "Hack2027" possession`; `github football possession tracking inference`.
- Web: `site:github.com "more-than-a-hack-2027" possession solution`; `site:github.com "Metrica" "possession" "challenge"`; `site:github.com soccer "possession" CRF ballradar`; `site:github.com "ball possession" "hidden Markov" tracking`.

Rejected or lower-priority leads:

| Lead | Why not shortlisted / limitation |
|---|---|
| [Official Metrica 2027 starter](https://github.com/metrica-sports/more-than-a-hack-2027/tree/f8f2629ff1e0985f81d7e59d8413678514ee1530) | Authoritative starter and rules, not an independent solution. Nearest-player/vote baseline already represented in ours. |
| MohamedBadr-14 and Alberstation same-name repositories | Tree inspection showed predominantly the starter; no added possession source implementation in the inspected Python tree. Larger repository size alone was not evidence of a stronger method. |
| amplius-devs same-name repository | Added pipeline/features/possession Python files were zero-length in the inspected tree. Planning material is not a working method. |
| ShrodengerCat/More-than-a-hackathon--ARGUS-XI- | Added only a few small baseline/heuristic solution files; no stronger independent evaluation evidence surfaced. |
| darfattt/mtah-2027-possession | Compact same-challenge baseline/priors/smoothing package. Lower evidence and novelty than the shortlisted model/evaluation systems; its source tree was screened, not performance-reproduced. |
| ZesterJ/more-than-a-hack-2027 | Real external-only benchmark exists, with contact-duration/Viterbi variants. Its documentation also retains earlier public-window trained/compared model results and a labeler. The cleaner external pipeline is plausible but mostly overlaps our tree and the shortlisted harnesses; historical public scores are not evidence for our selection. |
| gabrynapo/more-than-a-hack-2027 | Added alignment/features/model/refinement source exists. Not enough verified evaluation provenance inspected to place above the shortlist; no claim that the method is invalid. |
| [tryolabs/soccer-video-analytics](https://github.com/tryolabs/soccer-video-analytics) and common YOLO/OpenCV football-analysis clones | Generic video demos rather than same-challenge spell evaluation. Detection/tracking/team-colour pipelines and proximity possession do not resolve our present evidence gap by themselves. |
| Earlier More than a Hack / 2026 projects | Different open-ended challenge; not comparable 2027 H/A/D/X possession solutions. |

### Interpretation limits

These are method leads, not a ranking of entrants. Their absolute scores use different splits, label conventions, rates, corruptions and selection histories. Static inspection verifies that a mechanism is implemented; it does not verify author performance, execution reproducibility, checkpoint provenance or natural-gap transfer. No repository method was promoted to our source or baseline during this scout.

