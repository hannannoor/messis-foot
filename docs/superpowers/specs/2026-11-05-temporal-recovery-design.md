# Independent-provider validation and temporal possession recovery

5 November 2026. Proposed design for the user-approved next goals. The user authorised the work and an independent fresh-perspective agent. Model/gate choices below are builder proposals, not previously agreed numeric requirements. No new model has been fitted or independent-provider model score opened at this point.

## Intent and scope

Reduce unsupported possession output using evidence that survives external testing. The ambition is near-complete coverage; assigning every frame is not sufficient evidence of quality. Preserve the existing frozen tactical experiment, its artifact and its reports. New code is isolated from the published source and existing Desktop output. No challenge-driven selection, manual game labels, video/GT checking or asset uploads.

Deliver: immutable blind audit and its disposition; a licensed independent-provider benchmark; gap/observability diagnostics; an externally selected motion/temporal candidate compared with simpler alternatives; a frozen held-out evaluation; conditional local inference only if the candidate passes; tests, explanation and limitations. Record rejected candidates honestly rather than treating lower X as success.

## Independent audit and concrete code finding

`strategy-blind-audit-v1.md` preserves the initial independent response from a no-history agent. It did not inspect our code, strategy, results or local data. Its central disproof test is a short opposing spell hidden inside a gap with same-team endpoints. Two-sided filling can erase that event while improving frame accuracy.

The existing `load_atd` returns immediately on missing ball, before parsing player coordinates. The new path must retain available player positions during ball absence. The original loader and six freeze-protected sources remain unchanged. ATD does not expose a detection/extrapolation flag in this contract; finite coordinates mean available positions, not independently verified fresh detections.

## Approaches

1. **Two-sided interval rules:** transparent, cheap baseline using credible observations before/after a gap. They cannot identify hidden intermediate turnovers from endpoints alone. Implement for comparison, not as assumed truth.
2. **Player-motion model plus temporal decoding — recommended:** use available players, intermittent ball evidence and both-sided history, then decode team states offline. CPU-friendly and externally testable; it can fail if movement contains insufficient information or provider effects dominate.
3. **Recover additional observations from video:** potentially stronger evidence, but a separate detector/coordinate/time-validation project. Defer until the tracking-based experiment establishes its limits; it must not become challenge-video training/tuning.

The prior conversation proposed temporal possession inference and independent-provider checking, which the user asked us to work on. This design makes the tracking-first route concrete and keeps the simple method as a falsifiable baseline.

## Independent data and label contract

Use SkillCorner Open Data at revision `4340d274572876239c154c90bc507a9b3250a656`. The pinned repository LICENSE is MIT; preserve attribution to SkillCorner/PySport and licence text. No dataset-specific exception was found in the pinned README/LICENSE. Verify LFS object SHA256/size for raw tracking and git blob identities for metadata/event files. No videos or body-pose files are needed.

The actual tree contains 20 matches. `skillcorner-source-protocol.json` records all file identities and the pre-score split: sorted first eight development, next two calibration, next two validation, last eight final test. The old frozen model's initial cross-provider check uses development only; final test scores remain unopened until the new candidate is frozen. Match/team independence is limited by repeated teams and one competition.

Tracking is native 10 Hz with original frame IDs, timestamp and period; pre-match rows can have null period/time and no objects. Ball and player coordinates have explicit `is_detected` flags. Metadata supplies static team membership and pitch size. Primary benchmark features use detected positions only; a separately labelled available/extrapolated-position ablation tests reliance on provider inference.

Primary H/A reference comes from `team_in_possession_id` in phases of play, joined by original frame ID. The official tutorial uses left-closed/right-open intervals `[frame_start, frame_end)`; sampled duration/time fields agree with that convention. Confirm this automatically across acquired files. Overlap with conflicting teams, invalid IDs, missing annotation and absent phases stay unknown. **Absence of a phase is not converted to D.** The tracking `possession` field is a separate diagnostic reference, not an independent gold standard. These are provider-derived labels, not a human video validation study.

