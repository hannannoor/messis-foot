"""Reference-free complete H/A/D segment optima and post-inference queries."""
from dataclasses import dataclass
from math import isclose, isfinite

ABS_TOL = 1e-6
REL_TOL = 1e-10


def _best(values):
    a,b,c = values
    return 0 if a >= b and a >= c else (1 if b >= c else 2)


def _finite(values):
    if not all(isfinite(value) for value in values):
        raise ValueError('Nonfinite path arithmetic')


def _validated(emissions, switch_cost):
    try:
        cost = float(switch_cost)
        rows = tuple(tuple(float(value) for value in row) for row in emissions)
        if type(switch_cost) is bool or not isfinite(cost) or cost < 0 or not rows or any(len(row)!=3 for row in rows):
            raise ValueError('Invalid path dimensions or switch cost')
        for row in rows: _finite(row)
    except (TypeError,OverflowError) as error:
        raise ValueError('Invalid path values') from error
    return rows,cost


@dataclass(frozen=True)
class PathTables:
    emissions: tuple
    switch_cost: float
    forward: tuple
    backward: tuple
    forward_emissions: tuple
    backward_emissions: tuple
    forward_switches: tuple
    backward_switches: tuple
    labels: tuple
    score: float
    exact_ties: int


def path_tables(emissions, switch_cost=32.0):
    rows,cost = _validated(emissions,switch_cost)
    n=len(rows); forward=[]; fe=[]; fs=[]; predecessors=[]; ties=0
    offset=max(rows[0]); previous=tuple(value-offset for value in rows[0]); _finite(previous)
    forward.append(rows[0]);fe.append(rows[0]);fs.append((0,0,0));predecessors.append((0,1,2))
    for i in range(1,n):
        values=[]; emissions_sum=[]; switches=[]; back=[]
        for state in range(3):
            options=tuple(previous[k]-(cost if k!=state else 0.) for k in range(3))
            chosen=_best(options);ties+=sum(value==options[chosen] for value in options)>1
            values.append(options[chosen]+rows[i][state]);back.append(chosen)
            emissions_sum.append(fe[-1][chosen]+rows[i][state])
            switches.append(fs[-1][chosen]+int(chosen!=state))
        normal=max(values);offset+=normal;previous=tuple(value-normal for value in values)
        absolute=tuple(value+offset for value in previous)
        _finite((*previous,*absolute,*emissions_sum,offset))
        forward.append(absolute);fe.append(tuple(emissions_sum));fs.append(tuple(switches));predecessors.append(tuple(back))
    state=_best(previous);ties+=sum(value==previous[state] for value in previous)>1
    score=forward[-1][state]; labels=['']*n
    for i in range(n-1,-1,-1):
        labels[i]='HAD'[state];state=predecessors[i][state]
    backward=[None]*n;be=[None]*n;bs=[None]*n
    backward[-1]=(0.,0.,0.);be[-1]=(0.,0.,0.);bs[-1]=(0,0,0)
    following=(0.,0.,0.);offset=0.
    for i in range(n-2,-1,-1):
        values=[];emissions_sum=[];switches=[]
        for state in range(3):
            options=tuple(rows[i+1][k]+following[k]-(cost if k!=state else 0.) for k in range(3))
            chosen=_best(options);ties+=sum(value==options[chosen] for value in options)>1
            values.append(options[chosen]);emissions_sum.append(rows[i+1][chosen]+be[i+1][chosen])
            switches.append(bs[i+1][chosen]+int(chosen!=state))
        normal=max(values);offset+=normal;following=tuple(value-normal for value in values)
        absolute=tuple(value+offset for value in following)
        _finite((*following,*absolute,*emissions_sum,offset))
        backward[i]=absolute;be[i]=tuple(emissions_sum);bs[i]=tuple(switches)
    return PathTables(rows,cost,tuple(forward),tuple(backward),tuple(fe),tuple(be),tuple(fs),tuple(bs),tuple(labels),score,int(ties))


def _state(value):
    if type(value) is not int or value not in (0,1,2):
        raise ValueError('Invalid H/A/D state')


def state_summary(tables,index,reference_state,comparison_state):
    if type(index) is not int or not 0 <= index < len(tables.emissions):
        raise ValueError('Invalid path index')
    _state(reference_state);_state(comparison_state)
    r,p=reference_state,comparison_state
    prefix=tables.forward[index][p]-tables.forward[index][r]
    local=tables.emissions[index][p]-tables.emissions[index][r]
    future=tables.backward[index][p]-tables.backward[index][r]
    emission_margin=(tables.forward_emissions[index][p]+tables.backward_emissions[index][p]
                     -tables.forward_emissions[index][r]-tables.backward_emissions[index][r])
    switches=(tables.forward_switches[index][p]+tables.backward_switches[index][p]
              -tables.forward_switches[index][r]-tables.backward_switches[index][r])
    reference_score=tables.forward[index][r]+tables.backward[index][r]
    comparison_score=tables.forward[index][p]+tables.backward[index][p]
    full=prefix+future;switch_margin=-tables.switch_cost*switches
    _finite((prefix,local,future,full,emission_margin,switch_margin,reference_score,comparison_score))
    tolerance=ABS_TOL+REL_TOL*max(abs(reference_score),abs(comparison_score))
    if abs(emission_margin+switch_margin-full)>tolerance:
        raise ValueError('Constrained path decomposition differs')
    return dict(prefix=prefix,prefix_before=prefix-local,local=local,future=future,full=full,
                emission_margin=emission_margin,switch_margin=switch_margin,
                reference_score=reference_score,comparison_score=comparison_score,
                numerical_tie=isclose(reference_score,comparison_score,abs_tol=ABS_TOL,rel_tol=REL_TOL))


def constraint_summary(tables,index,reference_owner):
    if type(reference_owner) is not int or reference_owner not in (0,1):
        raise ValueError('Legacy ownership query requires H or A')
    return state_summary(tables,index,reference_owner,1-reference_owner)


def patch_summary(emissions,labels,first,stop,reference_owner,switch_cost=32.0):
    """Difference for a fixed-path patch; only changed span/adjacent edges enter it.

    The caller obtains the globally validated segment from path_tables. Validate
    dimensions and every value consumed by this local difference again here.
    """
    _state(reference_owner)
    n=len(emissions)
    if (n!=len(labels) or type(first) is not int or type(stop) is not int
            or not 0 <= first < stop <= n or not isfinite(switch_cost) or switch_cost<0):
        raise ValueError('Invalid fixed patch')
    for label in labels[max(0,first-1):min(n,stop+1)]:
        if label not in ('H','A','D'):raise ValueError('Patch needs supported H/A/D path')
    gain=0.
    for i in range(first,stop):
        row=emissions[i]
        if len(row)!=3:raise ValueError('Invalid patch emissions')
        _finite(row)
        gain+=row[reference_owner]-row['HAD'.index(labels[i])]
    def replacement(i):return 'HAD'[reference_owner] if first<=i<stop else labels[i]
    additional=sum(int(replacement(i-1)!=replacement(i))-int(labels[i-1]!=labels[i])
                   for i in range(max(1,first),min(n-1,stop)+1))
    objective_gain=gain-switch_cost*additional;_finite((gain,objective_gain))
    return dict(emission_gain=gain,additional_switches=int(additional),objective_gain=objective_gain)
