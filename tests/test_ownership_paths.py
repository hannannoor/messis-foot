"""Independent tiny-path oracles for the diagnostic, never provider data."""
import ast
from itertools import product
import math
from pathlib import Path
import unittest

from gap_solver.soft_sequence import decode_soft
try:
    import ownership_paths as paths
except ImportError:
    paths = None


def objective(emissions, states, cost):
    return sum(row[state] for row, state in zip(emissions, states))-cost*sum(a!=b for a,b in zip(states,states[1:]))


class OwnershipPaths(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(paths, 'Complete-segment instrument is missing')

    def test_exhaustive_unconstrained_and_every_forced_state(self):
        rows = [(0.,-2.,-4.),(-3.,-.5,0.),(-.3,-.7,-1.2),(0.,0.,0.),(-1.,-.2,-3.)]
        for n in range(1,6):
            emissions = rows[:n]
            for cost in (0.,1.75,32.):
                with self.subTest(n=n,cost=cost):
                    oracle = [(objective(emissions,state,cost),state) for state in product(range(3),repeat=n)]
                    table = paths.path_tables(emissions,cost)
                    self.assertAlmostEqual(table.score,max(v for v,_ in oracle),places=8)
                    self.assertEqual(table.labels,tuple(decode_soft(emissions,[1]*n,[True]*n,cost)))
                    self.assertAlmostEqual(objective(emissions,['HAD'.index(x) for x in table.labels],cost),table.score,places=8)
                    for i in range(n):
                        for state in range(3):
                            forced = max(v for v,s in oracle if s[i]==state)
                            self.assertAlmostEqual(table.forward[i][state]+table.backward[i][state],forced,places=8)
                            for side in ('forward','backward'):
                                score = getattr(table,side)[i][state]
                                emission = getattr(table,side+'_emissions')[i][state]
                                switches = getattr(table,side+'_switches')[i][state]
                                self.assertAlmostEqual(emission-cost*switches,score,places=8)
                        summary=paths.state_summary(table,i,0,2)
                        self.assertAlmostEqual(summary['prefix_before']+summary['local']+summary['future'],summary['full'],places=8)
                        self.assertAlmostEqual(summary['emission_margin']+summary['switch_margin'],summary['full'],places=8)

    def test_suffix_changes_full_not_prefix_margin(self):
        left=paths.path_tables([(0.,-1.,-5.)]+[(0.,-3.,-8.)]*5,1.75)
        right=paths.path_tables([(0.,-1.,-5.)]+[(-3.,0.,-8.)]*5,1.75)
        a=paths.constraint_summary(left,0,0);b=paths.constraint_summary(right,0,0)
        self.assertEqual(a['prefix_before'],0.)
        self.assertEqual(a['local'],-1.)
        self.assertEqual(a['prefix'],b['prefix'])
        self.assertAlmostEqual(a['full'],-2.75)
        self.assertAlmostEqual(b['full'],.75)

    def test_D_neutral_ties_and_unique_swap(self):
        neutral=paths.path_tables([(0.,0.,0.)]*5)
        self.assertEqual(neutral.labels,tuple('HHHHH'))
        self.assertGreater(neutral.exact_ties,0)
        self.assertTrue(paths.state_summary(neutral,2,0,2)['numerical_tie'])
        dead=paths.path_tables([(0.,-40.,-40.)]+[(-40.,-40.,0.)]*3+[(0.,-40.,-40.)])
        self.assertEqual(dead.labels,tuple('HDDDH'))
        original=[(0.,-10.,-20.)]*4+[(-10.,0.,-20.)]*4
        one=paths.path_tables(original,1.75)
        swapped=paths.path_tables([(a,h,d) for h,a,d in original],1.75)
        self.assertEqual(swapped.labels,tuple({'H':'A','A':'H','D':'D'}[x] for x in one.labels))

    def test_patch_boundary_switch_algebra(self):
        emissions=[(0.,-40.,-40.)]+[(-40.,-40.,0.)]*3+[(0.,-40.,-40.)]
        table=paths.path_tables(emissions)
        middle=paths.patch_summary(emissions,table.labels,1,4,0)
        self.assertEqual(middle['emission_gain'],-120.)
        self.assertEqual(middle['additional_switches'],-2)
        self.assertEqual(middle['objective_gain'],-56.)
        first=paths.patch_summary(emissions,table.labels,0,1,2)
        self.assertEqual(first['objective_gain'],-8.)
        for start in range(5):
            for stop in range(start+1,6):
                for state in range(3):
                    summary=paths.patch_summary(emissions,table.labels,start,stop,state)
                    replacement=list(table.labels);replacement[start:stop]=['HAD'[state]]*(stop-start)
                    delta=objective(emissions,['HAD'.index(x) for x in replacement],32.)-table.score
                    self.assertAlmostEqual(summary['objective_gain'],delta,places=8)
                    self.assertLessEqual(delta,1e-6)

    def test_invalid_and_overflow_inputs_fail(self):
        for emissions,cost in (([],32.),([(0.,0.)],32.),([(0.,float('nan'),0.)],32.),
                               ([(0.,0.,0.)],-1.),([(0.,0.,0.)],float('inf')),
                               ([(1e308,-1e308,0.)]*5,32.)):
            with self.subTest(emissions=emissions,cost=cost),self.assertRaises(ValueError):
                paths.path_tables(emissions,cost)
        table=paths.path_tables([(0.,-1.,-2.)]*3)
        for index,state in ((-1,0),(3,0),(0,3),(0,-1),(0,True)):
            with self.assertRaises(ValueError):paths.state_summary(table,index,state,0)
        with self.assertRaises(ValueError):paths.constraint_summary(table,0,2)
        for first,stop in ((-1,1),(1,1),(0,4)):
            with self.assertRaises(ValueError):paths.patch_summary(table.emissions,table.labels,first,stop,0)

    def test_new_source_has_python39_grammar(self):
        ast.parse((Path(__file__).resolve().parents[1]/'ownership_paths.py').read_text(),feature_version=(3,9))


if __name__=='__main__':unittest.main()
