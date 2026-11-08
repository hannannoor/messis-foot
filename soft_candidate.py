"""Opt-in experimental H/A/D sequence candidate; standard-library local inference."""
import argparse,csv,json,tempfile
from collections import Counter
from dataclasses import replace
from pathlib import Path
import xml.etree.ElementTree as ET
from gap_solver.accuracy_protocol import digest,hash_files,require_files
from gap_solver.anonymous_motion import associate_anonymous
from gap_solver.automatic_sync import publish_outputs
from gap_solver.candidate_cli import protect_output,predict_four
from gap_solver.input_contract import audit_source,read_epts_contract,iter_records,quality_mask,sha256
from gap_solver.io import N_FRAMES
from gap_solver.materialization_control import materialize_abstentions
from gap_solver.soft_sequence import soft_emissions,decode_soft,sequence_usable
from gap_solver.tactical import PortableTree,feature_rows
from gap_solver.tactical_model import FROZEN_MODEL
from gap_solver.temporal import PortableBoosted,motion_feature_rows
from gap_solver.temporal_protocol import load_temporal_frozen

ROOT=Path(__file__).resolve().parent
EXPECTED_SELECTION_SHA='ace59b6345fb6dbf36aeebd1ac737faa0acafd7a19abb59c5fbaf22079e03dbc'


def selected_artifact():
    path=ROOT/'benchmark/accuracy-first/selected.json';value=json.loads(path.read_text())
    if digest(value)!=EXPECTED_SELECTION_SHA or value['raw_tactical_model_sha256']!=digest(FROZEN_MODEL['model']):raise ValueError('Selected model/setting artifact changed')
    require_files(value['source_sha256'],{name:ROOT/name for name in value['source_sha256']})
    return value,path


def protect_soft_output(directory,inputs):
    protect_output(directory,inputs)
    path=Path(directory)
    if path.exists() and any(path.iterdir()):raise ValueError('Soft candidate requires a fresh or empty dedicated output directory')


def run_source(meta,raw,quality,directory,scope='tactical'):
    if scope not in ('tactical','synthetic'):raise ValueError('Tactical original timeline or explicit synthetic fixtures required')
    artifact,path=selected_artifact();inputs=[meta,raw,quality,path];protect_soft_output(directory,inputs)
    contract=read_epts_contract(meta)
    if scope=='tactical' and contract.rows!=N_FRAMES:raise ValueError('Keep every original tactical frame')
    audit=audit_source(meta,raw,quality,'tactical')
    if scope=='synthetic':audit=dict(audit,scope='synthetic',active_rows=contract.rows)
    frames=list(iter_records(contract,raw,[(1,0,contract.rows-1)] if scope=='synthetic' else None));mask=quality_mask(quality,len(frames))
    frames=[f if ok else replace(f,geometry_valid=False) for f,ok in zip(frames,mask)]
    frames,association=associate_anonymous(frames);temporal,manifest=load_temporal_frozen(ROOT/'benchmark/skillcorner/frozen',ROOT)
    if manifest['artifact_sha256']!=artifact['temporal_artifact_sha256']:raise ValueError('Comparator temporal model changed after experiment freeze')
    controls=predict_four(frames,temporal)
    tree=PortableTree(FROZEN_MODEL['model']);supports=[tree.predict(row) for row in feature_rows(frames)]
    scores=[0.]*len(frames)
    if artifact['weight']:
        boost=PortableBoosted(temporal['model']);scores=[boost.symmetric_score(row) for row in motion_feature_rows(frames)]
    periods=[f.period for f in frames];latent=decode_soft(soft_emissions(supports,scores,artifact['weight']),periods,[sequence_usable(f) for f in frames],artifact['switch_cost'])
    final=materialize_abstentions(latent,periods);active=[i for i,p in enumerate(periods) if p]
    report=dict(schema_version=1,method=artifact['method'],setting=artifact['selected_id'],experimental=True,scope=scope,
        target_accuracy_measured=False,fresh_external_validation=False,challenge_ground_truth_used=False,
        predictions_checked_against_video=False,challenge_training_or_tuning_performed=False,published_dead_interval_applied=False,
        smart_tagging_used=False,selected_motion_head_used=bool(artifact['weight']),audit=audit,association=association,
        selection_sha256=digest(artifact),source_sha256=artifact['source_sha256'],evidence=artifact['evidence'],
        driver_sha256=sha256(__file__),
        latent_unknown_active=sum(latent[i]=='X' for i in active),materialized_active=sum(latent[i]!=final[i] for i in active),
        selected_labels=dict(Counter(final[i] for i in active)),controls={name:dict(Counter(values[i] for i in active)) for name,values in controls.items()},limitations=artifact['limitations'])
    destination=Path(directory);destination.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.soft-candidate-',dir=destination.parent) as tmp:
        stage=Path(tmp)
        for name,values in dict(controls,submission=final).items():
            with (stage/(name+'.csv')).open('w',newline='',encoding='utf-8') as h:
                w=csv.writer(h);w.writerow(['frame','label']);w.writerows(enumerate(values))
        with (stage/'uncertainty.csv').open('w',newline='',encoding='utf-8') as h:
            w=csv.writer(h);w.writerow(['frame','period','incumbent_label','latent_label','final_label','materialized','geometry_usable','freshness_verified','identity_verified'])
            for i,f in enumerate(frames):w.writerow([i,f.period,controls['incumbent'][i],latent[i],final[i],int(latent[i]!=final[i]),int(sequence_usable(f)),0,0])
        report['csv_sha256']={p.name:sha256(p) for p in sorted(stage.glob('*.csv'))}
        if audit['input_sha256']!={name:sha256(p) for name,p in zip(('metadata','tracking','homography'),inputs[:3])}:raise ValueError('Input changed during inference')
        selected_artifact()
        (stage/'candidate-report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
        protect_soft_output(destination,inputs);publish_outputs(stage,destination)
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--prefix',required=True);p.add_argument('--out',required=True);p.add_argument('--scope',choices=['tactical','synthetic'],default='tactical');a=p.parse_args()
    try:r=run_source(*(a.prefix+s for s in ('_atd.xml','_atd.txt','_homography.csv')),a.out,scope=a.scope)
    except (OSError,ValueError,TypeError,KeyError,ET.ParseError) as error:p.error(str(error))
    print(json.dumps({k:r[k] for k in ('setting','experimental','target_accuracy_measured','latent_unknown_active','materialized_active','csv_sha256')},indent=2))

if __name__=='__main__':main()
