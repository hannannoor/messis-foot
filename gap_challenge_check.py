"""One prospective challenge self-consistency run; aggregate-only, no metric or GT."""
import argparse
from collections import Counter
from datetime import datetime,timezone
import hashlib
import json
from math import isfinite
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

import gap_liveness_experiment as gap
import metrica_gap_check as metrica
from touch_experiment import canonical,read,write_new

ROOT=Path(__file__).resolve().parent
PUBLIC=ROOT/'reports/gap-liveness/challenge-check'
PRIVATE=gap.PRIVATE/'challenge-check'
HANDLING=ROOT/'.superpowers/release/target-handling.json'
SPEC=ROOT/'docs/superpowers/specs/2026-11-10-gap-challenge-aggregate-design.md'
GAP_KEYS={'long_gaps','stoppage_gaps','live_or_unclassified_gaps','long_gap_frames','stoppage_gap_frames',
          'restart_extension_frames','frames_relabelled','reference_speed_mps','defined_speed_samples'}


def labels_valid(frames,labels):
    if len(frames)!=len(labels) or any(v not in ('H','A','D','X') for v in labels):raise ValueError('Invalid labels/dimensions')
    if any(type(f.period) is not int or f.period not in (0,1,2) for f in frames):raise ValueError('Invalid structural period')


def counts(labels):
    c=Counter(labels)
    return {key:c[key] for key in 'HADX'}


def label_summary(frames,labels):
    labels_valid(frames,labels)
    graded=[v for f,v in zip(frames,labels) if f.period in (1,2)]
    if not graded:raise ValueError('No graded frames')
    spells=0;previous=None
    for f,v in zip(frames,labels):
        current=(f.period,v) if f.period in (1,2) and v in ('H','A') else None
        if current is not None and current!=previous:spells+=1
        previous=current
    c=counts(graded)
    return dict(graded_frames=len(graded),label_counts=c,d_share=c['D']/len(graded),spells=spells)


def tag_starts(path):
    result=[]
    for item in ET.parse(path).iter('instance'):
        if ' '.join((item.findtext('code') or '').upper().split())!='SET PIECES':continue
        start=float(item.findtext('start'))
        if not isfinite(start):raise ValueError('Invalid automatic tag start')
        result.append(round(start*25))
    return result


def tag_coverage(frames,labels,starts):
    labels_valid(frames,labels);covered_at=bytearray(len(frames));last=None;period=None
    for i,(f,v) in enumerate(zip(frames,labels)):
        if f.period!=period or f.period not in (1,2):last=None
        period=f.period
        if f.period not in (1,2):continue
        if v=='D':last=i
        if last is not None and i-last<=75:covered_at[i]=1
    eligible=[i for i in starts if 0<=i<len(frames) and frames[i].period in (1,2)]
    covered=sum(covered_at[i] for i in eligible)
    return dict(covered=covered,total=len(eligible),share=covered/len(eligible) if eligible else None)


def second_half(frames,control,candidate):
    labels_valid(frames,control);labels_valid(frames,candidate)
    first=next((i for i,f in enumerate(frames) if f.period==2),None)
    if first is None:raise ValueError('No structural second-half block')
    stop=first
    while stop<len(frames) and frames[stop].period==2 and not frames[stop].ball_observed:stop+=1
    found=stop<len(frames) and frames[stop].period==2 and frames[stop].ball_observed
    return dict(frames=stop-first,observed_ball_found=bool(found),control=counts(control[first:stop]),candidate=counts(candidate[first:stop]))


def verify_patch(control,candidate,stoppages,extensions):
    if len(control)!=len(candidate):raise ValueError('Patch dimensions changed')
    mask=bytearray(len(control))
    for first,stop in tuple(stoppages)+tuple(extensions):
        if not 0<=first<stop<=len(control):raise ValueError('Invalid patch interval')
        if any(mask[first:stop]):raise ValueError('Overlapping patch intervals')
        mask[first:stop]=b'\1'*(stop-first)
    if any((b!='D' if mask[i] else a!=b) for i,(a,b) in enumerate(zip(control,candidate))):raise ValueError('Patch parity failed')


def decision(row):
    reasons=[]
    if row['candidate']['d_share']>.60:reasons.append('candidate D share exceeds 60 percent')
    if row['gap']['stoppage_gaps']==0:reasons.append('zero stoppage gaps')
    return dict(passed=not reasons,decision='Stop challenge check: '+'; '.join(reasons) if reasons else 'Pass challenge self-consistency check')


