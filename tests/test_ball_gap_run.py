import json,tempfile,unittest
from pathlib import Path
import numpy as np
import accuracy_experiment as original
try:
    import ball_gap_run as runner
except ImportError:
    runner=None


class BallGapRunner(unittest.TestCase):
    def setUp(self):self.assertIsNotNone(runner,'serialization-safe scored-engine runner absent')

    def test_live_metrics_and_saved_json_compare_identically_without_score_changes(self):
        gt=np.array([0]*20+[2]*20+[1]*20);periods=np.ones(60,dtype=np.uint8)
        metrics=original.aggregate_metrics(gt,gt,periods,gt)
        stored=json.loads(json.dumps(metrics))
        self.assertNotEqual(metrics,stored)
        self.assertEqual(runner.canonical_metrics(metrics),stored)
        self.assertEqual(runner.canonical_metrics(metrics)['metrics'],metrics['metrics'])

    def test_runner_sources_and_original_freeze_are_rechecked(self):
        from gap_solver.accuracy_protocol import hash_files
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);reports=root/'reports/ball-gap';reports.mkdir(parents=True)
            (root/'ball_gap_run.py').write_text('# synthetic wrapper')
            (reports/'comparison-freeze.json').write_text('{}')
            value=dict(source_sha256=hash_files({'ball_gap_run.py':root/'ball_gap_run.py'}),original_freeze_file_sha256=runner.sha256(reports/'comparison-freeze.json'))
            (reports/'runner-source.json').write_text(json.dumps(value))
            runner.check_runner_source(root)
            (root/'ball_gap_run.py').write_text('# mutated')
            with self.assertRaises(ValueError):runner.check_runner_source(root)

if __name__=='__main__':unittest.main()
