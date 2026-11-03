"""Local two-camera clock and evidence experiment: python -m gap_solver.multicam demo."""
import argparse
import csv
import json
from collections import Counter, deque
from dataclasses import replace
from math import isfinite
from pathlib import Path
import xml.etree.ElementTree as ET

from .clock_sync import Alignment, ClockRead, ClockTime, align_clocks, dense_clock, validate_timeline
from .core import Frame, infer, summary
from .fusion import Scene, fuse_vote, verify_geometry
from .io import N_FRAMES, _number, apply_published_dead, load_atd, load_tags, write_outputs


def resolve_source_prefix(root, source, source_dir=None):
    """Use existing export folders; never copy or rename match assets."""
    folders = ([Path(source_dir)] if source_dir is not None else
               [Path(root)/source, Path(root)/(source+' cam')])
    prefixes = [folder/('BAR-ATH_'+source) for folder in folders]
    suffixes = ('_atd.xml', '_atd.txt', '_homography.csv')
    complete = [prefix for prefix in prefixes
                if all(Path(str(prefix)+suffix).is_file() for suffix in suffixes)]
    if len(complete) > 1:
        raise ValueError('Multiple {} exports found; choose one with --{}-dir'.format(source, source))
    if not complete:
        missing = [str(prefix)+suffix for prefix in prefixes for suffix in suffixes
                   if not Path(str(prefix)+suffix).is_file()]
        raise ValueError('Missing {} export files: {}'.format(source, '; '.join(missing)))
    return complete[0]


def write_dense_clock(path, clocks):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.writer(handle, lineterminator='\n')
        writer.writerow(['frame', 'half', 'match_seconds', 'uncertainty_s', 'segment'])
        for frame, clock in enumerate(clocks):
            writer.writerow([frame, clock.half, clock.seconds, clock.uncertainty_s, clock.segment]
                            if clock else [frame, '', '', '', ''])


def read_dense_clock(path):
    clocks = []
    with open(path, newline='', encoding='utf-8-sig') as handle:
        for i, row in enumerate(csv.DictReader(handle)):
            if int(row['frame']) != i:
                raise ValueError('clock CSV must contain consecutive 0-based original frame IDs')
            if row['match_seconds'] == '':
                clocks.append(None)
            else:
                clock = ClockTime(float(row['match_seconds']), float(row['uncertainty_s']),
                                  int(row['half']), int(row['segment']))
                if (clock.half not in (1, 2) or not isfinite(clock.seconds) or clock.seconds < 0
                        or not isfinite(clock.uncertainty_s) or clock.uncertainty_s < 0):
                    raise ValueError('invalid clock CSV value')
                clocks.append(clock)
    if not clocks:
        raise ValueError('clock CSV empty')
    validate_timeline(clocks)
    return clocks


def write_alignment(path, mapping, tactical_clock):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.writer(handle, lineterminator='\n')
        writer.writerow(['tactical_frame', 'broadcast_frame', 'half', 'uncertainty_s', 'status'])
        for i, (link, clock) in enumerate(zip(mapping, tactical_clock)):
            writer.writerow([i, link.broadcast_frame if link.broadcast_frame is not None else '',
                             clock.half if clock else 0,
                             link.uncertainty_s if link.uncertainty_s is not None else '', link.status])


def read_alignment(path, n_tactical, n_broadcast):
    mapping, periods = [], [0] * n_broadcast
    previous_target, reuse = -1, Counter()
    recent = deque()
    with open(path, newline='', encoding='utf-8-sig') as handle:
        for i, row in enumerate(csv.DictReader(handle)):
            if int(row['tactical_frame']) != i:
                raise ValueError('alignment must preserve tactical frame index')
            frame = int(row['broadcast_frame']) if row['broadcast_frame'] else None
            uncertainty = float(row['uncertainty_s']) if row['uncertainty_s'] else None
            half = int(row['half'])
            if frame is not None:
                if (not 0 <= frame < n_broadcast or half not in (1, 2) or uncertainty is None
                        or not isfinite(uncertainty) or uncertainty < 0):
                    raise ValueError('invalid alignment target')
                if periods[frame] not in (0, half):
                    raise ValueError('one broadcast frame mapped into different halves')
                reuse[frame] += 1
                # At 25 fps in both exports, occasional rounding repeats are valid.
                if frame < previous_target or reuse[frame] > 2:
                    raise ValueError('broadcast mapping goes backwards or collapses time')
                recent.append((i, frame))
                while recent and i - recent[0][0] > 25:
                    recent.popleft()
                if recent and i - recent[0][0] >= 20:
                    rate = (frame - recent[0][1]) / (i - recent[0][0])
                    if rate < .55:
                        raise ValueError('broadcast mapping has sustained time collapse')
                previous_target = frame
                periods[frame] = half
            mapping.append(Alignment(frame, uncertainty, row['status']))
    if len(mapping) != n_tactical:
        raise ValueError('alignment row count differs from tactical recording')
    return mapping, periods


