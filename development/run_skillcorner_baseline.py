"""Frozen-old-model independent-provider check on development only; no fitting or final-test scores."""
import json
from pathlib import Path
from datetime import datetime,timezone
import numpy as np

from gap_solver.core import infer
from gap_solver.frozen_protocol import load_frozen
from gap_solver.skillcorner import load_motion_cache
from gap_solver.tactical import infer_tactical,Policy
from gap_solver.temporal_metrics import compare_temporal,native_gap_statistics
from gap_solver.temporal_protocol import evidence_identity,require_evidence


def codes(decisions):return np.fromiter(('HADX'.index(d.label) for d in decisions),dtype=np.uint8,count=len(decisions))


def main():
    code=Path(__file__).resolve().parent;root=code.parent/'independent-reference'
    artifact,manifest=load_frozen(code.parent/'external-reference',code/'gap_solver')
    provenance=json.loads((root/'provenance.json').read_text())
    identity=evidence_identity({**{p.relative_to(code).as_posix():p for p in (code/'gap_solver').glob('*.py')},
        'run_skillcorner_baseline.py':Path(__file__)},{str(m):root/'cache'/f'{m}-detected.metadata.json' for m in provenance['split']['development']},manifest['artifact_sha256'])
    destination=root/'reports/baseline-development.json';destination.parent.mkdir(parents=True,exist_ok=True)
    if destination.exists():
        report=json.loads(destination.read_text())
        require_evidence(report,identity)
        if report['old_frozen_artifact']!=manifest['artifact_sha256']:raise ValueError('Existing baseline belongs to a different frozen model')
        if report.get('complete'):
            print('Preserved complete independent-provider baseline.',flush=True);return
    else:
        report=dict(schema_version=1,identity=identity,complete=False,started_at_utc=datetime.now(timezone.utc).isoformat(),
            old_frozen_artifact=manifest['artifact_sha256'],source_revision=provenance['source_revision'],
            match_partition='development only; unseen by old frozen model, available for new development',
            final_test_scored=False,reference_scope='known-phase H/A; annotation absence is X, never D',matches={})
    for match in provenance['split']['development']:
        if str(match) in report['matches']:continue
        data=load_motion_cache(root/'cache'/(str(match)+'-detected'));frames=data.frames()
        old=codes(infer(frames));frozen=codes(infer_tactical(frames,artifact['model'],Policy(**artifact['policy'])))
        comparison=compare_temporal(data.reference,old,frozen,data.periods,frames)
        comparison['native_observations']=native_gap_statistics(data)
        comparison['source_quality']=data.notes['phase_reconciliation']
        comparison['source_quality_gate_passed']=data.notes['phase_reconciliation']['retained_reference_fraction']>=.95
        comparison['ball_provenance_counts']={name:sum(f.ball_provenance==name for f in frames) for name in set(f.ball_provenance for f in frames)}
        report['matches'][str(match)]=comparison
        temporary=destination.with_suffix('.json.new');temporary.write_text(json.dumps(report,indent=2)+'\n');temporary.replace(destination)
        print('{} known-play spell {:.4f}->{:.4f}; X {:.2%}->{:.2%}; source retention {:.2%}'.format(match,
            comparison['baseline']['metrics']['spell_f1_mean'],comparison['selected']['metrics']['spell_f1_mean'],
            comparison['baseline']['coverage']['undecided_fraction'],comparison['selected']['coverage']['undecided_fraction'],
            comparison['source_quality']['retained_reference_fraction']),flush=True)
        del data,frames
    report['complete']=True;report['finished_at_utc']=datetime.now(timezone.utc).isoformat()
    report['summary']={name:dict(spell_f1=float(np.mean([x[name]['metrics']['spell_f1_mean'] for x in report['matches'].values()])),
        unknown_fraction=float(np.mean([x[name]['coverage']['undecided_fraction'] for x in report['matches'].values()])))
        for name in ('baseline','selected')}
    temporary=destination.with_suffix('.json.new');temporary.write_text(json.dumps(report,indent=2)+'\n');temporary.replace(destination)
    print('Completed development-only provider check; final tests unopened.',flush=True)


if __name__=='__main__':main()
