"""Freeze the reviewed selected challenger before any final test score is opened."""
import argparse,json
from datetime import datetime,timezone
from pathlib import Path
from select_temporal_recovery import CODE,ROOT,WORK,sha,write_json,protocol,verify_selection_evidence,feature_sources
from gap_solver.temporal_protocol import digest,load_temporal_frozen


def cache_source_identity(path):
    value=json.loads(Path(path).read_text())
    if value.get('schema_version')!=2:raise ValueError('Invalid frozen cache-source contract')
    return {key:value[key] for key in ('schema_version','match_id','position_regime','input_identity','adapter_sources')}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--review',type=Path,required=True);args=parser.parse_args()
    if not args.review.is_file():parser.error('fresh whole-change review receipt is required')
    destination=WORK/'frozen'
    if (destination/'freeze-manifest.json').exists():
        load_temporal_frozen(destination,CODE);print('Preserved existing verified temporal freeze.');return
    selection=json.loads((WORK/'selection.json').read_text());draft=json.loads((WORK/'trained-draft.json').read_text())
    verify_selection_evidence(selection)
    if selection['draft_sha256']!=sha(WORK/'trained-draft.json') or selection['final_test_scored'] is not False:raise ValueError('invalid pre-test selection')
    selected=selection['selected'];policy=selected['policy']
    artifact=dict(schema_version=1,model=draft['model'],transition_cost=draft['transition_cost'],
        temperature=draft['temperatures'][str(policy['switch_multiplier'])],policy=policy,
        eligibility=selection['eligibility'],validation_passed=selected['gate']['passes'],validation_gate=selected['gate'],
        split=protocol()['split'],source_revision=protocol()['revision'],reference_scope='known in-play H/A only',
        license=protocol()['license'],attribution=protocol()['attribution'],training=draft['training'],
        feature_sources=feature_sources(),training_source_receipt=draft['feature_sources'],local_full_state_validated=False)
    names=[p.relative_to(CODE).as_posix() for p in (CODE/'gap_solver').glob('*.py')]
    names+=['select_temporal_recovery.py','evaluate_temporal_final.py','freeze_temporal.py']
    manifest=dict(schema_version=1,frozen_before_final_test=True,frozen_at_utc=datetime.now(timezone.utc).isoformat(),
        artifact_sha256=digest(artifact),source_sha256={p:sha(CODE/p) for p in sorted(names)},split=protocol()['split'],
        source_revision=protocol()['revision'],source_cache_sha256={str(m):sha(ROOT/'cache'/f'{m}-detected.metadata.json') for ms in protocol()['split'].values() for m in ms},
        source_cache_identity={str(m):cache_source_identity(ROOT/'cache'/f'{m}-detected.metadata.json') for ms in protocol()['split'].values() for m in ms},
        selection_sha256=sha(WORK/'selection.json'),validation_receipts=selection['validation_receipts'],draft_sha256=sha(WORK/'trained-draft.json'),review_sha256=sha(args.review),
        review_file=args.review.name,initial_blind_audit_sha256=sha(CODE/'docs/strategy-blind-audit-v1.md'))
    write_json(destination/'temporal-selected.json',artifact);write_json(destination/'freeze-manifest.json',manifest)
    load_temporal_frozen(destination,CODE)
    print('Frozen '+digest(artifact)+'; '+artifact['eligibility']+'; final test scores unopened.',flush=True)


if __name__=='__main__':main()
