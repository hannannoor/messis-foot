"""Selected frozen-control inference; only local geometry and standard library."""
from dataclasses import asdict, dataclass, replace
import hashlib
import json
from pathlib import Path
from typing import Sequence

from ball_gap_policy import POLICY_ID, decode_ball_gap
from gap_solver.anonymous_motion import associate_anonymous
from gap_solver.input_contract import read_epts_contract, iter_records, quality_mask, sha256
from gap_solver.io import N_FRAMES
from gap_solver.materialization_control import materialize_abstentions
from gap_solver.motion import MotionFrame
from gap_solver.soft_sequence import sequence_usable
from gap_solver.tactical import PortableTree, feature_rows
from gap_solver.tactical_model import FROZEN_MODEL

MODEL_SHA256 = '363c45c70838b398cd87aee7474d7e281fd392f059a31b85712e312058aaab4d'
VERSION = '2026.11.09-frozen-control-release'


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
