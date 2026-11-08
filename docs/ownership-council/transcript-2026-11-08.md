# Ownership-swap Council — 8 November 2026

Protocol: user's supplied llm-council SKILL.md, with task-specific thinking lenses. Five independent advisors, five fresh anonymous reviewers, then a separate chairman. All use isolated contexts; the same model family supplies thinking-style diversity, not independent model vendors. Host capacity requires3+2batches per round. No advisor sees another response before completing stage1. Framed question: `next-phase-notes/ownership-council/framed-question.md`.

## Framed question and shared context

# Framed council question — 8 November 2026

What explains the remaining home/away (H/A) possession swaps in this frozen football-possession candidate, what evidence would discriminate those explanations, and which bounded next experiment should be planned? Challenge the premise of retraining as well as the alternatives. Recommend a concrete diagnostic first action and explicit evidence that would change your recommendation. Do not assume a model replacement is warranted.

H means one team's live possession, A the other team's live possession, D dead ball and X abstention/unknown. The objective includes official possession-spell F1 (IoU thresholds .3–.7), frame accuracy and ownership-change timing. Filling X or increasing smoothing can improve one number while making other decisions worse.

## Current facts, not a preferred explanation

The current experimental candidate uses a frozen31-node H/A/D tree over geometry/history, then finite three-state offline Viterbi with motion weight0 and switch cost32. Missing ball coordinates give equal H/A/D emissions; observed-ball emissions are unchanged. Invalid/insufficient geometry is a barrier. A wholly unsupported usable segment is latent X. Structural-period carry is separate; a wholly-X active period falls back to D by convention. That convention is explicitly counted. The tactical head itself is not H/A-equivariant.

The last single-candidate experiment was frozen before scoring and passed seven declared checks separately on3previously examined validation and10previously examined regression matches, under natural and deterministic30% ball masking. SkillCorner masked mean frame accuracy improved75.78%→82.27%; DFL masked accuracy84.40%→87.46%, D recall92.64%→95.72%. Natural equal-provider spellF1 .564642→.566428. Some individual matches and missed-boundary counts worsened. No fresh full-state holdout or target accuracy is established.

A read-only pooled-confusion audit of the current natural regression outputs found:

- SkillCorner:612173known-live reference frames,85629errors;85557are H/A swaps and72false D. Of the swaps,75558occur among570001frames with finite ball coordinates,9999among42172without them. Coordinates being available does not verify freshness or player control.
- DFL:288371known H/A/D frames,20646errors;19549H/A swaps,349false D,748missed D.
- Masked SkillCorner:107730H/A swaps and321false D among612173known-live frames. Masked DFL:23695H/A swaps,6573false D and5809missed D among288371known frames.

These are counts on seen regressions, not fresh accuracy estimates. Natural SkillCorner's roughly99.9% H/A share of errors is conditional on a reference that annotates known-play H/A only; it cannot establish real stoppage quality.

The tree's features include team distances to ball, distance margin, ball position/speed, recent/slow speed, missing-ball age and remembered geometry-based control. Automatic remembered control updates after six consecutive geometry candidates. Feature history resets on structural period changes; it is not a verified identity/control history. A separate frozen40-tree H/A motion head was trained predominantly on incumbent-X rows. A prior16-setting soft-decoder comparison selected its weight0; that does not prove all motion information is useless.

## Evidence constraints

- All7licensed DFL and20licensed SkillCorner matches have already been examined. Existing development matches may be used for root-cause exploration; previously opened validation/regression results must remain labeled seen data.
- DFL has full-state provider labels but almost-frozen inactive ball coordinates; SkillCorner has known-play H/A phase labels, with unknown outside those phases, and cannot independently validate D. Some external player coordinates use identity-assisted interpolation. These are provider references, not certified independent human gold.
- Never access challenge GT/video, target raw assets or target frame-level CSVs. Never tune or hand-label that match, upload its assets, or use its output distribution as a selection objective. Challenge output correctness is unmeasured.
- Read-only source/evidence audit only. No predictor edits, fitting, new dependency installation, new target inference or hidden parameter search. Advisors receive this same factual brief independently; no other advisor output is shared in stage1.
- A model's agreement with other agents is not empirical verification. Distinguish observed findings, plausible hypotheses and decisive tests.

