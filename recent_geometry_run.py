"""Experiment A orchestration: preflight / freeze / fit / parity / natural / stress / summarise, with a budget ledger.

Heavy protocol modules are imported lazily inside commands so the ledger stays testable in isolation.
Private arrays live outside Git under PRIVATE_ROOT; only aggregates are written to reports/recent-geometry.
"""
import json
from pathlib import Path
import re

from datetime import datetime, timezone

EXPERIMENT = 'recent-geometry-2026-11-11'
ROOT = Path(__file__).resolve().parent
PRIVATE_ROOT = Path.home() / "Documents/ChatGPT/MESSI's FOOT/recent-geometry-reference"
BASE_COMMIT = 'a3b5b0a07ddc561db6aafcce26dcc56d31ef2bb2'

# Science budget (section 10).  Claimed on entry, cumulative across run ids, never refunded.
CAPS = dict(fit=2, prediction=100, score=115, feature_pass=200, decoder_pass=300)
FIT_ORDER = ('control', 'candidate')

SKILLCORNER = ('1874553', '1886347', '2007448', '2007721', '2010085', '2011166', '2013725', '2015213', '2016236', '2017461')
NATURAL_CASES = tuple('skillcorner-' + m for m in SKILLCORNER) + (
    'dfl-J03WR9', 'dfl-J03WN1', 'wcsf-used-match', 'dfl-J03WOH', 'dfl-J03WOY')
_SAFE = re.compile(r'[A-Za-z0-9_.:/-]{1,200}')


class BudgetError(ValueError):
    pass


def utc():
    return datetime.now(timezone.utc).isoformat()


class Ledger:
    """Claim-on-entry ledger.  ``parity`` is a separate implementation-verification category: bounded,
    unique identities, never counted against the science caps, and it produces no scores."""

    def __init__(self, claims, access):
        self.claims = Path(claims)
        self.access = Path(access)
        self.claims.mkdir(parents=True, exist_ok=True)
        self.access.parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _parity_allowed(identity):
        if identity == 'exporter':
            return True
        kind, _, case = identity.partition('/')
        return kind in ('release', 'prefix') and case in NATURAL_CASES

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
            if identity == 'candidate' and not (self.claims / 'fit--control.json').exists():
                raise BudgetError('Control fit must be claimed first')
        if kind in CAPS and self.count(kind) >= CAPS[kind]:
            raise BudgetError('Budget exhausted: ' + kind)
        path = self.claims / (kind + '--' + identity.replace('/', '__') + '.json')
        try:
            with path.open('x', encoding='utf-8') as handle:
                handle.write(json.dumps(dict(kind=kind, identity=identity, utc=utc()), sort_keys=True) + '\n')
        except FileExistsError:
            raise BudgetError('Already claimed (no reruns): ' + kind + ' ' + identity) from None
        with self.access.open('a', encoding='utf-8') as handle:
            handle.write(json.dumps(dict(event=kind + '_entry', identity=identity, utc=utc()), sort_keys=True) + '\n')

    def event(self, event, **fields):
        with self.access.open('a', encoding='utf-8') as handle:
            handle.write(json.dumps(dict(event=event, utc=utc(), **fields), sort_keys=True) + '\n')


# ----- shared helpers ----------------------------------------------------------------------------

def safe_run_id(run_id):
    if not isinstance(run_id, str) or not re.fullmatch('[a-z0-9][a-z0-9-]{0,63}', run_id):
        raise ValueError('Unsafe run ID')
    return run_id


def run_paths(run_id):
    from gap_solver.input_contract import reject_linked_ancestors
    safe_run_id(run_id)
    private = PRIVATE_ROOT / run_id
    public = ROOT / 'reports/recent-geometry' / run_id
    for path in (PRIVATE_ROOT, private, public):
        reject_linked_ancestors(path)
    return private, public


def open_ledger(run_id):
    private, _ = run_paths(run_id)
    private.mkdir(parents=True, exist_ok=True)
    return Ledger(PRIVATE_ROOT / 'claims', private / 'access.jsonl')


def verified_bindings():
    """Frozen input identities (training + evaluation) re-hashed against the historical bindings."""
    import memory_ablation_protocol as p
    bindings = p.input_bindings(ROOT)
    for group in bindings.values():
        for binding in group.values():
            if not binding['files'] or p.hashes(binding['files']) != binding['expected']:
                raise ValueError('Frozen input identity differs')
    return bindings


# ----- pre-freeze: distance recomputation parity -------------------------------------------------

def distance_parity(run_id):
    """Per case: does recomputing distances from player positions reproduce the loader's distances exactly?

    No predictions, no scoring.  Adapter access (which may parse reference containers) is logged.
    """
    import memory_ablation_protocol as p
    from memory_ablation_run import load_evaluation
    from recent_geometry_regimes import distance_recompute_audit
    ledger = open_ledger(run_id)
    _, public = run_paths(run_id)
    public.mkdir(parents=True, exist_ok=True)
    bindings = verified_bindings()['evaluation']
    cases = {}
    for cid in NATURAL_CASES:
        ledger.event('evaluation_adapter_entry', case_id=cid, purpose='distance_recompute_parity',
                     reference_container_may_be_parsed=not cid.startswith('wcsf'))
        loaded = load_evaluation(cid, bindings[cid])
        cases[cid] = distance_recompute_audit(loaded['frames'])
        ledger.event('distance_parity_case', case_id=cid, **cases[cid])
        del loaded
    providers = {}
    for cid, row in cases.items():
        provider = cid.split('-', 1)[0]
        agg = providers.setdefault(provider, dict(checked_rows=0, exact_rows=0, mismatched_rows=0, none_disagreements=0,
                                                  max_abs_diff=0., unobserved_rows_with_stored_distance=0))
        for key in agg:
            agg[key] = max(agg[key], row[key]) if key == 'max_abs_diff' else agg[key] + row[key]
    exact = all(row['mismatched_rows'] == 0 and row['none_disagreements'] == 0 and row['max_abs_diff'] == 0. for row in cases.values())
    value = dict(schema_version=1, status='exact' if exact else 'NOT_EXACT_STOP', cases=cases, providers=providers,
                 created_utc=utc())
    p.store_exact(public / 'distance-parity.json', value)
    return value


