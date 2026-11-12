"""Experiment C orchestration: freeze / preflight / parity / natural / stress / summarise, with a budget ledger.

Column-specific pieces are copied from ``recent_geometry_run`` (Experiment A, commit 01aea05) and adapted here; the
regimes, assembly and metrics modules of Experiment A are imported unchanged.  There are no fits.  Private arrays live
outside Git under PRIVATE_ROOT; only aggregates are written to reports/team-symmetry.
"""
import hashlib
import json
from datetime import datetime, timezone
from math import isfinite
from pathlib import Path
import random
import re

import numpy as np

import recent_geometry_assembly as ra
import recent_geometry_metrics as metrics
import recent_geometry_regimes as rr
import team_symmetry as ts

EXPERIMENT = 'team-symmetry-2026-11-12'
ROOT = Path(__file__).resolve().parent
PRIVATE_ROOT = Path.home() / "Documents/ChatGPT/MESSI's FOOT/team-symmetry-reference"
BASE_COMMIT = '01aea05f545cc366d5112f153f678399a5268dac'
BRANCH = 'experiment/team-symmetry'
MODEL_SHA = '363c45c70838b398cd87aee7474d7e281fd392f059a31b85712e312058aaab4d'
A_DIR = ROOT / 'reports/recent-geometry/2026-11-12-a'
A_FREEZE, A_PREFLIGHT, A_DISTANCE = A_DIR / 'freeze.json', A_DIR / 'preflight.json', A_DIR / 'distance-parity.json'
HISTORY = ROOT / 'reports/memory-ablation/2026-11-09-v3'
JITTER_PREFIX = 'team-symmetry-jitter-v1:1729:'
JITTER_SIGMA = rr.JITTER_SIGMA
SYMMETRY_TOLERANCE = 1e-12

# Science budget.  Claimed on entry, cumulative across run ids, never refunded.  There are no fits.
CAPS = dict(fit=0, prediction=100, score=115, feature_pass=200, decoder_pass=300)
PUBLIC_NAMES = dict(fit='fits', prediction='case_runs', score='score_bundles', feature_pass='feature_tree_passes',
                    decoder_pass='decoder_passes', parity='parity_checks')

SKILLCORNER = ('1874553', '1886347', '2007448', '2007721', '2010085', '2011166', '2013725', '2015213', '2016236', '2017461')
NATURAL_CASES = tuple('skillcorner-' + m for m in SKILLCORNER) + (
    'dfl-J03WR9', 'dfl-J03WN1', 'wcsf-used-match', 'dfl-J03WOH', 'dfl-J03WOY')
STOPPAGE_CASES = ('dfl-J03WR9', 'dfl-J03WN1', 'dfl-J03WOH', 'dfl-J03WOY', 'wcsf-used-match')
PRIMARY_RESTART = {'dfl': ('dfl-J03WR9', 'dfl-J03WN1'), 'wcsf': ('wcsf-used-match',)}
PROVIDERS = ('skillcorner', 'dfl', 'wcsf')
_SAFE = re.compile(r'[A-Za-z0-9_.:/-]{1,200}')
_PARITY = re.compile(r'(swap|symmetry|release)/(' + '|'.join(map(re.escape, NATURAL_CASES)) + r')(/retry[12])?')


class BudgetError(ValueError):
    pass


def utc():
    return datetime.now(timezone.utc).isoformat()


class Ledger:
    """Claim-on-entry ledger.  ``parity`` is a separate implementation-verification category: bounded, unique
    identities (a retry suffix is allowed only after a documented code defect), never counted against the science caps,
    and it produces no scores."""

    def __init__(self, claims, access):
        self.claims = Path(claims)
        self.access = Path(access)
        self.claims.mkdir(parents=True, exist_ok=True)
        self.access.parent.mkdir(parents=True, exist_ok=True)

    def count(self, kind):
        return len(list(self.claims.glob(kind + '--*.json')))

    def claim(self, kind, identity):
        if kind not in CAPS and kind != 'parity':
            raise BudgetError('Unknown claim kind')
        if not isinstance(identity, str) or not _SAFE.fullmatch(identity) or '__' in identity or '..' in identity:
            raise BudgetError('Unsafe claim identity')
        if kind == 'parity' and not _PARITY.fullmatch(identity):
            raise BudgetError('Unknown parity identity')
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
    public = ROOT / 'reports/team-symmetry' / run_id
    for path in (PRIVATE_ROOT, private, public):
        reject_linked_ancestors(path)
    return private, public


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
    with path.open('xb') as handle:
        handle.write(canonical(value))
    if path.read_bytes() != canonical(value):
        raise ValueError('Persisted canonical bytes differ')


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def encode(labels):
    return np.asarray(['HADX'.index(s) for s in labels], dtype=np.uint8)


