# Live/dead sequence experiment: NO_ADVANCEMENT

Verdict **NO_ADVANCEMENT**: no advancement for this fixed recipe.
Reason: stage 1 NO_ADVANCEMENT; stress not run.

Streams: frozen release, instantaneous binary head, temporal binary head, on reused external development/regression cases. Not a holdout, not a challenge estimate, no significance claim.

## Stage 1: natural inputs

Decision: NO_ADVANCEMENT

| Check | Status | Value | Threshold |
|---|---|---|---|
| case_loss | fail | dfl-J03WN1 -0.097810, dfl-J03WR9 -0.104219, skillcorner-1874553 -0.023120, skillcorner-1886347 -0.046467, skillcorner-2007448 -0.004886, skillcorner-2007721 -0.045845, skillcorner-2010085 -0.006311, skillcorner-2011166 -0.026433, skillcorner-2013725 -0.029834, skillcorner-2015213 -0.020464, skillcorner-2016236 -0.009449, skillcorner-2017461 -0.015662, wcsf-used-match 0.035284 | -0.020001 |
| dead_precision | fail |  | -0.010001 |
| dead_recall | fail |  | -0.010001 |
| false_d | fail |  | 0.005001 |
| interior_accuracy | reported | instant 0.868178, release 0.955367, temporal 0.904787 |  |
| owner_presence | pass |  |  |
| primary_spell_f1 | reported | instant 0.487099, release 0.550954, temporal 0.521428 |  |
| provider_nonregression | fail | dfl -0.101015, skillcorner -0.022847, wcsf 0.035284 | -0.000001 |
| short_spells | fail |  |  |
| spell_gain | fail | -0.029526 | 0.010000 |
| temporal_over_instant | pass | 0.034328 | 0.000001 |
| wcsf_dead_recall_rise | pass | 0.332517 | 0.030000 |

## Budget used

fits 2, stream_runs 45, score_bundles 45, decoder_passes 90, feature_tree_passes 83, parity_checks 36
