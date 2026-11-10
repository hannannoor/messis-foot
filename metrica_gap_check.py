"""One-shot paired Metrica sample harm check; source and reference frozen first."""
import argparse,hashlib,json,re,subprocess
from datetime import datetime,timezone
from math import fsum
from pathlib import Path

import gap_liveness_experiment as gap
from touch_experiment import write_new,read,canonical

ROOT=Path(__file__).resolve().parent
PUBLIC=ROOT/'reports/gap-liveness/metrica-check'
PRIVATE=gap.PRIVATE/'metrica/evaluation'
SOURCE=gap.PRIVATE/'metrica/source'
MANIFEST=ROOT/'reports/gap-liveness/metrica-source-freeze.json'
ACQUISITION=ROOT/'reports/gap-liveness/metrica-acquisition.json'
QUALIFICATION=ROOT/'reports/gap-liveness/metrica-format-qualification.json'
SPEC=ROOT/'docs/superpowers/specs/2026-11-10-gap-metrica-check-design.md'
GAMES=('Sample_Game_1','Sample_Game_2','Sample_Game_3')
LIMITS=dict(control=3,rule=3)


def verify_asset(directory,asset):
    path=Path(directory)/asset['path']
    if not path.is_file() or path.stat().st_size!=asset['bytes']:raise ValueError('Sample asset missing or size changed')
    digest=hashlib.sha1(b'blob '+str(asset['bytes']).encode()+b'\0')
    with path.open('rb') as handle:
        for block in iter(lambda:handle.read(1024*1024),b''):digest.update(block)
    if digest.hexdigest()!=asset['git_blob_sha1']:raise ValueError('Sample asset Git identity changed')


def check_assets():
    manifest=read(MANIFEST);acquisition=read(ACQUISITION)
    if acquisition!=read(SOURCE/'acquisition-receipt.json'):raise ValueError('Acquisition receipts differ')
    if read(SOURCE/'acquisition-entry.json')['manifest_sha256']!=gap.sha(MANIFEST) or acquisition['manifest_sha256']!=gap.sha(MANIFEST):raise ValueError('Pinned sample manifest changed')
    if manifest['games']!=list(GAMES) or acquisition['commit']!=manifest['commit'] or not acquisition['complete']:raise ValueError('Sample cohort/source changed')
    if len({a['path'] for a in manifest['assets']})!=len(manifest['assets']):raise ValueError('Duplicate sample source path')
    expected={a['path']:a for a in manifest['assets']};actual={a['path']:a for a in acquisition['assets']}
    if set(expected)!=set(actual):raise ValueError('Sample acquisition inventory changed')
    for name,a in expected.items():
        if any(a[k]!=actual[name][k] for k in ('bytes','git_blob_sha1')):raise ValueError('Acquired source differs from pin')
        verify_asset(SOURCE,a)
        if gap.sha(SOURCE/name)!=actual[name]['sha256']:raise ValueError('Acquired source SHA differs')
    return manifest,acquisition


def claim(directory,variant,game):
    if variant not in LIMITS or game not in GAMES:raise ValueError('Undeclared sample claim')
    folder=Path(directory)/'claims'/variant
    if folder.exists() and len(list(folder.iterdir()))>=LIMITS[variant]:raise ValueError('Sample score budget exhausted')
    write_new(folder/(game+'.json'),dict(game=game,variant=variant,utc=datetime.now(timezone.utc).isoformat()))


def provisional(directory,variant,game,row):
    if variant not in LIMITS or game not in GAMES:raise ValueError('Invalid sample provisional receipt')
    write_new(Path(directory)/'provisional'/variant/(game+'.json'),row)


def decide(records):
    if len(records)!=len(GAMES) or {r['game'] for r in records}!=set(GAMES):raise ValueError('Exact three sample records required')
    control=fsum(r['control']['metrics']['spell_f1_mean'] for r in records)/len(GAMES)
    candidate=fsum(r['candidate']['metrics']['spell_f1_mean'] for r in records)/len(GAMES)
    passed=gap.within_loss(candidate,control,0.)
    return dict(passed=passed,control_mean=control,candidate_mean=candidate,delta=candidate-control,
        decision='Pass Metrica clear-harm check' if passed else 'Reject gap rule: Metrica mean declined',games=len(records),
        circularity='Manually corrected tracking; ball absence largely during dead play. Event-derived labels are not independently adjudicated possession truth.')


