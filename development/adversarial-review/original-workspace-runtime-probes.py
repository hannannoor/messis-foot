import sys, os, json, csv, itertools, random, math, shutil
from pathlib import Path
from collections import Counter
from dataclasses import replace

WORK = Path(__file__).resolve().parents[1]
CODE = WORK/'snapshots/current-cee6741'
TMP = WORK/'.tmp/runtime-temp-v2'
TMP.mkdir(exist_ok=True)
os.environ['TEMP'] = os.environ['TMP'] = str(TMP)
sys.dont_write_bytecode = True
sys.path.insert(0, str(CODE))
from ball_gap_policy import decode_ball_gap
from gap_solver.soft_sequence import decode_soft, sequence_usable
from gap_solver.motion import motion_frame
from gap_solver.anonymous_motion import associate_anonymous
from gap_solver.tactical import feature_rows, PortableTree
from gap_solver.tactical_model import FROZEN_MODEL
from gap_solver.materialization_control import materialize_abstentions
from gap_solver.input_contract import read_epts_contract, iter_records, quality_mask
import ball_gap_candidate as candidate

out={}
tree=PortableTree(FROZEN_MODEL['model'])
def calc(fs):
    fs,assoc=associate_anonymous(fs)
    ps=[tree.predict(row) for row in feature_rows(fs)]
    y,c=decode_ball_gap(ps,[f.period for f in fs],[sequence_usable(f) for f in fs],[f.ball_observed for f in fs])
    return ps,y,c

# Independently enumerate all paths to verify the optimizer, not its tests.
rng=random.Random(301)
checks=0
for n in range(1,7):
    for case in range(10):
        rows=[tuple(rng.uniform(-5,3) for _ in range(3)) for _ in range(n)]
        cost=rng.choice([0.,.75,2.,32.])
        y=decode_soft(rows,[1]*n,[True]*n,cost)
        def score(path):return sum(rows[i][s] for i,s in enumerate(path))-cost*sum(a!=b for a,b in zip(path,path[1:]))
        actual=score(tuple('HAD'.index(v) for v in y))
        best=max(score(p) for p in itertools.product(range(3),repeat=n))
        assert abs(actual-best)<1e-9
        checks+=1
out['brute_force_optimal_paths_checked']=checks

out['burst']={}
for strength in (.9,.99,.6):
    other=.05 if strength==.9 else (.005 if strength==.99 else .4)
    dead=1-strength-other
    for n in (10,20,22,23,50,157,158):
        ps=[(strength,other,dead)]*100+[(other,strength,dead)]*n+[(strength,other,dead)]*100
        y,_=decode_ball_gap(ps,[1]*len(ps),[True]*len(ps),[True]*len(ps))
        out['burst'][f'{strength}/{n}']=dict(counts=dict(Counter(y)),middle=dict(Counter(y[100:100+n])))

out['neutral_ties']={}
for left,right in itertools.permutations('HAD',2):
    def support(s):return tuple(.98 if v==s else .01 for v in 'HAD')
    ps=[support(left)]*100+[(.33,.33,.34)]*1000+[support(right)]*100
    y,c=decode_ball_gap(ps,[1]*1200,[True]*1200,[True]*100+[False]*1000+[True]*100)
    out['neutral_ties'][left+right]=dict(gap=dict(Counter(y[100:1100])),cuts=[i for i in range(1,len(y)) if y[i]!=y[i-1]],counts=c)
out['one_anchor']={}
for n in (27,252,2502):
    y,c=decode_ball_gap([(.99,.005,.005)]*n,[1]*n,[True]*n,[True]+[False]*(n-1))
    out['one_anchor'][n]=dict(labels=dict(Counter(y)),counts=c)
y,c=decode_ball_gap([(.99,.005,.005)]*5,[1]*5,[True,True,False,True,True],[True,False,False,False,False])
out['barrier']=dict(latent=y,final=materialize_abstentions(y,[1]*5),counts=c)
y,c=decode_ball_gap([(.01,.01,.98)]*5,[1,1,0,2,2],[True]*5,[False]*5)
out['unobserved']=dict(latent=y,final=materialize_abstentions(y,[1,1,0,2,2]),counts=c)

