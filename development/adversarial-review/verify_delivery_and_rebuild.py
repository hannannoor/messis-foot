"""Independent synthetic cache and Git-byte checks; no challenge inputs."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent
SNAPSHOTS = ROOT / 'snapshots'
REFS = {
    'current-cee6741': 'cee674190775e9356745f461ba1561e9f2a46f7e',
    'main-3a1c860': '3a1c8608e050e2f812826719e1af882d87cf2f67',
    'audit-f426c0e': 'f426c0e542c1ffdab1296531bdcf5ff0af9d7405',
}


def git(*args):
    return subprocess.check_output(['git', '--git-dir=' + str(ROOT / 'mirror.git'), *args])


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    integrity = {}
    for directory, commit in REFS.items():
        rows = git('ls-tree', '-r', '-z', commit).split(b'\0')
        checked = 0
        for row in rows:
            if not row:
                continue
            meta, name = row.split(b'\t', 1)
            mode, kind, object_id = meta.split()
            assert kind == b'blob' and mode in (b'100644', b'100755')
            data = (SNAPSHOTS / directory / name.decode()).read_bytes()
            actual = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
            assert actual == object_id.decode(), name.decode()
            checked += 1
        integrity[directory] = {'commit': commit, 'tracked_blobs_equal': checked}

    audit = SNAPSHOTS / 'audit-f426c0e' / 'docs' / 'competitor-audit-2026-11-08'
    manifest = json.loads((audit / 'delivery-manifest.json').read_text(encoding='utf-8'))
    manifest_checks = []
    for entry in manifest['reports'] + [manifest['combined']]:
        actual_name = 'coordinator.md' if entry['path'] == 'root-review.md' else entry['path']
        data = (audit / actual_name).read_bytes()
        matches = len(data) == entry['bytes'] and sha(data) == entry['sha256']
        trimmed_matches = data.endswith(b'\r\n') and len(data[:-2]) == entry['bytes'] and sha(data[:-2]) == entry['sha256']
        assert not matches and trimmed_matches
        manifest_checks.append(dict(declared_path=entry['path'], actual_path=actual_name,
            declared_path_exists=(audit / entry['path']).is_file(), exact_match=matches,
            single_trailing_crlf_explains_difference=trimmed_matches, actual_sha256=sha(data)))
    absent = {k: not (audit / manifest['verification'][k]).exists() for k in ('log', 'probe_script')}
    assert all(absent.values())

    current = SNAPSHOTS / 'current-cee6741'
    sys.path[:0] = [str(current), str(current / 'tests')]
    import numpy as np
    from test_skillcorner import write_source
    from gap_solver.skillcorner import load_skillcorner, save_motion_cache, load_motion_cache
    (ROOT / '.tmp').mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='cache-rebuild-', dir=ROOT / '.tmp') as work:
        work = Path(work)
        match = load_skillcorner(*write_source(work))
        prefixes = [work / 'generation-a', work / 'generation-b']
        for prefix in prefixes:
            save_motion_cache(match, prefix)
            load_motion_cache(prefix)  # Both legitimate generations pass their own integrity checks.
        metas = [json.loads(Path(str(p) + '.metadata.json').read_text(encoding='utf-8')) for p in prefixes]
        assert metas[0]['generation_id'] != metas[1]['generation_id']
        assert metas[0]['input_identity'] == metas[1]['input_identity']
        differing_arrays = []
        equal_arrays = 0
        for suffix in ('.features.npz', '.reference.npz'):
            with np.load(str(prefixes[0]) + suffix, allow_pickle=False) as a, np.load(str(prefixes[1]) + suffix, allow_pickle=False) as b:
                assert a.files == b.files
                for name in a.files:
                    av, bv = a[name], b[name]
                    same = np.array_equal(av, bv, equal_nan=True) if av.dtype.kind in 'fc' else np.array_equal(av, bv)
                    if same:
                        equal_arrays += 1
                    else:
                        differing_arrays.append(suffix + ':' + name)
        assert differing_arrays == ['.features.npz:generation_id', '.reference.npz:generation_id']
        hashes = {suffix: [sha(Path(str(p) + suffix).read_bytes()) for p in prefixes]
                  for suffix in ('.features.npz', '.reference.npz', '.metadata.json')}
        assert all(pair[0] != pair[1] for pair in hashes.values())
        rebuild = dict(synthetic_only=True, both_generations_load=True,
            stable_input_identity_equal=True, generation_ids_differ=True,
            equal_semantic_arrays=equal_arrays, differing_arrays=differing_arrays,
            all_three_container_hashes_differ=True)

    output = dict(snapshot_integrity=integrity, audit_manifest_checks=manifest_checks,
        missing_declared_verification_artifacts=absent, synthetic_rebuild=rebuild,
        challenge_inputs_opened=False, predictor_source_changes=False)
    (ROOT / 'delivery-and-rebuild-verification.json').write_text(json.dumps(output, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(dict(snapshot_counts={k:v['tracked_blobs_equal'] for k,v in integrity.items()},
        stale_manifest_reports=len(manifest_checks), missing_verification_artifacts=absent,
        synthetic_rebuild=rebuild)))


if __name__ == '__main__':
    main()
