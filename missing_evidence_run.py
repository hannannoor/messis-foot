"""Experiment F orchestration: freeze / preflight / parity / natural / stress / summarise, with a budget ledger.

No fit: visible rows use Experiment E's committed control tree and missing-ball rows its committed candidate
(stillness) tree, both pinned by artifact SHA-256.

Heavy protocol modules are imported lazily inside commands so the ledger stays testable in isolation.
Private arrays live outside Git under PRIVATE_ROOT; only aggregates are written to reports/missing-evidence.
"""
import json
from pathlib import Path
import re

from datetime import datetime, timezone

EXPERIMENT = 'missing-evidence-2026-11-12'
BRANCH = 'experiment/missing-evidence'
ROOT = Path(__file__).resolve().parent
PRIVATE_ROOT = Path.home() / "Documents/ChatGPT/MESSI's FOOT/missing-evidence-reference"
BASE_COMMIT = '83b203e76bb8c5cf754e7fa3593980f4c9c1f85b'
JITTER_PREFIX = 'missing-evidence-jitter-v1:1729:'
E_RUN = ROOT / 'reports/player-stillness/2026-11-12-a'
MODEL_FILES = {'control': (E_RUN / 'models/control.json', '061780ef57a57e663ef1770ba5e38d97b320550b1ff622c8222ed8c0060e7a47'),
               'candidate': (E_RUN / 'models/candidate.json', '36f78e793e3ad295551743653f43362f51c5cc9dc2d6e7eac130dedff8357ef4')}
MODEL_SHA = dict(control='363c45c70838b398cd87aee7474d7e281fd392f059a31b85712e312058aaab4d',
                 candidate='4c5467062e327d11b38f7c34117a9bb33ef853c2faba0ba3efcd9acc2fd69f0e')
E_PRIVATE = Path.home() / "Documents/ChatGPT/MESSI's FOOT/player-stillness-reference/2026-11-12-a"


def supplied_support(method, matrix, model):
    from recent_geometry_assembly import SupportSet
    from memory_ablation import predict_supports
    from player_stillness_training import predict_supports_research
    if method == 'control':
        return SupportSet(method, predict_supports(matrix[:, :18], model))
    if method == 'candidate':
        return SupportSet(method, predict_supports_research(matrix, model))
    raise ValueError('Unknown method')


def pinned_environments():
    """Reuse the existing pinned installations; install/copy nothing."""
    import memory_ablation_protocol as p
    env = p.environments(ROOT.parent / 'competition-release-work')
    old = read_json(ROOT / 'reports/recent-geometry/2026-11-12-a/freeze.json')['environment']
    if p.public_environment(env) != old:
        raise ValueError('Pinned environments differ from Experiment A')
    return env


def loader_midpoint(cid, binding):
    """Apply each loader's native-centre mapping; require exact equality to 52.65."""
    from team_shape_features import provider_midpoint
    if cid == 'wcsf-used-match':
        return provider_midpoint('wcsf')
    path = next(v for k,v in binding['files'].items() if k.endswith('.metadata.json'))
    return provider_midpoint(provider_of(cid),read_json(path)['notes'])


def enforce_cutoff(stage, at=None):
    from datetime import timedelta
    local = timezone(timedelta(hours=8))
    now = datetime.now(timezone.utc) if at is None else at
    limit = datetime(2026,11,16,12,0,tzinfo=local) if stage == 'stress' else datetime(2026,11,15,23,59,tzinfo=local)
    if now.tzinfo is None or now > limit:
        raise ValueError('Fixed calendar cutoff missed: ' + stage)


def require_open_study(public):
    if (Path(public)/'stop.json').exists():
        raise ValueError('Study already stopped; reporting only')


def verdict_cutoff(public, at=None):
    try:
        enforce_cutoff('stress',at)
    except ValueError:
        path=Path(public)/'stop.json'
        if not path.exists():
            store_exact(path,dict(schema_version=1,status='stopped',command='full-verdict-cutoff',
                                 error_type='CalendarCutoff',created_utc=utc()))


