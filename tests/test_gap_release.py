import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import gap_liveness
import gap_release as r
from test_gap_liveness import fixture

HANDLING = Path(__file__).resolve().parent.parent / '.superpowers/release/target-handling.json'
CONTROL_SHA = '8d233ff132826d1c4eb96f9e43aa0c39f9a1c514cacf3f18edc673810d18a847'
CANDIDATE_SHA = '17bad133788026749395c977cd88e1ff9b154db8ef9f948394d2ee643d01a5c4'


def labels_sha(labels):
    return hashlib.sha256(''.join(labels).encode('ascii')).hexdigest()


class Synthetic(unittest.TestCase):
    def test_no_gap_no_tag_equals_control(self):
        f = fixture(gaps=())
        control = tuple('HAD'[i % 3] for i in range(len(f)))
        self.assertEqual(r.assemble(f, control, ()).final, control)

    def test_flags_disable_stages(self):
        f = fixture()
        control = ('H',) * len(f)
        full = r.assemble(f, control, (310,))
        self.assertEqual(full.control, control)
        self.assertEqual(full.gapped, gap_liveness.apply_gap_rule(f, control).labels)
        self.assertEqual(full.final[300:500], ('D',) * 200)
        self.assertEqual(full.final[:300], ('D',) * 300)   # kickoff patch: everything before the tag in period 1
        off = r.assemble(f, control, (310,), kickoff=False)
        self.assertEqual(off.final, off.gapped)
        none = r.assemble(f, control, (310,), gap=False, kickoff=False)
        self.assertEqual(none.final, control)


@unittest.skipUnless(HANDLING.exists(), 'provided-match handling file absent')
class ProvidedMatch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        prefix = json.loads(HANDLING.read_text(encoding='utf-8'))['input_prefix']
        paths = [Path(prefix + s) for s in ('_atd.xml', '_atd.txt', '_homography.csv')]
        if not all(p.exists() for p in paths):
            raise unittest.SkipTest('provided-match inputs absent')
        from release_runtime import load_source, predict_selected
        cls.frames, _ = load_source(*paths)
        cls.control = predict_selected(cls.frames).labels

    def test_rebuilds_checked_control_and_candidate(self):
        result = r.assemble(self.frames, self.control, (), kickoff=False)
        self.assertEqual(labels_sha(result.control), CONTROL_SHA)
        self.assertEqual(labels_sha(result.gapped), CANDIDATE_SHA)
        self.assertEqual(labels_sha(r.assemble(self.frames, self.control, (), gap=False, kickoff=False).final), CONTROL_SHA)


if __name__ == '__main__':
    unittest.main()
