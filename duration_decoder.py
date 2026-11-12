"""Experiment D: three-state decoder with a minimum-spell-length penalty.

State is (label s in H/A/D, run length k), k capped at ``min_run`` (k == min_run means "min_run or more").
Leaving a run shorter than ``min_run`` costs ``extra`` on top of the row's switch cost.  Every usable
segment starts each label at k == min_run, so the first spell of a segment is never penalised.

With ``extra == 0`` the labels equal ``touch_decoder.decode_variable`` exactly, including tie-breaking.
The existing decoder decides, on each row and for each label, between staying and switching in, with a
``>=`` chain in label order (on an exact tie a switch wins only from a lower-indexed label).  Runs of one
label all receive identical increments afterwards, so the outcome of that decision never reverses; but
floating-point rounding can later make two runs that once differed compare equal.  This decoder therefore
keeps, per label, a preference order over its runs that is fixed when each run is created (by the same
rule) and used to break any later exact tie.
"""
from array import array
from math import isfinite

from touch_decoder import validate_rows


def uniform_costs(n, cost):
    return [(float(cost),) * 3] * n


def _pick(values, order):
    """Index of the maximum of ``values``; exact ties go to the earlier entry of ``order``."""
    best = order[0]
    for k in order[1:]:
        if values[k] > values[best]:
            best = k
    return best


def duration_decode(emissions, periods, usable, costs, *, min_run, extra):
    validate_rows(emissions, periods, usable, costs)
    if type(min_run) is not int or min_run < 1:
        raise ValueError('min_run must be a positive integer')
    if not isinstance(extra, (int, float)) or not isfinite(extra) or extra < 0:
        raise ValueError('extra must be finite and non-negative')
    L = min_run
    extra = float(extra)
    n = len(periods)
    result = ['X'] * n
    src_label = [bytearray(n) for _ in range(3)]          # switch source for the k == 1 state
    src_k = [array('h', bytes(2 * n)) for _ in range(3)]
    merge = [bytearray(n) for _ in range(3)]              # k == L state: 0 from (s, L-1), 1 from (s, L)
    neg = float('-inf')
    i = 0
    while i < n:
        if not periods[i] or not usable[i]:
            i += 1
            continue
        first, period = i, periods[i]
        D = [[neg] * L for _ in range(3)]
        order = [[L - 1] for _ in range(3)]               # live run indices per label, most preferred first
        for s in range(3):
            D[s][L - 1] = 0.
        while i < n and periods[i] == period and usable[i]:
            row, cost = emissions[i], costs[i]
            out = []
            for s in range(3):
                adjusted = [v - extra if k < L - 1 else v for k, v in enumerate(D[s])] if extra else D[s]
                k = _pick(adjusted, order[s])
                out.append((adjusted[k], k))
            newD, newOrder = [], []
            for s in range(3):
                chosen = None
                for t in range(3):
                    if t != s:
                        value = out[t][0] - cost[s]
                        if chosen is None or value > chosen[0]:
                            chosen = (value, t)
                switch_value, switch_from = chosen
                src_label[s][i] = switch_from
                src_k[s][i] = out[switch_from][1]
                values = [neg] * L
                # stays: run k-1 -> k; runs L-2 and L-1 both feed L-1
                shifted = []
                if L > 1:
                    for k in range(1, L - 1):
                        values[k] = D[s][k - 1] - 0.
                    a, b = D[s][L - 2] - 0., D[s][L - 1] - 0.
                    rank = {k: r for r, k in enumerate(order[s])}
                    if a > b or (a == b and rank.get(L - 2, L) < rank.get(L - 1, L)):
                        values[L - 1], merge[s][i], winner = a, 0, L - 2
                    else:
                        values[L - 1], merge[s][i], winner = b, 1, L - 1
                    for k in order[s]:
                        if k == L - 1 or k == L - 2:
                            if k == winner and values[L - 1] != neg:
                                shifted.append(L - 1)
                        elif D[s][k] != neg:
                            shifted.append(k + 1)
                if L == 1:
                    stay = D[s][0] - 0.
                    if switch_value > stay or (switch_value == stay and switch_from < s):
                        values[0], merge[s][i] = switch_value, 0
                    else:
                        values[0], merge[s][i] = stay, 1
                    new_order = [0]
                else:
                    values[0] = switch_value
                    top = shifted[0] if shifted else None
                    if top is None or switch_value > values[top] or (switch_value == values[top] and switch_from < s):
                        new_order = [0] + shifted
                    else:
                        new_order = shifted + [0]
                newD.append([v + row[s] for v in values])
                newOrder.append(new_order)
            normal = max(max(r) for r in newD)
            if not isfinite(normal):
                raise ValueError('Decoder overflow')
            D = [[v - normal for v in r] for r in newD]
            order = newOrder
            i += 1
        a, b, c = (D[s][_pick(D[s], order[s])] for s in range(3))
        s = 0 if a >= b and a >= c else (1 if b >= c else 2)
        k = _pick(D[s], order[s])
        for j in range(i - 1, first - 1, -1):
            result[j] = 'HAD'[s]
            if L == 1:
                if merge[s][j] == 0:
                    s, k = src_label[s][j], src_k[s][j]
            elif k == 0:
                s, k = src_label[s][j], src_k[s][j]
            elif k < L - 1:
                k -= 1
            else:
                k = L - 2 if merge[s][j] == 0 else L - 1
    return result
