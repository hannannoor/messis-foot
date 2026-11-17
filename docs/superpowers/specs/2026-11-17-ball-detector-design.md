# Ball detector on the tactical video (round 12)

17 November 2026, evening. Branch: new `experiment/ball-detector` (code), data outside every repository. The
submitted file is untouched until the user decides.

## Why

The provided tracking has the ball on 58% of active frames. Every external check this week says the missing ball is
where the points are: the gap rule (built on ball absence) is our largest single decision, and the two strongest
public entries both rebuilt the ball themselves (Matra raised ball availability from 58% to 66% with a YOLO detector
on the tactical video). Our models already work on missing-ball frames from team shape, but a real ball position is
far stronger evidence for who has it.

## Goal

Recover the ball on as many of BAR–ATH's missing-ball frames as possible, accurately, and use it to build a v11
candidate that the user can choose to submit.

## Non-goals

- No change to the models, features or decoder settings beyond feeding the extra ball positions.
- No broadcast video (not aligned to the tracking; no mapping provided).
- No 3-D ball height; positions are ground projections.

## Anti-goals (failure even if it "works")

- Any human label, correction or threshold tied to frames of the provided match.
- Any frame, crop or raw row of the provided data entering a hosted model's context (competition terms). Only
  aggregate statistics are printed.
- Weakening the gap rule: if detected balls fill stoppage gaps, the rule stops calling them dead. The gap rule must
  keep seeing the provider's original ball absence.
- Shipping a detector whose accuracy was never measured.

## Constraints

- Laptop RTX 4050 (6 GB), about 2–3 hours of compute tonight; deadline 17 November (organisers, no time zone given).
- Packages installed with the user's approval: ultralytics 8.4.201, opencv-python 4.12.0.88 (PyTorch-GPU env,
  Python 3.9); weights `yolo26n.pt` from Ultralytics' releases.
- Video: 1920×1080, exactly 25 fps, 199,319 frames, frame n = tracking frame n. Homography: one matrix per frame,
  normalised pitch → pixels; inverse gives pitch metres (×105.3, ×68, as the tracking loader).
- The ball is about 6 px across (median; p10 4.7, p90 8.2).

## Approaches considered

| Approach | Trade-off | Decision |
|---|---|---|
| Train on public datasets (ISSIA, SoccerTrack v2, SoccerNet, Roboflow) | No tactical-view set with per-frame ball labels; ISSIA is non-commercial only; SoccerTrack v2 needs an account and 14 GB per match, ball only at events; different camera | rejected |
| Off-the-shelf ball detectors (WASB, FootAndBall, Roboflow YOLO) | Trained on ISSIA/broadcast, unclear licences, domain gap | rejected |
| **Self-training on the provided video: the provider's tracked ball, projected with the provided homography, labels the frames where it exists; the detector then finds the ball where tracking lost it** | Perfect domain match, no downloads beyond the model, allowed by the rules ("pseudo-labels produced by an algorithm, provided no person decided any of them"); labels inherit tracking error and miss balls in the air (ground projection) | **chosen** |

Model: YOLO26 nano with the extra stride-4 (P2) small-object head, from COCO weights, trained on 384 px native-resolution
crops (user asked for the fastest path; small model chosen over `s` for speed).

## Design

1. **Labels** (`ball-detector/make_pseudo.py`): tracked-ball frames → pixel via homography; 384 px crops with the ball
   off-centre (±140 px), box side 1.6 × apparent diameter; 9,000 positive and 1,500 empty training crops; 1,500
   validation crops. Split by 30 s blocks: every 5th block is held out (validation and the accuracy check).
2. **Training**: 45-minute budget, early stopping (patience 15), batch 32, mosaic, scale ±25%, horizontal flips, colour
   jitter, no rotation.
3. **Inference** (`infer_video.py`): full 1920×1080 frames at native resolution; frames where the tracking has no ball,
   plus the held-out tracked frames for the check; top-3 candidates per frame; several processes by frame range.
4. **Clean-up** (`postprocess.py`): one ball per frame, maximum 40 m/s between kept detections, minimum confidence,
   reject detections far off the pitch.
5. **Accuracy check** (`selfcheck.py`), on held-out tracked frames only: detection rate and median / p90 error in
   metres against the provider's ball. Gate: median error ≤ 1 m and at most 5% of detections more than 3 m off.
6. **Integration (v11)**: missing-ball frames with an accepted detection get `ball_x/ball_y` from the detector for
   **feature computation and the models**; the gap rule, its stoppage decisions and the ball-out rule use the
   **original** tracking (ball absence unchanged). Then the release decoder, kickoff patch and ball-out rule as v10.
7. **Decision**: v11 cannot be scored on external data (no external match has tactical video and labels). Evidence
   offered to the user: the accuracy check, how many frames gain a ball, how many labels change against v10, and
   whether the changes concentrate in live play. The user decides between v10 and v11.

## Left to the builder

Confidence threshold and the exact clean-up limits (set on held-out tracked frames only); whether to run every frame
or every second frame with interpolation (decided by measured inference speed); process count.

## Result (17 November, 23:05) — fails the accuracy gate; not used for a candidate

- First run (raw projected labels): validation mAP50 0.04. Brightness statistics (no frames viewed) showed the
  projected tracked ball is right in time (offset 0) and axes, but a few pixels off a 6 px ball, with a systematic
  3 px upward offset (ground point vs ball centre).
- Second run (labels shifted 3 px up and snapped to the brightest compact blob within 5 px): validation precision 0.72,
  recall 0.55, mAP50 0.61 (best epoch 17 of 30). Inference 31 frames/s on full 1080p frames (RTX 4050).
- Full held-out frames (800 random, against the provider's ball): median error 0.7–0.9 m, but 14–26% of detections
  more than 3 m off (median 14.8 m), mostly moving, 13% on a penalty or centre spot, 21% near a touchline.
- Six whole held-out 30 s blocks: temporal support filters change little (>3 m share 25–33%). A reachability filter
  (within 30 m/s of the last tracked ball) looked like 1.3% but only because the last tracked ball was usually one
  frame earlier; with realistic time since the last tracked ball (median 12.1 s on real missing frames, 56% over 10 s)
  the >3 m share stays 17–27%.
- Gate (≤ 5% beyond 3 m) failed under realistic conditions. No v11 built. Next if continued: hard negatives mined
  automatically, a larger model, longer training; and a reproducible CPU inference path.

## Result 2 (18 November, 00:35) — hard negatives help a little; still fails; v10 stays

Fine-tune from the snapped-label model with 1,243 automatically mined hard negatives (confident detections more than
3 m from the tracked ball on training-block frames), 23 epochs: validation mAP50 0.585 (best epoch 11). Full held-out
frames (800): detections more than 3 m off 17.3% / 16.5% / 13.6% at confidence 0.2 / 0.3 / 0.5 (before: 20.0% /
18.5% / 14.4%); p90 error at 0.2 fell from 10.4 m to 5.7 m; median 0.65–0.67 m. The 5% gate is still far away, so no
v11 was built. Some of the remaining "errors" may be the provider's tracked ball being wrong rather than the detector;
without labelled video of another match this cannot be separated.
