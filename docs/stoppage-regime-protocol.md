# Stoppage-regime protocol, 10 November 2026

Branch `codex/stoppage-regime-2026-11-10`, from head `7230797`. Restates the fixed design (brief sections 3, 6, 7) before the run.

## Regimes (`stoppage_regime.py`, from reference labels and periods; constants 76 and 268 are the provided match's long-gap threshold and median gap length)

- Long dead run: maximal run of reference D of at least 76 frames inside one period. Selected when `h(f"{match_id}:sel:{s}") % 100 < round(100c)`. Dead block `[s+a, e+b)`, `a = h(f"{match_id}:a:{s}") % 51`, `b = h(f"{match_id}:b:{s}") % 51`, clipped to the period; if shorter than 76 frames use `[s, e)`.
- Live blocks: consecutive 268-frame windows per period, index `k` from the period start. Implementation choices made before the run: only full 268-frame windows are used; `k` restarts per period (the period is in the hash key); windows are taken in ascending `h(f"{match_id}:live:{period}:{k}")` order until the removed live frames reach the target; a window overlapping any dead block is skipped.
- `natural`: nothing removed. `stop100`: c=1.0, no live blocks. `stop75`: c=0.75, live target one third of the removed dead frames. `stop50`: c=0.5, live target equal to the removed dead frames. `stop75-jitter`: as `stop75`, then `add_jitter`.

## Run (once)

Five matches (`dfl-J03WN1`, `dfl-J03WR9`, `wcsf-used-match` primary; `dfl-J03WOH`, `dfl-J03WOY` secondary) by five regimes by three variants (`control`; `candidate` = gap rule on control labels; `candidate+touch` = gap rule on `predict_observed_touch(frames, 3, 2, 8)` labels) = 75 official-metric scores. First reproduce each match's natural control spell F1 against `reports/tag-ownership/proxy-accuracy.json`; stop if any differs. Gap-rule selection rate is reported per regime, split by whether a long gap overlaps a dead block, a live block or neither. Primary mean = mean of (mean of the two primary DFL matches) and the WCSF match.

## Decisions fixed in advance

- 7.1: `candidate - control` on the primary mean in `stop75` below -0.005 means stop and report; the user decides.
- 7.2: touch evidence replaces the candidate only if on the primary mean: `candidate+touch - candidate >= +0.04` in `stop75`, `>= 0` in `stop75-jitter`, `>= -0.005` in `natural`; dead-ball recall of `candidate+touch` no more than 0.02 below `candidate` in `stop75`; no primary match loses more than 0.02 in `stop75`. Otherwise the candidate stays and the release steps are skipped.

Limits: these matches were scored before; `dfl-J03WN1` was in the development set that selected the touch setting; the primary set is three matches; re-testing touch evidence after a rejection is post-hoc; the regimes are a model of the provided match built from reference labels, not a measurement of it.
