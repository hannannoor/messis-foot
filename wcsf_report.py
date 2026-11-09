"""Strict bounded scalar/count evidence for one three-method match audit."""
import json
from math import isclose,isfinite

METHODS=('w0-c32-neutral-missing','official-convention-w50','matched-input-w50')
METRICS=('accuracy','official_macro_f1','supported_macro_f1','spell_f1_mean')
IOUS=('0.3','0.4','0.5','0.6','0.7')
BINS=('short','medium','long','very_long')


def parse_json(text):
    def pairs(items):
        result={}
        for key,value in items:
            if key in result:raise ValueError('Duplicate JSON key')
            result[key]=value
        return result
    def constant(_):raise ValueError('Nonfinite JSON value')
    return json.loads(text,object_pairs_hook=pairs,parse_constant=constant)


def read_json(path):
    with open(path,encoding='utf-8') as f:return parse_json(f.read())


def prf(tp,fp,fn):
    return dict(n_matched=int(tp),n_spurious=int(fp),n_missed=int(fn),
                precision=tp/(tp+fp) if tp+fp else None,
                recall=tp/(tp+fn) if tp+fn else None,
                f1=2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else None)


def mean_defined(values):
    values=list(values)
    return sum(values)/len(values) if values and all(v is not None for v in values) else None


def keys(value,names):
    if type(value) is not dict or set(value)!=set(names):raise ValueError('Unexpected bounded report fields')


def count(value):
    if type(value) is not int or not 0<=value<=100000000:raise ValueError('Invalid integer support/count')
    return value


def number(value,expected):
    if expected is None:
        if value is not None:raise ValueError('Unsupported rate must be null')
    elif type(value) not in (int,float) or not isfinite(value) or not isclose(value,expected,rel_tol=1e-10,abs_tol=1e-12):
        raise ValueError('Numeric rate/derivation differs')


def _prf(value):
    keys(value,('n_matched','n_spurious','n_missed','precision','recall','f1'))
    expected=prf(*(count(value[k]) for k in ('n_matched','n_spurious','n_missed')))
    for k in ('precision','recall','f1'):number(value[k],expected[k])


def _interval(value):
    keys(value,('n_gt','n_pred','per_iou','mean_f1'));ng=count(value['n_gt']);np=count(value['n_pred'])
    keys(value['per_iou'],IOUS);last=min(ng,np)
    for iou in IOUS:
        row=value['per_iou'][iou];_prf(row);tp=row['n_matched']
        if tp>last or tp+row['n_missed']!=ng or tp+row['n_spurious']!=np:raise ValueError('Interval support/count mismatch')
        last=tp
    number(value['mean_f1'],mean_defined(value['per_iou'][k]['f1'] for k in IOUS))


def _cell(value):
    keys(value,('support','metrics','confusion','spells','dead','duration','HA_boundaries'))
    s=value['support'];keys(s,('frames','known','unknown','H','A','D','H_seconds','A_seconds','D_seconds'))
    for key in ('frames','known','unknown','H','A','D'):count(s[key])
    cm=value['confusion']
    if type(cm) is not list or len(cm)!=4 or any(type(r) is not list or len(r)!=4 for r in cm):raise ValueError('Expected exact 4x4 aggregate confusion')
    for r in cm:
        for n in r:count(n)
    expected={'frames':sum(map(sum,cm)),'known':sum(map(sum,cm[:3])),'unknown':sum(cm[3]),
              **{name:sum(cm[k]) for k,name in enumerate('HAD')}}
    if any(s[k]!=v for k,v in expected.items()):raise ValueError('Frame support differs from confusion')
    for name in 'HAD':number(s[name+'_seconds'],s[name]/25)
    rates=[]
    for k in range(3):
        tp=cm[k][k];fp=sum(cm[j][k] for j in range(3))-tp;fn=sum(cm[k])-tp
        rates.append(prf(tp,fp,fn)['f1'])
    m=value['metrics'];keys(m,METRICS)
    number(m['accuracy'],sum(cm[k][k] for k in range(3))/s['known'] if s['known'] else None)
    number(m['official_macro_f1'],sum(v if v is not None else 0. for v in rates)/3 if s['known'] else None)
    number(m['supported_macro_f1'],mean_defined(rates))
    _interval(value['spells']);number(m['spell_f1_mean'],value['spells']['mean_f1'])
    d=value['dead'];keys(d,('frame','intervals'));_prf(d['frame']);_interval(d['intervals'])
    expected=prf(cm[2][2],sum(cm[k][2] for k in (0,1)),sum(cm[2])-cm[2][2])
    if d['frame']!=expected:raise ValueError('Dead frame counts differ from confusion')
    keys(value['duration'],BINS)
    for row in value['duration'].values():
        keys(row,('n_gt','per_iou'));ng=count(row['n_gt']);keys(row['per_iou'],IOUS)
        for cell in row['per_iou'].values():
            keys(cell,('n_matched','recall'));n=count(cell['n_matched'])
            if n>ng:raise ValueError('Short-spell match exceeds support')
            number(cell['recall'],n/ng if ng else None)
    if sum(r['n_gt'] for r in value['duration'].values())!=value['spells']['n_gt']:raise ValueError('Duration-bin support differs')
    for iou in IOUS:
        if sum(r['per_iou'][iou]['n_matched'] for r in value['duration'].values())!=value['spells']['per_iou'][iou]['n_matched']:
            raise ValueError('Duration matches differ from total matches')
    keys(value['HA_boundaries'],('12','25'))
    for tolerance,row in value['HA_boundaries'].items():
        keys(row,('n_gt','n_pred','n_matched','n_missed','n_spurious','n_ambiguous','precision','recall','f1',
                  'mean_latency_frames','mean_abs_latency_frames','matched_latency_denominator'))
        for k in ('n_gt','n_pred','n_matched','n_missed','n_spurious','n_ambiguous','matched_latency_denominator'):count(row[k])
        tp=row['n_matched']
        if tp+row['n_missed']!=row['n_gt'] or tp+row['n_spurious']!=row['n_pred'] or row['matched_latency_denominator']!=tp or row['n_ambiguous']>row['n_gt']:raise ValueError('Boundary support differs')
        expected=prf(tp,row['n_spurious'],row['n_missed'])
        for k in ('precision','recall','f1'):number(row[k],expected[k])
        for k in ('mean_latency_frames','mean_abs_latency_frames'):
            if not tp:number(row[k],None)
            elif type(row[k]) not in (int,float) or not isfinite(row[k]) or abs(row[k])>int(tolerance):raise ValueError('Invalid bounded latency')
        if tp and row['mean_abs_latency_frames']<abs(row['mean_latency_frames'])-1e-12:raise ValueError('Invalid latency moments')


