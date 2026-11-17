"""Fit on development only; select on validation only; freeze before any final test score."""
from dataclasses import asdict
import hashlib
from itertools import chain
import json
from pathlib import Path
from datetime import datetime,timezone

import numpy as np
from sklearn.tree import DecisionTreeClassifier

from gap_solver.external import load_cache
from gap_solver.core import infer
from gap_solver.tactical import FEATURE_NAMES,Policy,PortableTree,feature_rows,apply_policy
from gap_solver.selection import ball_mask,mask_frames,export_tree
from gap_solver.benchmark import evaluate_external,compare_external


ROOT=Path(__file__).resolve().parent.parent/'external-reference'
CODE=Path(__file__).resolve().parent


def features(frames):
    return np.fromiter(chain.from_iterable(feature_rows(frames)),dtype=np.float32,
                       count=len(frames)*len(FEATURE_NAMES)).reshape(len(frames),len(FEATURE_NAMES))


def codes(decisions):
    return np.fromiter(('HADX'.index(d.label) for d in decisions),dtype=np.uint8,count=len(decisions))


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode('utf-8')).hexdigest()


def gate(report,change,baseline):
    return (report['metrics']['spell_f1_mean']>baseline['metrics']['spell_f1_mean']
            and report['metrics']['macro_f1']>=baseline['metrics']['macro_f1']
            and report['coverage']['undecided_frames']<baseline['coverage']['undecided_frames']
            and change['newly_resolved_frames']>=250 and change['newly_resolved_intervals']>=20
            and change['newly_resolved_correct_fraction'] is not None
            and change['newly_resolved_correct_fraction']>=.9)