def add_visible_ball_noise(frames, cid):
    """Experiment A's noise generator, changed only to the prospective F seed prefix."""
    from dataclasses import replace
    import hashlib
    import random
    from math import isfinite
    from recent_geometry_regimes import JITTER_SIGMA, _nearest
    seed = int(hashlib.sha256((JITTER_PREFIX + cid).encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)
    out = []
    for f in frames:
        if not f.ball_observed:
            out.append(f)
            continue
        x,y = f.ball_x + rng.gauss(0,JITTER_SIGMA), f.ball_y + rng.gauss(0,JITTER_SIGMA)
        ds = [_nearest(f.home_xy,x,y), _nearest(f.away_xy,x,y)]
        if not all(isfinite(v) for v in (x,y)) or any(d is not None and not isfinite(d) for d in ds):
            raise ValueError('Non-finite transformed record')
        out.append(replace(f,ball_x=x,ball_y=y,home_distance=ds[0],away_distance=ds[1]))
    return out

# Science budget (section 10).  Claimed on entry, cumulative across run ids, never refunded.
CAPS = dict(fit=0, prediction=100, score=115, feature_pass=200, decoder_pass=300)
FIT_ORDER = ('control', 'candidate')
# Public-report-safe names for ledger kinds (the guard rejects keys such as 'prediction').
PUBLIC_NAMES = dict(fit='fits', prediction='case_runs', score='score_bundles', feature_pass='feature_tree_passes',
                    decoder_pass='decoder_passes', parity='parity_checks')

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
        """Run-scoped parity identities only (the claims folder is shared across runs)."""
        parts = identity.split('/')
        if len(parts) < 2:
            return False
        safe_run_id(parts[1])
        return len(parts) == 3 and parts[0] in ('release', 'prefix', 'equivalence', 'still-supports') and parts[2] in NATURAL_CASES

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
    public = ROOT / 'reports/missing-evidence' / run_id
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
    recorded = read_json(ROOT / 'reports/recent-geometry/2026-11-12-a/freeze.json')['input_sha256']
    current = {name:{cid:b['expected'] for cid,b in group.items()} for name,group in bindings.items()}
    if current != recorded:
        raise ValueError('Inputs differ from Experiment A freeze')
    return bindings


# ----- pre-freeze: distance recomputation parity -------------------------------------------------

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

def run_case_regime(ledger, regime, cid, frames, reference, models, directory, *, matrix=None, prep_claimed=False, pitch_midpoint=None, hidden_live=None):
    """Predict with both methods on identical transformed inputs and score the final labels.

    Control: the release flow on the control tree's supports.  Candidate: the same control supports on visible
    rows plus E-tree dead-ball evidence at LAMBDA on missing-ball rows.  One feature/tree claim per tree: the
    control tree under the control identity, the stillness tree under the candidate identity.
    ``reference`` is evaluation machinery used only to score.
    """
    import numpy as np
    import recent_geometry_assembly as ra
    import player_stillness_features as rf
    import recent_geometry_metrics as metrics
    from missing_evidence import LAMBDA, assemble_missing
    frames = list(frames)
    periods = np.asarray([f.period for f in frames], dtype=np.uint8)
    observed = np.asarray([f.ball_observed for f in frames], dtype=bool)
    reference = np.asarray(reference)
    if reference.shape != periods.shape:
        raise ValueError('Reference/frame dimensions differ')
    if hidden_live is not None:
        hidden_live = np.asarray(hidden_live, dtype=bool)
        if hidden_live.shape != periods.shape or regime != 'live-gap':
            raise ValueError('Invalid hidden-live scoring mask')
    if matrix is None:
        if not prep_claimed:
            ledger.claim('feature_pass', f'{regime}/{cid}/prep')
        matrix = rf.stillness_matrix(frames)
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    bundles, finals, latents = {}, {}, {}
    control_support = still_support = None
    for method in metrics.METHODS:
        identity = f'{regime}/{cid}/{method}'
        ledger.claim('prediction', identity)
        ledger.claim('feature_pass', identity + '/tree')
        if method == 'control':
            control_support = supplied_support('control', matrix, models['control'])
        else:
            still_support = supplied_support('candidate', matrix, models['candidate'])
        expected_passes = 2
        for k in range(expected_passes):
            ledger.claim('decoder_pass', f'{identity}/{k}')
        if method == 'control':
            assembly = ra.assemble_research(frames, control_support)
        else:
            assembly = assemble_missing(frames, control_support, still_support, lam=LAMBDA)
        if assembly.decoder_passes != expected_passes:
            raise ValueError('Decoder pass accounting differs from the claim')
        final = encode(assembly.final)
        finals[method], latents[method] = final, encode(assembly.latent)
        ledger.claim('score', identity)
        bundles[method] = metrics.score_bundle(reference, final, periods, observed, restart=(regime == 'stoppage'))
        arrays = dict(supports=control_support.supports, latent=latents[method], final=final)
        if method == 'candidate':
            arrays['still_supports'] = still_support.supports
        np.savez_compressed(directory / (method + '.npz'), **arrays)
    gt = np.where(periods > 0, reference, 3).astype(np.uint8)
    transitions = metrics.interior_transitions(gt, finals['control'], finals['candidate'], periods, observed,
                                               latents['control'], latents['candidate'])
    graded = (periods > 0) & ~observed
    to_d = graded & (finals['candidate'] == 2) & (finals['control'] != 2)
    receipt = dict(schema_version=1, regime=regime, case_id=cid, bundles=bundles,
                flats={m: metrics.flatten(bundles[m]) for m in metrics.METHODS}, interior_changes=transitions,
                input_summary=dict(rows=len(frames), observed_rows=int(observed.sum())),
                missing_rows_to_d=dict(rows=int(to_d.sum()), correct=int((to_d & (reference == 2)).sum()),
                                       missing_rows=int(graded.sum())))
    if hidden_live is not None:
        take = hidden_live & (periods > 0) & (reference < 2)
        n = int(take.sum())
        receipt['hidden_live'] = dict(rows=n, **{
            method:dict(correct=int((finals[method][take] == reference[take]).sum()),
                        strict_team_accuracy=float((finals[method][take] == reference[take]).mean()) if n else None)
            for method in metrics.METHODS})
    return receipt


# ----- protocol identity and freeze --------------------------------------------------------------

PROTOCOL_DOC = 'docs/missing-evidence-protocol.md'
NEW_FILES_PREFIXES = ('missing_evidence', 'tests/test_missing_evidence', 'docs/missing-evidence-protocol.md',
                      'reports/missing-evidence/', '.gitignore')
STOPPAGE_CASES = ('dfl-J03WR9', 'dfl-J03WN1', 'dfl-J03WOH', 'dfl-J03WOY', 'wcsf-used-match')
PRIMARY_RESTART = {'dfl': ('dfl-J03WR9', 'dfl-J03WN1'), 'wcsf': ('wcsf-used-match',)}
PROVIDERS = ('skillcorner', 'dfl', 'wcsf')


def provider_of(cid):
    return cid.split('-', 1)[0]


def is_primary(cid):
    return cid not in ('dfl-J03WOH', 'dfl-J03WOY')


def protocol_parameters():
    import player_stillness_features as rf
    import recent_geometry_metrics as m
    import recent_geometry_regimes as rr
    from memory_ablation import MODEL_SHA as RELEASE_MODEL_SHA
    from missing_evidence import FLOOR, LAMBDA
    return dict(experiment=EXPERIMENT, base_commit=BASE_COMMIT, model_sha256=RELEASE_MODEL_SHA,
                window=rf.WINDOW, min_players=rf.MIN_PLAYERS, speed_lag=rf.SPEED_LAG, still_speed=rf.STILL_SPEED,
                control_model_artifact_sha256=MODEL_FILES['control'][1], control_model_sha256=MODEL_SHA['control'],
                still_model_artifact_sha256=MODEL_FILES['candidate'][1], still_model_sha256=MODEL_SHA['candidate'],
                **{'lambda': LAMBDA}, missing_row_rule='(0, 0, lambda * max(0, log max(pD,1e-6) - log max((pH+pA)/2,1e-6)))',
                missing_row_floor=FLOOR, fit='none', mask_rate=.3, mask_seed=1729,
                jitter_prefix=JITTER_PREFIX, jitter_sigma=rr.JITTER_SIGMA, live_window=rr.LIVE_WINDOW,
                live_max_windows=rr.LIVE_MAX_WINDOWS, live_min_visible=rr.LIVE_MIN_VISIBLE, stoppage_tail=rr.STOPPAGE_TAIL,
                gain_threshold=m.GAIN_THRESHOLD, stress_primary_loss=m.STRESS_PRIMARY_LOSS, match_loss=m.MATCH_LOSS,
                dead_loss=m.DEAD_LOSS, false_d_rise=m.FALSE_D_RISE, short_recall_loss=m.SHORT_RECALL_LOSS,
                short_support=m.SHORT_SUPPORT, interior_margin=m.INTERIOR_MARGIN, restart_window=m.RESTART_WINDOW,
                recovery_frames=m.RECOVERY_FRAMES, min_live_windows=m.MIN_LIVE_WINDOWS, min_restart_events=m.MIN_RESTART_EVENTS,
                slack=m.EPS, roundoff=m.ROUNDOFF, switch_cost=32., log_floor=1e-6, kickoff='empty starts for both methods',
                caps={PUBLIC_NAMES[k]: v for k, v in CAPS.items()}, cutoff_local='2026-11-15T23:59', full_cutoff_local='2026-11-16T12:00', primary_cases=len([c for c in NATURAL_CASES if is_primary(c)]),
                secondary_cases=2, regimes=dict(natural=15, noise=15, live_gap=15, stoppage=5))


def source_paths():
    found = {}
    for pattern in ('*.py', 'gap_solver/*.py', 'tests/test_missing_evidence*.py'):
        for path in sorted(ROOT.glob(pattern)):
            found[path.relative_to(ROOT).as_posix()] = path
    for name in (PROTOCOL_DOC, 'requirements-memory-ablation.lock', 'requirements-training.txt'):
        if not (ROOT / name).is_file():
            raise ValueError('Required source missing: ' + name)
        found[name] = ROOT / name
    return found


def git(*args, cwd=None):
    import subprocess
    return subprocess.check_output(('git',) + args, cwd=cwd or ROOT, text=True).strip()


def check_repository(root=None, base=None):
    root, base = root or ROOT, base or BASE_COMMIT
    if git('rev-parse', '--abbrev-ref', 'HEAD', cwd=root) != BRANCH:
        raise ValueError('Wrong branch')
    if subprocess_ok('merge-base', '--is-ancestor', base, 'HEAD', cwd=root) is False:
        raise ValueError('Head does not descend from the base commit')
    changed = [line for line in git('diff', '--name-only', base, cwd=root).splitlines() if line]
    other = [name for name in changed if not name.startswith(NEW_FILES_PREFIXES)]
    if other:
        raise ValueError('Existing files changed: ' + ','.join(other))
    return git('rev-parse', 'HEAD', cwd=root)


def subprocess_ok(*args, cwd=None):
    import subprocess
    return subprocess.run(('git',) + args, cwd=cwd or ROOT, capture_output=True).returncode == 0


def freeze(run_id):
    import memory_ablation_protocol as p
    private, public = run_paths(run_id)
    require_open_study(public)
    parity_path = ROOT / 'reports/recent-geometry/2026-11-12-a/distance-parity.json'
    if not parity_path.is_file() or read_json(parity_path)['status'] != 'exact':
        raise ValueError('Exact distance-recompute parity is required before the freeze')
    head = check_repository()
    env = pinned_environments()
    bindings = verified_bindings()
    private.mkdir(parents=True, exist_ok=True)
    public.mkdir(parents=True, exist_ok=True)
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
    require_open_study(public)
    freeze_value = read_json(public / 'freeze.json')
    for name in (PROTOCOL_DOC, 'reports/missing-evidence/' + run_id + '/freeze.json'):
        import subprocess
        committed = subprocess.check_output(['git','show','HEAD:' + name],cwd=ROOT)
        if committed != (ROOT / name).read_bytes():
            raise ValueError('Protocol and freeze must be committed before preflight')
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
    from player_stillness_training import array_identity as identity
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
    enforce_cutoff('natural')
    import numpy as np
    from gap_solver.tactical import feature_rows
    import player_stillness_features as rf
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
        enforce_cutoff('natural')
        loaded = adapter_load(ledger, cid, bindings, 'preflight')
        frames = loaded['frames']
        reference = np.asarray(loaded['reference']())
        ledger.event('reference_codes_entry', case_id=cid, already_parsed_by_adapter=loaded['reference_loaded_by_adapter'])
        periods = np.asarray([f.period for f in frames], dtype=np.uint8)
        observed = np.asarray([f.ball_observed for f in frames], dtype=bool)
        ledger.claim('feature_pass', f'natural/{cid}/prep')
        midpoint = loader_midpoint(cid, bindings['evaluation'][cid])
        rows = list(rf.stillness_rows(frames))
        ledger.claim('parity', f'prefix/{run_id}/{cid}')
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
        cases[cid] = dict(rows=len(frames), pitch_midpoint=midpoint, still_support_rows=int((matrix[:,19] == 1).sum()), natural_observed_rows=int(observed.sum()), feature_prefix='identical',
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


# ----- models (no fit) ------------------------------------------------------------------------------

def load_models(files=None):
    """E's committed trees, pinned by artifact SHA-256 and semantic model SHA-256.  No fit."""
    from memory_ablation_training import model_digest
    files = files or MODEL_FILES
    models = {}
    for mode in ('control', 'candidate'):
        path, expected = files[mode]
        if file_sha(path) != expected:
            raise ValueError('Model artifact changed: ' + mode)
        models[mode] = read_json(path)['model']
        if model_digest(models[mode]) != MODEL_SHA[mode]:
            raise ValueError('Model semantic identity differs: ' + mode)
    return models


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
    """Implementation verification (ledger category 'parity'); only reconciliation scoring is science budget.

    Per case: release parity (research replica vs restart_release.assemble), F equivalence at lambda = 0
    (assemble_missing vs the replica), and still-tree parity (E-tree supports on the preflight matrix equal
    E's stored natural candidate supports).
    """
    enforce_cutoff('natural')
    import numpy as np
    import recent_geometry_assembly as ra
    from memory_ablation_metrics import score_variant
    from missing_evidence import assemble_missing
    import restart_release
    freeze_value, bindings = frozen(run_id, 'scoring')
    private, public = run_paths(run_id)
    if (public / 'parity.json').exists():
        raise ValueError('Preserve prior parity attempt')
    preflight_value = require(public, 'preflight.json', ok=('ready',))
    models = load_models()
    ledger = open_ledger(run_id)
    historical_dir = ROOT / 'reports/memory-ablation/2026-11-09-v3'
    fields = ('control', 'gapped', 'restarted', 'final', 'stoppage_gaps', 'gap_summary', 'kickoff_changed')
    cases, f1 = {}, {}
    for cid in NATURAL_CASES:
        enforce_cutoff('natural')
        arrays = load_arrays(private / 'cases' / (cid + '.npz'), preflight_value['cases'][cid]['case_arrays_sha256'])
        loaded = adapter_load(ledger, cid, bindings, 'parity')
        frames = loaded['frames']
        ledger.claim('parity', f'release/{run_id}/{cid}')
        real = restart_release.assemble(frames, (), use_restart=True)
        control = supplied_support('control', arrays['matrix'], models['control'])
        replica = ra.assemble_research(frames, control, verify_decoder=True)
        if not all(getattr(real, name) == getattr(replica, name) for name in fields):
            raise ValueError('Release parity failed on ' + cid)
        ledger.claim('parity', f'still-supports/{run_id}/{cid}')
        still = supplied_support('candidate', arrays['matrix'], models['candidate'])
        with np.load(E_PRIVATE / 'predictions' / f'natural--{cid}' / 'candidate.npz', allow_pickle=False) as stored:
            if not np.array_equal(still.supports, stored['supports']):
                raise ValueError('Still-tree supports differ from Experiment E on ' + cid)
        ledger.claim('parity', f'equivalence/{run_id}/{cid}')
        zero = assemble_missing(frames, control, still, lam=0.)
        if zero != ra.assemble_research(frames, control) or zero.decoder_passes != 2:
            raise ValueError('Lambda-zero equivalence failed on ' + cid)
        periods = np.asarray([f.period for f in frames], dtype=np.uint8)
        observed = np.asarray([f.ball_observed for f in frames], dtype=bool)
        ledger.claim('score', f'reconcile/{cid}')
        score = score_variant(arrays['reference'], encode(replica.control), periods, observed)
        historical = read_json(historical_dir / f'{cid}--natural.json')['variants']['control']
        if not reconcile_against_history(score, historical):
            raise ValueError('Historical reconciliation failed on ' + cid)
        f1[cid] = score['metrics']['spell_f1_mean']
        cases[cid] = dict(release_parity=True, equivalence=True, still_supports=True, reconciliation=True,
                          spell_f1_intermediate=f1[cid], historical_spell_f1=historical['metrics']['spell_f1_mean'])
        ledger.event('parity_case', case_id=cid, **cases[cid])
        del loaded, frames, real, replica, zero
    historical_summary = read_json(historical_dir / 'summary.json')['primary']['natural']['control']
    primary, reproduced = primary_natural_check(f1, historical_summary)
    if not reproduced:
        raise ValueError('Primary natural mean not reproduced')
    value = dict(schema_version=1, status='passed', release_parity_cases=15, equivalence_cases=15,
                 still_support_cases=15, reconciliation_cases=15, feature_prefix_cases=15,
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
    enforce_cutoff('natural')
    import recent_geometry_metrics as m
    freeze_value, bindings = frozen(run_id, 'scoring')
    private, public = run_paths(run_id)
    if (public / 'stage1.json').exists() or (private / 'predictions').exists():
        raise ValueError('Preserve prior stage-1 attempt')
    preflight_value = require(public, 'preflight.json', ok=('ready',))
    require(public, 'parity.json', ok=('passed',))
    models = load_models()
    ledger = open_ledger(run_id)
    ledger.event('stage_start', stage='natural')
    (private / 'predictions').mkdir()
    receipts = {}
    for cid in NATURAL_CASES:
        enforce_cutoff('natural')
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
    enforce_cutoff('natural')
    store_exact(public / 'stage1.json', value)
    ledger.event('stage_end', stage='natural', decision=outcome['verdict'])
    return dict(decision=outcome['verdict'], failing=sorted(outcome['failing']))


def stress(run_id):
    """Stage 2, only after a stage-1 pass: noise, pure live gaps, stoppage and reacquisition."""
    enforce_cutoff('stress')
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
    models = load_models()
    ledger = open_ledger(run_id)
    ledger.event('stage_start', stage='stress')
    receipts = {'noise': {}, 'live-gap': {}, 'stoppage': {}}
    for cid in NATURAL_CASES:
        enforce_cutoff('stress')
        info = preflight_value['cases'][cid]
        arrays = load_arrays(private / 'cases' / (cid + '.npz'), info['case_arrays_sha256'])
        sealed = dict(live=arrays['live'])
        if 'stoppage' in arrays:
            sealed['stoppage'] = arrays['stoppage']
        if rr.seal_digest(sealed) != info['mask_seal_sha256']:
            raise ValueError('Sealed masks changed before use')
        loaded = adapter_load(ledger, cid, bindings, 'stress')
        frames = loaded['frames']
        inputs = {'noise': add_visible_ball_noise(frames, cid), 'live-gap': rr.apply_ball_mask(frames, arrays['live'])}
        if 'stoppage' in arrays:
            inputs['stoppage'] = rr.apply_ball_mask(frames, arrays['stoppage'])
        for regime, transformed in inputs.items():
            receipt = run_case_regime(ledger, regime, cid, transformed, arrays['reference'], models,
                                      private / 'predictions' / f'{regime}--{cid}', pitch_midpoint=info['pitch_midpoint'],
                                      hidden_live=arrays['live'] if regime == 'live-gap' else None)
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
    hidden = {}
    for provider in PROVIDERS:
        rows = [r['hidden_live'] for cid,r in receipts['live-gap'].items()
                if provider_of(cid) == provider and is_primary(cid)]
        n = sum(r['rows'] for r in rows)
        hidden[provider] = dict(rows=n, **{method:dict(
            correct=sum(r[method]['correct'] for r in rows),
            strict_team_accuracy=sum(r[method]['correct'] for r in rows) / n if n else None)
            for method in m.METHODS})
    value = dict(schema_version=1, status='complete', gates=gates, created_utc=utc(), hidden_live_by_provider=hidden,
                 primary_spell_f1={regime: dict(
                     control=m.weighted({c: f[c]['control']['spell_f1'] for c in f}, regime)[0],
                     candidate=m.weighted({c: f[c]['candidate']['spell_f1'] for c in f}, regime)[0]) for regime, f in flats.items()},
                 interior_changes={regime: {cid: row['interior_changes'] for cid, row in rows.items()} for regime, rows in receipts.items()})
    enforce_cutoff('stress')
    store_exact(public / 'stage2.json', value)
    ledger.event('stage_end', stage='stress')
    return dict(status='complete')


def summarise(run_id):
    """Aggregate verdict.  A pass authorises nothing beyond a separate release decision."""
    import recent_geometry_metrics as m
    private, public = run_paths(run_id)
    verdict_cutoff(public)
    parts = {}
    for name in ('freeze', 'preflight', 'parity', 'stage1', 'stage2', 'stop'):
        if (public / (name + '.json')).is_file():
            parts[name] = read_json(public / (name + '.json'))
    gates = {}
    if 'stage1' in parts:
        gates.update(parts['stage1']['gates'])
    if 'stage2' in parts:
        gates.update(parts['stage2']['gates'])
    stopped = next((f"{n}:{parts[n]['status']}" for n in ('preflight', 'parity') if n in parts and parts[n]['status'] not in ('ready', 'complete', 'passed')), '')
    if 'stop' in parts:
        outcome = dict(verdict='FAIL',failing={'operational_stop':parts['stop']['command']},assessed=0)
    elif stopped:
        outcome = dict(verdict='FAIL', failing={stopped: 'stopped'}, assessed=0)
    elif 'stage1' in parts and not parts['stage1']['advance_to_stage2']:
        outcome = public_verdict(gates)
    elif 'stage2' in parts:
        outcome = public_verdict(gates)
    else:
        outcome = dict(verdict='INCOMPLETE', failing={}, assessed=len(gates))
    names = PUBLIC_NAMES
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


COMMANDS = ('freeze', 'preflight', 'parity', 'natural', 'stress', 'summarise')


def main(argv=None):
    import argparse
    import sys
    import traceback
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=COMMANDS)
    parser.add_argument('--run-id', required=True)
    args = parser.parse_args(argv)
    try:
        result = globals()[args.command](args.run_id)
        print(json.dumps(result, sort_keys=True, default=str))
        return 0 if result.get('status') not in ('NOT_EXACT_STOP',) else 2
    except Exception as error:
        private, public = run_paths(args.run_id)
        if private.is_dir():
            try:
                with (private / ('execution-error-' + args.command + '.log')).open('x', encoding='utf-8') as handle:
                    handle.write(traceback.format_exc())
            except OSError:
                pass
        if public.is_dir() and not (public/'stop.json').exists():
            store_exact(public/'stop.json',dict(schema_version=1,status='stopped',command=args.command,
                        error_type=type(error).__name__,created_utc=utc()))
        sys.stderr.write('Stopped; preserve this generation and inspect the private execution log.\n')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
