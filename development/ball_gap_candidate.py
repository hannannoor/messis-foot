"""Small pinned entry point for the experimental missing-ball-neutral candidate."""
import json
from pathlib import Path
import soft_candidate as base
from gap_solver.accuracy_protocol import digest,require_files
from ball_gap_policy import POLICY_ID

ROOT=Path(__file__).resolve().parent
EXPECTED_SELECTION_SHA='617a93ac930bdd3910af374a2faf7676298de5b7380c75b0e8062dfb62e73eca'


def selected_artifact():
    old,_=base.selected_artifact();path=ROOT/'benchmark/ball-gap/selected.json';value=json.loads(path.read_text())
    if digest(value)!=EXPECTED_SELECTION_SHA or value['base_selection_sha256']!=digest(old) or value['selected_id']!=POLICY_ID or value['weight']!=0. or value['switch_cost']!=32. or value['raw_tactical_model_sha256']!=digest(base.FROZEN_MODEL['model']):
        raise ValueError('Selected ball-gap artifact or model changed')
    require_files(value['source_sha256'],{n:ROOT/n for n in value['source_sha256']})
    require_files(value['evidence_file_sha256'],{n:ROOT/n for n in value['evidence_file_sha256']})
    return value,path


def run_source(*args,**kwargs):
    selected_artifact()
    from ball_gap_runtime import run_source as run
    return run(*args,**kwargs)


def main():
    selected_artifact()
    from ball_gap_runtime import main as run
    run()

if __name__=='__main__':main()
