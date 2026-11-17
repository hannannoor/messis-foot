import csv,json,tempfile,unittest,shutil
from pathlib import Path
from test_input_contract import fixture
try:
    from soft_candidate import run_source
except ImportError:
    run_source=None


class SoftCandidate(unittest.TestCase):
    def setUp(self):self.assertIsNotNone(run_source,'accepted experimental opt-in route missing')

    def test_reproducible_original_indices_and_latent_barrier_uncertainty(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);inputs=fixture(root)
            first=run_source(*inputs,root/'one',scope='synthetic');second=run_source(*inputs,root/'two',scope='synthetic')
            self.assertEqual(first['csv_sha256'],second['csv_sha256'])
            self.assertTrue(first['experimental']);self.assertFalse(first['target_accuracy_measured'])
            self.assertEqual(first['setting'],'w0-c32')
            self.assertEqual(first['latent_unknown_active'],3)
            self.assertEqual(first['materialized_active'],3)
            with (root/'one/submission.csv').open(newline='') as h:rows=list(csv.DictReader(h))
            self.assertEqual(rows,[{'frame':'0','label':'D'},{'frame':'1','label':'D'},{'frame':'2','label':'D'}])
            with (root/'one/uncertainty.csv').open(newline='') as h:rows=list(csv.DictReader(h))
            self.assertTrue(all(r['latent_label']=='X' and r['materialized']=='1' for r in rows))
            self.assertFalse(first['published_dead_interval_applied'])

    def test_bad_source_and_nonowned_directory_fail_before_outputs(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);inputs=fixture(root);out=root/'owned';out.mkdir();(out/'keep').write_text('keep')
            with self.assertRaises(ValueError):run_source(*inputs,out,scope='synthetic')
            self.assertEqual((out/'keep').read_text(),'keep')
            inputs[2].write_text('bad')
            with self.assertRaises(ValueError):run_source(*inputs,root/'absent',scope='synthetic')
            self.assertFalse((root/'absent').exists())

    def test_original_four_policy_generation_is_never_replaced(self):
        from gap_solver.candidate_cli import run_source as original_run
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);inputs=fixture(root);out=root/'original'
            original_run(*inputs,out,scope='synthetic')
            before={p.name:p.read_bytes() for p in out.iterdir()}
            with self.assertRaises(ValueError):run_source(*inputs,out,scope='synthetic')
            self.assertEqual({p.name:p.read_bytes() for p in out.iterdir()},before)

    def test_changed_comparator_aggregation_source_is_rejected(self):
        import soft_candidate
        real=soft_candidate.ROOT
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);artifact,_=soft_candidate.selected_artifact()
            names=[*artifact['source_sha256'],'benchmark/accuracy-first/selected.json','gap_solver/confidence_ensemble.py']
            for name in names:
                p=root/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(real/name,p)
            with (root/'gap_solver/confidence_ensemble.py').open('a') as h:h.write('\n# source changed\n')
            soft_candidate.ROOT=root
            try:
                with self.assertRaises(ValueError):soft_candidate.selected_artifact()
            finally:soft_candidate.ROOT=real

if __name__=='__main__':unittest.main()