def load_scenes(meta_path, raw_path, homography_path, n_frames):
    root = ET.parse(meta_path).getroot()
    teams = [t.get('id') for t in root.iter('Team')]
    slots = [p.get('teamId') for p in root.iter('Player')]
    if len(teams) != 2 or not slots or any(t not in teams for t in slots):
        raise ValueError('invalid tracking metadata for scene comparison')
    transforms = []
    with open(homography_path, newline='', encoding='utf-8-sig') as handle:
        for i, row in enumerate(csv.DictReader(handle)):
            if int(row['frame']) != i:
                raise ValueError('homography frame sequence differs from original recording')
            matrix = [_number(row['h'+str(a)+str(b)]) for a in range(3) for b in range(3)]
            valid = row['valid'].strip() == '1' and all(v is not None for v in matrix)
            if valid:
                a,b,c,d,e,f,g,h,j = matrix
                determinant = a*(e*j-f*h)-b*(d*j-f*g)+c*(d*h-e*g)
                scale = max(abs(v) for v in matrix)
                valid = scale > 0 and abs(determinant) > 1e-12 * scale**3
            error = _number(row['reprojection_error'])
            transforms.append((valid, error if error is not None else float('inf')))
    if len(transforms) != n_frames:
        raise ValueError('homography frame count differs from tracking')
    scenes = []
    with open(raw_path, encoding='utf-8-sig') as handle:
        for i, line in enumerate(handle):
            parts = line.strip().split(':')
            if len(parts) != 3 or int(parts[0]) != i + 1 or i >= n_frames:
                raise ValueError('scene tracking counter mismatch')
            players = parts[1].split(';')
            if len(players) != len(slots):
                raise ValueError('scene player slot count mismatch')
            positions = [[], []]
            for slot, player in enumerate(players):
                xyz = player.split(',')
                x, y = _number(xyz[0]), _number(xyz[1])
                if x is not None and y is not None:
                    positions[teams.index(slots[slot])].append((x * 105.3, y * 68))
            ball = parts[2].split(',')
            x, y = _number(ball[0]), _number(ball[1])
            valid, error = transforms[i]
            scenes.append(Scene(tuple(positions[0]), tuple(positions[1]),
                                (x*105.3, y*68) if x is not None and y is not None else None,
                                valid, error))
    if len(scenes) != n_frames:
        raise ValueError('scene count differs from video')
    return scenes


