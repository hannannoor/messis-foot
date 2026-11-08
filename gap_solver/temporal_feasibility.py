"""Conservative source-only confidence ceilings for the frozen two-state decoder.

A ceiling can disprove a gate on baseline X rows. It cannot certify that any
feature row, eligible interval, prediction or correctness level is attainable.
"""
from dataclasses import asdict
import math
import sys
from .temporal import MOTION_FEATURES,PortableBoosted,TemporalPolicy


def _number(value,name,minimum=None,strict=False):
    if type(value) not in (int,float):raise ValueError(name+' must be a finite number, not a boolean')
    try:value=float(value)
    except (OverflowError,ValueError) as error:raise ValueError(name+' is outside the supported numeric range') from error
    if not math.isfinite(value) or (minimum is not None and (value<=minimum if strict else value<minimum)):
        raise ValueError('Invalid '+name)
    return value


def _validate_model(model):
    try:
        if not isinstance(model,dict) or tuple(model.get('feature_names',()))!=MOTION_FEATURES:raise ValueError('Unknown feature schema')
        _number(model.get('initial_log_odds'),'initial_log_odds')
        rate=_number(model.get('learning_rate'),'learning_rate',0,True)
        if rate>1:raise ValueError('Invalid learning_rate')
        trees=model.get('trees')
        if not isinstance(trees,list) or not 1<=len(trees)<=1000:raise ValueError('Invalid ensemble dimensions')
        for tree in trees:
            fields=[tree[name] for name in ('children_left','children_right','feature','threshold','value')]
            n=len(fields[0])
            if not 1<=n<=4095 or any(not isinstance(v,list) or len(v)!=n for v in fields):raise ValueError('Invalid tree dimensions')
            for a,b,feature,threshold,value in zip(*fields):
                if any(type(v) is not int for v in (a,b,feature)):raise ValueError('Tree indices must be integers')
                if (a<0 or b<0) and (a,b)!=(-1,-1):raise ValueError('Invalid half-leaf')
                _number(threshold,'threshold');_number(value,'value')
        PortableBoosted(model)  # includes acyclicity, bounds and reachability
    except (KeyError,TypeError,IndexError,OverflowError) as error:
        raise ValueError('Malformed portable ensemble') from error


def _outward(value,direction):return math.nextafter(value,direction) if math.isfinite(value) else value


def symmetric_logit_bound(model):
    """Enclose actual binary64 score arithmetic, including initial-term cancellation.

    Float addition/multiplication are monotone on finite inputs. Walk the same
    score-accumulation order with every tree at its leaf extrema, rounding each
    interval endpoint outward. Correlated/unattainable leaf choices only loosen
    the enclosure. Extreme arithmetic declines proof instead of emitting NaN.
    """
    _validate_model(model);rate=float(model['learning_rate'])
    low=high=float(model['initial_log_odds']);ranges=[]
    for tree in model['trees']:
        leaves=[float(v) for child,v in zip(tree['children_left'],tree['value']) if child==-1]
        a,b=min(leaves),max(leaves);ranges.append(rate*((b-a)/2))
        low=_outward(low+_outward(rate*a,-math.inf),-math.inf)
        high=_outward(high+_outward(rate*b,math.inf),math.inf)
    try:exact=math.fsum(ranges)
    except OverflowError:exact=math.inf
    width=high-low
    bound=_outward(_outward(width,math.inf)/2,math.inf)
    supported=all(math.isfinite(v) for v in (low,high,bound))
    return dict(exact_real_bound=exact if math.isfinite(exact) else None,
        runtime_bound=bound if supported else None,tree_count=len(model['trees']),
        arithmetic_supported=supported,score_interval=[low,high] if supported else None,
        explanation='Leaf-only enclosure of both runtime scores; initial cancellation and rounding included.')


def _policy(value):
    try:
        policy=TemporalPolicy(**value) if isinstance(value,dict) else value
        if not isinstance(policy,TemporalPolicy):raise ValueError('Expected TemporalPolicy or policy dictionary')
        for name in ('confidence','max_gap_s','switch_multiplier'):_number(getattr(policy,name),name)
        if type(policy.minimum_players) is not int:raise ValueError('minimum_players must be an integer')
        policy.validate();return policy
    except TypeError as error:raise ValueError('Malformed policy fields') from error


def confidence_feasibility(model,transition_cost,temperature,policy):
    """Inspect only X-row confidence feasibility; never evaluate match data.

    Each incoming two-state transition message has log-odds in [-cost,cost].
    Add the emission and both messages, respecting the decoder's pre-temperature
    clip and the policy's post-temperature clip. Numerical uncertainty makes the
    result less decisive; a high ceiling is only 'not_ruled_out'.
    """
    policy=_policy(policy);cost=_number(transition_cost,'transition_cost',0)
    temperature=_number(temperature,'temperature',0,True)
    ensemble=symmetric_logit_bound(model);cost*=policy.switch_multiplier
    result=dict(scope='baseline_X_only',status='not_ruled_out',confidence_ceiling=1.,
        confidence_threshold=policy.confidence,symmetric_logit_bound=ensemble['runtime_bound'],
        exact_real_symmetric_bound=ensemble['exact_real_bound'],posterior_logit_bound=None,
        calibrated_logit_bound=None,ensemble=ensemble,policy=asdict(policy),
        correctness_measured=False,eligible_frame_existence_established=False)
    # Unsupported scales cannot produce a mathematical/runtime impossibility claim.
    ieee=(sys.float_info.radix==2 and sys.float_info.mant_dig==53)
    if not ieee or not ensemble['arithmetic_supported'] or not math.isfinite(cost) or cost>1e6:
        result['reason']='Unsupported or extreme arithmetic; no impossibility proof.';return result
    emission=min(50.,ensemble['runtime_bound'])
    # Local roundoff guard for normalized logadd/message subtraction on ordinary
    # binary64/libm implementations. Very large scales are declined above. Near
    # equality remains not ruled out; this is not a formal libm verification.
    allowance=256*math.ulp(max(50.,cost,emission))
    posterior=min(50.,_outward(emission+2*cost+allowance,math.inf))
    scaled=posterior/temperature
    if not math.isfinite(scaled):
        result['reason']='Extreme posterior/temperature division; no impossibility proof.';return result
    calibrated=min(50.,_outward(scaled,math.inf))
    positive=1/(1+math.exp(-calibrated));negative=1-1/(1+math.exp(calibrated))
    ceiling=min(1.,_outward(max(positive,negative),math.inf))
    result.update(posterior_logit_bound=posterior,calibrated_logit_bound=calibrated,confidence_ceiling=ceiling)
    if ceiling<policy.confidence:
        result.update(status='provably_impossible',reason='The conservative X-row confidence ceiling is below the configured threshold.')
    else:result['reason']='Confidence is not ruled out; actual reachability, input eligibility and correctness remain unestablished.'
    return result
