"""Selected frozen-control inference; only local geometry and standard library."""
from dataclasses import asdict, dataclass, replace
import argparse
from collections import Counter
import csv
import hashlib
import io
import json
import os
from pathlib import Path
from typing import Sequence
import xml.etree.ElementTree as ET

from ball_gap_policy import POLICY_ID, decode_ball_gap
from gap_solver.anonymous_motion import associate_anonymous
from gap_solver.input_contract import read_epts_contract, iter_records, quality_mask, sha256, reject_linked_ancestors
from gap_solver.io import N_FRAMES
from gap_solver.materialization_control import materialize_abstentions
from gap_solver.motion import MotionFrame
from gap_solver.soft_sequence import sequence_usable
from gap_solver.tactical import PortableTree, feature_rows
from gap_solver.tactical_model import FROZEN_MODEL

MODEL_SHA256 = '363c45c70838b398cd87aee7474d7e281fd392f059a31b85712e312058aaab4d'
VERSION = '2026.11.09-frozen-control-release'
SOURCE_FILES = {
    'ball_gap_policy': 'ball_gap_policy.py',
    'gap_solver': 'gap_solver/__init__.py',
    'gap_solver.anonymous_motion': 'gap_solver/anonymous_motion.py',
    'gap_solver.core': 'gap_solver/core.py',
    'gap_solver.input_contract': 'gap_solver/input_contract.py',
    'gap_solver.io': 'gap_solver/io.py',
    'gap_solver.materialization_control': 'gap_solver/materialization_control.py',
    'gap_solver.motion': 'gap_solver/motion.py',
    'gap_solver.soft_sequence': 'gap_solver/soft_sequence.py',
    'gap_solver.tactical': 'gap_solver/tactical.py',
    'gap_solver.tactical_model': 'gap_solver/tactical_model.py',
    'gap_solver.temporal': 'gap_solver/temporal.py',
    'release_runtime': 'release_runtime.py',
}
RELEASE_SETTINGS = {
    'schema_version': 1,
    'version': '2026.11.09-frozen-control-release',
    'source_base_commit': 'aaa5ba8f938545f77d8e2cb084bea561ef09c680',
    'policy_id': 'w0-c32-neutral-missing',
    'model_sha256': '363c45c70838b398cd87aee7474d7e281fd392f059a31b85712e312058aaab4d',
    'motion_weight': 0.0,
    'switch_cost': 32.0,
    'builder_version': 1,
    'reference_runtime': 'CPython 3.14.5 Windows x64',
    'csv_schema': 'frame,label; UTF-8 without BOM; CRLF including final row',
    'semantic_schema': 'release-input-v1; sorted compact JSON MotionFrame records; LF',
}
_BUNDLE_MANIFEST = None
_BUNDLE_ARTIFACT = None


def _json_bytes(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')


@dataclass(frozen=True)
class ReleasePrediction:
    latent: tuple[str, ...]
    labels: tuple[str, ...]
    counts: dict[str, int]


def load_source(meta: Path, raw: Path, quality: Path, *, scope: str = 'tactical') -> tuple[list[MotionFrame], dict]:
    if scope not in ('tactical', 'synthetic'):
        raise ValueError('Expected tactical source or explicit synthetic fixture')
    inputs = dict(metadata=Path(meta), tracking=Path(raw), homography=Path(quality))
    identities = {name: sha256(path) for name, path in inputs.items()}
    contract = read_epts_contract(meta)
    if scope == 'tactical' and contract.rows != N_FRAMES:
        raise ValueError('Expected all original tactical frames')
    blocks = [(1, 0, contract.rows-1)] if scope == 'synthetic' else None
    frames = list(iter_records(contract, raw, blocks))
    mask = quality_mask(quality, len(frames))
    frames = [frame if ok else replace(frame, geometry_valid=False) for frame, ok in zip(frames, mask)]
    frames, association = associate_anonymous(frames)
    audit = dict(rows=contract.rows, fps=25, scope=scope, input_sha256=identities,
                 source_start_index=1, output_start_index=0,
                 geometry_accepted=sum(mask), geometry_rejected=len(mask)-sum(mask),
                 source_speed_used=False, identity_verified=False, freshness_verified=False,
                 association=association)
    return frames, audit


def predict_selected(frames: Sequence[MotionFrame]) -> ReleasePrediction:
    if any(f.tag_team or f.restart_hint or f.dead_evidence or f.dead_source for f in frames):
        raise ValueError('Selected release accepts geometry without label hints')
    if hashlib.sha256(_json_bytes(FROZEN_MODEL['model'])).hexdigest() != MODEL_SHA256:
        raise ValueError('Frozen tactical model identity changed')
    tree = PortableTree(FROZEN_MODEL['model'])
    supports = [tree.predict(row) for row in feature_rows(frames)]
    periods = [frame.period for frame in frames]
    latent, counts = decode_ball_gap(supports, periods, [sequence_usable(f) for f in frames],
                                    [f.ball_observed for f in frames])
    labels = materialize_abstentions(latent, periods)
    counts = dict(counts, materialized_rows=sum(a != b for a, b in zip(latent, labels)),
                  latent_unknown_active=sum(bool(p) and label == 'X' for p, label in zip(periods, latent)))
    return ReleasePrediction(tuple(latent), tuple(labels), counts)


def semantic_sha256(frames: Sequence[MotionFrame]) -> str:
    digest = hashlib.sha256(b'release-input-v1\n')
    for frame in frames:
        digest.update(_json_bytes(asdict(frame)))
        digest.update(b'\n')
    return digest.hexdigest()


def submission_bytes(labels: Sequence[str]) -> bytes:
    if any(label not in ('H', 'A', 'D', 'X') for label in labels):
        raise ValueError('Invalid submission label')
    stream = io.StringIO(newline='')
    writer = csv.writer(stream, lineterminator='\r\n')
    writer.writerow(('frame', 'label'))
    writer.writerows(enumerate(labels))
    return stream.getvalue().encode('utf-8')


def _release_identity() -> dict:
    if _BUNDLE_MANIFEST is not None:
        manifest = _BUNDLE_MANIFEST
        identity = dict(mode='standalone', artifact_sha256=sha256(_BUNDLE_ARTIFACT))
    else:
        root = Path(__file__).resolve().parent
        manifest = dict(RELEASE_SETTINGS, sources={path: sha256(root/path) for path in sorted(SOURCE_FILES.values())})
        identity = dict(mode='source')
    return dict(identity, manifest_sha256=hashlib.sha256(_json_bytes(manifest)).hexdigest(),
                source_sha256=manifest['sources'], version=VERSION)


def _write_exclusive(path: Path, data: bytes) -> None:
    with path.open('xb') as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())


