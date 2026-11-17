"""Check delivered review coverage and saved verification receipts."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import re
import subprocess

ROOT = Path(__file__).resolve().parent


def read(name):
    return json.loads((ROOT / name).read_text(encoding='utf-8'))


def git(*args):
    return subprocess.check_output(['git', '--git-dir=' + str(ROOT / 'mirror.git'), *args]).decode().strip()


def main():
    before, after = read('repository-inventory-initial.json'), read('repository-inventory.json')
    branches = lambda value: {r['name']: r['commit']['sha'] for r in value['branches']}
    prs = lambda value: [(r['detail']['number'], r['detail']['state'], r['detail']['merged'],
        r['detail']['head']['sha'], r['detail']['base']['sha']) for r in value['pull_requests']]
    replay = read('external-score-replay.json')
    proof = read('delivery-and-rebuild-verification.json')
    interval = read('conditional-interval-verification.json')
    runtime = read('.tmp/runtime-temp-v2/results.json')
    report = (ROOT / 'VERIFIED-AUDIT-RESPONSE.md').read_text(encoding='utf-8')
    test_log = (ROOT / 'full-suite.log').read_text(encoding='utf-8')
    prior = json.loads((ROOT.parent / 'next-phase-notes/ownership-council/completion-audit.json').read_text(encoding='utf-8'))
    current = 'cee674190775e9356745f461ba1561e9f2a46f7e'
    audit = 'f426c0e542c1ffdab1296531bdcf5ff0af9d7405'
    diff = git('diff', '--name-status', current, audit).splitlines()
    claim_rows = [line for line in report.splitlines() if line.startswith('| ') and '**' in line]
    checks = {
        'all_three_remote_branch_heads_unchanged': branches(before) == branches(after) and len(branches(after)) == 3,
        'all_pr_states_unchanged': prs(before) == prs(after) and len(prs(after)) == 1,
        'requested_read_only_account': after['authenticated_login'].casefold() == 'the-leonjr' and not after['remote_mutations'],
        'all_21_reachable_commits_indexed': int(git('rev-list','--all','--count')) == 21 and (ROOT / 'history-index.json').is_file(),
        'audit_is_nine_added_artifacts_only': len(diff) == 9 and all(line.startswith('A\tdocs/competitor-audit-2026-11-08/') for line in diff),
        'all_three_tip_snapshots_git_identical': [v['tracked_blobs_equal'] for v in proof['snapshot_integrity'].values()] == [309,38,318],
        'full_audit_and_common_brief_available': len((ROOT / 'audit/FULL-COUNCIL-AUDIT.md').read_text(encoding='utf-8').splitlines()) == 780,
        'three_domain_verification_reports_delivered': all((ROOT / 'findings' / name).stat().st_size > 10000 for name in ('runtime.md','evidence.md','history-delivery.md')),
        'full_suite_evidence': 'Ran 341 tests' in test_log and 'OK (skipped=6)' in test_log and 'FAILED' not in test_log,
        'all_78_external_scores_reproduce': replay['all_published_metrics_reproduce'] and replay['case_receipts_checked'] == 26 and replay['variant_scoring_replays'] == 78,
        'all_case_supplementary_metrics_reproduce': all(all(row[k] for k in ('aggregate_metrics_match','dead_interval_counts_match','boundary_metrics_match','input_strata_match')) for row in replay['cases']),
        'replay_scope_explicit': not any(replay[k] for k in ('raw_acquisition_rebuilt','independent_provider_truth_verified','new_holdout','target_data_used','model_fitting')),
        'exact_conditional_interval_evidence': interval['compositions'] == 6435 and interval['ordered_skillcorner_samples'] == 16777216 and interval['lower'] > 0 and not interval['new_holdout'],
        'optimizer_mechanism_verified': runtime['brute_force_optimal_paths_checked'] == 60,
        'cache_rebuild_mechanism_verified': proof['synthetic_rebuild']['equal_semantic_arrays'] == 25 and proof['synthetic_rebuild']['all_three_container_hashes_differ'],
        'audit_delivery_defects_verified': len(proof['audit_manifest_checks']) == 7 and all(x['single_trailing_crlf_explains_difference'] for x in proof['audit_manifest_checks']) and all(proof['missing_declared_verification_artifacts'].values()),
        'prior_council_and_plan_complete_not_path_implementation': prior['status'] == 'complete' and not prior['predictor_changed'] and 'deeper path instrument not built' in prior['scope'],
        'dispositions_priorities_reasoning_limitations_written': len(claim_rows) >= 25 and all(text in report for text in ('Material claim ledger','Actual priority order','Main limitation','What history tells us','Status of the preceding Council')),
    }
    expected = {
        'ball-gap-work/docs/superpowers/specs/2026-11-08-ownership-path-diagnosis-design.md': prior['approved_design_sha256'],
        'ball-gap-work/docs/superpowers/plans/2026-11-08-ownership-path-diagnosis.md': prior['implementation_plan_sha256'],
    }
    checks['approved_design_and_written_plan_preserved'] = all(hashlib.sha256((ROOT.parent / name).read_bytes()).hexdigest() == value for name,value in expected.items())
    # Verify pinned links into this repository identify existing blobs and valid line bounds.
    links = re.findall(r'https://github\.com/hannannoor/messis-foot/blob/([0-9a-f]{40})/([^\s)#]+)(?:#L(\d+)(?:-L(\d+))?)?', report)
    for commit,path,first,last in links:
        data = subprocess.check_output(['git','--git-dir='+str(ROOT/'mirror.git'),'show',commit+':'+path])
        if first:
            assert 1 <= int(first) <= int(last or first) <= len(data.splitlines()), (path,first,last)
    checks['pinned_local_repository_links_verified'] = len(links) >= 5
    missing = [key for key,value in checks.items() if not value]
    assert not missing, missing
    files = ['VERIFIED-AUDIT-RESPONSE.md','findings/runtime.md','findings/evidence.md','findings/history-delivery.md',
        'external-score-replay.json','conditional-interval-verification.json','delivery-and-rebuild-verification.json',
        'verify_delivery_and_rebuild.py','verify_conditional_interval.py','verify_review_completion.py']
    output = dict(status='complete',checked_at_utc=datetime.now(timezone.utc).isoformat(),checks=checks,
        checks_passed=len(checks),pinned_repository_links_checked=len(links),
        artifact_sha256={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in files},
        production_changes=False,new_target_outputs=False,new_model_fitting=False,remote_mutations=False,
        next_engineering_work='bounded cadence/velocity-availability experiment; not implemented by this review',
        scientific_gate='genuinely unused licensed full-state evidence; not supplied by reused regression matches')
    (ROOT/'completion-audit.json').write_text(json.dumps(output,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(status=output['status'],checks_passed=len(checks),pinned_links_checked=len(links),remote_mutations=False,production_changes=False)))


if __name__ == '__main__':
    main()
