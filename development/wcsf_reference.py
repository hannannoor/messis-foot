"""Evaluation-only native consensus with no clock/quality feedback."""
from bisect import bisect_left
from contextlib import closing
from pathlib import Path
import sqlite3
import numpy as np
from wcsf_source import _integer


def _flag(value,lo,hi):
    try:return _integer(value,lo,hi)
    except ValueError:return None


def reference_codes(reference_db,index):
    grouped={1:{},2:{}}
    with closing(sqlite3.connect(Path(reference_db).resolve().as_uri()+'?mode=ro',uri=True)) as db:
        for p,t,alive,owner in db.execute('select period,t,alive,owner from annotations order by period,t,ordinal'):
            alive_set,owner_set=grouped[p].setdefault(t,(set(),set()))
            alive_set.add(_flag(alive,0,1));owner_set.add(_flag(owner,1,2))
    codes={p:{} for p in (1,2)}
    for p,samples in grouped.items():
        for t,(alive,owner) in samples.items():
            codes[p][t]=2 if alive=={0} else (next(iter(owner))-1 if alive=={1} and len(owner)==1 and None not in owner else 3)
    times={p:sorted(codes[p]) for p in (1,2)};result=[]
    for p,t in index:
        if p not in (1,2) or type(t) is not int or not 0<=t<=86400000:raise ValueError('Invalid canonical reference index')
        if t in codes[p]:result.append(codes[p][t]);continue
        i=bisect_left(times[p],t)
        if i and i<len(times[p]) and times[p][i]-times[p][i-1]==100:
            result.append(codes[p][times[p][i-1]])
        else:result.append(3)
    return np.asarray(result,dtype=np.uint8)
