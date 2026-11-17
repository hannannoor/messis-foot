"""Audit existing evidence and immutable inputs; never score provided match labels."""
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from gap_solver.frozen_protocol import load_frozen

code=Path(__file__).resolve().parent
root=code.parent
external=root/'external-reference'
analysis=root/'analysis'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
artifact,freeze=load_frozen(external,code/'gap_solver')
heldout=read(external/'reports/final-heldout.json')
assert heldout['complete'] and heldout['no_refitting_after_test']
assert heldout['artifact_sha256']==freeze['artifact_sha256']
assert datetime.fromisoformat(freeze['frozen_at_utc'])<datetime.fromisoformat(heldout['started_at_utc'])
assert all(s['every_match_spell_f1_improved'] and s['every_match_macro_f1_not_degraded'] and s['every_match_x_reduced']
           for s in heldout['summary'].values())
provenance=read(external/'provenance.json')
assert provenance['split_fixed_before_scores'] and len(provenance['files'])==21
assert provenance['license']['url']=='https://creativecommons.org/licenses/by/4.0/'
verified=[]
for file in provenance['files']:
    path=external/'raw'/file['name']
    assert path.stat().st_size==file['size'],path
    checksum=hashlib.md5()
    with path.open('rb') as handle:
        for block in iter(lambda:handle.read(8*1024*1024),b''):checksum.update(block)
    assert checksum.hexdigest()==file['md5'],path
    verified.append(dict(name=file['name'],md5=file['md5'],bytes=file['size']))
bundle=(code/'football_pipeline.py').read_text(encoding='utf-8')
tree=ast.parse(bundle,feature_version=(3,9))
sources=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign)
             and any(isinstance(t,ast.Name) and t.id=='SOURCES' for t in n.targets))
for module,text in sources.items():
    path=code/'gap_solver'/('__init__.py' if module=='gap_solver' else module.split('.')[-1]+'.py')
    assert text==path.read_text(encoding='utf-8'),module
    ast.parse(text,feature_version=(3,9))
local=read(analysis/'tactical-validated/tactical_report.json')
proof=read(analysis/'four-goal-coverage-verification.json')
assert proof['format_valid'] and proof['original_rows']==199319
assert proof['model_id']==freeze['artifact_sha256']==local['model_id']
assert digest(analysis/'tactical-validated/submission.csv')==proof['submission_sha256']
assert not local['accuracy_measured'] and not local['challenge_ground_truth_used']
assert not local['predictions_checked_against_video'] and not local['challenge_training_or_tuning_performed']
assert not local['published_dead_interval_applied'] and local['after']['published_dead_frames']==0
assert sum(local['unresolved_reasons'].values())==local['after']['labels']['X']==89200
assert local['before']['labels']['X']-local['after']['labels']['X']==20717
assert proof['unresolved_intervals']==dict(before=1045,after=509)
testlog=(code/'four-goal-final-tests.log').read_text(encoding='utf-8-sig')
match=re.search(r'Ran (\d+) tests',testlog)
assert match and int(match[1])==183 and 'OK (skipped=2)' in testlog and 'FAILED' not in testlog
# The installer tests consume a stable evidence copy, never an actively written log.
(code/'four-goal-test-evidence.log').write_text(testlog,encoding='utf-8')
coordinate=read(external/'reports/provider-coordinate-audit.json')
assert coordinate['model_or_policy_changed'] is False
assert local['external_validation_limitations']
diagnostic=read(external/'reports/team-occlusion-stress.json')
active_scores={m:{k:v['metrics']['spell_f1_mean'] for k,v in x['reference_active_only_diagnostic'].items() if k in ('baseline','selected')}
               for m,x in diagnostic['matches'].items()}
assert all(x['selected']<x['baseline'] for x in active_scores.values())
audit=dict(schema_version=1,checked_at_utc=datetime.now(timezone.utc).isoformat(),
    status='Four scoped workstreams evidenced; installed hashes are recorded separately by delivery-verification.json',
    release_status='Opt-in experiment, legacy default preserved',model_id=freeze['artifact_sha256'],
    goals={
      '1_external_benchmark':dict(status='complete',matches=7,raw_files_verified=verified,
          license='CC BY 4.0',split=freeze['split'],metric='unchanged official spellF1 functions',
          limitation='Provider reference, not challenge gold or an independent physical-event annotation'),
      '2_error_diagnosis':dict(status='complete for available evidence',
          evidence=['baseline-development-validation.json','boundary-and-observation-diagnostics.json',
                    'team-occlusion-stress.json','provider-coordinate-audit.json','tactical_report.json'],
          limitations='Boundary labels and flight/stationary proxies are provider/observable definitions; physical restart and flight ground truth unavailable'),
      '3_frozen_improvement':dict(status='complete for complete provider target only',frozen_before_test=True,
          source_integrity_verified=True,no_refitting=True,natural=heldout['summary']['natural'],
          active_only_spell_regressions=active_scores,
          limitations='Coordinate freezing can inflate D performance; transferable H/A and D quality are unverified'),
      '4_reduce_undecided':dict(status='coverage reduction demonstrated; local correctness unmeasured',
          original_rows=199319,match_frames=158857,before_x=109917,after_x=89200,net_reduction=20717,
          unresolved_intervals=proof['unresolved_intervals'],reason_totals=local['unresolved_reasons'],
          limitation='56.15% remains unknown; no provided video/GT validation or challenge-driven retuning')},
    verification=dict(full_suite_tests=183,skipped=2,bundled_modules=len(sources),python39_syntax=True,
                      standalone_sha256=digest(code/'football_pipeline.py'),submission_sha256=proof['submission_sha256']),
    review='docs/four-goal-final-review.md; important input and installation findings fixed with regression evidence',
    installation='Run install_four_goal_results.ps1 then -VerifyOnly; delivery-verification.json lists hashes for every installed file')
(analysis/'four-goal-completion-audit.json').write_text(json.dumps(audit,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(raw_files_verified=len(verified),model_id=audit['model_id'],tests=183,skipped=2,
                     bundle_modules=len(sources),local_net_x_reduction=20717,release_status=audit['release_status']),indent=2))