Exclude possession, phase definitions/boundaries, event outcomes, player-in-possession fields, tactical/pressure/EPV features, scores and identities from prediction inputs. Do not filter inference to reference-in-play intervals. Reference masks are used only for supervised training/scoring and reporting conditional scope. Period identity and static team membership are structural inputs. Label permutation must leave features unchanged.

Resample features onto canonical 25 Hz for the existing frozen runtime and competition scorer. Interpolate coordinates only between consecutive detected native observations in the same period (at most one native sample interval); never across a missing detection, period edge or discontinuity. Record interpolated availability separately from native detection. Categorical references use the documented half-open native intervals. Preserve the native-to-canonical mapping and do not claim resampling creates observations. Test time/index consistency and sensitivity to one native-frame boundary uncertainty. The previous model remains unchanged.

This reference supports independent-provider **known-in-play H/A** evaluation. It does not independently validate D, and must not be marketed as a full live/dead benchmark.

Unknown reference intervals remain explicit X in the complete canonical timeline. The unchanged official `valid_runs` and `possession_spells` routines score each contiguous known-reference run separately; never concatenate across a hole or imply that two surrounding H intervals form one established spell. Add an explicit H/X/H regression fixture. Period separators remain evaluation-only.

Source QA must reconcile phase durations/times with native tracking clocks and report requested, out-of-range, conflicted and retained annotation support by match. Contradictory intervals remain unknown; do not fit a label-dependent clock shift. If less than95% of requested in-range phase support survives reconciliation on any final match, mark the reference-quality gate failed and withhold promotion. Cache generations bind match, position regime, raw-input identities and hashes of both arrays; metadata is published last and verified before reuse.

## Proposed implementation

Add new modules rather than modifying the frozen six-source baseline. A motion record extends the existing frame evidence with both teams' available position tuples, observation counts, native/interpolated status and elapsed time. The ATD adapter parses players even when ball is absent and applies the existing homography-quality mask to all geometry. Raw challenge arrays remain local; only automatic aggregate reports are inspected here.

Features describe team centroid/shape changes, dispersion, speed/convergence, counts/missingness, last/next credible control and distance/time to each anchor. Coordinate reflection and home/away swap augmentation prevent easy direction/team-identity shortcuts. Do not use extrapolation flags as hidden possession targets; report detected-only and available-position regimes separately. No challenge-only tags are needed for the first candidate.

Fit one compact binary boosted-tree H/A model on development only: proposed 40 depth-two estimators, minimum leaf 150. Fit an optional scalar temperature on calibration only; it does not make confidence a guaranteed correctness probability. Export a portable standard-library ensemble. Symmetrise scores under home/away swap. Use a two-state forward/backward temporal decoder with training-derived switch priors, period/quality resets and fixed credible anchors. It may infer internal switches; do not force same-team endpoints to imply an uninterrupted same-team spell.

Compare: legacy geometry, the existing frozen tactical model, bounded last-owner retention, two-sided interval rules, motion without decoding and motion with decoding. Primary recovery fills eligible baseline X; it does not invent D or silently overwrite already-decided labels. D/ungraded/invalid-geometry boundaries stop bridging. Unbounded gaps or insufficient player support retain X. Proposed minimum player support is three available players per side; evaluate its coverage loss externally.

Predeclared policy grid: support gates .90/.95/.975; maximum full-gap duration 2/5/10 seconds; switch-prior multipliers .5/1/2 (27 policies). Natural missing detections are primary. Supplementary label-independent contiguous ball masking uses 30% masking with .2/.6/2/5/10-second durations and a fixed seed. Team loss, identity swaps, false ball detections and timing shifts are mechanism stress tests, not opportunities to tune from the challenge. No expansion of the grid after final-test scores.

## Quality gates and reporting

Select using validation only. Proposed eligibility on natural validation: at least five percentage points more known-reference coverage than the selective baseline; at least 90% newly assigned H and A agreement separately, each supported by at least 100 frames in ten distinct gaps; no per-match official team-spell decline; and no decrease in short opposing-spell recall inside same-endpoint gaps where reference support exists. Choose the strongest eligible team-spell score, then coverage. Report the simpler two-sided baseline; reject the motion mechanism claim if its advantage disappears against that baseline or without extrapolated/provider-derived inputs.

