"""Release entry point: observed-touch decoding + gap rule + kickoff patch -> submission CSV.

    python -I touch_release.py --prefix <tactical filename prefix> --tags <smart_tagging.xml> --out <new dir>

With touches disabled the output equals gap_release.py's (the current candidate).
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))  # python -I omits the script directory

from gap_release import assemble, labels_sha256
from kickoff_patch import kickoff_starts
from observed_touch import detect_observed_touches, predict_observed_touch
from release_runtime import load_source, predict_selected, submission_bytes

VERSION = '2026.11.10-observed-touch'
THETA, BETA, C_TOUCH = 3, 2, 8   # the setting the brief fixes; not tuned here


def predict_labels(frames, *, use_touch=True):
    if not use_touch:
        return tuple(predict_selected(frames).labels)
    return tuple(predict_observed_touch(frames, THETA, BETA, C_TOUCH).labels)


def generate(prefix, tags_path, out, *, use_touch=True):
    out = Path(out)
    if out.exists():
        raise FileExistsError('Output directory must not exist')
    frames, _ = load_source(*(Path(prefix + s) for s in ('_atd.xml', '_atd.txt', '_homography.csv')))
    base = predict_labels(frames, use_touch=use_touch)
    result = assemble(frames, base, kickoff_starts(tags_path))
    data = submission_bytes(result.final)
    out.mkdir(parents=True)
    (out / 'submission.csv').write_bytes(data)
    receipt = dict(version=VERSION, rows=len(result.final), csv_sha256=hashlib.sha256(data).hexdigest(),
                   control_labels_sha256=labels_sha256(result.control) if not use_touch else None,
                   decoded_labels_sha256=labels_sha256(result.control),
                   gap_labels_sha256=labels_sha256(result.gapped), final_labels_sha256=labels_sha256(result.final),
                   touch_enabled=bool(use_touch))
    (out / 'touch-release-receipt.json').write_text(json.dumps(receipt, sort_keys=True, separators=(',', ':')) + '\n', encoding='utf-8')
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
