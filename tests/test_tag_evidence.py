import ast
import hashlib
import json
from math import log
from pathlib import Path
import tempfile
import unittest

from ball_gap_policy import decode_ball_gap
from gap_solver.materialization_control import materialize_abstentions
import tag_evidence as t

XML = '<file><ALL_INSTANCES>{}</ALL_INSTANCES></file>'
INSTANCE = ('<instance><start>{start}</start><end>{end}</end><code>{code}</code>'
            '<label><group>Team</group><text>{team}</text></label></instance>')


def write_xml(directory, items):
    path = Path(directory) / 'tags.xml'
    path.write_text(XML.format(''.join(INSTANCE.format(code=c, team=m, start=s, end=e) for c, m, s, e in items)), encoding='utf-8')
    return path


def decode(rows, periods, effective=None):
    return t.decode_rows(rows, periods, effective if effective is not None else [bool(p) for p in periods])


class Parsing(unittest.TestCase):
    def test_only_mirror_codes_or_na_gives_no_tags(self):
        with tempfile.TemporaryDirectory() as d:
            path = write_xml(d, [('DEFENDING IN MIDDLE THIRD', 'Alpha', 0, 4), ('DEFENSIVE TRANSITION', 'Beta', 0, 4),
                                 ('BUILD UP', 'N/A', 0, 4), ('PROGRESSION', 'n/a', 0, 4)])
            self.assertEqual(t.read_tags(path), ())

    def test_attacking_codes_kept_case_insensitive(self):
        with tempfile.TemporaryDirectory() as d:
            path = write_xml(d, [('build  up', 'Alpha', 1, 2), ('LONG BALL', 'Beta', 3, 4), ('GOALS', 'Alpha', 5, 6)])
            self.assertEqual(len(t.read_tags(path)), 2)

    def test_window_boundaries(self):
        tags = (t.Tag('Alpha', 2.0, 4.0),)           # frames 50 up to but not including 100
        owner, names = t.owner_track(tags, [1] * 150)
        self.assertEqual(names, ('Alpha',))
        self.assertEqual(owner[49], -1)
        self.assertEqual(owner[50], 0)
        self.assertEqual(owner[99], 0)
        self.assertEqual(owner[100], -1)

    def test_overlap_of_both_teams_has_no_owner(self):
        tags = (t.Tag('Alpha', 0.0, 4.0), t.Tag('Beta', 2.0, 6.0))   # overlap frames 50..99
        owner, names = t.owner_track(tags, [1] * 200)
        self.assertEqual(names, ('Alpha', 'Beta'))
        self.assertEqual(owner[0], 0)
        self.assertEqual(owner[49], 0)
        self.assertEqual(set(owner[50:100]), {-1})
        self.assertEqual(owner[100], 1)
        self.assertEqual(owner[149], 1)
        self.assertEqual(owner[150], -1)

    def test_period_zero_has_no_owner(self):
        owner, _ = t.owner_track((t.Tag('Alpha', 0.0, 4.0),), [0] * 50 + [1] * 50 + [0] * 50)
        self.assertEqual(set(owner[:50]), {-1})
        self.assertEqual(set(owner[50:100]), {0})
        self.assertEqual(set(owner[100:]), {-1})


def mapping_fixture(n, agree_share, flip=False, margin=2.0):
    """n confident frames in period 1; labels alternate H/A; the owner agrees with 'T1=H' on agree_share of them."""
    rows, labels, owner = [], [], []
    for i in range(n):
        label = 'H' if i % 2 == 0 else 'A'
        rows.append((margin, 0., -9.) if label == 'H' else (0., margin, -9.))
        labels.append(label)
        agrees = (i / n) < agree_share
        want_h = label == 'H'
        owner.append(0 if want_h == agrees else 1)
    if flip:
        owner = [1 - o for o in owner]
    return rows, labels, owner, [1] * n, [True] * n


