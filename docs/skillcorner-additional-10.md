# SkillCorner additional-data integration — 17 November 2026

All ten requested matches were acquired, verified and processed. The external data
catalogue now contains **28 unique match identities: 7 DFL, 20 SkillCorner and 1 WCSF**.
The ten new cases are ready on this machine. The v9 models still use the original
18 matches. No model was fitted, tuned, scored or run to generate predictions.

Branch: `experiment/skillcorner-additional-10`, based on
`f637daeaf2540f78f520338908d41ed3e1d6d08b`.

## Acquisition and usable frame counts

Source: [SkillCorner Open Data](https://github.com/SkillCorner/opendata), pinned to
[`4340d274572876239c154c90bc507a9b3250a656`](https://github.com/SkillCorner/opendata/tree/4340d274572876239c154c90bc507a9b3250a656).
This is the revision already frozen in `benchmark/skillcorner/protocol.json`.
Each match has all four expected files: `{id}_match.json`,
`{id}_tracking_extrapolated.jsonl`, `{id}_dynamic_events.csv` and
`{id}_phases_of_play.csv`. All 40 match files and three source/attribution files
passed pinned byte-size and content-hash checks. The Git LFS payloads were acquired,
not pointer text. Tracking totals **898,211,241 bytes**; all acquired files total
**946,385,196 bytes**. Nothing is missing.

| Match | Native tracking rows | Active native rows | Native rows with detected ball | Processed 25 Hz rows | Known H/A rows at 25 Hz |
|---|---:|---:|---:|---:|---:|
| 1899585 | 60,530 | 60,511 | 31,826 | 151,325 | 74,206 |
| 1925299 | 61,301 | 61,282 | 38,618 | 153,253 | 89,108 |
| 1927964 | 59,070 | 59,051 | 38,215 | 147,675 | 92,812 |
| 1953632 | 59,250 | 59,231 | 35,038 | 148,125 | 81,853 |
| 1959846 | 58,541 | 58,532 | 34,824 | 146,353 | 74,499 |
| 1986691 | 59,090 | 59,071 | 34,019 | 147,725 | 78,919 |
| 1996435 | 57,621 | 57,602 | 34,701 | 144,053 | 80,275 |
| 1996436 | 60,280 | 60,261 | 32,785 | 150,700 | 67,562 |
| 2006229 | 59,270 | 59,251 | 35,881 | 148,175 | 81,370 |
| 2006363 | 59,101 | 59,072 | 36,160 | 147,753 | 81,017 |
| **Total** | **594,054** | **593,864** | **352,067** | **1,485,137** | **801,621** |

Active means tracking period 1 or 2. Detected-ball counts above are native active
rows with usable detected ball coordinates. Unobserved-ball rows remain useful as
missing-data context; they are not silently removed. The 25 Hz counts include
resampling and are **not additional independent observations**. The machine-readable
audit also reports rows with both teams visible, observation masks, period counts
and per-match H/A/X totals.

## Annotation compatibility and limitations

All ten have compatible provider possession-phase annotations with both H and A
labels. The existing adapter is used unchanged: detected-only coordinates, native
10 Hz frame/time reconciliation, half-open phase intervals, pitch normalization to
105.3 × 68 m and the existing 25 Hz resampling rules. Player identities and roster
membership are validated. Native frame IDs are contiguous, increasing and unique
from zero, with both match periods present. Dynamic event CSVs were acquired and
parsed for identity/schema/completeness, but are not feature inputs or labels.

SkillCorner provides **H/A possession supervision, not dead-ball supervision**.
Uncovered, conflicting and out-of-period frames remain X (code 3). D (code 2) is
never invented from a missing ball or missing phase. The existing trainers already
treat SkillCorner as H/A-only.

The unchanged adapter quarantined the following native frames because phase
annotations cross tracking-period boundaries:

| Match | Native frames retained as unknown |
|---|---:|
| 1899585 | 11 |
| 1925299 | 85 |
| 1927964 | 47 |
| 1953632 | 67 |
| 1959846 | 8 |
| 1986691 | 74 |
| 1996435 | 72 |
| 1996436 | 36 |
| 2006229 | 23 |
| 2006363 | 194 |
| **Total** | **617** |

There were no out-of-range phase frames or phase-clock disagreement intervals.
These are provider-generated proxy labels; missing observations, extrapolation and
differences in possession conventions remain limitations of this source.

## Storage and pipeline access

The checkout is at
`C:\Users\noorh\OneDrive\Documents\ChatGPT\HOOKER\messis-foot-skillcorner`.
Paths below are relative to its parent, `HOOKER`:

| Content | Location |
|---|---|
| Verified original files | `skillcorner-additional-data/raw/{id}/{id}_*` |
| Original licence and source README | `skillcorner-additional-data/source/` |
| Existing motion-cache schema | `skillcorner-additional-data/cache/{id}-detected.{features.npz,reference.npz,metadata.json}` |
| Training feature cases | `strong-emissions-reference/cases/skillcorner-{id}.npz` |
| Case content/feature provenance | `strong-emissions-reference/cases/skillcorner-{id}.data.json` |
| Local source and integrity audit | `skillcorner-additional-data/provenance.json` and `integrity/{id}.json` |
| Committed audit | `reports/data-integration/skillcorner-additional-10.json` |

`se_load.AVAILABLE` exposes all 28 identities; `se_data_catalog.ADDITIONAL_CASES`
exposes just the ten additions. `se_load.load('skillcorner-{id}')` loads new motion
caches from the new sibling directory. Legacy IDs still resolve to their original
`independent-reference/cache` paths. `se_load.ALL`, `SKILLCORNER`, `HOLDOUT`,
`PRIMARY`, and the trainers' historical `ALL`, `DEV` and folds retain their original
contents.

`prepare_additional_skillcorner.py` performs reproducible, hash-verified acquisition
and data-only conversion. It defaults to these locations and refuses differing
existing assets or partial/incompatible processed cases. It can use `--root`,
`--cases` and `--report` for a separate rebuild. For custom raw/cache roots, set
`se_load.ADDITIONAL_ROOT` accordingly before calling its loader; the trainers use
their existing `PRIVATE/cases` location.

Feature cases contain `X` (float32, 343 columns), `names`, `ref`, `period` and
`observed`, using `se_features.build` plus all five append blocks in their existing
order. They omit `release_sup`, which would require a frozen-model prediction.
Neither training reader needs that field. Analysis tools that explicitly consume
`release_sup` cannot use it on these cases without a separately authorized model
operation.

Both existing trainers already accept `extra_train`. The committed
`benchmark/skillcorner/additional-training-data.json` supplies only that data-list
option; merge its field into future training options if training is later authorized.
No training command or default split was changed or executed during this task.

## Preservation, split history and validation

- The ten additional IDs are disjoint from the existing ten SkillCorner IDs. Their
  pinned tracking SHA-256 objects are also unique and disjoint from the originals.
- The original external caches were absent beside this fresh checkout. Their
  contents could not be reverified here. No original raw/cache/case path was written;
  identity lists, legacy routing, adapter code and feature code remain unchanged.
- `strong_model/`, model architectures, training code, hyperparameters, release
  inference and v9 submission artifacts were not changed. No competition inputs
  were opened by the integration or sent to an external service.
- These are additions to the **v9 training list**, not previously unseen datasets:
  the original SkillCorner protocol classified 1899585–1986691 as development,
  1996435/1996436 as calibration and 2006229/2006363 as validation. Earlier repository
  benchmark reports already mention the last two. Future use for training must not
  present those historical validation results as independent evidence for a model
  trained on the additions.
- **20 data-only tests passed**, covering cache integrity, interpolation, time and
  phase reconciliation, unknown-label preservation, duplicate prevention, loader
  routing and compatibility with the unchanged GBM/GRU data readers. The synthetic
  decoder/model test in the existing suite was intentionally excluded.
- All ten real cases passed cache round-trip, source identity, index alignment,
  343-column feature order, finite-value and H/A/X checks. Both unchanged training
  readers were exercised directly without importing their model code. Existing
  release feature-name subsets are present in the new schema; no predictions or
  performance metrics were computed. See `reports/data-integration/reader-compatibility.json`.

Runtime for preparation: CPython 3.14.0, NumPy 2.4.2. Source-file hashes, raw checksums,
cache checksums, case checksums and detailed counts are in the committed audit.

## Licence and distribution

The pinned upstream repository carries the MIT licence, copyright © 2020 SkillCorner,
and requests SkillCorner attribution. The original licence and README are retained
locally; the repository already contains SkillCorner's licence under
`benchmark/skillcorner/LICENSE`. No additional licence restriction was found in
the pinned source files inspected for this integration.

The project documents a no-match-data-in-Git policy. Only integration code,
data-list configuration and audit metadata are committed. Raw tracking, events,
annotations, motion caches and processed feature matrices remain outside Git.