## Council execution

Use the user's supplied five-advisor method, adapted only for task relevance. Three concurrent-worker slots require3+2batches per round; no results are shared between advisors. Collect150–300word independent responses. Then shuffle/anonymize them as A–E and give five **fresh** reviewers all responses, asking strongest response, largest blind spot, and what all five missed, under200words. A separate chairman receives the de-anonymized responses and reviews and writes agreement, clashes, blind spots, recommendation and one first action.

Any new empirical diagnosis completed during stage1 will be provided identically to every reviewer/chair as a factual addendum, not as another advisor's opinion. No installation of a third-party Council application is implied.

## Stage1: Independent advisor responses

### The Contrarian

**Test reference alignment and possession semantics first.** The observed fact is that H/A disagreements dominate these seen regressions. That does not establish that the predictor repeatedly assigns objectively controlled balls to the wrong team. Finite coordinates establish availability; provider phase labels establish a reference convention. Neither certifies contemporaneous control.

My first-ranked hypothesis is a mismatch between instantaneous control and provider possession phases, compounded by timestamp alignment. Second is stale or interpolated geometry and self-reinforcing remembered control. Model capacity comes third. A global H/A reversal is unlikely given aggregate accuracy, but period-local team mapping still deserves a mechanical check.

First action: build a read-only discrepancy ledger on one existing development match per provider. Preselect ten H/A disagreement episodes and ten matched agreement episodes per match, covering phase boundaries and phase interiors. Record native timestamps, resampling rules, period/team mapping, reference transition times, coordinate provenance, and the six-candidate remembered-control timeline. Preserve episode-level context; thousands of adjacent frames are not thousands of independent failures.

The decisive check is whether disagreements persist well inside independently verified, unambiguous control intervals after mapping and alignment are checked. Where licensed development evidence permits, adjudicate those intervals blind to predictor output using a declared control rubric. Without independent evidence, the result remains a consistency audit.

If persistent interior errors survive those checks, a bounded feature/history diagnostic is justified. If disagreements primarily track reference boundaries or stale geometry, address that evidence problem first. Neither outcome yet justifies retraining: all available matches are seen, and another favorable comparison can overfit the investigation itself.

### The First Principles Thinker

Possession is a latent ownership claim, not a distance measurement. Nearest player, actual control, continuity through a loose ball, and provider-assigned phase ownership can legitimately disagree. An H/A/D-only system must assign contested live intervals to somebody; X can expose uncertainty but cannot define the correct owner.

**First explanation to test:** the remaining swaps substantially reflect a mismatch between geometry-based control and provider possession-spell semantics, especially around releases, interceptions and contested intervals. This is a hypothesis, not an inference established by the confusion counts. Finite ball coordinates establish neither freshness nor control. The tree’s remembered geometry repeats its own assumptions; it supplies no independent ownership evidence.

The concrete first action is a read-only audit of the providers’ operational definitions alongside existing swap runs on seen development matches. Measure swap-frame concentration by distance from reference ownership changes, run duration, and persistence of the observed geometry candidate. Keep provider results separate. Inspecting a deterministic sample can explain patterns; measuring the complete distribution establishes whether those patterns account for much error.

The minimum observation against the transition-semantics explanation would be substantial swap mass deep inside long reference spells, with persistent, usable geometry favoring the reference owner. That would redirect attention toward feature history, asymmetric tree decisions or decoder persistence. It would still not certify actual control.

Only then justify a bounded experiment: evaluate frozen predictions and emissions under a consistent H/A team-identity exchange on seen development data. Unexpected failure to exchange outputs would demonstrate implementation asymmetry, though its contribution to natural errors would remain to be measured. Retraining before separating semantic disagreement from identifiable decision failure risks learning the ambiguity more confidently.

### The Expansionist

**First-ranked hypothesis:** the remaining swaps disproportionately reflect ownership context discarded by instantaneous geometry and geometry-derived memory—especially passes where the ball approaches opponents before reaching its intended receiver. Finite coordinates do not establish control. This is plausible, not demonstrated; the rejected motion head, trained predominantly on incumbent-X rows, does not settle whether relational motion helps observed-ball swaps.

