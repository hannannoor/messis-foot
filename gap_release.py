"""Release entry point: frozen control + gap rule + kickoff patch -> submission CSV.

    python -I gap_release.py --prefix <tactical filename prefix> --tags <smart_tagging.xml> --out <new dir>
"""
import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from gap_liveness import apply_gap_rule
from kickoff_patch import apply_kickoff_patch, kickoff_starts

VERSION = '2026.11.10-gap-rule-kickoff-patch'


@dataclass(frozen=True)
class Assembly:
    control: tuple
    gapped: tuple
    final: tuple
    gap_summary: dict
    kickoff: object


def assemble(frames, control, starts, *, gap=True, kickoff=True):
    control = tuple(control)
    gap_result = apply_gap_rule(frames, control) if gap else None
    gapped = gap_result.labels if gap else control
    patch = apply_kickoff_patch(frames, gapped, starts) if kickoff else None
    return Assembly(control, gapped, patch.labels if kickoff else gapped,
                    gap_result.summary if gap else {}, patch)


def labels_sha256(labels):
    return hashlib.sha256(''.join(labels).encode('ascii')).hexdigest()


def generate(prefix, tags, out):
    from release_runtime import load_source, predict_selected, submission_bytes
    out = Path(out)
    if out.exists():
        raise FileExistsError('Output directory must not exist')
    frames, _ = load_source(*(Path(prefix + s) for s in ('_atd.xml', '_atd.txt', '_homography.csv')))
    control = predict_selected(frames).labels
    result = assemble(frames, control, kickoff_starts(tags))
    data = submission_bytes(result.final)
    out.mkdir(parents=True)
    (out / 'submission.csv').write_bytes(data)
    receipt = dict(version=VERSION, rows=len(result.final), csv_sha256=hashlib.sha256(data).hexdigest(),
                   control_labels_sha256=labels_sha256(result.control),
                   gap_labels_sha256=labels_sha256(result.gapped),
                   final_labels_sha256=labels_sha256(result.final), gap_summary=result.gap_summary,
                   kickoff_changed=result.kickoff.changed)
    (out / 'gap-release-receipt.json').write_text(json.dumps(receipt, sort_keys=True, separators=(',', ':')) + '\n', encoding='utf-8')
    return receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prefix', required=True)
    parser.add_argument('--tags', required=True, help='Smart Tagging XML (kickoff only)')
    parser.add_argument('--out', required=True, help='New nonexistent output directory')
    args = parser.parse_args(argv)
    receipt = generate(args.prefix, args.tags, args.out)
    print(json.dumps(dict(rows=receipt['rows'], csv_sha256=receipt['csv_sha256']), sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
