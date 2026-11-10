# Gap rule and observed-only touch addenda — 10 November 2026

Status: implementation and full-suite verification complete; external harm check pending. No scientific evaluation has run in this new experiment.

## Scope and preserved history

The user explicitly approved both addenda, retaining the fixed12m/s cap and restricting the scale test to unchanged eligibility, and authorized using their written aggregate claims because the named probe-results.json is absent. All854 files from the prior completed state at a5d5aa3 remain byte-identical, including the original touch experiment, its rejected result, frozen protocols, score receipts and release artifact.

The new branch is codex/gap-rule-touch-addenda-2026-11-10. New gap_liveness.py and observed_touch.py sit beside the archived code; no previous predictor, sealed result or source file was modified.

## Fixed gap rule

At every fifth canonical25Hz frame, match associated (team,id) pairs to the frame one second earlier within the same contiguous period. Discard displacement speeds>=12m/s; require10 known pairs and take their median. Unknown identities are excluded; known duplicate ids are errors. Match reference speed is the median sampled value outside ball gaps longer than75frames. A long gap is D only when its defined median is strictly lower than that reference. Undefined reference/gap speed preserves the control.

The new materialisation wrapper starts from the incumbent's fully materialised labels and patches only selected gap/restart frames. Every other frame remains identical. This avoids allowing a newly inserted D to propagate beyond the explicit rule mask.

Restart extension is literal: compare first reappearance to the last observed pre-gap ball position, times25, and keep D while speed<=.5m/s for at most250frames. No earlier observation, a large first displacement, a missing frame, a period change or a moving ball stops extension. A newly visible stationary ball at a different position therefore receives no extension; the rule was not silently changed to assume zero first-frame speed.

No Smart Tagging, reference labels, learned classifier or challenge-specific frame constant enters this pure standard-library module.

## Observed-only touch amendment

Only within-run kink touches are returned. Reacquisition events are excluded. The last-toucher bonus terminates at the first missing frame and cannot resume after that gap without a new touch. Missing emission rows remain bit-identical neutral control rows. The period, next-touch and ten-second expiry rules and the variable decoder's tie order are preserved. No-events and disabled-effects prediction objects match all existing release fixtures.

This amendment has6 targeted tests and has not been scientifically evaluated. The priority gap goal runs first. The previous touch grid, decision and exhausted budget remain untouched.

## Prospective external harm check

The separately owned budget is30 control and30 paired gap-rule scores: the same15 already-used external matches, natural and mask30-seed1729. There is no grid. The primary has13 fitting-disjoint matches, equal provider weight and equal match weight within provider; the two DFL fitting overlaps are secondary. Natural control must reproduce .551816 before the rule is scored; masked .469149 is checked too. Natural primary may lose at most .005, and no natural provider mean may lose more than .01. Masked results are reported and do not gate.

Control labels are generated once and stored privately with hashes, then reused for the paired rule case. Every completed aggregate is retained provisionally before post-score validation. Original freeze/map/source/doc identity and all label files are checked before dependent claims. The complete protocol is prospectively committed before scientific scoring.

If4a fails, keep the original control and stop dependent Metrica, challenge and release work. If it passes, separately pin and test all three public Metrica samples and the committed event-reference mapping before one sample evaluation. This check is partly circular: tracking is manually corrected and the ball disappears largely during dead play. Challenge self-consistency is then one aggregate-only run, never a tuning pass. Public-window/release execution still requires the handoff's separate go-ahead.

## Evidence and limitations

- No clean labelled source has the challenge's long-gap structure. The expected benefit is argued from label-free evidence, not a measured challenge gain.
- The addenda's narrative gap/speed/tag statistics are user-supplied evidence. Their missing underlying JSON receipt is not independently verified. No Stage0 rerun was performed.
- Their approximate51px standing-player estimate differs in measurement convention from our earlier22.4px planar-width proxy; both drop pose under100px. Neither old receipt is overwritten.
- Same-source identity association errors, missing players and the cap can make speed statistics undefined or biased. The reference is computed anew from the match, not hard-coded.
- All15 external matches have already been used; this is a harm check on used evidence, not a fresh hidden-score estimate.

Pre-score targeted verification:23 gap-rule tests,17 protocol tests and6 observed-touch tests pass. One fresh-context code/protocol review and one failing-first fix pass precede scoring. Full-suite counts, freezes, numerical outcomes and final recommendation will be appended below.

## Full-suite verification

The fixed-source run passed654 collected tests:633 executed,21 environment skips,zero failures/errors. The baseline group remains608 total/21 skips/587 executed; all46 addendum tests execute. The unchanged frozen artifact was rebuilt with SHA-256 e8d35e15be9524270bed82352791dc2849087b49b4c2b59c191023954b19eddb. No Python source changed after this successful run. The public count receipt is reports/gap-liveness/full-suite.json.
