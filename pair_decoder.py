"""Experiment G: three-state decoder with a 3x3 pair switch-cost table.

``decode_matrix`` is ``touch_decoder.decode_variable``'s recursion with the cost of moving from state ``k`` to
state ``s != k`` equal to ``matrix[k][s]`` (diagonal 0).  Validation, period/usability segmentation, per-row
normalisation, argmax order (H, A, D; first maximum wins) and backtrace are unchanged, so a uniform matrix
reproduces ``decode_variable`` with uniform costs label for label.
"""
from math import isfinite

from touch_decoder import validate_rows


def uniform_matrix(cost):
    c = float(cost)
    return ((0., c, c), (c, 0., c), (c, c, 0.))


def validate_matrix(matrix):
    try:
        rows = [tuple(r) for r in matrix]
    except TypeError:
        raise ValueError('Cost matrix must be 3x3') from None
    if len(rows) != 3 or any(len(r) != 3 for r in rows):
        raise ValueError('Cost matrix must be 3x3')
    for i, row in enumerate(rows):
        for j, v in enumerate(row):
            if isinstance(v, bool) or not isinstance(v, (int, float)) or not isfinite(v) or v < 0:
                raise ValueError('Cost matrix entries must be finite and non-negative')
            if i == j and v != 0:
                raise ValueError('Cost matrix diagonal must be zero')
    return tuple(tuple(float(v) for v in r) for r in rows)


def decode_matrix(emissions, periods, usable, matrix):
    C = validate_matrix(matrix)
    n = len(periods)
    validate_rows(emissions, periods, usable, [(0., 0., 0.)] * n)
    result = ['X'] * n
    back = [bytearray(n) for _ in range(3)]
    i = 0
    while i < n:
        if not periods[i] or not usable[i]:
            i += 1
            continue
        first, period = i, periods[i]
        previous = (0., 0., 0.)
        while i < n and periods[i] == period and usable[i]:
            row = emissions[i]
            values = []
            for state in range(3):
                a = previous[0] - (C[0][state] if state != 0 else 0.)
                b = previous[1] - (C[1][state] if state != 1 else 0.)
                c = previous[2] - (C[2][state] if state != 2 else 0.)
                chosen = 0 if a >= b and a >= c else (1 if b >= c else 2)
                back[state][i] = chosen
                values.append((a, b, c)[chosen] + row[state])
            normal = max(values)
            previous = tuple(v - normal for v in values)
            if not all(isfinite(v) for v in previous):
                raise ValueError('Decoder overflow')
            i += 1
        a, b, c = previous
        state = 0 if a >= b and a >= c else (1 if b >= c else 2)
        for j in range(i - 1, first - 1, -1):
            result[j] = 'HAD'[state]
            state = back[state][j]
    return result
