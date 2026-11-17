"""Acquire and prepare ten pinned SkillCorner matches. No models are imported or run.

Uses the existing motion adapter and all feature blocks from se_extract/se_append.
Case files intentionally omit release_sup (frozen-model predictions, not training inputs).
Existing differing assets/caches are preserved and rejected rather than overwritten.
"""
import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform

import numpy as np

from gap_solver.acquisition import acquire_asset, asset_digest
from gap_solver.skillcorner import load_skillcorner, save_motion_cache, load_motion_cache
from gap_solver.tactical import feature_rows
import se_features
import se_load
from se_data_catalog import ADDITIONAL_SKILLCORNER, ADDITIONAL_CASES

CODE = Path(__file__).resolve().parent
SUFFIXES = ('.features.npz', '.reference.npz', '.metadata.json')
FEATURE_SOURCES = ('se_features.py', 'gap_solver/tactical.py', 'gap_solver/core.py',
                   'gap_solver/motion.py', 'gap_solver/skillcorner.py')
CASE_FIELDS = {'X', 'names', 'ref', 'period', 'observed'}


def sha256(p):
    return asset_digest(p, Path(p).stat().st_size, 'sha256')


def write_json(p, value):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    temp = p.with_name(p.name + '.new')
    temp.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
    temp.replace(p)


def assets(protocol, root):
    """Only the ten requested matches and attribution files; never competition inputs."""
    pointers = {v['path']: v for v in protocol['tracking_lfs_objects']}
    wanted = set(ADDITIONAL_SKILLCORNER)
    entries = [x for x in protocol['files'] if x['path'].split('/')[2] in wanted]
    if len(entries) != 40 or len({x['path'] for x in entries}) != 40:
        raise ValueError('Expected exactly four unique assets per additional match')
    for item in entries + protocol['root_files']:
        name = item['path']
        pointer = pointers.get(name)
        size = pointer['object_bytes'] if pointer else item['repository_bytes']
        expected = pointer['object_sha256'] if pointer else item['git_blob_sha']
        algorithm = 'sha256' if pointer else 'git_blob_sha1'
        base = 'https://media.githubusercontent.com/media/' if pointer else 'https://raw.githubusercontent.com/'
        url = base + 'SkillCorner/opendata/' + protocol['revision'] + '/' + name
        dest = root / 'raw' / Path(name).relative_to('data/matches') if name.startswith('data/matches/') else root / 'source' / name
        result = acquire_asset(url, dest, size, expected, algorithm)
        yield dict(source_path=name, relative_path=dest.relative_to(root).as_posix(),
                   bytes=size, sha256=sha256(dest), pinned_digest=expected, algorithm=algorithm,
                   url=url, verified=True)


def inspect_raw(folder, match):
    meta = json.loads((folder / (match + '_match.json')).read_text(encoding='utf-8-sig'))
    if str(meta['id']) != match or meta['home_team']['id'] == meta['away_team']['id']:
        raise ValueError('Match/team identity mismatch')
    counts, periods = Counter(), Counter()
    previous = -1
    with (folder / (match + '_tracking_extrapolated.jsonl')).open(encoding='utf-8-sig') as handle:
        for line in handle:
            row = json.loads(line)
            number = row['frame']
            if type(number) is not int or number != previous + 1:
                raise ValueError('Tracking must be complete, contiguous and duplicate-free from frame zero')
            previous = number
            counts['tracking_rows'] += 1
            periods[str(row.get('period'))] += 1
            if row.get('period') in (1, 2):
                counts['active_native_frames'] += 1
                ball = row.get('ball_data') or {}
                if ball.get('is_detected') is True and ball.get('x') is not None and ball.get('y') is not None:
                    counts['detected_ball_active_native_frames'] += 1
    if not periods['1'] or not periods['2']:
        raise ValueError('Both match periods are required')
    for suffix, required in (
        ('phases_of_play.csv', {'match_id', 'period', 'frame_start', 'frame_end', 'team_in_possession_id'}),
        ('dynamic_events.csv', {'match_id', 'event_id', 'period', 'frame_start', 'frame_end'}),
    ):
        with (folder / (match + '_' + suffix)).open(newline='', encoding='utf-8-sig') as handle:
            reader = csv.DictReader(handle)
            if not required <= set(reader.fieldnames or ()):
                raise ValueError('Missing annotation columns: ' + suffix)
            n = 0
            for row in reader:
                if str(row['match_id']) != match or None in row:
                    raise ValueError('Annotation identity or CSV width mismatch')
                n += 1
            if not n:
                raise ValueError('Empty annotation file')
            counts[suffix.replace('.csv', '') + '_rows'] = n
    return dict(counts), dict(periods), meta


