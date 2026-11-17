"""Score development/validation baseline only. Never opens final test targets."""
from collections import Counter
import json
from pathlib import Path
import numpy as np
from gap_solver.external import load_cache
from gap_solver.benchmark import evaluate_external
from gap_solver.core import infer,summary
from gap_solver.audit import bridge_diagnostics


root=Path(__file__).resolve().parent.parent/'external-reference'
provenance=json.loads((root/'provenance.json').read_text(encoding='utf-8'))
results={}
for split in ('development','validation'):
    results[split]={}
    for match in provenance['split'][split]:
        data=load_cache(root/'cache'/match)
        frames=data.frames()
        decisions=infer(frames)
        prediction=np.array(['HADX'.index(d.label) for d in decisions],dtype=np.uint8)
        report=evaluate_external(data.reference,prediction,data.periods)
        report['baseline_summary']=summary(frames,decisions)
        report['gap_diagnostics']=bridge_diagnostics(frames,decisions)
        report['wrong_decided_by_reference']=dict(Counter('HADX'[int(g)]+'->'+d.label for g,d in zip(data.reference,decisions) if g<3 and d.label!='X' and d.label!='HADX'[int(g)]))
        results[split][match]=report
        print('{} {}: spellF1={:.4f}; macroF1={:.4f}; X={:.2%}; decided correctness={}'.format(
            split,match,report['metrics']['spell_f1_mean'],report['metrics']['macro_f1'],
            report['coverage']['undecided_fraction'],report['coverage']['decided_correct_fraction']),flush=True)
destination=root/'reports'
destination.mkdir(exist_ok=True)
(destination/'baseline-development-validation.json').write_text(json.dumps(results,indent=2)+'\n',encoding='utf-8')
print('Saved external baseline and error diagnostics; final test references remain unscored.',flush=True)
