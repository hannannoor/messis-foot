"""Explicit scorer-style carry control using structural periods, never reference masks."""


def materialize_abstentions(labels,periods):
    if len(labels)!=len(periods) or any(v not in ('H','A','D','X') for v in labels) or any(p not in (0,1,2) for p in periods):
        raise ValueError('Invalid materialization labels/periods')
    result=list(labels);i=0
    while i<len(result):
        if not periods[i]:i+=1;continue
        first=i;period=periods[i]
        while i<len(result) and periods[i]==period:i+=1
        stop=i;known=next((j for j in range(first,stop) if result[j]!='X'),None)
        # D for a wholly unknown block preserves zero predicted H/A spells.
        # It is a scoring convention, not independently observed dead-ball evidence.
        current=result[known] if known is not None else 'D'
        for j in range(first,stop):
            if result[j]=='X':result[j]=current
            else:current=result[j]
    return result