# ----- light I/O helpers (same canonical bytes as memory_ablation_protocol) ------------------------

import hashlib


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
    with path.open('xb') as handle:
        handle.write(canonical(value))
    if path.read_bytes() != canonical(value):
        raise ValueError('Persisted canonical bytes differ')


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def encode(labels):
    import numpy as np
    return np.asarray(['HADX'.index(s) for s in labels], dtype=np.uint8)


# ----- one case, one regime, both methods --------------------------------------------------------

def run_case_regime(ledger, regime, cid, frames, reference, models, directory, *, matrix=None, prep_claimed=False):
    """Predict with both methods on identical transformed inputs and score the final labels.

    ``frames`` are the transformed inference inputs; ``reference`` is evaluation machinery used only to score.
    Every unit of science budget is claimed before it is spent.  ``models`` = dict(control=model, candidate=model).
    """
    import numpy as np
    import recent_geometry_assembly as ra
    import recent_geometry_features as rf
    import recent_geometry_metrics as metrics
    frames = list(frames)
    periods = np.asarray([f.period for f in frames], dtype=np.uint8)
    observed = np.asarray([f.ball_observed for f in frames], dtype=bool)
    reference = np.asarray(reference)
    if reference.shape != periods.shape:
        raise ValueError('Reference/frame dimensions differ')
    if matrix is None:
        if not prep_claimed:
            ledger.claim('feature_pass', f'{regime}/{cid}/prep')
        matrix = rf.research_matrix(frames)
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    bundles, finals, latents = {}, {}, {}
    for method in metrics.METHODS:
        identity = f'{regime}/{cid}/{method}'
        ledger.claim('prediction', identity)
        ledger.claim('feature_pass', identity + '/tree')
        support = ra.SupportSet.from_matrix(method, matrix, models[method])
        expected_passes = 2
        for k in range(expected_passes):
            ledger.claim('decoder_pass', f'{identity}/{k}')
        assembly = ra.assemble_research(frames, support)
        if assembly.decoder_passes != expected_passes:
            raise ValueError('Decoder pass accounting differs from the claim')
        final = encode(assembly.final)
        finals[method], latents[method] = final, encode(assembly.latent)
        ledger.claim('score', identity)
        bundles[method] = metrics.score_bundle(reference, final, periods, observed, restart=(regime == 'stoppage'))
        np.savez_compressed(directory / (method + '.npz'), supports=support.supports, latent=latents[method], final=final)
    gt = np.where(periods > 0, reference, 3).astype(np.uint8)
    transitions = metrics.interior_transitions(gt, finals['control'], finals['candidate'], periods, observed,
                                               latents['control'], latents['candidate'])
    return dict(schema_version=1, regime=regime, case_id=cid, bundles=bundles,
                flats={m: metrics.flatten(bundles[m]) for m in metrics.METHODS}, interior_changes=transitions,
                input_summary=dict(rows=len(frames), observed_rows=int(observed.sum())))


# ----- protocol identity and freeze --------------------------------------------------------------

PROTOCOL_DOC = 'docs/recent-geometry-protocol.md'
NEW_FILES_PREFIXES = ('recent_geometry_', 'tests/test_recent_geometry_', 'docs/recent-geometry-protocol.md',
                      'reports/recent-geometry/', '.gitignore')
STOPPAGE_CASES = ('dfl-J03WR9', 'dfl-J03WN1', 'dfl-J03WOH', 'dfl-J03WOY', 'wcsf-used-match')
PRIMARY_RESTART = {'dfl': ('dfl-J03WR9', 'dfl-J03WN1'), 'wcsf': ('wcsf-used-match',)}
PROVIDERS = ('skillcorner', 'dfl', 'wcsf')


def provider_of(cid):
    return cid.split('-', 1)[0]


def is_primary(cid):
    return cid not in ('dfl-J03WOH', 'dfl-J03WOY')


