"""Missing carry control from the neutral audit; post-hoc external diagnostic only."""
import argparse,json
from pathlib import Path
import numpy as np
from ablate_ensemble import CODE,ROOT,DESTINATION as ENSEMBLES,identity as ensemble_identity,check_receipt
from evaluate_temporal_final import frozen
from select_temporal_recovery import sha,write_json
from gap_solver.materialization_control import materialize_abstentions
from gap_solver.temporal_metrics import score_temporal
from gap_solver.temporal_protocol import require_evidence

DESTINATION=ROOT/'materialization-controls-v2'


def identity(report,prediction_path,reference_path,receipt_path,source_variant):
    return dict(ensemble_identity=report['identity'],ensemble_receipt_sha256=sha(receipt_path),
        source_variant=source_variant,
        prediction_sha256=sha(prediction_path),reference_sha256=sha(reference_path),
        source_sha256={'driver':sha(Path(__file__)),'rule':sha(CODE/'gap_solver/materialization_control.py')})


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',choices=['baseline','head_agreement_on_X'],default='baseline');args=parser.parse_args()
    _,manifest=frozen();records=[]
    paths=[p for p in ENSEMBLES.glob('*.json') if p.name!='summary.json']
    expected={'skillcorner':set(manifest['split']['test']),'dfl':set(sum(json.loads((CODE.parent/'external-reference/provenance.json').read_text())['split'].values(),[]))}
    if len(paths)!=sum(map(len,expected.values())):raise ValueError('Missing source ensemble receipts')
    for path in sorted(paths):
        source=json.loads(path.read_text());cohort=source['cohort'];match=source['match'];predictions=path.with_suffix('.npz')
        check_receipt(source,ensemble_identity(cohort,match,manifest['artifact_sha256']),predictions)
        reference=(ROOT/'cache'/f'{match}-detected.reference.npz') if cohort=='skillcorner' else CODE.parent/'external-reference/cache'/f'{match}.reference.npz'
        ident=identity(source,predictions,reference,path,args.source);destination=DESTINATION/(path.stem+'-'+args.source+'.json')
        if destination.exists():
            record=json.loads(destination.read_text());require_evidence(record,ident)
        else:
            with np.load(predictions,allow_pickle=False) as arrays:old=arrays[args.source];original=arrays['baseline']
            with np.load(reference,allow_pickle=False) as arrays:gt=arrays['reference'];periods=arrays['periods']
            new=np.asarray(['HADX'.index(v) for v in materialize_abstentions(['HADX'[int(v)] for v in old],periods)],dtype=np.uint8)
            record=dict(identity=ident,cohort=cohort,match=match,source_variant=args.source,post_hoc=True,fresh_holdout=False,
                baseline=score_temporal(gt,old,periods),materialized=score_temporal(gt,new,periods),
                original_baseline=score_temporal(gt,original,periods),
                new_by_reference_label={label:int(((old==3)&(new<3)&(gt==code)).sum()) for code,label in enumerate('HADX')},
                total_new_outside_reference=int(((original==3)&(new<3)&(gt==3)).sum()),
                warning='Uses structural periods only. Unknown reference gaps may change temporal equivalence; no new evidence or local inference.')
            write_json(destination,record)
        records.append(record)
    for cohort,ids in expected.items():
        if {r['match'] for r in records if r['cohort']==cohort}!=ids:raise ValueError('Unexpected materialization cohort')
    result=dict(schema_version=1,source_variant=args.source,post_hoc=True,fresh_holdout=False,local_inference_performed=False,cohorts={})
    for cohort in expected:
        rows=[r for r in records if r['cohort']==cohort]
        result['cohorts'][cohort]=dict(matches=len(rows),source_spell_f1=float(np.mean([r['baseline']['metrics']['spell_f1_mean'] for r in rows])),
            original_baseline_spell_f1=float(np.mean([r['original_baseline']['metrics']['spell_f1_mean'] for r in rows])),
            materialized_spell_f1=float(np.mean([r['materialized']['metrics']['spell_f1_mean'] for r in rows])),
            materialized_accuracy=float(np.mean([r['materialized']['metrics']['accuracy'] for r in rows])),
            materialized_unknown_fraction=float(np.mean([r['materialized']['coverage']['undecided_fraction'] for r in rows])),
            equal_spell_matches=sum(r['baseline']['metrics']['spell_f1_mean']==r['materialized']['metrics']['spell_f1_mean'] for r in rows),
            added_outside_reference=sum(r['new_by_reference_label']['X'] for r in rows),
            total_new_outside_reference=sum(r['total_new_outside_reference'] for r in rows))
    write_json(DESTINATION/('summary-'+args.source+'.json'),result);print(json.dumps(result,indent=2),flush=True)


if __name__=='__main__':main()
