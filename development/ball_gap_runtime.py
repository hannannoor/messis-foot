"""Experimental opt-in missing-ball-neutral H/A/D candidate; stdlib inference."""
import argparse,csv,json,tempfile,os
from collections import Counter
from dataclasses import replace
from pathlib import Path
import xml.etree.ElementTree as ET
import soft_candidate as base
from gap_solver.accuracy_protocol import digest,require_files
from gap_solver.input_contract import sha256
from ball_gap_policy import decode_ball_gap,POLICY_ID
from ball_gap_post_review import carry_counts

ROOT=Path(__file__).resolve().parent
def selected_artifact():
    from ball_gap_candidate import selected_artifact as load
    return load()


def publish_no_clobber(staging,destination):
    """Rename a sibling stage; never replace a populated generation or user file."""
    staging,destination=Path(staging),Path(destination)
    if destination.exists():
        try:destination.rmdir()  # succeeds atomically only for an empty directory
        except OSError as error:raise ValueError('Output arrived before promotion; preserving it') from error
    try:os.rename(staging,destination)  # OS refuses a populated destination
    except OSError as error:raise ValueError('Output promotion refused; existing destination preserved') from error


def run_source(meta,raw,quality,directory,scope='tactical'):
    if scope not in ('tactical','synthetic'):raise ValueError('Tactical original timeline or explicit synthetic fixtures required')
    artifact,path=selected_artifact();inputs=[meta,raw,quality,path];base.protect_soft_output(directory,inputs)
    contract=base.read_epts_contract(meta)
    if scope=='tactical' and contract.rows!=base.N_FRAMES:raise ValueError('Keep every original tactical frame')
    audit=base.audit_source(meta,raw,quality,'tactical')
    if scope=='synthetic':audit=dict(audit,scope='synthetic',active_rows=contract.rows)
    frames=list(base.iter_records(contract,raw,[(1,0,contract.rows-1)] if scope=='synthetic' else None));mask=base.quality_mask(quality,len(frames))
    frames=[f if ok else replace(f,geometry_valid=False) for f,ok in zip(frames,mask)]
    frames,association=base.associate_anonymous(frames);temporal,manifest=base.load_temporal_frozen(ROOT/'benchmark/skillcorner/frozen',ROOT)
    if manifest['artifact_sha256']!=artifact['temporal_artifact_sha256']:raise ValueError('Comparator temporal model changed')
    controls=base.predict_four(frames,temporal);tree=base.PortableTree(base.FROZEN_MODEL['model'])
    supports=[tree.predict(row) for row in base.feature_rows(frames)];periods=[f.period for f in frames]
    usable=[base.sequence_usable(f) for f in frames];observed=[f.ball_observed for f in frames]
    latent,counts=decode_ball_gap(supports,periods,usable,observed);final=base.materialize_abstentions(latent,periods)
    counts.update(carry_counts(latent,periods,final))
    active=[i for i,p in enumerate(periods) if p]
    report=dict(schema_version=1,method=artifact['method'],setting=artifact['selected_id'],experimental=True,scope=scope,
        target_accuracy_measured=False,fresh_external_validation=False,challenge_ground_truth_used=False,
        predictions_checked_against_video=False,challenge_training_or_tuning_performed=False,published_dead_interval_applied=False,
        smart_tagging_used=False,selected_motion_head_used=False,audit=audit,association=association,
        selection_sha256=digest(artifact),source_sha256=artifact['source_sha256'],evidence_file_sha256=artifact['evidence_file_sha256'],
        driver_sha256=sha256(__file__),policy_diagnostics=counts,
        latent_unknown_active=sum(latent[i]=='X' for i in active),materialized_active=sum(latent[i]!=final[i] for i in active),
        selected_labels=dict(Counter(final[i] for i in active)),controls={name:dict(Counter(values[i] for i in active)) for name,values in controls.items()},limitations=artifact['limitations'])
    destination=Path(directory);destination.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.ball-gap-candidate-',dir=destination.parent) as tmp:
        stage=Path(tmp)
        for name,values in dict(controls,submission=final).items():
            with (stage/(name+'.csv')).open('w',newline='',encoding='utf-8') as handle:
                writer=csv.writer(handle);writer.writerow(['frame','label']);writer.writerows(enumerate(values))
        with (stage/'uncertainty.csv').open('w',newline='',encoding='utf-8') as handle:
            writer=csv.writer(handle);writer.writerow(['frame','period','incumbent_label','latent_label','final_label','materialized','geometry_usable','ball_available','neutralized','unsupported_segment','freshness_verified','identity_verified'])
            for i,f in enumerate(frames):writer.writerow([i,f.period,controls['incumbent'][i],latent[i],final[i],int(latent[i]!=final[i]),int(usable[i]),int(observed[i]),int(bool(f.period and usable[i] and not observed[i])),int(bool(f.period and usable[i] and latent[i]=='X')),0,0])
        report['csv_sha256']={p.name:sha256(p) for p in sorted(stage.glob('*.csv'))}
        if audit['input_sha256']!={name:sha256(p) for name,p in zip(('metadata','tracking','homography'),inputs[:3])}:raise ValueError('Input changed during inference')
        selected_artifact()
        (stage/'candidate-report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
        base.protect_soft_output(destination,inputs);publish_no_clobber(stage,destination)
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--prefix',required=True);parser.add_argument('--out',required=True);parser.add_argument('--scope',choices=['tactical','synthetic'],default='tactical');args=parser.parse_args()
    try:report=run_source(*(args.prefix+s for s in ('_atd.xml','_atd.txt','_homography.csv')),args.out,scope=args.scope)
    except (OSError,ValueError,TypeError,KeyError,ET.ParseError) as error:parser.error(str(error))
    print(json.dumps({k:report[k] for k in ('setting','experimental','target_accuracy_measured','policy_diagnostics','latent_unknown_active','materialized_active','csv_sha256')},indent=2))

if __name__=='__main__':main()
