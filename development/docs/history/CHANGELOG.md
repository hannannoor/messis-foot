# Changes and reasons

## 5 November 2026 — automatic synchronization and tactical experiment

This update follows `2026.11.05-clock-discovery` and publishes the work completed since that version. The executable is now `2026.11.05-tactical-validated`.

### Why the direction changed

The camera experiment had not established useful missing-ball recovery. Automatic discovery was extended into dense synchronization so it could be evaluated without manual clock setup. Each camera processed 1,704 dense samples with the existing .7 OCR cutoff, five-frame sampling and .25-second timing limit. Neither camera produced bounded dense clock estimates; the alignment had zero usable links. Clock-shaped text is also insufficient to verify live rather than replay footage. Continuing fusion without correspondence would manufacture support, so that work was paused.

The tactical system still left most frames undecided. Instead of choosing settings from this match's coverage, the next work established a licensed external benchmark and selected a small geometry/history model there.

### What changed

- Automatic-sync commands select windows and clock regions from discovery reports, preserve original indices, retain ambiguous half identity and publish complete output generations safely. The fixed OCR recipe was reproduced on generated fixtures; no match-driven cutoff adjustment was used.
- A strict streaming Sportec/DFL adapter separates coordinates from BallStatus/BallPossession reference labels. Unknown codes stay unknown. No target-derived filtering or event outcomes enter model features.
- The benchmark vendors the unchanged MIT-licensed official scoring functions, isolates periods and records whole-match splits, acquisition checksums and attribution.
- A 31-node, depth-four tree was trained on four external matches and selected on one validation match from 24 declared configurations. Natural and label-independent masked observations were tested separately. Model, policy and source hashes were frozen before two final test matches.
- `tactical run` is an explicit opt-in route. It uses geometry quality checks and bounded continuity, ignores Smart Tagging for selected inference, excludes the disputed fixed-D interval and keeps unsupported frames X. It does not replace the legacy default.
- Reports explain uncertainty, compare raw and scorer-expanded behavior, and distinguish coverage from accuracy. Review added guards against negative reprojection errors, injected dead labels and a tagged baseline incorrectly described as identical-input geometry.
- Local delivery stages and hashes all files before atomic publication, preserves a source backup, resumes only known partial files and leaves unrelated content intact.

### What happened in evaluation

| Measure | Baseline | Frozen candidate |
|---|---:|---:|
| Complete external test spellF1, mean of two matches | .37361 | .50513 |
| Complete external test macroF1 | .38871 | .86041 |
| External undecided share | 60.47% | 9.86% |
| Local undecided share, same 158,857-frame scope | 69.192% | 56.151% |
| Local unresolved intervals | 1,045 | 509 |

Both complete external test scores improved under each declared 10/30/50% ball-mask condition. Local output preserves all 199,319 original rows. Its 20,717-frame net X reduction is a coverage result; neither provided GT nor video was used to establish correctness. The comparable local baseline excludes the disputed D interval, unlike the earlier 67.74% X headline.

### What limits the conclusion

An audit found that 449,536/449,539 inactive external ball positions repeat the previous contiguous frame. Motion features can exploit that provider convention. Numeric coordinates do not establish fresh physical observation, and the external D score is not evidence of transferable stoppage recognition.

Newly resolved external agreement was 86.36% H, 88.95% A and 99.78% D; D dominates the pooled 96.32%. Active-only spellF1 declined from .53842 to .53403 and .53548 to .53490. Conditional team accuracy and one home-share estimate also worsened. No post-test gate or retuning was added to hide those regressions.

Most remaining local X consists of missing-ball/no-recent-owner frames (59,788) or insufficient leaf support (26,572). Long gaps, uncertain transitions and geometry failures remain real limits. Full reasoning and additional diagnostics are in [FOUR_GOALS.md](FOUR_GOALS.md).

### Verification and next work

The local suite ran 183 tests successfully with two skips; separate training/export and isolated CLI checks passed. Publication-checkout verification is recorded in [VERIFICATION.md](VERIFICATION.md). Source parity, Python 3.9 syntax, frozen identity, all 21 external checksums and the local output format were checked. Fresh independent review approved only a qualified opt-in experiment.

Next proposed work: independent provider validation, followed by externally validated inference across missing-ball intervals. Near-complete coverage is the ambition; forcing X to zero without quality evidence is not the acceptance criterion. This upload contains code, documents and external model/provenance metadata, not provided match assets or per-frame outputs.