def protocol_parameters():
    import recent_geometry_features as rf
    import recent_geometry_metrics as m
    import recent_geometry_regimes as rr
    import recent_geometry_training as rt
    from memory_ablation import MODEL_SHA
    return dict(experiment=EXPERIMENT, base_commit=BASE_COMMIT, model_sha256=MODEL_SHA, window=rf.WINDOW,
                expected_rows=rt.EXPECTED_ROWS, control_training_semantic_sha256=rt.CONTROL_TRAINING_SEMANTIC_SHA,
                tree=dict(max_depth=4, min_samples_leaf=125, random_state=1729), mask_rate=.3, mask_seed=1729,
                jitter_prefix=rr.JITTER_PREFIX, jitter_sigma=rr.JITTER_SIGMA, live_window=rr.LIVE_WINDOW,
                live_max_windows=rr.LIVE_MAX_WINDOWS, live_min_visible=rr.LIVE_MIN_VISIBLE, stoppage_tail=rr.STOPPAGE_TAIL,
                gain_threshold=m.GAIN_THRESHOLD, stress_primary_loss=m.STRESS_PRIMARY_LOSS, match_loss=m.MATCH_LOSS,
                dead_loss=m.DEAD_LOSS, false_d_rise=m.FALSE_D_RISE, short_recall_loss=m.SHORT_RECALL_LOSS,
                short_support=m.SHORT_SUPPORT, interior_margin=m.INTERIOR_MARGIN, restart_window=m.RESTART_WINDOW,
                recovery_frames=m.RECOVERY_FRAMES, min_live_windows=m.MIN_LIVE_WINDOWS, min_restart_events=m.MIN_RESTART_EVENTS,
                slack=m.EPS, roundoff=m.ROUNDOFF, switch_cost=32., log_floor=1e-6, kickoff='empty starts for both methods',
                caps=dict(CAPS), cutoff_local='2026-11-13T23:59', primary_cases=len([c for c in NATURAL_CASES if is_primary(c)]),
                secondary_cases=2, regimes=dict(natural=15, noise=15, live_gap=15, stoppage=5))


def source_paths():
    found = {}
    for pattern in ('*.py', 'gap_solver/*.py', 'tests/test_recent_geometry_*.py'):
        for path in sorted(ROOT.glob(pattern)):
            found[path.relative_to(ROOT).as_posix()] = path
    for name in (PROTOCOL_DOC, 'requirements-memory-ablation.lock', 'requirements-training.txt'):
        if not (ROOT / name).is_file():
            raise ValueError('Required source missing: ' + name)
        found[name] = ROOT / name
    return found


def git(*args):
    import subprocess
    return subprocess.check_output(('git',) + args, cwd=ROOT, text=True).strip()


def check_repository():
    if git('rev-parse', '--abbrev-ref', 'HEAD') != 'experiment/recent-geometry':
        raise ValueError('Wrong branch')
    if subprocess_ok('merge-base', '--is-ancestor', BASE_COMMIT, 'HEAD') is False:
        raise ValueError('Head does not descend from the base commit')
    changed = [line for line in git('diff', '--name-only', BASE_COMMIT).splitlines() if line]
    other = [name for name in changed if not name.startswith(NEW_FILES_PREFIXES)]
    if other:
        raise ValueError('Existing files changed: ' + ','.join(other))
    return git('rev-parse', 'HEAD')


def subprocess_ok(*args):
    import subprocess
    return subprocess.run(('git',) + args, cwd=ROOT, capture_output=True).returncode == 0


def freeze(run_id):
    import memory_ablation_protocol as p
    private, public = run_paths(run_id)
    parity_path = public / 'distance-parity.json'
    if not parity_path.is_file() or read_json(parity_path)['status'] != 'exact':
        raise ValueError('Exact distance-recompute parity is required before the freeze')
    head = check_repository()
    env = p.environments(ROOT)
    bindings = verified_bindings()
    private.mkdir(parents=True, exist_ok=True)
    sources = {name: file_sha(path) for name, path in source_paths().items()}
    value = dict(schema_version=1, run_id=run_id, created_utc=utc(), head_commit=head, protocol=protocol_parameters(),
                 protocol_doc_sha256=sources[PROTOCOL_DOC], source_sha256=sources,
                 input_sha256={c: {cid: b['expected'] for cid, b in group.items()} for c, group in bindings.items()},
                 environment=p.public_environment(env), distance_parity_sha256=file_sha(parity_path))
    store_exact(public / 'freeze.json', value)
    store_exact(private / 'environment-map.json', env, public=False)
    store_exact(private / 'input-map.json', {c: {cid: {k: str(Path(v).resolve()) for k, v in b['files'].items()}
                                                 for cid, b in group.items()} for c, group in bindings.items()}, public=False)
    store_exact(private / 'freeze-anchor.json', dict(freeze_sha256=file_sha(public / 'freeze.json')), public=False)
    open_ledger(run_id).event('frozen', freeze_sha256=file_sha(public / 'freeze.json'))
    return dict(status='frozen', freeze_sha256=file_sha(public / 'freeze.json'), head_commit=head)


def frozen(run_id, role=None):
    """Re-verify the freeze: sources, inputs, protocol and (optionally) the executing runtime."""
    import memory_ablation_protocol as p
    private, public = run_paths(run_id)
    freeze_value = read_json(public / 'freeze.json')
    if file_sha(public / 'freeze.json') != read_json(private / 'freeze-anchor.json')['freeze_sha256']:
        raise ValueError('Freeze changed')
    if {name: file_sha(path) for name, path in source_paths().items()} != freeze_value['source_sha256']:
        raise ValueError('Sources changed since the freeze')
    if freeze_value['protocol'] != protocol_parameters():
        raise ValueError('Protocol parameters changed since the freeze')
    bindings = verified_bindings()
    if {c: {cid: b['expected'] for cid, b in group.items()} for c, group in bindings.items()} != freeze_value['input_sha256']:
        raise ValueError('Input identities changed since the freeze')
    if role:
        if p.runtime_info(training=(role == 'training')) != freeze_value['environment'][role]:
            raise ValueError('Executing runtime differs from the freeze')
    return freeze_value, bindings


