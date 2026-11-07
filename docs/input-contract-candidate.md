# Experimental input-contract candidate

The new entry point preserves original frame indices and writes four frozen comparator CSVs, one selected CSV and a separate uncertainty file. It does not refit either model. Run from this checkout:

```powershell
python candidate.py --prefix "C:/Users/leonj/Desktop/more than a hack data/tactical cam/BAR-ATH_tactical" --out "../candidate-experimental-new"
```

Use a new dedicated output folder. Repeating the command into a folder owned by this route stages a complete new generation, moves the previous directory to a sibling backup, then installs staging; other populated folders and input aliases are rejected. The runtime uses only Python standard-library modules. `--scope synthetic` explicitly marks small fixture runs and never asserts challenge compatibility. Broadcast is audit-only until there is an automatic justified clock map.

Outputs:
- `incumbent.csv`: unchanged frozen tactical model on channel-referenced geometry.
- `carry.csv`: incumbent plus structural-period carry.
- `agreement.csv`: keep incumbent H/A/D; resolve X only when ungated temporal H/A and raw tactical H/A agree.
- `agreement-plus-carry.csv` and identical `submission.csv`: materialize remaining within-period X using previous label, or first known label for a leading gap. Wholly unknown periods become D by convention. Outside published half windows stays X.
- `uncertainty.csv`: original index, period, incumbent, latent agreement label, final label and materialization/quality indicators. No raw coordinates. A carried label is not additional evidence.
- `candidate-report.json`: aggregate policy counts, input/code/model hashes, coordinate/timing contract, correspondence statistics and limitations.

## Input findings and decisions

Team roles now follow the explicit raw register → PlayerChannelRef → player/team chain and documented official H/A team names. Permuting XML declaration order cannot change the result. The refreshed audit compares both declaration orders and per-slot team roles against the legacy interpretation; both real feeds agree, so it found no actual H/A swap. Registered slots must include both teams.

Both feeds declare 25Hz, normalized XY and a105x68m field. Canonical geometry remains105.3x68m, as documented by the competition. Metadata speed is `kph`/`speed_kph` while public DATA.md says m/s. Speed values are validated syntactically but unused; no conversion assumption affects inference. Source frames1..N become0..N-1, without trimming. Published tactical half windows provide structural periods only; no target labels are loaded.

Tactical has199319 rows/46 anonymous slots, broadcast164488/51 slots. Available values do not establish native detections: neither feed provides per-observation detection/extrapolation flags. Repeated positions are counted as a diagnostic and never used as proof of stale tracking. No freshness filter was invented from target outcomes.

The existing ≤3 reprojection-error rule is retained for comparison. It describes a pitch-to-pixel transform, so passing it does not independently validate pitch-space ATD observations. This remains an assumption rather than a calibrated universal cutoff.

ATD slots are not persistent player IDs. The new adapter sorts anonymous team point sets and accepts only mutual unique nearest neighbours within0.8m at adjacent25Hz frames. It starts new estimated correspondences for ties, unmatched/far points, missing geometry and period boundaries. The bound is20m/s divided by25Hz, predeclared from the existing feature scale, without local tuning. Estimated correspondence can still swap identities at crossings; these IDs are never claimed as verified players. The temporal model was trained on genuine external player identities, so transfer validity remains uncertain. Raw source speed is not used by the association.

## Validation limits

The comparison manifest fixes four policies, source hashes, association bound and two previously seen development stress matches before these runs. The original gated temporal artifact remains rejected. The ungated combination is post-hoc and experimental, not a retroactively accepted model. The seen SkillCorner match supplies known-play H/A reference; the seen DFL match includes provider H/A/D with its previously documented inactive-coordinate shortcut. Neither is a fresh holdout or target accuracy measurement.

The fresh-data scout found no fully qualified licensed full-state holdout. Groningen WCSF is closest semantically, but explicit rights, label provenance and non-overlap remain unresolved. No near-fit assets were downloaded, no labels manufactured and no opened cohort was renamed fresh. See `fresh-had-cohort-scout.md`.

Both camera input audits, compatibility stress aggregates and clean-run receipts are under `reports/input-contract/`. Per-frame target CSVs and source assets remain local and are excluded from publication. The Desktop baseline is preserved.
## Initial tactical result (V1, superseded after review)

Two clean runs produced the same six CSV hashes before review. Both selected files passed the official format-only validator at199319 rows, indices0..199318. The pre-review selected submission SHA256 was `b96922c04b03853a58f1ba7a941157b1c12483b67d458d1fd08e02bd3db86788`. All34 frozen sources and the Desktop installed pipeline remained unchanged.

| Policy | Active X frames | Active X fraction |
| --- | ---: | ---: |
| incumbent | 89200 | 56.1511% |
| carry | 0 | 0.0000% |
| agreement | 54390 | 34.2383% |
| agreement-plus-carry | 0 | 0.0000% |