def _protect_destination(directory: Path) -> None:
    reject_linked_ancestors(directory)
    if directory.exists():
        raise FileExistsError('Release requires a new nonexistent output directory')


def _verify_generation(directory: Path, *, _allow_incomplete: bool = False) -> dict:
    directory = Path(directory)
    if ((directory/'.incomplete').exists() and not _allow_incomplete) or not (directory/'release-receipt.json').is_file():
        raise ValueError('Incomplete release generation')
    expected = {'submission.csv', 'release-receipt.json'} | ({'.incomplete'} if _allow_incomplete else set())
    if {p.name for p in directory.iterdir()} != expected:
        raise ValueError('Unexpected files in release generation')
    receipt = json.loads((directory/'release-receipt.json').read_text(encoding='utf-8'))
    required = {'schema_version', 'policy_id', 'model_sha256', 'release', 'scope', 'input_sha256',
                'semantic_sha256', 'labels_sha256', 'csv_sha256', 'rows', 'label_counts', 'policy_counts'}
    if set(receipt) != required or receipt['schema_version'] != 1 or receipt['policy_id'] != POLICY_ID:
        raise ValueError('Invalid release receipt')
    data = (directory/'submission.csv').read_bytes()
    if hashlib.sha256(data).hexdigest() != receipt['csv_sha256']:
        raise ValueError('Submission identity differs from receipt')
    table = list(csv.reader(io.StringIO(data.decode('utf-8'), newline='')))
    if not table or table[0] != ['frame', 'label'] or len(table)-1 != receipt['rows']:
        raise ValueError('Submission dimensions differ from receipt')
    if any(len(row) != 2 or row[0] != str(i) for i, row in enumerate(table[1:])):
        raise ValueError('Submission indices differ')
    labels = [row[1] for row in table[1:]]
    if submission_bytes(labels) != data:
        raise ValueError('Noncanonical submission bytes')
    if (hashlib.sha256(''.join(labels).encode('ascii')).hexdigest() != receipt['labels_sha256']
            or dict(Counter(labels)) != receipt['label_counts']):
        raise ValueError('Submission labels differ from receipt')
    return receipt


def run_source(meta: Path, raw: Path, quality: Path, directory: Path, *, scope: str = 'tactical') -> dict:
    directory = Path(directory)
    _protect_destination(directory)
    frames, audit = load_source(meta, raw, quality, scope=scope)
    prediction = predict_selected(frames)
    semantic = semantic_sha256(frames)
    identity = _release_identity()
    data = submission_bytes(prediction.labels)
    directory.parent.mkdir(parents=True, exist_ok=True)
    _protect_destination(directory)
    directory.mkdir()  # the exclusive claim; never accept even an existing empty folder
    _write_exclusive(directory/'.incomplete', b'incomplete\n')
    _write_exclusive(directory/'submission.csv', data)
    current = {name: sha256(path) for name, path in zip(('metadata','tracking','homography'), (meta,raw,quality))}
    if current != audit['input_sha256']:
        raise ValueError('Input changed during inference')
    receipt = dict(schema_version=1, policy_id=POLICY_ID, model_sha256=MODEL_SHA256,
                   release=identity, scope=scope, input_sha256=current, semantic_sha256=semantic,
                   labels_sha256=hashlib.sha256(''.join(prediction.labels).encode('ascii')).hexdigest(),
                   csv_sha256=sha256(directory/'submission.csv'), rows=len(prediction.labels),
                   label_counts=dict(Counter(prediction.labels)), policy_counts=prediction.counts)
    _write_exclusive(directory/'release-receipt.json', _json_bytes(receipt)+b'\n')
    _verify_generation(directory, _allow_incomplete=True)
    (directory/'.incomplete').unlink()
    return receipt


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', action='version', version=VERSION)
    parser.add_argument('--prefix', required=True, help='Local tactical EPTS filename prefix')
    parser.add_argument('--out', required=True, help='New nonexistent output directory')
    args = parser.parse_args(argv)
    try:
        receipt = run_source(*(Path(args.prefix+suffix) for suffix in ('_atd.xml','_atd.txt','_homography.csv')), Path(args.out))
    except (OSError, ValueError, TypeError, KeyError, ET.ParseError) as error:
        parser.error('Release input/output validation failed ('+type(error).__name__+'); check schema, input identity and a new output directory')
    print(json.dumps(dict(status='complete', policy_id=POLICY_ID, rows=receipt['rows'], csv_sha256=receipt['csv_sha256']), sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
