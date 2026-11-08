"""Isolated standard-library probe against the generated bundle; synthetic input only."""
import importlib.util,json,sys
from pathlib import Path


def main():
    root=Path(__file__).resolve().parent
    spec=importlib.util.spec_from_file_location('portable_bundle',root/'football_pipeline.py')
    bundle=importlib.util.module_from_spec(spec);spec.loader.exec_module(bundle)
    sys.meta_path.insert(0,bundle._BundledModules())
    from gap_solver.motion import MotionFrame
    from gap_solver.core import Decision
    from gap_solver.temporal import infer_temporal,mask_motion_frames,PortableBoosted,MOTION_FEATURES,swap_feature_row
    draft=json.loads((root.parent/'independent-reference/temporal/trained-draft.json').read_text())
    artifact=dict(model=draft['model'],transition_cost=draft['transition_cost'],temperature=draft['temperatures']['1.0'],
        policy=dict(confidence=.95,max_gap_s=5.,minimum_players=3,switch_multiplier=1.))
    frames=[MotionFrame(ball_x=20.,ball_y=20.,home_distance=.5,away_distance=60.,
        home_xy=((20.,20.),(21.,21.),(22.,22.)),away_xy=((80.,20.),(81.,21.),(82.,22.)),home_ids=(1,2,3),away_ids=(4,5,6)) for _ in range(80)]
    frames=mask_motion_frames(frames,[16<=i<41 for i in range(80)])
    base=[Decision('X' if 16<=i<41 else 'H') for i in range(80)]
    result=infer_temporal(frames,artifact,base)
    assert len(result)==80 and all(a==b for a,b in zip(result,base) if b.label!='X')
    tree=PortableBoosted(draft['model']);row=[.25]*len(MOTION_FEATURES)
    assert abs(tree.symmetric_score(row)+tree.symmetric_score(swap_feature_row(row)))<1e-12
    assert not any(name in sys.modules for name in ('numpy','sklearn','pandas','scipy'))
    print('Bundled motion/40-tree/decoder inference passed on80 synthetic rows with Python '+sys.version.split()[0]+'; no third-party runtime modules.')


if __name__=='__main__':main()
