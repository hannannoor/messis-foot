# Competition-only briefing — stage1

Prepared7 November2026 for an independent two-stage audit. This packet contains competition details and session constraints only. Do not inspect this project's implementation, reports, other-agent outputs, earlier chat, GitHub branch or participant solutions in stage1. Do not infer the participant's chosen strategy.

Official source: Metrica Sports **More Than a Hack2027**, pinned revision `f8f2629ff1e0985f81d7e59d8413678514ee1530` (resolved from current public HEAD for this briefing).

Read these primary text/code sources through the GitHub connector or web; no asset download is needed:

- [README](https://github.com/metrica-sports/more-than-a-hack-2027/blob/f8f2629ff1e0985f81d7e59d8413678514ee1530/README.md)
- [DATA contract](https://github.com/metrica-sports/more-than-a-hack-2027/blob/f8f2629ff1e0985f81d7e59d8413678514ee1530/DATA.md)
- [RULES](https://github.com/metrica-sports/more-than-a-hack-2027/blob/f8f2629ff1e0985f81d7e59d8413678514ee1530/RULES.md)
- [Scorer source](https://github.com/metrica-sports/more-than-a-hack-2027/blob/f8f2629ff1e0985f81d7e59d8413678514ee1530/evaluation/possession_metrics.py)
- [Evaluation entry point](https://github.com/metrica-sports/more-than-a-hack-2027/blob/f8f2629ff1e0985f81d7e59d8413678514ee1530/evaluation/run_evaluation.py)
- [Submission validator](https://github.com/metrica-sports/more-than-a-hack-2027/blob/f8f2629ff1e0985f81d7e59d8413678514ee1530/evaluation/validate_submission.py)

The task is per-frame possession/state inference from supplied football inputs, with H/A/D/X labels. Derive exact definitions, supplied modalities, output/time contract, ranking and handling of uncertainty from those sources rather than from our interpretation. Source inspection may list asset paths; never open any challenge GT, video, tracking, tags, homography, saved predictions or reconstruction-capable derivatives. Text documentation and scoring code are sufficient for this stage.

## Participant-supplied controlling clarification

The participant supplied an organiser clarification on5 November2026, recorded locally. No independent public URL for that message is available in this packet. Treat its provenance separately from the pinned public rules. Its recorded requirements are:

- Not allowed: checking algorithm output against provided video; hand labels/human-produced or other manually created data on the provided game; uploading provided data to AI services; training/fitting/calibrating on ground-truth possession data or provided video.
- Allowed: automatic checks using provided data; inspecting data/video to understand possession; inference inputs from video, automatic tracking, smart tagging and generated data when the algorithm was not trained on provided video/GT; intermediate-step files; appropriately licensed external datasets.
- Training/retraining/parameter tuning must use external data. Inference is distinct from fitting.

Do not resolve a conflict by silently dropping this clarification, and do not treat an interpretation of it as a verified organiser statement. State uncertainties precisely.

## Stage1 output

Independently describe the actual task and scoring objective, what the inputs can/cannot establish, the most informative first checks/experiments, and the major ways an entrant might optimize the wrong thing or waste effort. Make your own priorities without seeing our work. Separate public-source facts, clarification constraints and your inferences. This is a read-only conceptual audit, not permission to inspect prohibited assets or tune any method.

Write only `next-phase-notes/neutral-audit-stage1.md`, then stop and notify the coordinator. Do not read stage2 material until it is separately delivered. Do not spawn subagents.