def freeze():
    if PRIVATE.exists() or (PUBLIC/'freeze.json').exists():raise FileExistsError('Sample experiment already exists')
    external=gap.audit()
    if external['decision']!='Pass external harm gate':raise ValueError('External harm gate required')
    manifest,acquisition=check_assets();qualification=read(QUALIFICATION)
    if not qualification['no_predictions_or_scores'] or {r['game'] for r in qualification['records']}!=set(GAMES):raise ValueError('Source qualification incomplete')
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();sources=gap.source_hashes(head)
    documents={str(p.relative_to(ROOT)).replace('\\','/'):gap.sha(p) for p in (SPEC,MANIFEST,ACQUISITION,QUALIFICATION)}
    gap.check_committed_documents(head,documents)
    value=dict(schema_version=1,source_commit=head,source_sha256=sources,document_sha256=documents,runtime=gap.runtime(),
        games=GAMES,limits=LIMITS,source_repository=manifest['repository'],source_revision=manifest['commit'],
        assets=manifest['assets'],external_verification=external,external_results_sha256=gap.sha(gap.PUBLIC/'external-results.json'),
        rule_source_sha256=gap.sha(ROOT/'gap_liveness.py'),reference_source_sha256=gap.sha(ROOT/'metrica_event_reference.py'),
        inference_has_no_reference_inputs=True,source_reference_format_inspected_before_scoring=True,reference_is_event_derived=True,
        no_rule_tuning=True,automatic_promotion=False,created_utc=datetime.now(timezone.utc).isoformat())
    PRIVATE.mkdir(parents=True)
    write_new(PRIVATE/'input-map.json',{a['path']:str((SOURCE/a['path']).resolve()) for a in manifest['assets']})
    write_new(PUBLIC/'freeze.json',value);gap.bind_freeze_identity(PUBLIC,PRIVATE,head)
    return dict(status='sample_freeze_requires_commit_before_scoring',games=3,limits=LIMITS)


def checked():
    frozen=read(PUBLIC/'freeze.json');gap.verify_freeze_identity(PUBLIC,PRIVATE,frozen)
    data=subprocess.check_output(['git','show','HEAD:reports/gap-liveness/metrica-check/freeze.json'],cwd=ROOT)
    if data!=(PUBLIC/'freeze.json').read_bytes():raise ValueError('Sample freeze not committed')
    commit=subprocess.check_output(['git','log','-1','--format=%H','--','reports/gap-liveness/metrica-check/freeze.json'],cwd=ROOT,text=True).strip()
    if gap.source_hashes(commit)!=frozen['source_sha256'] or gap.source_hashes(frozen['source_commit'])!=frozen['source_sha256']:raise ValueError('Sample source identity changed')
    if subprocess.run(['git','merge-base','--is-ancestor',frozen['source_commit'],commit],cwd=ROOT,capture_output=True).returncode:raise ValueError('Sample source is not prospective')
    gap.check_committed_documents(frozen['source_commit'],frozen['document_sha256'])
    if {name:gap.sha(ROOT/name) for name in frozen['document_sha256']}!=frozen['document_sha256'] or gap.runtime()!=frozen['runtime']:raise ValueError('Sample docs/runtime changed')
    if frozen['games']!=list(GAMES) or frozen['limits']!=LIMITS or gap.sha(gap.PUBLIC/'external-results.json')!=frozen['external_results_sha256']:raise ValueError('Sample cohort/budget/prerequisite changed')
    if gap.sha(ROOT/'gap_liveness.py')!=frozen['rule_source_sha256']:raise ValueError('Gap rule changed after4a')
    if not gap.preservation()['unchanged']:raise ValueError('Historical source archive changed')
    manifest,_=check_assets()
    expected={a['path']:str((SOURCE/a['path']).resolve()) for a in manifest['assets']}
    if read(PRIVATE/'input-map.json')!=expected:raise ValueError('Sample source path mapping changed')
    return frozen,commit


def seal_value(records,commit):
    expected={g+'.json' for g in GAMES}
    if {p.name for p in (PUBLIC/'cases').iterdir()}!=expected:raise ValueError('Sample receipt inventory differs')
    for variant in LIMITS:
        if {p.name for p in (PRIVATE/'claims'/variant).iterdir()}!=expected:raise ValueError('Sample claim inventory differs')
        if {p.name for p in (PRIVATE/'provisional'/variant).iterdir()}!=expected:raise ValueError('Sample completed-score inventory differs')
    identity=dict(freeze_commit=commit,freeze_sha256=gap.sha(PUBLIC/'freeze.json'))
    for row in records:
        if any(row.get(k)!=v for k,v in identity.items()):raise ValueError('Sample case freeze changed')
        for variant in LIMITS:
            expected_score=row['control' if variant=='control' else 'candidate']
            if read(PRIVATE/'provisional'/variant/(row['game']+'.json'))!=dict(identity,game=row['game'],variant=variant,score=expected_score):raise ValueError('Sample provisional score changed')
            path=PRIVATE/'predictions'/(row['game']+'-'+variant+'.labels')
            gap.load_control_labels(path,row['labels_sha256'][variant],row['control']['support']['frames'])
    return dict(identity,cases={p.name:gap.sha(p) for p in sorted((PUBLIC/'cases').iterdir())},summary_sha256=gap.sha(PUBLIC/'results.json'),
        claims={v:{p.name:gap.sha(p) for p in sorted((PRIVATE/'claims'/v).iterdir())} for v in LIMITS})


