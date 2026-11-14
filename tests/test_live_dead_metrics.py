"""Live/dead sequence experiment: three-stream gates on hand-built flats.  Synthetic only."""
import copy
import unittest

import live_dead_metrics as lm
from live_dead_protocol import CASES, PRIMARY, provider_of


def flat(f1=.5, recall=.5, precision=.5, false_d=.01, short_n=30, short_matched=15, interior=.8):
    return dict(spell_f1=f1, dead_precision=precision, dead_recall=recall, false_d=false_d, short_n_gt=short_n,
                short_matched=short_matched, short_recall=short_matched / short_n if short_n else None,
                pred_H=10, pred_A=10, sup_H=5, sup_A=5, interior_acc=interior, interior_n=100, interior_correct=80)


def flats(gain=.02, instant_gain=.0):
    out = {}
    for cid in CASES:
        out[cid] = dict(release=flat(), instant=flat(f1=.5 + instant_gain), temporal=flat(f1=.5 + gain))
        if provider_of(cid) == 'skillcorner':
            for s in out[cid].values():
                s['dead_precision'] = s['dead_recall'] = None
    out['wcsf-used-match']['temporal']['dead_recall'] = .55
    return out


def status(gates, name):
    return gates[name]['status']


class NaturalGateTest(unittest.TestCase):
    def test_baseline_passes(self):
        g = lm.gate_natural(flats())
        self.assertEqual(lm.verdict(dict(natural=g), []), 'PASS', g)

    def test_gain_exactly_threshold_passes(self):
        self.assertEqual(status(lm.gate_natural(flats(gain=.010)), 'spell_gain'), 'pass')
        self.assertEqual(status(lm.gate_natural(flats(gain=.00999)), 'spell_gain'), 'fail')

    def test_provider_and_case_bounds(self):
        f = flats(gain=.05)
        for cid in ('dfl-J03WR9', 'dfl-J03WN1'):
            f[cid]['temporal']['spell_f1'] = .5 - 1e-6
        self.assertEqual(status(lm.gate_natural(f), 'provider_nonregression'), 'pass')
        for cid in ('dfl-J03WR9', 'dfl-J03WN1'):
            f[cid]['temporal']['spell_f1'] = .5 - 2e-6
        self.assertEqual(status(lm.gate_natural(f), 'provider_nonregression'), 'fail')
        f = flats(gain=.05)
        f['skillcorner-1874553']['temporal']['spell_f1'] = .5 - .020
        self.assertEqual(status(lm.gate_natural(f), 'case_loss'), 'pass')
        f['skillcorner-1874553']['temporal']['spell_f1'] = .5 - .0201
        self.assertEqual(status(lm.gate_natural(f), 'case_loss'), 'fail')

    def test_temporal_must_beat_instant(self):
        self.assertEqual(status(lm.gate_natural(flats(gain=.02, instant_gain=.02 - 1e-6)), 'temporal_over_instant'), 'fail')
        self.assertEqual(status(lm.gate_natural(flats(gain=.02, instant_gain=.02 - 2e-6)), 'temporal_over_instant'), 'pass')

    def test_wcsf_recall_rise(self):
        f = flats()
        f['wcsf-used-match']['temporal']['dead_recall'] = .53
        self.assertEqual(status(lm.gate_natural(f), 'wcsf_dead_recall_rise'), 'pass')
        f['wcsf-used-match']['temporal']['dead_recall'] = .529
        self.assertEqual(status(lm.gate_natural(f), 'wcsf_dead_recall_rise'), 'fail')
        f['wcsf-used-match']['temporal']['dead_recall'] = None
        self.assertEqual(status(lm.gate_natural(f), 'wcsf_dead_recall_rise'), 'unresolved')
        self.assertEqual(lm.verdict(dict(natural=lm.gate_natural(f)), []), 'UNRESOLVED')

    def test_dead_precision_loss(self):
        f = flats()
        f['dfl-J03WN1']['temporal']['dead_precision'] = .49
        self.assertEqual(status(lm.gate_natural(f), 'dead_precision'), 'pass')
        f['dfl-J03WN1']['temporal']['dead_precision'] = .4899
        self.assertEqual(status(lm.gate_natural(f), 'dead_precision'), 'fail')

    def test_false_d_and_owners(self):
        f = flats()
        f['skillcorner-2017461']['temporal']['false_d'] = .01 + .0051
        self.assertEqual(status(lm.gate_natural(f), 'false_d'), 'fail')
        f = flats()
        f['skillcorner-2017461']['temporal']['pred_A'] = 0
        self.assertEqual(status(lm.gate_natural(f), 'owner_presence'), 'fail')
        f['skillcorner-2017461']['release']['sup_A'] = f['skillcorner-2017461']['temporal']['sup_A'] = 0
        self.assertEqual(status(lm.gate_natural(f), 'owner_presence'), 'pass')

    def test_short_spell_regimes(self):
        f = flats()
        for s in ('release', 'temporal'):
            f['dfl-J03WR9'][s].update(short_n_gt=20, short_matched=10, short_recall=.5)
        f['dfl-J03WR9']['temporal'].update(short_matched=10, short_recall=.48)
        self.assertEqual(status(lm.gate_natural(f), 'short_spells'), 'pass')
        f = flats()
        for s in ('release', 'temporal'):
            f['dfl-J03WR9'][s].update(short_n_gt=5, short_matched=3, short_recall=.6)
        f['dfl-J03WR9']['temporal'].update(short_matched=2, short_recall=.4)
        self.assertEqual(status(lm.gate_natural(f), 'short_spells'), 'fail')
        f = flats()
        for cid in PRIMARY:
            for s in f[cid].values():
                s.update(short_n_gt=0, short_matched=0, short_recall=None)
        self.assertEqual(status(lm.gate_natural(f), 'short_spells'), 'non_applicable')

    def test_interior_never_required(self):
        f = flats()
        for cid in CASES:
            f[cid]['temporal']['interior_acc'] = .1
        g = lm.gate_natural(f)
        self.assertEqual(g['interior_accuracy']['status'], 'reported')
        self.assertEqual(lm.verdict(dict(natural=g), []), 'PASS')

    def test_secondary_excluded(self):
        f = flats()
        g = lm.gate_natural(f)
        f2 = copy.deepcopy(f)
        f2['dfl-J03WOH']['temporal'].update(spell_f1=0., dead_recall=0., false_d=1., pred_H=0)
        self.assertEqual(lm.gate_natural(f2), g)

    def test_skillcorner_has_no_dead_checks(self):
        g = lm.gate_natural(flats())
        self.assertEqual(g['dead_precision']['assessed'], 3)
        self.assertEqual(g['false_d']['assessed'], 13)

    def test_missing_primary_case_raises(self):
        f = flats()
        del f['dfl-J03WR9']
        with self.assertRaises(ValueError):
            lm.gate_natural(f)