The first action should be a read-only, event-level audit on seen development matches. Group contiguous H/A errors into episodes, and compare them with correctly classified intervals matched by provider, reference team, ball availability and speed. Using existing evidence, measure whether error onset follows a change in the nearest team, whether remembered control changes six candidates later, and whether errors concentrate around reference ownership boundaries or persist within possession spells. Report both episode counts and duration so long failures cannot hide behind many short successes.

**Minimum falsifier:** if swaps remain comparably frequent during sustained, low-speed possession with stable geometry, and show no enrichment around transit or memory updates, passing-context recovery should lose priority. Long one-directional failures would instead elevate team asymmetry or reference alignment.

If the audit supports the hypothesis, the bounded next experiment should keep model capacity and decoder fixed, comparing the current head with an all-frame-supervised head using relative player–ball motion and receiving context, with paired H/A training symmetry. Predeclare provider-specific spell F1, swap duration, frame accuracy and ownership-change timing; reject gains purchased through extra boundary delay or worse D/X behavior. Seen-match improvement would justify seeking independent evaluation, not establish generalization.

### The Outsider

First test whether predictions and references represent the same team, time and possession definition. The brief establishes disagreement with provider labels; it does not establish which side is correct. Team mappings, timestamp alignment and the distinction between proximity, control and possession need explicit verification before “remaining swaps” becomes a model diagnosis.

The coordinate counts do not resolve this. Finite-coordinate frames account for approximately93%of SkillCorner’s known-live frames and88%of its swaps. Their swap rate is approximately13.3%, versus23.7%without coordinates. Most swaps occurring with coordinates therefore does not show that missingness is unimportant, or that available coordinates are trustworthy.

My first action is a bounded, read-only provenance audit on seen development data: select12swap episodes using a declared rule, plus12correctly classified comparison windows matched by period and ball availability. Inspect existing team-ID mappings, timestamp transformations, reference definitions and history-reset behavior. Record what can actually be established for each episode; do not manufacture human gold from agreement among derived signals.

A minimum falsification of a simple mapping/alignment explanation would be verified consistent team mappings and time alignment across those windows, with persistent interior swaps that cannot be explained by documented label semantics. That would justify moving the diagnostic priority to remembered-control errors and decoder persistence.

If provenance checks pass, plan one fixed episode-level analysis of whether wrong ownership starts before decoding and whether remembered control sustains it. Retraining becomes justified only after a repeatable input-to-ownership failure is demonstrated. Neither successful execution nor better seen-set averages supplies that evidence.

### The Executor

**Test persistent wrong-side evidence first:** geometry-derived remembered control may favor the wrong team, and switch cost32may prolong that mistake. This is a hypothesis. The observed dominance of H/A errors establishes the failure category; finite ball coordinates do not establish reliable control evidence.

The smallest useful diagnostic is a reproducible trace of12natural H/A error spells plus12correct live spells, selected deterministically across providers from seen development evidence. Freeze the candidate, selection rule and inspection window before examining traces. For each spell, align reference ownership and structural-period boundaries; frozen tree emissions and decoded state; distance margin, remembered-control value and last update; ball availability and recorded freshness evidence; and team-identity mapping.

Use existing recorded evidence; if required intermediates are absent, specify the missing instrumentation without rerunning inference during this read-only phase.

Classify each inspected error as **wrong emission**, **decoder overriding correct emission**, **identity/reference discrepancy**, or **unresolved**. Count spells and duration separately. Stop after the declared sample; do not expand it merely because the answer is inconclusive.

My leading explanation is weakened if wrong decoded ownership commonly persists while emissions consistently favor the reference team. That would prioritize decoder persistence. Correct geometry and memory paired with systematically reversed emissions would instead prioritize team asymmetry or identity mapping.

Only then justify one bounded experiment: a single decoder counterfactual if decoding causes the errors, or a single remembered-control ablation if history contamination does. Predeclare frame accuracy, spell F1 and ownership-change timing together. Retraining is justified only after demonstrating an emission-level failure that survives identity and history checks; these seen-data diagnostics cannot establish fresh generalization.

## Stage2: Fresh anonymous peer reviews

The Response A–E mapping was shuffled using the system random generator and retained separately. Reviewers saw only the framed question and anonymous responses, not advisor names, mapping, other reviews or source files.

### Reviewer1

