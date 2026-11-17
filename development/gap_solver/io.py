"""Local adapters. Match data must remain on the participant's machine."""
import csv
import json
from dataclasses import asdict, replace
from math import hypot, isfinite
from pathlib import Path
import xml.etree.ElementTree as ET

from .core import Config, Frame, interpolate_ball, summary, unresolved_intervals

N_FRAMES = 199319
BLOCKS = [(1, 11185, 90651), (2, 110808, 190197)]  # inclusive, published boundaries
PUBLISHED_PRE_KICKOFF = (110808, 113742)  # half-open; official FAQ: all 2934 frames are D


def apply_published_dead(frames):
    """Apply official reference-export context, never to another recording/game."""
    first, stop = PUBLISHED_PRE_KICKOFF
    if len(frames) != N_FRAMES or any(f.period != 2 for f in frames[first:stop]):
        raise ValueError('published context requires the reference tactical dimensions and half-2 block')
    result = list(frames)
    for i in range(first, stop):
        result[i] = replace(frames[i], dead_evidence=True, dead_source='published_pre_kickoff')
    return result


def _number(value):
    if value is None or str(value).strip().lower() in ('', 'nan', 'none'):
        return None
    n = float(value)
    if not isfinite(n):
        raise ValueError('infinite input is invalid')
    return n


def _bool(value):
    text = str(value).strip().lower()
    if text in ('', '0', 'false', 'none'):
        return False
    if text in ('1', 'true'):
        return True
    raise ValueError('boolean must be true/false or 1/0')


def load_atd(meta_path, raw_path, n_frames=N_FRAMES, blocks=None):
    """Strict 1-based ATD -> 0-based evidence, no legacy IdFrame offsets."""
    blocks = BLOCKS if blocks is None else blocks
    root = ET.parse(meta_path).getroot()
    teams = list(root.iter('Team'))
    if len(teams) != 2 or len({t.get('id') for t in teams}) != 2:
        raise ValueError('expected two distinct teams in metadata')
    ids = [t.get('id') for t in teams]
    names = tuple(t.findtext('Name') or '' for t in teams)
    slots = [p.get('teamId') for p in root.iter('Player')]
    if not slots or any(t not in ids for t in slots):
        raise ValueError('missing or invalid team membership')
    periods = [0] * n_frames
    for period, first, last in blocks:
        for i in range(max(0, first), min(n_frames, last + 1)):
            periods[i] = period
    frames = []
    with open(raw_path, encoding='utf-8-sig') as handle:
        for i, line in enumerate(handle):
            parts = line.strip().split(':')
            if len(parts) != 3 or int(parts[0]) != i + 1 or i >= n_frames:
                raise ValueError('ATD must have ordered, contiguous frame IDs 1..N')
            players = parts[1].split(';')
            if len(players) != len(slots):
                raise ValueError('player slot count differs from metadata at frame ' + str(i))
            ball = parts[2].split(',')
            if len(ball) != 3:
                raise ValueError('expected ball x,y,speed')
            bx, by = _number(ball[0]), _number(ball[1])
            if bx is None or by is None:
                frames.append(Frame(period=periods[i]))
                continue
            bx, by = bx * 105.3, by * 68.0
            nearest = [None, None]
            for slot, player in enumerate(players):
                xyz = player.split(',')
                if len(xyz) != 3:
                    raise ValueError('expected player x,y,speed')
                x, y = _number(xyz[0]), _number(xyz[1])
                if x is None or y is None:
                    continue
                distance = hypot(x * 105.3 - bx, y * 68.0 - by)
                side = ids.index(slots[slot])
                if nearest[side] is None or distance < nearest[side]:
                    nearest[side] = distance
            frames.append(Frame(period=periods[i], ball_x=bx, ball_y=by,
                                home_distance=nearest[0], away_distance=nearest[1]))
    if len(frames) != n_frames:
        raise ValueError('expected {} records; got {}'.format(n_frames, len(frames)))
    return frames, names


