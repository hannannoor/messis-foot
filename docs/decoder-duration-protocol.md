# Experiment D protocol — minimum spell length in the decoder (12 November 2026)

Frozen before any prediction or score. Design approved by the user on 12 November 2026; source spec `C:\Users\leonj\Desktop\dlor\projects\docs\superpowers\specs\2026-11-12-decoder-structure-design.md` (sections 2, 3, 6, 7 reproduced here).

## 1. Question

Does replacing both decodes of the release pipeline with a duration-aware decoder — leaving a spell shorter than L frames costs an extra 32 on top of the normal switch cost — raise natural provider-weighted spell F1 by at least 0.010 without unacceptable losses? The four earlier experiments (control-memory ablation, A, B, C) moved frame ownership but not spell structure; the decoded spell count is wrong in both directions (SkillCorner/WCSF over-split, DFL over-merge).

## 2. Method pair

- **Control:** frozen release tree (`363c45c7…aab4d`) supports → `recent_geometry_assembly.assemble_research` (the release pipeline; release parity proven against `restart_release.assemble`).
- **Candidate:** the same supports → `duration_assembly.assemble_duration(min_run=L, extra=32)`: identical pipeline with `duration_decoder.duration_decode` in the first decode (uniform switch cost 32) and the restart decode (per-row costs from `touch_evidence.evidence_rows`).
- **Decoder:** state (label, run length k ≤ L). Stay: no cost. Switch: the row's cost for the target label, plus 32 if the run being left has k < L. Every usable segment starts each label at k = L. Ties are broken exactly as `touch_decoder.decode_variable` (label order, `>=` chain), with a per-label run order fixed when each run is created.
- **L:** nearest-rank 10th percentile of pooled maximal reference runs (codes H/A/D, periods 1–2, broken by unknown codes, period changes and period 0) in the pinned training caches of `J03WOH, J03WOY, J03WPY, J03WMX`, clamped to [5, 50]. Computed once in preflight and recorded in `preflight.json`. No evaluation reference contributes.
- No fits.

## 3. Cohort, regimes, gates

Exactly Experiment A (`docs/recent-geometry-protocol.md`, `recent_geometry_metrics` constants): 15 cases (13 primary; DFL J03WOH/J03WOY secondary); natural, noise (prefix `decoder-duration-jitter-v1:1729:`, σ 0.25 m), live-gap and stoppage regimes with masks sealed in preflight and required to equal Experiment A's seals; stage 1 natural (gates 1, 3, 4, owner presence, 0.020 per-match natural bound); stage 2 stress only after a stage-1 pass. **Gate 4 (short spells) unchanged**, by the user's explicit decision. Round-off tolerance 1e-12.

## 4. Parity (stop on any failure)

Per natural case, ledger category `parity` with run-scoped identities, no scores:
1. **Release parity:** research assembly with control supports equals the real `restart_release.assemble(frames, (), use_restart=True).final` (all fields).
2. **Equivalence:** `assemble_duration(extra=0)` equals that replica in latent, control, gapped, restarted, final, stoppage gaps and gap summary.
Then **reconciliation** (15 score bundles): primary natural control mean reproduces 0.551816 (to 1e-6).

## 5. Budget

Fits 0; case predictions ≤ 100; score bundles ≤ 115; feature/tree passes ≤ 200; decoder passes ≤ 300; parity separate. Claim on entry; no reruns except a demonstrated defect with a test, inside budget.

## 6. Descriptive reports (no gate)

Per case and method: predicted spell count and number shorter than L (`short_spells` in each case receipt); predicted vs true spell counts from the score bundles.

## 7. Known behaviour recorded before any result

With the penalty, the decoder's optimum lengthens a strong short spell up to L when the extra rows' evidence costs less than 32, rather than deleting it (observed in synthetic tests). Spell boundaries may therefore move by a few frames around strong short spells.

## 8. Order and cut-offs

Commit code and this protocol → `freeze` → commit freeze → `preflight` → `parity` → `natural` → (`stress` only on a stage-1 pass) → `summarise` → report. Stage-1 decision by 23:59 local 14 November 2026; full verdict by 12:00 local 15 November 2026; missing either means stop and report.

## 9. Interpretation

A FAIL rejects this mechanism with these constants on this reused cohort. A PASS qualifies only for a separate release decision; it authorises no submission change by itself. Behaviour on the provided match (42% missing ball) stays unmeasured.

## 10. Hard rules

No provided-match material; no public five-minute ground truth; no constants from the provided match; no hand labels. Existing files byte-identical (`.gitignore` append-only). Commits as The-leonjr; no push, merge, PR, submission generation or upload.
