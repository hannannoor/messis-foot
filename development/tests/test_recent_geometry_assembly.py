"""Research assembly with supplied supports must reproduce the release exactly and never mix methods."""
import ast
from pathlib import Path
import unittest
from unittest.mock import patch

import numpy as np

from gap_solver.tactical import PortableTree, feature_rows
from gap_solver.tactical_model import FROZEN_MODEL
from memory_ablation import predict_supports
from release_runtime import predict_selected
import restart_release as release
from test_gap_liveness import fixture

try:
    import recent_geometry_assembly as ra
    import recent_geometry_features as rf
except ImportError:  # pragma: no cover - red phase
    ra = None


def frozen_supports(frames):
    tree = PortableTree(FROZEN_MODEL['model'])
    return np.asarray([tree.predict(row) for row in feature_rows(frames)], dtype=np.float64)


def varied(frames):
    """Fixture frames with a mix of distances so the frozen tree emits several leaves."""
    from dataclasses import replace
    out = []
    for i, f in enumerate(frames):
        if f.ball_observed:
            out.append(replace(f, home_distance=.5 + (i % 7), away_distance=2. + (i % 11) * .7))
        else:
            out.append(f)
    return out


class Assembly(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(ra, 'recent_geometry_assembly is missing')

    def frames(self):
        return (varied(fixture()), varied(fixture(gaps=())), varied(fixture(gap_speed=4.)),
                varied(fixture(n=1100, gaps=((300, 500), (700, 800)))))

    def test_frozen_supports_reproduce_the_release_pipeline_exactly(self):
        for frames in self.frames():
            expected = release.assemble(frames, (), use_restart=True)
            got = ra.assemble_research(frames, ra.SupportSet('control', frozen_supports(frames)))
            self.assertEqual(got.control, expected.control)
            self.assertEqual(got.gapped, expected.gapped)
            self.assertEqual(got.restarted, expected.restarted)
            self.assertEqual(got.final, expected.final)
            self.assertEqual(got.stoppage_gaps, expected.stoppage_gaps)
            self.assertEqual(got.gap_summary, expected.gap_summary)
            self.assertEqual(got.kickoff_changed, expected.kickoff_changed)

    def test_intermediate_control_labels_equal_predict_selected(self):
        for frames in self.frames():
            self.assertEqual(ra.assemble_research(frames, ra.SupportSet('control', frozen_supports(frames))).control,
                             predict_selected(frames).labels)

    def test_decoder_pass_counts_and_latent(self):
        frames = self.frames()[0]
        ss = ra.SupportSet('control', frozen_supports(frames))
        plain = ra.assemble_research(frames, ss)
        checked = ra.assemble_research(frames, ss, verify_decoder=True)
        self.assertEqual((plain.decoder_passes, checked.decoder_passes), (2, 3))
        self.assertEqual(ra.assemble_research(frames, ss, use_restart=False).decoder_passes, 1)
        from gap_solver.materialization_control import materialize_abstentions
        self.assertEqual(tuple(materialize_abstentions(list(plain.latent), [f.period for f in frames])), plain.control)
        self.assertEqual(plain.final, checked.final)

    def test_integrity_decode_detects_a_tampered_control(self):
        frames = self.frames()[0]
        ss = ra.SupportSet('control', frozen_supports(frames))
        with patch('recent_geometry_assembly.decode_variable', side_effect=lambda r, p, u, c: ['A'] * len(p)):
            with self.assertRaises(ValueError):
                ra.assemble_research(frames, ss, verify_decoder=True)

    def test_without_restart_matches_release_without_restart(self):
        frames = self.frames()[0]
        expected = release.assemble(frames, (), use_restart=False)
        got = ra.assemble_research(frames, ra.SupportSet('control', frozen_supports(frames)), use_restart=False)
        self.assertEqual(got.final, expected.final)
        self.assertEqual(got.restarted, expected.restarted)

    def test_matrix_route_equals_scalar_route(self):
        frames = self.frames()[0]
        matrix = rf.research_matrix(frames)
        a = ra.SupportSet.from_matrix('control', matrix, FROZEN_MODEL['model'])
        np.testing.assert_array_equal(a.supports, frozen_supports(frames))

    def test_both_decodes_use_the_same_methods_supports_and_never_mix(self):
        frames = self.frames()[3]
        control = ra.SupportSet('control', frozen_supports(frames))
        other = np.tile(np.asarray([[.05, .9, .05]]), (len(frames), 1))
        candidate = ra.SupportSet('candidate', other)
        seen = []
        real = ra.decode_variable

        def spy(rows, periods, usable, costs):
            seen.append(rows)
            return real(rows, periods, usable, costs)

        for support in (control, candidate, control):
            seen.clear()
            with patch('recent_geometry_assembly.decode_variable', side_effect=spy):
                result = ra.assemble_research(frames, support)
            self.assertEqual(len(seen), 1)    # restart decode only; the control decode is decode_ball_gap
            result_verified = None
            seen.clear()
            with patch('recent_geometry_assembly.decode_variable', side_effect=spy):
                result_verified = ra.assemble_research(frames, support, verify_decoder=True)
            self.assertEqual(len(seen), 2)
            self.assertTrue(all(rows is seen[0] for rows in seen), 'integrity and restart decode must share one row set')
            self.assertEqual(result_verified.final, result.final)
            again = ra.assemble_research(frames, support)
            self.assertEqual(result.final, again.final)
        a = ra.assemble_research(frames, control).final
        b = ra.assemble_research(frames, candidate).final
        self.assertNotEqual(a, b)
        self.assertEqual(ra.assemble_research(frames, control).final, a)

    def test_module_never_references_the_frozen_model_or_the_release_inference(self):
        source = (Path(ra.__file__)).read_text(encoding='utf-8')
        names = {n.id for n in ast.walk(ast.parse(source)) if isinstance(n, ast.Name)} | \
                {n.attr for n in ast.walk(ast.parse(source)) if isinstance(n, ast.Attribute)}
        for forbidden in ('FROZEN_MODEL', 'predict_selected', 'prepare_evidence', 'assemble'):
            self.assertNotIn(forbidden, names)

    def test_support_set_validation(self):
        frames = self.frames()[1]
        with self.assertRaises(ValueError):
            ra.SupportSet('both', frozen_supports(frames))
        with self.assertRaises(ValueError):
            ra.SupportSet('control', np.ones((5, 2)))
        bad = frozen_supports(frames); bad[3, 0] = np.nan
        with self.assertRaises(ValueError):
            ra.SupportSet('control', bad)
        with self.assertRaises(ValueError):
            ra.assemble_research(frames[:-1], ra.SupportSet('control', frozen_supports(frames)))

    def test_hinted_frames_are_refused_like_the_release(self):
        from dataclasses import replace
        frames = list(self.frames()[1])
        frames[3] = replace(frames[3], tag_team='H')
        with self.assertRaises(ValueError):
            ra.assemble_research(frames, ra.SupportSet('control', np.tile([[1 / 3, 1 / 3, 1 / 3]], (len(frames), 1))))

    def test_support_arrays_are_read_only_copies(self):
        values = frozen_supports(self.frames()[1])
        s = ra.SupportSet('control', values)
        values[0, 0] = .0
        self.assertNotEqual(s.supports[0, 0], .0)
        with self.assertRaises(ValueError):
            s.supports[0, 0] = 1.


if __name__ == '__main__':
    unittest.main()