# ----- private per-case arrays -------------------------------------------------------------------

def array_identity(arrays):
    from recent_geometry_training import array_identity as identity
    return identity(arrays)


def save_arrays(path, arrays):
    import numpy as np
    path = Path(path)
    if path.exists():
        raise FileExistsError(str(path))
    with path.open('xb') as handle:
        np.savez_compressed(handle, **arrays)


def load_arrays(path, expected_identity=None):
    import numpy as np
    with np.load(path, allow_pickle=False) as data:
        arrays = {key: data[key] for key in data.files}
    if expected_identity is not None and array_identity(arrays) != expected_identity:
        raise ValueError('Private case arrays changed')
    return arrays


def adapter_load(ledger, cid, bindings, purpose):
    from memory_ablation_run import load_evaluation
    ledger.event('evaluation_adapter_entry', case_id=cid, purpose=purpose,
                 reference_container_may_be_parsed=not cid.startswith('wcsf'))
    return load_evaluation(cid, bindings['evaluation'][cid])


# ----- preflight: masks, sealing, support qualification, feature-prefix parity ----------------------

def preflight(run_id):
    import numpy as np
    from gap_solver.tactical import feature_rows
    import recent_geometry_features as rf
    import recent_geometry_metrics as m
    import recent_geometry_regimes as rr
    freeze_value, bindings = frozen(run_id, 'scoring')
    private, public = run_paths(run_id)
    if (public / 'preflight.json').exists() or (private / 'cases').exists():
        raise ValueError('Preserve prior preflight attempts')
    ledger = open_ledger(run_id)
    (private / 'cases').mkdir()
    cases = {}
    for cid in NATURAL_CASES:
        loaded = adapter_load(ledger, cid, bindings, 'preflight')
        frames = loaded['frames']
        reference = np.asarray(loaded['reference']())
        ledger.event('reference_codes_entry', case_id=cid, already_parsed_by_adapter=loaded['reference_loaded_by_adapter'])
        periods = np.asarray([f.period for f in frames], dtype=np.uint8)
        observed = np.asarray([f.ball_observed for f in frames], dtype=bool)
        ledger.claim('feature_pass', f'natural/{cid}/prep')
        rows = list(rf.research_rows(frames))
        ledger.claim('parity', f'prefix/{cid}')
        base = list(feature_rows(frames))
        if len(rows) != len(base) or any(tuple(r[:18]) != tuple(b) for r, b in zip(rows, base)):
            raise ValueError('Feature-prefix mismatch on ' + cid)
        matrix = np.asarray(rows, dtype=np.float32)
        if not np.isfinite(matrix).all():
            raise ValueError('Non-finite research features on ' + cid)
        gt = np.where(periods > 0, reference, 3).astype(np.uint8)
        live = rr.live_gap_windows(cid, periods, reference, observed)
        arrays = dict(reference=reference.astype(np.uint8), matrix=matrix, live=live['mask'])
        sealed = dict(live=live['mask'])
        stoppage = None
        if cid in STOPPAGE_CASES:
            stoppage = rr.stoppage_mask(periods, reference)
            arrays['stoppage'] = stoppage
            sealed['stoppage'] = stoppage
        events, ungroupable = m.restart_events(gt, periods)
        save_arrays(private / 'cases' / (cid + '.npz'), arrays)
        cases[cid] = dict(rows=len(frames), natural_observed_rows=int(observed.sum()), feature_prefix='identical',
                          live_windows_eligible=len(live['eligible']), live_windows_selected=len(live['selected']),
                          live_masked_rows=int(live['mask'].sum()),
                          stoppage_masked_rows=None if stoppage is None else int(stoppage.sum()),
                          restart_events_eligible=len(events), restart_events_ungroupable=ungroupable,
                          mask_seal_sha256=rr.seal_digest(sealed), case_arrays_sha256=array_identity(arrays))
        ledger.event('preflight_case', case_id=cid, **{k: v for k, v in cases[cid].items() if k != 'rows'})
        del loaded, frames, rows, base
    windows = {p: sum(c['live_windows_selected'] for cid, c in cases.items() if provider_of(cid) == p and is_primary(cid)) for p in PROVIDERS}
    events = {p: sum(cases[cid]['restart_events_eligible'] for cid in ids) for p, ids in PRIMARY_RESTART.items()}
    problems = [f'live-gap windows {p}={n}' for p, n in windows.items() if n < m.MIN_LIVE_WINDOWS]
    problems += [f'restart events {p}={n}' for p, n in events.items() if n < m.MIN_RESTART_EVENTS]
    value = dict(schema_version=1, status='blocked_insufficient_support' if problems else 'ready', problems='; '.join(problems),
                 live_windows_selected_by_provider=windows, restart_events_eligible_by_provider=events, cases=cases,
                 freeze_sha256=file_sha(public / 'freeze.json'), created_utc=utc())
    store_exact(public / 'preflight.json', value)
    return dict(status=value['status'], problems=value['problems'], windows=windows, events=events)


def require(public, name, status_key='status', ok=('ready', 'complete', 'passed')):
    path = public / name
    if not path.is_file():
        raise ValueError('Missing prerequisite ' + name)
    value = read_json(path)
    if value.get(status_key) not in ok:
        raise ValueError(f'Prerequisite {name} did not pass: {value.get(status_key)}')
    return value


# ----- fit -----------------------------------------------------------------------------------------

