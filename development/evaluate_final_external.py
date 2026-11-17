"""Verify frozen-runtime parity, then score the two predeclared final external matches."""
from datetime import datetime,timezone
import json
from pathlib import Path
import numpy as np

from gap_solver.frozen_protocol import load_frozen
from gap_solver.external import load_cache
from gap_solver.tactical import Policy,infer_tactical
from gap_solver.core import infer,summary
from gap_solver.selection import ball_mask,mask_frames
from gap_solver.benchmark import evaluate_external,compare_external,evaluation_arrays
from gap_solver import official_metrics


ROOT=Path(__file__).resolve().parent.parent/'external-reference'
CODE=Path(__file__).resolve().parent/'gap_solver'


def codes(decisions):
    return np.fromiter(('HADX'.index(d.label) for d in decisions),dtype=np.uint8,count=len(decisions))


def score(data,frames,artifact,bootstrap=False):
    old=infer(frames);new=infer_tactical(frames,artifact['model'],Policy(**artifact['policy']))
    before,after=codes(old),codes(new)
    base=evaluate_external(data.reference,before,data.periods)
    selected=evaluate_external(data.reference,after,data.periods)
    if bootstrap:
        a,b=evaluation_arrays(data.reference,before,data.periods)
        _,c=evaluation_arrays(data.reference,after,data.periods)
        base['metrics']=official_metrics.evaluate(a,b,bootstrap_n=1000)
        selected['metrics']=official_metrics.evaluate(a,c,bootstrap_n=1000)
    return dict(baseline=base,selected=selected,change=compare_external(data.reference,before,after,data.periods),
                selected_summary=summary(frames,new))


def main():
    artifact,manifest=load_frozen(ROOT,CODE)
    destination=ROOT/'reports'/'final-heldout.json'
    if destination.exists():
        output=json.loads(destination.read_text(encoding='utf-8'))
        if output.get('artifact_sha256')!=manifest['artifact_sha256']:
            raise ValueError('Existing held-out results belong to a different frozen model')
        if output.get('complete'):
            print('Held-out scoring already complete for this frozen model; preserved existing results.',flush=True)
            return
    else:
        # No final-test target is opened before this runtime validation reproduces selection.
        for index,match in enumerate(manifest['split']['validation']):
            data=load_cache(ROOT/'cache'/match)
            original=data.frames()
            for expected in artifact['selection']['validation']:
                if expected['match']!=match:
                    continue
                rate=expected['mask_rate']
                frames=original if rate==0 else mask_frames(original,ball_mask(data.periods,rate,2729+index))
                actual=score(data,frames,artifact)
                for name in ('confusion','spell_f1_mean','macro_f1'):
                    if actual['selected']['metrics'][name]!=expected['report']['metrics'][name]:
                        raise ValueError('Frozen portable inference differs from its validation result: '+name)
                if actual['selected']['coverage']!=expected['report']['coverage']:
                    raise ValueError('Frozen runtime coverage differs from validation')
                print('Verified selected-runtime validation parity: {} mask {}'.format(match,rate),flush=True)
        output=dict(schema_version=1,artifact_sha256=manifest['artifact_sha256'],complete=False,
                    model_frozen_before_test=True,started_at_utc=datetime.now(timezone.utc).isoformat(),matches={})
        destination.write_text(json.dumps(output,indent=2)+'\n',encoding='utf-8')
    for index,match in enumerate(manifest['split']['test']):
        data=load_cache(ROOT/'cache'/match)
        original=data.frames()
        cases=output['matches'].setdefault(match,{})
        for rate in (0.,.1,.3,.5):
            key='natural' if rate==0 else 'ball_mask_'+str(rate)
            if key in cases:
                continue
            frames=original if rate==0 else mask_frames(original,ball_mask(data.periods,rate,3729+index))
            result=score(data,frames,artifact,bootstrap=rate==0)
            result['mask_rate']=rate
            cases[key]=result
            destination.write_text(json.dumps(output,indent=2)+'\n',encoding='utf-8')
            print('HELD OUT {} {}: spell {:.4f}->{:.4f}; X {:.2%}->{:.2%}; newly resolved correct {:.2%}'.format(
                match,key,result['baseline']['metrics']['spell_f1_mean'],result['selected']['metrics']['spell_f1_mean'],
                result['baseline']['coverage']['undecided_fraction'],result['selected']['coverage']['undecided_fraction'],
                result['change']['newly_resolved_correct_fraction'] or 0.),flush=True)
    summaries={}
    for key in ('natural','ball_mask_0.1','ball_mask_0.3','ball_mask_0.5'):
        cases=[match[key] for match in output['matches'].values()]
        summaries[key]={}
        for stage in ('baseline','selected'):
            summaries[key][stage]=dict(
                match_macro_spell_f1=float(np.mean([c[stage]['metrics']['spell_f1_mean'] for c in cases])),
                match_macro_macro_f1=float(np.mean([c[stage]['metrics']['macro_f1'] for c in cases])),
                match_macro_undecided_fraction=float(np.mean([c[stage]['coverage']['undecided_fraction'] for c in cases])))
        count=sum(c['change']['newly_resolved_frames'] for c in cases)
        correct=sum(c['change']['newly_resolved_frames']*c['change']['newly_resolved_correct_fraction'] for c in cases)
        summaries[key]['newly_resolved_correct_fraction']=correct/count if count else None
        summaries[key]['every_match_spell_f1_improved']=all(c['selected']['metrics']['spell_f1_mean']>c['baseline']['metrics']['spell_f1_mean'] for c in cases)
        summaries[key]['every_match_macro_f1_not_degraded']=all(c['selected']['metrics']['macro_f1']>=c['baseline']['metrics']['macro_f1'] for c in cases)
        summaries[key]['every_match_x_reduced']=all(c['selected']['coverage']['undecided_fraction']<c['baseline']['coverage']['undecided_fraction'] for c in cases)
    output.update(complete=True,summary=summaries,finished_at_utc=datetime.now(timezone.utc).isoformat(),
                  no_refitting_after_test=True,reference_type='external provider reference; challenge accuracy unmeasured')
    destination.write_text(json.dumps(output,indent=2)+'\n',encoding='utf-8')
    print('Completed fixed held-out protocol; no model or policy changed.',flush=True)


if __name__=='__main__':
    main()
