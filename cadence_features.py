"""One frozen external-only reacquisition-speed contrast; legacy sources stay intact."""
from collections import deque
from dataclasses import dataclass
from math import hypot,isfinite
from typing import Optional

from gap_solver.tactical import feature_rows
from gap_solver.soft_sequence import sequence_usable


POLICY_ID='bounded-reacquisition-speed-v1'
MAX_GAP_S=.20
TIME_BOUND_TOLERANCE_S=1e-9


@dataclass(frozen=True)
class CadenceRow:
    legacy: tuple
    candidate: tuple
    velocity_valid: bool
    time_basis: str
    pair_dt_s: Optional[float]
    repaired: bool
    unavailable_reason: str


def _pair_duration(previous,current,first,index):
    times=(previous.ball_sample_time_s,current.ball_sample_time_s)
    if any(t is not None and (not isinstance(t,(float,int)) or not isfinite(t)) for t in times):
        return None,'invalid_source','nonfinite_source_time'
    if all(t is not None for t in times):
        duration=times[1]-times[0]
        if duration<=0:return None,'invalid_source','nonincreasing_source_time'
        basis='source'
    else:
        duration=(index-first)/25
        basis='canonical_grid'
    if index-first>5 or duration>MAX_GAP_S+TIME_BOUND_TOLERANCE_S:
        return None,basis,'pair_too_old'
    return duration,basis,''


def cadence_feature_rows(frames,max_gap_s=MAX_GAP_S):
    if isinstance(max_gap_s,bool) or not isinstance(max_gap_s,(int,float)) or max_gap_s!=MAX_GAP_S:
        raise ValueError('This fixed contrast permits only the frozen .20 second horizon')
    previous_period=None
    previous_observed=None
    speeds=deque(maxlen=12)
    for index,(frame,legacy) in enumerate(zip(frames,feature_rows(frames))):
        if frame.period!=previous_period or frame.period==0:
            speeds.clear()
            previous_observed=None
        previous_period=frame.period
        valid=False;basis='none';duration=None;repaired=False
        reason='no_previous_observation'
        values=list(legacy)
        if not sequence_usable(frame):
            previous_observed=None
            reason='input_barrier'
        elif not frame.ball_observed:
            reason='ball_missing'
        else:
            if previous_observed is not None:
                first,prior=previous_observed
                duration,basis,reason=_pair_duration(prior,frame,first,index)
                valid=duration is not None
                if valid and first<index-1:
                    values[9]=min(50.,hypot(frame.ball_x-prior.ball_x,frame.ball_y-prior.ball_y)/duration)
                    repaired=True
            previous_observed=(index,frame)
        speeds.append(values[9])
        values[10]=sum(speeds)/len(speeds)
        yield CadenceRow(tuple(legacy),tuple(values),valid,basis,duration,repaired,reason)
