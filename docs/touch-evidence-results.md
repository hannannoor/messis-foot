# Touch evidence experiment — 10 November 2026

Status: **Reject under the prospective safeguards. Recommend the unchanged frozen control.** Stages 0–4 are complete; Stage 5 did not run.

## Stage 0

Challenge inputs matched the frozen release's metadata, tracking and homography SHA-256 values before and after the aggregate probe. No public labels, images, video or tracking rows were read back.

| Apparent-size proxy | 5% | 25% | Median | 75% | 95% |
|---|---:|---:|---:|---:|---:|
| Standing player, pixels | 12.35 | 17.05 | 22.39 | 28.63 | 40.09 |
| Ball diameter, pixels | 1.51 | 2.08 | 2.74 | 3.50 | 4.90 |

This is a **planar pitch-width Jacobian proxy**, multiplied by 1.8 m or .22 m; it is not a measurement of vertical body projection. Under the fixed median <100 px rule, pose estimation is **considered and dropped**.

Across 158,857 graded frames, 94,214 have observed ball coordinates. There are 149 observed-ball runs (median 345 frames, 13.8 seconds) and 150 gaps (median 268 frames, 10.72 seconds). On 59.1101% of observed frames, at least one tracked player is within 2.5 m. Full bounded quantiles and coarse length histograms are in reports/touch-evidence/stage0.json. These describe available input, not touch accuracy or hidden challenge performance.

## Stage 1

Twelve synthetic detector tests pass, including straight/decelerating tracks, attribution, contested/remote contacts, reacquisition, period resets, mirror symmetry, invalid coordinates, and the declared seeded .05 m jitter gate at theta 3 and 5. No parameter was changed after that gate.

## Stage 2

Twelve evidence/decoder tests pass, including 250 seeded constant-cost parity sequences and all three existing synthetic release fixtures. Both no-events and beta=0/c_touch=32 match full incumbent prediction objects. A synthetic H–A–H sequence demonstrates the intended mechanism. Its initial H emission margin was corrected from .1 to .5 so its 20-frame total exceeds the declared touch switch cost 8; the original failure is retained. The first fixture run also hit a Windows temporary-folder permission error; the test now uses the workspace temporary directory. No scientific run was involved.

The existing frozen release artifact retains SHA-256 e8d35e15be9524270bed82352791dc2849087b49b4c2b59c191023954b19eddb. The stable full suite passed: 608 collected, 21 environment skips, 587 executed, zero failures/errors. The original 565-test group has 544 executed and 21 skips, matching the handoff; all 43 new tests execute. Every one of the 551 base tracked files remains byte-identical. No scientific score or promotion has yet occurred.

## Pre-score verification

All 15 external cases and 54 required files exist and match their recorded hashes. The original restricted runs are retained and do not count as a passing baseline. Normal Windows permissions were required for existing folder-link tests; the stable full run took 905.84 seconds. It held source fixed throughout. See native-suite.json and the pre-score review record.

## Prospective freeze and control gate

Freeze commit: `6a5151a552a4d3d1de2650153b53f571f7cccd36`; freeze SHA-256: `5a207320fc6f2c726c417c6ce060072c1d08133f064858d111a4b9be42a7d375`. The full design, exact grid, split, seeds, source/input hashes, runtime and gates were committed before the first scientific score.

| Control primary, 13 fitting-disjoint matches | Required, six decimals | Reproduced |
|---|---:|---:|
| Natural | .551816 | .551816081677 |
| Mask30-seed1729 | .469149 | .469148838945 |
| Jitter after mask30 | No historical target | .393673276003 |

The exact required natural/masked gate passed. The 45 control scores cover all 15 matches and three declared regimes; the two fitting-overlap DFL matches are secondary. Control receipts and the aggregate gate were sealed and committed at `6f93e96` before candidate evaluation.

## Interpretation limits fixed before viewing candidate results