fs=[motion_frame(1,(25+.08*i,34),[(25+.08*i+.5,34)],[(25+.08*i+1,34)]) for i in range(180)]
swapped=[motion_frame(f.period,(f.ball_x,f.ball_y),f.away_xy,f.home_xy) for f in fs]
ps,y,c=calc(fs);qs,z,_=calc(swapped)
out['tactical_swap']=dict(original=dict(Counter(y)),swapped=dict(Counter(z)),last_support=ps[-1],swapped_last_support=qs[-1],support_vectors_equal=ps==qs)
altered=[replace(f,ball_native_observation=False,ball_provenance='synthetic_held',ball_interpolated=True,interpolated=True,ball_sample_time_s=-123) for f in fs]
out['provenance_invariance']=dict(supports_identical=calc(altered)[0]==ps,labels_identical=calc(altered)[1]==y)
stationary=[motion_frame(1,(52.65,34),[(53.65,34)],[(62.65,34)]) for _ in range(100)]
ss,sy,_=calc(stationary)
out['finite_stationary']=dict(labels=dict(Counter(sy)),last_support=ss[-1])

# Own EPTS fixtures: declaration order differs from channel-register order.
def fixture(name, frames, invalid=()):
    root=TMP/name;root.mkdir(exist_ok=True)
    players=[(s+str(i),s) for s in ('h','a') for i in range(3)]
    x=['<Match><FrameRate>25</FrameRate><FieldSize><Width>105</Width><Height>68</Height></FieldSize>',
       '<Team id="a"><Name>Athletic Club</Name></Team><Team id="h"><Name>Barcelona</Name></Team>']
    x += [f'<Player id="{p}" teamId="{s}"/>' for p,s in reversed(players)]
    x += [f'<Channel id="{c}"><Name>{n}</Name><Unit>{u}</Unit></Channel>' for c,n,u in [('x','position_x','normalized'),('y','position_y','normalized'),('s','speed_kph','kph')]]
    x += [f'<PlayerChannel id="{p}{c}" playerId="{p}" channelId="{c}"/>' for p,_ in players for c in 'xys']
    x += [f'<DataFormatSpecification startFrame="1" endFrame="{len(frames)}" separator=":"><StringRegister name="frameCount"/><SplitRegister separator=";">']
    for p,_ in players:x += ['<SplitRegister separator=",">'+''.join(f'<PlayerChannelRef playerChannelId="{p}{c}"/>' for c in 'xys')+'</SplitRegister>']
    x += ['</SplitRegister><SplitRegister separator=",">'+''.join(f'<BallChannelRef channelId="{c}"/>' for c in 'xys')+'</SplitRegister></DataFormatSpecification></Match>']
    meta,raw,q=[root/n for n in ('meta.xml','raw.txt','quality.csv')]
    meta.write_text(''.join(x),encoding='utf-8')
    def triple(p):return 'nan,nan,nan' if p is None else f'{p[0]/105.3:.16g},{p[1]/68:.16g},0'
    lines=[]
    for i,f in enumerate(frames):
        pts=[*f.home_xy,*f.away_xy]
        lines.append(str(i+1)+':'+(';'.join(triple(p) for p in pts))+':'+triple((f.ball_x,f.ball_y) if f.ball_observed else None)+'\n')
    raw.write_text(''.join(lines),encoding='utf-8')
    with q.open('w',newline='') as h:
        w=csv.writer(h);w.writerow(['frame','valid','reprojection_error']+['h'+str(a)+str(b) for a in range(3) for b in range(3)])
        for i in range(len(frames)):w.writerow([i,int(i not in invalid),1,1,0,0,0,1,0,0,0,1])
    return meta,raw,q
def scene(i,swap=False,missing=False):
    b=(25+.08*i,34)
    h=[(b[0]+.5,34),(b[0]+10,20),(b[0]+15,45)]
    a=[(b[0]+1,34),(b[0]+25,20),(b[0]+30,45)]
    return motion_frame(1,None if missing else b,a if swap else h,h if swap else a)

out['whole_runtime']={}
for name,frames in [('orig',[scene(i) for i in range(180)]),('swap',[scene(i,True) for i in range(180)]),('gap',[scene(i%80,missing=100<=i<1100) for i in range(1200)])]:
    inputs=fixture(name,frames)
    report=candidate.run_source(*inputs,TMP/(name+'-output'),scope='synthetic')
    with (TMP/(name+'-output')/'submission.csv').open() as h:rows=list(csv.DictReader(h))
    out['whole_runtime'][name]={k:report[k] for k in ('setting','selected_labels','latent_unknown_active','materialized_active','selected_motion_head_used','policy_diagnostics')}
    out['whole_runtime'][name]['sequential_indices']= [int(r['frame']) for r in rows]==list(range(len(frames)))
    if name=='gap':
        with (TMP/(name+'-output')/'uncertainty.csv').open() as h:u=list(csv.DictReader(h))
        out['whole_runtime'][name]['gap_final']=dict(Counter(r['final_label'] for r in u[100:1100]))
        out['whole_runtime'][name]['gap_materialized']=sum(int(r['materialized']) for r in u[100:1100])
        out['whole_runtime'][name]['gap_neutralized']=sum(int(r['neutralized']) for r in u[100:1100])