def load_training_groups(input_map, expected):
    from gap_solver.external import load_cache
    from memory_ablation_training import TRAIN_MATCHES
    groups = []
    for match in TRAIN_MATCHES:
        files = input_map['training'][match]
        for key, path in files.items():
            if file_sha(path) != expected['training'][match][key]:
                raise ValueError('Training input identity differs')
        features = next(path for path in files.values() if str(path).endswith('.features.npz'))
        data = load_cache(Path(str(features)[:-len('.features.npz')]))
        if data.match_id != 'DFL-MAT-' + match:
            raise ValueError('Training cache match identity differs')
        groups.append(dict(match=match, frames=data.frames(), reference=data.reference, periods=data.periods))
    return groups


def fit_worker(run_id):
    """Runs under the pinned training interpreter.  Exactly two fits, control first."""
    import recent_geometry_training as rt
    freeze_value, _ = frozen(run_id, 'training')
    private, public = run_paths(run_id)
    require(public, 'preflight.json', ok=('ready',))
    if (public / 'fit.json').exists() or (private / 'fit.incomplete').exists():
        raise ValueError('Preserve consumed or interrupted fitting attempts')
    store_exact(private / 'fit.incomplete', dict(utc=utc()), public=False)
    ledger = open_ledger(run_id)
    freeze_sha = file_sha(public / 'freeze.json')
    ledger.event('training_reference_cache_entry', reference_container_parsed=True)
    groups = load_training_groups(read_json(private / 'input-map.json'), freeze_value['input_sha256'])
    pair = rt.prepare_pair(groups)
    rt.require_rows(pair)                                      # 228,776 or stop

    def arrays(d):
        return dict(matrix=d.matrix, target=d.target, weights=d.weights, row_identity=d.row_identity)

    control_identity = rt.array_identity(arrays(pair.control))
    candidate_identity = rt.array_identity(arrays(pair.candidate))
    save_arrays(private / 'training-control.npz', arrays(pair.control))
    save_arrays(private / 'training-candidate.npz', arrays(pair.candidate))
    base = dict(schema_version=1, freeze_sha256=freeze_sha, rows=len(pair.control.matrix),
                training_semantic_sha256=control_identity, expected_training_semantic_sha256=rt.CONTROL_TRAINING_SEMANTIC_SHA,
                candidate_training_semantic_sha256=candidate_identity, prefix_semantic_sha256=pair.prefix_semantic_sha256)
    if control_identity != rt.CONTROL_TRAINING_SEMANTIC_SHA:
        store_exact(public / 'fit.json', dict(base, status='stopped_training_identity_mismatch', fits=0))
        return dict(status='stopped_training_identity_mismatch', fits=0)

    def summary(results):
        out = {}
        for mode, row in results.items():
            out[mode + '_model_sha256'] = row['model_sha256']
            out[mode + '_nodes'] = row['node_count']
            out[mode + '_depth'] = row['depth']
            out[mode + '_parity_max_abs_diff'] = row['parity_max_abs_diff']
        if 'candidate' in results:
            out['appended_columns_used'] = ','.join(map(str, results['candidate']['appended_columns_used'])) or 'none'
            out['appended_splits'] = '; '.join(f"node {s['node']}: {s['name']} <= {s['threshold']:.9g}"
                                               for s in results['candidate']['appended_splits']) or 'none'
            out['all_split_features'] = ','.join(map(str, results['candidate']['split_features']))
        return out

    try:
        results = rt.fit_research(pair.control, pair.candidate, lambda mode: ledger.claim('fit', mode))
    except rt.ControlMismatch as error:
        store_exact(private / 'failed-control-model.json', error.model, public=False)
        store_exact(public / 'fit.json', dict(base, status='stopped_control_mismatch', fits=1,
                    control_model_sha256=error.receipt['model_sha256'], expected_control_model_sha256=rt.MODEL_SHA))
        return dict(status='stopped_control_mismatch', fits=1)
    except rt.UnusedRepresentation as error:
        results = error.results
        directory = public / 'models'
        directory.mkdir()
        for mode, row in results.items():
            store_exact(directory / (mode + '.json'), row, public=False)
        store_exact(public / 'fit.json', dict(base, status='stopped_unused_representation', fits=2,
                    expected_control_model_sha256=rt.MODEL_SHA, **summary(results)))
        return dict(status='stopped_unused_representation', fits=2)
    directory = public / 'models'
    directory.mkdir()
    for mode, row in results.items():
        store_exact(directory / (mode + '.json'), row, public=False)
    value = dict(base, status='complete', fits=2, expected_control_model_sha256=rt.MODEL_SHA,
                 control_model_matches_expected=results['control']['model_sha256'] == rt.MODEL_SHA,
                 model_artifact_sha256={mode: file_sha(directory / (mode + '.json')) for mode in results}, **summary(results))
    store_exact(public / 'fit.json', value)
    (private / 'fit.incomplete').unlink()
    return dict(status='complete', fits=2)


def fit(run_id):
    import subprocess
    import memory_ablation_protocol as p
    frozen(run_id)
    private, public = run_paths(run_id)
    require(public, 'preflight.json', ok=('ready',))
    env = read_json(private / 'environment-map.json')
    result = subprocess.run([env['training_python'], str(ROOT / 'recent_geometry_run.py'), 'fit', '--run-id', run_id, '--worker'],
                            cwd=ROOT, env=p.thread_environment(), capture_output=True, text=True)
    for name, text in (('fit-worker.stdout.log', result.stdout), ('fit-worker.stderr.log', result.stderr)):
        with (private / name).open('x', encoding='utf-8') as handle:
            handle.write(text)
    if result.returncode:
        raise ValueError('Pinned training worker stopped; private logs retained')
    return json.loads(result.stdout.strip().splitlines()[-1])