def provider_of(cid):
    return cid.split('-', 1)[0]


def is_primary(cid):
    return cid not in ('dfl-J03WOH', 'dfl-J03WOY')


def load_model():
    """The frozen release tree, re-hashed against the frozen identity (here and in the release runtime)."""
    from gap_solver.tactical_model import FROZEN_MODEL
    import release_runtime
    model = FROZEN_MODEL['model']
    digest = hashlib.sha256(release_runtime._json_bytes(model)).hexdigest()
    if digest != MODEL_SHA or digest != release_runtime.MODEL_SHA256:
        raise ValueError('Frozen tactical model identity differs')
    ts.check_schema(model['feature_names'])
    ts.check_leaf_22(model)
    return model


def verified_bindings():
    """Evaluation input identities re-hashed against the historical bindings (training files are not used)."""
    import memory_ablation_protocol as p
    bindings = p.input_bindings(ROOT)
    for binding in bindings['evaluation'].values():
        if not binding['files'] or p.hashes(binding['files']) != binding['expected']:
            raise ValueError('Frozen input identity differs')
    return bindings


def adapter_load(ledger, cid, bindings, purpose):
    from memory_ablation_run import load_evaluation
    ledger.event('evaluation_adapter_entry', case_id=cid, purpose=purpose,
                 reference_container_may_be_parsed=not cid.startswith('wcsf'))
    return load_evaluation(cid, bindings['evaluation'][cid])


def array_identity(arrays):
    from memory_ablation_protocol import array_identity as identity
    return identity(arrays)


def save_arrays(path, arrays):
    path = Path(path)
    if path.exists():
        raise FileExistsError(str(path))
    with path.open('xb') as handle:
        np.savez_compressed(handle, **arrays)


def load_arrays(path, expected_identity=None):
    with np.load(path, allow_pickle=False) as data:
        arrays = {key: data[key] for key in data.files}
    if expected_identity is not None and array_identity(arrays) != expected_identity:
        raise ValueError('Private case arrays changed')
    return arrays


def require(public, name, status_key='status', ok=('ready', 'complete', 'passed')):
    path = public / name
    if not path.is_file():
        raise ValueError('Missing prerequisite ' + name)
    value = read_json(path)
    if value.get(status_key) not in ok:
        raise ValueError(f'Prerequisite {name} did not pass: {value.get(status_key)}')
    return value


# ----- visible-ball noise (Experiment A's rule with this experiment's prefix) -----------------------

def noise_seed(case_id, prefix=JITTER_PREFIX):
    return int(hashlib.sha256((prefix + case_id).encode('utf-8')).hexdigest()[:8], 16)


def add_visible_ball_noise(frames, case_id, prefix=JITTER_PREFIX):
    """Zero-mean Gaussian (sigma 0.25 m) on each naturally visible ball coordinate; distances recomputed.

    Identical in every respect to ``recent_geometry_regimes.add_visible_ball_noise`` except the seed prefix.
    """
    from dataclasses import replace
    rng = random.Random(noise_seed(case_id, prefix))
    out = []
    for frame in frames:
        if not frame.ball_observed:
            out.append(frame)
            continue
        if not hasattr(frame, 'home_xy') or not hasattr(frame, 'away_xy'):
            raise ValueError('visible-ball noise needs player positions to recompute distances')
        x = frame.ball_x + rng.gauss(0, JITTER_SIGMA)
        y = frame.ball_y + rng.gauss(0, JITTER_SIGMA)
        distances = [rr._nearest(frame.home_xy, x, y), rr._nearest(frame.away_xy, x, y)]
        if not (isfinite(x) and isfinite(y)) or any(d is not None and not isfinite(d) for d in distances):
            raise ValueError('non-finite transformed record')
        out.append(replace(frame, ball_x=x, ball_y=y, home_distance=distances[0], away_distance=distances[1]))
    return out


# ----- one case, one regime, both methods --------------------------------------------------------

