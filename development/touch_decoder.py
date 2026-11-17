"""Three-state decoder with per-frame costs for entering each state."""
from math import isfinite


def validate_rows(emissions,periods,usable,costs):
    n=len(periods)
    if any(len(v)!=n for v in (emissions,usable,costs)):raise ValueError('Invalid decoder dimensions')
    if any(type(p) is not int or p not in (0,1,2) for p in periods):raise ValueError('Invalid decoder periods')
    if any(type(u) is not bool for u in usable):raise ValueError('Explicit usability flags required')
    for rows,nonnegative in ((emissions,False),(costs,True)):
        if any(len(r)!=3 or not all(isinstance(v,(int,float)) and isfinite(v) and (not nonnegative or v>=0) for v in r) for r in rows):
            raise ValueError('Invalid decoder emissions/costs')


def decode_variable(emissions,periods,usable,costs):
    validate_rows(emissions,periods,usable,costs)
    n=len(periods);result=['X']*n;back=[bytearray(n) for _ in range(3)];i=0
    while i<n:
        if not periods[i] or not usable[i]:i+=1;continue
        first=i;period=periods[i];previous=(0.,0.,0.)
        while i<n and periods[i]==period and usable[i]:
            row=emissions[i];values=[]
            for state in range(3):
                cost=costs[i][state]
                a=previous[0]-(cost if state!=0 else 0.)
                b=previous[1]-(cost if state!=1 else 0.)
                c=previous[2]-(cost if state!=2 else 0.)
                chosen=0 if a>=b and a>=c else (1 if b>=c else 2)
                back[state][i]=chosen;values.append((a,b,c)[chosen]+row[state])
            normal=max(values);previous=tuple(v-normal for v in values)
            if not all(isfinite(v) for v in previous):raise ValueError('Decoder overflow')
            i+=1
        a,b,c=previous;state=0 if a>=b and a>=c else (1 if b>=c else 2)
        for j in range(i-1,first-1,-1):result[j]='HAD'[state];state=back[state][j]
    return result
