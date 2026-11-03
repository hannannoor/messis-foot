# Missing-ball handling implementation plan

**Goal:** implement and verify a conservative, explainable gap layer before match assets arrive.

**Architecture:** feature extraction, control confirmation, bounded gap resolution, then local diagnostics. Python 3.9+, standard library only.

**Spec:** DESIGN.md

1. Write synthetic behaviour tests for occlusions, deflections, real turnovers, conflicting anchors, long gaps, restarts, D evidence, half resets and impossible interpolation. Observe failures before implementation.
2. Implement `Frame`, `Config`, `Decision`, `infer`, `interpolate_ball` and summary/interval exports in `gap_solver/core.py`.
3. Test and implement raw ATD metadata/coordinates and SportsCode phase mapping in `gap_solver/io.py`; fail on counter/slot mismatches.
4. Add CLI evidence/demo/match commands and test exported files end to end. Never access the supplied public labels in tests or demos.
5. Document local execution, provisional defaults and the absent live/dead classifier. Run the whole suite, demo and official submission validator; package the source and synthetic outputs.