# Check changed source/evidence guard on copied seal-required files only.
v,_=candidate.selected_artifact();clone=TMP/'seal-copy';clone.mkdir(exist_ok=True)
names=set(v['source_sha256'])|set(v['evidence_file_sha256'])|{'benchmark/ball-gap/selected.json'}
for name in names:
    p=clone/name;p.parent.mkdir(exist_ok=True,parents=True);shutil.copyfile(CODE/name,p)
real=candidate.ROOT;candidate.ROOT=clone
out['seal_checks']={}
try:
    candidate.selected_artifact();out['seal_checks']['clean_copy']='passes'
    for name in ('ball_gap_runtime.py','ball_gap_policy.py','reports/ball-gap/summary.json','gap_solver/multicam.py'):
        p=clone/name;before=p.read_bytes();p.write_bytes(before+b'\n')
        try:candidate.selected_artifact();result='ACCEPTED'
        except ValueError as e:result=type(e).__name__+': '+str(e)
        out['seal_checks'][name]=result;p.write_bytes(before)
finally:candidate.ROOT=real

out['anonymous']={}
cross=[motion_frame(1,None,[(0,0),(1,0)],[(10,0)]),motion_frame(1,None,[(.45,0),(.55,0)],[(10,0)]),motion_frame(1,None,[(1,0),(0,0)],[(10,0)])]
ca,_=associate_anonymous(cross)
out['anonymous']['crossing_ids']=[list(zip(f.home_ids,f.home_xy)) for f in ca]
rev=[replace(f,home_xy=tuple(reversed(f.home_xy)),away_xy=tuple(reversed(f.away_xy))) for f in cross]
out['anonymous']['order_invariant']=associate_anonymous(rev)[0]==ca

# Missing samples can manufacture zero-speed evidence on every retained row.
out['sparse_reacquisition']={}
for stride in (1,2,3,5):
    fs2=[]
    for i in range(180):
        b=(25+.08*i,34)
        fs2.append(motion_frame(1,b if i%stride==0 else None,
            [(b[0]+1,34),(10,10),(15,15)],[(b[0]+10,34),(70,55),(75,60)],
            ball_native_observation=i%stride==0,ball_sample_time_s=i/25 if i%stride==0 else None))
    p2,y2,c2=calc(fs2)
    out['sparse_reacquisition'][stride]=dict(labels=dict(Counter(y2)),last_observed_support=p2[((len(fs2)-1)//stride)*stride],
        observed_recent_speeds=sorted(set(row[10] for f,row in zip(fs2,feature_rows(fs2)) if f.ball_observed)),counts=c2)

# Keep the complete selected runtime within the pitch on this independent probe.
for stride in (1,2):
    frames=[]
    for i in range(180):
        b=(25+.08*i,34)
        frames.append(motion_frame(1,b if i%stride==0 else None,[(b[0]+1,34),(10,10),(15,15)],[(b[0]+10,34),(70,55),(75,60)]))
    report=candidate.run_source(*fixture('sparse'+str(stride),frames),TMP/('sparse-output'+str(stride)),scope='synthetic')
    out['sparse_reacquisition'][stride]['whole_runtime_labels']=report['selected_labels']

inputs=fixture('parser',[scene(0)])
meta,raw,q=inputs;c=read_epts_contract(meta)
out['parser']=dict(sides=c.sides,roles_correct=c.sides==('H','H','H','A','A','A'),quality=quality_mask(q,1))
original=raw.read_text()
out['parser']['rejections']={}
for name,value in [('index',original.replace('1:','2:',1)),('partial',original.rsplit(':',1)[0]+':nan,.5,0\n'),('infinity',original.replace(',0;',',inf;',1)),('numeric',original.replace(',0;',',oops;',1))]:
    raw.write_text(value)
    try:list(iter_records(c,raw,[(1,0,0)]));result='ACCEPTED'
    except ValueError as e:result=str(e)
    out['parser']['rejections'][name]=result
raw.write_text(original)
print(json.dumps(out,indent=2))
(TMP/'results.json').write_text(json.dumps(out,indent=2)+'\n')
