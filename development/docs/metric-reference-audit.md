# Official metric and tactical-state audit

Read-only audit, 5 November 2026. No challenge assets, predictions, or `evaluation/gt` files were opened. No algorithm was changed and no external performance improvement is claimed here.

## Reference and runtime

Reference root: `C:/Users/leonj/Desktop/more than a hack data/more-than-a-hack-2027-main/more-than-a-hack-2027-main`.

Read `evaluation/possession_metrics.py`, `EVALUATION.md`, `games.py`, and `LICENSE`. Metric SHA256: `341bad48904b489d6e875397b27687f5d6a4d22a397f3dc8af3a00d48f16874d`.

The metric imports only numpy and pandas, and has no asset reads at import. Runtime check: `C:/Python314/python.exe` successfully imported numpy 2.5.1 and pandas 3.0.5 from the user's Python314 site-packages. These are sufficient dependencies; sklearn is unnecessary. Import this exact file with `importlib.util.spec_from_file_location`, rather than invoking the challenge runner or relying on a potentially different module on `sys.path`.

Repository source and documentation are MIT licensed, copyright 2026–2027 Metrica Sports. Preserve the copyright and permission notice if copying/vendoring the metric. The license explicitly excludes the match assets.

## Relevant exact function signatures

```python
read_label_csv(path)
validate_submission(frame, n_expected)
label_codes(frame_or_labels)
evaluate(gt_codes, pred_codes, taus=TAUS, bootstrap_n=BOOTSTRAP_N, typed="to")
valid_runs(gt_codes)
fill_abstentions(pred_codes, runs)
segments(codes, runs)
transitions(codes, runs)
match_transitions(gt_trans, pred_trans, tol, typed="to")
transition_scores(gt_trans, pred_trans, tol, typed="to")
fragmentation(gt_codes, pred_codes, runs)
possession_spells(codes, runs)
spell_overlaps(gt_spells, pred_spells)
matched_gt_flags(overlaps, n_gt, threshold)
match_spells(overlaps, n_gt, n_pred, threshold)
spell_scores(gt_codes, pred_codes, runs, ious=SPELL_IOUS)
possession_stats(codes, runs)
bootstrap_macro_f1(gt_codes, pred_codes, runs, n_draws,
                   seed=BOOTSTRAP_SEED, percentiles=BOOTSTRAP_PERCENTILES)
bootstrap_spell_f1(gt_codes, pred_codes, runs, n_draws,
                   seed=BOOTSTRAP_SEED, percentiles=BOOTSTRAP_PERCENTILES)
```

Constants: H/A/D/X = 0/1/2/3; TAUS = (12,25); SPELL_IOUS = (0.3,0.4,0.5,0.6,0.7); headline IoU = 0.5; FPS = 25; bootstrap defaults to 0 draws, seed 0, percentiles (5,95). `evaluate` accepts arrays of codes, not label strings, paths, periods, masks, or explicit runs. Convert labels through `label_codes` first. `evaluate` checks equal lengths only; validate input codes/shape/finite values/nonempty scored support in the external harness. CSV validation requires ordered integer frames 0..N-1 and one valid nonblank H/A/D/X label per row; call it explicitly because `evaluate` does not.

## What the metrics actually do

