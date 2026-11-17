# Touch transfer and decoder restart — fixed protocol, 11 November 2026

Source: WORKER-BRIEF-6-TOUCH-TRANSFER-2026-11-10.md, revised 11 November.
Starting state verified: clean `codex/stoppage-regime-2026-11-10` at
`5147e236235daf9cd9c4ddac6bc9afcd04366b66`; work branch
`codex/touch-transfer-2026-11-10`. MATCHES and split_matches match the brief.
Original tracked sources stay unchanged except the final README/DESIGN update.

## Fixed design and sequence

1. Synthetic tests first: constant/known-change surprise, short and split runs,
   owned rate, exact deterministic hash thinning including unowned events,
   high-rate identity, no-gap restart identity, reset gap flags and unchanged
   pre-gap labels, H-to-A post-gap mechanism, uniform-cost decoder parity, and
   static input boundaries. Initial test run failed because the new profile
   module did not exist; implementation then passed all nine tests.
2. Profile only: provided track, all 15 natural external tracks, and five
   DFL/WCSF stop75-jitter tracks. No scoring. Observed minutes = observed graded
   frames / 1500. Surprise uses five-frame before/after displacements, within
   consecutive observed runs and periods. Peaks use the detector's earliest-tie
   five-frame suppression rule; unattributed means no player within range, not
   a contested attribution. Bonus frame counts use actual emission changes.
3. Stop before scoring unless provided median surprise is within 2% of 1.127,
   owned touch rate within 2% of 10.46, and every primary stop75-jitter median
   surprise is in [0.9, 1.4]. Commit this note and the aggregate profile first.
4. One external evaluation: ten SkillCorner natural tracks and five DFL/WCSF
   stop75-jitter tracks (make_mask stop75, mask_motion_frames, add_jitter).
   Six variants: control, candidate, candidate+touch, candidate+touch-thin,
   candidate+reset, candidate+touch+reset. Fixed touch setting (3,2,8).
   Read thinning rate from the profile; target = round(rate * observed_minutes).
   If owned > target, keep every event type iff SHA256 of
   `{match_id}:thin:{frame_index}` modulo 10000 < round(10000*target/owned).
5. Reset: prepare original evidence, find first gap application stoppage gaps,
   mark their frames unusable, decode the same rows/costs again, materialize,
   apply gap rule again. No predictor changes. Touch evidence is computed
   using the original usable flags. Assert plain variable-decoder parity.
6. Check natural-control reproduction for all 15 matches against proxy-accuracy
   (absolute error <= 1e-9) and three stop75-jitter variants on all five
   DFL/WCSF matches against stoppage-regime (same tolerance). These checks stop
   execution on a mismatch, with no tuning or automatic retry.

Ruling: the brief's 90 variant scores plus natural-control reproduction on
the five DFL/WCSF matches require **95 metric calls**, because those natural
controls are outside the 90 cases. Ten SkillCorner natural controls are reused.
The five additional scores are only the explicitly required reproduction
checks; no additional variants, settings, rates, or regimes are explored.

An exclusive .started marker prevents an interrupted run being silently
repeated; bounded incremental results preserve completed work. A retry requires
a demonstrated and reported code defect. No freeze/seal machinery is added.

## Reports and decisions fixed before scores

Report spell F1, macro F1, dead recall only for DFL/WCSF, predicted/reference
spell counts, touch rates and bonus shares, reset gains and changed shares.
Restart agreement: for each selected reference long-dead run with a later
reference H/A owner in the same period, compare the first predicted H/A owner
after its end with that reference owner (skip D/X separately); no later
predicted owner is incorrect. Store matched/eligible counts as well as shares.
This diagnostic does not gate selection.
Aggregate owner agreement is a weighted mean of the per-match shares, with
the same weights as the reported group; per-match support counts are retained.

SkillCorner confirmation/development means are plain five-match means.
DFL/WCSF primary weights: WN1 .25, WR9 .25, WCSF .5.

Touch replaces the candidate only if all hold:

| Gate | Fixed condition |
|---|---|
| A | SC confirmation touch minus candidate >= -.01 |
| B | SC confirmation thinned touch minus candidate >= -.01 |
| C | DFL/WCSF primary thinned touch minus candidate >= +.02 |
| D | DFL/WCSF primary thinned dead recall minus candidate >= -.02 |

First choose base = unthinned touch if A–D all pass, otherwise candidate.
Restart qualifies only if all hold:

| Gate | Fixed condition |
|---|---|
| E | WR9/WCSF plain mean restart spell gain >= .005 and neither negative |
| F | SC confirmation mean restart spell change >= -.005 |
| G | WR9/WCSF plain mean dead recall change >= -.02 |

Touch-file SHA256: `1de96acb8ac2198c960637f6b20c2438c9ff142e76a9ab463c384b52814b8d14`.
Candidate-file SHA256: `31b947d3b250b6267a7d8f0aac0c4e4eafd82a4fc873c82759806e676b1bf963`.
Both Desktop files matched these hashes before work. User makes the final
choice. No submission generation, public-truth access, push, PR, merge or upload.
Restart qualification only records eligibility for a separate release brief.

Pre-run verification note: the initial full suite ran 755 tests (20 skipped)
with 274 errors under the app's default temporary folder. Traces show Windows
permission failures when creating/writing/cleaning test fixtures there. A
workspace-local temporary-folder probe and the affected tactical CLI group
(6 tests) pass after setting TEMP and TMP to the checkout's .tmp folder.
The full suite is repeated with that environment correction; this is not a
repeat scientific evaluation. The initial test discovery began before the
new tests were imported, so its count is the unchanged baseline count.
Independent author-separated review (same model family) found no critical or
important correctness issue. Its reporting suggestions are addressed before
scoring: mean owner agreement, explicit probe comparison in the final report,
and including the aggregate-only decision module in the static input check.
Pre-run performance change: the runner reuses identical prepared geometry
emissions for the unthinned and thinned touch decodes and their bonus counts.
A new synthetic parity test was observed failing before that helper existed,
then checks exact labels against predict_observed_touch and exact bonus counts
against the standalone profile calculation. No setting or scientific case changes.

## Required limits

All matches were scored before. Touch settings were selected using five
development SkillCorner matches and WN1. This is the third, post-hoc touch
test. SkillCorner has no dead-ball reference and longer possessions. White
noise and random thinning match two aggregate statistics, not the causes of
missed touches. Gate sets contain five and three matches. Restart's expected
gain is about .01, below what two matches can confirm: E is a consistency
check, not proof. The idea followed a probe of WN1/WOH/WOY and SC development;
those matches cannot gate reset. The regime hides the ball up to two seconds
after a restart, which may not match actual reacquisition delay.
