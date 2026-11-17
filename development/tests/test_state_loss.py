import unittest

import numpy as np

try:
    import se_degrade as d
except ImportError:
    d = None


def match():
    """Two halves of 6000 frames. Stoppages: 1000-1400, 3000-3040 (short), 4000-5000 in each half."""
    ref = np.zeros(13000, np.uint8)
    period = np.zeros(13000, np.int8)
    for p, base in ((1, 0), (2, 7000)):
        period[base:base + 6000] = p
        ref[base + 2000:base + 6000] = 1
        for a, b in ((1000, 1400), (3000, 3040), (4000, 5000)):
            ref[base + a:base + b] = 2
    ref[period == 0] = 3
    return ref, period


class StateLoss(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(d, 'se_degrade missing')
        self.ref, self.period = match()

    def test_deterministic_and_seed_dependent(self):
        a = d.state_loss(self.ref, self.period, 'x#sda')
        b = d.state_loss(self.ref, self.period, 'x#sda')
        c = d.state_loss(self.ref, self.period, 'x#sda2')
        self.assertTrue(all(np.array_equal(u, v) for u, v in zip(a, b)))
        self.assertFalse(np.array_equal(a[0], c[0]) and np.array_equal(a[1], c[1]))

    def test_never_outside_periods(self):
        for seed in ('a', 'b', 'c', 'd'):
            drop, kH, kA = d.state_loss(self.ref, self.period, seed)
            off = self.period == 0
            self.assertFalse(drop[off].any()); self.assertFalse(kH[off].any()); self.assertFalse(kA[off].any())

    def test_ball_loss_follows_stoppages(self):
        dead = self.ref == 2
        live = self.ref < 2
        miss_dead, miss_live = [], []
        for i in range(40):
            drop, _, _ = d.state_loss(self.ref, self.period, f's{i}')
            miss_dead.append(drop[dead].mean()); miss_live.append(drop[live].mean())
        self.assertGreater(np.mean(miss_dead), .6)
        self.assertLess(np.mean(miss_live), .1)

    def test_short_stoppage_keeps_ball_and_no_gap_option(self):
        for i in range(20):
            drop, _, _ = d.state_loss(self.ref, self.period, f't{i}', live_gaps=0.0, p_late=0.0)
            self.assertFalse(drop[3000:3040].any()); self.assertFalse(drop[10000:10040].any())
            self.assertFalse(drop[self.ref < 2].any())
        drop, _, _ = d.state_loss(self.ref, self.period, 'u', live_gaps=0.0, p_no_gap=1.0)
        self.assertFalse(drop.any())

    def test_gap_never_starts_before_the_stop(self):
        for i in range(20):
            drop, _, _ = d.state_loss(self.ref, self.period, f'v{i}', live_gaps=0.0)
            for base in (0, 7000):
                self.assertFalse(drop[base + 900:base + 1000].any()); self.assertFalse(drop[base + 3900:base + 4000].any())

    def test_more_players_lost_in_stoppage_gaps(self):
        in_gap, in_live = [], []
        for i in range(40):
            drop, kH, kA = d.state_loss(self.ref, self.period, f'w{i}')
            both = kH.astype(int) + kA
            if drop.any():
                in_gap.append(both[drop & (self.ref == 2)].mean())
            in_live.append(both[(self.ref < 2) & ~drop].mean())
        self.assertGreater(np.mean(in_gap), 2.5); self.assertLess(np.mean(in_live), 1.0)

    def test_variants_shift_the_lag(self):
        frac = {}
        for kind in ('sde2', 'sde3'):
            v = [d.state_loss(self.ref, self.period, f'z{i}', live_gaps=0.0, **d.SD_KINDS[kind])[0][self.ref == 2].mean() for i in range(60)]
            frac[kind] = np.mean(v)
        self.assertGreater(frac['sde2'], frac['sde3'])


if __name__ == '__main__':
    unittest.main()
