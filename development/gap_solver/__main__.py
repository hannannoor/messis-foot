"""Run from the extracted project folder: python -m gap_solver demo."""
import argparse
import json
from dataclasses import replace
from pathlib import Path
import xml.etree.ElementTree as ET

from .core import Config, Frame, infer, summary
from .io import N_FRAMES, apply_published_dead, load_atd, load_tags, read_evidence, write_outputs


def demo_frames():
    def control(side, n=20):
        return [Frame(ball_x=10, ball_y=10,
                      home_distance=0.5 if side == 'H' else 8,
                      away_distance=0.5 if side == 'A' else 8) for _ in range(n)]

    examples = [
        ('short_occlusion', control('H') + [Frame()] * 10 + control('H')),
        ('tag_supported_occlusion', control('H') + [Frame(tag_team='H')] * 35 + control('H')),
        ('hidden_turnover_ambiguous', control('H') + [Frame()] * 20 + control('A')),
        ('long_gap_ambiguous', control('A') + [Frame()] * 70 + control('A')),
        ('restart_ambiguous', control('H') + [Frame(restart_hint=True)] * 10 + control('H')),
        ('brief_deflection', control('H') + control('A', 2) + control('H')),
        ('confirmed_turnover', control('H') + control('A')),
        ('upstream_dead_detector', control('H') + [Frame(dead_evidence=True)] * 15 + control('H')),
    ]
    frames, scenes = [], []
    for name, clip in examples:
        scenes.append({'name': name, 'start_frame': len(frames),
                       'end_frame_exclusive': len(frames) + len(clip)})
        frames.extend(clip)
        frames.append(Frame(period=0))  # isolate independent synthetic scenarios
    return frames, scenes


def main():
    parser = argparse.ArgumentParser(description='Experimental local possession-gap handler')
    sub = parser.add_subparsers(dest='command', required=True)
    for command in ('demo', 'evidence', 'match'):
        p = sub.add_parser(command)
        p.add_argument('--out', default='outputs/' + command)
        p.add_argument('--config', help='JSON object with Config fields; defaults are provisional')
        if command == 'demo':
            p.add_argument('--full-length', action='store_true',
                           help='pad SYNTHETIC demo to 199319 rows for format validation only')
        elif command == 'evidence':
            p.add_argument('--input', required=True)
        else:
            p.add_argument('--data-dir', required=True,
                           help='local parent of tactical/; never uploads assets')
    args = parser.parse_args()
    try:
        cfg = Config(**(json.loads(Path(args.config).read_text()) if args.config else {}))
        cfg.validate()
        scenes = None
        if args.command == 'demo':
            frames, scenes = demo_frames()
            if args.full_length:
                frames += [Frame(period=0)] * (N_FRAMES - len(frames))
        elif args.command == 'evidence':
            frames = read_evidence(args.input)
        else:
            tactical = Path(args.data_dir) / 'tactical'
            stem = tactical / 'BAR-ATH_tactical'
            frames, names = load_atd(str(stem) + '_atd.xml', str(stem) + '_atd.txt')
            tag_path = Path(str(stem) + '_smart_tagging.xml')
            if tag_path.exists():
                frames = load_tags(tag_path, frames, names, cfg.fps)
            frames = apply_published_dead(frames)
            print('EXPERIMENTAL: published pre-kickoff D context included; general live/dead detector absent.')
        decisions = infer(frames, cfg)
        report = write_outputs(args.out, frames, decisions, cfg)
        if scenes is not None:
            before = summary(frames, infer(frames, replace(cfg, short_bridge_s=0, tagged_bridge_s=0)))
            comparison = {'synthetic_only': True, 'accuracy_measured': False,
                          'before': before, 'after': report, 'scenarios': scenes}
            Path(args.out, 'demo_comparison.json').write_text(json.dumps(comparison, indent=2) + '\n')
            print('Synthetic scenarios only; not a match benchmark or a real recovery estimate.')
            print('Unresolved frames before/after bridging: {} / {}'.format(
                before['labels']['X'], report['labels']['X']))
        print('Active frames: {}; inferred: {}; unresolved: {}'.format(
            report['active_frames'], report['inferred_frames'], report['labels']['X']))
        print('Output: ' + str(Path(args.out).resolve()))
    except (OSError, ValueError, TypeError, KeyError, ET.ParseError) as exc:
        parser.error(str(exc))


if __name__ == '__main__':
    main()
