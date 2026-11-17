# Touch evidence design — 10 November 2026

Execution authorized in chat: “u are teh worker so yes please begin”. The supplied handoff is the design authority; historical handover instructions are context, superseded by this request.

Base: 431d1ec556ef77a46d76e8227eba9690c07d08e5. Official HEAD checked unchanged: f8f2629ff1e0985f81d7e59d8413678514ee1530.

## 2. The idea being implemented

"Predict what the ball should do; where it does something else, someone touched it."

A free ball moves predictably: roughly straight, slowing down. A sudden change in its velocity near a player is a touch. The team of the player at the moment of contact is much stronger ownership evidence than "who is nearest right now", which is what the tree uses on every frame.

This produces two things the current pipeline lacks:

1. **Last-toucher evidence.** From a touch by team T until the next touch, add a bonus to T's emission. This also applies on missing-ball frames, which today carry no evidence at all.
2. **Touch-timed boundaries.** At the frame of an attributed touch, switching to the toucher's team is cheaper than 32. Elsewhere the cost is unchanged.

Item 1 is the main lever (it targets the 97%). Item 2 is secondary (it targets boundary timing).

It is deliberately not an ensemble and not a second model. Where no touch is detected, the candidate must behave exactly like the frozen control.

### What is out of scope

- Pose or skeleton estimation, unless Stage 0 says players are large enough (expected: they are not).
- Any large learned world model, video transformer or new neural network.
- Refitting the tree, changing its features, or changing materialisation.
- Reviving camera fusion or the broadcast feed.
- Merging the TCN pilot into anything.

## 3. Hard guardrails

Competition rules (from `RULES.md` and `FAQ.md`; reread them, they outrank this summary):
1. No hand labels, hand corrections, or constants tied to specific frames of the provided match. Do not hard-code frame numbers learned from the match or the FAQ into inference; derive them from data with code.
2. The public 5-minute ground truth is a correctness check only. Never use it to train, tune, choose thresholds or choose between versions.
3. No human-produced data about the provided match from any source.
4. The repository must regenerate the submitted file byte-for-byte.
5. Match data must never be committed, and no derived export that would reconstruct it (per-frame tracking, clips, frames).
6. **Do not send provided match material to any hosted model.** You are a hosted model. You may write and run scripts locally against the match data, but you must only read back bounded aggregates: counts, means, histograms with coarse bins, hashes, pass/fail. Never print or read per-frame rows, coordinates, image frames or video of the provided match. If a task seems to need that, stop and ask the user.

Project rules:
7. The frozen release artifact, PRs 1–5, existing seals, logs, receipts and freezes stay byte-identical. All new work is additive, on a new branch.
8. All parameter choices are made on external matches only, from a grid declared and committed before any scoring.
9. No silent protocol amendments. If a declared step cannot run as written, stop, preserve the failure, and ask the user.
10. Report results faithfully, including rejections. A rejected experiment is an acceptable outcome; an unreported one is not.
11. Do not merge, promote, or publish without the user saying so in chat. Commit locally; push and open a draft PR only after the user confirms. Author and committer must be **The-leonjr** (see the older handover for the credential alias; keep credentials out of files).
12. Follow the user's standing preference: Superpowers workflow (spec, then written plan, then test-first implementation), sequential bounded goals.

Stop and ask the user when: a stage gate fails, a rule seems to conflict with a step, a path or cohort named here does not exist, or the budget in section 6 is exhausted.

## 4. Stages

Work on a new branch from `431d1ec`, suggested name `codex/touch-evidence-2026-11-10`.
First action: write the spec to `docs/superpowers/specs/2026-11-10-touch-evidence-design.md` from sections 2–6 of this file, then the implementation plan, then implement test-first.

### Stage 0 — two numeric probes on the challenge match (aggregates only)

Purpose: settle the pose question with a number, and measure how much the touch layer has to work with.

- **Probe A, apparent size.** Using the tactical homography and tracked player positions, compute the local image scale (pixels per metre, across the viewing direction) at each tracked player position on graded frames. Report only: quantiles (5/25/50/75/95) of estimated standing-player height in pixels (scale × 1.8 m) and of ball diameter in pixels (scale × 0.22 m).
  - Decision rule, fixed now: if the median estimated player height is under 100 px, pose estimation is dropped and recorded as "considered and dropped" in the technical document. The 100 px figure is a rule of thumb from the previous assistant, not a measured threshold; the expected result is far below it.
