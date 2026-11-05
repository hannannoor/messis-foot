# Controlling Initial Challenge clarification

Recorded from the organiser clarification supplied by the participant on 5 November 2026. It takes precedence over earlier documentation, emails and individual answers. Earlier experiment instructions in this repository are historical wherever they conflict with this page.

## Organiser requirements

Not allowed:

- Checking algorithm output against the provided video.
- Hand labels, human-produced data or other manually created data on the provided game.
- Uploading the provided data to AI services.
- Training, fitting or calibrating on ground-truth possession data or the provided video.

Allowed:

- Automatic checks using only the provided data.
- Inspecting the provided data and video to understand what counts as possession.
- Using video, automatic tracking, smart tagging and other generated data as inputs, provided the algorithm was not trained on the ground truth or provided video.
- Providing intermediate-step files.
- Using external datasets with appropriate rights, after checking their licences.

Any training, retraining or parameter tuning must use external data, never challenge ground truth or the provided video. Running inference is distinct from fitting or tuning on those inputs.

This is a conditional requirement, not an instruction to train a model. A deterministic algorithm or an existing pretrained tool can run inference without a new training stage. External data need not be footage: appropriately licensed external tracking or other data may suit the component being trained or tuned. Synthetic fixtures check implementation behavior; they do not establish real-match accuracy.

## Consequences for this prototype

Keep provided footage, crops and tracking/tagging/homography data off AI services. Develop with synthetic fixtures or appropriately licensed external data; run challenge inference locally. Aggregate automatic diagnostics can explain execution and missing inputs, but higher assignment coverage on this game is not a parameter-selection objective or evidence of correctness.

Do not compare predictions to challenge video, annotate possession/replays/stoppages, hand-correct outputs or create manual frame correspondences. Earlier manual ROI selection, screenshot-derived crop presets and manually located playback ranges/anchors are historical experiments. Do not assume their resulting setup is eligible for a final entry. Replace match-specific manual setup with automatic processing designed and evaluated externally. The earlier 0.5 OCR-cutoff trial must not become a match-based optimisation loop; record parameter provenance and tune externally.

The fixed 2934-frame D interval comes from an earlier organiser answer. Its status under the newer ban on human-produced game data needs clarification before relying on it in a final entry. Keep its effect separate; the controlled report includes a stage without this interval. The clarification does not establish that this special-case label assignment is permitted.

The executable still includes historical manual ROI options and the earlier fixed D context. The 5 November `discover-clock` addition implements automatic full-recording clock-region discovery without those inputs. It does not yet supply dense alignment, half identity or replay verification, and does not certify a compliant final entry. Historical pilot counts establish neither eligibility nor accuracy.

Continue with code correctness checks, synthetic invariants and external validation. Evaluate automatic alignment, temporal replay filtering, longer-gap inference and general live/dead detection on external data before freezing a challenge-inference version. Automatic input processing does not permit fitting its parameters on the challenge game.