def load_tags(path, frames, team_names, fps=25):
    """Soft possession-oriented votes. Set-piece intervals only block bridging."""
    def norm(s):
        return ' '.join((s or '').lower().split())

    mapping = {norm(team_names[0]): 'H', norm(team_names[1]): 'A'}
    # Documented provider spelling variations, not player/match annotations.
    for name, side in zip(team_names, ('H', 'A')):
        if 'barcelona' in norm(name):
            mapping.update({'barcelona': side, 'fc barcelona': side})
        if 'atletic' in norm(name) or 'athletic' in norm(name):
            mapping.update({'atletic club': side, 'athletic club': side})
    attacking = {'build up', 'progression', 'creating chances', 'attacking transition',
                 'long ball', 'ball in final third', 'ball in the box', 'players in the box'}
    defending = {'defending in attacking third', 'defending in middle third',
                 'defending in defensive third', 'defensive transition'}
    votes = [set() for _ in frames]
    restarts = [False] * len(frames)
    for event in ET.parse(path).iter('instance'):
        code = norm(event.findtext('code'))
        tags = {norm(l.findtext('group')): norm(l.findtext('text')) for l in event.findall('label')}
        side = mapping.get(tags.get('team'))
        start_s, end_s = float(event.findtext('start')), float(event.findtext('end'))
        if not isfinite(start_s) or not isfinite(end_s) or end_s < start_s:
            raise ValueError('invalid tagging interval')
        start, end = max(0, round(start_s * fps)), min(len(frames), round(end_s * fps))
        if code in defending and side:
            side = 'A' if side == 'H' else 'H'
        if code not in attacking | defending:
            side = None
        for i in range(start, end):
            if side:
                votes[i].add(side)
            if code == 'set pieces':
                restarts[i] = True
    return [replace(f, tag_team=next(iter(v)) if len(v) == 1 else ('CONFLICT' if v else ''),
                    restart_hint=f.restart_hint or restarts[i])
            for i, (f, v) in enumerate(zip(frames, votes))]


def read_evidence(path):
    frames = []
    with open(path, newline='', encoding='utf-8-sig') as handle:
        for i, row in enumerate(csv.DictReader(handle)):
            if int(row['frame']) != i:
                raise ValueError('evidence frame IDs must be ordered 0..N-1')
            period = int(row['period'])
            tag = row.get('tag_team', '').strip().upper()
            if period not in (0, 1, 2) or tag not in ('', 'H', 'A', 'CONFLICT'):
                raise ValueError('invalid period or tag_team')
            frames.append(Frame(period=period,
                                ball_x=_number(row.get('ball_x_m')),
                                ball_y=_number(row.get('ball_y_m')),
                                home_distance=_number(row.get('home_distance_m')),
                                away_distance=_number(row.get('away_distance_m')),
                                tag_team=tag, restart_hint=_bool(row.get('restart_hint')),
                                dead_evidence=_bool(row.get('dead_evidence'))))
    if not frames:
        raise ValueError('evidence file is empty')
    return frames


def write_outputs(directory, frames, decisions, cfg=Config(), audit_stages=None):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    if len(frames) != len(decisions):
        raise ValueError('frame/decision length mismatch')
    audit_stages = audit_stages or {}
    if audit_stages:
        from .audit import scorer_expanded_labels
        expanded = {name: scorer_expanded_labels(frames, labels) for name, labels in audit_stages.items()}
        final_expanded = scorer_expanded_labels(frames, decisions)
    xy = interpolate_ball(frames, cfg)
    with (directory / 'submission.csv').open('w', newline='', encoding='utf-8') as handle:
        writer = csv.writer(handle, lineterminator='\n')
        writer.writerow(['frame', 'label'])
        writer.writerows((i, d.label) for i, d in enumerate(decisions))
    with (directory / 'diagnostics.csv').open('w', newline='', encoding='utf-8') as handle:
        writer = csv.writer(handle, lineterminator='\n')
        writer.writerow(['frame', 'period', 'label', 'reason', 'evidence_level', 'ball_observed',
                         'estimated_ball_x_m', 'estimated_ball_y_m'] +
                        [column for name in audit_stages for column in (name+'_label', 'scorer_'+name+'_label')] +
                        (['scorer_final_label'] if audit_stages else []))
        for i, (f, d, estimate) in enumerate(zip(frames, decisions, xy)):
            writer.writerow([i, f.period, d.label, d.reason, d.evidence_level,
                             int(f.ball_observed), *(estimate or ('', ''))] +
                            [value for name, labels in audit_stages.items() for value in (labels[i].label, expanded[name][i])] +
                            ([final_expanded[i]] if audit_stages else []))
    report = summary(frames, decisions)
    report['config'] = asdict(cfg)
    report['live_dead_classifier_included'] = False
    for name, obj in [('report.json', report),
                      ('unresolved_intervals.json', unresolved_intervals(frames, decisions))]:
        (directory / name).write_text(json.dumps(obj, indent=2) + '\n', encoding='utf-8')
    return report