- **Probe B, ball-track shape.** On graded frames report only: count and length distribution of observed-ball runs, count and length distribution of gaps, and the share of observed frames with a tracked player within 2.5 m of the ball.

Output: one small JSON of aggregates, committed. No per-frame data leaves the machine or enters the repo.
Gate: none blocks Stage 1. Probe B is context for interpreting later results.

### Stage 1 — touch detector (pure functions, no reference labels)

New module, suggested `touch_physics.py`. Standard library only, deterministic, no I/O.

Input per frame: period, ball observed flag, ball x/y in metres, home and away player positions in metres (the fields already on `MotionFrame`).
Output: a list of touch events `(frame_index, team, kind)` with `team` in `{'H', 'A', ''}` (empty means contested or unknown) and `kind` in `{'kink', 'reacquire'}`.

Definition, version 1:
- Within a run of observed ball frames in one period, compute `v_before` as mean velocity over the 5 frames before frame t and `v_after` over the 5 frames after. The surprise is `|v_after − v_before|` in m/s. Frames without 5 observed frames on both sides are not candidates.
- Frame t is a kink candidate when the surprise is at least `theta` and is a local maximum within ±5 frames.
- A candidate becomes a touch only if some tracked player is within `R = 2.5 m` of the ball at t. A kink with nobody near is discarded (bounce, flight artefact, tracking jump).
- Team attribution: nearest home distance versus nearest away distance at t. If they differ by at least `0.5 m`, the nearer team gets the touch; otherwise the team is empty.
- Reacquisition: when the ball reappears after a gap, extrapolate the pre-gap velocity across the gap. If the reappearance position is off that line by more than `theta × gap_seconds` and a player is within `R`, emit a `reacquire` touch at the reappearance frame with the same attribution rule. If there is no pre-gap velocity, emit nothing.
- State resets at period boundaries. Nothing is emitted in period 0.

`R`, the 0.5 m margin and the 5-frame windows are fixed design constants, chosen by judgment and not to be tuned. `theta` is a grid parameter (section 6).

### Stage 2 — evidence rows and decoder

New module, suggested `touch_evidence.py`, plus a new decoder function in a new module (do not edit `gap_solver/soft_sequence.py` or `ball_gap_policy.py`).

- **Emission bonus.** After an attributed touch by team T at frame t, add `beta` to T's log-emission on every later usable frame until the next touch event of any kind, the end of the period, or `10 s`, whichever comes first. A contested touch (empty team) ends the previous bonus and starts none. The bonus applies on missing-ball frames too.
- **Switch cost.** The decoder takes a per-frame cost for entering each state. Default is 32 everywhere. At the frame of an attributed touch by T, the cost of entering T is `c_touch`. Costs of entering D or the other team are unchanged.
- Everything else is as in `decode_ball_gap`: zero motion weight, neutral base emissions on missing-ball rows, unsupported all-missing segments excluded, same tie-breaking order, same materialisation afterwards.

Required property: with no touch events, or with `beta = 0` and `c_touch = 32`, labels are identical to `release_runtime.predict_selected` on the same frames.

### Stage 3 — external evaluation

Reuse the memory-ablation cohort so numbers reconcile: 15 already-used external matches; primary = 13 fitting-disjoint matches (10 SkillCorner, 2 DFL, 1 WCSF), equal provider weight, equal match weight within provider; the 2 overlap DFL matches stay secondary. Confirm the exact match list from `memory_ablation_protocol.py` and the PR 5 receipts rather than from this summary.

Regimes:
- `natural`
- `mask30-seed1729` (existing)
- `jitter`: new. Add independent Gaussian noise to observed ball x and y, fixed sigma `0.05 m` per frame, fixed seed, on top of the mask30 regime. This exists because external tracks are cleaner than the challenge tracking, and jitter looks like touches. The sigma is a judgment value, not a measurement of the challenge tracking; declare it in the freeze and do not tune it. (With 5-frame windows this noise gives a typical surprise near 0.6 m/s, well under the smallest `theta`; much larger noise would swamp the detector, which is a known limit of version 1.)

Before any candidate is scored, reproduce the control's primary numbers exactly: natural **0.551816**, masked **0.469149**. If they do not reproduce, stop.

Split, declared in the freeze before scoring:
- Development set: sort SkillCorner primary match IDs ascending, take positions 1, 3, 5, 7, 9; sort the DFL primary IDs, take the first.
- Confirmation set: the remaining 5 SkillCorner, the other DFL match, and WCSF.
- Selection uses the development set only. The confirmation set is scored exactly once, with the single selected configuration.

