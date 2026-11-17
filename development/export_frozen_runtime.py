"""Embed only the frozen portable model/policy and attribution, never match data."""
import json
from pathlib import Path
import pprint
from gap_solver.frozen_protocol import artifact_digest,load_frozen

code=Path(__file__).resolve().parent
root=code.parent/'external-reference'
artifact,manifest=load_frozen(root,code/'gap_solver')
heldout=json.loads((root/'reports'/'final-heldout.json').read_text(encoding='utf-8'))
if not heldout.get('complete') or heldout.get('artifact_sha256')!=manifest['artifact_sha256']:
    raise ValueError('Held-out evaluation is incomplete or belongs to a different model')
passed=all(summary['every_match_spell_f1_improved'] and summary['every_match_macro_f1_not_degraded']
           and summary['every_match_x_reduced'] and summary['newly_resolved_correct_fraction']>=.9
           for summary in heldout['summary'].values())
runtime=dict(schema_version=1,model=artifact['model'],policy=artifact['policy'],
             artifact_sha256=manifest['artifact_sha256'],
             model_policy_sha256=artifact_digest(dict(model=artifact['model'],policy=artifact['policy'])),
             externally_heldout_validated=passed,
             reference_type=artifact['reference_type'],training_matches=artifact['training_matches'],
             validation_matches=artifact['validation_matches'],test_matches=artifact['test_matches'],
             citation=artifact['citation'],license=artifact['license'],leaf_support_is_calibrated_probability=False,
             heldout_summary=heldout['summary'],
             validation_limitations=[
                 'Experimental provider-reference agreement, not challenge accuracy or cross-provider validation.',
                 'External inactive ball coordinates repeat the previous frame on 99.9993% of contiguous inactive frames; motion features can exploit this provider convention.',
                 'Newly resolved H/A agreement is 86.36%/88.95%; pooled 96.32% agreement is dominated by D.',
                 'Active-only diagnostic spellF1 slightly regressed on both held-out matches; conditional team accuracy and one home-share estimate also regressed.',
                 'Finite ball coordinates do not establish a fresh physical observation.'])
if not passed:
    raise ValueError('Frozen model did not pass declared final held-out safeguards; refusing production export')
text='"""Frozen external-reference model, CC BY 4.0 attribution below. No challenge fitting."""\n\n'
text+='FROZEN_MODEL = '+pprint.pformat(runtime,width=110,sort_dicts=False)+'\n'
(code/'gap_solver'/'tactical_model.py').write_text(text,encoding='utf-8')
print('Exported frozen standard-library runtime model:',runtime['artifact_sha256'])