def load_models(public):
    fit_value = require(public, 'fit.json', ok=('complete',))
    models = {}
    for mode in ('control', 'candidate'):
        row = read_json(public / 'models' / (mode + '.json'))
        if file_sha(public / 'models' / (mode + '.json')) != fit_value['model_artifact_sha256'][mode]:
            raise ValueError('Model artifact changed')
        models[mode] = row['model']
    return models, fit_value


# ----- parity: exporter, feature prefix, release, reconciliation ----------------------------------

def reconcile_against_history(score, historical):
    """Primary scalar to 1e-9 and every per-IoU matched/missed/spurious count exactly."""
    from math import isclose
    ok = isclose(score['metrics']['spell_f1_mean'], historical['metrics']['spell_f1_mean'], rel_tol=0, abs_tol=1e-9)
    ok = ok and (score['spells']['n_gt'], score['spells']['n_pred']) == (historical['spells']['n_gt'], historical['spells']['n_pred'])
    ok = ok and set(score['spells']['per_iou']) == set(historical['spells']['per_iou'])
    for threshold, row in historical['spells']['per_iou'].items():
        got = score['spells']['per_iou'].get(threshold, {})
        ok = ok and all(got.get(k) == row[k] for k in ('n_matched', 'n_missed', 'n_spurious'))
    return bool(ok)


def primary_natural_check(f1_by_case, historical_summary):
    """Provider-weighted primary natural mean must be 0.551816 (1e-6) and the historical summary value (1e-9)."""
    import recent_geometry_metrics as m
    primary, _ = m.weighted(f1_by_case, 'natural')
    ok = primary is not None and abs(primary - 0.551816) <= 1e-6 and abs(primary - historical_summary) <= 1e-9
    return primary, bool(ok)


def parity(run_id):
    """Implementation verification (ledger category 'parity'); only reconciliation scoring is science budget."""
    import numpy as np
    import recent_geometry_assembly as ra
    import recent_geometry_metrics as m
    from memory_ablation_metrics import score_variant
    import restart_release
    freeze_value, bindings = frozen(run_id, 'scoring')
    private, public = run_paths(run_id)
    if (public / 'parity.json').exists():
        raise ValueError('Preserve prior parity attempt')
    preflight_value = require(public, 'preflight.json', ok=('ready',))
    models, fit_value = load_models(public)
    ledger = open_ledger(run_id)
    ledger.claim('parity', 'exporter')
    ledger.event('exporter_parity', max_abs_diff=fit_value['candidate_parity_max_abs_diff'])
    if fit_value['candidate_parity_max_abs_diff'] > 1e-12 or fit_value['control_parity_max_abs_diff'] > 1e-12:
        raise ValueError('Exporter parity failed')
    historical_dir = ROOT / 'reports/memory-ablation/2026-11-09-v3'
    cases, f1 = {}, {}
    for cid in NATURAL_CASES:
        arrays = load_arrays(private / 'cases' / (cid + '.npz'), preflight_value['cases'][cid]['case_arrays_sha256'])
        loaded = adapter_load(ledger, cid, bindings, 'parity')
        frames = loaded['frames']
        ledger.claim('parity', f'release/{cid}')
        real = restart_release.assemble(frames, (), use_restart=True)
        support = ra.SupportSet.from_matrix('control', arrays['matrix'], models['control'])
        replica = ra.assemble_research(frames, support, verify_decoder=True)
        same = {name: getattr(real, name) == getattr(replica, name)
                for name in ('control', 'gapped', 'restarted', 'final', 'stoppage_gaps', 'gap_summary', 'kickoff_changed')}
        if not all(same.values()):
            raise ValueError('Release parity failed on ' + cid)
        periods = np.asarray([f.period for f in frames], dtype=np.uint8)
        observed = np.asarray([f.ball_observed for f in frames], dtype=bool)
        ledger.claim('score', f'reconcile/{cid}')
        score = score_variant(arrays['reference'], encode(replica.control), periods, observed)
        historical = read_json(historical_dir / f'{cid}--natural.json')['variants']['control']
        if not reconcile_against_history(score, historical):
            raise ValueError('Historical reconciliation failed on ' + cid)
        f1[cid] = score['metrics']['spell_f1_mean']
        cases[cid] = dict(release_parity=True, reconciliation=True, spell_f1_intermediate=f1[cid],
                          historical_spell_f1=historical['metrics']['spell_f1_mean'])
        ledger.event('parity_case', case_id=cid, **cases[cid])
        del loaded, frames, real, replica
    historical_summary = read_json(historical_dir / 'summary.json')['primary']['natural']['control']
    primary, reproduced = primary_natural_check(f1, historical_summary)
    if not reproduced:
        raise ValueError('Primary natural mean not reproduced')
    value = dict(schema_version=1, status='passed', release_parity_cases=15, reconciliation_cases=15,
                 feature_prefix_cases=15, exporter_parity_max_abs_diff=fit_value['candidate_parity_max_abs_diff'],
                 primary_natural_mean=primary, historical_primary_natural_mean=historical_summary,
                 primary_reproduced_to_1e6=True, cases=cases, freeze_sha256=file_sha(public / 'freeze.json'), created_utc=utc())
    store_exact(public / 'parity.json', value)
    return dict(status='passed', primary_natural_mean=primary)


