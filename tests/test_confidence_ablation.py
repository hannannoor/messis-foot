import unittest
from gap_solver.core import Decision
from gap_solver.temporal import mask_motion_frames
from test_temporal import motion_fixture
try:
    from ablate_confidence import temporal_variants,raw_tree_decisions
except ImportError:
    temporal_variants=raw_tree_decisions=None


class ConfidenceAblation(unittest.TestCase):
    def test_consumed_case_and_source_array_changes_invalidate_reuse_and_summary(self):
        import tempfile,json
        from pathlib import Path
        from unittest.mock import patch
        import ablate_confidence as ablation
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);code=root/'code';data=root/'independent';work=data/'temporal';out=data/'ablation'
            (code/'gap_solver').mkdir(parents=True);(data/'cache').mkdir(parents=True);(work/'cases').mkdir(parents=True)
            (work/'frozen').mkdir();out.mkdir();(root/'external-reference').mkdir()
            (root/'external-reference/provenance.json').write_text(json.dumps({'split':{'development':[],'validation':[],'test':[]}}))
            for path in (ablation.CODE/'gap_solver').glob('*.py'):(code/'gap_solver'/path.name).write_text('')
            (work/'frozen/temporal-selected.json').write_text('{}')
            targets=[data/'cache/7-detected.metadata.json',data/'cache/7-detected.features.npz',data/'cache/7-detected.reference.npz',
                work/'cases/7-detected.json',work/'cases/7-detected-natural.npz']
            for path in targets:path.write_bytes(b'original')
            with patch.object(ablation,'CODE',code),patch.object(ablation,'ROOT',data),patch.object(ablation,'WORK',work),patch.object(ablation,'DESTINATION',out),patch.object(ablation,'frozen',return_value=({},dict(artifact_sha256='artifact',split={'test':[7]}))):
                identity=ablation.source_identity('skillcorner',7,'artifact')
                (out/'skillcorner-7.json').write_text(json.dumps(dict(identity=identity,cohort='skillcorner',match=7)))
                for path in targets[1:]:
                    path.write_bytes(b'changed')
                    with self.subTest(file=path.name,stage='reuse'),self.assertRaises(ValueError):ablation.run_one('skillcorner',7)
                    with self.subTest(file=path.name,stage='summary'),self.assertRaises(ValueError):ablation.summarize()
                    path.write_bytes(b'original')

    def test_raw_three_class_head_can_select_dead_and_keeps_structural_unknown(self):
        self.assertIsNotNone(raw_tree_decisions)
        from dataclasses import replace
        from gap_solver.tactical import FEATURE_NAMES
        model=dict(feature_names=list(FEATURE_NAMES),children_left=[-1],children_right=[-1],
            feature=[-2],threshold=[0.],probabilities=[[0.,.2,.8]])
        frames=motion_fixture(2);frames[0]=replace(frames[0],period=0)
        self.assertEqual([d.label for d in raw_tree_decisions(frames,model)],['X','D'])

    def test_confidence_off_keeps_support_guards_but_direct_mode_fills_unknown(self):
        self.assertIsNotNone(temporal_variants)
        frames=mask_motion_frames(motion_fixture(),[16<=i<41 for i in range(80)])
        base=[Decision('X' if 16<=i<41 else 'H') for i in range(80)]
        policy=dict(confidence=.975,max_gap_s=2.,minimum_players=3,switch_multiplier=.5)
        off,direct=temporal_variants(frames,base,[.001]*80,policy)
        self.assertTrue(all(d.label=='A' for d in off[16:41]))
        missing=mask_motion_frames(frames,[True]*80)
        off,direct=temporal_variants(missing,base,[0.]*80,policy)
        self.assertTrue(all(d.label=='X' for d in off[16:41]))
        self.assertTrue(all(d.label=='H' for d in direct[16:41]))

    def test_structural_unknown_and_existing_decisions_are_preserved(self):
        self.assertIsNotNone(temporal_variants)
        from dataclasses import replace
        frames=motion_fixture(4);frames[0]=replace(frames[0],period=0)
        base=[Decision('X'),Decision('D'),Decision('A'),Decision('X')]
        off,direct=temporal_variants(frames,base,[1.]*4,dict(confidence=.975,max_gap_s=2.))
        self.assertEqual([d.label for d in direct],['X','D','A','A'])
