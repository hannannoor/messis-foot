# Ball Detector (v11 candidate) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Detect the ball in BAR–ATH's tactical video where the provided tracking lost it, measure the detector's accuracy label-free, and build a v11 candidate that uses detected balls for the models only.

**Architecture:** A YOLO26-nano P2 detector trained on pseudo-labels (provider's tracked ball projected through the provided homography) runs on missing-ball frames; a track builder turns candidates into one pitch-space ball per frame; the release fills those balls into a copy of the frames used for features and models, while the decoder, gap rule and ball-out rule keep the original frames.

**Tech Stack:** Python 3.9 (PyTorch-GPU env: torch 2.8.0+cu128, ultralytics 8.4.201, opencv-python 4.12.0.88) for detection; CPython 3.14.5 + numpy 2.5.1 for the release; unittest.

**Spec:** `docs/superpowers/specs/2026-11-17-ball-detector-design.md`

## Global Constraints

- No frame, crop, image or raw data row of the provided match is printed, read into a model's context or committed; scripts print aggregate counts only.
- No human label, correction or constant tied to frames of the provided match; thresholds are set on held-out tracked frames only (every 5th 30 s block, `split.npz` → `held`).
- Pitch frame: 0..105.3 × 0..68 m; homography rows map normalised pitch → pixels; pixel → pitch is `inv(H[f])`, then ×105.3, ×68.
- Video frame n = tracking frame n (199,319 frames, 25 fps). Ball diameter ≈ 6 px (p10 4.7, p90 8.2).
- The gap rule, ball-out rule and decoder use the provider's original frames; detected balls feed features and models only.
- Accuracy gate: median error ≤ 1.0 m and ≤ 5% of detections more than 3.0 m off, on held-out tracked frames.
- Reproduction rule (organisers): the public repo must regenerate the same file. Detection results are derived match data and are never committed; the release must recompute them.
- `final-submission/` is changed only on the user's decision.

## Review Focus

- A detection in the stands or on a spare ball by the touchline: expect it dropped (outside pitch +3 m) or out-voted by the track's speed limit. Test in Task 3.
- A missing-ball run during a stoppage where the detector finds the ball: the gap rule must still mark it D (it reads original frames). Test in Task 4.
- Frames outside the halves (period 0): never filled. Test in Task 4.
- A frame where the tracking has the ball: never overwritten by a detection. Test in Task 4.
- GPU vs CPU inference giving slightly different candidates: the release must use one fixed, documented inference path. Decision in Task 2, check in Task 5.

---

### Task 1: Finish training and export

**Files:**
- Use: `ball-detector/train.py` (running, run `n_p2_384`)
- Create: `ball-detector/runs/ball/n_p2_384/weights/best.pt` (by training), `best.onnx`

**Interfaces:**
- Produces: `best.pt`, `best.onnx` (opset 17, input 1×3×1088×1920, dynamic off)

- [ ] **Step 1:** Wait for training to end (45 min budget or early stop). Record final val precision, recall, mAP50 from `results.csv` (aggregate numbers only).
- [ ] **Step 2:** Export: `YOLO(best.pt).export(format='onnx', imgsz=(1088,1920), opset=17, simplify=False)`. Expected: `best.onnx` written.
- [ ] **Step 3:** Gate: val recall ≥ 0.7 at conf 0.25. If below, retrain 30 min more with `--resume` before continuing.

### Task 2: Inference speed and path decision

**Files:**
- Use: `ball-detector/infer_video.py`
- Create: `ball-detector/bench/` (detections of 3,000 held-out frames)

- [ ] **Step 1:** GPU benchmark: `infer_video.py --video <tactical.mp4> --weights best.pt --out bench/gpu --start <first held-out block start> --end +3000 --conf 0.05 --topk 3`. Record fps.
- [ ] **Step 2:** CPU benchmark with `best.onnx` (onnxruntime CPU, 6 threads) on the same 3,000 frames. Record fps and the share of top-1 candidates that differ from GPU by > 1 px.
- [ ] **Step 3:** Decide and write the decision into the spec: CPU-ONNX in the release if it covers the target frames (Task 3) in ≤ 60 min; otherwise GPU, and the technical document states that reproduction needs the same GPU path (risk flagged to the user).

### Task 3: Run detection and build the ball track

**Files:**
- Create: `development/detected_ball.py` (repo `repo-cleanup`, branch `experiment/ball-detector` from `candidate/ball-out-rule`)
- Test: `development/tests/test_detected_ball.py`

**Interfaces:**
- Consumes: detection rows `(frame:int, u:float, v:float, conf:float)`, homographies `H: ndarray (n,3,3)`
- Produces:
  - `to_pitch(H: ndarray, frames: ndarray, u: ndarray, v: ndarray) -> tuple[ndarray, ndarray]` (metres)
  - `build_track(frames, x, y, conf, *, min_conf=0.25, vmax=40.0, link_gap=12, margin=3.0) -> dict[int, tuple[float, float]]`

- [ ] **Step 1: Write failing tests**

```python
def test_to_pitch_inverts_projection():   # H from a known pitch->pixel map; pixel of (52.65, 34) maps back within 1e-6 m
def test_build_track_drops_off_pitch():    # candidate at x=-5 m (beyond margin 3 m) -> not in track
def test_build_track_speed_limit():        # frames 10,11 at 0 m and 30 m apart (750 m/s) -> only one kept
def test_build_track_low_conf_dropped():   # conf 0.2 < 0.25 -> absent
```

- [ ] **Step 2:** Run `python -m unittest tests.test_detected_ball -v` from `development/`. Expected: FAIL (module missing).
- [ ] **Step 3:** Implement both functions in `development/detected_ball.py` (numpy only, CPython 3.14). `build_track`: keep the top candidate per frame above `min_conf` and inside the pitch ± `margin`; drop any kept point whose speed to the previous kept point (within `link_gap` frames) exceeds `vmax`; no interpolation.
- [ ] **Step 4:** Run tests. Expected: PASS.
- [ ] **Step 5:** Run detection on the target frames with the path chosen in Task 2: all active frames where the tracking has no ball, plus all held-out tracked frames (for Task 4's check). Several processes by frame range. Print counts only.
- [ ] **Step 6:** Commit (`development/detected_ball.py`, test). Detections stay in `ball-detector-data/` (never committed).

### Task 4: Accuracy check and integration

**Files:**
- Modify: `development/detected_ball.py` (add `fill_frames`), `strong_release.py` (fill before features), `development/strong_runtime.py` (`DETECTED_BALL = True`)
- Create: `ball-detector/check_track.py` (accuracy gate)
- Test: `development/tests/test_detected_ball.py`

**Interfaces:**
- Produces: `fill_frames(frames: list[MotionFrame], track: dict[int, tuple[float, float]]) -> list[MotionFrame]` — returns a new list; frames with a provider ball or period 0 are returned unchanged; others get `ball_x, ball_y`, recomputed `home_distance, away_distance` (nearest player), `ball_provenance='detector'`.

- [ ] **Step 1:** Accuracy check (`check_track.py`): on held-out tracked frames, compare `build_track` positions to the provider ball. Print detection rate, median and p90 error (m), share > 3 m. Gate from Global Constraints; if it fails, raise `min_conf` in steps of 0.05 (held-out frames only) until it passes or report failure.
- [ ] **Step 2: Write failing tests**

```python
def test_fill_never_overwrites_provider_ball():   # frame with ball_x=10 keeps 10 when track has (50, 30)
def test_fill_skips_period_zero():                # period 0 frame stays unobserved
def test_fill_sets_distances():                   # home player at 1 m -> home_distance == 1.0
def test_gap_rule_uses_original_frames():         # release path: assemble() receives the original frame list (monkeypatched assemble records its argument)
```

- [ ] **Step 3:** Run tests. Expected: FAIL.
- [ ] **Step 4:** Implement `fill_frames` with `dataclasses.replace`. In `strong_release.generate`: build `feat_frames = fill_frames(frames, track)` when `strong_runtime.DETECTED_BALL`; compute `feature_rows`, `se_features.build` and the extra feature blocks on `feat_frames`; pass the original `frames` to `assemble` and `apply_ball_out`. The track comes from running the detector inside the release (path from Task 2).
- [ ] **Step 5:** Run all tests (`python -m unittest discover tests` from `development/`, plus the new file). Expected: new tests PASS, no new failures.
- [ ] **Step 6:** Commit.

### Task 5: Build v11 and compare with v10

**Files:**
- Create: `MESSI's FOOT/v11-detector-candidate/out/submission.csv` (outside the repo)

- [ ] **Step 1:** Run the release from the branch into `v11-detector-candidate/out`. Expected: 199,319 rows, format check passes.
- [ ] **Step 2:** Run it a second time; expected byte-identical (same machine, same inference path).
- [ ] **Step 3:** Compare with v10 (`c86cf7ee…`), counts only: frames that gained a ball, labels changed, changes by previous label (H/A/D), share inside graded frames, number of possession spells (X forward-filled) before and after.
- [ ] **Step 4:** Record results in the design doc ("Result" section) and commit.

### Task 6: Decision handoff

- [ ] **Step 1:** Report to the user: accuracy gate result, frames gained, labels changed, reproduction path and its risk, and that no external match can score the change. Recommend v10 or v11 with the reason.
- [ ] **Step 2:** On the user's choice only: copy the file into `final-submission/` (previous kept), refresh `form-upload/`, fast-forward `main`, rebuild from a fresh clone, update the technical document and PDF.