# ----- stages ---------------------------------------------------------------------------------------

def public_verdict(named_gates):
    import recent_geometry_metrics as m
    result = m.verdict(named_gates)
    return dict(verdict=result['verdict'], failing={name: 'not_passed' for name in result['failing']}, assessed=result['assessed'])


def _flats(receipts):
    return {cid: row['flats'] for cid, row in receipts.items()}


def _store_case(public, regime, receipt, cid, preflight_case):
    value = dict(receipt, role='primary' if is_primary(cid) else 'secondary', provider=provider_of(cid),
                 case_arrays_sha256=preflight_case['case_arrays_sha256'])
    store_exact(public / f'{cid}--{regime}.json', value)
    return value


def natural(run_id):
    """Stage 1.  Gates 1, 3, 4, the owner-presence check and gate 2's per-match natural bound."""
    import recent_geometry_metrics as m
    freeze_value, bindings = frozen(run_id, 'scoring')
    private, public = run_paths(run_id)
    if (public / 'stage1.json').exists() or (private / 'predictions').exists():
        raise ValueError('Preserve prior stage-1 attempt')
    preflight_value = require(public, 'preflight.json', ok=('ready',))
    require(public, 'parity.json', ok=('passed',))
    models, _ = load_models(public)
    ledger = open_ledger(run_id)
    ledger.event('stage_start', stage='natural')
    (private / 'predictions').mkdir()
    receipts = {}
    for cid in NATURAL_CASES:
        arrays = load_arrays(private / 'cases' / (cid + '.npz'), preflight_value['cases'][cid]['case_arrays_sha256'])
        loaded = adapter_load(ledger, cid, bindings, 'natural')
        receipt = run_case_regime(ledger, 'natural', cid, loaded['frames'], arrays['reference'], models,
                                  private / 'predictions' / f'natural--{cid}', matrix=arrays['matrix'])
        receipts[cid] = _store_case(public, 'natural', receipt, cid, preflight_value['cases'][cid])
        ledger.event('case_complete', case_id=cid, regime='natural')
        del loaded, arrays
    flats = _flats(receipts)
    gates = {'G1_natural_benefit': m.gate_natural_benefit(flats), 'G2_natural_match_loss': m.gate_loss(flats, 'natural'),
             'G3_natural': m.gate_dead_and_owners(flats, 'natural'), 'G4_natural': m.gate_short_spells(flats, 'natural')}
    outcome = public_verdict(gates)
    control, candidate = ({cid: flats[cid][k]['spell_f1'] for cid in flats} for k in m.METHODS)
    value = dict(schema_version=1, status='complete', decision=outcome['verdict'], advance_to_stage2=outcome['verdict'] == 'PASS',
                 failing=outcome['failing'], gates=gates,
                 primary_spell_f1=dict(control=m.weighted(control, 'natural')[0], candidate=m.weighted(candidate, 'natural')[0]),
                 provider_spell_f1=dict(control=m.weighted(control, 'natural')[1], candidate=m.weighted(candidate, 'natural')[1]),
                 case_receipts=len(receipts), created_utc=utc())
    store_exact(public / 'stage1.json', value)
    ledger.event('stage_end', stage='natural', decision=outcome['verdict'])
    return dict(decision=outcome['verdict'], failing=sorted(outcome['failing']))


def stress(run_id):
    """Stage 2, only after a stage-1 pass: noise, pure live gaps, stoppage and reacquisition."""
    import recent_geometry_metrics as m
    import recent_geometry_regimes as rr
    freeze_value, bindings = frozen(run_id, 'scoring')
    private, public = run_paths(run_id)
    stage1 = require(public, 'stage1.json', ok=('complete',))
    if not stage1['advance_to_stage2']:
        raise ValueError('Stage 1 did not pass; stress is not run')
    if (public / 'stage2.json').exists():
        raise ValueError('Preserve prior stage-2 attempt')
    preflight_value = require(public, 'preflight.json', ok=('ready',))
    models, _ = load_models(public)
    ledger = open_ledger(run_id)
    ledger.event('stage_start', stage='stress')
    receipts = {'noise': {}, 'live-gap': {}, 'stoppage': {}}
    for cid in NATURAL_CASES:
        info = preflight_value['cases'][cid]
        arrays = load_arrays(private / 'cases' / (cid + '.npz'), info['case_arrays_sha256'])
        sealed = dict(live=arrays['live'])
        if 'stoppage' in arrays:
            sealed['stoppage'] = arrays['stoppage']
        if rr.seal_digest(sealed) != info['mask_seal_sha256']:
            raise ValueError('Sealed masks changed before use')
        loaded = adapter_load(ledger, cid, bindings, 'stress')
        frames = loaded['frames']
        inputs = {'noise': rr.add_visible_ball_noise(frames, cid), 'live-gap': rr.apply_ball_mask(frames, arrays['live'])}
        if 'stoppage' in arrays:
            inputs['stoppage'] = rr.apply_ball_mask(frames, arrays['stoppage'])
        for regime, transformed in inputs.items():
            receipt = run_case_regime(ledger, regime, cid, transformed, arrays['reference'], models,
                                      private / 'predictions' / f'{regime}--{cid}')
            receipts[regime][cid] = _store_case(public, regime, receipt, cid, info)
            ledger.event('case_complete', case_id=cid, regime=regime)
        del loaded, frames, inputs, arrays
    flats = {regime: _flats(rows) for regime, rows in receipts.items()}
    gates = {}
    for regime, key in (('noise', 'noise'), ('live-gap', 'live'), ('stoppage', 'stoppage')):
        gates[f'G2_{key}'] = m.gate_loss(flats[regime], regime)
        gates[f'G3_{key}'] = m.gate_dead_and_owners(flats[regime], regime)
        gates[f'G4_{key}'] = m.gate_short_spells(flats[regime], regime)
    gates['G5_noise_mechanism'] = m.gate_noise_mechanism(flats['noise'])
    gates['G6_support_restart'] = m.gate_support_and_restart(
        flats['stoppage'], preflight_value['live_windows_selected_by_provider'], preflight_value['restart_events_eligible_by_provider'])
    value = dict(schema_version=1, status='complete', gates=gates, created_utc=utc(),
                 primary_spell_f1={regime: dict(
                     control=m.weighted({c: f[c]['control']['spell_f1'] for c in f}, regime)[0],
                     candidate=m.weighted({c: f[c]['candidate']['spell_f1'] for c in f}, regime)[0]) for regime, f in flats.items()},
                 interior_changes={regime: {cid: row['interior_changes'] for cid, row in rows.items()} for regime, rows in receipts.items()})
    store_exact(public / 'stage2.json', value)
    ledger.event('stage_end', stage='stress')
    return dict(status='complete')


