"""Public runner: JSON-compatible comparator equality, unchanged frozen scoring math."""
import json,sys
from pathlib import Path
import ball_gap_experiment as engine
from accuracy_evidence import portable_require_files
from gap_solver.accuracy_protocol import hash_files

ROOT=Path(__file__).resolve().parent
sha256=engine.sha256
RAW_METRICS=engine.original.aggregate_metrics


def canonical_metrics(value):
    # JSON spells numeric IoU dictionary keys as strings. Normalize both old and
    # new evidence to that representation without altering a metric value.
    return json.loads(json.dumps(value,allow_nan=False))


def check_runner_source(root=ROOT):
    reports=Path(root)/'reports/ball-gap';value=json.loads((reports/'runner-source.json').read_text())
    portable_require_files(value['source_sha256'],{n:Path(root)/n for n in value['source_sha256']})
    if value['original_freeze_file_sha256']!=sha256(reports/'comparison-freeze.json'):raise ValueError('Original ball-gap freeze changed')


def seal():
    engine.load_freeze()
    if any(engine.REPORTS.glob('*/*.json')):raise ValueError('Runner source must be sealed before any scored receipt')
    value=dict(schema_version=1,source_sha256=hash_files({'ball_gap_run.py':ROOT/'ball_gap_run.py'}),
        original_freeze_file_sha256=sha256(engine.REPORTS/'comparison-freeze.json'),
        purpose='Only normalize numeric IoU dict keys for JSON comparator equality; frozen math and policy unchanged')
    engine.store_identical(engine.REPORTS/'runner-source.json',value)
    print('Serialization runner sealed before scoring; original freeze preserved',flush=True)


def activate():
    check_runner_source();engine.load_freeze()
    engine.original.aggregate_metrics=lambda *a,**kw:canonical_metrics(RAW_METRICS(*a,**kw))


if __name__ in ('__main__','__mp_main__'):
    if len(sys.argv)>1 and sys.argv[1]=='seal':
        if __name__=='__main__':seal()
    else:
        activate()
        if __name__=='__main__':engine.main()
