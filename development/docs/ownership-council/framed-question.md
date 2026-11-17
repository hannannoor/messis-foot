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
