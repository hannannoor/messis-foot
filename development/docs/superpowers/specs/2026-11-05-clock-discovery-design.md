# Automatic clock discovery

## Intent and scope

Continue the authorised camera-setup work without manual crops, selected playback anchors or training on the challenge game. The first deliverable is a local `camera discover-clock` command. It scans the entire video at a fixed interval, locates clock-shaped text anywhere in each sampled image and reports spatially stable progressing-clock segments. It does not yet generate a dense timing map or feed fusion. Its output is an automatic intermediate input for that next step, not live-footage verification, a possession label or a submission.

## Approaches and decision

1. Full-frame sparse OCR with pretrained Tesseract: reuses installed tools, requires no new training and has no match-specific crop coordinates. Chosen by the implementer under the user's instruction to carry on.
2. Tracking-only synchronization: avoids OCR but needs a new temporal scene-search subsystem, with weak evidence when both balls are absent. Deferred.
3. Train a clock detector externally: potentially stronger localization but adds dataset/licence/model-distribution work. Not required by the organiser rules and deferred.

## Behavior and constraints

- Python 3.9+, standard library, existing local FFmpeg/ffprobe/Tesseract. One standalone source file remains the Windows interface.
- Stream grayscale PGM samples through memory; do not export a video/frame collection. Preserve original decoded indices: decode errors are fatal and the complete decoded frame count is checked before any report is accepted. Protect the source video and path aliases from output overwrite. Default sample interval 30 seconds, minimum OCR score 0.7; engineering defaults, not match-tuned or calibrated correctness probabilities.
- Parse full-frame TSV boxes, including adjacent split clock tokens. Exclude scorelines, malformed/confidence-invalid/out-of-bounds detections. Keep distinct clock candidates rather than choosing a region based only on confidence.
- A segment needs at least three readings. Accepted readings must share at least 0.5 box IoU with both the previous and first boxes and progress within one second of elapsed video time. Allow at most one missed scheduled sample. Reject non-unique spatial correspondences; freezes, resets and overlay moves split tracks. A split stoppage clock is one observation, including its prefix confidence. These fixed rules are not real-data accuracy claims.
- Report all candidates and accepted segments in one overwritten JSON file. Missing prefixes/halftime, duplicate progressing clocks and absent clocks are legitimate output states. No half is invented and no interpolation/extrapolation is exported.
- Emit `ready_for_fusion: false`, `live_verified: false`, parameter provenance and counts. The old fusion route and inference thresholds remain unchanged.
- No challenge assets are processed here. Tests use generated images/video and synthetic TSV/clock histories. A matching live clock on replay remains a known limitation.

## Verification

Test full-frame parsing, token spacing, split digits, invalid boxes/confidence, chronological validation, one-miss versus long-gap splitting, freezes/resets, duplicate candidates, moved overlays, exact stream sample indices, corrupt/truncated PGM, missing tools, no-clock success and actual FFmpeg/Tesseract CLI execution on a generated video. Verify standalone source parity and the existing complete suite.
