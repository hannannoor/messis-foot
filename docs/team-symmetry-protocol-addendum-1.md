# Experiment C — protocol addendum 1 (clarifications from the user, 12 November 2026)

Recorded **after** the freeze commit `e18b7b1` (freeze receipt of run `2026-11-12-a`, protocol digest
`40645d91f2e8b813656f9f220e2e1bc67d8242123d9ce503a5403f11ead2495f`) and before any scoring. The user asked for the first point to be
written into the protocol before the freeze; it reached the worker after the freeze, so it is kept here as a separate,
dated file instead of editing the frozen protocol (an edit would change the protocol digest and invalidate the freeze). Both
points describe what the frozen code already does; no code, parameter, gate or budget changes.

1. **Mask seals.** The comparison with Experiment A's committed `preflight.json` covers only the live-gap and stoppage masks.
   The seal (`recent_geometry_regimes.seal_digest`) is computed over exactly those two arrays (`live`, and `stoppage` for the
   five stoppage cases) and nothing else. The visible-ball noise regime has no mask and no seal; its draws use the prefix
   `team-symmetry-jitter-v1:1729:`, so they legitimately differ from Experiment A's, and that difference is never a stop
   condition. A difference in a live-gap or stoppage seal remains a stop (`stopped_mask_mismatch`).
2. **Tree-pass budget.** The cap of 200 feature/tree passes is used exactly if every stage runs (15 + 15·3 + 35·4), with no slack
   and no request to raise it. If a defect appears in stage 2, the study stops and reports: no rerun of any stage-2 case-regime
   and no request for a larger cap.

Everything else in `docs/team-symmetry-protocol.md` stands unchanged.
