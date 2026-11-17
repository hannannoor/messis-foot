"""Round 11: SkillCorner dead-ball reference from the provider's own stoppage events, and dead-ball scoring on it.

    python se_sc_dead.py ref                       -> sc_deadref/<cid>.npy (0 H, 1 A, 2 D, 3 X) + aggregate counts
    python se_sc_dead.py score <out> [procs]       -> scores2/scdead_<out>.json and a table

Reference. SkillCorner's dynamic events mark restarts: an on-ball event (player_possession / on_ball_engagement) with
`game_interruption_before` set (throw-in, free kick, goal kick, corner, kick-off after a goal) starts play again. The
stoppage before it runs from the end of the previous on-ball event in the same half to the start of that event. Those
frames become D; all other frames keep SkillCorner's own H/A/X phase labels. Edges are approximate (the last event
ends before the ball crosses the line), so the reference decides WHICH long gaps are stoppages better than WHERE
exactly they start.

Scoring. Predictions come from models that never trained on the match: v8-recipe CV folds (B8) for the original dev
matches, the v8-recipe models trained on dev only (HB8) for the ten added matches. The holdout matches are not used.
Every variant is the release decoder (switch cost 20, touch and boundary costs) followed by a gap rule variant.
"""
import csv
import json
import sys
from multiprocessing import Pool

import numpy as np

import se_load
from se_data_catalog import ADDITIONAL_SKILLCORNER

OUT = se_load.PRIVATE / 'sc_deadref'
ORIGINAL_EVENTS = se_load.WORKSPACE / 'skillcorner-additional-data' / 'events-original'
DEV_SC = tuple(c for c in se_load.ALL if c.startswith('skillcorner') and c not in se_load.HOLDOUT)
NEW_SC = tuple('skillcorner-' + m for m in ADDITIONAL_SKILLCORNER)
ON_BALL = ('player_possession', 'on_ball_engagement')


def events_path(match):
    if match in ADDITIONAL_SKILLCORNER:
        return se_load.ADDITIONAL_ROOT / 'raw' / match / (match + '_dynamic_events.csv')
    return ORIGINAL_EVENTS / match / (match + '_dynamic_events.csv')


def stoppages(match):
    """[(first native frame, restart native frame, kind)] from the provider's events."""
    with open(events_path(match), newline='', encoding='utf-8-sig') as f:
        ev = [r for r in csv.DictReader(f) if r['event_type'] in ON_BALL]
    ev.sort(key=lambda r: int(r['frame_start']))
    out, last_end, last_per = [], None, None
    for r in ev:
        fs, fe, per = int(r['frame_start']), int(r['frame_end']), r['period']
        if r['game_interruption_before'] and last_end is not None and per == last_per and fs > last_end:
            out.append((last_end, fs, r['game_interruption_before']))
        last_end = max(last_end, fe) if (per == last_per and last_end is not None) else fe
        last_per = per
    return out


def source_frames(cid):
    from gap_solver.skillcorner import load_motion_cache
    match = cid.split('-', 1)[1]
    root = se_load.ADDITIONAL_ROOT if match in ADDITIONAL_SKILLCORNER else se_load.WORKSPACE / 'independent-reference'
    data = load_motion_cache(root / 'cache' / (match + '-detected'))
    return np.asarray(data.source_frames, np.float64), np.asarray(data.reference, np.uint8), np.asarray(data.periods)


def build_ref(cid, margin=0, out_dir=None):
    """margin (native 10 Hz frames): the first `margin` frames of each stoppage become X (unknown) instead of D,
    because the last event ends before the ball actually goes out. For training only; scoring uses margin 0."""
    src, ref, per = source_frames(cid)
    out = ref.copy()
    st = stoppages(cid.split('-', 1)[1])
    dead = np.zeros(len(ref), bool)
    unsure = np.zeros(len(ref), bool)
    for a, b, _ in st:
        dead |= (src >= a + margin) & (src < b)
        unsure |= (src >= a) & (src < min(b, a + margin))
    dead &= per > 0
    out[dead] = 2
    out[unsure & (per > 0)] = 3
    d = OUT if out_dir is None else se_load.PRIVATE / out_dir
    d.mkdir(exist_ok=True)
    np.save(d / (cid + '.npy'), out)
    act = per > 0
    return cid, dict(stoppages=len(st), dead_share=round(float(dead[act].mean()), 3),
                     ha_overwritten=int(((ref < 2) & dead).sum()), x_left=int(((out == 3) & act).sum()))


# ---- scoring ---------------------------------------------------------------------------------------------------
# gap rule variants: (LONG_GAP frames, SPEED_FACTOR, MAX_EXTENSION frames); None = no gap rule
VARIANTS = {'nogap': None, 'v9': (75, 1.0, 250)}
for lg in (25, 50, 75, 125, 250):
    for sf in (0.8, 1.0, 1.25, 1.5, 2.0, 99.0):
        for mx in (0, 250):
            VARIANTS[f'g{lg}s{sf}m{mx}'] = (lg, sf, mx)


TAGS = {'dev': ('B8', ('r8ba', 'r8bb')), 'new': ('HB8', ('H_r8ba', 'H_r8bb'))}   # --dev tag:bnd1,bnd2  --new tag:bnd1,...


def model_tags(cid):
    return TAGS['dev'] if cid in DEV_SC else TAGS['new']


