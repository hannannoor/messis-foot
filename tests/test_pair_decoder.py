"""Experiment G: three-state decoder with a 3x3 pair switch-cost table."""
import random
import unittest

from touch_decoder import decode_variable

try:
    import pair_decoder as m
except ImportError:
    m = None


def case(seed):
    rng = random.Random(seed)
    n = rng.randint(1, 400)
    periods, period = [], rng.choice((0, 1, 2))
    for _ in range(n):
        if rng.random() < .02:
            period = rng.choice((0, 1, 2))
        periods.append(period)
    usable = [rng.random() > .05 for _ in range(n)]
    if seed < 100:   # small integers force exact ties
        emissions = [tuple(float(rng.randint(-3, 3)) for _ in range(3)) for _ in range(n)]
    else:
        emissions = [tuple(rng.uniform(-6, 2) for _ in range(3)) for _ in range(n)]
    return emissions, periods, usable


def matrix(hh=0., **pairs):
    out = [[0., 100., 100.], [100., 0., 100.], [100., 100., 0.]]
    for name, value in pairs.items():
        out['HAD'.index(name[0])]['HAD'.index(name[1])] = value
    return tuple(tuple(r) for r in out)


class PairDecoder(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(m, 'pair_decoder is missing')

    def test_uniform_matrix_equals_decode_variable(self):
        for seed in range(200):
            e, p, u = case(seed)
            with self.subTest(seed=seed):
                self.assertEqual(m.decode_matrix(e, p, u, m.uniform_matrix(32.)),
                                 decode_variable(e, p, u, [(32.,) * 3] * len(p)))

    def test_uniform_matrix_shape(self):
        self.assertEqual(m.uniform_matrix(32.), ((0., 32., 32.), (32., 0., 32.), (32., 32., 0.)))

    def test_cheap_pair_used(self):
        # H for 10 rows, A slightly better for 10 rows, H again for 10 rows
        e = [(1., 0., 0.)] * 10 + [(0., 1., 0.)] * 10 + [(1., 0., 0.)] * 10
        p, u = [1] * 30, [True] * 30
        cheap = m.decode_matrix(e, p, u, matrix(HA=1., AH=1.))
        self.assertEqual(''.join(cheap), 'H' * 10 + 'A' * 10 + 'H' * 10)
        dear = m.decode_matrix(e, p, u, matrix(HA=100., AH=1.))
        self.assertEqual(''.join(dear), 'H' * 30)

    def test_asymmetric_pair(self):
        # D is clearly better in the middle; entering D is cheap but leaving back to H is dear.
        e = [(1., 0., 0.)] * 10 + [(0., 0., 3.)] * 10 + [(1., 0., 0.)] * 10
        p, u = [1] * 30, [True] * 30
        labels = ''.join(m.decode_matrix(e, p, u, matrix(HD=1., DH=100.)))
        self.assertEqual(labels, 'H' * 10 + 'D' * 20)
        both = ''.join(m.decode_matrix(e, p, u, matrix(HD=1., DH=1.)))
        self.assertEqual(both, 'H' * 10 + 'D' * 10 + 'H' * 10)

    def test_rejects_bad_matrix(self):
        e, p, u = [(0., 0., 0.)], [1], [True]
        bad = [((0., 1.), (1., 0.)),
               ((0., -1., 1.), (1., 0., 1.), (1., 1., 0.)),
               ((0., float('nan'), 1.), (1., 0., 1.), (1., 1., 0.)),
               ((0., float('inf'), 1.), (1., 0., 1.), (1., 1., 0.)),
               ((1., 1., 1.), (1., 0., 1.), (1., 1., 0.))]
        for value in bad:
            with self.subTest(value=value), self.assertRaises(ValueError):
                m.decode_matrix(e, p, u, value)


if __name__ == '__main__':
    unittest.main()
