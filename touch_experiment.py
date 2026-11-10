"""Bounded external-only experiment; inference and challenge probes are separate."""
import argparse
from collections import defaultdict
from dataclasses import replace
from datetime import datetime,timezone
import hashlib
import json
from math import fsum,hypot
from pathlib import Path
import platform
import random
import re
import subprocess
import sys

BASE='431d1ec556ef77a46d76e8227eba9690c07d08e5'
ROOT=Path(__file__).resolve().parent
PUBLIC=ROOT/'reports/touch-evidence'
PRIVATE=ROOT.parent/'touch-evidence-private/2026-11-10'
REGIMES=('natural','mask30-seed1729','jitter')
GRID=tuple(dict(theta=t,beta=b,c_touch=c) for t in (3,5) for b in (1,2,4) for c in (32,8))
LIMITS=dict(control=45,development=216,confirmation=21)


def split_matches():
    from memory_ablation_metrics import MATCHES
    sc=sorted(cid for cid,p,role in MATCHES if p=='skillcorner' and role=='fit-disjoint')
    dfl=sorted(cid for cid,p,role in MATCHES if p=='dfl' and role=='fit-disjoint')
    dev=sc[::2]+dfl[:1]
    confirmation=sc[1::2]+dfl[1:]+['wcsf-used-match']
    return dev,confirmation


def provider_mean(scores):
    groups=defaultdict(list)
    for cid,value in scores.items():groups[cid.split('-',1)[0]].append(value)
    if not groups:raise ValueError('No provider scores')
    return fsum(fsum(v)/len(v) for v in groups.values())/len(groups)


def select_config(scores,control):
    eligible=[s for s in scores if all(s['means'][r]>=control[r] for r in REGIMES[1:])]
    if not eligible:return None
    return min(eligible,key=lambda s:(-s['means']['natural'],s['config']['beta'],s['config']['c_touch']!=32,-s['config']['theta']))['config']


def add_jitter(frames):
    rng=random.Random(1729);result=[]
    for f in frames:
        if not f.ball_observed:result.append(f);continue
        x,y=f.ball_x+rng.gauss(0,.05),f.ball_y+rng.gauss(0,.05)
        distances=[min((hypot(a-x,b-y) for a,b in points),default=None) for points in (f.home_xy,f.away_xy)]
        result.append(replace(f,ball_x=x,ball_y=y,home_distance=distances[0],away_distance=distances[1]))
    return result


def claim(directory,phase,key):
    if phase not in LIMITS or not re.fullmatch('[a-zA-Z0-9-]+',key):raise ValueError('Invalid scientific claim')
    folder=Path(directory)/'claims'/phase;folder.mkdir(parents=True,exist_ok=True)
    if len(list(folder.iterdir()))>=LIMITS[phase]:raise ValueError('Scientific budget exhausted')
    with (folder/(key+'.json')).open('x',encoding='utf-8') as handle:
        json.dump(dict(key=key,utc=datetime.now(timezone.utc).isoformat()),handle,sort_keys=True)


def classify(means,safeguards_pass,provider_natural_pass):
    gain=means['natural']['candidate']-means['natural']['control']
    if gain<=0 or not safeguards_pass:return 'Reject'
    if gain>=.04 and all(means[r]['candidate']>means[r]['control'] for r in REGIMES[1:]) and provider_natural_pass:
        return 'Accept'
    return 'Inconclusive'


def safeguards(rows):
    failures=[];ratios=defaultdict(lambda:dict(control=[],candidate=[]))
    for row in rows:
        cid,regime=row['case_id'],row['regime'];cohort=cid.split('-',1)[0]
        control,candidate=row['control'],row['candidate']
        if any(candidate['predicted_on_known'][t]<=0 for t in ('H','A')):failures.append(dict(case_id=cid,regime=regime,gate='both_owners'))
        if cohort in ('dfl','wcsf'):
            a,b=control['dead']['recall'],candidate['dead']['recall']
            if a is None or b is None or b<a-.02:failures.append(dict(case_id=cid,regime=regime,gate='dead_recall'))
        for variant in ('control','candidate'):
            spells=row[variant]['spells'];gt=spells['n_gt']
            if gt<=0:failures.append(dict(case_id=cid,regime=regime,gate='spell_support'));continue
            ratios[(cohort,regime)][variant].append(spells['n_pred']/gt)
    provider_ratios=[]
    for (cohort,regime),values in sorted(ratios.items()):
        means={v:fsum(a)/len(a) for v,a in values.items() if a}
        if set(means)!={'control','candidate'} or abs(means['candidate']-1)>abs(means['control']-1):
            failures.append(dict(provider=cohort,regime=regime,gate='spell_count_ratio'))
        provider_ratios.append(dict(provider=cohort,regime=regime,**means))
    return dict(passed=not failures,failures=failures,provider_spell_ratios=provider_ratios)


