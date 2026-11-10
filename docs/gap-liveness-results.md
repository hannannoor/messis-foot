# Gap rule and observed-only touch addenda — 10 November 2026

Status: fixed gap rule passed external4a harm check; Metrica4b source/reference qualification complete, no sample predictions or scores yet.

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

## Stage4a external harm check: pass

Prospective freeze549d42b6f4ee465a84096c0f7e08c96242a090a9, SHA-25668b4635894a506d13b35a70f5102b262820e9b9d86683d43ca98ffacc47fa92a. Thirty control scores reproduced .5518160816768707 natural and .4691488389454344 masked, and every complete control count table exactly matched the archived control. Control results were sealed at fcd384f before the thirty rule scores. Rule results were sealed at e55a0d0. No rule parameter changed afterward.

| Primary equal-provider score | Control | Gap rule | Delta | Gates? |
|---|---:|---:|---:|---|
| natural | 0.551816 | 0.550876 | -0.000940 | Pass |
| mask30-seed1729 | 0.469149 | 0.438025 | -0.031124 | Descriptive only |

| Provider | Regime | Control | Gap rule | Delta |
|---|---|---:|---:|---:|
| skillcorner | natural | 0.596567 | 0.593746 | -0.002820 |
| skillcorner | mask30-seed1729 | 0.555155 | 0.479297 | -0.075858 |
| dfl | natural | 0.553665 | 0.553665 | +0.000000 |
| dfl | mask30-seed1729 | 0.441154 | 0.429656 | -0.011498 |
| wcsf | natural | 0.505216 | 0.505216 | +0.000000 |
| wcsf | mask30-seed1729 | 0.411138 | 0.405122 | -0.006016 |

Natural primary loss .000940 is within .005, and SkillCorner loss .002820 is within .01; natural DFL/WCSF are unchanged and contain no long gaps. Thus4a passes; this establishes no measured gain. The masked primary loss .031124 and SkillCorner masked loss .075858 are retained as material robustness limitations, although random-mask results were expressly nongating.

| Provider | Role | Regime | Long gaps | Stoppage | Relabelled frames | Of these on known reference |
|---|---|---|---:|---:|---:|---:|
| skillcorner | fit-disjoint | natural | 1337 | 494 | 226795 | 10148 |
| dfl | fit-disjoint | natural | 0 | 0 | 0 | 0 |
| dfl | fitting-overlap | natural | 0 | 0 | 0 | 0 |
| wcsf | fit-disjoint | natural | 0 | 0 | 0 | 0 |
| skillcorner | fit-disjoint | mask30-seed1729 | 2175 | 989 | 417612 | 95693 |
| dfl | fit-disjoint | mask30-seed1729 | 356 | 165 | 5087 | 5087 |
| dfl | fitting-overlap | mask30-seed1729 | 346 | 168 | 6507 | 6507 |
| wcsf | fit-disjoint | mask30-seed1729 | 178 | 69 | 9437 | 9420 |

Since the rule only changes labels to D, the increase in predicted-D on known-reference rows equals relabelled known frames; this table is derived from counts without another run. Much natural SkillCorner relabelling lies outside known-reference support, and the other natural providers have no long gaps. The external harm gate therefore offers limited direct evidence about long challenge stoppages.

The read-only audit verified all sixty receipts/provisionals/claims, private control hashes, source/input/freeze identities and preservation of854 prior files with zero additional inference or scoring calls. The result is external-verification.json.

## Stage4b source and reference qualification

All three Metrica samples plus README/event definitions were pinned at e706dd506b360d69d9d123d5b8026e7294b13996; all11 downloaded assets matched recorded byte counts and Git blob identities. The public repository has no formal dataset licence in its README; it requests responsible use and source acknowledgement. Source: Metrica Sports Sample Data, https://github.com/metrica-sports/sample-data . Raw files remain private and will not be committed.

The event-derived reference and geometry mapping were committed before any sample prediction/score. Source clocks all agree at25Hz; index=source frame-1, without a fitted shift. Game3 varying player slots are resolved through XML channel metadata. Sourceformat tests qualified145006,141156 and143761 frames respectively, with141398,139015 and141346 known-reference rows. Referencing convention details and uncertainty are in the separately committed Metrica design document.

One qualification attempt failed on a missing end timestamp on a SET PIECE. The initial diagnosis incorrectly called it a pretracking start; bounded inspection corrected that diagnosis. The valid restart start is preserved and the irrelevant absent end is normalized to an instantaneous restart, with a missing-end counter. Failing-first tests, the original failed log/receipt, corrected diagnostic and successful qualification are all retained. This happened with zero predictions/scores; no rule threshold, time shift, team or event reference was selected from model performance.

The Metrica check is partly circular because tracking is manually corrected and ball absence is largely dead play. The sparse-event convention is not adjudicated possession truth; match identity/overlap with fitting sources is not independently known. These limits remain regardless of the eventual measured result.


### Final pre-score reference qualification and review

One fresh-context review of the new Metrica subproject found integrity, preservation and scope issues. The single pre-score fix pass binds qualification/source/sequence hashes, retains returned aggregates before validation, uses a strictly nondeclining mean gate, holds CARD inert, verifies source inventory/runtime after computation, keeps detailed per-case scores private, and reconstructs the entire final authorized summary. Thirty-six targeted Metrica tests pass.

A draft three-kind GOAL whitelist was too narrow for the addendum's rule that any goal starts D: Game3 includes a RECOVERY/GOAL annotation. This was discovered without any model inference or score. The final rule treats an exact GOAL subtype on any supported non-card event as a stop. All intermediate reference code, qualification versions and bounded sequence witnesses are preserved. Qualification-v3 reproduces the original qualified reference sequences exactly in all three games (zero changed labels, same SHA-256), while strengthening future-edge handling. It has141398,139015 and141346 known rows respectively. The source-count qualification and model scoring are separate; zero sample predictions/scores have run so far.

## Stage4b completed — PASS

The preceding zero-call statement describes the pre-score checkpoint. After the full suite passed690 collected tests (669 executed,21 skipped, zero failures), the prospective Metrica freeze was committed as0b9ea445cfe11874aa75f076d68a900ec3c0a94b. Exactly three control and three gap-rule scores were then completed, with no rerun or tuning.

| Sample | Control spell F1 | Gap-rule spell F1 | Delta |
|---|---:|---:|---:|
| Game1 | 0.443845 | 0.567704 | +0.123859 |
| Game2 | 0.441356 | 0.542012 | +0.100656 |
| Game3 | 0.454936 | 0.525599 | +0.070663 |
| Equal-game mean | 0.446712 | 0.545105 | +0.098393 |

The strict nondecline gate passes. Long-gap/stoppage counts were91/85,95/89,99/97; candidate D masks covered54710,56194,45380 frames, with zero restart-extension frames. These are sample-only observations. Tracking is manually corrected and ball absence is mostly dead play, making this check partly circular; sparse-event possession labels are approximate. This does not measure the expected challenge-match gain.

A read-only audit verified the complete source/input/freeze identities, six claims, retained provisionals, private prediction hashes and reconstructed result summary, with zero additional inference or scoring. The authorized aggregate-only challenge check may now proceed under its separate prospective freeze. No release or public-window check has been authorized.
