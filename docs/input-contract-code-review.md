# Fresh whole-change review and response

Reviewer: independent fresh-context agent,7 November2026; read-only review of the isolated change against its design/plan. No target raw frames, predictions, GT or video inspected. Summary transcribed from the review's final response; this is one review and one substantive fix pass.

## Findings and disposition

1. **Critical — compatibility reports contained scorer transition arrays.** The driver serialized the entire metrics dictionary, including per-event `pairs`, `missed` and `spurious`. These files were held from publication. The driver now selects named scalar/count metrics and coverage fields. A recursive regression rejects event arrays and arbitrary frame fields. Published V1 exports are redacted with all retained scalar values verified identical; V2 is regenerated. No per-event arrays were uploaded.
2. **Important — skipped decoder placeholders became H.** The direct temporal head interpreted zero even on rejected geometry. A mirrored H/A synthetic regression failed with latent H where the head had not run. V2 requires temporal applicability before proposing H/A; otherwise it retains X for the carry layer. Parameters/model are unchanged. V2 freeze records the correction before reruns.
3. **Important — legacy H/A audit was incomplete.** Register/Player order alone omitted XML Team order, and an unused team could have no registered slots. The audit now records legacy team order and per-slot role equality, and requires registered observations on both teams. Away-first/matching-register synthetic cases demonstrate the difference. Both real feeds were re-audited.
4. **Important — malformed homography structures were silently rejected rather than reported.** Duplicate columns, invalid flags and truncated/overlong rows now fail before inference. Correctly shaped records retain the original determinant/error gate. Tests reproduced the previous acceptance and passed after correction.
5. **Important — output protection missed old-Python junctions and audit races.** Protection now reads Windows reparse flags through lstat; a real junction ancestor is rejected on Python3.14 and isolated Python3.11. Reports use exclusive creation; two concurrent writers yield one winner. Dangling symlinks are checked and exclusive creation also refuses existing leaf entries, but that specific regression is skipped because this account lacks Windows symlink privilege. Hardlink and junction cases execute.
6. **Minor, deferred — synthetic audit periods differ from predictor periods.** The explicitly synthetic fixture uses all-period-one prediction while its audit follows the tactical convention. Real tactical runs agree; documented limitation remains.
7. **Documentation impact regraded Important — identity-assisted external preprocessing.** The SkillCorner cache interpolated25Hz points using provider identities. This is now disclosed beside the compatibility discussion; zero changed labels on that cache does not prove transfer to anonymous detections.
8. **Minor, deferred — more direct association tests and grid contract.** The original equidistant test is outside the displacement bound and cannot isolate tie rejection. In-bound ties/crossings and arbitrary direct-caller gaps merit stronger tests. The tactical reader enforces contiguous ticks; the helper assumes a contiguous canonical25Hz input sequence. It is not a general timestamp-aware tracker.
9. **Documentation impact regraded Important — replacement visibility.** Documentation now says staged replacement, explains the temporary destination gap and sibling backup on interruption, and makes no crash-transaction guarantee. The unchanged frozen publication helper was not modified.

The new regressions were observed failing before fixes. Final suite:294 tests,6 skips. The original5 skips remain; the sixth is the unavailable Windows symlink privilege. Two reviewed local runs, hashes and external stress receipts are documented separately. No re-review or model fitting was performed.

## Declined to judge and executor rulings

- Target accuracy, true identity, per-observation freshness and actual target correspondence correctness: remain unverified. No target labels or video were opened; coverage cannot answer these questions.
- Fresh-data rights or full-state coverage beyond the scout: remain unresolved. No new assets were acquired and no opened cohort was relabelled fresh.

## Builder rulings

- No local git repository exists: use isolated exact-byte copies and authenticated GitHub tree verification. Cost: local git history is unavailable; remote receipts and hashes provide traceability.
- Use only predeclared seen development matches1874553/J03WOH for adapter stress. Cost: this gives no fresh generalization or target accuracy result.
- Windows hardlink/junction tests require execution outside the sandbox; all temporary targets stay within the workspace. Cost: this verifies the local Windows environment rather than all platforms.
- Keep audit as a separate read-only command and fix the estimated-correspondence adapter for this candidate. Cost: changing adapter semantics requires a new recorded experiment.
- Regrade preprocessing and transactional-visibility omissions as important documentation issues; correct them without changing inference. Cost if the assumptions fail: compatibility may overstate anonymous transfer and interrupted replacement requires manual backup recovery.

Deferred minor findings are6 and8 above. They remain visible and are not represented as fixed.