def require_method(support_set, method):
    """Candidate and frozen supports cannot mix."""
    if not isinstance(support_set, ra.SupportSet) or support_set.method != method:
        raise ValueError('Support set belongs to a different method')
    return support_set


def run_case_regime(ledger, regime, cid, frames, reference, model, directory, *, matrix=None, prep_claimed=False):
    """Predict with both methods on identical transformed inputs and score the final labels.

    ``frames`` are the transformed inference inputs; ``reference`` is evaluation machinery used only to score.
    Every unit of science budget is claimed before it is spent: the control uses one tree pass, the candidate two.
    """
    from gap_solver.tactical import feature_rows
    frames = list(frames)
    periods = np.asarray([f.period for f in frames], dtype=np.uint8)
    observed = np.asarray([f.ball_observed for f in frames], dtype=bool)
    reference = np.asarray(reference)
    if reference.shape != periods.shape:
        raise ValueError('Reference/frame dimensions differ')
    if matrix is None:
        if not prep_claimed:
            ledger.claim('feature_pass', f'{regime}/{cid}/prep')
        matrix = np.asarray(list(feature_rows(frames)), dtype=np.float32)
        if not np.isfinite(matrix).all():
            raise ValueError('Non-finite features')
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    bundles, finals, latents = {}, {}, {}
    for method in metrics.METHODS:
        identity = f'{regime}/{cid}/{method}'
        ledger.claim('prediction', identity)
        if method == 'control':
            ledger.claim('feature_pass', identity + '/tree')
            support = ra.SupportSet('control', ts.control_supports(matrix, model))
        else:
            ledger.claim('feature_pass', identity + '/tree/0')
            ledger.claim('feature_pass', identity + '/tree/1')
            support = ra.SupportSet('candidate', ts.candidate_supports(matrix, model))
        require_method(support, method)
        for k in range(2):
            ledger.claim('decoder_pass', f'{identity}/{k}')
        assembly = ra.assemble_research(frames, support)
        if assembly.decoder_passes != 2:
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

PROTOCOL_DOC = 'docs/team-symmetry-protocol.md'
NEW_FILES_PREFIXES = ('team_symmetry', 'tests/test_team_symmetry', 'docs/team-symmetry-protocol.md',
                      'reports/team-symmetry/', '.gitignore')


def protocol_parameters():
    return dict(experiment=EXPERIMENT, base_commit=BASE_COMMIT, branch=BRANCH, model_sha256=MODEL_SHA,
                swap_permutation=','.join(map(str, ts.PERMUTATION)), swap_negated=','.join(map(str, ts.NEGATED)),
                support_rule='sH=(pH+qA)/2; sA=(pA+qH)/2; sD=(pD+qD)/2; q=tree(swap(x))', fits=0, mask_rate=.3, mask_seed=1729,
                jitter_prefix=JITTER_PREFIX, jitter_sigma=JITTER_SIGMA, live_window=rr.LIVE_WINDOW,
                live_max_windows=rr.LIVE_MAX_WINDOWS, live_min_visible=rr.LIVE_MIN_VISIBLE, stoppage_tail=rr.STOPPAGE_TAIL,
                gain_threshold=metrics.GAIN_THRESHOLD, stress_primary_loss=metrics.STRESS_PRIMARY_LOSS,
                match_loss=metrics.MATCH_LOSS, dead_loss=metrics.DEAD_LOSS, false_d_rise=metrics.FALSE_D_RISE,
                short_recall_loss=metrics.SHORT_RECALL_LOSS, short_support=metrics.SHORT_SUPPORT,
                interior_margin=metrics.INTERIOR_MARGIN, restart_window=metrics.RESTART_WINDOW,
                recovery_frames=metrics.RECOVERY_FRAMES, min_live_windows=metrics.MIN_LIVE_WINDOWS,
                min_restart_events=metrics.MIN_RESTART_EVENTS, slack=metrics.EPS, roundoff=metrics.ROUNDOFF,
                symmetry_tolerance=SYMMETRY_TOLERANCE, switch_cost=32., log_floor=1e-6,
                kickoff='empty starts for both methods', caps={PUBLIC_NAMES[k]: v for k, v in CAPS.items()},
                stage1_cutoff_local='2026-11-14T23:59', full_cutoff_local='2026-11-15T12:00',
                primary_cases=len([c for c in NATURAL_CASES if is_primary(c)]), secondary_cases=2,
                regimes=dict(natural=15, noise=15, live_gap=15, stoppage=5))


