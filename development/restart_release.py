"""Frozen control, gap rule, decoder restart, then automatic kickoff patch.

    python -I restart_release.py --prefix <tactical prefix> --tags <tags.xml> --out <new dir>
"""
import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from gap_liveness import apply_gap_rule
from gap_release import labels_sha256
from gap_solver.materialization_control import materialize_abstentions
from kickoff_patch import apply_kickoff_patch, kickoff_starts
from release_runtime import predict_selected
from touch_decoder import decode_variable
from touch_evidence import prepare_evidence

VERSION = '2026.11.11-stoppage-decoder-restart'


@dataclass(frozen=True)
class Assembly:
    control: tuple
    gapped: tuple
    restarted: tuple
    final: tuple
    stoppage_gaps: tuple
    gap_summary: dict
    kickoff_changed: dict


def decode_stoppages(frames, control, prepared, *, use_restart=True):
    rows, costs, periods, usable, _ = prepared
    original = tuple(materialize_abstentions(decode_variable(rows, periods, usable, costs), periods))
    if original != tuple(control):
        raise ValueError('Variable decoder does not reproduce the frozen control')
    first = apply_gap_rule(frames, control)
    usable2 = list(usable)
    if not use_restart:
        return first, first, usable2
    for first_frame, stop in first.stoppage_gaps:
        usable2[first_frame:stop] = [False]*(stop-first_frame)
    latent = decode_variable(rows, periods, usable2, costs)
    second = apply_gap_rule(frames, materialize_abstentions(latent, periods))
    if second.stoppage_gaps != first.stoppage_gaps:
        raise ValueError('Stoppage gaps changed during the second application')
    return first, second, usable2


def assemble(frames, starts, *, use_restart=True):
    control = predict_selected(frames).labels
    prepared = prepare_evidence(frames, [], 0, 32)
    first, second, _ = decode_stoppages(frames, control, prepared, use_restart=use_restart)
    patch = apply_kickoff_patch(frames, second.labels, starts)
    return Assembly(tuple(control), first.labels, second.labels, patch.labels,
                    first.stoppage_gaps, second.summary, patch.changed)


def generate(prefix, tags, out, *, use_restart=True):
    from release_runtime import load_source, submission_bytes
    out = Path(out)
    if out.exists() or out.is_symlink():
        raise FileExistsError('Output directory must not exist')
    prefix = str(prefix)
    frames, _ = load_source(*(Path(prefix+s) for s in ('_atd.xml', '_atd.txt', '_homography.csv')))
    result = assemble(frames, kickoff_starts(tags), use_restart=use_restart)
    data = submission_bytes(result.final)
    receipt = dict(version=VERSION, use_restart=use_restart, rows=len(result.final),
                   csv_sha256=hashlib.sha256(data).hexdigest(),
                   control_labels_sha256=labels_sha256(result.control),
                   first_gap_labels_sha256=labels_sha256(result.gapped),
                   restart_gap_labels_sha256=labels_sha256(result.restarted),
                   final_labels_sha256=labels_sha256(result.final),
                   stoppage_gaps=len(result.stoppage_gaps), gap_summary=result.gap_summary,
                   kickoff_changed=result.kickoff_changed)
    out.mkdir(parents=True, exist_ok=False)
    (out/'submission.csv').write_bytes(data)
    (out/'restart-release-receipt.json').write_text(json.dumps(receipt, sort_keys=True, indent=1)+'\n', encoding='utf-8')
    return receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prefix', required=True)
    parser.add_argument('--tags', required=True, help='Automatic kickoff tags only')
    parser.add_argument('--out', required=True, help='New nonexistent output directory')
    args = parser.parse_args(argv)
    receipt = generate(args.prefix, args.tags, args.out)
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
