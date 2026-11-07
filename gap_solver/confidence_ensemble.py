"""Explicit diagnostic hard-label combinations; agreement is not a probability."""
from .core import Decision


def aggregate_decisions(frames,baseline,temporal,raw,supported):
    inputs=(baseline,temporal,raw,supported)
    if any(len(values)!=len(frames) for values in inputs):raise ValueError('Ensemble dimensions disagree')
    if any(d.label not in ('H','A','D','X') for values in inputs for d in values):raise ValueError('Invalid ensemble label')
    result={name:list(baseline) for name in ('gated_plus_raw_HAD','head_agreement_on_X','supported_head_agreement_on_X')}
    for i,(frame,base,t,r,s) in enumerate(zip(frames,*inputs)):
        if base.label!='X' or not frame.period:continue
        if r.label in ('H','A','D'):result['gated_plus_raw_HAD'][i]=Decision(r.label,'diagnostic_raw_fallback','unsupported_estimate')
        if t.label==r.label and t.label in ('H','A'):
            result['head_agreement_on_X'][i]=Decision(t.label,'diagnostic_head_agreement','unsupported_estimate')
        if t.label==s.label==r.label and s.label in ('H','A'):
            result['supported_head_agreement_on_X'][i]=Decision(s.label,'diagnostic_supported_agreement','unsupported_estimate')
    return result
