"""Local frozen-model tactical route; no video, challenge GT, fitting or camera synchronization."""
import argparse
from collections import Counter
import csv
from dataclasses import replace
import json
from math import isfinite
from pathlib import Path
import tempfile
import xml.etree.ElementTree as ET

from .audit import bridge_diagnostics,compare_decisions
from .automatic_sync import publish_outputs
from .core import Config,infer,summary,unresolved_intervals
from .frozen_protocol import artifact_digest
from .io import _bool,_number,load_atd,load_tags,read_evidence,write_outputs
from .multicam import resolve_source_prefix
from .tactical import FEATURE_NAMES,Policy,PortableTree,feature_rows,infer_tactical


OUTPUT_FILES={'submission.csv','diagnostics.csv','report.json','unresolved_intervals.json','tactical_report.json'}
METHOD='frozen_external_tactical_v1'


def protect_output(directory,inputs):
    directory=Path(directory)
    for name in OUTPUT_FILES:
        target=directory/name
        for source in map(Path,inputs):
            if target.resolve()==source.resolve() or target.exists() and source.exists() and target.samefile(source):
                raise ValueError('Tactical output must not replace an input or an alias of it')
    if directory.is_symlink():
        raise ValueError('Tactical output requires a dedicated directory, not a link')
    if directory.exists():
        if not directory.is_dir():
            raise ValueError('Tactical output must be a directory')
        if any(directory.iterdir()):
            try:
                report=json.loads((directory/'tactical_report.json').read_text(encoding='utf-8'))
                owned=report.get('method')==METHOD and all(p.name in OUTPUT_FILES and p.is_file() and not p.is_symlink()
                                                         for p in directory.iterdir())
            except (OSError,ValueError,AttributeError):
                owned=False
            if not owned:
                raise ValueError('Nonempty output is not owned by this tactical route; use a dedicated folder')


def apply_geometry_quality(frames,path,max_reprojection_error=3.):
    valid=[]
    with open(path,newline='',encoding='utf-8-sig') as handle:
        for i,row in enumerate(csv.DictReader(handle)):
            if int(row['frame'])!=i or i>=len(frames):
                raise ValueError('Tactical homography indices disagree with original tracking')
            matrix=[_number(row['h'+str(a)+str(b)]) for a in range(3) for b in range(3)]
            accepted=row['valid'].strip()=='1' and all(v is not None for v in matrix)
            if accepted:
                a,b,c,d,e,f,g,h,j=matrix
                determinant=a*(e*j-f*h)-b*(d*j-f*g)+c*(d*h-e*g)
                scale=max(abs(v) for v in matrix)
                accepted=scale>0 and abs(determinant)>1e-12*scale**3
            error=_number(row['reprojection_error'])
            valid.append(accepted and error is not None and 0<=error<=max_reprojection_error)
    if len(valid)!=len(frames):
        raise ValueError('Tactical homography row count differs from original tracking')
    return ([f if usable else replace(f,ball_x=None,ball_y=None,home_distance=None,away_distance=None)
             for f,usable in zip(frames,valid)],valid)


def load_model(path=None):
    if path:
        artifact=json.loads(Path(path).read_text(encoding='utf-8'))
        externally_validated=False
        identifier=artifact_digest(artifact)
    else:
        from .tactical_model import FROZEN_MODEL
        artifact=FROZEN_MODEL
        externally_validated=artifact.get('externally_heldout_validated') is True
        identifier=artifact['artifact_sha256']
        actual=artifact_digest(dict(model=artifact['model'],policy=artifact['policy']))
        if actual!=artifact.get('model_policy_sha256') or not externally_validated:
            raise ValueError('Embedded model is not the verified externally frozen policy')
    if artifact.get('schema_version')!=1:
        raise ValueError('Unsupported tactical model schema')
    PortableTree(artifact['model']);Policy(**artifact['policy']).validate()
    return artifact,identifier,externally_validated


def load_geometry_evidence(path):
    with open(path,newline='',encoding='utf-8-sig') as handle:
        for row in csv.DictReader(handle):
            if _bool(row.get('dead_evidence')) or str(row.get('dead_source') or '').strip():
                raise ValueError('Geometry-only tactical evidence cannot contain dead_evidence/dead_source labels')
    tagged=read_evidence(path)
    geometry=[replace(f,tag_team='',restart_hint=False) for f in tagged]
    return tagged,geometry


def unresolved_explanations(frames,decisions,quality,artifact):
    tree=PortableTree(artifact['model']);policy=Policy(**artifact['policy'])
    counts=Counter()
    for f,d,usable,row in zip(frames,decisions,quality,feature_rows(frames)):
        if not f.period or d.label!='X':
            continue
        probabilities=tree.predict(row)
        winner=max(range(3),key=lambda k:probabilities[k])
        if not usable:
            reason='homography_quality_rejected'
        elif not f.ball_observed and (not (row[15] or row[16]) or row[17]>policy.max_gap_s):
            reason='missing_ball_without_recent_confirmed_owner'
        elif not f.ball_observed and winner==2:
            reason='missing_ball_cannot_confirm_dead'
        elif f.ball_observed and (not row[1] or not row[2]):
            reason='incomplete_team_geometry'
        elif probabilities[winner]<policy.confidence:
            reason='model_leaf_support_below_gate'
        else:
            reason='insufficient_stable_run_or_conflicting_interval'
        counts[reason]+=1
    return dict(counts)