def aggregate(frames,control,candidate,starts,summary,*,validate=True):
    row=dict(control=label_summary(frames,control),candidate=label_summary(frames,candidate),
        tag_coverage=dict(control=tag_coverage(frames,control,starts),candidate=tag_coverage(frames,candidate,starts)),
        second_half_initial=second_half(frames,control,candidate),gap=dict(summary),
        changed_frames=sum(a!=b for a,b in zip(control,candidate)))
    row.update(decision(row))
    if validate:validate_aggregate(row)
    return row


def integer(value,maximum):
    if type(value) is not int or not 0<=value<=maximum:raise ValueError('Invalid aggregate count')


def validate_aggregate(row):
    expected={'control','candidate','tag_coverage','second_half_initial','gap','changed_frames','passed','decision'}
    if type(row) is not dict or set(row)!=expected:raise ValueError('Unexpected aggregate fields')
    n=row['control']['graded_frames'];integer(n,10000000)
    if n==0:raise ValueError('No graded support')
    def valid_counts(c,total):
        if type(c) is not dict or set(c)!=set('HADX'):raise ValueError('Invalid label count schema')
        for v in c.values():integer(v,total)
        if sum(c.values())!=total:raise ValueError('Label counts do not reconcile')
    for name in ('control','candidate'):
        v=row[name]
        if set(v)!={'graded_frames','label_counts','d_share','spells'} or v['graded_frames']!=n:raise ValueError('Invalid label summary')
        valid_counts(v['label_counts'],n);integer(v['spells'],n)
        if v['d_share']!=v['label_counts']['D']/n:raise ValueError('D share does not reconcile')
    g=row['gap']
    if type(g) is not dict or set(g)!=GAP_KEYS:raise ValueError('Invalid gap count schema')
    for key,v in g.items():
        if key=='reference_speed_mps':
            if v is not None and (type(v) not in (int,float) or not isfinite(v) or not 0<=v<12):raise ValueError('Invalid reference speed')
        else:integer(v,n)
    if g['long_gaps']!=g['stoppage_gaps']+g['live_or_unclassified_gaps'] or g['stoppage_gap_frames']>g['long_gap_frames']:raise ValueError('Gap counts do not reconcile')
    integer(row['changed_frames'],n)
    if row['changed_frames']!=g['frames_relabelled'] or row['changed_frames']>g['stoppage_gap_frames']+g['restart_extension_frames']:raise ValueError('Patch counts do not reconcile')
    if row['candidate']['label_counts']['D']-row['control']['label_counts']['D']!=row['changed_frames']:raise ValueError('D delta does not reconcile')
    if set(row['tag_coverage'])!={'control','candidate'}:raise ValueError('Invalid tag schema')
    for v in row['tag_coverage'].values():
        if set(v)!={'covered','total','share'}:raise ValueError('Unexpected tag fields')
        integer(v['total'],10000000);integer(v['covered'],v['total'])
        if v['share']!=(v['covered']/v['total'] if v['total'] else None):raise ValueError('Tag share does not reconcile')
    if row['tag_coverage']['control']['total']!=row['tag_coverage']['candidate']['total']:raise ValueError('Tag denominator changed')
    half=row['second_half_initial']
    if set(half)!={'frames','observed_ball_found','control','candidate'} or type(half['observed_ball_found']) is not bool:raise ValueError('Invalid half summary')
    integer(half['frames'],n);valid_counts(half['control'],half['frames']);valid_counts(half['candidate'],half['frames'])
    if any(row[k]!=v for k,v in decision(row).items()):raise ValueError('Decision mismatch')


def claim(directory,freeze_sha256):
    write_new(Path(directory)/'run-entry.json',dict(freeze_sha256=freeze_sha256,paired_inference_attempt=1,utc=datetime.now(timezone.utc).isoformat()))


def input_paths():
    handling=read(HANDLING);prefix=handling['input_prefix']
    return handling,dict(zip(('metadata','tracking','homography','automatic_tags'),
        (Path(prefix+s) for s in ('_atd.xml','_atd.txt','_homography.csv','_smart_tagging.xml'))))


def input_hashes(paths):
    return {name:gap.sha(path) for name,path in paths.items()}


