"""Label-free ball-out rule (v10 candidate): a ball observed more than 1 m outside a touchline or goal line is dead.

D also continues through the ball-tracking gap that directly follows (the ball went out, then left the camera's view).
When the ball comes back onto the pitch while still being tracked (a throw-in or a kick taken from outside the line),
D is released 0.4 s before it re-enters, because play restarts while the ball is still just outside.
Pitch: 0..105.3 x 0..68 m, as every adapter and the provided match use. No labels, no constants tied to the match.
Checked on external data only (round 11 design note): SkillCorner +0.022 (17/17), WCSF +0.004, DFL -0.002.
"""
L, W = 105.3, 68.0
MARGIN = 1.0      # metres outside the line
RELEASE = 10      # frames (0.4 s at 25 Hz) released before a tracked re-entry


def apply_ball_out(frames, labels):
    labels = list(labels)
    n = len(frames)
    if len(labels) != n:
        raise ValueError('labels and frames differ in length')
    seen = [bool(f.ball_observed) for f in frames]
    out = [seen[i] and frames[i].period in (1, 2) and (frames[i].ball_x < -MARGIN or frames[i].ball_x > L + MARGIN
                                                      or frames[i].ball_y < -MARGIN or frames[i].ball_y > W + MARGIN)
           for i in range(n)]
    i = 0
    while i < n:   # tracked re-entry: release D before the ball comes back in
        if not out[i]:
            i += 1
            continue
        j = i
        while j < n and out[j]:
            j += 1
        if j < n and seen[j] and frames[j].period == frames[i].period:
            for k in range(max(i, j - RELEASE), j):
                out[k] = False
        i = j
    for i in range(n):
        if not out[i]:
            continue
        labels[i] = 'D'
        j = i + 1
        if j < n and not seen[j] and frames[j].period == frames[i].period:
            while j < n and not seen[j] and frames[j].period == frames[i].period:
                labels[j] = 'D'
                j += 1
    return labels
