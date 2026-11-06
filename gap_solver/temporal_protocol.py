"""Fail-closed freeze and eligibility contract; a rejected validation result stays rejected."""
import hashlib,json
from pathlib import Path


def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def evidence_identity(sources,inputs,artifact):
    return dict(artifact_sha256=artifact,source_sha256={name:hashlib.sha256(Path(p).read_bytes()).hexdigest() for name,p in sources.items()},
        input_sha256={name:hashlib.sha256(Path(p).read_bytes()).hexdigest() for name,p in inputs.items()})


def require_evidence(report,expected):
    if report.get('identity')!=expected:raise ValueError('Stale or mismatched evidence identity')


def load_temporal_frozen(directory,code_directory):
    directory=Path(directory);code_directory=Path(code_directory)
    artifact=json.loads((directory/'temporal-selected.json').read_text(encoding='utf-8'))
    manifest=json.loads((directory/'freeze-manifest.json').read_text(encoding='utf-8'))
    if manifest.get('frozen_before_final_test') is not True or digest(artifact)!=manifest.get('artifact_sha256'):
        raise ValueError('Temporal artifact freeze integrity failed')
    split=manifest.get('split',{})
    if set(split)!={'development','calibration','validation','test'} or any(not isinstance(v,list) or not v for v in split.values()):
        raise ValueError('Invalid temporal partition')
    ids=sum(split.values(),[])
    if len(ids)!=len(set(ids)):raise ValueError('Temporal match partitions overlap')
    sources=manifest.get('source_sha256',{})
    if not sources:raise ValueError('Temporal freeze lacks prediction/evaluation sources')
    for name,expected in sources.items():
        path=Path(name)
        if path.is_absolute() or '..' in path.parts or path.suffix!='.py':raise ValueError('Invalid temporal source path')
        if hashlib.sha256((code_directory/path).read_bytes()).hexdigest()!=expected:raise ValueError('Temporal source changed after freeze: '+name)
    if (artifact.get('eligibility')=='eligible')!=(artifact.get('validation_passed') is True):raise ValueError('Inconsistent temporal validation eligibility')
    if artifact.get('eligibility') not in ('eligible','rejected_before_final_test'):raise ValueError('Unknown temporal eligibility')
    return artifact,manifest


def local_eligible(artifact,final_report):
    return (artifact.get('eligibility')=='eligible' and artifact.get('validation_passed') is True
        and final_report.get('artifact_sha256')==digest(artifact) and final_report.get('acceptance',{}).get('passes') is True)
