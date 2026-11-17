# Version comparison and score estimate (17 November 2026)

**Bottom line.** The submission stays v9. Tonight's two retrains did not produce a better file. My estimate for v9 on the full BAR–ATH match is a spell F1 of about **0.54**, plausibly anywhere from **0.40 to 0.70**, against the organisers' floor of **0.243**. No BAR–ATH ground truth was used for any number here except the organisers' own published baseline scores and one pipeline check recorded earlier.

## 1. What tonight changed

| Attempt | Evidence for | Evidence against | Outcome |
|---|---|---|---|
| Retrain on state-dependent ball loss, with the swap fix | Metrica ownership +0.006 | WCSF −0.030; dev and simulated views flat | Rejected |
| v9 recipe + Metrica games as ownership-only training data (the v10 candidate) | Metrica leave-one-game-out +0.030, 3 of 3 games | Holdout −0.004; WCSF −0.010; simulated views −0.002 to −0.008; clean dev +0.001 | Not recommended |

- **Why the candidate is not recommended:** its gain shows up only on Metrica, where training and test games share the provider. On every other provider it is flat to slightly worse. BAR–ATH is a different provider again.
- **How far the candidate is from v9:** 1.5% of frames differ and it has 289 possessions against 295, so the two files would score within about ±0.01 of each other.
- **Expected improvement over v9 from tonight:** about 0.00, with a range of −0.01 to +0.01. That is inside the metric's noise band of 0.04.
- **What the night did deliver:** a corrected Metrica yardstick, corrected claims in the technical document, a check that v9 still rebuilds to the submitted hash after the code edits, and two ideas ruled out with evidence.

## 2. Version comparison on external data

All figures are spell F1 on matches the scored models never trained on.

| Version | Holdout | Dev CV | Metrica, ownership only | WCSF | Degraded DFL dev | BAR–ATH possessions |
|---|---:|---:|---:|---:|---:|---:|
| Old release | 0.536 | 0.584 | 0.631 | 0.505 | – | 415 |
| v1 | 0.726 | – | – | – | – | 289 |
| v2 | 0.742 | – | 0.835 | – | 0.483 | 337 |
| v3 | 0.746 | – | – | – | 0.590 | 331 |
| v4 | 0.759 | 0.798 | 0.870 | – | 0.599 | 281 |
| v5 | 0.765 | 0.803 | 0.866 | – | 0.664 | 300 |
| v6 | 0.767 | 0.801 | 0.867 | – | 0.676 | 297 |
| v8 | 0.783 | 0.809 | 0.878 | 0.763 | 0.700 | 296 |
| **v9 (submitted)** | as v8 | 0.808 | 0.878 | 0.763 | as v8 | 295 |
| v10 candidate | −0.004 vs v8 recipe | +0.001 | +0.030 | −0.010 | – | 289 |

- **Holdout** is the locked set as it stood for each version (five matches up to v8). The candidate's difference is on the four matches left after WCSF was released, where the v8 recipe scores 0.785 and the candidate recipe 0.781.
- **v9** is v8's models with the gap rule added. The gap rule changes nothing on these matches because their ball is always visible, so v9's rows equal v8's.
- **Candidate row** shows differences against the v8 recipe measured like for like, not absolute scores.
- **Metrica, ownership only** removes dead-ball calls from the score, because Metrica's ball is blanked exactly when play is dead.
- **BAR–ATH possessions** is a count from each file, with no ground truth involved. The old release fragments play into 415 possessions; v4 onwards sit near 290.

## 3. Estimated full-match score on BAR–ATH

| File | Estimate | Plausible range | Basis |
|---|---:|---:|---|
| Organisers' baseline (`baseline_smooth50`) | 0.243 | exact | Published by the organisers |
| Old release | 0.36 | 0.25–0.45 | Scored 0.361 on the public 5 minutes in an earlier pipeline check |
| v1–v2 | 0.50 | 0.37–0.65 | Method below |
| v4–v6 | 0.53 | 0.39–0.68 | Method below |
| v8 | 0.54 | 0.40–0.70 | Method below |
| **v9 (submitted)** | **0.54** | **0.40–0.70** | Method below |
| v10 candidate | 0.54 | 0.40–0.70 | v9 ± 0.01 |

**Method.**
1. **Anchor.** The only BAR–ATH measurement of one of our files is the old release's 0.361 on the public 5-minute window, recorded as a pipeline check before this work. Its scores on external data at the time were 0.51 to 0.63.
2. **Gain on external data.** From the old release to v9 the gain is +0.25 on the holdout, +0.22 on dev, +0.25 on Metrica and +0.26 on WCSF, so about +0.24.
3. **Transfer.** I assume between half and all of that gain carries over to BAR–ATH. That gives 0.48 to 0.60, with 0.54 as the middle.
4. **Widening.** The anchor rests on 17 possessions, and the public window is not the full match: the organisers' own baselines drop by 0.08 to 0.20 from the window to the full match. That widens the range to 0.40–0.70.

**Limits of the estimate.**
- **Ceiling.** If BAR–ATH behaved like the external matches, v9 would score 0.76 to 0.80. I do not expect that, because BAR–ATH loses the ball on 42% of frames and the external matches almost never do.
- **Versions close together.** v4 through v9 are separated by less than 0.02 in this estimate, which is below the metric's noise band. The ordering among them is not established for BAR–ATH.
- **Gap rule.** v9's gap rule decides 94.6% of missing-ball frames as dead. The external data cannot test that choice, so it is the largest single unknown in the v9 figure.
- **No selection on BAR–ATH.** No version was chosen using BAR–ATH ground truth, and the public window was not rerun for this comparison.

## 4. Against the baseline and the old release

| Comparison | Estimated difference |
|---|---:|
| v9 over the organisers' baseline | +0.30 (about 2.2 times the baseline); +0.16 at the low end of the range |
| v9 over the old release | +0.18 |
| v10 candidate over v9 | 0.00 ± 0.01 |