All of these matches have been used before. Nothing here is a fresh holdout; say so in the results.

### Stage 4 — decision

On the confirmation set, compared with the control:

| Outcome | Condition | Action |
|---|---|---|
| Accept | natural primary spell F1 gain ≥ 0.04, masked and jitter gains > 0, no provider mean declines in natural, safeguards pass | Proceed to Stage 5 |
| Inconclusive | natural gain > 0 but < 0.04, or one secondary condition fails | Report, recommend shipping the control, let the user decide |
| Reject | natural gain ≤ 0 or safeguards fail | Keep the control, write up, stop |

Safeguards (reuse the memory-ablation definitions where they exist): per-match dead-ball recall on DFL and WCSF does not fall by more than 0.02; both owners are still predicted in every match; the predicted-to-reference spell-count ratio does not move further from 1 on the provider mean.

### Stage 5 — challenge run and release (only after Accept and the user's go-ahead)

1. Build a new deterministic entry point beside the existing release; do not modify `competition_release.py` or its manifest. Standard library only, same pinned interpreter as the frozen release.
2. Generate the submission twice from raw inputs into two fresh directories; the CSV bytes must be identical.
3. Run the official `validate_submission.py` on the exact file.
4. Report aggregates only: label counts per class in graded frames, number of predicted spells, number of touch events by kind and team, share of graded frames carrying a bonus.
5. Second-half kickoff audit: report the label counts the candidate emits between the start of the graded second-half block and the second-half kickoff. The FAQ states those frames are all dead ball. If they are not all D, the fix must be derived by code from an allowed input (for example the Smart Tagging `Kick Off (Start)` instance for the 2nd half), never a hard-coded frame number. Treat this as a separate small change with its own test and tell the user before adding it.
6. Public-window check: record the ship/no-ship decision **before** running it. Run it once. It may only veto on a pipeline defect (misalignment, wrong label meaning). It may not reopen selection. For reference the frozen control's single check gave spell F1 0.38 on 17 possessions; a different number for the candidate is not evidence either way.
7. Update the technical document: approach, assets used and dropped (including pose and the TCN), training data, possession rules, limitations, reproduction command.

### Stage V — video ball recovery (probe only; do not build)

Not part of this goal. If and only if Stages 1–4 end in Accept and time remains, write a one-page proposal for recovering missing ball positions from the tactical video and stop for the user's approval. The proposal must address: a publicly available detector and weights with a stated licence; no hand labels on this match; CPU-deterministic inference so the submission stays byte-reproducible; and the fact that recovered positions are noisier than provider tracking.

## 5. Tests and checks

Write each test before the code it covers and watch it fail first. Use the repo's existing `unittest` layout under `tests/`.

**Detector (synthetic tracks, exact expectations)**
1. Straight constant-velocity ball, players far away → 0 touches.
2. Straight decelerating ball → 0 touches.
3. One 90° direction change with a home player 0.5 m from the ball and no away player within 5 m → exactly 1 touch, team H, within ±2 frames of the true change.
4. Same change with no player within `R` → 0 touches.
5. Same change with home and away players both 0.6 m away → 1 touch with empty team.
6. Straight 500-frame track with seeded Gaussian jitter at the declared sigma and a player kept within 1 m of the ball → 0 touches at every grid `theta`. If this fails, the grid is wrong for the declared noise; stop and tell the user rather than quietly changing either.
7. Gap, then reappearance on the extrapolated line → 0 touches. Gap, then reappearance well off the line next to an away player → 1 `reacquire` touch, team A, at the reappearance frame.
8. Kink in the last frame before a period change does not leak into the next period; period 0 never emits.
9. Mirror symmetry: swapping home and away inputs swaps the teams in the output and changes nothing else.
10. Invalid input (non-finite coordinates on an observed frame, bad period) raises `ValueError`.

**Evidence and decoder**
11. Parity A: the new decoder with constant cost 32 returns exactly the same labels as `decode_soft` on at least 200 seeded random emission sequences, including ties, unusable rows and period changes.
12. Parity B: the full candidate with no touch events, and separately with `beta = 0, c_touch = 32`, returns labels identical to `predict_selected` on the existing release fixtures.
13. Bonus placement: bonus appears only for the attributed team, starts at the touch frame, ends at the next touch, the period end or 10 s, and is present on missing-ball frames inside that span.
14. Mechanism test: a synthetic sequence with weak, ambiguous emissions and a 20-frame away spell between two home spells, with attributed touches at both boundaries, decodes to H–A–H with the candidate and to a single H spell with the control.
15. All emission and cost rows are finite; negative or non-finite parameters raise `ValueError`.