* `spell_f1_mean` ranks the board. Maximal H/A runs are possession objects; D is excluded. Half-open interval IoU is computed only for overlapping same-team pairs. All pairs are sorted by decreasing IoU, with GT/prediction indices breaking ties. Greedy matching consumes both spells once. At each inclusive IoU threshold, TP = matches, FP = predicted count - TP, FN = GT count - TP; F1 is the usual 2TP/(2TP+FP+FN), or zero with no match. The headline is the unweighted mean over the five thresholds. This is greedy IoU matching, not a maximum-cardinality/Hungarian matcher and not average precision.
* GT X defines the exclusion mask. `valid_runs` returns maximal contiguous GT-non-X spans. The scored confusion is exactly rows H/A/D and columns H/A/D/X. GT-X frames manufacture neither FP nor FN. Prediction X on a graded frame is a false negative of the true class. Per-class precision/recall/F1 have zero conventions for absent classes; macroF1 averages all three H/A/D F1s unweighted, including an absent class's zero.
* Frame metrics see raw prediction X. All temporal metrics see a COPY of predictions forward-filled within each GT valid run and back-filled at its leading edge from the first non-X label. An entirely X predicted run remains X, contrary to the documentation's simplified claim that no abstentions remain. No fill crosses a GT-X hole. Filling X between identical team anchors can improve macroF1 while leaving spellF1 exactly unchanged; filling at a turnover can shift an entire effective boundary and damage spellF1.
* `alive_dead_f1` treats ALIVE as positive: H/A-to-H/A are TP even when the team is wrong; GT-D-to-H/A are FP; GT-H/A-to-D/X are FN. GT-D-to-X is not charged by that particular binary metric, but is charged by D recall and macroF1. Always inspect D precision/recall/F1 too.
* `team_acc_gt_alive` charges D/X on GT-alive frames as wrong. `team_acc_both_alive` conditions on both agreeing alive, so it can look strong despite poor coverage. `fragmentation` counts all constant H/A/D/X segments after fill, divided by GT segment count; `n_pred_spells`, spell-count error, and durations separately expose team fragmentation and mergers.
* Transitions are the first frame of the new state. Matching is inclusive within +/- tolerance, destination-typed by default (`typed="to"`); origin is ignored. `typed="pair"` requires both endpoints; `typed="none"` ignores labels. Earliest-to-earliest matching within each type is maximum cardinality, but not minimum total latency. Positive latency means prediction late. The returned `pairs`, `missed`, `spurious`, and `n_ambiguous` support error tables. Latency can change among equally good matchings.
* The source's macro_f1 docstring still says the scoreboard ranks on macroF1; this is stale relative to the module introduction and EVALUATION.md. Likewise constant H/A spellF1 is not mathematically guaranteed to be zero on arbitrary external clips: a constant H on an all-H clip is perfect. Published constants and noise bands describe the reference match, not general identities.

## External periods, timebases, and masks

Do not import game constants as external-match metadata. `games.py` is the challenge-specific alignment contract: submission row index is tactical VIDEO frame, while legacy tracking IdFrame offsets differ per half. Its half spans are inclusive; metric runs are half-open. The current `load_atd` instead explicitly accepts ordered 1-based export rows and maps them to row-1. An external adapter must declare which convention its own source uses and verify it from that source; neither convention can be inferred from a shared filename.

`evaluate` has no `periods=` argument. Adjacent halves with no GT X between them become one run: fills can cross halftime and identical labels can merge spells. More subtly, `match_transitions` has no run identity at all; it assumes separated runs are farther apart than tolerance. A one-frame GT-X boundary does split spells and filling, but still permits cross-period transition matching when events lie within 25 frames.

Safe choices:

1. Evaluate each period independently, retain each report, and explicitly aggregate confusion counts and per-IoU match counts if a pooled report is required. A mean of per-period F1s is not the same pooled metric.
2. For an unchanged `evaluate` call producing a pooled match report, build a separate evaluation-only array by concatenating periods with at least `max(taus)+1` X frames in BOTH GT and prediction. Preserve an index-to-original-frame manifest and exclude pads from coverage/duration summaries. The pad prevents cross-boundary matching; `n_frames` includes pads while `n_graded` does not. Never alter production frame indices or the exported submission to insert these pads. Real short GT annotation gaps within a period retain the official behavior; boundary-guarded diagnostics can be reported separately if needed.

Prefer a declared canonical 25 Hz time grid for comparable transition tolerances and duration output, with half-open timestamp annotation intervals and an explicit conversion rule. On native different-FPS data, IoU is unitless but (12,25) no longer means 0.48/1 second, and the official `FPS=25` duration report becomes wrong. Passing scaled `taus` alone does not repair durations. Do not silently monkey-patch the official module or call native-rate scores directly comparable to 25 Hz scores.

`audit.scorer_expanded_labels` uses Frame.period blocks rather than GT-valid runs. It mirrors official fill only when the blocks match exactly. On sparsely annotated external games, GT-X holes can differ, so do not use this audit's expansion as the scoring oracle. Use the official `fill_abstentions(pred, valid_runs(gt))`. Keep production coverage over declared active periods separate from correctness over independently graded frames. Do not change a physical match period to zero merely because reference annotations are missing; otherwise the algorithm would see evaluation availability.

## Safe external evaluation design