def source_paths():
    found = {}
    for pattern in ('*.py', 'gap_solver/*.py', 'tests/test_team_symmetry*.py'):
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


def subprocess_ok(*args):
    import subprocess
    return subprocess.run(('git',) + args, cwd=ROOT, capture_output=True).returncode == 0


def check_repository():
    if git('rev-parse', '--abbrev-ref', 'HEAD') != BRANCH:
        raise ValueError('Wrong branch')
    if not subprocess_ok('merge-base', '--is-ancestor', BASE_COMMIT, 'HEAD'):
        raise ValueError('Head does not descend from the base commit')
    changed = [line for line in git('diff', '--name-only', BASE_COMMIT).splitlines() if line]
    other = [name for name in changed if not name.startswith(NEW_FILES_PREFIXES)]
    if other:
        raise ValueError('Existing files changed: ' + ','.join(other))
    return git('rev-parse', 'HEAD')


def freeze(run_id):
    import memory_ablation_protocol as p
    private, public = run_paths(run_id)
    a_freeze = read_json(A_FREEZE)
    if read_json(A_DISTANCE)['status'] != 'exact':
        raise ValueError('Experiment A distance-recompute parity is not exact')
    head = check_repository()
    runtime = p.runtime_info()
    if runtime != a_freeze['environment']['scoring']:
        raise ValueError('Scoring environment differs from the Experiment A freeze')
    load_model()
    bindings = verified_bindings()
    evaluation = {cid: b['expected'] for cid, b in bindings['evaluation'].items()}
    if evaluation != a_freeze['input_sha256']['evaluation']:
        raise ValueError('Evaluation inputs differ from the Experiment A freeze')
    private.mkdir(parents=True, exist_ok=True)
    sources = {name: file_sha(path) for name, path in source_paths().items()}
    value = dict(schema_version=1, run_id=run_id, created_utc=utc(), head_commit=head, protocol=protocol_parameters(),
                 protocol_doc_sha256=sources[PROTOCOL_DOC], source_sha256=sources, input_sha256=dict(evaluation=evaluation),
                 environment=dict(scoring=runtime), distance_parity_sha256=file_sha(A_DISTANCE),
                 experiment_a_freeze_sha256=file_sha(A_FREEZE), experiment_a_preflight_sha256=file_sha(A_PREFLIGHT))
    store_exact(public / 'freeze.json', value)
    store_exact(private / 'input-map.json', {cid: {k: str(Path(v).resolve()) for k, v in b['files'].items()}
                                             for cid, b in bindings['evaluation'].items()}, public=False)
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
    if {cid: b['expected'] for cid, b in bindings['evaluation'].items()} != freeze_value['input_sha256']['evaluation']:
        raise ValueError('Input identities changed since the freeze')
    if role == 'scoring' and p.runtime_info() != freeze_value['environment']['scoring']:
        raise ValueError('Executing runtime differs from the freeze')
    return freeze_value, bindings


# ----- preflight: masks, sealing, support qualification ---------------------------------------------

def check_mask_seals(seals):
    """Per case: does the mask seal equal Experiment A's (the brief requires the same masks)?"""
    if not A_PREFLIGHT.is_file():
        raise ValueError('Experiment A preflight receipt is missing')
    theirs = read_json(A_PREFLIGHT)['cases']
    return {cid: cid in theirs and theirs[cid]['mask_seal_sha256'] == seal for cid, seal in seals.items()}


