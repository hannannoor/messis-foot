# Automatic synchronization stage

This continues the automatic setup in Plan Data Analysis Variables. It uses the existing sparse discovery reports to select processing windows and clock boxes, then runs local dense OCR with the existing .7 confidence cutoff, five-frame sampling and .25-second timing limit. Sparse interpolation chooses processing bounds only; it never supplies dense timestamps. No possession predictions, training, calibration or tuning are performed.

OCR uses the pre-existing fixed camera-polarity, 12-pixel border and weak-read retry recipe. Its in-memory implementation is checked byte-for-byte against the original FFmpeg preprocessing on generated PGM images. No treatment or cutoff is selected to increase challenge coverage.

Run the updated single-file program in the existing football environment:

```powershell
python football_pipeline.py camera auto-sync --tactical-video "C:\football-data\tactical cam\BAR-ATH_tactical.mp4" --broadcast-video "C:\football-data\broadcast cam\BAR-ATH_broadcast.mp4" --tactical-discovery outputs/tactical-discovery.json --broadcast-discovery outputs/broadcast-discovery.json --out outputs/automatic-sync
```

The output folder must be empty or contain only a previous automatic-sync generation. The command rejects unrelated existing files, source aliases and the same camera supplied twice. It builds both cameras in a temporary local directory, checks complete decoder counts and replaces the output directory as a complete generation. A failed replacement restores the previous generation.

Published tactical evaluation half windows supply structural reference metadata. Broadcast continuous match clocks below 45 minutes and explicit `45+`/`90+` notation carry half information. Ordinary clocks at or beyond 45 minutes remain ambiguous in this stage: missing sparse first-half coverage is never treated as proof of the second half. This deliberately leaves some usable footage unprocessed until an independent automatic period anchor exists.

Each OCR sample uses its active discovered clock region, including when the overlay moves. Decoder crops and OCR inputs stay in memory. No video frames or crops are displayed to an AI service, and no visual prediction check occurs.

Outputs are original-length tactical and broadcast clock CSVs, raw local OCR readings, candidate alignment and sync-report.json. Bounded timing, consistent geometry and progressing clocks remain insufficient to prove live footage. `live_verified`, `ready_for_fusion` and `accuracy_measured` remain false. Do not treat these intermediate files as a validated final submission.

The separate local aggregate audit checks tracking/homography dimensions, ball availability, camera geometry and three-time-point geometry concurrence without changing possession decisions. Count mismatches are reported; rows are never shifted, padded or trimmed to conceal them.