def run(frames,tagged,quality,artifact,identifier,externally_validated,directory,inputs,source_kind):
    destination=Path(directory)
    protect_output(destination,inputs)
    policy=Policy(**artifact['policy'])
    tagged_before=infer(tagged)
    quality_before=infer(frames)
    print('Running frozen tactical model on {} original frames...'.format(len(frames)),flush=True)
    decisions=infer_tactical(frames,artifact['model'],policy)
    before=summary(tagged,tagged_before);after=summary(frames,decisions)
    model_input=summary(frames,quality_before)
    report=dict(schema_version=1,method=METHOD,source_kind=source_kind,model_id=identifier,
                model_externally_validated=externally_validated,model_reference_type=artifact.get('reference_type','custom model; unverified'),
                model_policy=artifact['policy'],leaf_support_is_calibrated_probability=False,
                selected_features=list(FEATURE_NAMES),smart_tagging_used_for_selected_inference=False,
                before=before,baseline_on_model_inputs=model_input,after=after,
                unresolved_intervals_before=len(unresolved_intervals(tagged,tagged_before)),
                unresolved_intervals_after=len(unresolved_intervals(frames,decisions)),
                reference_free_changes=compare_decisions(frames,tagged_before,decisions),
                reference_free_changes_on_identical_inputs=compare_decisions(frames,quality_before,decisions),
                remaining_gap_diagnostics=bridge_diagnostics(frames,decisions),
                unresolved_reasons=unresolved_explanations(frames,decisions,quality,artifact),
                quality=dict(original_frames=len(frames),unusable_homography_frames=sum(not v for v in quality),
                             unusable_graded_homography_frames=sum(f.period!=0 and not q for f,q in zip(frames,quality)),
                             maximum_reprojection_error=3.),
                undecided_relative_reduction=1-after['labels']['X']/before['labels']['X'] if before['labels']['X'] else None,
                accuracy_measured=False,challenge_ground_truth_used=False,predictions_checked_against_video=False,
                challenge_training_or_tuning_performed=False,published_dead_interval_applied=False,
                live_dead_classifier_included=True,replay_detector_included=False,
                warning='Challenge coverage/behavior only. External provider-reference validation does not establish challenge correctness.')
    if externally_validated:
        report['external_heldout_summary']=artifact.get('heldout_summary')
        report['external_attribution']=artifact.get('citation')
        report['external_license']=artifact.get('license')
        report['external_validation_limitations']=artifact.get('validation_limitations',[])
    destination.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.tactical-result-',dir=destination.parent) as staging:
        stage=Path(staging)
        output=write_outputs(stage,frames,decisions,audit_stages={'legacy_tagged_no_fixed_D':tagged_before,
                                                               'geometry_on_model_inputs':quality_before})
        output.update(live_dead_classifier_included=True,external_model_id=identifier,method=METHOD)
        (stage/'report.json').write_text(json.dumps(output,indent=2)+'\n',encoding='utf-8')
        (stage/'tactical_report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
        protect_output(destination,inputs)
        publish_outputs(stage,destination)
    print('Undecided graded frames: {} -> {}'.format(before['labels']['X'],after['labels']['X']),flush=True)
    print('Resolved coverage: {:.2%} -> {:.2%}'.format(before['resolved_fraction'],after['resolved_fraction']),flush=True)
    print('No challenge accuracy measured. Output: '+str(destination.resolve()),flush=True)
    return report


def main():
    parser=argparse.ArgumentParser(description='Frozen externally validated tactical possession model; local inference only')
    sub=parser.add_subparsers(dest='command',required=True)
    for name in ('run','evidence'):
        command=sub.add_parser(name)
        command.add_argument('--model',help='optional custom JSON artifact; reported as unverified')
        command.add_argument('--out',default='outputs/tactical-validated')
        if name=='run':
            command.add_argument('--data-dir',required=True)
            command.add_argument('--tactical-dir')
        else:
            command.add_argument('--input',required=True,help='automatic evidence CSV for development; original indices required')
    args=parser.parse_args()
    try:
        artifact,identifier,validated=load_model(args.model)
        inputs=[args.model] if args.model else []
        if args.command=='evidence':
            inputs.append(args.input)
            protect_output(args.out,inputs)
            tagged,frames=load_geometry_evidence(args.input)
            quality=[True]*len(frames)
        else:
            prefix=str(resolve_source_prefix(args.data_dir,'tactical',args.tactical_dir))
            inputs.extend(prefix+suffix for suffix in ('_atd.xml','_atd.txt','_homography.csv'))
            protect_output(args.out,inputs)
            raw,teams=load_atd(prefix+'_atd.xml',prefix+'_atd.txt')
            tagging=Path(prefix+'_smart_tagging.xml')
            tagged=load_tags(tagging,raw,teams) if tagging.exists() else raw
            frames,quality=apply_geometry_quality(raw,prefix+'_homography.csv')
        run(frames,tagged,quality,artifact,identifier,validated,args.out,inputs,args.command)
    except (OSError,ValueError,TypeError,KeyError,ET.ParseError) as error:
        parser.error(str(error))


if __name__=='__main__':
    main()