def canonical(value):return (json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write_new(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb') as handle:handle.write(canonical(value))
def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def config_id(config):return 't'+str(config['theta'])+'-b'+str(config['beta'])+'-c'+str(config['c_touch'])


def preserved_sources():
    names=subprocess.check_output(['git','ls-tree','-r','--name-only',BASE],cwd=ROOT,text=True).splitlines()
    changes=[]
    for name in names:
        original=subprocess.check_output(['git','show',BASE+':'+name],cwd=ROOT)
        if not (ROOT/name).is_file() or hashlib.sha256(original).hexdigest()!=sha(ROOT/name):changes.append(name)
    return dict(base=BASE,original_files=len(names),unchanged=not changes,changed_paths=changes)


def source_hashes():
    names=subprocess.check_output(['git','ls-files','*.py'],cwd=ROOT,text=True).splitlines()
    return {name:sha(ROOT/name) for name in names}


def freeze():
    import memory_ablation_protocol as p
    from memory_ablation_metrics import MATCHES
    preservation=preserved_sources()
    if not preservation['unchanged']:raise ValueError('Preserved sources changed')
    if PRIVATE.exists() or (PUBLIC/'freeze.json').exists():raise FileExistsError('Touch experiment already exists')
    bindings=p.input_bindings(ROOT)['evaluation']
    for binding in bindings.values():
        if p.hashes(binding['files'])!=binding['expected']:raise ValueError('External input identity differs')
    dev,confirm=split_matches()
    import numpy,pandas
    frozen=dict(schema_version=1,experiment='touch-evidence-2026-11-10',created_utc=datetime.now(timezone.utc).isoformat(),
        base=BASE,official_commit='f8f2629ff1e0985f81d7e59d8413678514ee1530',grid=GRID,regimes=REGIMES,
        sigma_m=.05,jitter_seed=1729,mask_seed=1729,mask_rate=.3,limits=LIMITS,development=dev,confirmation=confirm,
        secondary=[cid for cid,p,role in MATCHES if role=='fitting-overlap'],
        source_sha256=source_hashes(),input_sha256={cid:b['expected'] for cid,b in bindings.items()},
        design_sha256=sha(ROOT/'docs/superpowers/specs/2026-11-10-touch-evidence-design.md'),
        plan_sha256=sha(ROOT/'docs/superpowers/plans/2026-11-10-touch-evidence.md'),
        runtime=dict(python=platform.python_version(),numpy=numpy.__version__,pandas=pandas.__version__,executable_sha256=sha(sys.executable)),
        gates=dict(natural_gain_min=.04,masked_jitter_strict_gain=True,natural_provider_no_decline=True,
            max_dead_recall_loss=.02,both_owners=True,provider_spell_ratio_no_further_from_one=True),
        expected_control=dict(natural=.551816,**{'mask30-seed1729':.469149}),
        preservation=preservation,fresh_holdout=False,automatic_promotion=False,
        adapter_reference_container_may_be_parsed=True)
    PRIVATE.mkdir(parents=True)
    write_new(PRIVATE/'input-map.json',{cid:{k:str(v) for k,v in b['files'].items()} for cid,b in bindings.items()})
    write_new(PUBLIC/'freeze.json',frozen)
    return dict(status='frozen_not_yet_committed',cases=len(bindings),development=len(dev),confirmation=len(confirm))


def checked_freeze():
    frozen=read(PUBLIC/'freeze.json')
    if source_hashes()!=frozen['source_sha256']:raise ValueError('Frozen source changed')
    if sha(ROOT/'docs/superpowers/specs/2026-11-10-touch-evidence-design.md')!=frozen['design_sha256'] or sha(ROOT/'docs/superpowers/plans/2026-11-10-touch-evidence.md')!=frozen['plan_sha256']:
        raise ValueError('Frozen design changed')
    committed=subprocess.check_output(['git','show','HEAD:reports/touch-evidence/freeze.json'],cwd=ROOT)
    if committed!=(PUBLIC/'freeze.json').read_bytes():raise ValueError('Freeze not committed before scoring')
    commit=subprocess.check_output(['git','log','-1','--format=%H','--','reports/touch-evidence/freeze.json'],cwd=ROOT,text=True).strip()
    from memory_ablation_metrics import MATCHES
    if frozen['grid']!=list(GRID) or frozen['limits']!=LIMITS:raise ValueError('Protocol changed')
    files=read(PRIVATE/'input-map.json')
    bindings={cid:dict(files={k:Path(v) for k,v in paths.items()}) for cid,paths in files.items()}
    import memory_ablation_protocol as p
    for cid,b in bindings.items():
        if p.hashes(b['files'])!=frozen['input_sha256'][cid]:raise ValueError('Frozen external input changed')
    import numpy,pandas
    runtime=dict(python=platform.python_version(),numpy=numpy.__version__,pandas=pandas.__version__,executable_sha256=sha(sys.executable))
    if runtime!=frozen['runtime']:raise ValueError('Frozen runtime changed')
    return frozen,bindings,commit


def regimes(frames):
    from gap_solver.temporal_selection import contiguous_mask
    from gap_solver.temporal import mask_motion_frames
    yield 'natural',frames
    mask=contiguous_mask([f.period for f in frames],.3,1729)
    masked=mask_motion_frames(frames,mask)
    yield 'mask30-seed1729',masked
    yield 'jitter',add_jitter(masked)


def score(reference,labels,frames):
    from memory_ablation_metrics import score_variant
    from memory_ablation_protocol import validate_score
    result=score_variant(reference,labels,[f.period for f in frames],[f.ball_observed for f in frames])
    validate_score(result)
    return result


def means_for(records,ids,variant):
    return {r:provider_mean({x['case_id']:x[variant]['metrics']['spell_f1_mean'] for x in records if x['regime']==r and x['case_id'] in ids}) for r in REGIMES}


def control_run():
    frozen,bindings,commit=checked_freeze()
    from memory_ablation_run import load_evaluation
    from memory_ablation_metrics import MATCHES
    from release_runtime import predict_selected
    if (PRIVATE/'control-entry.json').exists():raise FileExistsError('Control phase cannot restart')
    write_new(PRIVATE/'control-entry.json',dict(freeze_commit=commit))
    records=[]
    for cid,_,_ in MATCHES:
        case=load_evaluation(cid,bindings[cid]);natural=case['frames']
        for regime,frames in regimes(natural):
            key=cid+'-'+regime;claim(PRIVATE,'control',key)
            prediction=predict_selected(frames)
            result=score(case['reference'](),prediction.labels,frames)
            row=dict(case_id=cid,regime=regime,control=result,freeze_commit=commit,freeze_sha256=sha(PUBLIC/'freeze.json'))
            write_new(PUBLIC/'control'/f'{key}.json',row);records.append(row)
            print(json.dumps(dict(phase='control',completed=len(records),maximum=45,case_id=cid,regime=regime)),flush=True)
    primary=[cid for cid,_,role in MATCHES if role=='fit-disjoint']
    means=means_for(records,primary,'control')
    passed=all(round(means[r],6)==frozen['expected_control'][r] for r in REGIMES[:2])
    receipt=dict(freeze_commit=commit,means=means,expected=frozen['expected_control'],passed=passed,scoring_calls=len(records))
    write_new(PUBLIC/'control-reproduction.json',receipt)
    if not passed:raise ValueError('Control reproduction gate failed')
    return receipt


def candidate_phase(phase,configs,ids,bindings,commit):
    from memory_ablation_run import load_evaluation
    from touch_evidence import prepare_evidence,evidence_rows
    from touch_physics import detect_touches
    from touch_decoder import decode_variable
    from gap_solver.materialization_control import materialize_abstentions
    records=[]
    write_new(PRIVATE/(phase+'-entry.json'),dict(configs=configs,ids=ids,freeze_commit=commit))
    for cid in ids:
        case=load_evaluation(cid,bindings[cid])
        for regime,frames in regimes(case['frames']):
            base,costs,periods,usable,_=prepare_evidence(frames,[],0,32)
            events={theta:detect_touches(frames,theta) for theta in sorted({c['theta'] for c in configs})}
            reference=case['reference']()
            control=read(PUBLIC/'control'/f'{cid}-{regime}.json')['control']
            for config in configs:
                key=cid+'-'+regime+'-'+config_id(config);claim(PRIVATE,phase,key)
                rows,costs=evidence_rows(base,periods,usable,events[config['theta']],config['beta'],config['c_touch'])
                latent=decode_variable(rows,periods,usable,costs);labels=materialize_abstentions(latent,periods)
                result=score(reference,labels,frames)
                row=dict(case_id=cid,regime=regime,config=config,control=control,candidate=result,freeze_commit=commit,
                    freeze_sha256=sha(PUBLIC/'freeze.json'),touch_counts={kind:{team:sum(e.kind==kind and e.team==team for e in events[config['theta']]) for team in ('H','A','')} for kind in ('kink','reacquire')},
                    labels_sha256=hashlib.sha256(''.join(labels).encode()).hexdigest())
                write_new(PUBLIC/phase/(key+'.json'),row);records.append(row)
                print(json.dumps(dict(phase=phase,completed=len(records),maximum=LIMITS[phase],case_id=cid,regime=regime,config=config)),flush=True)
    return records


def development_run():
    frozen,bindings,commit=checked_freeze()
    if not read(PUBLIC/'control-reproduction.json')['passed']:raise ValueError('Control reproduction gate required')
    ids=frozen['development'];controls=[read(p) for p in sorted((PUBLIC/'control').glob('*.json'))]
    records=candidate_phase('development',GRID,ids,bindings,commit)
    summaries=[]
    for config in GRID:
        rows=[r for r in records if r['config']==config]
        summaries.append(dict(config=config,means=means_for(rows,ids,'candidate')))
    control=means_for(controls,ids,'control');selected=select_config(summaries,control)
    receipt=dict(freeze_commit=commit,control=control,configurations=summaries,selected=selected,
        decision='Reject' if selected is None else 'selected_for_single_confirmation',scoring_calls=len(records),fresh_holdout=False)
    write_new(PUBLIC/'selection.json',receipt)
    return receipt


def confirmation_run():
    frozen,bindings,commit=checked_freeze();selection=read(PUBLIC/'selection.json');selected=selection['selected']
    if selected is None:raise ValueError('Development rejected; confirmation prohibited')
    ids=frozen['confirmation'];records=candidate_phase('confirmation',[selected],ids,bindings,commit)
    means={r:dict(control=means_for(records,ids,'control')[r],candidate=means_for(records,ids,'candidate')[r]) for r in REGIMES}
    safeguards_result=safeguards(records)
    providers=[]
    for cohort in ('skillcorner','dfl','wcsf'):
        subset=[cid for cid in ids if cid.startswith(cohort+'-')]
        a=means_for(records,subset,'control');b=means_for(records,subset,'candidate')
        providers.extend(dict(provider=cohort,regime=r,control=a[r],candidate=b[r],delta=b[r]-a[r]) for r in REGIMES)
    no_decline=all(r['delta']>=0 for r in providers if r['regime']=='natural')
    receipt=dict(freeze_commit=commit,selected=selected,means=means,providers=providers,safeguards=safeguards_result,
        natural_provider_no_decline=no_decline,decision=classify(means,safeguards_result['passed'],no_decline),
        scoring_calls=len(records),fresh_holdout=False,automatic_promotion=False)
    write_new(PUBLIC/'decision.json',receipt)
    return receipt


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=('freeze','control','development','confirmation'))
    args=parser.parse_args()
    action={'freeze':freeze,'control':control_run,'development':development_run,'confirmation':confirmation_run}[args.command]
    try:result=action()
    except Exception as error:
        PRIVATE.mkdir(parents=True,exist_ok=True)
        import traceback
        path=PRIVATE/(args.command+'-failure-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')+'.log')
        with path.open('x',encoding='utf-8') as handle:traceback.print_exc(file=handle)
        raise SystemExit('Touch experiment stopped: '+type(error).__name__+'; failure retained privately. No retry or budget reset.') from None
    print(json.dumps(result,sort_keys=True,allow_nan=False),flush=True)

if __name__=='__main__':main()