def prerequisites():
    external=gap.audit();sample=metrica.audit()
    if external['decision']!='Pass external harm gate' or sample['decision']!='Pass Metrica clear-harm check':raise ValueError('Prior harm checks must pass')
    return dict(external=external,metrica=sample)


def baseline_receipts(handling):
    root=Path(handling['private_root']);rows=[]
    for run in ('raw-run-1','raw-run-2'):
        receipt=read(root/run/'release-receipt.json')
        if receipt['input_sha256']!=handling['expected_input_sha256']:raise ValueError('Historical control input mismatch')
        if gap.sha(root/run/'submission.csv')!=receipt['csv_sha256']:raise ValueError('Historical control output changed')
        rows.append(receipt)
    if rows[0]!=rows[1]:raise ValueError('Historical control reproductions differ')
    return rows[0]


def freeze():
    if PRIVATE.exists() or (PUBLIC/'freeze.json').exists():raise FileExistsError('Challenge check already exists')
    prior=prerequisites();handling,paths=input_paths();identities=input_hashes(paths)
    if {k:identities[k] for k in handling['expected_input_sha256']}!=handling['expected_input_sha256']:raise ValueError('Challenge inputs differ from frozen control')
    baseline=baseline_receipts(handling)
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    documents={str(SPEC.relative_to(ROOT)).replace('\\','/'):gap.sha(SPEC)}
    gap.check_committed_documents(head,documents)
    value=dict(schema_version=1,source_commit=head,source_sha256=gap.source_hashes(head),document_sha256=documents,
        runtime=gap.runtime(),input_sha256=identities,handling_sha256=gap.sha(HANDLING),prerequisites=prior,baseline_labels_sha256=baseline['labels_sha256'],
        rows=baseline['rows'],rule_source_sha256=gap.sha(ROOT/'gap_liveness.py'),limits=dict(paired_inference=1,scoring=0),
        automatic_promotion=False,created_utc=datetime.now(timezone.utc).isoformat())
    PRIVATE.mkdir(parents=True)
    write_new(PRIVATE/'input-map.json',{k:str(p.resolve()) for k,p in paths.items()})
    write_new(PUBLIC/'freeze.json',value);gap.bind_freeze_identity(PUBLIC,PRIVATE,head)
    return dict(status='challenge_freeze_requires_commit_before_run',limits=value['limits'])


def checked(allow_additive=False):
    frozen=read(PUBLIC/'freeze.json');gap.verify_freeze_identity(PUBLIC,PRIVATE,frozen)
    data=subprocess.check_output(['git','show','HEAD:reports/gap-liveness/challenge-check/freeze.json'],cwd=ROOT)
    if data!=(PUBLIC/'freeze.json').read_bytes():raise ValueError('Challenge freeze not committed')
    commit=subprocess.check_output(['git','log','-1','--format=%H','--','reports/gap-liveness/challenge-check/freeze.json'],cwd=ROOT,text=True).strip()
    metrica.verify_source_inventory(frozen,allow_additive)
    if gap.source_hashes(commit)!=frozen['source_sha256'] or gap.source_hashes(frozen['source_commit'])!=frozen['source_sha256']:raise ValueError('Challenge source changed')
    if subprocess.run(['git','merge-base','--is-ancestor',frozen['source_commit'],commit],cwd=ROOT,capture_output=True).returncode:raise ValueError('Nonprospective challenge source')
    gap.check_committed_documents(frozen['source_commit'],frozen['document_sha256'])
    if {name:gap.sha(ROOT/name) for name in frozen['document_sha256']}!=frozen['document_sha256'] or gap.runtime()!=frozen['runtime']:raise ValueError('Challenge docs/runtime changed')
    if frozen['limits']!=dict(paired_inference=1,scoring=0):raise ValueError('Challenge budget changed')
    if prerequisites()!=frozen['prerequisites'] or not gap.preservation()['unchanged']:raise ValueError('Prior evidence changed')
    handling,paths=input_paths()
    if gap.sha(HANDLING)!=frozen['handling_sha256'] or {k:str(p.resolve()) for k,p in paths.items()}!=read(PRIVATE/'input-map.json') or input_hashes(paths)!=frozen['input_sha256']:raise ValueError('Challenge input identity changed')
    if gap.sha(ROOT/'gap_liveness.py')!=frozen['rule_source_sha256'] or baseline_receipts(handling)['labels_sha256']!=frozen['baseline_labels_sha256']:raise ValueError('Frozen rule/control changed')
    return frozen,commit,paths


