"""Predeclared held-out acceptance, with paired matches as the resampling unit."""
import numpy as np
from .temporal_selection import validation_gate


def final_acceptance(reports,endpoints,masked_reports=None,masked_endpoints=None,
                     validation_passed=False,regression_passed=False):
    gate=validation_gate(reports,endpoints,masked_reports,masked_endpoints)
    checks=dict(gate['checks']);checks.pop('team_spell_no_match_decline')
    changes=np.asarray([r['selected']['metrics']['spell_f1_mean']-r['baseline']['metrics']['spell_f1_mean'] for r in reports])
    rng=np.random.RandomState(1729);draws=rng.choice(changes,size=(10000,len(changes))).mean(axis=1)
    lower=float(np.quantile(draws,.025))
    checks.update(validation_eligibility=bool(validation_passed),seen_data_regression=bool(regression_passed),
        team_spell_mean_nonnegative=bool(changes.mean()>=0),team_spell_match_tolerance=bool((changes>=-.02).all()),
        paired_bootstrap_lower_bound=lower>-.02)
    return dict(passes=all(checks.values()),checks=checks,paired_spell_changes=changes.tolist(),
        paired_match_bootstrap=dict(draws=10000,seed=1729,lower_95_percent_bound=lower,mean_change=float(changes.mean())),
        recovery_gate=gate,reference_scope='known in-play H/A only; no independent full-state validation')
