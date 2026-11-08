"""Reproducible external development/calibration/validation; never reads test scores."""
import argparse
from concurrent.futures import ProcessPoolExecutor,as_completed
from datetime import datetime,timezone
import ast,hashlib,itertools,json,math
from pathlib import Path
import numpy as np

from gap_solver.core import infer
from gap_solver.frozen_protocol import load_frozen
from gap_solver.skillcorner import load_motion_cache
from gap_solver.temporal import (MOTION_FEATURES,PortableBoosted,TemporalPolicy,mask_motion_frames,
    decode_team_sequence,apply_temporal_policy,anchor_context)
from gap_solver.temporal_development import (feature_cases,training_sample,codes,decisions,
    ensemble_scores,symmetric_scores,endpoint_predictions)
from gap_solver.temporal_selection import export_boosted,fit_temperature,validation_gate
from gap_solver.temporal_metrics import compare_temporal
from gap_solver.temporal_protocol import evidence_identity,require_evidence
from gap_solver.temporal_diagnostics import eligibility_diagnostics

CODE=Path(__file__).resolve().parent
ROOT=CODE.parent/'independent-reference'
WORK=ROOT/'temporal'
POLICIES=[TemporalPolicy(confidence=c,max_gap_s=g,switch_multiplier=m)
          for c,g,m in itertools.product((.9,.95,.975),(2.,5.,10.),(.5,1.,2.))]


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write_json(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temporary=Path(str(path)+'.new');temporary.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n',encoding='utf-8');temporary.replace(path)
def policy_id(policy):return 'c{}-g{}-m{}'.format(policy.confidence,policy.max_gap_s,policy.switch_multiplier)
def protocol():return json.loads((CODE/'benchmark/skillcorner/protocol.json').read_text())
def function_digest(path,name):
    node=next(n for n in ast.parse(Path(path).read_text(encoding='utf-8')).body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name)
    return hashlib.sha256(ast.dump(node,include_attributes=False).encode()).hexdigest()
def feature_sources():
    files=['motion.py','skillcorner.py','temporal.py','tactical.py','tactical_model.py','core.py']
    result={name:sha(CODE/'gap_solver'/name) for name in files}
    for file,name in [('temporal_development.py','feature_cases'),('temporal_selection.py','contiguous_mask')]:
        result[file+'::'+name]=function_digest(CODE/'gap_solver'/file,name)
    return result


def recertify_feature_cases():
    """One migration: prove unchanged feature functions against preserved pre-review sources."""
    preserved=CODE/'.superpowers/sdd/temporal-recovery/pre-review-source';new=feature_sources()
    for path in sorted((WORK/'cases').glob('*.json')):
        record=json.loads(path.read_text());old=record['identity']['sources']
        if old==new:continue
        for name in ('temporal_development.py','temporal_selection.py'):
            if sha(preserved/name)!=old[name]:raise ValueError('Missing original feature-source proof')
        for file,name in [('temporal_development.py','feature_cases'),('temporal_selection.py','contiguous_mask')]:
            if function_digest(preserved/file,name)!=new[file+'::'+name]:raise ValueError('Feature behavior changed; rebuild required')
        for name,value in new.items():
            if '::' not in name and old.get(name)!=value:raise ValueError('Prediction source changed; rebuild required')
        for name,value in record['files'].items():
            if sha(WORK/name)!=value:raise ValueError('Feature arrays changed during recertification')
        record['dependency_migration']=dict(previous_sources=old,proof='unchanged full prediction files and exact ASTs of feature_cases/contiguous_mask; arrays rehashed',new_sources=new)
        record['identity']['sources']=new;write_json(path,record)
    print('Recertified unchanged feature arrays; scoring changes require validation rescoring, no refit.',flush=True)


def validation_identity(match,name):
    sources={p.relative_to(CODE).as_posix():p for p in (CODE/'gap_solver').glob('*.py')}
    sources['select_temporal_recovery.py']=CODE/'select_temporal_recovery.py'
    result=evidence_identity(sources,{'source_cache':ROOT/'cache'/f'{match}-detected.metadata.json',
        'feature_cases':WORK/'cases'/f'{match}-detected.json'},sha(WORK/'trained-draft.json'))
    result.update(match=match,mask_regime=name);return result


def load_validation(match,name):
    value=json.loads((WORK/'validation'/f'{match}-{name}.json').read_text())
    require_evidence(value,validation_identity(match,name));return value


def verify_selection_evidence(selection):
    if selection['draft_sha256']!=sha(WORK/'trained-draft.json'):raise ValueError('selection draft mismatch')
    expected={}
    for match in protocol()['split']['validation']:
        for name in ('natural','masked'):
            load_validation(match,name);file=f'{match}-{name}.json';expected[file]=sha(WORK/'validation'/file)
    if selection.get('validation_receipts')!=expected:raise ValueError('Selection evidence changed since selection')


def prepare_one(match,regime='detected'):
    prefix=ROOT/'cache'/f'{match}-{regime}';destination=WORK/'cases'/f'{match}-{regime}'
    identity=dict(input_cache_sha256=sha(str(prefix)+'.metadata.json'),sources=feature_sources(),seed=1729+int(match))
    meta=Path(str(destination)+'.json')
    if meta.exists():
        existing=json.loads(meta.read_text())
        if existing['identity']==identity and all(sha(WORK/path)==digest for path,digest in existing['files'].items()):
            return f'{match}: verified existing {regime} feature cases'
    data=load_motion_cache(prefix);cases=feature_cases(data.frames(),identity['seed']);files={}
    destination.parent.mkdir(parents=True,exist_ok=True)
    for name,arrays in cases.items():
        target=Path(str(destination)+f'-{name}.npz');temporary=Path(str(target)+'.new')
        with temporary.open('wb') as handle:np.savez_compressed(handle,**arrays)
        temporary.replace(target);files[target.relative_to(WORK).as_posix()]=sha(target)
    write_json(meta,dict(identity=identity,files=files,reference_in_feature_arrays=False))
    return f'{match}: prepared natural + masked {regime} cases ({len(data.reference)} rows)'


def load_case(match,name,regime='detected'):
    meta=json.loads((WORK/'cases'/f'{match}-{regime}.json').read_text())
    if meta['identity']['sources']!=feature_sources():raise ValueError('stale external feature implementation')
    if meta['identity']['input_cache_sha256']!=sha(ROOT/'cache'/f'{match}-{regime}.metadata.json'):raise ValueError('stale source cache')
    relative=f'cases/{match}-{regime}-{name}.npz';path=WORK/relative
    hashes={name.replace('\\','/'):value for name,value in meta['files'].items()}
    if sha(path)!=hashes[relative]:raise ValueError('external feature case content changed')
    with np.load(path,allow_pickle=False) as archive:return {key:archive[key] for key in archive.files}


def case_frames(data,case):return mask_motion_frames(data.frames(),case['mask'])


def train():
    from sklearn.ensemble import GradientBoostingClassifier
    split=protocol()['split'];xs=[];ys=[];weights=[];sources={};same=changes=0
    load_frozen(CODE.parent/'external-reference',CODE/'gap_solver')
    for match in split['development']:
        data=load_motion_cache(ROOT/'cache'/f'{match}-detected');gt=data.reference
        valid=(gt[:-1]<2)&(gt[1:]<2)&(data.periods[:-1]==data.periods[1:])&(data.periods[1:]>0)
        changes+=int((valid&(gt[:-1]!=gt[1:])).sum());same+=int((valid&(gt[:-1]==gt[1:])).sum())
        for name in ('natural','masked'):
            case=load_case(match,name);x,y,w=training_sample(case['x'],gt,case['baseline'],offset=int(match)%5)
            xs.append(x);ys.append(y);weights.append(w)
        sources[str(match)]=sha(ROOT/'cache'/f'{match}-detected.metadata.json')
    x=np.concatenate(xs);y=np.concatenate(ys);w=np.concatenate(weights);w*=len(w)/w.sum()
    classifier=GradientBoostingClassifier(n_estimators=40,max_depth=2,min_samples_leaf=150,
        learning_rate=.1,random_state=1729).fit(x,y,sample_weight=w)
    model=export_boosted(classifier);portable=PortableBoosted(model)
    checks=x[np.linspace(0,len(x)-1,min(1000,len(x)),dtype=int)]
    expected=classifier.decision_function(checks);actual=ensemble_scores(model,checks)
    np.testing.assert_allclose(actual,expected,rtol=0,atol=1e-12)
    np.testing.assert_allclose([portable.score(row) for row in checks],expected,rtol=0,atol=1e-12)
    transition_cost=math.log((same+1)/(changes+1));calibration={m:[] for m in (.5,1.,2.)}
    targets=[];cal_weights=[]
    for match in split['calibration']:
        data=load_motion_cache(ROOT/'cache'/f'{match}-detected')
        for name in ('natural','masked'):
            case=load_case(match,name);frames=case_frames(data,case);base=decisions(case['baseline'])
            scores=symmetric_scores(model,case['x']);scores[case['baseline']!=3]=0.
            selected=(data.reference<2)&(case['baseline']==3)
            if not selected.any():raise ValueError('empty calibration case')
            targets.append(data.reference[selected]);cal_weights.append(np.full(int(selected.sum()),1/int(selected.sum())))
            for multiplier in calibration:
                posterior=decode_team_sequence(scores,frames,base,transition_cost*multiplier)
                calibration[multiplier].append(np.asarray(posterior)[selected])
        sources[str(match)]=sha(ROOT/'cache'/f'{match}-detected.metadata.json')
    temperatures={str(m):fit_temperature(np.concatenate(z),np.concatenate(targets),np.concatenate(cal_weights)) for m,z in calibration.items()}
    draft=dict(schema_version=1,model=model,transition_cost=transition_cost,temperatures=temperatures,
        train_matches=split['development'],calibration_matches=split['calibration'],training_sources=sources,
        feature_sources=feature_sources(),training=dict(rows=len(x),trees=40,depth=2,min_leaf=150,learning_rate=.1,
            seed=1729,stride=5,augmentation=['identity','swap','reflection','swap+reflection'],
            weighting='equal total weight for every match/regime; only known H/A on baseline X'),
        calibration_population='known H/A baseline X, equal match/regime weights; posterior temperature per switch multiplier',
        transition_counts=dict(same=same,changes=changes),portable_parity_max_error=float(np.max(np.abs(actual-expected))),
        final_test_scored=False,created_at_utc=datetime.now(timezone.utc).isoformat())
    write_json(WORK/'trained-draft.json',draft)
    print(f'Trained fixed 40-tree candidate on {len(x)} augmented rows; calibrated only two designated matches.',flush=True)


def compare(data,frames,base,pred):
    report=compare_temporal(data.reference,codes(base),codes(pred),data.periods,frames)
    report['source_quality_gate_passed']=data.notes['phase_reconciliation']['retained_reference_fraction']>=.95
    report['source_quality']=data.notes['phase_reconciliation']
    return report


def full_endpoint_rules(frames,base,cap):
    proposal=apply_temporal_policy(frames,base,[-50.]*len(frames),TemporalPolicy(confidence=.9,max_gap_s=cap))
    return {mode:endpoint_predictions(frames,base,proposal,cap,mode=mode)[0] for mode in ('last_owner','two_sided')}


def validate_one(match,name):
    draft=json.loads((WORK/'trained-draft.json').read_text());identity=validation_identity(match,name)
    destination=WORK/'validation'/f'{match}-{name}.json'
    if destination.exists():
        previous=json.loads(destination.read_text())
        if previous['identity']==identity:return f'{match} {name}: preserved completed validation'
    data=load_motion_cache(ROOT/'cache'/f'{match}-detected');case=load_case(match,name)
    frames=case_frames(data,case);base=decisions(case['baseline']);context=anchor_context(frames)
    scores=symmetric_scores(draft['model'],case['x']);scores[case['baseline']!=3]=0.
    posteriors={m:np.asarray(decode_team_sequence(scores,frames,base,draft['transition_cost']*m))/draft['temperatures'][str(m)] for m in (.5,1.,2.)}
    result=dict(identity=identity,match=match,regime=name,candidates={},baselines={})
    # Independent fixed geometry and current frozen comparisons are retained.
    result['baselines']['geometry_vs_frozen']=compare(data,frames,infer(frames),base)
    for policy in POLICIES:
        pred=apply_temporal_policy(frames,base,posteriors[policy.switch_multiplier],policy,context)
        endpoint,matching=endpoint_predictions(frames,base,pred,policy.max_gap_s)
        report=compare(data,frames,base,pred);other=compare(data,frames,base,endpoint)
        result['candidates'][policy_id(policy)]=dict(policy=policy.__dict__,motion=report,endpoint=other,matching=matching)
    # Same policy grid for the no-decoder ablation; do not select on this table.
    for cap in (2.,5.,10.):
        policy=TemporalPolicy(confidence=.95,max_gap_s=cap)
        pred=apply_temporal_policy(frames,base,scores,policy,context)
        result['baselines'][f'no_decoder_c.95_g{cap}']=compare(data,frames,base,pred)
        for mode,pred in full_endpoint_rules(frames,base,cap).items():
            result['baselines'][f'{mode}_full_g{cap}']=compare(data,frames,base,pred)
        result.setdefault('input_eligibility',{})[str(cap)]=eligibility_diagnostics(frames,base,policy)
    write_json(destination,result)
    return f'{match} {name}: completed all 27 fixed policies and no-decoder ablations'


def select():
    split=protocol()['split'];values={}
    for match in split['validation']:
        for name in ('natural','masked'):
            values[match,name]=load_validation(match,name)
    candidates=[]
    for policy in POLICIES:
        pid=policy_id(policy)
        reports=[values[m,'natural']['candidates'][pid]['motion'] for m in split['validation']]
        endpoint=[values[m,'natural']['candidates'][pid]['endpoint'] for m in split['validation']]
        masked=[values[m,'masked']['candidates'][pid]['motion'] for m in split['validation']]
        masked_endpoint=[values[m,'masked']['candidates'][pid]['endpoint'] for m in split['validation']]
        gate=validation_gate(reports,endpoint,masked,masked_endpoint)
        f1=float(np.mean([r['selected']['metrics']['spell_f1_mean'] for r in reports]))
        gain=float(np.mean([r['baseline']['coverage']['undecided_fraction']-r['selected']['coverage']['undecided_fraction'] for r in reports]))
        candidates.append(dict(policy=policy.__dict__,id=pid,gate=gate,mean_spell_f1=f1,mean_coverage_gain=gain))
    # Fixed selection order: eligible first, then mean spell F1, coverage, conservative confidence/cap.
    candidates.sort(key=lambda c:(c['gate']['passes'],c['mean_spell_f1'],c['mean_coverage_gain'],c['policy']['confidence'],-c['policy']['max_gap_s']),reverse=True)
    simple=[]
    for mode,cap in itertools.product(('last_owner','two_sided'),(2.,5.,10.)):
        name=f'{mode}_full_g{cap}'
        natural=[values[m,'natural']['baselines'][name] for m in split['validation']]
        masked=[values[m,'masked']['baselines'][name] for m in split['validation']]
        gate=validation_gate(natural,natural,masked,masked)
        for check in ('positive_hidden_recovery','bounded_false_opposing_spells','mean_spell_advantage_over_endpoint'):gate['checks'].pop(check)
        gate['passes']=all(gate['checks'].values());gate['claim']='simple rule, no motion mechanism claim; unchanged support thresholds'
        simple.append(dict(method=name,gate=gate,mean_coverage_gain=float(np.mean([r['baseline']['coverage']['undecided_fraction']-r['selected']['coverage']['undecided_fraction'] for r in natural])),
            mean_spell_f1=float(np.mean([r['selected']['metrics']['spell_f1_mean'] for r in natural]))))
    if any(rule['gate']['passes'] for rule in simple):raise ValueError('A simpler rule qualifies; explicitly select and freeze its implementation before any test score')
    result=dict(schema_version=1,draft_sha256=sha(WORK/'trained-draft.json'),validation_matches=split['validation'],simple_alternatives=simple,
        validation_receipts={f'{m}-{n}.json':sha(WORK/'validation'/f'{m}-{n}.json') for m in split['validation'] for n in ('natural','masked')},
        candidates=candidates,selected=candidates[0],eligibility='eligible' if candidates[0]['gate']['passes'] else 'rejected_before_final_test',
        final_test_scored=False,selection_order='eligible; mean team-spell F1; coverage; confidence; shorter cap',
        warning='No gate relaxed. Rejected candidate can receive diagnostic final evaluation only, never local deployment.')
    write_json(WORK/'selection.json',result)
    print(json.dumps(dict(selected=result['selected'],eligibility=result['eligibility']),indent=2),flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('stage',choices=['prepare','train','validate','select','recertify'])
    parser.add_argument('--workers',type=int,default=2);args=parser.parse_args()
    if args.stage=='prepare':
        matches=sum((protocol()['split'][s] for s in ('development','calibration','validation')),[])
        with ProcessPoolExecutor(max_workers=args.workers) as pool:
            futures=[pool.submit(prepare_one,m) for m in matches]
            for future in as_completed(futures):print(future.result(),flush=True)
    elif args.stage=='train':train()
    elif args.stage=='validate':
        with ProcessPoolExecutor(max_workers=args.workers) as pool:
            futures=[pool.submit(validate_one,m,n) for m in protocol()['split']['validation'] for n in ('natural','masked')]
            for future in as_completed(futures):print(future.result(),flush=True)
    elif args.stage=='recertify':recertify_feature_cases()
    else:select()


if __name__=='__main__':main()