Define a short hidden opposing spell as a reference H/A spell lasting .2–2 seconds, wholly inside a natural or declared synthetic missing-ball interval, with credible same-team endpoints belonging to the opposite team. A hit requires an opposite-team predicted spell matched at IoU>=.5. Report natural and masked support separately. The mechanism gate requires at least20 such spells across at least2 validation matches; otherwise its evidence is insufficient, not a pass. Obtain additional support through the predeclared masking experiment only; do not search masks using labels. Any claim about natural hidden turnovers additionally needs natural support and cannot be inherited from masking.

The informed follow-up found that zero recall tying zero could pass nondecrease. Tighten the mechanism claim before fitting: require positive paired incremental hidden-opponent recovery over the two-sided rule on the same recoverable population and at matched coverage; additional false opposing spells may not exceed additional correctly recovered opposing spells. Repeat support and incremental-recovery checks on the frozen final evaluation. If natural support is insufficient, report the mechanism as unestablished for natural gaps, irrespective of masked results. This does not turn interpolation or adjacent frames into independent examples; show native counts and gap/match weighting.

Reference holes must never become inference-time barriers. Only structural period/out-of-recording boundaries, observed D baseline decisions and independently available geometry quality may stop decoding. Removing or permuting the entire phase reference must leave predictions identical. Also report newly assigned H/A outside known-reference support, whose correctness this benchmark cannot establish.

Before final testing, freeze features, adapter/scoring sources, model, calibration, policy, split and checksums. Final eight-match acceptance additionally requires nonnegative mean team-spell change, no match decline exceeding .02, a paired match-bootstrap lower bound above -.02, per-class newly assigned agreement at least90%, and the declared coverage gain. These are proposed operating tolerances, not promised results. Show every match, short-spell recall, boundary error, false switches, raw X and scorer-expanded changes. Abstentions count against coverage/recall; official X filling is reported separately. Calibration/validation cannot stand in for final testing.

The previously used DFL matches are no longer fresh holdouts for this phase. Use them only as an explicitly seen-data regression/stress check against new H/A assignments during known D and contiguous masking. They cannot repair SkillCorner's missing independent D reference. Require no loss of complete-target spellF1/macroF1 in the declared regression cases; report all failures. A successful H/A recovery is not proof of transferable stoppage detection.

Only a passed frozen candidate is run locally in a new **experimental** folder. The known-in-play benchmark does not authorise a claim about added H/A labels during unknown local stoppages. Preserve the prior submission, write the new hypothesis separately with evidence/uncertainty flags, and explicitly mark it unvalidated for local live/dead correctness. Do not promote the default or claim a generally validated final submission. Independent full-state evidence would be needed for that stronger claim; the seen DFL regression is not a substitute.

Use original challenge indices, no disputed fixed-D interval, no video or GT, no retuning after local coverage. Inspect automatic aggregates: residual reasons, duration buckets, observation counts, changes and unknown intervals. Record local accuracy as unmeasured. If motion is ineligible or cannot beat the two-sided rule, report that mechanism as rejected. A simpler rule may proceed only if it independently meets every applicable quality/support gate; choosing it must follow measured superiority, not ease of implementation. If no method is eligible, freeze the predeclared best validation challenger as **rejected before test**, evaluate it once for diagnosis only, preserve that rejection even if its final score happens to look good, and perform no new local inference. Do not relax gates or retune after final tests merely to reach zero X.

## Verification and completion

TDD for adapters, hidden-turnover fixtures, missing-opponent/ball guards, period resets, malformed clocks, feature/reference independence, home/away symmetry, portable ensemble parity and output ownership/index safety. Test native10/canonical25 mapping and unknown reference holes. Run full synthetic suite, standalone parity/Python3.9 parsing and isolated standard-library execution. Obtain a builder check before implementation and fresh whole-change review before final freeze/test/delivery. Preserve the original blind memo and keep later informed comments separate.

Completion requires the independent-provider check, diagnostics, actual candidate comparison/selection, frozen final evaluation, conditional local decision and documented evidence/disposition. A plan alone is not completion. A rejected candidate is reported as rejected; it is not a claimed accuracy or coverage improvement.