* Input manifest: external dataset license/provenance, match ID and split, immutable input checksums, team-ID mapping, original frame/timestamp/period conventions, pitch dimensions, FPS, annotation ontology, and which frames have independently available H/A/D truth. Never load challenge match assets, labels, or predictions into this harness. Import only the reference metric file by direct path.
* Keep independent external truth separate from algorithm inputs. If labels are derived from event possession/team fields, do not expose those same fields as `tag_team`; that would measure leakage. Incomplete pass/shot/touch events do not justify dense H/A/D annotations across unobserved stoppages. Mark genuine unannotated truth X and disclose scored support and class coverage. A dataset with no D truth cannot validate the dead-ball behavior; absent-D macroF1 also has an upper bound of 2/3 even with perfect H/A.
* Freeze match-level development and held-out splits before selecting an improvement. Tune thresholds on development matches, run a locked baseline and one selected candidate on held-out MATCHES, report every match plus unweighted match average and optional pooled counts. One half of a match held out from its other half is weak evidence of generalization. With few matches, label results as preliminary.
* Official call on external arrays: `pm.evaluate(pm.label_codes(gt_labels), pm.label_codes(pred_labels), taus=(12,25), bootstrap_n=1000, typed="to")`. The GT labels already contain the independent annotation mask and any evaluation-only period separators. Preserve source SHA256, configuration, split manifest and versions alongside outputs. Use finite-safe JSON handling for all values and retain per-IoU counts.
* Report primary mean spellF1, per-IoU spell F1, macroF1, D PRF, alive F1, both team accuracies, raw X fraction on active frames AND graded frames, newly resolved-frame correctness, raw/expanded changes, spell count/fragmentation, and matched-boundary signed/absolute latency. Stratify by ball observed/missing, reason, flight/control, restart, original period, clip length, and long/short possessions.
* A candidate succeeds only with measured held-out improvement and an honest coverage/correctness tradeoff. Report paired per-match deltas. Official bootstraps resample GT segments/spells within a match; the spell interval holds predicted count fixed and clamps resampled FP, so it is not a full match-generalization interval or a paired baseline-vs-candidate test. Avoid treating the reference ~0.04 spell noise band as universal.

## Highest-payoff algorithm limitations to test

These are source-level observations and hypotheses, not empirical rankings.

1. **No independent alive/dead classifier.** `infer` emits D only on supplied `dead_evidence`. A stationary ball near a set-piece taker for six frames is labelled team control even though the game may still be stopped. The current restart repair correctly stops vetoing *all* sustained proximity during broad set-piece tags, but broad restart context plus proximity cannot tell pre-kick dead time from active play. This can both miss D frames and merge same-team possessions across stoppages. Evaluate an external-rule-based live/dead state with observable out-of-play/restart motion evidence and explicit provenance; missing ball or low ball speed alone is insufficient dead evidence.
2. **Flight and control share one proximity heuristic.** `_candidate` checks only nearest team distances (<2 m with >=0.75 m margin), not ball velocity, player-ball relative velocity, height, contact, or approach/departure. `max_ball_speed_m_s` affects diagnostic interpolation only, never inference. A moving ball near an opponent for >=0.24 s can backdate a false turnover. Conversely normal passes with no player inside 2 m reset owner/candidate every frame and produce large X runs. Preserve a separately named last-confirmed team plus bounded in-flight state, or gate new control with trajectory/contact evidence, rather than reusing proximity as proof of reception. Any retained label must retain inferred provenance; both turnover latency and wrong carry across turnovers must be measured.
3. **Confirmation requires strictly consecutive support and fully resets on one ambiguous frame.** Intermittent detection/margin failures repeatedly erase a nearly confirmed run. This explains a plausible source of high X even with visible ball, but increasing bridges indiscriminately would hide turnovers. A quality-aware confirmation window is a testable alternative, with hold-out precision/recall for new anchors and short-possession recall as guardrails. A six-frame confirmation backdates decisions, so this is an offline algorithm, not a claim of zero-latency causal prediction.
4. **Tags are soft gap evidence, with some questionable semantic mappings.** `load_tags` correctly flips named defending team to opposite possession team and ignores unrelated codes. But `players in the box`, `ball in final third`, `ball in the box`, and broad transition/team phase tags do not by themselves establish team control; an area/shape/team annotation can persist through turnover or stoppage. They currently extend a same-team gap up to two seconds and can veto short bridges on conflict. Validate each tag code's control semantics on independent external data; exclude non-possession tags from evidence until supported. Never treat every named team as owner, or every set-piece tag as D.
5. **The adapter is challenge-specific.** `load_atd` assumes first metadata Team is home, pitch 105.3 x 68.0, normalized coordinates, supplied challenge half blocks, and at most periods 1/2. For external data pass explicit blocks and convert to proper metre coordinates via a separate adapter; verify home/away identity from documented metadata. Do not apply `apply_published_dead` externally: its shape/period check is not a unique match identity check, so an unrelated same-shaped array could accept the reference correction. External extra time requires a deliberate period mapping or separate-period calls because `infer` rejects periods 3/4.

Best first tactical comparison depends on external annotation quality. A control/flight gate is a contained candidate when external tracking and independent possession annotations exist. An alive/dead model is likely essential for realistic full-match output, but it needs trustworthy external stoppage truth. Reject a candidate that only reduces raw X while official filled temporal labels and independent correctness fail to improve.
