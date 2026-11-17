import ast
from pathlib import Path
import tempfile
import unittest

from gap_solver.motion import motion_frame
import kickoff_patch as k

XML = '<file><ALL_INSTANCES>{}</ALL_INSTANCES></file>'
INSTANCE = ('<instance><ID>1</ID><start>{start}</start><end>{end}</end><code>SET PIECES</code>'
            '<label><group>Type</group><text>{text}</text></label></instance>')


def write_xml(directory, items):
    path = Path(directory) / 'tags.xml'
    path.write_text(XML.format(''.join(INSTANCE.format(start=s, end=s + 5, text=t) for s, t in items)), encoding='utf-8')
    return path


def frames(periods):
    return [motion_frame(p, (0., 0.), [(0., 0.)], [(1., 1.)]) for p in periods]


class KickoffPatch(unittest.TestCase):
    def test_starts_convert_seconds_to_frames_and_filter_text(self):
        with tempfile.TemporaryDirectory() as d:
            path = write_xml(d, [(2.0, 'Kick Off (Start)'), (4.0, 'kick  off (start)'), (6.0, 'Throw-in')])
            self.assertEqual(k.kickoff_starts(path), (50, 100))

    def test_frames_before_tag_become_dead_and_later_unchanged(self):
        f = frames([0] * 2 + [1] * 10 + [0] * 2 + [2] * 10)
        labels = ['H'] * len(f)
        out = k.apply_kickoff_patch(f, labels, (6, 20))
        self.assertEqual(out.labels[:2], ('H', 'H'))
        self.assertEqual(out.labels[2:6], ('D',) * 4)
        self.assertEqual(out.labels[6:14], ('H',) * 8)
        self.assertEqual(out.labels[14:20], ('D',) * 6)
        self.assertEqual(out.labels[20:], ('H',) * 4)
        self.assertEqual(out.changed, {1: 4, 2: 6})

    def test_missing_tag_changes_nothing(self):
        f = frames([1] * 5 + [2] * 5)
        out = k.apply_kickoff_patch(f, ['H'] * 10, (7,))   # half 1 has no tag
        self.assertEqual(out.labels, ('H',) * 5 + ('D', 'D') + ('H',) * 3)
        self.assertEqual(out.changed, {1: 0, 2: 2})
        self.assertEqual(k.apply_kickoff_patch(f, ['H'] * 10, ()).labels, ('H',) * 10)

    def test_two_tags_in_one_half_change_nothing(self):
        f = frames([1] * 10)
        out = k.apply_kickoff_patch(f, ['H'] * 10, (3, 6))
        self.assertEqual(out.labels, ('H',) * 10)

    def test_tag_outside_period_changes_nothing(self):
        f = frames([0] * 3 + [1] * 5 + [0] * 3)
        for start in (1, 9, 100, -1):
            self.assertEqual(k.apply_kickoff_patch(f, ['H'] * 11, (start,)).labels, ('H',) * 11)

    def test_period_zero_never_changes(self):
        f = frames([0] * 4 + [1] * 4)
        out = k.apply_kickoff_patch(f, ['A'] * 8, (6,))
        self.assertEqual(out.labels[:4], ('A',) * 4)
        self.assertEqual(out.labels[4:6], ('D', 'D'))

    def test_dimension_and_label_validation(self):
        with self.assertRaises(ValueError):
            k.apply_kickoff_patch(frames([1] * 3), ['H'] * 2, ())
        with self.assertRaises(ValueError):
            k.apply_kickoff_patch(frames([1] * 3), ['H', 'H', 'Q'], ())

    def test_source_has_no_large_integer_and_no_ground_truth(self):
        source = Path(k.__file__).read_text(encoding='utf-8')
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, ast.Constant) and type(node.value) is int:
                self.assertLessEqual(abs(node.value), 1000)
        self.assertNotIn('ground', source.lower())
        self.assertNotIn('open(', source)


if __name__ == '__main__':
    unittest.main()