class Mapping(unittest.TestCase):
    NAMES = ('Alpha', 'Beta')

    def estimate(self, n, share, flip=False):
        rows, labels, owner, periods, observed = mapping_fixture(n, share, flip)
        return t.estimate_mapping(labels, rows, observed, periods, owner, self.NAMES)

    def test_agreeing_fixture_maps_t1_to_h(self):
        e = self.estimate(4000, .9)
        self.assertTrue(e.enabled)
        self.assertEqual(e.mapping, {'Alpha': 'H', 'Beta': 'A'})
        self.assertAlmostEqual(e.p, .9, places=3)

    def test_mirrored_fixture_maps_t1_to_a_with_same_p(self):
        e = self.estimate(4000, .9, flip=True)
        self.assertTrue(e.enabled)
        self.assertEqual(e.mapping, {'Alpha': 'A', 'Beta': 'H'})
        self.assertAlmostEqual(e.p, .9, places=3)

    def test_p_is_capped_at_095(self):
        self.assertEqual(self.estimate(4000, 1.0).p, .95)

    def test_disabled_below_065(self):
        self.assertFalse(self.estimate(4000, .6).enabled)
        self.assertTrue(self.estimate(4000, .66).enabled)

    def test_disabled_below_2000_frames(self):
        self.assertFalse(self.estimate(1999, .9).enabled)
        self.assertTrue(self.estimate(2000, .9).enabled)

    def test_disabled_unless_exactly_two_team_names(self):
        rows, labels, owner, periods, observed = mapping_fixture(4000, .9)
        self.assertFalse(t.estimate_mapping(labels, rows, observed, periods, owner, ('Alpha',)).enabled)

    def test_confident_frames_use_top_quartile_of_margin(self):
        # 7400 weak frames that disagree with the tag, 2600 strong frames that agree; the 75th-percentile value (7500th of 10000) is strong.
        rows, labels, owner = [], [], []
        for i in range(10000):
            strong = i >= 7400
            rows.append((3., 0., -9.) if strong else (.1, 0., -9.))
            labels.append('H')
            owner.append(0 if strong else 1)
        e = t.estimate_mapping(labels, rows, [True] * 10000, [1] * 10000, owner, self.NAMES)
        self.assertEqual(e.frames, 2600)
        self.assertEqual(e.mapping['Alpha'], 'H')

    def test_unobserved_and_period_zero_frames_are_not_counted(self):
        rows, labels, owner, periods, observed = mapping_fixture(4000, .9)
        self.assertFalse(t.estimate_mapping(labels, rows, [False] * 4000, periods, owner, self.NAMES).enabled)
        self.assertFalse(t.estimate_mapping(labels, rows, [True] * 4000, [0] * 4000, owner, self.NAMES).enabled)


class Fusion(unittest.TestCase):
    NAMES = ('Alpha', 'Beta')
    HOME = {'Alpha': 'H', 'Beta': 'A'}

    def test_one_frame_arithmetic(self):
        rows = [(-1., -2., -3.)]
        out = t.fuse(rows, [0], self.HOME, self.NAMES, .8)
        self.assertAlmostEqual(out[0][0], -1 + log(1.6))
        self.assertAlmostEqual(out[0][1], -2 + log(.4))
        self.assertEqual(out[0][2], -3.)
        out = t.fuse(rows, [1], self.HOME, self.NAMES, .8)
        self.assertAlmostEqual(out[0][0], -1 + log(.4))
        self.assertAlmostEqual(out[0][1], -2 + log(1.6))
        out = t.fuse(rows, [0], {'Alpha': 'A', 'Beta': 'H'}, self.NAMES, .8)
        self.assertAlmostEqual(out[0][1], -2 + log(1.6))
        self.assertAlmostEqual(out[0][0], -1 + log(.4))

    def test_no_owner_leaves_rows_identical_and_d_never_changes(self):
        rows = [(-1., -2., -3.), (-4., -5., -6.)]
        self.assertEqual(t.fuse(rows, [-1, -1], self.HOME, self.NAMES, .9), rows)
        out = t.fuse(rows, [0, 1], self.HOME, self.NAMES, .9)
        self.assertEqual([r[2] for r in out], [-3., -6.])

    def test_short_blip_with_weak_evidence_is_absorbed_but_long_strong_stretch_kept(self):
        # H frames (0,-3,-30); opposite-team frames (-3,0,-30): per-frame advantage d=3 for A.
        # Tag term at p=.9 shifts H relative to A by ln(1.8)-ln(.2)=ln 9=2.197 per frame.
        # Without tags a run of L frames gains 3L against a 2*32=64 switch penalty: L=30 -> 90 (kept).
        # With tags the net is (3-2.197)L: L=30 -> 24.1 < 64 (absorbed); L=100 -> 80.3 > 64 (kept).
        def labels_for(blip, use_tags):
            rows = [(0., -3., -30.)] * 100 + [(-3., 0., -30.)] * blip + [(0., -3., -30.)] * 100
            n = len(rows)
            if use_tags:
                rows = t.fuse(rows, [0] * n, self.HOME, self.NAMES, .9)
            return decode(rows, [1] * n)
        self.assertEqual(labels_for(30, False)[100:130], ['A'] * 30)
        self.assertEqual(labels_for(30, True)[100:130], ['H'] * 30)
        self.assertEqual(labels_for(100, True)[100:200], ['A'] * 100)

    def test_missing_ball_frames_inside_window_take_the_tagged_team(self):
        # Observed A (0 vs 3), then 40 neutral frames, then observed A. The tag says H on the neutral frames only.
        # At p=.95 the shift is ln(1.9)-ln(.1)=2.944 per frame, 118 over 40 frames, above the 64 switch penalty.
        rows = [(-3., 0., -30.)] * 60 + [(0., 0., 0.)] * 40 + [(-3., 0., -30.)] * 60
        owner = [-1] * 60 + [0] * 40 + [-1] * 60
        plain = decode(rows, [1] * 160)
        self.assertEqual(plain[60:100], ['A'] * 40)
        fused = decode(t.fuse(rows, owner, self.HOME, self.NAMES, .95), [1] * 160)
        self.assertEqual(fused[60:100], ['H'] * 40)

    def test_mirror_symmetry(self):
        rows = [(0., -3., -30.)] * 100 + [(-3., 0., -30.)] * 100
        owner = [0] * 200
        a = decode(t.fuse(rows, owner, self.HOME, self.NAMES, .9), [1] * 200)
        swapped = [(r[1], r[0], r[2]) for r in rows]
        b = decode(t.fuse(swapped, owner, {'Alpha': 'A', 'Beta': 'H'}, self.NAMES, .9), [1] * 200)
        self.assertEqual(b, ['A' if v == 'H' else 'H' if v == 'A' else v for v in a])

    def test_mapping_flips_when_home_and_away_swap(self):
        rows, labels, owner, periods, observed = mapping_fixture(4000, .9)
        swapped_rows = [(r[1], r[0], r[2]) for r in rows]
        swapped_labels = ['A' if v == 'H' else 'H' for v in labels]
        e1 = t.estimate_mapping(labels, rows, observed, periods, owner, self.NAMES)
        e2 = t.estimate_mapping(swapped_labels, swapped_rows, observed, periods, owner, self.NAMES)
        self.assertEqual(e1.mapping, {'Alpha': 'H', 'Beta': 'A'})
        self.assertEqual(e2.mapping, {'Alpha': 'A', 'Beta': 'H'})
        self.assertEqual(e1.p, e2.p)