Agreement added34810 inferred H/A labels;54390 latent X labels remain and are explicitly marked when materialized. This establishes reproducibility and coverage behavior, not local correctness. The ungraded40462 rows remain X. Full suite287 tests passed with5 skips; two Python3.11 isolated `-I -S` synthetic CLI runs were byte-identical, and runtime sources parse using Python3.9 grammar. This is a syntax check, not execution on Python3.9. Initial OCR test failures came from an absent temporary directory and passed after the test environment was corrected.

## Initial seen correspondence compatibility stress (V1)

| Provider/match | Policy | Original-ID spellF1 | Estimated-correspondence spellF1 | Changed rows |
| --- | --- | ---: | ---: | ---: |
| skillcorner/1874553 | incumbent | 0.537331 | 0.537331 | 0 |
| skillcorner/1874553 | carry | 0.530825 | 0.530825 | 0 |
| skillcorner/1874553 | agreement | 0.544970 | 0.544970 | 0 |
| skillcorner/1874553 | agreement-plus-carry | 0.533718 | 0.533718 | 0 |
| dfl/J03WOH | incumbent | 0.505415 | 0.505415 | 0 |
| dfl/J03WOH | carry | 0.505415 | 0.505415 | 0 |
| dfl/J03WOH | agreement | 0.522968 | 0.522968 | 0 |
| dfl/J03WOH | agreement-plus-carry | 0.522968 | 0.522968 | 0 |

Both predeclared seen development matches had identical four-policy predictions with original versus estimated correspondences. Some velocity/continuity features changed, but no labels did. This is a useful limited compatibility result, not proof that the adapter recovers real identities or transfers safely to anonymous target slots. The40-tree model actually splits on team speeds/continuities as well as counts, widths, anchors and gap duration, so the identity contract still matters. No parameter was changed after seeing these results.

## Review corrections and remaining scope

The fresh code review found an applicability bug: invalid-geometry frames skipped by the decoder still held a zero placeholder, which the direct head converted to H. V2 makes this head abstain whenever geometry was skipped. A confidence threshold is still not applied; an absent prediction is no longer treated as an H proposal. This is a software-contract correction, fixed and frozen before rerunning, without fitting a model or choosing a threshold from local outcomes. V1 receipts are preserved separately and are not the selected candidate.

The homography parser now rejects duplicate headers, invalid flags and short/long rows before applying the unchanged numerical gate. The legacy audit compares actual per-slot roles as well as XML/register order, and requires registered slots on both sides. Output checks use reparse-point metadata on older Python/Windows too; audit reports use exclusive creation so a second writer cannot overwrite a first report. A Windows dangling-symlink regression cannot execute under this account without the symlink privilege; real junction, hardlink and concurrent-writer checks do execute.

Compatibility exports now use an explicit aggregate-field allowlist. The initial local scorer results contained per-event transition arrays; these were caught before any publication. Published V1 exports remove them while preserving allowed scalar scores exactly. V2 uses the corrected serializer and is recursively checked before upload. Raw source data and per-frame experimental output remain local.

The SkillCorner stress cache was resampled to25Hz using player-identity-assisted interpolation. Its zero-change result therefore concerns that preprocessed cache and does not fully simulate anonymous detections. No model was selected using that stress.

Staged directory replacement does not guarantee atomic visibility: readers may briefly see no destination between renames, and interruption can leave a sibling `.previous` backup. Preserve and inspect that backup before recovering it to the expected destination. This route does not claim crash-proof transactions.

Deferred minor issues: synthetic audit period counts still use the tactical audit convention while the synthetic predictor uses a single test period; this does not affect real tactical runs. The anonymous helper requires a contiguous canonical25Hz sequence supplied by its caller (the tactical reader enforces it); stronger direct-call gap/crossing tests and an in-bound tie regression are deferred. Estimated correspondences remain unverified.

## Reviewed result (V2, current experimental candidate)

Two clean V2 runs match all six CSVs byte-for-byte. Official format validation passed both selected199319-row files. Selected SHA256: `b96922c04b03853a58f1ba7a941157b1c12483b67d458d1fd08e02bd3db86788`.

| Policy | Active X frames | Active X fraction |
| --- | ---: | ---: |
| incumbent | 89200 | 56.1511% |
| carry | 0 | 0.0000% |
| agreement | 54577 | 34.3561% |
| agreement-plus-carry | 0 | 0.0000% |

The applicability correction withdrew187 unsupported latent H proposals. Agreement now adds34623 inferred H/A labels and retains54577 latent uncertain rows. Carry leaves the final selected CSV unchanged from V1; those187 rows are correctly marked materialized instead. No local correctness was measured, and no threshold/model was tuned. The40462 out-of-scope rows remain X.

Verification:294 tests passed with6 skips, including one Windows symlink privilege limitation; isolated Python3.11 standard-library runs match, Python3.9 grammar parses,34 frozen sources and Desktop installation are unchanged. See the fresh [code review and fix dispositions](input-contract-code-review.md).

The V2 seen-data stress was rerun after the applicability correction. Both predeclared matches still had0changed predictions for each of the four policies when switching original IDs to estimated correspondences; V2 aggregate-only receipts are current. This does not add independent validation or change the selection.
