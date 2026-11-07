"""Guarded entry point for the preserved, already-scored accuracy experiment."""
import argparse,json
from concurrent.futures import ProcessPoolExecutor,as_completed
from pathlib import Path
import numpy as np
from accuracy_evidence import (engine,EvidenceGuard,RAW_PREPARE,RAW_SCORE,RAW_SELECT,RAW_SUMMARIZE,
    RAW_LOAD_CASE,assert_public_report,boundary_summary,portable_require_files)
from gap_solver.accuracy_protocol import digest,hash_files,SPLITS

GUARD=EvidenceGuard()
score_heads=engine.score_heads
four_from_scores=engine.four_from_scores
aggregate_metrics=engine.aggregate_metrics


def load_freeze():return GUARD.core()


def prepare_one(cohort,match):
    core=GUARD.core();portable_require_files(core['input_sha256'][f'{cohort}-{match}'],engine.input_paths(cohort,match))
    return RAW_PREPARE(cohort,match)


def score_one(stage,cohort,match):
    core=GUARD.core()
    if stage=='regression':GUARD.verified_selection(core)
    return RAW_SCORE(stage,cohort,match)


def select():
    core=GUARD.core();GUARD.verified_receipts('validation',core)
    if (engine.REPORTS/'selection.json').exists():GUARD.verified_selection(core)
    return RAW_SELECT()


def summarize():
    GUARD.verified_summary_inputs();return RAW_SUMMARIZE()


def source_check():
    path=engine.REPORTS/'verification-source.json'
    if not path.exists():raise ValueError('Missing committed verification-source manifest')
    value=json.loads(path.read_text());portable_require_files(value['source_sha256'],{name:engine.ROOT/name for name in value['source_sha256']})
    if value['original_experiment_sha256']!=digest(GUARD.core()):raise ValueError('Verification wrapper points at another experiment')
    portable_require_files(value['original_scored_receipt_sha256'],{name:engine.ROOT/name for name in value['original_scored_receipt_sha256']})
    portable_require_files({'selection':value['original_selection_file_sha256'],'summary':value['original_summary_file_sha256']},
        {'selection':engine.REPORTS/'selection.json','summary':engine.REPORTS/'summary.json'})


def supplemental_one(stage,cohort,match):
    core=GUARD.core();selected=GUARD.verified_selection(core);result=[]
    for regime in ('natural','masked'):
        arrays,record=RAW_LOAD_CASE(cohort,match,regime,core);gt,periods=engine.reference(cohort,match)
        if not np.array_equal(periods,arrays['periods']):raise ValueError('Boundary reference grid differs')
        latent=engine.decode_soft(engine.soft_emissions(arrays['supports'],arrays['motion_scores'],selected['weight']),periods,arrays['usable'],selected['switch_cost'])
        pred=engine.encode(engine.materialize_abstentions(latent,periods))
        result.append(dict(stage=stage,cohort=cohort,match=match,regime=regime,score_archive_sha256=record['archive_sha256']['scores'],
            boundary_metrics={'agreement-plus-carry':boundary_summary(gt,arrays['agreement-plus-carry'],periods),selected['selected_id']:boundary_summary(gt,pred,periods)}))
    return result


def boundaries(workers):
    core=GUARD.core();selected=GUARD.verified_selection(core);GUARD.verified_summary_inputs(core)
    jobs=[(stage,c,m) for stage,groups in SPLITS.items() for c,ids in groups.items() for m in ids];cases=[]
    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures=[pool.submit(supplemental_one,*job) for job in jobs]
        for future in as_completed(futures):cases.extend(future.result())
    cases.sort(key=lambda r:(r['stage'],r['cohort'],str(r['match']),r['regime']))
    result=dict(schema_version=1,experiment_sha256=digest(core),selection_sha256=digest(selected),fresh_holdout=False,
        parameter_reselection_performed=False,units='latency in canonical25Hz frames and seconds; no event locations',cases=cases)
    assert_public_report(result);engine.write_report(engine.REPORTS/'boundary-diagnostics.json',result)
    print('Boundary diagnostics complete: '+str(len(cases))+' cases; frozen winner and agreement-plus-carry only',flush=True)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('stage',choices=['freeze','prepare','validate','select','regress','summarize','verify','boundaries']);p.add_argument('--workers',type=int,default=2);a=p.parse_args()
    source_check()
    if a.stage=='freeze':engine.freeze();return
    if a.stage=='select':select();return
    if a.stage=='summarize':summarize();return
    if a.stage=='verify':
        GUARD.verified_summary_inputs();print('Frozen models, inputs, archives, validation-derived selection and all scored receipts verified');return
    if a.stage=='boundaries':boundaries(a.workers);return
    stages=('validation','regression') if a.stage=='prepare' else (('validation',) if a.stage=='validate' else ('regression',))
    jobs=[(stage,c,m) for stage in stages for c,ids in SPLITS[stage].items() for m in ids]
    with ProcessPoolExecutor(max_workers=a.workers) as pool:
        futures=[pool.submit(prepare_one,c,m) if a.stage=='prepare' else pool.submit(score_one,stage,c,m) for stage,c,m in jobs]
        for future in as_completed(futures):print(future.result(),flush=True)


# Ensure the old engine's internal re-entry (including ProcessPool children) also
# passes the new checks; raw inference functions and frozen score evidence remain.
engine.load_freeze=load_freeze
engine.prepare_one=prepare_one
engine.score_one=score_one
engine.select=select
engine.summarize=summarize

if __name__=='__main__':main()
