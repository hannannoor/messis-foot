"""Validate local output format and derive coverage facts without any reference labels."""
import csv
import hashlib
import json
from pathlib import Path
from gap_solver import official_metrics
from gap_solver.frozen_protocol import load_frozen

code=Path(__file__).resolve().parent
root=code.parent
directory=root/'analysis'/'tactical-validated'
artifact,manifest=load_frozen(root/'external-reference',code/'gap_solver')
report=json.loads((directory/'tactical_report.json').read_text(encoding='utf-8'))
if report['model_id']!=manifest['artifact_sha256']:
    raise ValueError('Local inference does not use the frozen external model')
table=official_metrics.read_label_csv(directory/'submission.csv')
error=official_metrics.validate_submission(table,199319)
if error:
    raise ValueError(error)
counts={'before':0,'after':0}
previous={'before':None,'after':None}
previous_period=None
with (directory/'diagnostics.csv').open(newline='',encoding='utf-8') as handle:
    for i,row in enumerate(csv.DictReader(handle)):
        if int(row['frame'])!=i:
            raise ValueError('Diagnostic index differs from submission row')
        period=int(row['period'])
        if period!=previous_period:
            previous={'before':None,'after':None}
        if period:
            for name,key in [('before','legacy_tagged_no_fixed_D_label'),('after','label')]:
                label=row[key]
                counts[name]+=label=='X' and previous[name]!='X'
                previous[name]=label
        previous_period=period
queue=json.loads((directory/'unresolved_intervals.json').read_text(encoding='utf-8'))
if len(queue)!=counts['after']:
    raise ValueError('Unresolved queue and CSV disagree')
if sum(report['unresolved_reasons'].values())!=report['after']['labels']['X']:
    raise ValueError('Unresolved explanation totals disagree with X frame count')
if report['after']['published_dead_frames'] or report['published_dead_interval_applied']:
    raise ValueError('New route unexpectedly applied the excluded published-D interval')
report['unresolved_intervals_before']=counts['before']
report['unresolved_intervals_after']=counts['after']
from gap_solver.tactical_model import FROZEN_MODEL
report['external_validation_limitations']=FROZEN_MODEL['validation_limitations']
(directory/'tactical_report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
proof=dict(schema_version=1,format_valid=True,original_rows=len(table),model_id=report['model_id'],
           graded_frames=report['after']['active_frames'],unresolved_intervals=counts,
           undecided_frames_before=report['before']['labels']['X'],undecided_frames_after=report['after']['labels']['X'],
           no_challenge_reference_read=True,no_model_or_policy_change=True,
           submission_sha256=hashlib.sha256((directory/'submission.csv').read_bytes()).hexdigest())
(root/'analysis'/'four-goal-coverage-verification.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
print(json.dumps(proof,indent=2))