def ensemble(frames, broadcast_frames, scenes, broadcast_scenes, mapping):
    if (len(frames) != len(mapping) or len(frames) != len(scenes)
            or len(broadcast_frames) != len(broadcast_scenes)):
        raise ValueError('ensemble inputs must preserve original camera dimensions')
    # Shared match context can constrain either camera; it is not new visual evidence.
    shared = list(broadcast_frames)
    for i, link in enumerate(mapping):
        j = link.broadcast_frame
        if frames[i].period == 0 or j is None or link.status != 'clock_candidate':
            continue
        if not 0 <= j < len(shared):
            raise ValueError('broadcast candidate outside original frame range')
        f, b = frames[i], shared[j]
        if f.period == b.period and (f.restart_hint or f.dead_evidence):
            shared[j] = replace(b, restart_hint=b.restart_hint or f.restart_hint,
                                dead_evidence=b.dead_evidence or f.dead_evidence,
                                dead_source=f.dead_source if f.dead_evidence and f.dead_source else b.dead_source)
    primary, secondary = infer(frames), infer(shared)
    decisions, rows = list(primary), []
    verified_reasons, skip_reasons = Counter(), Counter()
    funnel = dict.fromkeys(('candidates_with_missing_tactical_ball', 'unresolved_missing_ball_candidates',
                            'broadcast_ball_observed', 'broadcast_direct_control', 'geometry_verified',
                            'broadcast_weight_sufficient', 'rescued'), 0)

    def record(i, j, status, tw, bw, reason, quality=None):
        f, link = frames[i], mapping[i]
        rows.append((i, j if j is not None else '', status, tw, bw, reason,
                     int(f.ball_observed), int(shared[j].ball_observed) if j is not None else '',
                     int(f.restart_hint), int(f.dead_evidence),
                     link.uncertainty_s if link.uncertainty_s is not None else '',
                     quality if quality is not None else '', primary[i].label,
                     secondary[j].label if j is not None else '', decisions[i].label))

    for i, link in enumerate(mapping):
        if (frames[i].period == 0 or link.broadcast_frame is None or link.status != 'clock_candidate'):
            reason = 'ungraded' if frames[i].period == 0 else link.status
            skip_reasons[reason] += 1
            record(i, None, 'no_verified_clock_candidate', 0, 0, reason)
            continue
        j = link.broadcast_frame
        if frames[i].period != shared[j].period:
            skip_reasons['half_mismatch'] += 1
            record(i, j, 'half_mismatch', 0, 0, 'half_mismatch')
            continue
        verification = verify_geometry(scenes[i], broadcast_scenes[j])
        vote = fuse_vote(primary[i], secondary[j], verification, link.uncertainty_s)
        decisions[i] = vote.decision
        reason = verification.reason
        if verification.accepted and (link.uncertainty_s is None or not isfinite(link.uncertainty_s)
                                      or not 0 <= link.uncertainty_s <= .25):
            reason = 'timing_uncertain'
        verified_reasons[reason] += 1
        record(i, j, vote.status, vote.tactical_weight, vote.broadcast_weight, reason, verification.quality)
        if not frames[i].ball_observed:
            funnel['candidates_with_missing_tactical_ball'] += 1
            if primary[i].label == 'X':
                funnel['unresolved_missing_ball_candidates'] += 1
                if shared[j].ball_observed:
                    funnel['broadcast_ball_observed'] += 1
                    if secondary[j].label in ('H', 'A') and secondary[j].evidence_level == 'direct_heuristic':
                        funnel['broadcast_direct_control'] += 1
                        if verification.accepted:
                            funnel['geometry_verified'] += 1
                            if vote.broadcast_weight >= .3:
                                funnel['broadcast_weight_sufficient'] += 1
                                funnel['rescued'] += vote.status == 'broadcast_rescue'
    statuses = Counter(r[2] for r in rows)
    report = {'accuracy_measured': False, 'before': summary(frames, primary),
              'after': summary(frames, decisions), 'fusion_status_counts': dict(statuses),
              'broadcast_rescued_frames': statuses['broadcast_rescue'],
              'weak_tactical_replaced_frames': statuses['broadcast_overrides_inferred'],
              'camera_comparison_frames': sum(verified_reasons.values()),
              'not_compared_frames': sum(skip_reasons.values()),
              'verification_reason_counts': dict(verified_reasons),
              'comparison_skip_reason_counts': dict(skip_reasons),
              'alignment_status_counts': dict(Counter(link.status for link in mapping)),
              'missing_ball_funnel': funnel,
              'shared_restart_context': True,
              'replay_detector_included': False,
              'general_live_dead_detector_included': False,
              'scope_note': 'Unmapped frames are not failed comparisons. Alignment alone cannot distinguish unscanned frames from OCR failure.',
              'warning': 'Heuristic quality gates do not prove alignment, live footage or accuracy.'}
    return decisions, rows, report


