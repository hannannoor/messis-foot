"""Live/dead sequence experiment: freeze / preflight / fit / parity / natural / stress / summarise.

Claim-on-entry ledger with fixed science caps; a separate, bounded parity category for implementation checks.
Private arrays live under PRIVATE_ROOT (outside Git); only bounded aggregates go to reports/live-dead/<run-id>.
Heavy modules are imported inside commands so the ledger and guards stay testable without match data.

    python live_dead_run.py <command> --run-id <id>
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

import live_dead_protocol as lp

ROOT = Path(__file__).resolve().parent
PRIVATE_ROOT = ROOT.parent / 'live-dead-reference'
REPORT_ROOT = ROOT / 'reports/live-dead'
BASE_COMMIT = '83b203e76bb8c5cf754e7fa3593980f4c9c1f85b'
BRANCH = 'experiment/live-dead-sequence'
PROTOCOL_DOC = 'docs/live-dead-protocol.md'
SPEC_DOC = 'docs/superpowers/specs/2026-11-14-live-dead-sequence-design.md'
PLAN_DOC = 'docs/superpowers/plans/2026-11-14-live-dead-sequence.md'
NEW_FILES_PREFIXES = ('live_dead_', 'tests/test_live_dead_', PROTOCOL_DOC, 'docs/superpowers/', 'reports/live-dead/')
HISTORICAL_DIR = ROOT / 'reports/memory-ablation/2026-11-09-v3'
PRIMARY_NATURAL_MEAN = 0.551816
PITCH = (105.3, 68.0)

CAPS = dict(fit=2, prediction=123, score=123, decoder_pass=246, feature_pass=213)
PARITY_CAP = 36
FIT_ORDER = ('instant', 'temporal')
PUBLIC_NAMES = dict(fit='fits', prediction='stream_runs', score='score_bundles', feature_pass='feature_tree_passes',
                    decoder_pass='decoder_passes', parity='parity_checks')
STRESS_REGIMES = ('jitter', 'degrade')
RESTART_CASES = ('dfl-J03WR9', 'dfl-J03WN1', 'dfl-J03WOH', 'dfl-J03WOY', 'wcsf-used-match')
_SAFE = re.compile(r'[A-Za-z0-9_.:/-]{1,200}')


class BudgetError(ValueError):
    pass


def now():
    return datetime.now(timezone.utc)


def deadline():
    lp.enforce_deadline(now())


def utc():
    return now().isoformat()


def safe_run_id(run_id):
    if not isinstance(run_id, str) or not re.fullmatch('[a-z0-9][a-z0-9-]{0,63}', run_id):
        raise ValueError('Unsafe run ID')
    return run_id


class Ledger:
    """Claims are files created exclusively; cumulative across run ids and never refunded."""

    def __init__(self, claims, access):
        self.claims = Path(claims)
        self.access = Path(access)
        self.claims.mkdir(parents=True, exist_ok=True)
        self.access.parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _parity_allowed(identity):
        parts = identity.split('/')
        if len(parts) != 3:
            return False
        safe_run_id(parts[1])
        kind, item = parts[0], parts[2]
        return ((kind == 'exporter' and item in FIT_ORDER)
                or (kind == 'training-alignment' and item in lp.TRAIN_MATCHES)
                or (kind in ('release', 'disabled') and item in lp.CASES))

    def count(self, kind):
        return len(list(self.claims.glob(kind + '--*.json')))

    def claim(self, kind, identity):
        if kind not in CAPS and kind != 'parity':
            raise BudgetError('Unknown claim kind')
        if not isinstance(identity, str) or not _SAFE.fullmatch(identity) or '__' in identity or '..' in identity:
            raise BudgetError('Unsafe claim identity')
        if kind == 'parity' and not self._parity_allowed(identity):
            raise BudgetError('Unknown parity identity')
        if kind == 'fit':
            if identity not in FIT_ORDER:
                raise BudgetError('Unknown fit')
            if identity == 'temporal' and not (self.claims / 'fit--instant.json').exists():
                raise BudgetError('Instant fit must be claimed first')
        cap = PARITY_CAP if kind == 'parity' else CAPS[kind]
        if self.count(kind) >= cap:
            raise BudgetError('Budget exhausted: ' + kind)
        path = self.claims / (kind + '--' + identity.replace('/', '__') + '.json')
        try:
            with path.open('x', encoding='utf-8') as handle:
                handle.write(json.dumps(dict(kind=kind, identity=identity, utc=utc()), sort_keys=True) + '\n')
        except FileExistsError:
            raise BudgetError('Already claimed (no reruns): ' + kind + ' ' + identity) from None
        self.event(kind + '_entry', identity=identity)

    def event(self, event, **fields):
        with self.access.open('a', encoding='utf-8') as handle:
            handle.write(json.dumps(dict(event=event, utc=utc(), **fields), sort_keys=True) + '\n')

    def usage(self):
        out = {PUBLIC_NAMES[k]: self.count(k) for k in CAPS}
        out[PUBLIC_NAMES['parity']] = self.count('parity')
        return out


# ----- paths and I/O --------------------------------------------------------------------------------

def run_paths(run_id):
    safe_run_id(run_id)
    return PRIVATE_ROOT / run_id, REPORT_ROOT / run_id


def open_ledger(run_id):
    private, _ = run_paths(run_id)
    private.mkdir(parents=True, exist_ok=True)
    return Ledger(PRIVATE_ROOT / 'claims', private / 'access.jsonl')


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()


def file_sha(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as handle:
        for block in iter(lambda: handle.read(1 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def store_exact(path, value, *, public=True):
    from accuracy_evidence import assert_public_report
    if public:
        assert_public_report(value)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as handle:
        handle.write(canonical(value))
    if path.read_bytes() != canonical(value):
        raise ValueError('Persisted canonical bytes differ')


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def require(public, name, ok):
    path = public / name
    if not path.is_file():
        raise ValueError('Missing prerequisite ' + name)
    value = read_json(path)
    if value.get('status') not in ok:
        raise ValueError(f'Prerequisite {name} did not pass: {value.get("status")}')
    return value


def array_identity(arrays):
    from memory_ablation_training import semantic_digest
    value = {key: semantic_digest(array) for key, array in sorted(arrays.items())}
    return hashlib.sha256(canonical(value)).hexdigest()


def save_arrays(path, arrays):
    import numpy as np
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as handle:
        np.savez_compressed(handle, **arrays)
    return array_identity(arrays)


def load_arrays(path, expected_identity):
    import numpy as np
    with np.load(path, allow_pickle=False) as data:
        arrays = {key: data[key] for key in data.files}
    if array_identity(arrays) != expected_identity:
        raise ValueError('Private array identity differs: ' + Path(path).name)
    return arrays


def encode(labels):
    import numpy as np
    return np.asarray(['HADX'.index(s) for s in labels], dtype=np.uint8)


# ----- repository, environment, inputs, freeze --------------------------------------------------------

def git(*args):
    import subprocess
    return subprocess.check_output(('git',) + args, cwd=ROOT, text=True).strip()


def foreign_changes(names):
    return [name for name in names if not name.startswith(NEW_FILES_PREFIXES)]


def check_repository():
    import subprocess
    if git('rev-parse', '--abbrev-ref', 'HEAD') != BRANCH:
        raise ValueError('Wrong branch')
    if subprocess.run(('git', 'merge-base', '--is-ancestor', BASE_COMMIT, 'HEAD'), cwd=ROOT).returncode:
        raise ValueError('Head does not descend from the base commit')
    changed = [line for line in git('diff', '--name-only', BASE_COMMIT).splitlines() if line]
    untracked = [line for line in git('ls-files', '--others', '--exclude-standard').splitlines() if line]
    other = foreign_changes(changed + untracked)
    if other:
        raise ValueError('Existing files changed: ' + ','.join(other))
    return git('rev-parse', 'HEAD')


def pinned_environments():
    import memory_ablation_protocol as p
    env = p.environments(ROOT.parent / 'competition-release-work')
    old = read_json(ROOT / 'reports/recent-geometry/2026-11-12-a/freeze.json')['environment']
    if p.public_environment(env) != old:
        raise ValueError('Pinned environments differ from the Experiment A freeze')
    return env


def verified_bindings():
    import memory_ablation_protocol as p
    bindings = p.input_bindings(ROOT)
    for group in bindings.values():
        for binding in group.values():
            if not binding['files'] or p.hashes(binding['files']) != binding['expected']:
                raise ValueError('Frozen input identity differs')
    recorded = read_json(ROOT / 'reports/recent-geometry/2026-11-12-a/freeze.json')['input_sha256']
    if {name: {cid: b['expected'] for cid, b in group.items()} for name, group in bindings.items()} != recorded:
        raise ValueError('Inputs differ from the Experiment A freeze')
    return bindings


def source_paths():
    found = {}
    for pattern in ('*.py', 'gap_solver/*.py', 'tests/test_live_dead_*.py'):
        for path in sorted(ROOT.glob(pattern)):
            found[path.relative_to(ROOT).as_posix()] = path
    for name in (PROTOCOL_DOC, SPEC_DOC, PLAN_DOC, 'requirements-memory-ablation.lock', 'requirements-training.txt'):
        if not (ROOT / name).is_file():
            raise ValueError('Required source missing: ' + name)
        found[name] = ROOT / name
    return found


def protocol_parameters():
    import live_dead_features as lf
    import live_dead_metrics as lm
    import live_dead_regimes as lg
    import live_dead_training as lt
    from memory_ablation import MODEL_SHA
    return dict(experiment=lp.EXPERIMENT, base_commit=BASE_COMMIT, start_local=lp.START_LOCAL,
                deadline_local=lp.DEADLINE_LOCAL, frozen_model_sha256=MODEL_SHA, pitch_m=dict(length=PITCH[0], width=PITCH[1]),
                offsets=dict(first=lf.OFFSETS[0], last=lf.OFFSETS[-1], step=5, positions=len(lf.OFFSETS)),
                frame_columns=lf.FRAME_COLUMNS, speed_lag=lf.SPEED_LAG, max_speed=lf.MAX_SPEED, slow=lf.SLOW,
                fast=lf.FAST, cap=lf.CAP, min_support=lf.MIN_SUPPORT, min_side=lf.MIN_SIDE, quantile='linear',
                forest=dict(lt.PARAMETERS), training_floors=dict(rows=lt.MIN_ROWS, per_class=lt.MIN_CLASS),
                clip=1e-6, seed_prefix=lp.SEED_PREFIX, stress_block_rows=lg.BLOCK, stress_remove_den=lg.REMOVE_DEN,
                gates=dict(gain=lm.GAIN, case_loss=lm.CASE_LOSS, wcsf_recall_rise=lm.WCSF_RECALL_RISE,
                           dead_loss=lm.DEAD_LOSS, false_d_rise=lm.FALSE_D_RISE, short_support=lm.SHORT_SUPPORT,
                           short_recall_loss=lm.SHORT_RECALL_LOSS, stress_primary_loss=lm.STRESS_PRIMARY_LOSS,
                           eps=lm.EPS, roundoff=lm.ROUNDOFF),
                evaluation_floors=dict(integration=lm.MIN_INTEGRATION, share=lm.MIN_SHARE, live=lm.MIN_LIVE, dead=lm.MIN_D),
                caps={PUBLIC_NAMES[k]: v for k, v in CAPS.items()}, parity_cap=PARITY_CAP,
                primary_cases=len(lp.PRIMARY), secondary_cases=len(lp.SECONDARY), kickoff='empty starts')


def freeze(run_id):
    private, public = run_paths(run_id)
    if (public / 'freeze.json').exists():
        raise ValueError('Preserve the existing freeze')
    head = check_repository()
    env = pinned_environments()
    bindings = verified_bindings()
    lp.load_frozen_model()
    import memory_ablation_protocol as p
    sources = {name: file_sha(path) for name, path in source_paths().items()}
    value = dict(schema_version=1, run_id=run_id, created_utc=utc(), head_commit=head, protocol=protocol_parameters(),
                 protocol_doc_sha256=sources[PROTOCOL_DOC], spec_sha256=sources[SPEC_DOC], plan_sha256=sources[PLAN_DOC],
                 source_sha256=sources, frozen_model_artifact_sha256=file_sha(lp.FROZEN_MODEL_PATH),
                 input_sha256={c: {cid: b['expected'] for cid, b in group.items()} for c, group in bindings.items()},
                 environment=p.public_environment(env))
    store_exact(public / 'freeze.json', value)
    private.mkdir(parents=True, exist_ok=True)
    store_exact(private / 'environment-map.json', env, public=False)
    store_exact(private / 'input-map.json', {c: {cid: {k: str(Path(v).resolve()) for k, v in b['files'].items()}
                                                 for cid, b in group.items()} for c, group in bindings.items()}, public=False)
    store_exact(private / 'freeze-anchor.json', dict(freeze_sha256=file_sha(public / 'freeze.json')), public=False)
    open_ledger(run_id).event('frozen', freeze_sha256=file_sha(public / 'freeze.json'))
    return dict(status='frozen', freeze_sha256=file_sha(public / 'freeze.json'), head_commit=head)


def frozen(run_id, role=None):
    """Re-verify the committed freeze, sources, protocol, inputs, frozen model and the executing runtime."""
    import subprocess
    import memory_ablation_protocol as p
    private, public = run_paths(run_id)
    value = read_json(public / 'freeze.json')
    for name in (PROTOCOL_DOC, 'reports/live-dead/' + run_id + '/freeze.json'):
        if subprocess.check_output(['git', 'show', 'HEAD:' + name], cwd=ROOT) != (ROOT / name).read_bytes():
            raise ValueError('Protocol and freeze must be committed before science commands')
    if file_sha(public / 'freeze.json') != read_json(private / 'freeze-anchor.json')['freeze_sha256']:
        raise ValueError('Freeze changed')
    if {name: file_sha(path) for name, path in source_paths().items()} != value['source_sha256']:
        raise ValueError('Sources changed since the freeze')
    if value['protocol'] != protocol_parameters():
        raise ValueError('Protocol parameters changed since the freeze')
    if file_sha(lp.FROZEN_MODEL_PATH) != value['frozen_model_artifact_sha256']:
        raise ValueError('Frozen model artifact changed')
    bindings = verified_bindings()
    if {c: {cid: b['expected'] for cid, b in group.items()} for c, group in bindings.items()} != value['input_sha256']:
        raise ValueError('Input identities changed since the freeze')
    if role and p.runtime_info(training=(role == 'training')) != value['environment'][role]:
        raise ValueError('Executing runtime differs from the freeze')
    return value, bindings


# ----- preflight -------------------------------------------------------------------------------------

def case_pitch(cid, binding):
    if cid == 'wcsf-used-match':
        from wcsf_geometry import _canonical
        cx, cy = _canonical(0, 0)
        return (2 * cx, 2 * cy)
    path = next(v for k, v in binding['files'].items() if str(k).endswith('.metadata.json'))
    pitch = read_json(path)['notes']['canonical_pitch_m']
    return tuple(float(v) for v in pitch)


def training_pitch(files):
    path = next(Path(v) for k, v in files.items() if str(k).endswith('.metadata.json'))
    return tuple(float(v) for v in read_json(path)['notes']['canonical_pitch_m'])


def adapter_load(ledger, cid, bindings, purpose):
    from memory_ablation_run import load_evaluation
    ledger.event('evaluation_adapter_entry', case_id=cid, purpose=purpose,
                 reference_container_may_be_parsed=not cid.startswith('wcsf'))
    return load_evaluation(cid, bindings['evaluation'][cid])


def coverage(frames, reference, eligible, integration, denominator):
    import numpy as np
    from live_dead_features import id_mismatch_rows
    periods = np.asarray([f.period for f in frames], dtype=np.uint8)
    observed = np.asarray([f.ball_observed for f in frames], dtype=bool)
    active = periods > 0
    out = dict(rows=len(frames), active_rows=int(active.sum()), denominator=int(denominator.sum()),
               integration=int(integration.sum()), share=float(integration.sum() / denominator.sum()) if denominator.any() else None,
               eligible=int(eligible.sum()), eligible_ball_missing=int((eligible & ~observed).sum()),
               active_ball_missing=int((active & ~observed).sum()), id_mismatch_rows=id_mismatch_rows(frames),
               known_live=int((integration & (reference < 2)).sum()), known_d=int((integration & (reference == 2)).sum()),
               integration_by_period={str(p): int((integration & (periods == p)).sum()) for p in (1, 2)},
               denominator_by_period={str(p): int((denominator & (periods == p)).sum()) for p in (1, 2)})
    return out


def preflight(run_id):
    deadline()
    import numpy as np
    from gap_solver.tactical import feature_rows
    import live_dead_assembly as la
    import live_dead_features as lf
    import live_dead_metrics as lm
    import live_dead_training as lt
    import player_stillness_training as pst
    freeze_value, bindings = frozen(run_id, 'scoring')
    private, public = run_paths(run_id)
    if (public / 'preflight.json').exists() or (private / 'cases').exists():
        raise ValueError('Preserve prior preflight attempts')
    ledger = open_ledger(run_id)
    (private / 'cases').mkdir(parents=True)
    input_map = read_json(private / 'input-map.json')
    problems = []
    for match in lp.TRAIN_MATCHES:
        if training_pitch(input_map['training'][match]) != PITCH:
            problems.append(f'{match}: canonical pitch differs')
    for cid in lp.CASES:
        if case_pitch(cid, bindings['evaluation'][cid]) != PITCH:
            problems.append(f'{cid}: canonical pitch differs')
    if problems:
        store_exact(public / 'preflight.json', dict(schema_version=1, status='UNRESOLVED_input', problems='; '.join(problems)))
        return dict(status='UNRESOLVED_input', problems=problems)
    # Training rows: natural motion player tracks, aligned to the cached reference first.
    ledger.event('training_reference_cache_entry', reference_container_parsed=True)
    groups = pst.load_training_groups(input_map, freeze_value['input_sha256'])
    alignment = {}
    for i, group in enumerate(groups):
        ledger.claim('parity', f'training-alignment/{run_id}/{group["match"]}')
        alignment[group['match']] = pst.alignment_check(group, i)
    for method in FIT_ORDER:
        for match in lp.TRAIN_MATCHES:
            ledger.claim('feature_pass', f'training/{method}/{match}')
    if [g['match'] for g in groups] != list(lp.TRAIN_MATCHES):
        raise ValueError('Training match order differs')
    training = lt.select_training(groups, PITCH)
    del groups
    training_arrays = dict(instant=training.instant, temporal=training.temporal, target=training.target,
                           weights=training.weights, row_identity=training.row_identity)
    training_identity = save_arrays(private / 'training.npz', training_arrays)
    training_problems = lt.check_floors(training)
    store_exact(public / 'training-alignment.json', dict(status='passed', cases={
        m: {k: v for k, v in row.items() if isinstance(v, (int, float, str))} for m, row in alignment.items()}))
    cases, counts = {}, {}
    if not training_problems:
        for cid in lp.CASES:
            deadline()
            loaded = adapter_load(ledger, cid, bindings, 'preflight')
            frames = list(loaded['frames'])
            reference = np.asarray(loaded['reference'](), dtype=np.uint8)
            ledger.event('reference_codes_entry', case_id=cid)
            if reference.shape != (len(frames),):
                raise ValueError('Reference/frame dimensions differ on ' + cid)
            ledger.claim('feature_pass', f'natural/{cid}/liveness')
            x = lf.liveness_inputs(frames, PITCH)
            ledger.claim('feature_pass', f'natural/{cid}/frozen')
            frozen_matrix = np.asarray(list(feature_rows(frames)), dtype=np.float32)
            denominator = la.denominator_mask(frames)
            integration = la.integration_mask(frames, x.eligible)
            arrays = dict(reference=reference, instant=np.asarray(x.instant), eligible=np.asarray(x.eligible),
                          frozen_matrix=frozen_matrix, integration=integration, denominator=denominator)
            identity = save_arrays(private / 'cases' / (cid + '.npz'), arrays)
            cases[cid] = dict(coverage(frames, reference, x.eligible, integration, denominator),
                              role='primary' if cid in lp.PRIMARY else 'secondary', provider=lp.provider_of(cid),
                              case_arrays_sha256=identity)
            counts[cid] = cases[cid]
            ledger.event('preflight_case', case_id=cid, integration=cases[cid]['integration'])
            del loaded, frames, x, frozen_matrix
    evaluation_problems = lm.coverage_floors(counts) if not training_problems else []
    all_problems = training_problems + evaluation_problems
    status = 'ready' if not all_problems else 'UNRESOLVED_support'
    value = dict(schema_version=1, status=status, problems='; '.join(all_problems),
                 training=dict(counts={c['match']: {k: v for k, v in c.items() if k != 'match'} for c in training.counts},
                               training_arrays_sha256=training_identity),
                 cases=cases, freeze_sha256=file_sha(public / 'freeze.json'), created_utc=utc())
    store_exact(public / 'preflight.json', value)
    return dict(status=status, problems=all_problems)


# ----- fit ---------------------------------------------------------------------------------------------

def fit_worker(run_id):
    """Runs under the pinned training interpreter.  Exactly two fits, instant first."""
    deadline()
    import live_dead_training as lt
    frozen(run_id, 'training')
    private, public = run_paths(run_id)
    pre = require(public, 'preflight.json', ('ready',))
    if (public / 'fit.json').exists() or (private / 'fit.incomplete').exists():
        raise ValueError('Preserve consumed or interrupted fitting attempts')
    store_exact(private / 'fit.incomplete', dict(utc=utc()), public=False)
    ledger = open_ledger(run_id)
    arrays = load_arrays(private / 'training.npz', pre['training']['training_arrays_sha256'])
    counts = tuple(dict(match=m, **c) for m, c in pre['training']['counts'].items())
    training = lt.TrainingSet(arrays['instant'], arrays['temporal'], arrays['target'], arrays['weights'],
                              arrays['row_identity'], counts)
    if lt.check_floors(training):
        raise ValueError('Training floors not met')

    def entry(mode):
        deadline()
        ledger.claim('fit', mode)

    results = lt.fit_pair(training, entry)
    directory = public / 'models'
    for mode, row in results.items():
        if row['parameters'] != lt.PARAMETERS:
            raise ValueError('Production fit used non-recipe parameters')
        store_exact(directory / (mode + '.json'), row, public=False)
    value = dict(schema_version=1, status='complete', fits=2, rows=int(len(training.target)),
                 training_arrays_sha256=pre['training']['training_arrays_sha256'],
                 model_artifact_sha256={m: file_sha(directory / (m + '.json')) for m in results},
                 **{f'{m}_{k}': results[m][k] for m in results for k in ('model_sha256', 'parity_max_abs_diff', 'node_count')},
                 class_support=results['temporal']['class_support'],
                 split_counts={m: results[m]['split_counts'] for m in results},
                 freeze_sha256=file_sha(public / 'freeze.json'), created_utc=utc())
    store_exact(public / 'fit.json', value)
    (private / 'fit.incomplete').unlink()
    return dict(status='complete', fits=2)


def fit(run_id):
    deadline()
    import subprocess
    import memory_ablation_protocol as p
    frozen(run_id)
    private, public = run_paths(run_id)
    require(public, 'preflight.json', ('ready',))
    env = read_json(private / 'environment-map.json')
    result = subprocess.run([env['training_python'], str(ROOT / 'live_dead_run.py'), 'fit', '--run-id', run_id, '--worker'],
                            cwd=ROOT, env=p.thread_environment(), capture_output=True, text=True)
    for name, text in (('fit-worker.stdout.log', result.stdout), ('fit-worker.stderr.log', result.stderr)):
        with (private / name).open('x', encoding='utf-8') as handle:
            handle.write(text)
    if result.returncode:
        raise ValueError('Pinned training worker stopped; private logs retained')
    return json.loads(result.stdout.strip().splitlines()[-1])


def load_models(public):
    import live_dead_training as lt
    from live_dead_features import FRAME_COLUMNS, WINDOW_COLUMNS
    fit_value = require(public, 'fit.json', ('complete',))
    models = {}
    for mode, width in (('instant', FRAME_COLUMNS), ('temporal', WINDOW_COLUMNS)):
        path = public / 'models' / (mode + '.json')
        if file_sha(path) != fit_value['model_artifact_sha256'][mode]:
            raise ValueError('Model artifact changed')
        models[mode] = read_json(path)['model']
        lt.validate_forest(models[mode], width)
    return models, fit_value


# ----- parity --------------------------------------------------------------------------------------------

FIELDS = ('control', 'gapped', 'restarted', 'final', 'stoppage_gaps', 'gap_summary', 'kickoff_changed')


def reconcile_against_history(score, historical):
    from math import isclose
    ok = isclose(score['metrics']['spell_f1_mean'], historical['metrics']['spell_f1_mean'], rel_tol=0, abs_tol=1e-9)
    ok = ok and (score['spells']['n_gt'], score['spells']['n_pred']) == (historical['spells']['n_gt'], historical['spells']['n_pred'])
    ok = ok and set(score['spells']['per_iou']) == set(historical['spells']['per_iou'])
    for threshold, row in historical['spells']['per_iou'].items():
        got = score['spells']['per_iou'].get(threshold, {})
        ok = ok and all(got.get(k) == row[k] for k in ('n_matched', 'n_missed', 'n_spurious'))
    return bool(ok)


def parity(run_id):
    deadline()
    import numpy as np
    import live_dead_assembly as la
    import live_dead_metrics as lm
    import restart_release
    from memory_ablation import predict_supports
    from memory_ablation_metrics import score_variant
    from recent_geometry_assembly import assemble_research
    from release_runtime import submission_bytes
    _, bindings = frozen(run_id, 'scoring')
    private, public = run_paths(run_id)
    if (public / 'parity.json').exists():
        raise ValueError('Preserve prior parity attempt')
    pre = require(public, 'preflight.json', ('ready',))
    _, fit_value = load_models(public)
    frozen_model = lp.load_frozen_model()
    ledger = open_ledger(run_id)
    for mode in FIT_ORDER:
        ledger.claim('parity', f'exporter/{run_id}/{mode}')
        if fit_value[mode + '_parity_max_abs_diff'] > 1e-12:
            raise ValueError('Exporter parity failed: ' + mode)
    cases, f1 = {}, {}
    for cid in lp.CASES:
        deadline()
        arrays = load_arrays(private / 'cases' / (cid + '.npz'), pre['cases'][cid]['case_arrays_sha256'])
        loaded = adapter_load(ledger, cid, bindings, 'parity')
        frames = list(loaded['frames'])
        ledger.claim('parity', f'release/{run_id}/{cid}')
        real = restart_release.assemble(frames, (), use_restart=True)
        supports = np.asarray(predict_supports(arrays['frozen_matrix'], frozen_model), dtype=np.float64)
        replica = assemble_research(frames, la.StreamSupportSet('release', supports), verify_decoder=True)
        if not all(getattr(real, n) == getattr(replica, n) for n in FIELDS):
            raise ValueError('Release parity failed on ' + cid)
        periods = np.asarray([f.period for f in frames], dtype=np.uint8)
        observed = np.asarray([f.ball_observed for f in frames], dtype=bool)
        score = score_variant(arrays['reference'], encode(replica.control), periods, observed)
        historical = read_json(HISTORICAL_DIR / f'{cid}--natural.json')['variants']['control']
        if not reconcile_against_history(score, historical):
            raise ValueError('Historical reconciliation failed on ' + cid)
        f1[cid] = score['metrics']['spell_f1_mean']
        ledger.claim('parity', f'disabled/{run_id}/{cid}')
        disabled = la.integrate(supports, np.full(len(frames), .5), np.zeros(len(frames), dtype=bool))
        if disabled.tobytes() != supports.tobytes():
            raise ValueError('Disabled head changed supports on ' + cid)
        off = la.assemble_stream(frames, 'temporal', disabled)
        if not all(getattr(off, n) == getattr(replica, n) for n in FIELDS) or off.latent != replica.latent:
            raise ValueError('Disabled-head parity failed on ' + cid)
        if submission_bytes(off.final) != submission_bytes(real.final):
            raise ValueError('Disabled-head CSV bytes differ on ' + cid)
        cases[cid] = dict(release_parity=True, reconciliation=True, disabled_head_parity=True,
                          spell_f1_intermediate=f1[cid], historical_spell_f1=historical['metrics']['spell_f1_mean'])
        ledger.event('parity_case', case_id=cid)
        del loaded, frames, real, replica, off
    primary, _ = lm.weighted(f1)
    historical_summary = read_json(HISTORICAL_DIR / 'summary.json')['primary']['natural']['control']
    if primary is None or abs(primary - PRIMARY_NATURAL_MEAN) > 1e-6 or abs(primary - historical_summary) > 1e-9:
        raise ValueError('Primary natural mean not reproduced')
    value = dict(schema_version=1, status='passed', release_parity_cases=15, reconciliation_cases=15,
                 disabled_head_cases=15, exporter_parity_max_abs_diff=max(fit_value['instant_parity_max_abs_diff'],
                                                                           fit_value['temporal_parity_max_abs_diff']),
                 primary_natural_mean=primary, historical_primary_natural_mean=historical_summary, cases=cases,
                 freeze_sha256=file_sha(public / 'freeze.json'), created_utc=utc())
    store_exact(public / 'parity.json', value)
    return dict(status='passed', primary_natural_mean=primary)


# ----- one bundle: three streams on identical inputs -------------------------------------------------------

def _changes(reference, base, other, observed, supported):
    """Rows the stream corrected or newly broke against the release, by ball and head-support strata."""
    known = reference < 3
    out = {}
    for ball_name, ball in (('visible', observed), ('missing', ~observed)):
        for sup_name, sup in (('supported', supported), ('fallback', ~supported)):
            at = known & ball & sup
            out[f'{ball_name}_{sup_name}'] = dict(
                known=int(at.sum()), corrected=int((at & (base != reference) & (other == reference)).sum()),
                introduced=int((at & (base == reference) & (other != reference)).sum()))
    return out


def run_bundle(ledger, regime, cid, frames, reference, instant, eligible, frozen_matrix, models, frozen_model, directory):
    import numpy as np
    import live_dead_assembly as la
    import live_dead_training as lt
    import recent_geometry_metrics as metrics
    from live_dead_features import barrier_ids, window_matrix
    from memory_ablation import predict_supports
    frames = list(frames)
    periods = np.asarray([f.period for f in frames], dtype=np.uint8)
    observed = np.asarray([f.ball_observed for f in frames], dtype=bool)
    reference = np.asarray(reference)
    temporal = window_matrix(instant, barrier_ids(frames))
    mask = la.integration_mask(frames, eligible)
    ledger.claim('feature_pass', f'{regime}/{cid}/release/tree')
    frozen = np.asarray(predict_supports(frozen_matrix, frozen_model), dtype=np.float64)
    supports, q = {'release': frozen}, {}
    for mode, matrix in (('instant', instant), ('temporal', temporal)):
        ledger.claim('feature_pass', f'{regime}/{cid}/{mode}/tree')
        score = np.full(len(frames), np.nan)
        if mask.any():
            score[mask] = lt.dead_scores(matrix[mask], models[mode])
        q[mode] = score
        supports[mode] = la.integrate(frozen, score, mask)
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    bundles, finals, assemblies, hashes = {}, {}, {}, {}
    for stream in la.STREAMS:
        identity = f'{regime}/{cid}/{stream}'
        ledger.claim('prediction', identity)
        for k in range(2):
            ledger.claim('decoder_pass', f'{identity}/{k}')
        assembly = la.assemble_stream(frames, stream, supports[stream])
        if assembly.decoder_passes != 2:
            raise ValueError('Decoder pass accounting differs from the claim')
        assemblies[stream] = assembly
        finals[stream] = encode(assembly.final)
        ledger.claim('score', identity)
        bundles[stream] = metrics.score_bundle(reference, finals[stream], periods, observed,
                                               restart=cid in RESTART_CASES)
        arrays = dict(supports=supports[stream], final=finals[stream], latent=encode(assembly.latent))
        if stream in q:
            arrays['dead_score'] = q[stream]
        hashes[stream] = save_arrays(directory / (stream + '.npz'), arrays)
    la.require_same_gaps(assemblies)
    changes = {s: _changes(reference, finals['release'], finals[s], observed, mask) for s in ('instant', 'temporal')}
    score_summary = {s: dict(mean=float(np.mean(q[s][mask])) if mask.any() else None,
                             above_half=int((q[s][mask] > .5).sum())) for s in q}
    return dict(schema_version=1, regime=regime, case_id=cid, bundles=bundles,
                flats={s: metrics.flatten(bundles[s]) for s in la.STREAMS}, changes=changes, dead_scores=score_summary,
                integration_rows=int(mask.sum()), stoppage_gap_count=len(assemblies['release'].stoppage_gaps),
                kickoff_changed_any=any(bool(v) for v in assemblies['release'].kickoff_changed.values())
                if isinstance(assemblies['release'].kickoff_changed, dict) else None,
                stream_arrays_sha256=hashes)


def _store_case(public, regime, receipt, cid):
    value = dict(receipt, role='primary' if cid in lp.PRIMARY else 'secondary', provider=lp.provider_of(cid))
    store_exact(public / 'cases' / f'{cid}--{regime}.json', value)
    return value


def finish_stage(path, value):
    """Store a completed stage aggregate; past the deadline it is kept but marked timeout/UNRESOLVED."""
    try:
        deadline()
    except ValueError:
        value = dict(value, status='timeout', decision='UNRESOLVED', decision_before_timeout=value.get('decision'))
        if 'advance_to_stage2' in value:
            value['advance_to_stage2'] = False
    store_exact(path, value)
    return value


# ----- stages ----------------------------------------------------------------------------------------------------

def natural(run_id):
    deadline()
    import live_dead_metrics as lm
    _, bindings = frozen(run_id, 'scoring')
    private, public = run_paths(run_id)
    if (public / 'stage1.json').exists() or (private / 'predictions' / 'natural').exists():
        raise ValueError('Preserve prior stage-1 attempt')
    pre = require(public, 'preflight.json', ('ready',))
    require(public, 'parity.json', ('passed',))
    models, _ = load_models(public)
    frozen_model = lp.load_frozen_model()
    ledger = open_ledger(run_id)
    ledger.event('stage_start', stage='natural')
    flats = {}
    for cid in lp.CASES:
        deadline()
        arrays = load_arrays(private / 'cases' / (cid + '.npz'), pre['cases'][cid]['case_arrays_sha256'])
        loaded = adapter_load(ledger, cid, bindings, 'natural')
        receipt = run_bundle(ledger, 'natural', cid, loaded['frames'], arrays['reference'], arrays['instant'],
                             arrays['eligible'], arrays['frozen_matrix'], models, frozen_model,
                             private / 'predictions' / 'natural' / cid)
        flats[cid] = _store_case(public, 'natural', receipt, cid)['flats']
        ledger.event('case_complete', case_id=cid, regime='natural')
        del loaded, arrays
    gates = lm.gate_natural(flats)
    decision = lm.verdict(dict(natural=gates), [])
    value = finish_stage(public / 'stage1.json', dict(
        schema_version=1, status='complete', decision=decision, advance_to_stage2=decision == 'PASS', gates=gates,
        budget=ledger.usage(), created_utc=utc()))
    decision = value['decision']
    ledger.event('stage_end', stage='natural', decision=decision)
    return dict(decision=decision, failing=sorted(k for k, v in gates.items() if v['status'] not in ('pass', 'reported', 'non_applicable')))


def _stress_inputs(ledger, regime, cid, bindings, case_arrays, transform, directory):
    """Transform one case, build its liveness and frozen inputs (two feature passes) and measure coverage."""
    import numpy as np
    from gap_solver.tactical import feature_rows
    import live_dead_assembly as la
    import live_dead_features as lf
    loaded = adapter_load(ledger, cid, bindings, regime + '-inputs')
    frames = transform(list(loaded['frames']), cid)
    ledger.claim('feature_pass', f'{regime}/{cid}/liveness')
    x = lf.liveness_inputs(frames, PITCH)
    if regime == 'jitter' and (np.asarray(x.instant).tobytes() != case_arrays['instant'].tobytes()
                               or np.asarray(x.eligible).tobytes() != case_arrays['eligible'].tobytes()):
        raise ValueError('Liveness inputs changed under ball jitter on ' + cid)
    ledger.claim('feature_pass', f'{regime}/{cid}/frozen')
    frozen_matrix = np.asarray(list(feature_rows(frames)), dtype=np.float32)
    denominator = la.denominator_mask(frames)
    integration = la.integration_mask(frames, x.eligible)
    reference = np.asarray(case_arrays['reference'])
    arrays = dict(instant=np.asarray(x.instant), eligible=np.asarray(x.eligible), frozen_matrix=frozen_matrix)
    identity = save_arrays(Path(directory) / (cid + '.npz'), arrays)
    return dict(coverage(frames, reference, x.eligible, integration, denominator), stress_arrays_sha256=identity)


def stress(run_id):
    """Stage 2 after a stage-1 PASS.  Transformed inputs and support floors for both regimes are checked before any
    prediction or score claim; any shortfall stops the stage as UNRESOLVED_support and lists every shortfall."""
    deadline()
    _, public = run_paths(run_id)
    stage1_path = public / 'stage1.json'
    if not stage1_path.is_file() or read_json(stage1_path).get('decision') != 'PASS':
        raise ValueError('Stress requires a stage 1 PASS')
    import live_dead_metrics as lm
    import live_dead_regimes as lg
    _, bindings = frozen(run_id, 'scoring')
    private, public = run_paths(run_id)
    if (public / 'stage2.json').exists() or (private / 'stress-inputs').exists():
        raise ValueError('Preserve prior stage-2 attempt')
    pre = require(public, 'preflight.json', ('ready',))
    models, _ = load_models(public)
    frozen_model = lp.load_frozen_model()
    ledger = open_ledger(run_id)
    transforms = dict(jitter=lg.jitter_ball, degrade=lg.degrade_players)
    coverages, problems = {}, []
    for regime in STRESS_REGIMES:
        ledger.event('stage_start', stage=regime + '-inputs')
        coverages[regime] = {}
        for cid in lp.PRIMARY:
            deadline()
            case_arrays = load_arrays(private / 'cases' / (cid + '.npz'), pre['cases'][cid]['case_arrays_sha256'])
            coverages[regime][cid] = _stress_inputs(ledger, regime, cid, bindings, case_arrays, transforms[regime],
                                                    private / 'stress-inputs' / regime)
        problems += [regime + ': ' + p for p in lm.coverage_floors(coverages[regime])]
    if problems:
        finish_stage(public / 'stage2.json', dict(
            schema_version=1, status='UNRESOLVED_support', decision='UNRESOLVED', problems='; '.join(problems),
            coverage=coverages, budget=ledger.usage(), created_utc=utc()))
        return dict(decision='UNRESOLVED', problems=problems)
    gates, decisions = {}, {}
    for regime in STRESS_REGIMES:
        flats = {}
        for cid in lp.PRIMARY:
            deadline()
            case_arrays = load_arrays(private / 'cases' / (cid + '.npz'), pre['cases'][cid]['case_arrays_sha256'])
            inputs = load_arrays(private / 'stress-inputs' / regime / (cid + '.npz'),
                                 coverages[regime][cid]['stress_arrays_sha256'])
            loaded = adapter_load(ledger, cid, bindings, regime)
            frames = transforms[regime](list(loaded['frames']), cid)
            receipt = run_bundle(ledger, regime, cid, frames, case_arrays['reference'], inputs['instant'],
                                 inputs['eligible'], inputs['frozen_matrix'], models, frozen_model,
                                 private / 'predictions' / regime / cid)
            flats[cid] = _store_case(public, regime, receipt, cid)['flats']
            ledger.event('case_complete', case_id=cid, regime=regime)
            del loaded, frames, inputs, case_arrays
        gates[regime] = lm.gate_stress(flats)
        decisions[regime] = lm.verdict({regime: gates[regime]}, [])
    value = finish_stage(public / 'stage2.json', dict(
        schema_version=1, status='complete', decision=lm.verdict(gates, []), regimes=decisions, gates=gates,
        coverage=coverages, budget=ledger.usage(), created_utc=utc()))
    return dict(decision=value['decision'], regimes=decisions)


def summarise(run_id):
    _, public = run_paths(run_id)
    if (public / 'summary.json').exists():
        raise ValueError('Preserve the existing summary')
    ledger = open_ledger(run_id)
    pre = read_json(public / 'preflight.json') if (public / 'preflight.json').exists() else None
    stage1 = read_json(public / 'stage1.json') if (public / 'stage1.json').exists() else None
    stage2 = read_json(public / 'stage2.json') if (public / 'stage2.json').exists() else None
    if pre is None or pre['status'] != 'ready':
        verdict, reason = 'UNRESOLVED', 'preflight ' + (pre['status'] if pre else 'missing') + (': ' + pre['problems'] if pre else '')
    elif stage1 is None:
        verdict, reason = 'UNRESOLVED', 'stage 1 incomplete'
    elif stage1['decision'] != 'PASS':
        verdict, reason = stage1['decision'], 'stage 1 ' + stage1['decision'] + '; stress not run'
    elif stage2 is None:
        verdict, reason = 'UNRESOLVED', 'stage 2 incomplete'
    else:
        verdict, reason = stage2['decision'], 'stage 2 ' + stage2['decision']
    value = dict(schema_version=1, status='complete', verdict=verdict, reason=reason,
                 meaning=('supports a separate release investigation only' if verdict == 'PASS' else
                          'no advancement for this fixed recipe' if verdict == 'NO_ADVANCEMENT' else
                          'integrity, support, incompleteness or timeout; not scientific evidence'),
                 budget=ledger.usage(), deadline_local=lp.DEADLINE_LOCAL, created_utc=utc())
    store_exact(public / 'summary.json', value)
    with (public / 'report.md').open('x', encoding='utf-8') as handle:
        handle.write(render_report(value, pre, stage1, stage2))
    return value


def _cell(value):
    if isinstance(value, float):
        return f'{value:.6f}'
    if isinstance(value, dict):
        return ', '.join(f'{k} {_cell(v)}' for k, v in value.items() if not isinstance(v, dict))
    return '' if value is None else str(value)


def _gate_table(gates):
    lines = ['| Check | Status | Value | Threshold |', '|---|---|---|---|']
    for name, check in gates.items():
        shown = {k: v for k, v in check.items() if k not in ('status', 'threshold')}
        value = check.get('value', shown if check['status'] == 'reported' else None)
        lines.append(f"| {name} | {check['status']} | {_cell(value)} | {_cell(check.get('threshold'))} |")
    return '\n'.join(lines)


def render_report(summary, pre, stage1, stage2):
    out = [f"# Live/dead sequence experiment: {summary['verdict']}", '',
           f"Verdict **{summary['verdict']}**: {summary['meaning']}.", f"Reason: {summary['reason']}.", '',
           'Streams: frozen release, instantaneous binary head, temporal binary head, on reused external '
           'development/regression cases. Not a holdout, not a challenge estimate, no significance claim.', '']
    if pre and pre.get('problems'):
        out += ['## Preflight shortfalls', '', pre['problems'], '']
    if stage1 and stage1.get('gates'):
        out += ['## Stage 1: natural inputs', '', f"Decision: {stage1['decision']}", '', _gate_table(stage1['gates']), '']
    if stage2:
        out += ['## Stage 2: stress regimes', '', f"Decision: {stage2['decision']}", '']
        if stage2.get('problems'):
            out += [stage2['problems'], '']
        for regime, gates in (stage2.get('gates') or {}).items():
            out += [f'### {regime}', '', _gate_table(gates), '']
    out += ['## Budget used', '', ', '.join(f'{k} {v}' for k, v in summary['budget'].items()), '']
    return '\n'.join(out)


COMMANDS = dict(freeze=freeze, preflight=preflight, fit=fit, parity=parity, natural=natural, stress=stress,
                summarise=summarise)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=sorted(COMMANDS))
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--worker', action='store_true')
    args = parser.parse_args(argv)
    if args.worker and args.command != 'fit':
        raise SystemExit('--worker applies to fit only')
    result = fit_worker(args.run_id) if args.worker else COMMANDS[args.command](args.run_id)
    print(json.dumps(result, sort_keys=True, default=str))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