def run():
    frozen,commit,paths=checked();claim(PRIVATE,gap.sha(PUBLIC/'freeze.json'))
    from release_runtime import load_source,predict_selected
    from gap_liveness import apply_gap_rule
    frames,source_audit=load_source(*(paths[k] for k in ('metadata','tracking','homography')))
    baseline=predict_selected(frames).labels;candidate=apply_gap_rule(frames,baseline)
    starts=tag_starts(paths['automatic_tags'])
    row=aggregate(frames,baseline,candidate.labels,starts,candidate.summary,validate=False)
    identity=dict(freeze_commit=commit,freeze_sha256=gap.sha(PUBLIC/'freeze.json'))
    labels_sha={name:hashlib.sha256(''.join(labels).encode('ascii')).hexdigest() for name,labels in (('control',baseline),('candidate',candidate.labels))}
    result=dict(identity,aggregate=row,labels_sha256=labels_sha,rows=len(frames),paired_inference_attempts=1,scoring_calls=0)
    with (PRIVATE/'provisional.json').open('x',encoding='utf-8') as handle:
        json.dump(result,handle,sort_keys=True,separators=(',',':'),allow_nan=True);handle.write('\n')
    verify_patch(baseline,candidate.labels,candidate.stoppage_gaps,candidate.extensions)
    if len(frames)!=frozen['rows'] or labels_sha['control']!=frozen['baseline_labels_sha256']:raise ValueError('Challenge control parity failed')
    if source_audit['input_sha256']!={k:frozen['input_sha256'][k] for k in ('metadata','tracking','homography')}:raise ValueError('Loader input identity mismatch')
    checked();validate_aggregate(row)
    write_new(PUBLIC/'results.json',result)
    write_new(PRIVATE/'results-seal.json',dict(results_sha256=gap.sha(PUBLIC/'results.json'),provisional_sha256=gap.sha(PRIVATE/'provisional.json'),claim_sha256=gap.sha(PRIVATE/'run-entry.json')))
    return result


def audit():
    frozen,commit,_=checked(allow_additive=True)
    row=read(PUBLIC/'results.json');private=read(PRIVATE/'provisional.json');seal=read(PRIVATE/'results-seal.json')
    if row!=private or set(row)!={'freeze_commit','freeze_sha256','aggregate','labels_sha256','rows','paired_inference_attempts','scoring_calls'}:raise ValueError('Challenge result mismatch')
    validate_aggregate(row['aggregate'])
    if row['freeze_commit']!=commit or row['freeze_sha256']!=gap.sha(PUBLIC/'freeze.json') or row['rows']!=frozen['rows'] or row['paired_inference_attempts']!=1 or row['scoring_calls']!=0:raise ValueError('Challenge result identity/calls mismatch')
    if set(row['labels_sha256'])!={'control','candidate'} or row['labels_sha256']['control']!=frozen['baseline_labels_sha256']:raise ValueError('Challenge prediction identity mismatch')
    expected=dict(results_sha256=gap.sha(PUBLIC/'results.json'),provisional_sha256=gap.sha(PRIVATE/'provisional.json'),claim_sha256=gap.sha(PRIVATE/'run-entry.json'))
    if seal!=expected or read(PRIVATE/'run-entry.json')['freeze_sha256']!=gap.sha(PUBLIC/'freeze.json'):raise ValueError('Challenge seal mismatch')
    if {p.name for p in PRIVATE.iterdir()}!={'input-map.json','freeze-identity.json','run-entry.json','provisional.json','results-seal.json'}:raise ValueError('Unexpected challenge private inventory')
    return dict(verified=True,decision=row['aggregate']['decision'],extra_inference_or_scoring=0,freeze_commit=commit)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('stage',choices=('freeze','run','audit'));args=parser.parse_args()
    try:result={'freeze':freeze,'run':run,'audit':audit}[args.stage]()
    except Exception as error:
        PRIVATE.mkdir(parents=True,exist_ok=True)
        import traceback
        name=args.stage+'-failure-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')+'.log'
        with (PRIVATE/name).open('x',encoding='utf-8') as handle:traceback.print_exc(file=handle)
        raise SystemExit('Challenge check stopped: '+type(error).__name__+'; private failure retained, no automatic retry or budget reset.') from None
    print(json.dumps(result,sort_keys=True,allow_nan=False),flush=True)


if __name__=='__main__':main()
