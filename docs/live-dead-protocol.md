# Live/dead sequence experiment: fixed protocol

Approved design: `docs/superpowers/specs/2026-11-14-live-dead-sequence-design.md` (sha256 `89981385e2001eca20f320b1788e72a1b3e086928c381e8a1500b31af8033234`).
Approved plan: `docs/superpowers/plans/2026-11-14-live-dead-sequence.md` (sha256 `9373996ad07f435a10f1f23a0cc6d092a91b8c5b1fa371396659b412b58383b0`).
Design approved by the user on 2026-11-14; native (inline) execution chosen.

## Budget clock (Asia/Singapore)

- Start (first implementation action): 2026-11-14T15:03:04+08:00
- Deadline (24 elapsed hours): 2026-11-15T15:03:04+08:00

Every science command checks the deadline on entry and before each case. Expiry is UNRESOLVED, never a result.

## Source

Branch `experiment/live-dead-sequence` from Experiment E commit `83b203e76bb8c5cf754e7fa3593980f4c9c1f85b`. Only new files
(`live_dead_*`, `tests/test_live_dead_*`, this document, `docs/superpowers/**`, `reports/live-dead/**`) may differ from it.
The frozen release support model is Experiment E's committed control refit
(`reports/player-stillness/2026-11-12-a/models/control.json`), which must hash to the release model digest.

## Budget

Science (cumulative, claim-on-entry, never refunded): fits 2 (instant, then temporal); stream predictions 123; score
bundles 123; decoder passes 246; feature/tree passes 213 (41 bundles x 5 + 8 training preparations).
Parity (implementation verification, no science scores) capped at 36 identities: exporter/{instant,temporal} 2,
training-alignment 4, release 15 (includes historical reconciliation), disabled-head 15.

## Features, models, integration

As the approved design: ten player-only values per 25 Hz row; offsets -50..+50 step 5 (210 columns, chronological);
linear (type 7) quantiles; barriers at period changes, recording edges and every invalid-geometry row; eligibility
requires centre spatial and motion support and at least five motion-supported positions strictly before and after.
Forest recipe fixed exactly as the design. Integration on eligible, ball-observed, geometry-valid active rows:
`((1-q)r, (1-q)(1-r), q)`, q clipped to [1e-6, 1-1e-6], r = h/(h+a) or .5.

## Stress mechanics (stage 2 only)

1. Jitter: existing visible-ball .25 m Gaussian noise; seed sha256(prefix + 'jitter:' + case)[:8]. Liveness inputs must be byte-identical to natural.
2. Player degradation: 125-row blocks from each period's first row; per (period, block) rank distinct non-null
   (team, id) by sha256('live-dead-sequence-v1:1729:{case}:{period}:{block}:{team}:{id}') ascending and remove the
   first n // 4 from every row of the block. Then noise: random.Random(sha256(prefix + 'degrade-noise:' + case)[:8]),
   rows ascending, home then away, stored order, gauss(0, .25) x then y; non-finite players draw nothing. Ball-to-
   nearest-player distances recomputed; ball, periods, flags and references unchanged. IDs are as associated by the
   adapter before degradation. All three streams are recomputed from the transformed frames.

## Gates (temporal against release unless stated; slack 1e-6, round-off 1e-12)

Natural: primary spell F1 gain >= .010; every provider delta >= -1e-6; every primary case >= -.020-1e-6; temporal
minus instant > 1e-6; WCSF D recall rise >= .030; per primary DFL/WCSF case D precision and recall loss <= .010+1e-6;
per primary case known-live false-D rise <= .005+1e-6; H and A represented where supported; short spells (<= 25 rows,
IoU .5): >= 20 spells recall loss <= .020+1e-6, 1-19 no lost matched count, 0 non-applicable. Interior team accuracy
reported, not required.
Stress (each regime): primary loss <= .005+1e-6, case loss <= .020+1e-6, and the natural D, false-D, owner and short-spell limits.
Support floors: training match >= 1,000 selected rows, >= 125 D, >= 125 live; primary case >= 1,000 integration-eligible
rows and >= 10% of the denominator, >= 125 known-live, DFL/WCSF >= 125 known-D. Shortfall: UNRESOLVED, stop.

Verdicts: PASS (supports a separate release investigation only), NO_ADVANCEMENT, UNRESOLVED/INVALID.
No provided match, public-window evaluation, upload, push, merge, PR, release installation or submission change.
