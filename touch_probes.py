"""Aggregate-only numeric probes. Never emits tracking rows, images or video."""
import argparse
from collections import Counter
import csv
import json
from math import hypot,isfinite
from pathlib import Path


def width_scale(matrix,x_m,y_m):
    if len(matrix)!=9 or not all(isfinite(v) for v in (*matrix,x_m,y_m)):
        raise ValueError('Invalid planar scale input')
    a,b,c,d,e,f,g,h,i=matrix
    x,y=x_m/105.3,y_m/68
    w=g*x+h*y+i
    if abs(w)<1e-12: raise ValueError('Singular planar scale')
    scale=hypot((b*w-(a*x+b*y+c)*h)/(w*w*68),
                (e*w-(d*x+e*y+f)*h)/(w*w*68))
    if not isfinite(scale) or scale<=0: raise ValueError('Invalid planar scale')
    return scale


def quantiles(values):
    values=sorted(values)
    if not values: return {f'q{q}':None for q in (5,25,50,75,95)}
    def at(q):
        index=(len(values)-1)*q/100;lo=int(index);hi=min(lo+1,len(values)-1)
        return values[lo]+(values[hi]-values[lo])*(index-lo)
    return {f'q{q}':at(q) for q in (5,25,50,75,95)}


def lengths(values):
    edges=(1,5,25,125,250)
    return dict(count=len(values),total_frames=sum(values),quantiles_frames=quantiles(values),
        histogram={str(edge):sum((0 if j==0 else edges[j-1])<v<=edge for v in values) for j,edge in enumerate(edges)} | {'over250':sum(v>250 for v in values)})


def probe(frames,homographies):
    if len(frames)!=len(homographies): raise ValueError('Probe dimensions differ')
    scales=[];runs=[];gaps=[];current=0;previous=None;seen=near=graded=0
    def close():
        if current: (runs if previous[1] else gaps).append(current)
    for frame,matrix in zip(frames,homographies):
        if not frame.period:
            close();current=0;previous=None;continue
        graded+=1
        observed=frame.ball_observed;key=(frame.period,observed)
        if key!=previous:
            close();current=0
        previous=key;current+=1
        points=(*frame.home_xy,*frame.away_xy)
        scales.extend(width_scale(matrix,x,y) for x,y in points)
        if observed:
            seen+=1
            near+=any(hypot(x-frame.ball_x,y-frame.ball_y)<=2.5 for x,y in points)
    close()
    heights=quantiles([s*1.8 for s in scales])
    return dict(schema_version=1,graded_frames=graded,observed_frames=seen,
        player_samples=len(scales),player_height_px=heights,ball_diameter_px=quantiles([s*.22 for s in scales]),
        ball_runs=lengths(runs),gaps=lengths(gaps),observed_near_player_share=near/seen if seen else None,
        pose_decision='considered_and_dropped' if heights['q50'] is not None and heights['q50']<100 else 'not_dropped_by_size_rule',
        scale_limitation='Planar pitch-width Jacobian proxy, not a measured vertical body projection.')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--handling',required=True);parser.add_argument('--out',required=True)
    args=parser.parse_args()
    from gap_solver.input_contract import read_epts_contract,iter_records,sha256
    handling=json.loads(Path(args.handling).read_text(encoding='utf-8'))
    paths={key:Path(handling['input_prefix']+suffix) for key,suffix in
        [('metadata','_atd.xml'),('tracking','_atd.txt'),('homography','_homography.csv')]}
    if not all(path.is_file() for path in paths.values()): raise ValueError('Missing declared challenge input')
    hashes={k:sha256(v) for k,v in paths.items()}
    if hashes!=handling['expected_input_sha256']: raise ValueError('Challenge input identity differs')
    frames=list(iter_records(read_epts_contract(paths['metadata']),paths['tracking']))
    matrices=[]
    with paths['homography'].open(encoding='utf-8-sig',newline='') as handle:
        for index,row in enumerate(csv.DictReader(handle)):
            if int(row['frame'])!=index or int(row['valid'])!=1:raise ValueError('Invalid homography contract')
            matrices.append(tuple(float(row[f'h{a}{b}']) for a in range(3) for b in range(3)))
    result=probe(frames,matrices)
    if {k:sha256(v) for k,v in paths.items()}!=hashes:raise ValueError('Challenge input changed')
    result['input_sha256']=hashes
    with Path(args.out).open('x',encoding='utf-8',newline='\n') as handle:
        json.dump(result,handle,sort_keys=True,indent=2,allow_nan=False);handle.write('\n')
    print(json.dumps(result,sort_keys=True,allow_nan=False))

if __name__=='__main__':
    try: main()
    except Exception as error:
        raise SystemExit('Aggregate probe stopped: '+type(error).__name__+'. No source rows printed.') from None
