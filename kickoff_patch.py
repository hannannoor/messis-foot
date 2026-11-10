"""Kickoff patch: graded frames before a half's tagged kickoff are dead ball.

Reads only the Smart Tagging XML (an allowed input). Tag times are seconds from the first
tactical-video frame, so round(seconds * FPS) is a video frame (organisers' DATA.md, "Time base").
"""
from dataclasses import dataclass
from math import isfinite
import xml.etree.ElementTree as ET

FPS = 25
KICKOFF_TEXT = 'KICK OFF (START)'


@dataclass(frozen=True)
class KickoffApplication:
    labels: tuple
    changed: dict   # half -> frames changed
    before: dict    # half -> frames of the half before the derived kickoff
    starts: dict    # half -> derived kickoff frame, or None when the rule did not apply


def _normal(text):
    return ' '.join((text or '').upper().split())


def kickoff_starts(xml_path):
    result = []
    for item in ET.parse(xml_path).iter('instance'):
        if not any(_normal(label.findtext('text')) == KICKOFF_TEXT for label in item.findall('label')):
            continue
        start = float(item.findtext('start'))
        if not isfinite(start):
            raise ValueError('Invalid kickoff tag start')
        result.append(round(start * FPS))
    return tuple(result)


def apply_kickoff_patch(frames, labels, starts):
    if len(frames) != len(labels) or any(v not in ('H', 'A', 'D', 'X') for v in labels):
        raise ValueError('Invalid labels/dimensions')
    result = list(labels)
    changed = {1: 0, 2: 0}
    before = {1: 0, 2: 0}
    used = {1: None, 2: None}
    for half in (1, 2):
        inside = [s for s in starts if 0 <= s < len(frames) and frames[s].period == half]
        if len(inside) != 1:
            continue
        start = inside[0]
        used[half] = start
        for i in range(start):
            if frames[i].period != half:
                continue
            before[half] += 1
            if result[i] != 'D':
                result[i] = 'D'
                changed[half] += 1
    return KickoffApplication(tuple(result), changed, before, used)
