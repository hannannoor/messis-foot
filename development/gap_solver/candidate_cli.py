"""Experimental four-policy tactical candidate with explicit uncertainty."""
import argparse
from collections import Counter
import csv
from dataclasses import replace
import json
from pathlib import Path
import tempfile
import xml.etree.ElementTree as ET

from .anonymous_motion import associate_anonymous
from .automatic_sync import publish_outputs
from .confidence_ensemble import aggregate_decisions
from .core import Decision
from .input_contract import audit_source,read_epts_contract,iter_records,quality_mask,sha256,reject_linked_ancestors
from .io import N_FRAMES
from .materialization_control import materialize_abstentions
from .tactical import infer_tactical,Policy,PortableTree,feature_rows
from .tactical_model import FROZEN_MODEL
from .temporal import PortableBoosted,motion_feature_rows,decode_team_sequence
from .temporal_protocol import load_temporal_frozen

ROOT=Path(__file__).resolve().parents[1]
POLICIES=('incumbent','carry','agreement','agreement-plus-carry')
METHOD='experimental_channel_contract_anonymous_agreement_v2'
OUTPUT_FILES={name+'.csv' for name in POLICIES}|{'submission.csv','uncertainty.csv','candidate-report.json'}


def protect_output(directory,inputs):
    directory=Path(directory)
    # Also reject junction/reparse aliases in ancestors, including nonexistent leaves.
    reject_linked_ancestors(directory)
    for name in OUTPUT_FILES:
        target=directory/name
        if target.is_symlink():raise ValueError('Linked output file')
        for source in map(Path,inputs):
            if target.resolve()==source.resolve() or target.exists() and source.exists() and target.samefile(source):
                raise ValueError('Output must not replace an input alias')
    if directory.exists():
        if not directory.is_dir():raise ValueError('Output must be a directory')
        if any(directory.iterdir()):
            try:
                report=json.loads((directory/'candidate-report.json').read_text(encoding='utf-8'))
                owned=report.get('method')==METHOD and all(p.name in OUTPUT_FILES and p.is_file() and not p.is_symlink() for p in directory.iterdir())
            except (OSError,ValueError,AttributeError):owned=False
            if not owned:raise ValueError('Output directory is not owned by this experimental command')


def predict_four(frames,artifact):
    if any(f.dead_evidence or f.tag_team or f.restart_hint for f in frames):raise ValueError('Candidate requires geometry-only inputs')
    baseline=infer_tactical(frames,FROZEN_MODEL['model'],Policy(**FROZEN_MODEL['policy']))
    tree=PortableBoosted(artifact['model'])
    scores=[tree.symmetric_score(row) if d.label=='X' and f.period and f.geometry_valid else 0.
            for f,d,row in zip(frames,baseline,motion_feature_rows(frames))]
    posterior=decode_team_sequence(scores,frames,baseline,artifact['transition_cost']*artifact['policy']['switch_multiplier'])
    temporal=[Decision('A' if z>0 else 'H','diagnostic_argmax','unsupported_estimate') if f.period and f.geometry_valid and b.label=='X' else b for f,b,z in zip(frames,baseline,posterior)]
    raw_tree=PortableTree(FROZEN_MODEL['model']);raw=[]
    for f,row in zip(frames,feature_rows(frames)):
        p=raw_tree.predict(row)
        raw.append(Decision('HAD'[max(range(3),key=lambda k:p[k])]) if f.period else Decision())
    agreement=aggregate_decisions(frames,baseline,temporal,raw,temporal)['head_agreement_on_X']
    baseline=[d.label for d in baseline];agreement=[d.label for d in agreement];periods=[f.period for f in frames]
    return {'incumbent':baseline,'carry':materialize_abstentions(baseline,periods),'agreement':agreement,
        'agreement-plus-carry':materialize_abstentions(agreement,periods)}