def summarise(run_id):
    """Aggregate verdict.  A pass authorises nothing beyond a separate release decision."""
    import recent_geometry_metrics as m
    private, public = run_paths(run_id)
    parts = {}
    for name in ('freeze', 'distance-parity', 'preflight', 'fit', 'parity', 'stage1', 'stage2'):
        if (public / (name + '.json')).is_file():
            parts[name] = read_json(public / (name + '.json'))
    gates = {}
    if 'stage1' in parts:
        gates.update(parts['stage1']['gates'])
    if 'stage2' in parts:
        gates.update(parts['stage2']['gates'])
    stopped = next((f"{n}:{parts[n]['status']}" for n in ('preflight', 'fit', 'parity') if n in parts and parts[n]['status'] not in ('ready', 'complete', 'passed')), '')
    if stopped:
        outcome = dict(verdict='FAIL', failing={stopped: 'stopped'}, assessed=0)
    elif 'stage1' in parts and not parts['stage1']['advance_to_stage2']:
        outcome = public_verdict(gates)
    elif 'stage2' in parts:
        outcome = public_verdict(gates)
    else:
        outcome = dict(verdict='INCOMPLETE', failing={}, assessed=len(gates))
    names = dict(fit='fits', prediction='case_runs', score='score_bundles', feature_pass='feature_tree_passes',
                 decoder_pass='decoder_passes', parity='parity_checks')
    ledger_counts = {names[kind]: len(list((PRIVATE_ROOT / 'claims').glob(kind + '--*.json'))) for kind in list(CAPS) + ['parity']}
    events = [json.loads(line) for line in (private / 'access.jsonl').read_text(encoding='utf-8').splitlines()]
    stages = {e['stage'] + '_' + e['event'][6:]: e['utc'] for e in events if e['event'] in ('stage_start', 'stage_end')}
    tables = {}
    for regime in m.REGIMES:
        suffix = {'live-gap': 'live-gap'}.get(regime, regime)
        rows = {}
        for cid in NATURAL_CASES:
            path = public / f'{cid}--{suffix}.json'
            if path.is_file():
                rows[cid] = read_json(path)['flats']
        if rows:
            tables[regime] = rows
    text = {'PASS': 'PASS - qualifies for a separate release decision', 'FAIL': 'FAIL', 'INCOMPLETE': 'INCOMPLETE'}[outcome['verdict']]
    value = dict(schema_version=1, verdict=text, failing_checks=outcome['failing'], checks_assessed=outcome['assessed'],
                 stage2_run='stage2' in parts, budget_used=ledger_counts, budget_caps={names[k]: v for k, v in CAPS.items()}, stage_timestamps=stages,
                 tables=tables, authorises='nothing beyond a separate release decision', created_utc=utc())
    target = public / 'summary.json'
    store_exact(target, value)
    return dict(verdict=text, failing=sorted(outcome['failing']), budget=ledger_counts)


COMMANDS = ('distance-parity', 'freeze', 'preflight', 'fit', 'parity', 'natural', 'stress', 'summarise')


def main(argv=None):
    import argparse
    import sys
    import traceback
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=COMMANDS)
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--worker', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    try:
        if args.worker and args.command != 'fit':
            raise ValueError('Invalid worker command')
        if args.worker:
            result = fit_worker(args.run_id)
        else:
            result = globals()[args.command.replace('-', '_')](args.run_id)
        print(json.dumps(result, sort_keys=True, default=str))
        return 0 if result.get('status') not in ('NOT_EXACT_STOP',) else 2
    except Exception:
        private, _ = run_paths(args.run_id)
        if private.is_dir():
            try:
                with (private / ('execution-error-' + args.command + ('-worker' if args.worker else '') + '.log')).open('x', encoding='utf-8') as handle:
                    handle.write(traceback.format_exc())
            except OSError:
                pass
        sys.stderr.write('Stopped; preserve this generation and inspect the private execution log.\n')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
