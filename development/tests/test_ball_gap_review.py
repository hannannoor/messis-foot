import json,tempfile,unittest,shutil
from pathlib import Path
from unittest.mock import patch
from test_input_contract import fixture
import ball_gap_candidate as cli
import soft_candidate as base
try:
    import ball_gap_post_review as audit
except ImportError:
    audit=None


class BallGapReview(unittest.TestCase):
    def test_complete_late_arrival_survives_between_last_check_and_publication(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);inputs=fixture(root);destination=root/'result';real=base.protect_soft_output;calls=0
            def late_arrival(*args):
                nonlocal calls
                real(*args);calls+=1
                if calls==2:destination.mkdir();(destination/'user.txt').write_text('late user result')
            with patch.object(base,'protect_soft_output',side_effect=late_arrival):
                with self.assertRaises((ValueError,FileExistsError)):cli.run_source(*inputs,destination,scope='synthetic')
            self.assertEqual((destination/'user.txt').read_text(),'late user result')
            self.assertEqual([p.name for p in destination.iterdir()],['user.txt'])

    def test_carry_conventions_distinguish_unknown_period_and_ordinary_dead_carry(self):
        self.assertIsNotNone(audit,'additive carry diagnostic absent')
        latent=list('XXXDXHXX');periods=[1,1,0,2,2,2,2,2];final=list('DDXDDHHH')
        counts=audit.carry_counts(latent,periods,final)
        self.assertEqual(counts,dict(wholly_latent_X_periods=1,wholly_latent_X_period_rows=2,fallback_D_rows=2,
            latent_X_carried_to_D_rows=3,latent_X_carried_to_H_rows=2,latent_X_carried_to_A_rows=0,materialized_active_rows=5))

    def test_substantive_runtime_adapter_is_pinned(self):
        value,_=cli.selected_artifact();self.assertIn('ball_gap_runtime.py',value['source_sha256'])
        real=cli.ROOT
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            for name in set(value['source_sha256'])|set(value['evidence_file_sha256'])|{'benchmark/ball-gap/selected.json'}:
                p=root/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(real/name,p)
            cli.ROOT=root
            try:
                cli.selected_artifact();p=root/'ball_gap_runtime.py';p.write_bytes(p.read_bytes()+b'\n# changed adapter\n')
                with self.assertRaises(ValueError):cli.selected_artifact()
            finally:cli.ROOT=real

    def test_runner_empty_map_design_edits_and_extra_receipts_fail_structural_check(self):
        self.assertIsNotNone(audit,'release-anchored verification absent')
        from gap_solver.accuracy_protocol import SPLITS
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);reports=root/'reports/ball-gap';reports.mkdir(parents=True)
            design=root/'docs/superpowers/specs/2026-11-07-ball-gap-evidence-design.md';design.parent.mkdir(parents=True)
            shutil.copyfile(cli.ROOT/'docs/superpowers/specs/2026-11-07-ball-gap-evidence-design.md',design)
            shutil.copyfile(cli.ROOT/'reports/ball-gap/comparison-freeze.json',reports/'comparison-freeze.json')
            seal=reports/'runner-source.json';seal.write_text(json.dumps({'source_sha256':{'ball_gap_run.py':'0'*64}}))
            for stage,groups in SPLITS.items():
                folder=reports/stage;folder.mkdir()
                for c,ids in groups.items():
                    for m in ids:
                        for regime in ('natural','masked'):(folder/f'{c}-{m}-{regime}.json').write_text('{}')
            audit.check_structure(root)
            seal.write_text(json.dumps({'source_sha256':{}}))
            with self.assertRaises(ValueError):audit.check_structure(root)
            seal.write_text(json.dumps({'source_sha256':{'ball_gap_run.py':'0'*64}}))
            before=design.read_bytes();design.write_bytes(before+b'\nchanged')
            with self.assertRaises(ValueError):audit.check_structure(root)
            design.write_bytes(before);(reports/'validation/extra.json').write_text('{}')
            with self.assertRaises(ValueError):audit.check_structure(root)

    def test_paired_deltas_are_signed_candidate_minus_current_baseline(self):
        self.assertIsNotNone(audit,'paired diagnostics absent')
        rows=[dict(stage='validation',cohort='dfl',match='synthetic',regime='natural',variants={
            'w0-c32':{'metrics':{'accuracy':.8,'macro_f1':.7,'spell_f1_mean':.6}},
            'w0-c32-neutral-missing':{'metrics':{'accuracy':.85,'macro_f1':.69,'spell_f1_mean':.61}}})]
        row=audit.paired_deltas(rows)[0]
        self.assertAlmostEqual(row['accuracy_delta'],.05);self.assertAlmostEqual(row['macro_f1_delta'],-.01);self.assertAlmostEqual(row['spell_f1_mean_delta'],.01)

if __name__=='__main__':unittest.main()
