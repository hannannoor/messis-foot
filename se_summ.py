"""Summarise scores2 json: python se_summ.py <dir-name> [stage]  -> provider-weighted mean per cfg
Default stage is the submitted decoder ('gapko', v9). Files scored before v9 lack it: rescore with se_score2.py."""
import json, sys
from pathlib import Path
import numpy as np
import se_load
d = se_load.PRIVATE / 'scores2' / sys.argv[1]; stage = sys.argv[2] if len(sys.argv) > 2 else 'gapko'
by = {}
for f in sorted(d.glob('*.json')):
    for cfg, v in json.loads(f.read_text()).items():
        if stage in v:
            by.setdefault(cfg, {}).setdefault(se_load.provider(f.stem), {})[f.stem] = v[stage]
if not by:
    print(f'no "{stage}" scores in {d.name}: rescore with se_score2.py or pass an older stage (nogap, final)')
for cfg, m in by.items():
    pm = {p: round(float(np.mean(list(x.values()))), 4) for p, x in m.items()}
    print(sys.argv[1], cfg, round(float(np.mean(list(pm.values()))), 4), pm, sum(len(x) for x in m.values()))
