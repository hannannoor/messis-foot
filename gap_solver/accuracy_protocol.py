"""Predeclared bounded comparison and aggregate-only external evidence."""
import hashlib
import json
from math import isfinite
from pathlib import Path

PARAMETERS=tuple((f'w{w:g}-c{c:g}',w,c) for w in (0.,.25,.5,1.) for c in (0.,2.,8.,32.))
SPLITS={
    'validation':{'dfl':['J03WQQ'],'skillcorner':[2006229,2006363]},
    'regression':{'dfl':['J03WR9','J03WN1'],'skillcorner':[2007448,2007721,2010085,2011166,2013725,2015213,2016236,2017461]},
}
CONTROLS=('incumbent','carry','agreement','agreement-plus-carry')


def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def hash_files(files):
    result={}
    for name,path in files.items():
        h=hashlib.sha256()
        with Path(path).open('rb') as handle:
            for block in iter(lambda:handle.read(1024*1024),b''):h.update(block)
        result[name]=h.hexdigest()
    return result


def require_files(expected,files):
    if expected!=hash_files(files):raise ValueError('Consumed source/input identity changed')


def assert_aggregate(value):
    if isinstance(value,dict):
        forbidden={'pairs','missed','spurious','reference','prediction','predictions','home_xy','away_xy','ball_x','ball_y','source_frames','timestamps'}
        if set(value)&forbidden:raise ValueError('Per-frame/event field in aggregate export')
        if 'frames' in value and type(value['frames']) is not int:raise ValueError('Frame arrays in aggregate export')
        for member in value.values():assert_aggregate(member)
    elif isinstance(value,(list,tuple)):
        for member in value:assert_aggregate(member)
    elif isinstance(value,float) and not isfinite(value):raise ValueError('Nonfinite aggregate')


def balanced_mean(reports,variant,metric):
    return sum(sum(float(r['variants'][variant]['metrics'][metric]) for r in reports if r['cohort']==cohort)/len(matches)
        for cohort,matches in SPLITS['validation'].items())/2


def select_validation(reports):
    expected={(c,str(m)) for c,ids in SPLITS['validation'].items() for m in ids}
    keys=[(r['cohort'],str(r['match'])) for r in reports]
    if len(keys)!=len(set(keys)) or set(keys)!=expected or any(r['regime']!='natural' for r in reports):raise ValueError('Selection needs exact natural validation cases only')
    required={p[0] for p in PARAMETERS}|{'agreement-plus-carry'}
    for r in reports:
        if not required<=set(r['variants']) or set(r['variants'])-required-set(CONTROLS):raise ValueError('Incomplete or unknown validation settings')
        for name in required:
            for metric in ('spell_f1_mean','macro_f1'):
                value=r['variants'][name]['metrics'][metric]
                if not isfinite(value) or not 0<=value<=1:raise ValueError('Invalid validation metric')
    rows=[dict(id=name,weight=w,switch_cost=c,score=balanced_mean(reports,name,'spell_f1_mean'),macro_f1=balanced_mean(reports,name,'macro_f1')) for name,w,c in PARAMETERS]
    rows.sort(key=lambda r:(-r['score'],-r['macro_f1'],r['weight'],r['switch_cost']))
    best=rows[0];baseline=balanced_mean(reports,'agreement-plus-carry','spell_f1_mean')
    return dict(selected_id=best['id'],weight=best['weight'],switch_cost=best['switch_cost'],score=best['score'],macro_f1=best['macro_f1'],baseline_score=baseline,validation_improved=best['score']>baseline,ranking=rows)
