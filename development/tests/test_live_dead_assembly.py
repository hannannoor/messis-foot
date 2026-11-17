"""Live/dead sequence experiment: substitution into frozen supports and stream assembly.  Synthetic only."""
from dataclasses import replace
import unittest

import numpy as np

import live_dead_assembly as la
from live_dead_protocol import load_frozen_model
from release_runtime import submission_bytes
from tests.test_live_dead_features import frame

FIELDS = ('control', 'gapped', 'restarted', 'final', 'stoppage_gaps', 'gap_summary', 'kickoff_changed')


def match(count=600):
    fs = []
    for i in range(count):
        ball = None if 200 <= i < 260 else (20. + (i % 300) * .2, 30.)
        f = frame(i, speeds=[(.2 if 300 <= i < 420 else 2.5) + .05 * j for j in range(22)], ball=ball)
        fs.append(f)
    return fs


class SubstitutionTest(unittest.TestCase):
    def test_substitution_values(self):
        out = la.integrate(np.array([[.6, .2, .2]]), np.array([.5]), np.array([True]))
        np.testing.assert_allclose(out, [[.375, .125, .5]], rtol=0, atol=1e-15)

    def test_ratio_preserved_and_normalised(self):
        rng = np.random.default_rng(1)
        frozen = rng.dirichlet((1, 1, 1), size=500)
        q = rng.uniform(size=500)
        out = la.integrate(frozen, q, np.ones(500, dtype=bool))
        np.testing.assert_allclose(out.sum(axis=1), 1., rtol=0, atol=1e-12)
        np.testing.assert_allclose(out[:, 0] / (out[:, 0] + out[:, 1]), frozen[:, 0] / (frozen[:, 0] + frozen[:, 1]),
                                   rtol=1e-12)
        np.testing.assert_allclose(out[:, 2], q.clip(1e-6, 1 - 1e-6), rtol=0, atol=0)

    def test_zero_live_support_uses_half(self):
        out = la.integrate(np.array([[0., 0., 1.]]), np.array([.4]), np.array([True]))
        np.testing.assert_allclose(out, [[.3, .3, .4]], rtol=0, atol=1e-15)

    def test_q_clipped(self):
        out = la.integrate(np.array([[.5, .5, 0.], [.5, .5, 0.]]), np.array([0., 1.]), np.array([True, True]))
        self.assertEqual(out[0, 2], 1e-6)
        self.assertEqual(out[1, 2], 1 - 1e-6)

    def test_unmasked_rows_bitwise_copied(self):
        rng = np.random.default_rng(2)
        frozen = rng.dirichlet((1, 1, 1), size=50)
        mask = rng.uniform(size=50) < .5
        out = la.integrate(frozen, rng.uniform(size=50), mask)
        self.assertEqual(out[~mask].tobytes(), frozen[~mask].tobytes())
        self.assertEqual(out.dtype, np.float64)

    def test_rejects_bad_inputs(self):
        with self.assertRaises(ValueError):
            la.integrate(np.ones((3, 2)), np.zeros(3), np.zeros(3, dtype=bool))
        with self.assertRaises(ValueError):
            la.integrate(np.ones((3, 3)) / 3, np.zeros(2), np.zeros(3, dtype=bool))
        with self.assertRaises(ValueError):
            la.integrate(np.ones((3, 3)) / 3, np.array([0., np.nan, 0.]), np.ones(3, dtype=bool))
        with self.assertRaises(ValueError):
            la.StreamSupportSet('candidate', np.ones((3, 3)) / 3)
        with self.assertRaises(ValueError):
            la.StreamSupportSet('temporal', np.ones((3, 2)))


class MaskTest(unittest.TestCase):
    def test_mask_requires_observed_ball(self):
        fs = [frame(0), frame(1, ball=None), frame(2, valid=False), frame(3, period=0), frame(4)]
        eligible = np.array([True, True, True, True, False])
        np.testing.assert_array_equal(la.integration_mask(fs, eligible), [True, False, False, False, False])
        np.testing.assert_array_equal(la.denominator_mask(fs), [True, False, False, False, True])


class StreamTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frames = match()
        cls.model = load_frozen_model()
        cls.frozen = la.frozen_supports(cls.frames, cls.model)

    def test_release_stream_matches_restart_release(self):
        import restart_release
        real = restart_release.assemble(self.frames, (), use_restart=True)
        mine = la.assemble_stream(self.frames, 'release', self.frozen)
        for name in FIELDS:
            self.assertEqual(getattr(real, name), getattr(mine, name), name)

    def test_empty_mask_reproduces_frozen(self):
        q = np.full(len(self.frames), .9)
        supports = la.integrate(self.frozen, q, np.zeros(len(self.frames), dtype=bool))
        self.assertEqual(supports.tobytes(), self.frozen.tobytes())
        a = la.assemble_stream(self.frames, 'release', self.frozen)
        b = la.assemble_stream(self.frames, 'temporal', supports)
        for name in FIELDS + ('latent',):
            self.assertEqual(getattr(a, name), getattr(b, name), name)
        self.assertEqual(submission_bytes(a.final), submission_bytes(b.final))

    def test_same_gaps_required(self):
        a = la.assemble_stream(self.frames, 'release', self.frozen)
        la.require_same_gaps(dict(release=a, temporal=a))
        with self.assertRaises(ValueError):
            la.require_same_gaps(dict(release=a, temporal=replace(a, stoppage_gaps=a.stoppage_gaps + ((1, 2),))))


if __name__ == '__main__':
    unittest.main()
