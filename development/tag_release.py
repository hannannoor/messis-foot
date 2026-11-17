"""Release entry point: control + tag evidence + gap rule + kickoff patch -> submission CSV.

    python -I tag_release.py --prefix <tactical filename prefix> --tags <smart_tagging.xml> --out <new dir>

With tags disabled (or unusable) the output equals gap_release.py's.
"""
import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))  # python -I omits the script directory

import tag_evidence as te
from gap_release import assemble, labels_sha256
from kickoff_patch import kickoff_starts

VERSION = '2026.11.10-tag-evidence'


@dataclass(frozen=True)
class Predicted:
    control: tuple       # control labels rebuilt from its emissions (equals predict_selected)
    fused: tuple         # control + tag evidence (equals control when tags are disabled)
    rows: list           # control emissions
    fused_rows: list
    effective: list
    owner: list
    names: tuple
    estimate: object


def control_parts(frames):
    """Everything predict_selected computes, exposed so the emissions can be reused."""
    from ball_gap_policy import POLICY_ID  # noqa: F401  (identity of the frozen policy)
    from gap_solver.materialization_control import materialize_abstentions
    from gap_solver.soft_sequence import sequence_usable
    from gap_solver.tactical import PortableTree, feature_rows
    from gap_solver.tactical_model import FROZEN_MODEL
    from release_runtime import MODEL_SHA256, _json_bytes
    if any(f.tag_team or f.restart_hint or f.dead_evidence or f.dead_source for f in frames):
        raise ValueError('Selected release accepts geometry without label hints')
    if hashlib.sha256(_json_bytes(FROZEN_MODEL['model'])).hexdigest() != MODEL_SHA256:
        raise ValueError('Frozen tactical model identity changed')
    tree = PortableTree(FROZEN_MODEL['model'])
    supports = [tree.predict(row) for row in feature_rows(frames)]
    periods = [f.period for f in frames]
    observed = [f.ball_observed for f in frames]
    rows, effective = te.control_rows(supports, periods, [sequence_usable(f) for f in frames], observed)
    labels = tuple(materialize_abstentions(te.decode_rows(rows, periods, effective), periods))
    return supports, rows, effective, labels, periods, observed


def predict(frames, tags, *, use_tags=True, parts=None):
    _, rows, effective, control, periods, observed = parts or control_parts(frames)
    from gap_solver.materialization_control import materialize_abstentions
    owner, names = te.owner_track(tags, periods)
    estimate = te.estimate_mapping(control, rows, observed, periods, owner, names)
    if not (use_tags and estimate.enabled):
        return Predicted(control, control, rows, rows, effective, owner, names, estimate)
    fused_rows = te.fuse(rows, owner, estimate.mapping, names, estimate.p)
    fused = tuple(materialize_abstentions(te.decode_rows(fused_rows, periods, effective), periods))
    return Predicted(control, fused, rows, fused_rows, effective, owner, names, estimate)


def generate(prefix, tags_path, out, *, use_tags=True):
    from release_runtime import load_source, submission_bytes
    out = Path(out)
    if out.exists():
        raise FileExistsError('Output directory must not exist')
    frames, _ = load_source(*(Path(prefix + s) for s in ('_atd.xml', '_atd.txt', '_homography.csv')))
    predicted = predict(frames, te.read_tags(tags_path), use_tags=use_tags)
    result = assemble(frames, predicted.fused, kickoff_starts(tags_path))
    data = submission_bytes(result.final)
    out.mkdir(parents=True)
    (out / 'submission.csv').write_bytes(data)
    estimate = predicted.estimate
    receipt = dict(version=VERSION, rows=len(result.final), csv_sha256=hashlib.sha256(data).hexdigest(),
                   control_labels_sha256=labels_sha256(predicted.control),
                   fused_labels_sha256=labels_sha256(predicted.fused),
                   final_labels_sha256=labels_sha256(result.final),
                   tags_enabled=bool(use_tags and estimate.enabled), reliability=estimate.p,
                   confident_tagged_frames=estimate.frames)
    (out / 'tag-release-receipt.json').write_text(json.dumps(receipt, sort_keys=True, separators=(',', ':')) + '\n', encoding='utf-8')
    return receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prefix', required=True)
    parser.add_argument('--tags', required=True, help='Smart Tagging XML')
    parser.add_argument('--out', required=True, help='New nonexistent output directory')
    args = parser.parse_args(argv)
    receipt = generate(args.prefix, args.tags, args.out)
    print(json.dumps(dict(rows=receipt['rows'], csv_sha256=receipt['csv_sha256'], tags_enabled=receipt['tags_enabled']), sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