def run_source(meta,raw,quality,directory,scope='tactical'):
    if scope not in ('tactical','synthetic'):raise ValueError('Candidate supports tactical source or explicitly synthetic fixtures only; broadcast is unaligned')
    inputs=[meta,raw,quality];protect_output(directory,inputs)
    contract=read_epts_contract(meta)
    if scope=='tactical' and contract.rows!=N_FRAMES:raise ValueError('Tactical source must retain all original frames')
    audit=audit_source(meta,raw,quality,'tactical')
    blocks=[(1,0,contract.rows-1)] if scope=='synthetic' else None
    frames=list(iter_records(contract,raw,blocks));mask=quality_mask(quality,len(frames))
    frames=[f if ok else replace(f,geometry_valid=False) for f,ok in zip(frames,mask)]
    frames,association=associate_anonymous(frames)
    artifact,manifest=load_temporal_frozen(ROOT/'benchmark/skillcorner/frozen',ROOT)
    predictions=predict_four(frames,artifact);active=[i for i,f in enumerate(frames) if f.period]
    report=dict(schema_version=1,method=METHOD,scope=scope,experimental=True,selected='agreement-plus-carry',
        accuracy_measured=False,fresh_external_validation=False,challenge_ground_truth_used=False,predictions_checked_against_video=False,
        challenge_training_or_tuning_performed=False,published_dead_interval_applied=False,smart_tagging_used=False,
        audit=audit,association=association,temporal_artifact_sha256=manifest['artifact_sha256'],
        temporal_original_eligibility=artifact['eligibility'],tactical_artifact_sha256=FROZEN_MODEL['artifact_sha256'],
        source_sha256={p.relative_to(ROOT).as_posix():sha256(p) for p in sorted((ROOT/'gap_solver').glob('*.py'))},
        policies={name:dict(active_labels=dict(Counter(values[i] for i in active)),active_rows=len(active),
            abstentions=sum(values[i]=='X' for i in active),materialized=sum(values[i]!=predictions['incumbent' if name=='carry' else 'agreement'][i] for i in active) if name in ('carry','agreement-plus-carry') else 0)
            for name,values in predictions.items()},
        warning='Experimental anonymous correspondence differs from model training identities. Agreement and carry do not establish correctness; carried D is not dead-ball evidence.')
    destination=Path(directory);destination.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.candidate-',dir=destination.parent) as tmp:
        stage=Path(tmp)
        for name,values in dict(predictions,submission=predictions['agreement-plus-carry']).items():
            with (stage/(name+'.csv')).open('w',newline='',encoding='utf-8') as h:
                w=csv.writer(h);w.writerow(['frame','label']);w.writerows(enumerate(values))
        with (stage/'uncertainty.csv').open('w',newline='',encoding='utf-8') as h:
            w=csv.writer(h);w.writerow(['frame','period','incumbent_label','latent_label','final_label','materialized','geometry_valid','freshness_verified','identity_verified'])
            for i,f in enumerate(frames):
                latent=predictions['agreement'][i];final=predictions['agreement-plus-carry'][i]
                w.writerow([i,f.period,predictions['incumbent'][i],latent,final,int(latent!=final),int(f.geometry_valid),0,0])
        report['csv_sha256']={p.name:sha256(p) for p in sorted(stage.glob('*.csv'))}
        if audit['input_sha256']!={n:sha256(p) for n,p in zip(('metadata','tracking','homography'),inputs)}:raise ValueError('Input changed during run')
        (stage/'candidate-report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
        protect_output(destination,inputs);publish_outputs(stage,destination)
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--prefix',required=True);p.add_argument('--out',required=True)
    p.add_argument('--scope',choices=['tactical','synthetic'],default='tactical');a=p.parse_args()
    try:
        result=run_source(*(a.prefix+s for s in ('_atd.xml','_atd.txt','_homography.csv')),a.out,scope=a.scope)
    except (OSError,ValueError,TypeError,KeyError,ET.ParseError) as error:p.error(str(error))
    print(json.dumps({k:result[k] for k in ('experimental','accuracy_measured','policies','csv_sha256')},indent=2))

if __name__=='__main__':main()
