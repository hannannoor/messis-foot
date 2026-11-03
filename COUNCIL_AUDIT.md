# Council audit: baseline repair before wider fusion

Audit performed on 2 November 2026 using five independent advisor roles and five anonymous peer reviews. This was a reasoning audit, not empirical model evaluation or an ensemble of five trained predictors.

## Decision

Repair the tactical baseline and expose rejection causes before widening camera fusion or building a larger temporal model. Keep the two-camera approach as a source of additional evidence, with stronger temporal validity checks planned separately.

## Agreement

- Automatic set-piece phases are context, not exact possession or dead-state labels.
- Both cameras need compatible restart/dead policy.
- Matching clock text cannot authenticate replay content.
- Missing-ball recovery and possession boundaries matter more than reducing X as a standalone objective.
- A controlled comparison should isolate each change and preserve provenance.
- The 43899 restart-blocked frames are not all recoverable possession.

## Peer-review corrections

- The current direct-control label is an unvalidated proximity heuristic; a player waiting for a restart can be close to the ball.
- Short same-team bridging already exists. Measure why it rejects gaps before adding another version or loosening its limits.
- The timing uncertainty is comparable to the control-confirmation duration. Future broadcast attribution must account for all plausible offsets near turnovers.
- The scorer forward-fills X and backfills the head of a half. A changed anchor can affect more frames than the raw assignment count suggests, or have no temporal effect.
- Count usable missing-ball opportunities before interpreting zero recoveries.

## Implementation sequence

1. Repair restart precedence with regression tests, retained bridge vetoes and explicit dead-state precedence.
2. Add staged baseline comparisons, detailed rejection counts, missing-ball opportunities and scorer-expanded diagnostics.
3. Develop multi-frame configuration/motion correspondence for broadcast. Uncertain or replay-like evidence should have zero broadcast vote; temporal consistency is still a heuristic until independently evaluated.
4. Develop possession-state inference using sustained anchors and explicit transition uncertainty. Opposing anchors do not reveal a turnover's exact location.
5. Develop general dead-play evidence using multiple signals. Ball absence or stationary proximity alone is insufficient.

Steps 1 and 2 are implemented in version `2026.11.02-restart-audit`, alongside the separately published pre-kickoff D context. Steps 3–5 remain future evaluated work.

## Acceptance evidence

Synthetic invariants establish implementation behavior. Use permitted other-match labels to evaluate spellF1, macroF1, transition timing, false switches, false-dead decisions, missing-ball cases and replay rejection. Keep validation examples separate from tuning choices. Public competition labels remain pipeline sanity checks only.

The first local experiment reuses the cached alignment and tracking; no new OCR scan is needed. It compares the legacy tactical baseline, restart-repaired tactical inference, published-context tactical inference and final fusion. Additional coverage is not described as improved correctness.