def build_case(frames, reference):
    f18 = np.asarray(list(feature_rows(frames)), dtype=np.float64)
    X, names, info = se_features.build(frames, f18)
    names = list(names)
    for fn in (se_features.impulse_features, se_features.impulse_rel_features,
               se_features.team_shape_features, se_features.team_shape_ext_features,
               se_features.restart_features):
        extra, extra_names = fn(frames)
        X = np.concatenate((X, extra), axis=1)
        names.extend(extra_names)
    return dict(X=X, names=np.asarray(names), ref=np.asarray(reference, dtype=np.uint8),
                period=info['period'], observed=info['observed'])


def validate_case(z, reference, periods, expected_names):
    n = len(reference)
    if set(z) != CASE_FIELDS or z['X'].shape != (n, len(expected_names)):
        raise ValueError('Incompatible case schema or shape')
    if z['names'].tolist() != expected_names or len(set(expected_names)) != len(expected_names):
        raise ValueError('Feature names/order mismatch or duplicates')
    if z['X'].dtype != np.float32 or not np.isfinite(z['X']).all():
        raise ValueError('Non-finite or incorrectly typed features')
    if z['observed'].shape != (n,) or z['observed'].dtype != bool:
        raise ValueError('Invalid observation mask')
    if not np.array_equal(z['ref'], reference) or not np.array_equal(z['period'], periods):
        raise ValueError('Reference/feature frame alignment mismatch')
    if not set(np.unique(z['ref'])) <= {0, 1, 3} or not np.any(z['ref'] == 0) or not np.any(z['ref'] == 1):
        raise ValueError('SkillCorner needs H/A/unknown labels with no invented D')
    if np.any((periods == 0) & (z['ref'] != 3)):
        raise ValueError('Labels outside active match periods')


def legacy_snapshot(root, cases):
    """Hash only pre-existing legacy external files, never challenge data."""
    found = {}
    old_root = CODE.parent / 'independent-reference'
    for match in se_load.SKILLCORNER:
        for base in (old_root, root):
            for p in list((base / 'raw' / match).glob('*')) + list((base / 'cache').glob(match + '-*')):
                if p.is_file():
                    found[str(p)] = sha256(p)
        p = cases / ('skillcorner-' + match + '.npz')
        if p.is_file():
            found[str(p)] = sha256(p)
    return found


