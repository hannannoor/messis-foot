"""Exact empirical bootstrap of published match-level deltas, not fresh evidence."""
from pathlib import Path
import hashlib
import json
import math
import statistics

ROOT = Path(__file__).resolve().parent
RECEIPTS = ROOT / 'snapshots/current-cee6741/reports/ball-gap/regression'


def compositions(total, length):
    if length == 1:
        yield (total,)
    else:
        for first in range(total + 1):
            for rest in compositions(total - first, length - 1):
                yield (first,) + rest


def main():
    deltas = {'dfl': [], 'skillcorner': []}
    checksums = {}
    for path in sorted(RECEIPTS.glob('*-natural.json')):
        data = path.read_bytes()
        row = json.loads(data)
        variants = row['variants']
        before = variants['w0-c32']['metrics']['spell_f1_mean']
        after = variants['w0-c32-neutral-missing']['metrics']['spell_f1_mean']
        deltas[row['cohort']].append(dict(match=row['match'], delta=after-before))
        checksums[path.name] = hashlib.sha256(data).hexdigest()
    assert len(deltas['dfl']) == 2 and len(deltas['skillcorner']) == 8
    assert all(row['delta'] == 0 for row in deltas['dfl'])
    values = [row['delta'] for row in deltas['skillcorner']]
    n = len(values)
    distribution = []
    for counts in compositions(n, n):
        weight = math.factorial(n) // math.prod(math.factorial(c) for c in counts)
        score = .5 * sum(c * value for c, value in zip(counts, values)) / n
        distribution.append((score, weight))
    distribution.sort()
    total = n**n
    assert sum(weight for _, weight in distribution) == total

    def quantile(q):
        threshold = math.ceil(q * total)
        cumulative = 0
        for value, weight in distribution:
            cumulative += weight
            if cumulative >= threshold:
                return value
        raise AssertionError('quantile not found')

    output = dict(estimator='equal-provider mean of unweighted paired natural-match spell-F1 deltas',
        resampling='with replacement within provider at original provider match count',
        interval='exact empirical inverse-CDF 0.025 and 0.975 quantiles, no interpolation',
        rng='none: exhaustive multinomial compositions; DFL deltas all zero',
        compositions=len(distribution), ordered_skillcorner_samples=total,
        mean_delta=.5*statistics.fmean(values), lower=quantile(.025), upper=quantile(.975),
        empirical_mass_at_or_below_zero=sum(w for x,w in distribution if x<=0)/total,
        match_deltas=deltas, receipt_sha256=checksums,
        reused_matches=True, adaptive_selection_corrected=False, new_holdout=False,
        physical_reference_accuracy_verified=False)
    assert math.isclose(output['mean_delta'], .0017862686598655725, abs_tol=1e-15)
    assert math.isclose(output['lower'], .0004760517173494558, abs_tol=1e-15)
    assert math.isclose(output['upper'], .0032891634823429064, abs_tol=1e-15)
    (ROOT / 'conditional-interval-verification.json').write_text(json.dumps(output,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:output[k] for k in ('compositions','ordered_skillcorner_samples','mean_delta','lower','upper','empirical_mass_at_or_below_zero','new_holdout')}))


if __name__ == '__main__':
    main()