1. **C is strongest.** It separates emission errors from decoder effects, specifies frozen traces and comparison spells, and states observations that would redirect the investigation. Its next experiment depends on the diagnosed mechanism rather than assuming retraining is useful. However, “emissions favor the reference” needs a cumulative, segment-level definition.

2. **E has the biggest blind spot.** Its proposed all-frame-supervised head simultaneously changes training coverage, motion features, receiving context and symmetry. Improvement would not identify which change helped or demonstrate that passing-context loss caused the original errors. Its audit could justify investigating those factors, but not that bundled experiment without narrower attribution.

3. **All five miss an explicit treatment of offline Viterbi’s dependence on future evidence across the entire usable segment.** A wrong decoded interval can reflect emissions elsewhere, switch penalties and barrier placement; local emission preference does not establish that decoding caused an avoidable error. The council should require segment boundaries, cumulative path scores and competing-path costs in the diagnostic ledger. This would distinguish weak local evidence from globally preferred persistence and make a subsequent decoder counterfactual interpretable.

### Reviewer2

1. **C is strongest.** It separates emission errors from decoder persistence, identity/reference discrepancies and unresolved cases, with deterministic sampling and explicit stopping rules. Its observations can change the proposed intervention, and it respects the read-only constraint when intermediates are unavailable. The sample can identify mechanisms, though it cannot establish their population contribution.

2. **E has the biggest blind spot.** Its proposed retraining changes supervision coverage, features and training symmetry together. Even a successful comparison would not identify which change helped or establish that passing context caused the original errors. Its falsifier usefully challenges that hypothesis, but the proposed experiment needs a narrower causal contrast after reference and decoder explanations are separated.

3. **All five miss the nonlocal consequences of offline Viterbi.** Future emissions can influence earlier ownership decisions, so error onset near a geometry change or six-candidate memory update need not identify the cause. Episode-local traces could misattribute a globally preferred path to local memory. The council should inspect whole usable-segment evidence, including emissions after each disagreement and the score margin between competing ownership paths, wherever existing records permit. This could distinguish weak local evidence from a distant anchor driving many swaps without changing the predictor.

### Reviewer3

1. **C is strongest.** It separates emission failures from decoder overrides, identity discrepancies and unresolved cases, making the diagnosis actionable and falsifiable. Its predetermined sample, comparison spells and prohibition on rerunning inference respect the evidence constraints. The proposed next experiment follows the diagnosed mechanism. Its small sample can identify mechanisms, however, not establish their contribution to total error.

2. **E has the biggest blind spot.** Its proposed training comparison simultaneously changes supervision coverage, motion features, receiving context and training symmetry. Improvement would not identify which change mattered or validate the passing-context explanation. Boundary enrichment and memory-update timing could also reflect provider semantics or decoder behavior. A single-factor diagnostic should precede that bundled experiment.

3. **All five miss an explicit test of future-context dependence in offline Viterbi.** A wrong ownership interval can be driven by later emissions and segment endpoints, rather than by the geometry or remembered-control update near its onset. The council should plan a fixed analysis of existing emission paths, decoder transitions and segment boundaries, reporting signed onset/offset errors. Any later counterfactual should distinguish backward influence from ordinary persistence before attributing delayed or premature ownership changes to the tactical head.

### Reviewer4

1. **C is strongest.** It separates emission errors, decoder persistence and identity/reference discrepancies, specifies a frozen comparison sample, and explicitly handles unavailable intermediates without violating the read-only constraint. Its proposed next experiment depends on the diagnosed mechanism, making the recommendation testable rather than merely plausible.

2. **E has the biggest blind spot.** Its proposed experiment combines changed supervision, motion/receiving features and training symmetry. Even an improvement would not identify which change mattered or establish the passing-context explanation. Evidence of errors near passes could also reflect reference semantics, alignment or decoder behavior. A single-factor diagnostic should precede that training comparison.

3. **All five miss the implications of offline decoding for causal attribution.** Viterbi can revise earlier ownership using later evidence. Locally reference-favoring emissions alongside wrong decoded states do not, by themselves, demonstrate excessive persistence. The council should inspect complete usable segments and cumulative competing-path scores, including switch penalties, barriers and neutral emissions during missing-ball gaps. That would distinguish a locally misleading trace from a decoder decision actually driven by the suspected mechanism.

