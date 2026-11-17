"""Local gap-rule support counts and threshold proximity; no per-gap output."""
import json
from pathlib import Path
from statistics import median
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gap_liveness import player_speed_statistics, long_gaps, apply_gap_rule
from release_runtime import load_source, predict_selected

ROOT = Path(__file__).resolve().parent
OUT = ROOT/'reports/submission/gap-support.json'


def support_summary(statistics, gaps, chosen, reference):
    chosen = set(chosen)
    result = {}
    for name, selected in (('relabelled', True), ('not_relabelled', False)):
        blocks = [(a,b) for a,b in gaps if ((a,b) in chosen) == selected]
        samples = [[v for v in statistics[a:b] if v is not None] for a,b in blocks]
        counts = sorted(len(values) for values in samples)
        entry = dict(gaps=len(blocks), minimum_samples=min(counts) if counts else None,
                     p10_samples=counts[int(.1*(len(counts)-1)+.5)] if counts else None,
                     median_samples=median(counts) if counts else None,
                     fewer_than_5_samples=sum(n < 5 for n in counts), no_samples=sum(n == 0 for n in counts))
        if selected:
            near = [block for block, values in zip(blocks, samples) if values and reference is not None and median(values) > .9*reference]
            frames = sum(b-a for a,b in blocks)
            entry.update(near_threshold_gaps=len(near),
                         near_threshold_frame_share=sum(b-a for a,b in near)/frames if frames else None)
        result[name] = entry
    return result


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open('x', encoding='utf-8') as handle:
        handle.write('{"status":"running"}\n')
    prefix = json.loads((ROOT/'.superpowers/release/target-handling.json').read_text(encoding='utf-8'))['input_prefix']
    frames, _ = load_source(*(Path(prefix+s) for s in ('_atd.xml','_atd.txt','_homography.csv')))
    application = apply_gap_rule(frames, predict_selected(frames).labels)
    gaps = long_gaps(frames)
    result = dict(status='complete', long_gaps=len(gaps), reference_speed_mps=application.summary['reference_speed_mps'],
                  restart_extension_frames=application.summary['restart_extension_frames'],
                  **support_summary(player_speed_statistics(frames), gaps, application.stoppage_gaps,
                                    application.summary['reference_speed_mps']))
    OUT.write_text(json.dumps(result, sort_keys=True, indent=1)+'\n', encoding='utf-8')
    print(json.dumps(result, sort_keys=True, indent=1))


if __name__ == '__main__':
    main()