def main():
    if (ROOT/'frozen'/'freeze-manifest.json').exists():
        raise ValueError('Selection is already frozen. Do not refit from held-out or challenge feedback.')
    provenance=json.loads((ROOT/'provenance.json').read_text(encoding='utf-8'))
    train_x=[];train_y=[];weights=[]
    for index,match in enumerate(provenance['split']['development']):
        data=load_cache(ROOT/'cache'/match)
        original=data.frames()
        for rate in (0.,.3):
            frames=original if rate==0 else mask_frames(original,ball_mask(data.periods,rate,1729+index))
            matrix=features(frames)
            take=(np.arange(len(frames))%5==0)&(data.reference<3)
            train_x.append(matrix[take]);train_y.append(data.reference[take])
            weights.append(np.full(int(take.sum()),1./int(take.sum()),dtype=np.float64))
        print('Prepared development-only training features: '+match,flush=True)
    x=np.concatenate(train_x);y=np.concatenate(train_y);weight=np.concatenate(weights)
    del train_x,train_y,weights
    validations=[]
    for index,match in enumerate(provenance['split']['validation']):
        data=load_cache(ROOT/'cache'/match)
        original=data.frames()
        for rate in (0.,.3):
            frames=original if rate==0 else mask_frames(original,ball_mask(data.periods,rate,2729+index))
            base=infer(frames);base_codes=codes(base)
            validations.append(dict(match=match,rate=rate,data=data,frames=frames,matrix=features(frames),
                                    baseline=base,baseline_codes=base_codes,
                                    baseline_report=evaluate_external(data.reference,base_codes,data.periods)))
    records=[];eligible=[]
    for depth in (4,6):
        for leaf in (125,500):
            classifier=DecisionTreeClassifier(max_depth=depth,min_samples_leaf=leaf,random_state=1729)
            classifier.fit(x,y,sample_weight=weight)
            exported=export_tree(classifier)
            portable=PortableTree(exported)
            predictions=[]
            for value in validations:
                probabilities=classifier.predict_proba(value['matrix'])
                # Check every validation row against the exported standard-library tree.
                actual=np.asarray([portable.predict(row) for row in value['matrix']])
                if not np.allclose(actual,probabilities,rtol=0,atol=1e-12):
                    raise ValueError('Portable/runtime model parity failed')
                predictions.append(probabilities)
            for confidence in (.8,.9,.95):
                for minimum_run in (6,12):
                    policy=Policy(confidence=confidence,minimum_run_frames=minimum_run,max_gap_s=2.,bridge_s=2.)
                    details=[]
                    for value,probabilities in zip(validations,predictions):
                        decisions=apply_policy(value['frames'],zip(value['matrix'],probabilities),policy,value['baseline'])
                        prediction=codes(decisions)
                        report=evaluate_external(value['data'].reference,prediction,value['data'].periods)
                        change=compare_external(value['data'].reference,value['baseline_codes'],prediction,value['data'].periods)
                        details.append(dict(match=value['match'],mask_rate=value['rate'],report=report,change=change,
                                            baseline=value['baseline_report'],passes=gate(report,change,value['baseline_report'])))
                    candidate=dict(depth=depth,minimum_leaf=leaf,policy=asdict(policy),validation=details,
                                   eligible=all(d['passes'] for d in details))
                    records.append(candidate)
                    natural=details[0]
                    print('depth={} leaf={} gate={} run={}: spell={:.4f}; X={:.2%}; new-correct={:.3f}; eligible={}'.format(
                        depth,leaf,confidence,minimum_run,natural['report']['metrics']['spell_f1_mean'],
                        natural['report']['coverage']['undecided_fraction'],natural['change']['newly_resolved_correct_fraction'] or 0.,
                        candidate['eligible']),flush=True)
                    if candidate['eligible']:
                        key=(natural['report']['metrics']['spell_f1_mean'],natural['report']['metrics']['macro_f1'],
                             -natural['report']['coverage']['undecided_fraction'])
                        eligible.append((key,exported,candidate,classifier.feature_importances_.tolist()))
    report_path=ROOT/'reports'/'validation-selection.json'
    report_path.write_text(json.dumps(dict(candidate_grid_predeclared=True,final_test_scored=False,
                                         candidates=records),indent=2)+'\n',encoding='utf-8')
    if not eligible:
        raise ValueError('No candidate passed declared validation quality/coverage safeguards; no final test opened.')
    _,model,selected,importance=max(eligible,key=lambda item:item[0])
    artifact=dict(schema_version=1,model=model,policy=selected['policy'],selection=selected,
                  feature_importance=dict(zip(FEATURE_NAMES,importance)),
                  reference_type='external provider reference, not competition gold',
                  training_matches=provenance['split']['development'],validation_matches=provenance['split']['validation'],
                  test_matches=provenance['split']['test'],features_exclude_reference_labels=True,
                  leaf_support_is_calibrated_probability=False,training_observation_masks=[0.,.3],
                  citation=provenance['attribution'],license=provenance['license'])
    frozen=ROOT/'frozen';frozen.mkdir(exist_ok=True)
    (frozen/'tactical-selected.json').write_text(json.dumps(artifact,indent=2)+'\n',encoding='utf-8')
    source_hashes={name:hashlib.sha256((CODE/'gap_solver'/name).read_bytes()).hexdigest()
                   for name in ('tactical.py','external.py','benchmark.py','official_metrics.py','core.py','selection.py')}
    manifest=dict(artifact_sha256=digest(artifact),source_sha256=source_hashes,split=provenance['split'],
                  frozen_before_test_scores=True,frozen_at_utc=datetime.now(timezone.utc).isoformat(),
                  selection_rule='Pass natural and 30% masked validation safeguards; maximize natural spellF1, then macroF1, then coverage.',
                  validation_safeguards='spellF1 increases; macroF1 no worse; X decreases; >=250 new frames in >=20 intervals; >=90% newly resolved correctness')
    (frozen/'freeze-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print('FROZEN before final tests: '+manifest['artifact_sha256'],flush=True)
    print('Selected: '+json.dumps(dict(depth=selected['depth'],minimum_leaf=selected['minimum_leaf'],policy=selected['policy'])),flush=True)


if __name__=='__main__':
    main()