class ControlParity(unittest.TestCase):
    def test_rebuilt_control_equals_decode_ball_gap(self):
        n = 400
        periods = [0] * 20 + [1] * 180 + [0] * 10 + [2] * 190
        observed = [(i % 7) < 4 and not 100 <= i < 160 for i in range(n)]
        usable = [bool(p) for p in periods]
        supports = []
        for i in range(n):
            a = .6 if (i // 40) % 2 else .2
            supports.append((a, .7 - a, .3))
        rows, effective = t.control_rows(supports, periods, usable, observed)
        latent, _ = decode_ball_gap(supports, periods, usable, observed)
        self.assertEqual(materialize_abstentions(t.decode_rows(rows, periods, effective), periods),
                         materialize_abstentions(latent, periods))

    def test_no_tags_labels_equal_control_and_are_deterministic(self):
        n = 300
        periods = [1] * n
        supports = [(.5, .3, .2) if i % 50 < 25 else (.2, .6, .2) for i in range(n)]
        rows, effective = t.control_rows(supports, periods, [True] * n, [True] * n)
        control = materialize_abstentions(t.decode_rows(rows, periods, effective), periods)
        names, home = ('Alpha', 'Beta'), {'Alpha': 'H', 'Beta': 'A'}
        l1 = materialize_abstentions(t.decode_rows(t.fuse(rows, [-1] * n, home, names, .9), periods, effective), periods)
        l2 = materialize_abstentions(t.decode_rows(t.fuse(rows, [-1] * n, home, names, .9), periods, effective), periods)
        self.assertEqual(l1, control)
        self.assertEqual(hashlib.sha256(''.join(l1).encode()).hexdigest(), hashlib.sha256(''.join(l2).encode()).hexdigest())


class Static(unittest.TestCase):
    def test_modules_have_no_ground_truth_third_party_team_name_or_large_integer(self):
        for name in ('tag_evidence.py', 'tag_release.py'):
            path = Path(__file__).resolve().parent.parent / name
            source = path.read_text(encoding='utf-8')
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, ast.Constant) and type(node.value) is int:
                    self.assertLessEqual(abs(node.value), 2000, name)
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    module = (node.module if isinstance(node, ast.ImportFrom) else node.names[0].name) or ''
                    self.assertNotIn(module.split('.')[0], {'numpy', 'pandas', 'scipy', 'sklearn'}, name)
            lowered = source.lower()
            for word in ('barcelona', 'atletic', 'ground_truth', 'groundtruth', 'possession_gt', 'run_evaluation'):
                self.assertNotIn(word, lowered, name)


HANDLING = Path(__file__).resolve().parent.parent / '.superpowers/release/target-handling.json'
CONTROL_SHA = '8d233ff132826d1c4eb96f9e43aa0c39f9a1c514cacf3f18edc673810d18a847'
CSV_SHA = '31b947d3b250b6267a7d8f0aac0c4e4eafd82a4fc873c82759806e676b1bf963'


@unittest.skipUnless(HANDLING.exists(), 'provided-match handling file absent')
class ProvidedMatchDisabled(unittest.TestCase):
    def test_tags_disabled_reproduces_current_candidate(self):
        import tag_release as r
        prefix = json.loads(HANDLING.read_text(encoding='utf-8'))['input_prefix']
        if not Path(prefix + '_atd.txt').exists():
            self.skipTest('inputs absent')
        with tempfile.TemporaryDirectory() as d:
            receipt = r.generate(prefix, prefix + '_smart_tagging.xml', Path(d) / 'out', use_tags=False)
        self.assertEqual(receipt['control_labels_sha256'], CONTROL_SHA)
        self.assertEqual(receipt['csv_sha256'], CSV_SHA)


if __name__ == '__main__':
    unittest.main()