def preflight(run_id):
    from gap_solver.tactical import feature_rows
    freeze_value, bindings = frozen(run_id, 'scoring')
    private, public = run_paths(run_id)
    if (public / 'preflight.json').exists() or (private / 'cases').exists():
        raise ValueError('Preserve prior preflight attempts')
    load_model()
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
        matrix = np.asarray(list(feature_rows(frames)), dtype=np.float32)
        if not np.isfinite(matrix).all():
            raise ValueError('Non-finite features on ' + cid)
        gt = np.where(periods > 0, reference, 3).astype(np.uint8)
        live = rr.live_gap_windows(cid, periods, reference, observed)
        arrays = dict(reference=reference.astype(np.uint8), matrix=matrix, live=live['mask'])
        sealed = dict(live=live['mask'])
        stoppage = None
        if cid in STOPPAGE_CASES:
            stoppage = rr.stoppage_mask(periods, reference)
            arrays['stoppage'] = stoppage
            sealed['stoppage'] = stoppage
        events, ungroupable = metrics.restart_events(gt, periods)
        save_arrays(private / 'cases' / (cid + '.npz'), arrays)
        cases[cid] = dict(rows=len(frames), natural_observed_rows=int(observed.sum()),
                          live_windows_eligible=len(live['eligible']), live_windows_selected=len(live['selected']),
                          live_masked_rows=int(live['mask'].sum()),
                          stoppage_masked_rows=None if stoppage is None else int(stoppage.sum()),
                          restart_events_eligible=len(events), restart_events_ungroupable=ungroupable,
                          mask_seal_sha256=rr.seal_digest(sealed), case_arrays_sha256=array_identity(arrays))
        ledger.event('preflight_case', case_id=cid, **{k: v for k, v in cases[cid].items() if k != 'rows'})
        del loaded, frames, matrix
    match = check_mask_seals({cid: row['mask_seal_sha256'] for cid, row in cases.items()})
    for cid, row in cases.items():
        row['mask_seal_matches_experiment_a'] = bool(match[cid])
    windows = {p: sum(c['live_windows_selected'] for cid, c in cases.items() if provider_of(cid) == p and is_primary(cid)) for p in PROVIDERS}
    events = {p: sum(cases[cid]['restart_events_eligible'] for cid in ids) for p, ids in PRIMARY_RESTART.items()}
    problems = [f'live-gap windows {p}={n}' for p, n in windows.items() if n < metrics.MIN_LIVE_WINDOWS]
    problems += [f'restart events {p}={n}' for p, n in events.items() if n < metrics.MIN_RESTART_EVENTS]
    if not all(match.values()):
        status, problems = 'stopped_mask_mismatch', ['mask seals differ from Experiment A: ' + ','.join(c for c, ok in match.items() if not ok)]
    else:
        status = 'blocked_insufficient_support' if problems else 'ready'
    value = dict(schema_version=1, status=status, problems='; '.join(problems), model_sha256=MODEL_SHA,
                 live_windows_selected_by_provider=windows, restart_events_eligible_by_provider=events, cases=cases,
                 freeze_sha256=file_sha(public / 'freeze.json'), created_utc=utc())
    store_exact(public / 'preflight.json', value)
    return dict(status=status, problems=value['problems'], windows=windows, events=events)


# ----- parity gates ----------------------------------------------------------------------------------

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
    primary, _ = metrics.weighted(f1_by_case, 'natural')
    ok = primary is not None and abs(primary - 0.551816) <= 1e-6 and abs(primary - historical_summary) <= 1e-9
    return primary, bool(ok)


def swap_validity(frames):
    """feature_rows(team-swapped frames) must equal swap(feature_rows(frames)) bit for bit."""
    from gap_solver.tactical import feature_rows
    frames = list(frames)
    direct = np.asarray(list(feature_rows(frames)), dtype=np.float64)
    swapped = np.asarray(list(feature_rows(ts.swap_frames(frames))), dtype=np.float64)
    identical = direct.shape == swapped.shape and ts.swap_matrix(direct).tobytes() == swapped.tobytes()
    return dict(identical=bool(identical), rows=len(direct), matrix=direct)


def release_parity(frames, model, matrix=None):
    """Research assembly with the control supports against the real, unmodified ``restart_release.assemble``."""
    import restart_release
    from gap_solver.tactical import feature_rows
    frames = list(frames)
    if matrix is None:
        matrix = np.asarray(list(feature_rows(frames)), dtype=np.float32)
    real = restart_release.assemble(frames, (), use_restart=True)
    replica = ra.assemble_research(frames, ra.SupportSet('control', ts.control_supports(matrix, model)), verify_decoder=True)
    fields = {name: getattr(real, name) == getattr(replica, name)
              for name in ('control', 'gapped', 'restarted', 'final', 'stoppage_gaps', 'gap_summary', 'kickoff_changed')}
    return dict(fields=fields, replica=replica)


