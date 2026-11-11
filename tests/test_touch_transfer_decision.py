"""Decision thresholds tested on invented aggregate metrics only."""
import copy
import unittest
from touch_transfer import SC_CONFIRM, PRIMARY
from touch_transfer_decision import decide


def results():
    matches = {}
    for cid in SC_CONFIRM+PRIMARY:
        base = dict(spell_f1=.4, dead_recall=.8)
        matches[cid] = dict(variants={
            'candidate': dict(base),
            'candidate+touch': dict(base, spell_f1=.45),
            'candidate+touch-thin': dict(base, spell_f1=.43),
            'candidate+reset': dict(base, spell_f1=.41),
            'candidate+touch+reset': dict(base, spell_f1=.46)})
    return dict(matches=matches)


class Decision(unittest.TestCase):
    def test_all_pass_chooses_unthinned_touch_and_reset(self):
        value = decide(results())
        self.assertTrue(all(g['passed'] for g in value['conditions'].values()))
        self.assertEqual(value['base'], 'candidate+touch')
        self.assertTrue(value['restart_qualifies'])

    def test_touch_failure_switches_reset_base_to_candidate(self):
        value = results()
        for cid in SC_CONFIRM:
            value['matches'][cid]['variants']['candidate+touch-thin']['spell_f1'] = .38
        decision = decide(value)
        self.assertFalse(decision['conditions']['B']['passed'])
        self.assertEqual(decision['base'], 'candidate')
        self.assertTrue(decision['restart_qualifies'])

    def test_e_requires_neither_match_negative_despite_positive_mean(self):
        value = results()
        value['matches']['dfl-J03WR9']['variants']['candidate+touch+reset']['spell_f1'] = .449
        value['matches']['wcsf-used-match']['variants']['candidate+touch+reset']['spell_f1'] = .48
        decision = decide(value)
        self.assertGreater(decision['conditions']['E']['value'], .005)
        self.assertFalse(decision['conditions']['E']['passed'])
        self.assertFalse(decision['restart_qualifies'])

    def test_each_touch_gate_and_reset_harm_gate_can_reject(self):
        for gate, ids, variant, metric, number in (
            ('A', SC_CONFIRM, 'candidate+touch', 'spell_f1', .38),
            ('C', PRIMARY, 'candidate+touch-thin', 'spell_f1', .41),
            ('D', PRIMARY, 'candidate+touch-thin', 'dead_recall', .77),
            ('F', SC_CONFIRM, 'candidate+touch+reset', 'spell_f1', .44),
            ('G', ('dfl-J03WR9', 'wcsf-used-match'), 'candidate+touch+reset', 'dead_recall', .77)):
            with self.subTest(gate=gate):
                value = copy.deepcopy(results())
                for cid in ids:
                    value['matches'][cid]['variants'][variant][metric] = number
                self.assertFalse(decide(value)['conditions'][gate]['passed'])
