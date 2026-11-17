"""One fixed missing-ball intervention; no reference inputs or learned parameters."""
from gap_solver.soft_sequence import soft_emissions,decode_soft

POLICY_ID='w0-c32-neutral-missing'


def decode_ball_gap(supports,periods,usable,observed):
    n=len(periods)
    if any(len(v)!=n for v in (supports,usable,observed)):
        raise ValueError('Ball-gap input dimensions differ')
    if any(type(v) is not bool for v in (*usable,*observed)):
        raise ValueError('Availability and usability must be explicit bool flags')
    if any(p not in (0,1,2) for p in periods):raise ValueError('Invalid period')
    rows=soft_emissions(supports,[0.]*n,0.)
    rows=[row if available else (0.,0.,0.) for row,available in zip(rows,observed)]
    effective=list(usable);segments=unsupported=0;i=0
    while i<n:
        if not periods[i] or not usable[i]:i+=1;continue
        first=i;period=periods[i]
        while i<n and periods[i]==period and usable[i]:i+=1
        if not any(observed[first:i]):
            segments+=1;unsupported+=i-first
            effective[first:i]=[False]*(i-first)
    labels=decode_soft(rows,periods,effective,32.)
    return labels,dict(neutral_active_usable_rows=sum(bool(p and u and not o) for p,u,o in zip(periods,usable,observed)),
        unsupported_segments=segments,unsupported_active_rows=unsupported)
