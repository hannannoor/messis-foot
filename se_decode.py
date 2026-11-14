"""Plain 3-state Viterbi over per-row log supports with a uniform switch cost. Rows in period 0 are X.
Decoding restarts at every period change. No reference inputs."""
import numpy as np


def viterbi(logp, cost):
    n = len(logp)
    back = np.zeros((n, 3), np.int8)
    score = logp[0].copy()
    for t in range(1, n):
        best = score.argmax()
        stay = score
        switch = score[best] - cost
        # for each state: stay in it, or come from best other state
        cand_switch = np.full(3, switch)
        # if best equals the state itself, switching from second best
        order = np.argsort(score)
        second = score[order[1]] - cost
        for k in range(3):
            if best == k:
                cand_switch[k] = second
        frm = np.where(stay >= cand_switch, np.arange(3), np.where(np.arange(3) == best, order[1], best))
        score = np.maximum(stay, cand_switch) + logp[t]
        back[t] = frm
    path = np.zeros(n, np.int8)
    path[-1] = score.argmax()
    for t in range(n - 1, 0, -1):
        path[t - 1] = back[t, path[t]]
    return path


def decode(sup, period, cost=32.0, power=1.0, d_bias=0.0):
    sup = np.clip(np.asarray(sup, np.float64), 1e-9, 1)
    logp = power * np.log(sup)
    logp[:, 2] += d_bias
    out = np.full(len(sup), 3, np.uint8)
    per = np.asarray(period)
    i, n = 0, len(per)
    while i < n:
        if per[i] == 0:
            i += 1
            continue
        j = i
        while j < n and per[j] == per[i]:
            j += 1
        out[i:j] = viterbi(logp[i:j], cost)
        i = j
    return out
