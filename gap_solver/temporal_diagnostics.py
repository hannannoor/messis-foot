"""Reference-free eligibility denominators, reported independently of model confidence."""
from collections import Counter
from .temporal import anchor_context,_points


def eligibility_diagnostics(frames,baseline,policy):
    policy.validate()
    if len(frames)!=len(baseline):raise ValueError('eligibility dimensions disagree')
    left,right,_=anchor_context(frames);barriers=[0]
    for f,d in zip(frames,baseline):barriers.append(barriers[-1]+int(not f.period or not f.geometry_valid or d.label=='D'))
    reasons=Counter();unknown=0
    for i,(f,d) in enumerate(zip(frames,baseline)):
        if d.label!='X':continue
        unknown+=1;a,b=left[i],right[i]
        if not f.period:reason='unknown_structural_period'
        elif not f.geometry_valid:reason='invalid_geometry'
        elif min(len(_points(f,'home')),len(_points(f,'away')))<policy.minimum_players:reason='insufficient_players'
        elif a<0 or b<0:reason='missing_two_sided_control_anchors'
        elif max(b-a-1,0)/25>policy.max_gap_s:reason='anchor_span_exceeds_cap'
        elif barriers[b+1]!=barriers[a]:reason='dead_or_invalid_geometry_barrier'
        else:reason='eligible_before_confidence'
        reasons[reason]+=1
    return dict(baseline_unknown_rows=unknown,reasons=dict(reasons),reference_used=False,policy=policy.__dict__)
