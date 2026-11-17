"""Apply the preregistered gates to bounded receipts; never loads tracks."""
import json
from math import fsum
from pathlib import Path
from touch_transfer import ROOT, SC_CONFIRM, PRIMARY

CANDIDATE_SHA = '31b947d3b250b6267a7d8f0aac0c4e4eafd82a4fc873c82759806e676b1bf963'
TOUCH_SHA = '1de96acb8ac2198c960637f6b20c2438c9ff142e76a9ab463c384b52814b8d14'
LIMITS = [
    'Every match has been scored before; touch settings were selected on five development SkillCorner matches and dfl-J03WN1.',
    'This is the third test of touch evidence and is post-hoc.',
    'SkillCorner references have no dead ball and longer possessions than the challenge.',
    'White noise and random thinning match two tracking statistics, not the causes of missing touches; real misses may be nonrandom.',
    'Touch gating sets contain five and three matches.',
    'Expected reset gain is about 0.01, below what two matches can confirm; gate E is a consistency check, not proof.',
    'The reset idea was chosen after a probe on nongating matches.',
    'The regime hides the ball up to two seconds after a restart, which may not match the provided track reacquisition delay.'
]


def decide(results):
    matches = results['matches']
    def delta(ids, variant, base, metric='spell_f1', weights=None):
        weights = weights or [1/len(ids)] * len(ids)
        return fsum((matches[c]['variants'][variant][metric]-matches[c]['variants'][base][metric])*w for c, w in zip(ids, weights))
    conditions = {}
    def gate(name, value, minimum, **details):
        conditions[name] = dict(value=value, minimum=minimum, passed=value >= minimum, **details)
    gate('A', delta(SC_CONFIRM, 'candidate+touch', 'candidate'), -.01)
    gate('B', delta(SC_CONFIRM, 'candidate+touch-thin', 'candidate'), -.01)
    gate('C', delta(PRIMARY, 'candidate+touch-thin', 'candidate', weights=[.25, .25, .5]), .02)
    gate('D', delta(PRIMARY, 'candidate+touch-thin', 'candidate', 'dead_recall', [.25, .25, .5]), -.02)
    touch = all(conditions[k]['passed'] for k in 'ABCD')
    base = 'candidate+touch' if touch else 'candidate'
    reset = base+'+reset'
    held = ('dfl-J03WR9', 'wcsf-used-match')
    individual = {c: delta((c,), reset, base) for c in held}
    gate('E', delta(held, reset, base), .005, per_match=individual, neither_negative=all(v >= 0 for v in individual.values()))
    conditions['E']['passed'] &= conditions['E']['neither_negative']
    gate('F', delta(SC_CONFIRM, reset, base), -.005)
    gate('G', delta(held, reset, base, 'dead_recall'), -.02)
    return dict(conditions=conditions, touch_replaces_candidate=touch, base=base,
                recommended_file_sha256=TOUCH_SHA if touch else CANDIDATE_SHA,
                restart_qualifies=all(conditions[k]['passed'] for k in 'EFG'),
                release_built=False, user_final_choice_pending=True, limits=LIMITS)


def main():
    results = json.loads((ROOT/'reports/touch-transfer/results.json').read_text(encoding='utf-8'))
    if results['status'] != 'complete' or results['variant_scores'] != 90 or results['scoring_calls'] != 95:
        raise ValueError('Incomplete fixed run')
    value = decide(results)
    with (ROOT/'reports/touch-transfer/decision.json').open('x', encoding='utf-8') as handle:
        json.dump(value, handle, sort_keys=True, indent=1, allow_nan=False)
        handle.write('\n')
    print(json.dumps(value, sort_keys=True, indent=1))


if __name__ == '__main__':
    main()
