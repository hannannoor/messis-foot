# MESSI's FOOT — frozen-control technical document

Candidate: `w0-c32-neutral-missing`, packaged as `competition_release.py`. Exact revision, artifact identity and delivery checks are in [the release decision](competition-release-decision.md). Team registration/name and submission-form logistics remain to be confirmed by the team.

## Approach

We infer H/A/D on the original tactical timeline using a frozen 31-node geometry/history tree and an offline three-state sequence decoder. EPTS register references determine the documented teams and coordinate channels. Normalized coordinates use the existing 105.3x68 metre convention; the homography file supplies a quality gate. Anonymous adjacent-frame association and invalid-geometry clearing are preserved from the research route. Declared source speeds are validated but unused.

The tree consumes 18 observation, distance, ball-motion and retained-control features. Its leaf supports are uncalibrated H/A/D evidence. Float32 feature comparisons match the exported tree. Log supports use floor 1e-6; each state change costs 32. The selected motion-head weight is zero. Equal path scores follow deterministic H,A,D ordering. The decoder runs within input-only usable segments and structural halves; reference labels do not determine inference barriers.

When the ball is missing, all three emission scores are zero: absence is not positive D evidence. Entirely unsupported usable segments remain latent X. A separate original materialization step forward-fills, then head-backfills, within each structural period. An entirely unknown active block becomes D by convention; this is not an observed stoppage. Outside structural periods output remains X. The release changes packaging and output handling, not these decisions.

Finite sequence decoding was retained because it can reconsider wrong existing decisions while discouraging fragmented spells. A subsequent fixed neutral-missing correction reduced false D under missing-ball stress. Both were selected on previously examined external evidence, not the supplied match. Cadence-only velocity repair was later rejected by liveness safeguards; no rejected model was promoted. [Performance history](performance-history-and-next-step.md).

## Assets and labelled sources

**Selected match inputs:** tactical `_atd.xml`, `_atd.txt` and `_homography.csv`, processed locally by code. No video, Smart Tagging, broadcast stream, challenge hand labels, event-provider game data or private GT enters selected inference. Earlier OCR/synchronization work yielded zero usable camera links and was dropped from this route. No manual corrections are applied.

**DFL / Sportec Solutions:** the [integrated spatiotemporal/event dataset](https://doi.org/10.1038/s41597-025-04505-y), [Figshare v1](https://doi.org/10.6084/m9.figshare.28196177.v1), CC BY 4.0. The frozen tactical tree was fitted on four external matches, J03WOH/J03WOY/J03WPY/J03WMX, with original and fixed 30% observation masking. J03WQQ supplied original validation; J03WR9/J03WN1 supplied the original two-match test. Labels are the dataset's provider BallStatus/BallPossession fields; individual human annotators/annotation error rates were not independently audited. Those fields never enter prediction features. All seven matches were later reused in development/regression work and cannot now be called fresh holdouts. [Manifest and attribution](../benchmark/provenance.json), [frozen artifact](../benchmark/frozen/tactical-selected.json).

**SkillCorner / PySport:** [MIT open data at revision 4340d274572876239c154c90bc507a9b3250a656](https://github.com/SkillCorner/opendata/tree/4340d274572876239c154c90bc507a9b3250a656). Twenty tracking exports were used in the research programme: eight development, two calibration, two validation and eight final diagnostic/test matches. Provider possession phases support known-play H/A; unannotated regions are X and cannot validate D. The motion model trained using external development data is not used by the selected zero-weight route. Reference/coordinate interpolation and provider-identity advantages are disclosed in [the pinned protocol](../benchmark/skillcorner/protocol.json) and [benchmark notes](../benchmark/skillcorner/README.md). No new annotations were created for this release.

**WCSF:** one anonymous external Dutch match, two halves, [source revision 1c9ba798f98a9fffb16081a5d3965774d4e5662c](https://github.com/MatKempeGroningen/WCSF_SolutionRoom/tree/1c9ba798f98a9fffb16081a5d3965774d4e5662c). The source owner's recorded clarification describes MIT dataset terms and manual SciSports Alive/Possession annotations. This was a fixed transfer audit, not fitting/selection data for the current control. Native inputs are supplied smoothed 10 Hz samples resampled to the canonical grid. The case is permanently used evidence now. Anonymous identity is not recovered; raw files, reference/prediction arrays and local stores are not published. [Qualification](reference-qualification/source-comparison.md), [audit and limits](wcsf-transfer-results.md).

The research history and provenance remain public; external source acquisition is unnecessary to run the selected frozen artifact. Preserved historical byte seals are not rewritten to make fresh cache containers impersonate original generations.

## Possession conventions

H/A mean the model's inferred home/away control state, not an adjudicated last touch. Loose balls and challenges have no separate state: geometry, retained near-player control and sequence continuity decide between H/A/D. There is no explicit independently validated restart detector. D is jointly inferred from the learned geometry/history evidence and decoder. Missing observations alone do not establish D; all-unknown-block D is separately disclosed carry convention. Fixed published pre-kickoff D labels are not applied.

The official ranking measures mean team-possession spell F1 at IoUs .3/.4/.5/.6/.7, with frame macro F1 and transition/latency tie-breaks. X is a frame miss on graded frames and is filled for temporal scoring. Accordingly zero X, high frame accuracy or fewer transitions alone do not establish a stronger possession result. [Official metric specification](https://github.com/metrica-sports/more-than-a-hack-2027/blob/f8f2629ff1e0985f81d7e59d8413678514ee1530/EVALUATION.md).

## Evidence and limitations

On the previously unused WCSF audit, the unchanged control scored spell F1 .505216, macro F1 .707246 and frame accuracy 70.9517%; fixed w50 comparators scored .384073 spell F1. One smoothed provider match does not establish population superiority or challenge accuracy. WCSF is now development/regression evidence.

The control misses many stoppages: WCSF D recall 49.6198%, with missed D accounting for 81.095% of wrong frames. That does not quantify its share of spell-score loss. Direct H/A boundary recall within 12 canonical frames is 84/237. Frozen DFL inactive coordinates may make stationarity an overly effective provider shortcut. Missing/reacquired ball speeds, retained-control features, asymmetric learned support, unobserved hidden changes, nonlocal smoothing and deterministic ties remain limitations. Coordinate availability does not prove observation freshness or physical possession truth.

The release decision reports real-file regeneration and any scoped public five-minute check separately. The public check is not model-selection evidence; the private full-match score/rank remains unknown. Future performance work should attribute missed/split/merged spell objects and emissions versus decoder costs before testing one justified intervention.

## Reproduction

Use CPython 3.14.5 Windows x64 and the exact release artifact/revision in the decision record. No runtime dependencies beyond the standard library are needed. Run:

```powershell
python competition_release.py --prefix "C:/football-data/tactical cam/BAR-ATH_tactical" --out "C:/football-data/submissions/new-frozen-control-run"
```

Keep the output path new. Confirm a matching completion receipt and validate the exact CSV with the unchanged official validator. Full setup, deterministic builder check, source identities, test/evaluator setup and private-data boundaries are in [competition-release.md](competition-release.md). Publish code/docs/model metadata only; submit the verified CSV through the organiser's form under the registered team name.