def _init(tags):
    TAGS.update(tags)


def score_one(cid):
    import gap_liveness as gl
    import strong_runtime as rt
    from memory_ablation_metrics import score_variant
    from se_assembly import assemble
    from se_metrica_rescore import ownership_only
    if not hasattr(gl, '_orig_pss'):   # pool workers are reused: keep the real function
        gl._orig_pss = gl.player_speed_statistics
    gl.player_speed_statistics = gl._orig_pss
    frames, _ = se_load.load(cid)
    ref = np.load(OUT / (cid + '.npy'))
    per = np.asarray([f.period for f in frames], np.uint8)
    obs = np.asarray([f.ball_observed for f in frames], bool)
    z = np.load(se_load.PRIVATE / 'cases' / (cid + '.npz'))
    names = [str(s) for s in z['names']]
    tag, btags = model_tags(cid)
    sup = np.load(se_load.PRIVATE / 'preds' / tag / (cid + '.npz'))['sup']
    sup = np.clip(sup, 1e-9, 1) ** 2.0
    sup = np.clip(sup / sup.sum(1, keepdims=True), 1e-6, 1)
    sup /= sup.sum(1, keepdims=True)
    bnd = np.mean([np.load(se_load.PRIVATE / 'preds' / t / (cid + '.npz'))['bnd'] for t in btags], 0)
    st = assemble(frames, sup, (), missing_w=rt.MISSING_W, cost=rt.SWITCH_COST, cost_rows=rt.cost_rows(z['X'], names, bnd))
    control = st['control']
    stats = gl.player_speed_statistics(frames)
    gl.player_speed_statistics = lambda _f: stats   # same frames for every variant
    res = {}

    def score(lab, key):
        lab = np.asarray(['HADX'.index(s) for s in lab], np.uint8) if not isinstance(lab, np.ndarray) else lab
        full = score_variant(ref, lab, per, obs)
        own = score_variant(ref, ownership_only(ref, lab), per, obs)
        res[key] = dict(full=full['metrics']['spell_f1_mean'], own=own['metrics']['spell_f1_mean'],
                        dead_recall=full['dead']['recall'], dead_precision=full['dead']['precision'])

    for key, v in VARIANTS.items():
        if v is None:
            lab = control
        else:
            gl.LONG_GAP, gl.SPEED_FACTOR, gl.MAX_EXTENSION = v
            lab = gl.apply_gap_rule(frames, control).labels
        score(lab, key)
    gl.LONG_GAP, gl.SPEED_FACTOR, gl.MAX_EXTENSION = 75, 1.0, 250
    if tuple(gl.apply_gap_rule(frames, control).labels) != tuple(st['gapko']):
        raise RuntimeError('v9 variant differs from the release gapko stage')
    # bounds: D exactly where the reference says (labels elsewhere from the v9 variant)
    lab = np.asarray(['HADX'.index(s) for s in gl.apply_gap_rule(frames, control).labels], np.uint8)
    lab[ref == 2] = 2
    lab[(ref != 2) & (lab == 2)] = 3
    score(lab, 'oracle_dead')
    return cid, res


if __name__ == '__main__':
    if sys.argv[1] == 'ref':
        with Pool(4) as pool:
            res = dict(pool.map(build_ref, DEV_SC + NEW_SC + tuple(c for c in se_load.HOLDOUT if c.startswith('skillcorner'))))
        (OUT / 'summary.json').write_text(json.dumps(res, indent=1))
        for c, r in res.items():
            print(c, r)
    else:
        args = sys.argv[2:]
        for k in ('dev', 'new'):
            if '--' + k in args:
                i = args.index('--' + k); t, b = args[i + 1].split(':'); TAGS[k] = (t, tuple(b.split(','))); del args[i:i + 2]
        out = args[0]
        sys.argv = [sys.argv[0], 'score'] + args
        cids = [c for c in DEV_SC + NEW_SC
                if all((se_load.PRIVATE / 'preds' / t / (c + '.npz')).exists() for t in (model_tags(c)[0],) + model_tags(c)[1])]
        with Pool(int(sys.argv[3]) if len(sys.argv) > 3 else 3, initializer=_init, initargs=(dict(TAGS),)) as pool:
            res = dict(pool.map(score_one, cids))
        (se_load.PRIVATE / 'scores2' / f'scdead_{out}.json').write_text(json.dumps(res, indent=1))
        keys = list(VARIANTS) + ['oracle_dead']
        rows = []
        for k in keys:
            d = np.array([res[c][k]['full'] - res[c]['v9']['full'] for c in cids])
            rows.append((np.mean([res[c][k]['full'] for c in cids]), k, d.mean(), d.std(ddof=1) / np.sqrt(len(d)), int((d > 0).sum()),
                         np.mean([res[c][k]['own'] for c in cids]), np.mean([res[c][k]['dead_recall'] for c in cids]),
                         np.mean([res[c][k]['dead_precision'] for c in cids])))
        print(f'{len(cids)} matches: {cids}')
        for full, k, dm, se, up, own, rec, prec in sorted(rows, reverse=True)[:25] + [r for r in rows if r[1] in ('v9', 'nogap')]:
            print(f'{k:18s} full {full:.4f}  vs v9 {dm:+.4f} +- {se:.4f} up {up:2d}/{len(cids)}  own {own:.4f}  dead R {rec:.3f} P {prec:.3f}')