**Isolation and integrity**
16. Static check: the touch modules import nothing that reads reference labels or the official metrics, and no numpy or third-party package.
17. Determinism: the same input twice gives the same label SHA-256.
18. Preservation: existing release, preservation and history tests still pass; the frozen release artifact hash is unchanged.
19. Whole suite: at the starting commit the suite was 565 collected, 21 environment skips, 544 executed, 0 failures. Record the count on your machine before starting. After your work: 0 failures, and executed count = your baseline + your new tests.

**Experiment bookkeeping**
20. The freeze commit (grid, split, sigma, seeds, gates) exists before the first scoring call; its hash appears in the results.
21. Control reproduction equals 0.551816 and 0.469149 to six decimals.
22. Scoring-call count in the receipts equals the declared budget or less.

**Release (Stage 5 only)**
23. Two generations, identical CSV bytes; exactly 199,319 rows; official validator passes; no match data or per-frame derivative in the commit.

## 6. Budget and parameter grid

Grid, declared now, 12 configurations, no additions:
- `theta` ∈ {3, 5} m/s
- `beta` ∈ {1, 2, 4} (log-emission units; base emissions range from about −13.8 to 0)
- `c_touch` ∈ {32, 8}

Budget:
- Development: 12 configurations × the development matches × 3 regimes, once.
- Selection rule: highest natural equal-provider development spell F1 among configurations whose masked and jitter development means are not below the control's; ties go to the smaller `beta`, then `c_touch = 32`, then larger `theta`.
- If no configuration qualifies, the outcome is Reject without touching the confirmation set.
- Confirmation: 1 configuration, once.
- Challenge match: 2 identical generations, 1 validation, 1 public-window check.
- No second grid, no re-tuning after confirmation, no extra regimes. A new idea needs a new plan and the user's approval.


## Implementation conventions declared before computation

- All detector timing uses the canonical 25 Hz grid. Mean velocities use five intervals, (position[t]-position[t-5])*5 and (position[t+5]-position[t])*5. Reacquisition uses the last five pre-gap intervals and elapsed time from the last observed frame to reappearance.
- Equal surprise plateaux select the earliest frame within the ±5 local window, deterministically. Events are sorted and unique per frame. A contested event clears prior evidence.
- Bonus starts at the touch frame (explicit test 13), covers elapsed times strictly less than 10 seconds, and resets at period boundaries.
- Jitter uses random.Random(1729), independent gauss(0,0.05) draws x then y for observed frames after the historical mask. The seed resets per match. Synthetic jitter also uses seed 1729.
- The development set has only SkillCorner and DFL: equal weight across its two represented providers. Confirmation has all three: equal weight across its three represented providers. No WCSF development leakage.
- The 15-match control reproduction is separate from candidate scoring; candidates are scored only for the six development and seven confirmation matches allowed by the split. The two overlap matches remain historical secondary evidence, not additional candidate calls. Development maximum 216 candidate scorings, confirmation maximum 21. Control maximum 45 case/regime scorings (including jitter); counts are separate.
- Probe A is a planar apparent-size proxy, not a physical vertical-body projection: use the image Jacobian in the pitch-width direction, in pixels/metre, at player coordinates; multiply by 1.8 and 0.22. This limitation must accompany results.
- New source files only; every pre-existing tracked file must remain byte-identical to base. Existing local checkout stays in place to preserve sibling-store paths; a separate branch isolates commits. Never push or merge.

## Pre-freeze numerical and receipt verification

Dead recall and provider spell-count ratio safeguards compare exact fractions reconstructed from integer counts. Inclusive floating score thresholds permit only four units in the last binary place to avoid representing an exact .04 gain as slightly smaller; this is rounding treatment, not a scientific nonregression slack. Selection tie order and strict masked/jitter gains remain unchanged.

Each phase has an exclusive entry record and fixed claim inventory. A private exclusive seal binds the exact public case/summary hashes to the committed freeze. Later phases validate the seal and reconstruct control reproduction/selection from the exact receipt inventory. Source hashes must match the actual Git freeze commit, not just the working tree. Input identity is checked before loading and after computation for each match, before its results are persisted.