def save_ensemble(directory, frames, decisions, rows, report, audit_stages=None):
    write_outputs(directory, frames, decisions, audit_stages=audit_stages)
    directory = Path(directory)
    with (directory / 'fusion_diagnostics.csv').open('w', newline='', encoding='utf-8') as handle:
        writer = csv.writer(handle, lineterminator='\n')
        writer.writerow(['tactical_frame', 'broadcast_frame', 'fusion_status',
                         'tactical_weight', 'broadcast_weight', 'verification',
                         'tactical_ball_observed', 'broadcast_ball_observed', 'restart_phase_hint',
                         'dead_evidence', 'timing_uncertainty_s', 'geometry_quality',
                         'tactical_label', 'broadcast_label', 'final_label'])
        writer.writerows(rows)
    (directory / 'ensemble_report.json').write_text(json.dumps(report, indent=2) + '\n')


def _demo(directory):
    frames = [Frame(ball_x=40, ball_y=30, home_distance=.5, away_distance=8)] * 200
    for start in (60, 140):
        frames[start:start+20] = [Frame()] * 20
    broadcast = [Frame(period=0)] * 37 + [Frame(ball_x=40, ball_y=30,
                                              home_distance=.5, away_distance=8)] * 200
    def reads(offset=0):
        return [ClockRead(i+offset, '19:{:02d}'.format(i//25), .95, 1) for i in range(0, 200, 5)]
    tc, bc = dense_clock(reads(), 200), dense_clock(reads(37), 237)
    mapping = align_clocks(tc, bc)
    scene = Scene(((10,10), (20,15), (30,20), (40,25)),
                  ((12,40), (22,45), (32,50), (42,55)), (40,30), True, .2)
    scenes = [replace(scene, ball=None) if not f.ball_observed else scene for f in frames]
    broadcast_scenes = [scene] * 237
    for i in range(177, 197):  # second synthetic gap has an unreliable broadcast transform
        broadcast_scenes[i] = replace(scene, homography_valid=False)
    decisions, rows, report = ensemble(frames, broadcast, scenes, broadcast_scenes, mapping)
    report['synthetic_only'] = True
    save_ensemble(directory, frames, decisions, rows, report)
    write_dense_clock(Path(directory) / 'tactical_clock.csv', tc)
    write_dense_clock(Path(directory) / 'broadcast_clock.csv', bc)
    write_alignment(Path(directory) / 'alignment.csv', mapping, tc)
    print('SYNTHETIC camera experiment only; no match accuracy measured.')
    print('Unresolved tactical frames before/after: {} / {}'.format(
        report['before']['labels']['X'], report['after']['labels']['X']))
    print('Verified broadcast rescues: ' + str(report['broadcast_rescued_frames']))


def main():
    parser = argparse.ArgumentParser(description='Local clock alignment and gated two-camera fusion')
    sub = parser.add_subparsers(dest='command', required=True)
    demo = sub.add_parser('demo')
    demo.add_argument('--out', default='outputs/two-camera-demo')
    check = sub.add_parser('ocr-check', help='test one local clock image without rescanning video')
    check.add_argument('--image', required=True)
    check.add_argument('--source', choices=('tactical', 'broadcast'), required=True)
    check.add_argument('--ffmpeg', default='ffmpeg')
    check.add_argument('--tesseract', default='tesseract')
    clock = sub.add_parser('clock')
    clock.add_argument('--video', required=True)
    clock.add_argument('--source', choices=('tactical', 'broadcast'), required=True)
    clock.add_argument('--half', type=int, choices=(1,2), required=True)
    clock.add_argument('--start-frame', type=int, required=True)
    clock.add_argument('--end-frame', type=int, required=True, help='exclusive; choose a clip within the selected half')
    clock.add_argument('--stride', type=int, default=5)
    clock.add_argument('--min-confidence', type=float, default=.7,
                       help='OCR score cutoff; 0.5 is an explicit trial setting, not measured accuracy')
    crop_options=clock.add_mutually_exclusive_group()
    crop_options.add_argument('--roi', help='normalised x,y,width,height; overrides provisional crop preset')
    crop_options.add_argument('--roi-file', help='reuse a saved local clock-box JSON file')
    crop_options.add_argument('--select-roi', action='store_true', help='draw the clock box locally before OCR')
    clock.add_argument('--preview', help='save first enlarged clock crop locally for inspection')
    clock.add_argument('--ffmpeg', default='ffmpeg')
    clock.add_argument('--ffprobe', default='ffprobe')
    clock.add_argument('--tesseract', default='tesseract')
    clock.add_argument('--out', required=True, help='dense clock CSV; original video frame count')
    align = sub.add_parser('align')
    align.add_argument('--tactical-clock', required=True)
    align.add_argument('--broadcast-clock', required=True)
    align.add_argument('--max-uncertainty', type=float, default=.25)
    align.add_argument('--out', default='outputs/alignment.csv')
    fuse = sub.add_parser('fuse')
    fuse.add_argument('--data-dir', default='.', help='parent of tactical/ and broadcast/, or tactical cam/ and broadcast cam/')
    fuse.add_argument('--tactical-dir', help='explicit folder containing BAR-ATH_tactical tracking and homography')
    fuse.add_argument('--broadcast-dir', help='explicit folder containing BAR-ATH_broadcast tracking and homography')
    fuse.add_argument('--alignment', required=True)
    fuse.add_argument('--audit-baseline', action='store_true',
                      help='isolate legacy restart, restart repair, published dead context and fusion using cached alignment')
    fuse.add_argument('--out', default='outputs/ensemble')
    args = parser.parse_args()
    try:
        if args.command == 'demo':
            _demo(args.out)
        elif args.command == 'ocr-check':
            from .clock_ocr import check_clock_image
            raw, processed = check_clock_image(args.image, args.source, args.ffmpeg, args.tesseract)
            print('Original: clock={!r}; Tesseract confidence={:.3f}'.format(*raw))
            print('Preprocessed: clock={!r}; Tesseract confidence={:.3f}'.format(*processed))
            print('Confidence is an OCR score, not measured correctness. Clock default cutoff is 0.7; --min-confidence overrides it for a trial.')
        elif args.command == 'clock':
            from .clock_ocr import extract_clock, ocr_summary
            if not 0 <= args.min_confidence <= 1:
                raise ValueError('--min-confidence must be between 0 and 1')
            roi = tuple(float(v) for v in args.roi.split(',')) if args.roi else None
            if roi is not None and len(roi) != 4:
                raise ValueError('ROI needs x,y,width,height')
            if args.roi_file:
                from .roi import load_roi
                roi=load_roi(args.roi_file,args.source)
            if args.select_roi:
                from .roi import choose_roi
                roi=choose_roi(args.video,args.start_frame,args.source,
                               str(args.out)+'.roi.json',args.ffmpeg,args.ffprobe)
            reads, count, fps = extract_clock(args.video, args.source, args.half,
                args.start_frame, args.end_frame, args.stride, roi,
                args.ffmpeg, args.ffprobe, args.tesseract, args.preview,
                min_confidence=args.min_confidence)
            timeline = dense_clock(reads, count, fps, min_confidence=args.min_confidence)
            write_dense_clock(args.out, timeline)
            with Path(str(args.out) + '.reads.csv').open('w', newline='', encoding='utf-8') as handle:
                writer = csv.writer(handle, lineterminator='\n')
                writer.writerow(['frame', 'half', 'clock_text', 'ocr_confidence', 'ocr_method', 'ocr_attempts'])
                writer.writerows((r.frame, r.half, r.text, r.confidence, r.method, r.attempts) for r in reads)
            print('OCR samples: {}; frames with bounded clock estimate: {}'.format(
                len(reads), sum(c is not None for c in timeline)))
            stats=ocr_summary(reads,args.min_confidence)
            print('Clock-shaped readings: {}; accepted at cutoff {:.3f}: {}; unreadable: {}'.format(
                stats['parsed'],stats['cutoff'],stats['accepted_by_score'],stats['unreadable']))
            print('OCR retries: {}; recovered at cutoff: {}; conflicting retries: {}'.format(
                stats['retried'],stats['recovered'],stats['conflicts']))
            if stats['p01_all'] is not None:
                print('Confidence across ALL crops (unreadable=0): p01={:.3f}; median={:.3f}; minimum={:.3f}'.format(
                    stats['p01_all'],stats['median_all'],stats['minimum_all']))
                print('First-percentile confidence > 0.5: '+('YES' if stats['p01_above_half'] else 'NO'))
            print('Clock matching alone does not verify live footage or possession.')
        elif args.command == 'align':
            tactical = read_dense_clock(args.tactical_clock)
            broadcast = read_dense_clock(args.broadcast_clock)
            mapping = align_clocks(tactical, broadcast, args.max_uncertainty)
            write_alignment(args.out, mapping, tactical)
            print(json.dumps(dict(Counter(m.status for m in mapping)), indent=2))
        else:
            root = Path(args.data_dir)
            t = str(resolve_source_prefix(root, 'tactical', args.tactical_dir))
            b = str(resolve_source_prefix(root, 'broadcast', args.broadcast_dir))
            mapping, periods = read_alignment(args.alignment, N_FRAMES, 164488)
            candidates = sum(link.broadcast_frame is not None and link.status == 'clock_candidate'
                             for link in mapping)
            if not candidates:
                raise ValueError('No clock candidates in alignment; select overlapping match-clock clips first.')
            print('Clock candidates: {}; loading tactical tracking...'.format(candidates), flush=True)
            frames, teams = load_atd(t+'_atd.xml', t+'_atd.txt')
            tagging = Path(t+'_smart_tagging.xml')
            if tagging.exists():
                frames = load_tags(tagging, frames, teams)
            raw_frames = frames
            frames = apply_published_dead(raw_frames)
            print('Loading broadcast tracking...', flush=True)
            other, other_teams = load_atd(b+'_atd.xml', b+'_atd.txt', n_frames=164488,
                                         blocks=[(1, 0, 164487)])
            other = [replace(f, period=p) for f, p in zip(other, periods)]
            print('Loading both camera scenes and homographies...', flush=True)
            scenes = load_scenes(t+'_atd.xml', t+'_atd.txt', t+'_homography.csv', N_FRAMES)
            other_scenes = load_scenes(b+'_atd.xml', b+'_atd.txt', b+'_homography.csv', 164488)
            def norm(name):
                return name.lower().replace('fc ', '').replace('atletic', 'athletic').strip()
            if tuple(map(norm, teams)) == tuple(reversed(tuple(map(norm, other_teams)))):
                other = [replace(f, home_distance=f.away_distance, away_distance=f.home_distance) for f in other]
                other_scenes = [replace(s, home=s.away, away=s.home) for s in other_scenes]
            elif tuple(map(norm, teams)) != tuple(map(norm, other_teams)):
                raise ValueError('Team identities do not match across exports')
            print('Comparing camera evidence and writing results...', flush=True)
            decisions, rows, report = ensemble(frames, other, scenes, other_scenes, mapping)
            audit_stages = None
            if args.audit_baseline:
                from .audit import build_baseline_audit
                comparison, audit_stages = build_baseline_audit(raw_frames, frames, decisions)
                report['controlled_comparison'] = comparison
            save_ensemble(args.out, frames, decisions, rows, report, audit_stages=audit_stages)
            print('EXPERIMENTAL: live/dead detector still absent; no match accuracy measured.')
            print('Unresolved tactical frames before/after: {} / {}'.format(
                report['before']['labels']['X'], report['after']['labels']['X']))
            print('Broadcast-rescued frames: {}'.format(report['broadcast_rescued_frames']))
            print('Camera comparison frames: {}'.format(report['camera_comparison_frames']))
            print('Missing-ball opportunity funnel: '+json.dumps(report['missing_ball_funnel']))
            if args.audit_baseline:
                print('Controlled baseline comparison (coverage and behavior, not measured accuracy):')
                for name, stage in report['controlled_comparison']['stages'].items():
                    print('  {}: H={H}; A={A}; D={D}; X={X}'.format(name, **stage['labels']))
                for name, change in report['controlled_comparison']['comparisons'].items():
                    print('  {}: raw changes={}; scorer-expanded changes={}'.format(
                        name, change['raw_label_changes'], change['scorer_expanded_label_changes']))
            print('Detailed verification reasons: '+json.dumps(report['verification_reason_counts']))
            print(json.dumps(report['fusion_status_counts'], indent=2))
    except (OSError, ValueError, TypeError, KeyError, IndexError, ET.ParseError) as exc:
        parser.error(str(exc))


if __name__ == '__main__':
    main()