def parity(run_id):
    """Gates 1-4 (ledger category 'parity'; no scores), the descriptive bias report, then historical reconciliation.

    Reconciliation scoring spends science budget, so it runs only after every parity gate has passed on all 15 cases.
    """
    from memory_ablation_metrics import score_variant
    from gap_solver.soft_sequence import sequence_usable
    freeze_value, bindings = frozen(run_id, 'scoring')
    private, public = run_paths(run_id)
    if (public / 'parity.json').exists() or (public / 'bias.json').exists():
        raise ValueError('Preserve prior parity attempt')
    preflight_value = require(public, 'preflight.json', ok=('ready',))
    model = load_model()
    ledger = open_ledger(run_id)
    held, biases, worst = {}, {}, 0.
    for cid in NATURAL_CASES:
        arrays = load_arrays(private / 'cases' / (cid + '.npz'), preflight_value['cases'][cid]['case_arrays_sha256'])
        loaded = adapter_load(ledger, cid, bindings, 'parity')
        frames = loaded['frames']
        matrix = arrays['matrix']
        ledger.claim('parity', f'swap/{cid}')
        validity = swap_validity(frames)
        if not validity['identical']:
            raise ValueError('Swap-map validity failed on ' + cid)
        if validity['matrix'].astype(np.float32).tobytes() != matrix.tobytes():
            raise ValueError('Stored feature matrix differs from the feature generator on ' + cid)
        ledger.claim('parity', f'symmetry/{cid}')
        error = ts.symmetry_error(matrix, model)
        if not error <= SYMMETRY_TOLERANCE:
            raise ValueError('Candidate symmetry check failed on ' + cid)
        worst = max(worst, error)
        p, s = ts.control_supports(matrix, model), ts.candidate_supports(matrix, model)
        usable = np.asarray([bool(sequence_usable(f)) for f in frames], dtype=bool)
        observed = np.asarray([f.ball_observed for f in frames], dtype=bool)
        biases[cid] = ts.bias_summary(p, s, usable, observed, ts.leaf_index(matrix, model))
        ledger.claim('parity', f'release/{cid}')
        result = release_parity(frames, model, matrix)
        if not all(result['fields'].values()):
            raise ValueError('Release parity failed on ' + cid)
        held[cid] = dict(control=encode(result['replica'].control), periods=np.asarray([f.period for f in frames], dtype=np.uint8),
                         observed=observed, reference=arrays['reference'])
        ledger.event('parity_case', case_id=cid, swap_validity=True, release_parity=True, symmetry_max_abs_diff=error)
        del loaded, frames, validity, result
    historical_dir = HISTORY
    cases, f1 = {}, {}
    for cid in NATURAL_CASES:                                    # science budget: 15 reconciliation bundles
        ledger.claim('score', f'reconcile/{cid}')
        row = held[cid]
        score = score_variant(row['reference'], row['control'], row['periods'], row['observed'])
        historical = read_json(historical_dir / f'{cid}--natural.json')['variants']['control']
        if not reconcile_against_history(score, historical):
            raise ValueError('Historical reconciliation failed on ' + cid)
        f1[cid] = score['metrics']['spell_f1_mean']
        cases[cid] = dict(swap_validity=True, release_parity=True, reconciliation=True, spell_f1_intermediate=f1[cid],
                          historical_spell_f1=historical['metrics']['spell_f1_mean'])
    historical_summary = read_json(historical_dir / 'summary.json')['primary']['natural']['control']
    primary, reproduced = primary_natural_check(f1, historical_summary)
    if not reproduced:
        raise ValueError('Primary natural mean not reproduced')
    providers = {prov: ts.merge_bias(biases[cid] for cid in NATURAL_CASES if provider_of(cid) == prov) for prov in PROVIDERS}
    store_exact(public / 'bias.json', dict(
        schema_version=1, definition='usable rows only; h_minus_a is pH-pA (control) or sH-sA (candidate); argmax over H,A,D; '
        'pooled by adding counts and sums over every case of the provider', providers=providers, cases=biases,
        freeze_sha256=file_sha(public / 'freeze.json'), created_utc=utc()))
    value = dict(schema_version=1, status='passed', swap_validity_cases=15, symmetry_cases=15, release_parity_cases=15,
                 reconciliation_cases=15, candidate_symmetry_max_abs_diff=worst, primary_natural_mean=primary,
                 historical_primary_natural_mean=historical_summary, primary_reproduced_to_1e6=True, cases=cases,
                 freeze_sha256=file_sha(public / 'freeze.json'), created_utc=utc())
    store_exact(public / 'parity.json', value)
    return dict(status='passed', primary_natural_mean=primary, candidate_symmetry_max_abs_diff=worst)


# ----- stages ---------------------------------------------------------------------------------------