def run():
    frozen,commit=checked()
    from metrica_sample_adapter import load_game,load_events
    from metrica_event_reference import build_reference
    from release_runtime import predict_selected
    from gap_liveness import apply_gap_rule
    from ownership_diagnosis import _codes
    write_new(PRIVATE/'run-entry.json',dict(freeze_commit=commit));records=[]
    qualification={r['game']:r for r in read(QUALIFICATION)['records']}
    for game in GAMES:
        frames,mapping=load_game(SOURCE,game)
        if len(frames)!=qualification[game]['frames']:raise ValueError('Qualified sample grid changed')
        claim(PRIVATE,'control',game);baseline=predict_selected(frames).labels
        claim(PRIVATE,'rule',game);candidate=apply_gap_rule(frames,baseline)
        predictions=dict(control=baseline,rule=candidate.labels);identities={}
        for variant,labels in predictions.items():
            path=PRIVATE/'predictions'/(game+'-'+variant+'.labels');path.parent.mkdir(parents=True,exist_ok=True)
            with path.open('xb') as handle:handle.write(''.join(labels).encode('ascii'))
            identities[variant]=gap.sha(path)
        events=load_events(SOURCE,game,mapping);reference,ref_summary=build_reference(events,[f.period for f in frames])
        if ref_summary!=qualification[game]['reference']:raise ValueError('Qualified event reference changed')
        identity=dict(freeze_commit=commit,freeze_sha256=gap.sha(PUBLIC/'freeze.json'))
        scores={}
        for variant,labels in predictions.items():
            scores[variant]=gap.score(_codes(reference),labels,frames)
            provisional(PRIVATE,variant,game,dict(identity,game=game,variant=variant,score=scores[variant]))
        check_assets()
        row=dict(identity,game=game,control=scores['control'],candidate=scores['rule'],gap=candidate.summary,reference=ref_summary,labels_sha256=identities)
        write_new(PUBLIC/'cases'/(game+'.json'),row);records.append(row)
        print(json.dumps(dict(game=game,completed=len(records),games=3,control=scores['control']['metrics']['spell_f1_mean'],candidate=scores['rule']['metrics']['spell_f1_mean'])),flush=True)
    result=dict(decide(records),freeze_commit=commit,freeze_sha256=gap.sha(PUBLIC/'freeze.json'),scoring_calls=6,
        per_game=[dict(game=r['game'],control=r['control']['metrics']['spell_f1_mean'],candidate=r['candidate']['metrics']['spell_f1_mean'],gap=r['gap']) for r in records])
    write_new(PUBLIC/'results.json',result);write_new(PRIVATE/'results-seal.json',seal_value(records,commit))
    return result


def audit():
    frozen,commit=checked();records=[read(PUBLIC/'cases'/(game+'.json')) for game in GAMES]
    if read(PRIVATE/'results-seal.json')!=seal_value(records,commit):raise ValueError('Sample result seal changed')
    summary=decide(records);saved=read(PUBLIC/'results.json')
    if any(saved.get(k)!=v for k,v in summary.items()):raise ValueError('Sample mean/gate differs')
    return dict(verified=True,decision=summary['decision'],claims=LIMITS,extra_inference_or_scoring=0,freeze_commit=commit)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('stage',choices=('freeze','run','audit'));args=parser.parse_args()
    try:result={'freeze':freeze,'run':run,'audit':audit}[args.stage]()
    except Exception as error:
        PRIVATE.mkdir(parents=True,exist_ok=True)
        import traceback
        filename=args.stage+'-failure-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')+'.log'
        with (PRIVATE/filename).open('x',encoding='utf-8') as f:traceback.print_exc(file=f)
        raise SystemExit('Metrica check stopped: '+type(error).__name__+'; private failure retained, no automatic retry or budget reset.') from None
    print(json.dumps(result,sort_keys=True,allow_nan=False),flush=True)

if __name__=='__main__':main()
