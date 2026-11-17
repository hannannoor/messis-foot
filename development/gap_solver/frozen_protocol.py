"""Integrity and split checks before final external evaluation; no model fitting."""
import hashlib
import json
from pathlib import Path
from .tactical import Policy,PortableTree


def artifact_digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode('utf-8')).hexdigest()


def load_frozen(root,code_directory):
    root,code_directory=Path(root),Path(code_directory)
    artifact=json.loads((root/'frozen'/'tactical-selected.json').read_text(encoding='utf-8'))
    manifest=json.loads((root/'frozen'/'freeze-manifest.json').read_text(encoding='utf-8'))
    provenance=json.loads((root/'provenance.json').read_text(encoding='utf-8'))
    if (artifact.get('schema_version')!=1 or not artifact.get('features_exclude_reference_labels')
            or manifest.get('frozen_before_test_scores') is not True
            or artifact_digest(artifact)!=manifest.get('artifact_sha256')):
        raise ValueError('Frozen model/policy integrity failed')
    split=manifest.get('split',{})
    if set(split)!={'development','validation','test'} or split!=provenance.get('split'):
        raise ValueError('Frozen external split differs from acquisition protocol')
    all_ids=[]
    for name,field in [('development','training_matches'),('validation','validation_matches'),('test','test_matches')]:
        ids=split[name]
        if not isinstance(ids,list) or not ids or any(not isinstance(x,str) or not x for x in ids) or artifact.get(field)!=ids:
            raise ValueError('Invalid/changed external match partition')
        all_ids.extend(ids)
    if len(all_ids)!=len(set(all_ids)):
        raise ValueError('External train/validation/test partitions overlap')
    sources=manifest.get('source_sha256',{})
    if not sources:
        raise ValueError('Frozen prediction/evaluation sources are missing')
    for name,expected in sources.items():
        if Path(name).name!=name or not name.endswith('.py'):
            raise ValueError('Invalid frozen source name')
        if hashlib.sha256((code_directory/name).read_bytes()).hexdigest()!=expected:
            raise ValueError('Prediction/evaluation source changed after freezing: '+name)
    PortableTree(artifact['model'])
    Policy(**artifact['policy']).validate()
    return artifact,manifest
