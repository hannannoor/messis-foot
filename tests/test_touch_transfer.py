"""Fixed-brief synthetic checks; no match data or scientific scores."""
import ast
from dataclasses import replace
import hashlib
from pathlib import Path
import unittest

from gap_solver.motion import motion_frame
from gap_liveness import apply_gap_rule
from gap_solver.materialization_control import materialize_abstentions
from observed_touch import detect_observed_touches
from release_runtime import predict_selected
from touch_decoder import decode_variable
from touch_evidence import prepare_evidence
from touch_physics import TouchEvent
from test_gap_liveness import fixture
from test_touch_physics import track
import tracking_profile as p
import touch_transfer as r


class Profile(unittest.TestCase):
    def test_constant_velocity_and_hand_computed_change(self):
        frames = [motion_frame(1, (float(i), 0.), (), ()) for i in range(15)]
        self.assertEqual(p.surprise_values(frames), [0.] * 5)
        # Slope changes from 0 to 1 metre/frame at index 7. At t=5..9,
        # the two five-frame velocities differ by 15,20,25,20,15 m/s.
        frames = [motion_frame(1, (float(max(0, i-7)), 0.), (), ()) for i in range(15)]
        self.assertEqual(p.surprise_values(frames), [15., 20., 25., 20., 15.])
        self.assertEqual(p.profile(frames)['median_surprise_mps'], 20.)

    def test_short_runs_missing_and_period_boundaries(self):
        frames = track(n=21)
        self.assertEqual(p.surprise_values(frames[:10]), [])
        self.assertEqual(len(p.surprise_values(frames[:11])), 1)
        frames[10] = motion_frame(1, None, (), ())
        self.assertEqual(p.surprise_values(frames), [])
        frames = [replace(f, period=1 if i < 10 else 2) for i, f in enumerate(track(n=20))]
        self.assertEqual(p.surprise_values(frames), [])

    def test_owned_rate_and_remote_peaks(self):
        frames = track(n=80, kink=40)
        result = p.profile(frames)
        self.assertEqual(result['owned_touches'], 1)
        self.assertAlmostEqual(result['owned_touch_rate'], 18.75)
        self.assertEqual(result['unattributed_peak_share'], 0.)
        remote = p.profile(track(n=80, kink=40, near=False))
        self.assertEqual(remote['owned_touches'], 0)
        self.assertEqual(remote['unattributed_peak_share'], 1.)


class Thinning(unittest.TestCase):
    def test_hash_subset_identity_determinism_and_order(self):
        events = [TouchEvent(i, 'HA'[i % 2] if i % 3 else '', 'kink') for i in range(120)]
        self.assertEqual(r.thin_events('m', events, 1., 1000.), events)
        owned = 80
        cutoff = round(10000 * round(20. * 1.) / owned)
        expected = [e for e in events if int(hashlib.sha256(f'm:thin:{e.frame_index}'.encode()).hexdigest(), 16) % 10000 < cutoff]
        actual = r.thin_events('m', events, 1., 20.)
        self.assertEqual(actual, expected)
        self.assertEqual(actual, r.thin_events('m', events, 1., 20.))
        self.assertNotEqual(actual, r.thin_events('other', events, 1., 20.))
        self.assertEqual(actual, sorted(actual, key=lambda e: e.frame_index))

    def test_high_rate_matches_unthinned_decoding(self):
        frames = track(n=80, kink=40)
        result = r.variant_labels('fixture', frames, 1e6)
        self.assertEqual(result['candidate+touch-thin'], result['candidate+touch'])


class Restart(unittest.TestCase):
    def test_plain_variable_decoder_matches_frozen_control(self):
        for frames in (track(n=80, kink=40), fixture(), fixture(gaps=())):
            rows, costs, periods, usable, _ = prepare_evidence(frames, [], 0, 32)
            labels = materialize_abstentions(decode_variable(rows, periods, usable, costs), periods)
            self.assertEqual(tuple(labels), tuple(predict_selected(frames).labels))

    def test_no_gap_is_identity(self):
        out = r.variant_labels('no-gap', fixture(gaps=()), 10.)
        self.assertEqual(out['candidate+reset'], out['candidate'])
        self.assertEqual(out['candidate+touch+reset'], out['candidate+touch'])

    def test_restart_unusable_gap_and_first_owner(self):
        frames = fixture()
        periods = [1] * 900
        rows = [(0., -10., -20.)] * 300 + [(0., 0., 0.)] * 200 + [(-2., 0., -20.)] * 20 + [(0., -10., -20.)] * 380
        costs = [(32.,) * 3] * 900
        usable = [True] * 900
        labels = tuple(materialize_abstentions(decode_variable(rows, periods, usable, costs), periods))
        first = apply_gap_rule(frames, labels)
        second, usable2 = r.restart_decode(frames, rows, periods, usable, costs, labels)
        self.assertEqual(first.stoppage_gaps, ((300, 500),))
        self.assertEqual(usable2[300:500], [False] * 200)
        self.assertEqual(second.labels[:300], first.labels[:300])
        self.assertEqual(second.stoppage_gaps, first.stoppage_gaps)
        self.assertEqual(first.labels[500], 'H')
        self.assertEqual(second.labels[500], 'A')


class Boundaries(unittest.TestCase):
    def test_only_profile_cli_loads_provided_and_no_public_truth(self):
        root = Path(__file__).resolve().parent.parent
        for name in ('tracking_profile.py', 'touch_transfer.py', 'touch_transfer_decision.py'):
            source = (root / name).read_text(encoding='utf-8')
            for forbidden in ('gt_public', 'ground_truth', '_smart_tagging', 'submission.csv'):
                self.assertNotIn(forbidden, source)
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name != 'main':
                    text = ast.get_source_segment(source, node)
                    self.assertNotIn('load_source', text)
                    self.assertNotIn('target-handling', text)
            if name != 'tracking_profile.py':
                self.assertNotIn('load_source', source)
                self.assertNotIn('target-handling', source)


class AgreementReporting(unittest.TestCase):
    def test_weighted_per_match_agreement_mean_and_missing_group(self):
        matches = {}
        for cid, before, after in (('a', .2, .4), ('b', .8, .9)):
            matches[cid] = dict(resets={v: dict(owner_agreement_without=dict(share=before),
                                               owner_agreement_with=dict(share=after))
                                       for v in ('candidate+reset', 'candidate+touch+reset')})
        value = r.owner_agreement_means(matches, ('a', 'b'), (.25, .75))
        self.assertAlmostEqual(value['candidate+reset']['without'], .65)
        self.assertAlmostEqual(value['candidate+reset']['with'], .775)
        matches['a'] = dict(resets={'candidate+reset': {}, 'candidate+touch+reset': {}})
        self.assertIsNone(r.owner_agreement_means(matches, ('a',), (1.,)))

    def test_first_owner_diagnostic_skips_dead_unknown_and_period_end(self):
        reference = [0]*4 + [2]*80 + [3, 1, 1] + [2]*80
        periods = [1]*len(reference)
        labels = ['H']*4 + ['D']*80 + ['D', 'X', 'A'] + ['D']*80
        value = r.restart_agreement(reference, labels, periods, [4, 87])
        self.assertEqual(value, dict(matched=1, total=1, share=1.))
        labels[86] = 'H'
        self.assertEqual(r.restart_agreement(reference, labels, periods, [4])['share'], 0.)


if __name__ == '__main__':
    unittest.main()
