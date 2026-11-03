# Missing-ball handling prototype

The user authorised implementation of missing-observation handling first. This is a local Python prototype, not a validated competition entry.

## Approach

Use bounded, two-sided team continuity first. A probabilistic sequence model needs an independent validation source; full video retracking is deferred until unresolved intervals identify where it is useful. These are implementation choices, not measured performance findings.

1. Convert tracking to nearest home/away distances in metres. Track slots are temporary, never persistent player IDs.
2. Confirm control only after consecutive close, unambiguous observations. Backdate a confirmed run to its start; never let evidence accumulate across missing frames.
3. Leave missing/contested observations unknown initially. Bridge a short gap only when both confirmed anchors agree. Restart hints block bridging. Longer gaps additionally require consistent automatic possession-phase evidence throughout.
4. Retain explicit algorithmic dead-ball evidence supplied by an upstream component. The reference-match adapter also applies the organiser-published pre-second-kickoff interval [110808,113742) as D with separate provenance. This prototype does NOT infer D from missing tracking, a stationary ball, or a set-piece interval. A match-ready live/dead detector remains separate work.
5. Estimate short missing ball coordinates only for diagnostics when displacement is plausible; never use these invented coordinates to decide a hidden turnover.
6. Export unresolved intervals as a queue for a future local video algorithm. Never use manual corrections on the competition match.

## Constraints

No gated assets leave the local machine. No public-ground-truth training, tuning, or model selection. Reset at half boundaries. Preserve X for unresolved intervals. Heuristic evidence levels are not calibrated probabilities. A same-team gap can still contain a hidden turnover or stoppage: bounded bridging is a hypothesis, not proof.

## Defaults chosen for synthetic development

25 fps; control distance 2 m; opposing distance advantage 0.75 m; 0.24 s confirmation; 0.6 s short continuity; 2 s tag-supported continuity; 0.4 s coordinate interpolation; 35 m/s displacement cap. All are provisional and exposed in config. Synthetic examples cannot tune real-match accuracy.

## Deliverables

Standard-library Python package, raw ATD/Smart Tagging adapter, evidence CSV interface, deterministic demo, tests, submission-shaped CSV, frame diagnostics, unresolved-interval JSON and coverage report. Default match adapter has no D classifier, so its output is explicitly experimental.