def validate_report(value):
    keys(value,('schema_version','full_state_complete','match','halves','deltas'))
    if type(value['schema_version']) is not int or value['schema_version']!=1 or type(value['full_state_complete']) is not bool:raise ValueError('Invalid report identity')
    keys(value['match'],METHODS);keys(value['halves'],('1','2'));keys(value['deltas'],METHODS[1:])
    for group in (value['match'],*value['halves'].values()):
        keys(group,METHODS)
        for cell in group.values():_cell(cell)
        supports=[cell['support'] for cell in group.values()]
        if any(s!=supports[0] for s in supports):raise ValueError('Different reference support across methods')
    base=value['match'][METHODS[0]]
    if value['full_state_complete']!=all(base['support'][name]>0 for name in 'HAD'):raise ValueError('Full-state support claim differs')
    for method in METHODS:
        cell=value['match'][method];halves=[value['halves'][p][method] for p in ('1','2')]
        for row in range(4):
            for col in range(4):
                if cell['confusion'][row][col]!=sum(h['confusion'][row][col] for h in halves):raise ValueError('Match confusion not pooled')
        for kind in ('spells','dead_intervals'):
            extract=lambda c:c['spells'] if kind=='spells' else c['dead']['intervals']
            match=extract(cell)
            for key in ('n_gt','n_pred'):
                if match[key]!=sum(extract(h)[key] for h in halves):raise ValueError('Match intervals not pooled')
            for iou in IOUS:
                for key in ('n_matched','n_spurious','n_missed'):
                    if match['per_iou'][iou][key]!=sum(extract(h)['per_iou'][iou][key] for h in halves):raise ValueError('Match IoU counts not pooled')
        for name in BINS:
            row=cell['duration'][name]
            if row['n_gt']!=sum(h['duration'][name]['n_gt'] for h in halves):raise ValueError('Duration support not pooled')
            for iou in IOUS:
                if row['per_iou'][iou]['n_matched']!=sum(h['duration'][name]['per_iou'][iou]['n_matched'] for h in halves):raise ValueError('Duration matches not pooled')
        for tolerance in ('12','25'):
            row=cell['HA_boundaries'][tolerance];parts=[h['HA_boundaries'][tolerance] for h in halves]
            for key in ('n_gt','n_pred','n_matched','n_missed','n_spurious','n_ambiguous','matched_latency_denominator'):
                if row[key]!=sum(p[key] for p in parts):raise ValueError('Boundary counts not pooled')
            for key in ('mean_latency_frames','mean_abs_latency_frames'):
                total=row['matched_latency_denominator']
                expected=sum(p[key]*p['matched_latency_denominator'] for p in parts if p['matched_latency_denominator'])/total if total else None
                number(row[key],expected)
    for method,delta in value['deltas'].items():
        keys(delta,METRICS)
        for metric in METRICS:
            a=value['match'][method]['metrics'][metric];b=base['metrics'][metric]
            number(delta[metric],None if a is None or b is None else a-b)