- Contact-team attribution still uses nearest-player geometry and shares some errors with the frozen tree. More reliable ownership at contact is a hypothesis, not an established fact.
- An airborne ball's pitch-plane projection can produce false kinks; the player-within-2.5-m rule is the only version-1 flight safeguard.
- Many challenge touches are invisible because the ball is missing on 41% of graded frames. The bonus can then retain a stale owner for up to ten seconds.
- SkillCorner supplies no known dead-ball labels. Dead-ball safeguards therefore rely on the fitting-disjoint DFL matches and WCSF.
- Every external match was used before, and the control was selected on overlapping evidence. Neither this split nor an improvement is a fresh estimate of hidden challenge performance.
- The .05 m Gaussian jitter level is a judgment, not a measurement of challenge noise. Its effect on the control does not calibrate challenge error.
- The planar size proxy does not establish actual upright player resolution. Pose is recorded as considered and dropped under the fixed proxy rule.
- The prior TCN on the same 18 features, camera fusion, motion-head gates, velocity-only cadence repair and retained-owner ablation remain rejected historical experiments. None was repeated or merged here.

Stage 5 is conditional on Accept and a separate user go-ahead. No candidate challenge generation, public-window check, release packaging, push, merge or promotion has run.

## Stage 3 development selection

All 216 declared candidate scores completed once: 12 configurations × six development matches × three regimes. The automatic selection chose **theta=3 m/s, beta=2, c_touch=8**. The selection was sealed and committed at `b6dd46c` before the first confirmation candidate call. No confirmation candidate result entered selection.

| Development equal-provider mean | Control | Selected | Delta |
|---|---:|---:|---:|
| natural | 0.567550 | 0.660390 | +0.092840 |
| mask30-seed1729 | 0.476420 | 0.536839 | +0.060419 |
| jitter | 0.392956 | 0.437698 | +0.044742 |

The development provider mean uses equal weight for SkillCorner and DFL, the two represented providers. All 12 configurations met the masked/jitter eligibility condition; natural F1 selected the winner. The complete grid remains in selection.json.

## Stage 4 confirmation: Reject

Exactly one selected configuration completed all 21 confirmation scores: seven matches × three regimes, once. Confirmation has five SkillCorner, one DFL and one WCSF match; each provider receives one third of the mean. The committed confirmation/decision checkpoint is `702556f`. No retuning, additional candidate, second grid, challenge candidate generation or public-window check followed.

| Confirmation equal-provider mean | Control | Candidate | Delta |
|---|---:|---:|---:|
| natural | 0.556860 | 0.619634 | +0.062774 |
| mask30-seed1729 | 0.483638 | 0.517002 | +0.033364 |
| jitter | 0.408913 | 0.436680 | +0.027766 |

The natural gain of **+.062774** exceeds the declared .04 threshold, and both masked/jitter mean gains are positive. The outcome is nevertheless **Reject**, because safeguards fail. The natural provider nondecline condition also fails on SkillCorner. This is the prospective rule, not a post-result change of criteria.

| Provider | Regime | Control spell F1 | Candidate | Delta |
|---|---|---:|---:|---:|
| skillcorner | natural | 0.586912 | 0.582943 | -0.003968 |
| skillcorner | mask30-seed1729 | 0.553308 | 0.531607 | -0.021702 |
| skillcorner | jitter | 0.556800 | 0.511591 | -0.045209 |
| dfl | natural | 0.578452 | 0.695827 | +0.117375 |
| dfl | mask30-seed1729 | 0.486469 | 0.567742 | +0.081273 |
| dfl | jitter | 0.320553 | 0.417445 | +0.096893 |
| wcsf | natural | 0.505216 | 0.580132 | +0.074916 |
| wcsf | mask30-seed1729 | 0.411138 | 0.451659 | +0.040521 |
| wcsf | jitter | 0.349388 | 0.381003 | +0.031615 |

### Dead-ball recall safeguard

Three of six supported DFL/WCSF match-regime comparisons lose more than .02 recall. Both owners remain present on known-reference rows in all 21 confirmation cases.

| Match | Regime | Control D recall | Candidate | Delta | Within .02 loss? |
|---|---|---:|---:|---:|---|
| dfl-J03WR9 | natural | 0.993739 | 0.989397 | -0.004342 | Pass |
| dfl-J03WR9 | mask30-seed1729 | 0.960582 | 0.888461 | -0.072121 | Fail |
| dfl-J03WR9 | jitter | 0.000000 | 0.000000 | +0.000000 | Pass |
| wcsf-used-match | natural | 0.496198 | 0.456790 | -0.039408 | Fail |
| wcsf-used-match | mask30-seed1729 | 0.477047 | 0.433471 | -0.043576 | Fail |
| wcsf-used-match | jitter | 0.000000 | 0.000000 | +0.000000 | Pass |

