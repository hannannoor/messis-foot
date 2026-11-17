# Fresh external H/A/D cohort scout

Date: 2026-11-07. Decision: **no genuinely fresh, accessible, explicitly licensed cohort with verified full H/A/D reference was established.** Do not treat this scout as authorization to ingest any of the near-fits below.

The seven IDSSE/DFL matches and all twenty previously opened SkillCorner matches are excluded from fresh-holdout consideration. Inspection was limited to public source documentation, repository metadata/trees and loader source. No match assets, weights, video, reference CSVs or tracking rows were downloaded; no existing local raw/reference data was inspected, no dependencies installed and no authors contacted.

## 1. Groningen WCSF Solution Room: strongest semantic fit; licence unresolved

Source: [repository and guide](https://github.com/MatKempeGroningen/WCSF_SolutionRoom), [pinned README](https://github.com/MatKempeGroningen/WCSF_SolutionRoom/blob/1c9ba798f98a9fffb16081a5d3965774d4e5662c/README.md). Commit **1c9ba798f98a9fffb16081a5d3965774d4e5662c**, dated 2023-05-27.

One anonymous professional European match, optical tracking downsampled from 25 to 10 Hz. Each player/timestamp row includes player and ball positions, timestamp_ms since kick-off, AliveFlag (1 alive, 0 dead) and PossessionFlag (team group; home=1, away=2). These fields provide documented co-timed state and owner rather than an inference from missing events. Coordinates are mirrored per team and need de-mirroring. The README does not explain label annotation/adjudication or contested-ball conventions. Source: [data guide](https://raw.githubusercontent.com/MatKempeGroningen/WCSF_SolutionRoom/1c9ba798f98a9fffb16081a5d3965774d4e5662c/README.md).

Public repository asset entries:

| Asset | Stored bytes | Git blob SHA |
| --- | ---: | --- |
| [positions_FIRST_HALF.csv.zip](https://github.com/MatKempeGroningen/WCSF_SolutionRoom/blob/1c9ba798f98a9fffb16081a5d3965774d4e5662c/positions_FIRST_HALF.csv.zip) | 22,704,565 | d7de2a38f5650150684b1008aa7f4fd28b85d777 |
| [positions_SECOND_HALF.csv.zip](https://github.com/MatKempeGroningen/WCSF_SolutionRoom/blob/1c9ba798f98a9fffb16081a5d3965774d4e5662c/positions_SECOND_HALF.csv.zip) | 23,746,663 | 66fc3ee2966aaf3392d4a327ba3f49385e9c7032 |

Combined ZIP size: **46,451,228 bytes**. Availability is established at repository metadata level; ZIP contents and complete frame coverage were deliberately not fetched.

**Licence:** GitHub repository metadata reports license=null and the complete seven-file tree contains no licence file. The README asks for citation; that does not establish an explicit data/label reuse licence. [Repository metadata](https://api.github.com/repos/MatKempeGroningen/WCSF_SolutionRoom), [pinned tree](https://api.github.com/repos/MatKempeGroningen/WCSF_SolutionRoom/git/trees/1c9ba798f98a9fffb16081a5d3965774d4e5662c?recursive=1).

**Adapter assessment (inference):** after a suitable explicit data/label grant, a small adapter could group rows by half/timestamp, require unanimous duplicated flags, emit D when AliveFlag=0, H/A when alive and PossessionFlag=1/2, and retain unresolved owner/invalid flags as unscored unknown. Preserve the native 10 Hz timeline; do not claim 25 Hz boundary precision. Verify half-clock reset behavior, timestamp completeness, row consistency and ball-coordinate reconstruction after ingestion. Never give AliveFlag, PossessionFlag or team_game_phase to the predictor. Exact real-match identity is withheld, so overlap against the already opened IDSSE matches cannot be conclusively ruled out from identifiers alone. Thus this is **not presently an admissible fresh licensed holdout**, despite being the closest schema match.

## 2. Metrica sample Game 3: easy public access; incomplete reference evidence and informal terms

Source: [provider repository](https://github.com/metrica-sports/sample-data), pinned commit **e706dd506b360d69d9d123d5b8026e7294b13996**, dated 2021-04-15; candidate ID **Sample_Game_3**. The provider documents synchronized tracking and events and an anonymized 105x68 m pitch. Its legal section asks responsible use and public acknowledgement; GitHub reports license=null and the full tree has no licence file. [Pinned README](https://github.com/metrica-sports/sample-data/blob/e706dd506b360d69d9d123d5b8026e7294b13996/README.md), [repository metadata](https://api.github.com/repos/metrica-sports/sample-data).

| Public asset | Stored bytes |
| --- | ---: |
| Sample_Game_3_tracking.txt | 53,443,115 |
| Sample_Game_3_events.json | 1,709,486 |
| Sample_Game_3_metadata.xml | 81,806 |

Total **55,234,407 bytes**; filenames and sizes verified through the [pinned repository tree](https://api.github.com/repos/metrica-sports/sample-data/git/trees/e706dd506b360d69d9d123d5b8026e7294b13996?recursive=1), with no asset bodies fetched.

The maintained [Kloppy EPTS loader](https://github.com/PySport/kloppy/blob/a9651eba7c4dbbe2d2fc6d4cffb4aea63fadac11/kloppy/infra/serializers/tracking/metrica_epts/deserializer.py) explicitly creates frames with ball_owning_team=None and ball_state=None. This establishes a loader limitation, not proof that every possible provider artifact lacks reference labels. The public evidence inspected does not establish a separate complete H/A/D reference.

**Adapter assessment (inference):** tracking/frame mapping is achievable, but synchronized event timestamps cannot by themselves certify every interval's owner and alive/dead state. Producing labels by carrying the last team or marking event gaps dead would manufacture an evaluation target. Need an explicitly licensed, independently justified complete state reference before implementing a scored adapter. The early public release supports temporal disjointness from the 2024/25 SkillCorner cohort, but no full fresh H/A/D cohort is approved here.

## 3. PFF FC 2022 World Cup: provider access gate and event-derived state evidence

The [provider announcement](https://www.blog.fc.pff.com/blog/pff-fc-release-2022-world-cup-data) describes all **64** World Cup games, per-game {game_id}.jsonl.bz2 tracking, events.json, metadata/roster CSVs and PDF specifications. It directs users to complete an access form. A public exact-byte download and applicable data/label licence were not verified. No form was submitted and no account/contact action taken. A one-match licensed cohort, exact match ID and size therefore remain unpinned.

The [Kloppy PFF loader](https://github.com/PySport/kloppy/blob/a9651eba7c4dbbe2d2fc6d4cffb4aea63fadac11/kloppy/infra/serializers/tracking/pff.py), at commit **a9651eba7c4dbbe2d2fc6d4cffb4aea63fadac11**, uses frameNum, period and periodElapsedTime. It initializes DEAD and owner=None, changes state on game_event OUT/END versus kickoffs/OTB, and carries home_ball ownership forward. It does not read an independent dense state field. Kloppy's licence covers its software and cannot grant rights to PFF data.

**Adapter assessment (inference):** the frame clock is explicit, but the provider specification must establish complete transition coverage, ownership through passes/contests, missing-video treatment and out/restart conventions. Forward-filled event states are not independently verified per-frame GT. Access, licence and full-state semantics all remain unresolved. This route is not achievable within the current no-contact/no-asset scope.

## Operational conclusion

There is **no admissible fresh external evaluation cohort selected**. WCSF is the smallest concrete future acquisition candidate, subject to explicit data/label rights, reference provenance, coverage and non-overlap checks. Metrica and PFF remain rejected until their specific deficiencies are resolved. Continue using existing opened cohorts only as development material, without relabeling them fresh holdouts.

Access limitation: the web tool could not fetch several GitHub API pages; the connected GitHub read-only fetch successfully supplied repository/commit/tree metadata and loader source. Exact sizes above are repository metadata sizes, not verified downloaded/decompressed sizes. No binary availability, checksums beyond Git blob identifiers, actual state coverage or semantic quality was claimed from documentation alone.