### Reviewer5

1. **C is strongest.** Its trace separates emission errors from decoder persistence, identity/reference discrepancies and unresolved cases. That makes competing explanations distinguishable using existing evidence. Its explicit handling of missing intermediates also respects the read-only constraint. The classifications still describe disagreement with provider references, so provenance checks remain essential.

2. **E has the biggest blind spot.** Its proposed experiment simultaneously changes supervision coverage, motion/context features and training symmetry. Even if performance improved, the result would not identify which change helped or establish that discarded passing context caused the swaps. Its transit hypothesis has a useful falsifier, but the subsequent experiment needs one isolated intervention.

3. **All five missed a useful paired diagnostic already available:** compare the same episodes under natural and deterministic masking, using recorded outputs and intermediates where available. Measure where masking introduces, extends, removes or shifts swaps, including effects beyond the masked frames through memory and offline decoding. This could discriminate missing-evidence propagation from errors already present with observed coordinates. Aggregate masked accuracy cannot establish that mechanism, and one deterministic mask would remain a limited perturbation rather than a general missingness model.

## Stage3: Separate chairman verdict

### Where the Council Agrees

The frozen candidate's main natural error on seen regressions is assigning possession to the opposite provider-labeled team. On SkillCorner, known-play phases supply H/A labels and leave play outside those phases unknown. DFL also labels dead ball. Native team-ID and clock checks found no global correction to apply. Neither provider supplies independent truth about who controlled a contested ball.

### Where the Council Clashes

The Contrarian and First Principles Thinker prioritize possession semantics and timing. The Expansionist favors missing pass and receiver context. The Executor favors remembered geometry and decoder persistence. The Outsider points out that exposure changes the interpretation of raw counts.

The four-match frozen replay narrows that dispute. SkillCorner swaps occurred on 3383/10257 missing-ball frames (33.0%) and 13426/151528 observed-ball frames (8.9%). DFL had no missing known-live frames in this sample. Swap rates within two seconds of a known state boundary were24.9%and28.4%for SkillCorner and DFL, respectively. Yet observed reference interiors still contained5602/112356and2883/84921swap frames. Boundary proximity is associated with disagreement and leaves substantial interior error unexplained.

Remembered control opposed the reference on94.2%and92.0%of swap frames. It shares its geometry with the predictor, so this does not establish that memory caused those swaps. Exchanging H/A identities changed690/161785and1194/148231outputs after exchanging them back. That establishes asymmetry, while leaving its contribution to natural errors unresolved.

### Blind Spots the Council Caught

All five fresh reviewers preferred the Executor's trace and challenged the Expansionist's bundled changes to supervision, features and symmetry. These were isolated reviews from one model family. Four identified a substantive flaw in an episode-local trace. Offline Viterbi uses later evidence across the entire usable segment. A locally correct tree decision followed by a wrong final state cannot identify excessive smoothing. In fact, on observed usable known-live rows, decoding corrected more local decisions than it spoiled on both providers, by2720to431and1828to1661. The fifth reviewer proposed paired masking to trace propagation beyond missing frames. That addresses a separate question.

### The Recommendation

Run one whole-segment competing-path diagnostic on the same four natural development matches. Replay the frozen predictor and, at each known-live frame, compare the best complete path constrained to the reference owner with the best constrained to the opposite owner. Record their score difference, cumulative emission and switch-cost contributions, and the signed change in that difference when future evidence is included. Respect barriers and identify structural carry separately. Require the unconstrained replay to reproduce the frozen outputs.

Report swap episodes, duration and signed boundary timing by provider, alongside corresponding agreement frames and their denominators. If later evidence or avoided switches repeatedly overturns reference-favoring evidence across long swap episodes, prioritize a subsequent single-factor decoder test. If emissions already favor the opposite owner through observed interiors, shift attention to geometry and remembered control. If margins cluster near ties at provider boundaries, keep possession semantics unresolved. These outcomes explain decisions against provider references. None establishes physical control or warrants a production refit.

### The One Thing to Do First

Freeze a one-page diagnostic protocol specifying the four match identifiers, path-score calculation, tie handling, episode definitions and replay-equivalence check before inspecting any traces.