def prepare(root, cases, report):
    protocol = json.loads((CODE / 'benchmark/skillcorner/protocol.json').read_text(encoding='utf-8'))
    if protocol['revision'] != '4340d274572876239c154c90bc507a9b3250a656' or not protocol['license'].startswith('MIT'):
        raise ValueError('Unexpected source revision/licence')
    if set(se_load.SKILLCORNER) & set(ADDITIONAL_SKILLCORNER) or len(set(se_load.AVAILABLE)) != 28:
        raise ValueError('Duplicate match identities')
    root, cases = root.resolve(), cases.resolve()
    if root == CODE or CODE in root.parents or cases == CODE or CODE in cases.parents:
        raise ValueError('Raw/processed data must stay outside the code repository')
    before = legacy_snapshot(root, cases)
    files = list(assets(protocol, root))
    source_hashes = {name: sha256(CODE / name) for name in FEATURE_SOURCES}
    # Determine the exact schema using tracking-only fixtures, without reading model weights.
    from gap_solver.motion import motion_frame
    fixture = [motion_frame(1, (50.0, 34.0), ((49.0, 34.0),), ((60.0, 34.0),), (1,), (2,)) for _ in range(800)]
    expected_names = build_case(fixture, np.full(800, 3, np.uint8))['names'].tolist()
    records = []
    cases.mkdir(parents=True, exist_ok=True)
    for match, cid in zip(ADDITIONAL_SKILLCORNER, ADDITIONAL_CASES):
        folder = root / 'raw' / match
        raw, raw_periods, meta = inspect_raw(folder, match)
        prefix = root / 'cache' / (match + '-detected')
        cache_paths = [Path(str(prefix) + s) for s in SUFFIXES]
        inputs = {p.name: sha256(p) for p in (folder / (match + '_match.json'), folder / (match + '_tracking_extrapolated.jsonl'), folder / (match + '_phases_of_play.csv'))}
        if any(p.exists() for p in cache_paths):
            if not all(p.exists() for p in cache_paths):
                raise ValueError('Partial motion cache preserved: ' + match)
            data = load_motion_cache(prefix)
            if data.notes['input_sha256'] != inputs:
                raise ValueError('Existing cache differs from pinned sources')
        else:
            data = load_skillcorner(folder / (match + '_match.json'), folder / (match + '_tracking_extrapolated.jsonl'), folder / (match + '_phases_of_play.csv'), detected_only=True)
            save_motion_cache(data, prefix)
        if data.match_id != match or data.notes['native_grid_rows'] != raw['tracking_rows']:
            raise ValueError('Motion cache identity/grid mismatch')
        # Always reload through the public cache adapter, as se_load.load does.
        ref, source_frames = data.reference.copy(), data.source_frames.copy()
        del data
        data = load_motion_cache(prefix)
        if not np.array_equal(data.reference, ref) or not np.array_equal(data.source_frames, source_frames):
            raise ValueError('Cache round-trip changed frame alignment')
        case_path = cases / (cid + '.npz')
        case_meta = cases / (cid + '.data.json')
        identity = dict(source_hashes=source_hashes, input_sha256=inputs, feature_names=expected_names)
        if case_path.exists() or case_meta.exists():
            if not case_path.exists() or not case_meta.exists():
                raise ValueError('Partial case preserved: ' + cid)
            saved = json.loads(case_meta.read_text(encoding='utf-8'))
            if saved['identity'] != identity or saved['case_sha256'] != sha256(case_path):
                raise ValueError('Existing processed case differs; preserving it: ' + cid)
        else:
            z = build_case(data.frames(), data.reference)
            validate_case(z, data.reference, data.periods, expected_names)
            temp = case_path.with_suffix('.new.npz')
            np.savez_compressed(temp, **z)
            temp.replace(case_path)
            write_json(case_meta, dict(identity=identity, case_sha256=sha256(case_path)))
            del z
        with np.load(case_path, allow_pickle=False) as archive:
            z = {key: archive[key] for key in archive.files}
        validate_case(z, data.reference, data.periods, expected_names)
        known = data.reference < 2
        active = data.periods > 0
        usable = np.fromiter((f.period > 0 and bool(f.home_xy) and bool(f.away_xy) for f in data.frames()), bool)
        record = dict(match_id=match, home_team=meta['home_team']['name'], away_team=meta['away_team']['name'],
                      **raw, raw_period_counts=raw_periods, canonical_25hz_frames=len(data.frames()),
                      active_25hz_frames=int(active.sum()), both_teams_visible_25hz_frames=int(usable.sum()),
                      detected_ball_available_25hz_frames=int(z['observed'].sum()),
                      known_ha_native_frames=int((data.native_reference < 2).sum()),
                      known_ha_25hz_frames=int(known.sum()),
                      labels={label: int((data.reference == i).sum()) for i, label in enumerate(('H', 'A', 'D', 'X'))},
                      feature_shape=list(z['X'].shape), case_sha256=sha256(case_path),
                      cache_files={p.name: sha256(p) for p in cache_paths},
                      phase_reconciliation=data.notes['phase_reconciliation'],
                      phase_period_conflict_native_frames=data.notes['phase_period_conflict_native_frames'],
                      historical_split=next(k for k, values in protocol['split'].items() if int(match) in values),
                      compatible=True)
        records.append(record)
        write_json(root / 'integrity' / (match + '.json'), record)
        print(match, record['tracking_rows'], 'native rows;', record['known_ha_25hz_frames'], 'labelled 25Hz rows;', z['X'].shape, flush=True)
        del data, z
    after = legacy_snapshot(root, cases)
    if before != after:
        raise ValueError('Legacy external files changed')
    output = dict(schema_version=1, source=protocol['source'], source_revision=protocol['revision'],
                  license=protocol['license'], attribution=protocol['attribution'],
                  prepared_at_utc=datetime.now(timezone.utc).isoformat(),
                  runtime=dict(python=platform.python_version(), numpy=np.__version__),
                  raw_and_motion_root=str(root), cases_root=str(cases), source_hashes=source_hashes,
                  model_operations_performed=False, release_supports_generated=False,
                  historical_match_ids=list(se_load.ALL), additional_match_ids=list(ADDITIONAL_CASES),
                  available_external_matches=len(se_load.AVAILABLE), feature_names=expected_names,
                  preexisting_legacy_files_checked=len(before), legacy_files_unchanged=before == after,
                  legacy_files_available_for_reverification=bool(before), files=files, matches=records)
    write_json(root / 'provenance.json', output)
    write_json(report, output)
    print('Prepared 10 additional matches; 28 catalogued external matches; no model operations.', flush=True)
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=se_load.ADDITIONAL_ROOT)
    parser.add_argument('--cases', type=Path, default=se_load.PRIVATE / 'cases')
    parser.add_argument('--report', type=Path, default=CODE / 'reports/data-integration/skillcorner-additional-10.json')
    args = parser.parse_args()
    prepare(args.root, args.cases, args.report)


if __name__ == '__main__':
    main()
