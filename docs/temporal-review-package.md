# Fresh whole-change review package

Base is the verified 89-file publication copy at commit c4643e7d7680284776ad4a3789d920ba489dc408 (`../github-upload`). Current isolated source is `temporal-work`; no local git history exists. Compare file identities rather than moving any branch. The original six freeze-protected files must remain identical.

Review source additions: gap_solver/{motion,skillcorner,acquisition,temporal,temporal_selection,temporal_development,temporal_metrics,temporal_protocol,temporal_acceptance,dfl_motion}.py; acquire_skillcorner.py; prepare_skillcorner.py; run_skillcorner_baseline.py; select_temporal_recovery.py; freeze_temporal.py; evaluate_temporal_final.py; corresponding tests and pinned benchmark/skillcorner/protocol.json. Plan/spec and ledger are authoritative. Source data stays outside the publication tree.

Read `docs/superpowers/plans/2026-11-05-temporal-recovery.md`, its spec, and `.superpowers/sdd/temporal-recovery/progress.md` Ruling lines. User approved tracking-first, with no local output unless gates pass. Blind initial audit is immutable, later informed review separate. Fixed 40-tree fit completed on357964 augmented rows; two calibration matches only. Validation27-policy experiment is running; final eight test scores remain unopened. Review before freeze/final evaluation. Conditional local CLI/export is deliberately not implemented until eligibility is established; if validation rejects, no new local inference or model promotion is permitted. Documentation results will be filled from frozen outputs.

Review Focus (verbatim from plan):

1. False fresh observations from extrapolation or interpolation; never bridge a missing native detection.
2. Label-dependent features, filters or event outcomes; permuting reference fields must leave features identical.
3. Same-team endpoints hiding an opposing spell; do not force the interior to one owner.
4. Unknown periods/annotation holes silently merging spells or becoming D.
5. Portable tree/logit/calibration/decoder parity and local output alias protection.

Also assess gates, matched-coverage endpoint comparison, per-class/per-gap support, held-out isolation, final acceptance bootstrap, repeatability/checkpoints and any execution failure you can establish. Existing231-test full suite passed5 skips; new freeze/acceptance checks subsequently passed. Training/export test ran independently in Python3.12; standard-library probe is pending. Do not count skipped training tests as executed. Do not read challenge video, tracking, per-frame predictions or GT. You may inspect source and aggregate external reports; do not score final test. Read-only, no subagents; return exact lines, effect, severity, proposed fixes and an explicit 'Declined to judge' list.
