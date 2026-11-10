# Touch evidence experiment — 10 November 2026

Status: implementation in progress; no scientific candidate score yet.

## Stage 0

Challenge inputs matched the frozen release's metadata, tracking and homography SHA-256 values before and after the aggregate probe. No public labels, images, video or tracking rows were read back.

| Apparent-size proxy | 5% | 25% | Median | 75% | 95% |
|---|---:|---:|---:|---:|---:|
| Standing player, pixels | 12.35 | 17.05 | 22.39 | 28.63 | 40.09 |
| Ball diameter, pixels | 1.51 | 2.08 | 2.74 | 3.50 | 4.90 |

This is a **planar pitch-width Jacobian proxy**, multiplied by 1.8 m or .22 m; it is not a measurement of vertical body projection. Under the fixed median <100 px rule, pose estimation is **considered and dropped**.

Across 158,857 graded frames, 94,214 have observed ball coordinates. There are 149 observed-ball runs (median 345 frames, 13.8 seconds) and 150 gaps (median 268 frames, 10.72 seconds). On 59.1101% of observed frames, at least one tracked player is within 2.5 m. Full bounded quantiles and coarse length histograms are in reports/touch-evidence/stage0.json. These describe available input, not touch accuracy or hidden challenge performance.

## Stage 1

Ten synthetic detector tests pass, including straight/decelerating tracks, attribution, contested/remote contacts, reacquisition, period resets, mirror symmetry, invalid coordinates, and the declared seeded .05 m jitter gate at theta 3 and 5. No parameter was changed after that gate.

## Stage 2

Twelve evidence/decoder tests pass, including 250 seeded constant-cost parity sequences and all three existing synthetic release fixtures. Both no-events and beta=0/c_touch=32 match full incumbent prediction objects. A synthetic H–A–H sequence demonstrates the intended mechanism. Its initial H emission margin was corrected from .1 to .5 so its 20-frame total exceeds the declared touch switch cost 8; the original failure is retained. The first fixture run also hit a Windows temporary-folder permission error; the test now uses the workspace temporary directory. No scientific run was involved.

The existing frozen release artifact retains SHA-256 e8d35e15be9524270bed82352791dc2849087b49b4c2b59c191023954b19eddb. The stable full suite passed: 608 collected, 21 environment skips, 587 executed, zero failures/errors. The original 565-test group has 544 executed and 21 skips, matching the handoff; all 43 new tests execute. Every one of the 551 base tracked files remains byte-identical. No scientific score or promotion has yet occurred.

## Pre-score verification

All 15 external cases and 54 required files exist and match their recorded hashes. The original restricted runs are retained and do not count as a passing baseline. Normal Windows permissions were required for existing folder-link tests; the stable full run took 905.84 seconds. It held source fixed throughout. See native-suite.json and the pre-score review record.