**Jitter limitation:** both the control and candidate predict zero D on the two D-supported confirmation matches under the declared jitter regime. Their D recall is zero, not missing/unsupported. A relative nonregression check cannot establish adequate absolute liveness performance here. The .05 m noise sensitivity is a real limitation of these pipelines on this artificial regime, not a measured prevalence on the challenge match.

### Spell-count ratio safeguard

The mean predicted/reference spell-count ratio moves further from one in five of nine provider-regime comparisons: all three SkillCorner regimes and natural/masked WCSF. Ratios are compared as exact fractions of integer counts before rounding the table.

| Provider | Regime | Control ratio | Candidate ratio | No farther from 1? |
|---|---|---:|---:|---|
| dfl | jitter | 0.564865 | 0.735135 | Pass |
| dfl | mask30-seed1729 | 0.637838 | 0.843243 | Pass |
| dfl | natural | 0.781081 | 0.878378 | Pass |
| skillcorner | jitter | 1.085280 | 1.269776 | Fail |
| skillcorner | mask30-seed1729 | 1.090570 | 1.173179 | Fail |
| skillcorner | natural | 1.312312 | 1.338233 | Fail |
| wcsf | jitter | 0.788321 | 0.844282 | Pass |
| wcsf | mask30-seed1729 | 1.009732 | 1.053528 | Fail |
| wcsf | natural | 1.192214 | 1.204380 | Fail |

## Recommendation and completed budget

Retain **w0-c32-neutral-missing**, the existing frozen control, as the submission candidate. Its saved CSV identity is `4074cc046500e3d54668a81baf5e46f6d90aeb40a0a247fcefbfa8ee1bd226a5`; the release artifact identity is `e8d35e15be9524270bed82352791dc2849087b49b4c2b59c191023954b19eddb`.

The touch hypothesis produced a substantial aggregate spell-F1 gain on this used confirmation evidence, especially DFL and WCSF, but it did not meet the agreed liveness/count/provider conditions. This rejects this selected configuration under this protocol; it does not establish that every touch-based method is ineffective. No alternative was scored after confirmation.

| Scientific stage | Completed | Declared maximum |
|---|---:|---:|
| Control | 45 | 45 |
| Development candidate | 216 | 216 |
| Confirmation candidate | 21 | 21 |
| New fits | 0 | 0 |
| Candidate challenge generations | 0 | Stage 5 not entered |
| Candidate public-window checks | 0 | Stage 5 not entered |

All 282 score receipts are bounded aggregates, without tracking rows or event traces. A final read-only audit checks the private phase seals, exact receipt/claim inventories, committed source/input identities, count-derived F1 arithmetic, selected configuration and decision without another inference or scoring call. Its result is in reports/touch-evidence/verification.json.

Code verification: **608 collected, 21 environment skips, 587 executed, zero failures/errors**. The original group has 565/21/544; all 43 new tests execute. The 551 original tracked files and frozen release bytes remain unchanged. One fresh-context code/protocol review and one failing-first fix pass preceded all scientific scoring; the reviewer did not independently review scientific outcomes. Initial interrupted/restricted verification logs remain preserved and are not counted as passing runs.

Everything is committed locally on `codex/touch-evidence-2026-11-10` as The-leonjr. Nothing was pushed, merged, promoted or submitted. Stage 5 and the separate video-recovery proposal did not run because Accept was not achieved. This experiment's scoring budget is exhausted; another idea needs a new approved plan.

Final audit result: **passed**. All 282 complete score tables reconcile with 45/216/21 exclusive claims; selection, provider means, safeguard failures and Reject are reproduced arithmetically without rescoring. The current source/input hashes match the committed freeze, all 551 old tracked bytes match base, and both saved frozen-control CSVs retain the published hash. See verification.json and fallback-integrity.json. No unresolved important review finding remains; no minor finding is deferred.