class StressGateTest(unittest.TestCase):
    def test_stress_loss_bounds(self):
        f = {cid: v for cid, v in flats(gain=-.005).items() if cid in PRIMARY}
        f['wcsf-used-match']['temporal']['dead_recall'] = .5
        g = lm.gate_stress(f)
        self.assertEqual(g['primary_loss']['status'], 'pass')
        self.assertNotIn('spell_gain', g)
        self.assertEqual(lm.gate_stress({c: v for c, v in flats(gain=-.0051).items() if c in PRIMARY})['primary_loss']['status'], 'fail')


class FloorAndVerdictTest(unittest.TestCase):
    def ok(self):
        return {cid: dict(denominator=5000, integration=1000, known_live=125, known_d=125) for cid in PRIMARY}

    def test_coverage_floors_messages(self):
        self.assertEqual(lm.coverage_floors(self.ok()), [])
        c = self.ok()
        c['dfl-J03WR9']['integration'] = 999
        c['dfl-J03WN1'].update(denominator=10101)
        c['skillcorner-1874553'].update(known_live=124, known_d=0)
        c['wcsf-used-match']['known_d'] = 124
        problems = lm.coverage_floors(c)
        self.assertEqual(len(problems), 4, problems)
        self.assertTrue(any('dfl-J03WR9' in p and 'integration' in p for p in problems))
        self.assertTrue(any('dfl-J03WN1' in p and 'share' in p for p in problems))
        self.assertTrue(any('skillcorner-1874553' in p and 'live' in p for p in problems))
        self.assertTrue(any('wcsf-used-match' in p and 'D' in p for p in problems))
        c = self.ok()
        c['dfl-J03WR9']['denominator'] = 0
        self.assertTrue(lm.coverage_floors(c))
        del c['dfl-J03WR9']
        self.assertTrue(any('dfl-J03WR9' in p for p in lm.coverage_floors(c)))

    def test_hard_fail_outranks_candidate_unresolved(self):
        f = flats(gain=.0)
        f['dfl-J03WN1']['temporal'].update(dead_precision=None, dead_recall=0.)    # collapsed head: no D at all
        g = lm.gate_natural(f)
        self.assertEqual(g['dead_precision']['status'], 'unresolved')
        self.assertEqual(lm.verdict(dict(natural=g), []), 'NO_ADVANCEMENT')

    def test_verdict_precedence(self):
        f = flats(gain=.0)
        g = lm.gate_natural(f)
        self.assertEqual(lm.verdict(dict(natural=g), []), 'NO_ADVANCEMENT')
        self.assertEqual(lm.verdict(dict(natural=g), ['floor shortfall']), 'UNRESOLVED')


if __name__ == '__main__':
    unittest.main()