def public_verdict(named_gates):
    result = metrics.verdict(named_gates)
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
    freeze_value, bindings = frozen(run_id, 'scoring')
    private, public = run_paths(run_id)
    if (public / 'stage1.json').exists() or (private / 'predictions').exists():
        raise ValueError('Preserve prior stage-1 attempt')
    preflight_value = require(public, 'preflight.json', ok=('ready',))
    require(public, 'parity.json', ok=('passed',))
    model = load_model()
    ledger = open_ledger(run_id)
    ledger.event('stage_start', stage='natural')
    (private / 'predictions').mkdir()
    receipts = {}
    for cid in NATURAL_CASES:
        arrays = load_arrays(private / 'cases' / (cid + '.npz'), preflight_value['cases'][cid]['case_arrays_sha256'])
        loaded = adapter_load(ledger, cid, bindings, 'natural')
        receipt = run_case_regime(ledger, 'natural', cid, loaded['frames'], arrays['reference'], model,
                                  private / 'predictions' / f'natural--{cid}', matrix=arrays['matrix'])
        receipts[cid] = _store_case(public, 'natural', receipt, cid, preflight_value['cases'][cid])
        ledger.event('case_complete', case_id=cid, regime='natural')
        del loaded, arrays
    flats = _flats(receipts)
    m = metrics
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
    freeze_value, bindings = frozen(run_id, 'scoring')
    private, public = run_paths(run_id)
    stage1 = require(public, 'stage1.json', ok=('complete',))
    if not stage1['advance_to_stage2']:
        raise ValueError('Stage 1 did not pass; stress is not run')
    if (public / 'stage2.json').exists():
        raise ValueError('Preserve prior stage-2 attempt')
    preflight_value = require(public, 'preflight.json', ok=('ready',))
    model = load_model()
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
        inputs = {'noise': add_visible_ball_noise(frames, cid), 'live-gap': rr.apply_ball_mask(frames, arrays['live'])}
        if 'stoppage' in arrays:
            inputs['stoppage'] = rr.apply_ball_mask(frames, arrays['stoppage'])
        for regime, transformed in inputs.items():
            receipt = run_case_regime(ledger, regime, cid, transformed, arrays['reference'], model,
                                      private / 'predictions' / f'{regime}--{cid}')
            receipts[regime][cid] = _store_case(public, regime, receipt, cid, info)
            ledger.event('case_complete', case_id=cid, regime=regime)
        del loaded, frames, inputs, arrays
    m = metrics
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
    private, public = run_paths(run_id)
    parts = {}
    for name in ('freeze', 'preflight', 'parity', 'stage1', 'stage2'):
        if (public / (name + '.json')).is_file():
            parts[name] = read_json(public / (name + '.json'))
    gates = {}
    if 'stage1' in parts:
        gates.update(parts['stage1']['gates'])
    if 'stage2' in parts:
        gates.update(parts['stage2']['gates'])
    stopped = next((f"{n}:{parts[n]['status']}" for n in ('preflight', 'parity') if n in parts
                    and parts[n]['status'] not in ('ready', 'complete', 'passed')), '')
    if stopped:
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
    for regime in metrics.REGIMES:
        rows = {}
        for cid in NATURAL_CASES:
            path = public / f'{cid}--{regime}.json'
            if path.is_file():
                rows[cid] = read_json(path)['flats']
        if rows:
            tables[regime] = rows
    text = {'PASS': 'PASS - qualifies for a separate release decision', 'FAIL': 'FAIL', 'INCOMPLETE': 'INCOMPLETE'}[outcome['verdict']]
    value = dict(schema_version=1, verdict=text, failing_checks=outcome['failing'], checks_assessed=outcome['assessed'],
                 stage2_run='stage2' in parts, budget_used=ledger_counts, budget_caps={names[k]: v for k, v in CAPS.items()},
                 stage_timestamps=stages, tables=tables, authorises='nothing beyond a separate release decision', created_utc=utc())
    store_exact(public / 'summary.json', value)
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
        return 0
    except Exception:
        private, _ = run_paths(args.run_id)
        if private.is_dir():
            try:
                with (private / ('execution-error-' + args.command + '.log')).open('x', encoding='utf-8') as handle:
                    handle.write(traceback.format_exc())
            except OSError:
                pass
        sys.stderr.write('Stopped; preserve this generation and inspect the private execution log.\n')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
