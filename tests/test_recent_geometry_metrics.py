"""Interior strata, restart events, provider weighting and every gate at/above/below its threshold."""
import copy
import unittest

import numpy as np

try:
    import recent_geometry_metrics as m
except ImportError:  # pragma: no cover - red phase
    m = None


def flat(**kw):
    base = dict(spell_f1=.5, interior_n=100, interior_correct=80, interior_acc=.8, dead_precision=.9, dead_recall=.9,
                false_d=.02, short_n_gt=30, short_matched=20, short_recall=20 / 30, pred_H=100, pred_A=100, sup_H=100, sup_A=100,
                restart={'same': dict(n=5, correct=3), 'changed': dict(n=5, correct=3)})
    base.update(kw)
    return base


def regime_flats(regime, candidate=None, control=None):
    """Paired flats for every case in the regime.  ``candidate(cid, flat)`` may mutate the candidate row."""
    out = {}
    for cid in m.REGIME_CASES[regime]:
        c, k = flat(), flat()
        if control:
            control(cid, c)
        if candidate:
            candidate(cid, k)
        out[cid] = dict(control=c, candidate=k)
    return out


def only(cid_pred, **change):
    def mutate(cid, f):
        if cid_pred(cid):
            f.update(change)
    return mutate


class Interior(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(m, 'recent_geometry_metrics is missing')

    def test_fifty_frames_from_a_boundary_is_not_interior_fifty_one_is(self):
        gt = np.array([0] * 400, dtype=np.uint8)
        gt[200:] = 1
        mask = m.interior_mask(gt, np.ones(400, dtype=np.uint8))
        self.assertFalse(mask[50]); self.assertTrue(mask[51])           # 50 vs 51 frames from the period start
        self.assertTrue(mask[148]); self.assertFalse(mask[149])         # run [0,200): last frame 199
        self.assertFalse(mask[250]); self.assertTrue(mask[251])
        self.assertFalse(mask[349]); self.assertTrue(mask[348])

    def test_every_state_and_annotation_change_is_a_boundary_and_d_x_are_never_interior(self):
        gt = np.array([0] * 300 + [2] * 300 + [0] * 300 + [3] * 300 + [1] * 300, dtype=np.uint8)
        mask = m.interior_mask(gt, np.ones(len(gt), dtype=np.uint8))
        self.assertFalse(mask[300:600].any()); self.assertFalse(mask[900:1200].any())
        self.assertTrue(mask[100]); self.assertFalse(mask[299]); self.assertFalse(mask[601])

    def test_period_edge_is_a_boundary(self):
        gt = np.zeros(400, dtype=np.uint8)
        periods = np.r_[np.ones(200), np.full(200, 2)].astype(np.uint8)
        mask = m.interior_mask(gt, periods)
        self.assertFalse(mask[199]); self.assertFalse(mask[200]); self.assertFalse(mask[149]); self.assertTrue(mask[148])

    def test_accuracy_counts_d_x_as_wrong_and_ignores_unobserved(self):
        gt = np.zeros(400, dtype=np.uint8)
        pred = gt.copy()
        pred[100] = 1; pred[101] = 2; pred[102] = 3
        seen = np.ones(400, dtype=bool); seen[103:110] = False
        periods = np.ones(400, dtype=np.uint8)
        out = m.interior_accuracy(gt, pred, periods, seen)
        interior = int(m.interior_mask(gt, periods)[:].sum())
        self.assertEqual(out['n'], interior - 7)
        self.assertEqual(out['correct'], interior - 7 - 3)

    def test_transitions_split_by_error_class(self):
        gt = np.zeros(400, dtype=np.uint8); periods = np.ones(400, dtype=np.uint8); seen = np.ones(400, dtype=bool)
        a = gt.copy(); b = gt.copy()
        a[100] = 1; a[101] = 2; a[102] = 0          # control wrong-team, false-D, correct
        b[100] = 0; b[101] = 0; b[102] = 1          # candidate fixes two, breaks one (wrong team)
        lat_a = np.zeros(400, dtype=np.uint8); lat_a[101] = 3
        out = m.interior_transitions(gt, a, b, periods, seen, lat_a, np.zeros(400, dtype=np.uint8))
        self.assertEqual(out['corrections'], dict(wrong_team=1, false_D=0, carried_unsupported=1))
        self.assertEqual(out['introduced'], dict(wrong_team=1, false_D=0, carried_unsupported=0))


class Restart(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(m, 'recent_geometry_metrics is missing')

    def seq(self, *parts):
        return np.concatenate([np.full(n, v, dtype=np.uint8) for v, n in parts])

    def test_eligibility_and_grouping(self):
        gt = self.seq((0, 40), (2, 10), (0, 40), (2, 10), (1, 40), (2, 10), (3, 5), (0, 40), (2, 10))
        events, ungroupable = m.restart_events(gt, np.ones(len(gt), dtype=np.uint8))
        self.assertEqual([(e['kind'], e['before'], e['after']) for e in events], [('same', 0, 0), ('changed', 0, 1)])
        self.assertEqual(ungroupable, 2)    # D then X, and the terminal D

    def test_period_opening_preceding_x_and_terminal_d_are_ungroupable(self):
        gt = self.seq((2, 10), (0, 30), (3, 5), (2, 10), (1, 30), (2, 10))
        events, ungroupable = m.restart_events(gt, np.ones(len(gt), dtype=np.uint8))
        self.assertEqual(events, [])
        self.assertEqual(ungroupable, 3)

    def test_d_run_cannot_span_periods_and_neighbours_must_share_the_period(self):
        gt = self.seq((0, 40), (2, 10), (2, 10), (1, 40))
        periods = np.r_[np.ones(50), np.full(50, 2)].astype(np.uint8)
        events, ungroupable = m.restart_events(gt, periods)
        self.assertEqual(events, [])
        self.assertEqual(ungroupable, 2)

    def outcome(self, correct, length=25, after=1, extra_tail=40):
        gt = self.seq((0, 20), (2, 10), (after, length), (3, 3), (after, extra_tail))
        pred = gt.copy()
        pred[30:30 + length] = 2
        pred[30:30 + correct] = after
        return m.restart_outcomes(gt, pred, np.ones(len(gt), dtype=np.uint8))

    def test_strictly_more_than_half_of_twenty_five(self):
        self.assertEqual(self.outcome(12)['events']['changed']['correct'], 0)
        self.assertEqual(self.outcome(13)['events']['changed']['correct'], 1)

    def test_window_ends_at_next_reference_change_and_ties_fail(self):
        # only 10 live frames of the new owner before the reference changes (to X)
        self.assertEqual(self.outcome(5, length=10)['events']['changed']['correct'], 0)   # 5 of 10 is a tie
        self.assertEqual(self.outcome(6, length=10)['events']['changed']['correct'], 1)

    def test_d_and_x_predictions_count_in_the_denominator_and_never_correct(self):
        gt = self.seq((0, 20), (2, 10), (1, 25), (0, 30))
        pred = gt.copy()
        pred[30:42] = 1        # 12 correct
        pred[42:50] = 2        # D
        pred[50:55] = 3        # X
        out = m.restart_outcomes(gt, pred, np.ones(len(gt), dtype=np.uint8))
        self.assertEqual(out['events']['changed']['correct'], 0)

    def test_first_frame_and_recovery_diagnostics(self):
        gt = self.seq((0, 20), (2, 10), (1, 60))
        pred = gt.copy(); pred[30:34] = 2; pred[34:] = 1
        row = m.restart_outcomes(gt, pred, np.ones(len(gt), dtype=np.uint8))['events']['changed']
        self.assertEqual((row['first_frame_correct'], row['recovered'], row['recovered_correct'], row['latency_sum']), (0, 1, 1, 4))
        pred[30:] = 2
        row = m.restart_outcomes(gt, pred, np.ones(len(gt), dtype=np.uint8))['events']['changed']
        self.assertEqual((row['recovered'], row['correct']), (0, 0))

    def test_recovery_is_censored_by_the_next_reference_change(self):
        gt = self.seq((0, 20), (2, 10), (1, 5), (3, 60))
        pred = gt.copy(); pred[30:35] = 2; pred[35:] = 0
        row = m.restart_outcomes(gt, pred, np.ones(len(gt), dtype=np.uint8))['events']['changed']
        self.assertEqual(row['recovered'], 0)


class Weighting(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(m, 'recent_geometry_metrics is missing')

    def test_case_inventory(self):
        self.assertEqual(len(m.PRIMARY), 13)
        self.assertEqual(sorted(m.SECONDARY), ['dfl-J03WOH', 'dfl-J03WOY'])
        self.assertEqual(sum(len(v) for k, v in m.REGIME_CASES.items()), 15 * 3 + 5)

    def test_natural_weights_are_one_third_per_provider_with_equal_matches(self):
        values = {cid: 0. for cid in m.REGIME_CASES['natural']}
        for cid in m.PRIMARY:
            if cid.startswith('skillcorner'):
                values[cid] = 0.1
            elif cid.startswith('dfl'):
                values[cid] = 0.4 if cid.endswith('WR9') else 0.6
            else:
                values[cid] = 0.9
        total, means = m.weighted(values, 'natural')
        self.assertAlmostEqual(total, (.1 + .5 + .9) / 3)
        self.assertEqual(set(means), set(m.PROVIDERS))

    def test_secondary_cases_never_enter_a_mean(self):
        values = {cid: .5 for cid in m.REGIME_CASES['natural']}
        values['dfl-J03WOH'] = 99.; values['dfl-J03WOY'] = -99.
        self.assertAlmostEqual(m.weighted(values, 'natural')[0], .5)

    def test_stoppage_weights_half_dfl_half_wcsf_primary_only(self):
        values = {'dfl-J03WR9': .2, 'dfl-J03WN1': .4, 'dfl-J03WOH': 50., 'dfl-J03WOY': 50., 'wcsf-used-match': .9}
        total, means = m.weighted(values, 'stoppage')
        self.assertAlmostEqual(total, .5 * .3 + .5 * .9)
        self.assertEqual(set(means), {'dfl', 'wcsf'})

    def test_undefined_value_makes_the_mean_undefined(self):
        values = {cid: .5 for cid in m.REGIME_CASES['natural']}
        values['skillcorner-2007448'] = None
        self.assertIsNone(m.weighted(values, 'natural')[0])


class Gates(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(m, 'recent_geometry_metrics is missing')

    # -- gate 1
    def natural_gain(self, gain, sc_extra=0., acc_gain=.05):
        return m.gate_natural_benefit(regime_flats(
            'natural', candidate=lambda cid, f: f.update(spell_f1=.5 + gain + (sc_extra if cid.startswith('skillcorner') else 0),
                                                           interior_acc=.8 + acc_gain)))

    def test_gain_at_just_below_and_above_the_hurdle(self):
        self.assertEqual(self.natural_gain(.010)['spell_gain']['status'], 'pass')
        self.assertEqual(self.natural_gain(.010 + 1e-9)['spell_gain']['status'], 'pass')
        self.assertEqual(self.natural_gain(.00999)['spell_gain']['status'], 'fail')

    def test_each_provider_must_not_regress(self):
        out = self.natural_gain(.02, sc_extra=-.0600)          # skillcorner mean change = -0.04
        self.assertEqual(out['provider_nonregression']['status'], 'fail')
        ok = m.gate_natural_benefit(regime_flats('natural', candidate=lambda cid, f: f.update(
            spell_f1=.5 + (.03 if cid.startswith('wcsf') else .03 if cid.startswith('dfl') else .03 - 1e-6))))
        self.assertEqual(ok['provider_nonregression']['status'], 'pass')      # exactly -1e-6 slack is allowed on a loss check
        bad = m.gate_natural_benefit(regime_flats('natural', candidate=lambda cid, f: f.update(
            spell_f1=.5 + (.03 if not cid.startswith('wcsf') else -1.1e-6))))
        self.assertEqual(bad['provider_nonregression']['status'], 'fail')

    def test_interior_accuracy_must_improve_by_more_than_one_millionth(self):
        self.assertEqual(self.natural_gain(.02, acc_gain=1e-6 * 1.5)['interior_accuracy']['status'], 'pass')
        self.assertEqual(self.natural_gain(.02, acc_gain=1e-6)['interior_accuracy']['status'], 'fail')
        self.assertEqual(self.natural_gain(.02, acc_gain=0.)['interior_accuracy']['status'], 'fail')
        self.assertEqual(self.natural_gain(.02, acc_gain=-.01)['interior_accuracy']['status'], 'fail')

    def test_per_provider_interior_effects_are_reported(self):
        out = self.natural_gain(.02, acc_gain=.03)
        self.assertEqual(set(out['interior_accuracy']['per_provider']), set(m.PROVIDERS))

    def test_undefined_interior_accuracy_is_unresolved_not_a_pass(self):
        out = m.gate_natural_benefit(regime_flats('natural', candidate=only(lambda c: c == 'wcsf-used-match', interior_acc=None)))
        self.assertEqual(out['interior_accuracy']['status'], 'unresolved')

    def test_missing_regime_cases_are_rejected(self):
        flats = regime_flats('natural')
        del flats['dfl-J03WR9']
        with self.assertRaises(ValueError):
            m.gate_natural_benefit(flats)

    # -- gate 2
    def test_match_loss_bound_twenty_thousandths(self):
        for loss, status in ((.020, 'pass'), (.0200009, 'pass'), (.0201, 'fail')):
            out = m.gate_loss(regime_flats('natural', candidate=only(lambda c: c == 'skillcorner-2007448', spell_f1=.5 - loss)), 'natural')
            self.assertEqual(out['match_loss']['status'], status, loss)

    def test_secondary_match_loss_is_ignored(self):
        out = m.gate_loss(regime_flats('natural', candidate=only(lambda c: c == 'dfl-J03WOH', spell_f1=0.)), 'natural')
        self.assertEqual(out['match_loss']['status'], 'pass')

    def test_stress_primary_loss_bound_five_thousandths(self):
        for regime in ('noise', 'live-gap', 'stoppage'):
            for loss, status in ((.005, 'pass'), (.0050005, 'pass'), (.0051, 'fail')):
                out = m.gate_loss(regime_flats(regime, candidate=lambda cid, f, loss=loss: f.update(spell_f1=.5 - loss)), regime)
                self.assertEqual(out['primary_loss']['status'], status, (regime, loss))

    def test_natural_has_no_primary_loss_check(self):
        self.assertNotIn('primary_loss', m.gate_loss(regime_flats('natural'), 'natural'))

    # -- gate 3
    def dead(self, regime='natural', **change):
        return m.gate_dead_and_owners(regime_flats(regime, candidate=only(lambda c: c == 'dfl-J03WR9', **change)), regime)

    def test_d_precision_and_recall_losses_at_a_hundredth(self):
        for key in ('dead_precision', 'dead_recall'):
            self.assertEqual(self.dead(**{key: .9 - .010})[key]['status'], 'pass')
            self.assertEqual(self.dead(**{key: .9 - .0100009})[key]['status'], 'pass')
            self.assertEqual(self.dead(**{key: .9 - .0101})[key]['status'], 'fail')

    def test_skillcorner_has_no_d_precision_recall_but_has_false_d(self):
        out = m.gate_dead_and_owners(regime_flats('natural', candidate=only(lambda c: c.startswith('skillcorner'), dead_precision=0., dead_recall=0.)), 'natural')
        self.assertEqual((out['dead_precision']['status'], out['dead_recall']['status']), ('pass', 'pass'))
        out = m.gate_dead_and_owners(regime_flats('natural', candidate=only(lambda c: c == 'skillcorner-1874553', false_d=.02 + .0051)), 'natural')
        self.assertEqual(out['false_d']['status'], 'fail')

    def test_false_d_rise_bound_half_a_percent(self):
        for rise, status in ((.005, 'pass'), (.0050009, 'pass'), (.0051, 'fail')):
            self.assertEqual(self.dead(false_d=.02 + rise)['false_d']['status'], status, rise)

    def test_undefined_required_d_support_is_unresolved_never_a_pass(self):
        self.assertEqual(self.dead(dead_precision=None)['dead_precision']['status'], 'unresolved')
        self.assertEqual(self.dead(dead_recall=None)['dead_recall']['status'], 'unresolved')
        self.assertEqual(self.dead(false_d=None)['false_d']['status'], 'unresolved')
        flats = regime_flats('natural', control=only(lambda c: c == 'wcsf-used-match', dead_recall=None))
        self.assertEqual(m.gate_dead_and_owners(flats, 'natural')['dead_recall']['status'], 'unresolved')

    def test_both_owners_must_still_be_predicted_where_each_has_reference_support(self):
        self.assertEqual(self.dead(pred_H=0)['owner_presence']['status'], 'fail')
        self.assertEqual(self.dead(pred_A=0)['owner_presence']['status'], 'fail')
        flats = regime_flats('natural', candidate=only(lambda c: c == 'dfl-J03WR9', pred_A=0), control=only(lambda c: c == 'dfl-J03WR9', sup_A=0))
        self.assertEqual(m.gate_dead_and_owners(flats, 'natural')['owner_presence']['status'], 'pass')

    # -- gate 4
    def short(self, n, control_matched, candidate_matched, control_recall=None, candidate_recall=None):
        def control(cid, f):
            if cid == 'dfl-J03WR9':
                f.update(short_n_gt=n, short_matched=control_matched, short_recall=control_recall)
        def candidate(cid, f):
            if cid == 'dfl-J03WR9':
                f.update(short_n_gt=n, short_matched=candidate_matched, short_recall=candidate_recall)
        return m.gate_short_spells(regime_flats('natural', candidate=candidate, control=control), 'natural')

    def test_twenty_or_more_short_spells_use_recall_loss_two_hundredths(self):
        self.assertEqual(self.short(20, 10, 10, .5, .5 - .02)['status'], 'pass')
        self.assertEqual(self.short(20, 10, 10, .5, .5 - .0200009)['status'], 'pass')
        self.assertEqual(self.short(20, 10, 10, .5, .5 - .0201)['status'], 'fail')
        self.assertEqual(self.short(19, 10, 10, .5, .5)['status'], 'pass')

    def test_one_to_nineteen_short_spells_allow_no_loss_in_matched_count(self):
        self.assertEqual(self.short(19, 10, 10)['status'], 'pass')
        self.assertEqual(self.short(19, 10, 11)['status'], 'pass')
        self.assertEqual(self.short(19, 10, 9)['status'], 'fail')
        self.assertEqual(self.short(1, 1, 0)['status'], 'fail')

    def test_zero_short_spells_is_non_applicable_and_stated(self):
        flats = regime_flats('natural', candidate=lambda c, f: f.update(short_n_gt=0, short_matched=0, short_recall=None),
                             control=lambda c, f: f.update(short_n_gt=0, short_matched=0, short_recall=None))
        out = m.gate_short_spells(flats, 'natural')
        self.assertEqual(out['status'], 'non_applicable')
        self.assertEqual(out['non_applicable'], 13)

    def test_changed_reference_support_is_an_error(self):
        with self.assertRaises(ValueError):
            self.short(25, 10, 10, .4, .4) if False else m.gate_short_spells(
                regime_flats('natural', candidate=only(lambda c: c == 'dfl-J03WR9', short_n_gt=31)), 'natural')

    # -- gate 5
    def test_noise_interior_accuracy_must_not_regress(self):
        for delta, status in ((0., 'pass'), (-1e-6, 'pass'), (-1.1e-6, 'fail'), (.01, 'pass'), (-.01, 'fail')):
            out = m.gate_noise_mechanism(regime_flats('noise', candidate=lambda c, f, d=delta: f.update(interior_acc=.8 + d)))
            self.assertEqual(out['status'], status, delta)

    # -- gate 6
    def stoppage(self, **kw):
        def candidate(cid, f):
            for kind, correct in kw.items():
                if cid == 'dfl-J03WR9':
                    f['restart'] = copy.deepcopy(f['restart']); f['restart'][kind]['correct'] = correct
        return regime_flats('stoppage', candidate=candidate)

    def good_support(self):
        return dict(live_windows=dict(skillcorner=5, dfl=5, wcsf=5), restart_eligible=dict(dfl=20, wcsf=20))

    def test_support_thresholds(self):
        s = self.good_support()
        self.assertEqual(m.gate_support_and_restart(self.stoppage(), **s)['status'], 'pass')
        for key, value, field in (('live_windows', dict(skillcorner=4, dfl=5, wcsf=5), 'live_windows'),
                                  ('live_windows', dict(skillcorner=5, dfl=5, wcsf=None), 'live_windows'),
                                  ('restart_eligible', dict(dfl=19, wcsf=20), 'restart_eligible'),
                                  ('restart_eligible', dict(dfl=20, wcsf=19), 'restart_eligible')):
            bad = dict(s); bad[key] = value
            out = m.gate_support_and_restart(self.stoppage(), **bad)
            self.assertEqual(out['status'], 'blocked', value)
            self.assertTrue(out['problems'])

    def test_correct_count_must_not_fall_within_any_supported_subgroup(self):
        s = self.good_support()
        self.assertEqual(m.gate_support_and_restart(self.stoppage(same=3), **s)['status'], 'pass')
        self.assertEqual(m.gate_support_and_restart(self.stoppage(same=4), **s)['status'], 'pass')
        out = m.gate_support_and_restart(self.stoppage(same=2), **s)
        self.assertEqual(out['status'], 'fail')
        self.assertEqual(out['subgroups']['dfl/same']['status'], 'fail')
        self.assertEqual(m.gate_support_and_restart(self.stoppage(changed=2), **s)['status'], 'fail')

    def test_empty_optional_subgroup_is_reported_unsupported_not_failed(self):
        def empty(cid, f):
            f['restart'] = {'same': dict(n=0, correct=0), 'changed': dict(n=5, correct=3)}
        flats = regime_flats('stoppage', candidate=empty, control=empty)
        out = m.gate_support_and_restart(flats, **self.good_support())
        self.assertEqual(out['subgroups']['wcsf/same']['status'], 'unsupported')
        self.assertEqual(out['status'], 'pass')

    def test_pooling_over_dfl_primary_matches_only(self):
        s = self.good_support()
        def candidate(cid, f):
            if cid == 'dfl-J03WOH':          # secondary: must be ignored even if it collapses
                f['restart'] = {'same': dict(n=5, correct=0), 'changed': dict(n=5, correct=0)}
        out = m.gate_support_and_restart(regime_flats('stoppage', candidate=candidate), **s)
        self.assertEqual(out['status'], 'pass')
        self.assertEqual(out['subgroups']['dfl/same']['n'], 10)

    def test_stage_one_support_check_without_stoppage_results(self):
        out = m.gate_support_and_restart(None, **self.good_support())
        self.assertEqual(out['status'], 'pass')

    # -- verdict
    def test_verdict_passes_only_if_every_check_passes_and_names_each_failure(self):
        good = {'G1': m.gate_natural_benefit(regime_flats('natural', candidate=lambda c, f: f.update(spell_f1=.52, interior_acc=.85))),
                'G4': m.gate_short_spells(regime_flats('natural'), 'natural')}
        self.assertEqual(m.verdict(good)['verdict'], 'PASS')
        bad = copy.deepcopy(good)
        bad['G1']['spell_gain']['status'] = 'fail'
        bad['G4'] = dict(status='unresolved')
        out = m.verdict(bad)
        self.assertEqual(out['verdict'], 'FAIL')
        self.assertEqual(out['failing'], ['G1/spell_gain', 'G4'])
        self.assertEqual(m.verdict({})['verdict'], 'FAIL')


class Bundle(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(m, 'recent_geometry_metrics is missing')

    def test_score_bundle_runs_the_official_scorer_and_flattens(self):
        rng = np.random.RandomState(1)
        ref = np.repeat(np.array([0, 1, 2, 0, 1, 0, 3, 1], dtype=np.uint8), 150)
        periods = np.ones(len(ref), dtype=np.uint8)
        pred = ref.copy(); pred[::17] = 1 - (pred[::17] % 2) if False else pred[::17]
        seen = rng.rand(len(ref)) > .1
        bundle = m.score_bundle(ref, np.where(ref == 3, 0, ref).astype(np.uint8), periods, seen, restart=True)
        flat_ = m.flatten(bundle)
        self.assertIn('restart', flat_)
        self.assertEqual(sum(v['n_gt'] for v in bundle['extras']['spell_bins'].values()), bundle['score']['spells']['n_gt'])
        self.assertEqual(flat_['interior_n'] > 0, True)


if __name__ == '__main__':
    unittest.main()
