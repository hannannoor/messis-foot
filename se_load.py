"""Strong-emissions experiment: load any external match as (frames, reference) without bindings ceremony.

External data only. The provided challenge match is never loaded here.
"""
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parent
PRIVATE = WORKSPACE / 'strong-emissions-reference'

SKILLCORNER = ('1874553', '1886347', '2007448', '2007721', '2010085', '2011166', '2013725', '2015213', '2016236',
               '2017461')
DFL = ('J03WMX', 'J03WN1', 'J03WOH', 'J03WOY', 'J03WPY', 'J03WQQ', 'J03WR9')
ALL = tuple('skillcorner-' + m for m in SKILLCORNER) + tuple('dfl-' + m for m in DFL) + ('wcsf-used-match',)

# Fixed before any modelling (design doc 2026-11-14-strong-emissions).
HOLDOUT = ('wcsf-used-match', 'dfl-J03WN1', 'skillcorner-2013725', 'skillcorner-2016236', 'skillcorner-2017461')
# Release tree was fitted on these four, so release scores on them are in-sample.
RELEASE_TRAIN = ('dfl-J03WOH', 'dfl-J03WOY', 'dfl-J03WPY', 'dfl-J03WMX')
PRIMARY = tuple('skillcorner-' + m for m in SKILLCORNER) + ('dfl-J03WR9', 'dfl-J03WN1', 'wcsf-used-match')


def provider(cid):
    return cid.split('-', 1)[0]


METRICA = ('Sample_Game_1', 'Sample_Game_2', 'Sample_Game_3')
METRICA_SOURCE = WORKSPACE / 'gap-liveness-private' / '2026-11-10' / 'metrica' / 'source'


def load(cid, reference='event'):
    """reference: Metrica only. 'event' = round-9 event-derived labels; 'ball' = round-10 ball-flag dead ball
    (metrica_ball_reference). Other cohorts ignore it."""
    cohort, match = cid.split('-', 1)
    if cohort == 'metrica':   # round 9: public Metrica samples, event-derived reference (metrica_event_reference)
        from metrica_sample_adapter import load_game, load_events
        from metrica_event_reference import build_reference
        loaded, team_map = load_game(METRICA_SOURCE, match)
        frames = list(loaded) if not isinstance(loaded, tuple) else list(loaded[0])
        if isinstance(loaded, tuple):
            team_map = loaded[1]
        events, periods = load_events(METRICA_SOURCE, match, team_map), [f.period for f in frames]
        if reference == 'ball':
            from metrica_ball_reference import build_ball_reference
            labels, _ = build_ball_reference(events, periods, [bool(f.ball_observed) for f in frames])
        elif reference == 'event':
            labels, _ = build_reference(events, periods)
        else:
            raise ValueError('Unknown Metrica reference')
        return frames, np.asarray(['HADX'.index(v) for v in labels], dtype=np.uint8)
    if cohort == 'wcsf':
        import memory_ablation_protocol as p
        binding = p.input_bindings(ROOT)['evaluation'][cid]
        loaded = p.legacy._load_case(cid, binding)
        frames = list(loaded['frames'])
        ref = loaded['reference']
        ref = ref() if callable(ref) else ref
        return frames, np.asarray(ref, dtype=np.uint8)
    if cohort == 'skillcorner':
        from gap_solver.skillcorner import load_motion_cache
        data = load_motion_cache(WORKSPACE / 'independent-reference' / 'cache' / (match + '-detected'))
        frames = data.frames()
    else:
        from gap_solver.external import load_cache
        from gap_solver.dfl_motion import load_dfl_motion
        raw = WORKSPACE / 'external-reference' / 'raw'
        data = load_cache(WORKSPACE / 'external-reference' / 'cache' / match)
        meta = next(raw.glob('DFL_02_01_matchinformation_*' + match + '.xml'))
        pos = next(raw.glob('DFL_04_03_positions_raw_observed_*' + match + '.xml'))
        frames = load_dfl_motion(meta, pos, data)
    if str(data.match_id) not in (match, 'DFL-MAT-' + match):
        raise ValueError('match identity differs')
    return list(frames), np.asarray(data.reference, dtype=np.uint8)
