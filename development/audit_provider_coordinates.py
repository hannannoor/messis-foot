"""Reproduce the provider-coordinate convention audit from external numeric caches."""
import json
from pathlib import Path
import numpy as np
from gap_solver.external import load_cache
from gap_solver.frozen_protocol import load_frozen

code=Path(__file__).resolve().parent
root=code.parent/'external-reference'
artifact,manifest=load_frozen(root,code/'gap_solver')
totals={state:{'frames':0,'finite_xy':0,'same_xy_as_previous_contiguous_frame':0,'raw_origin_sentinel':0} for state in ('active','inactive')}
matches={}
for match in [m for names in manifest['split'].values() for m in names]:
    data=load_cache(root/'cache'/match)
    finite=np.isfinite(data.ball_xy).all(axis=1)
    contiguous=np.r_[False,(data.periods[1:]==data.periods[:-1])&(data.source_frames[1:]==data.source_frames[:-1]+1)]
    same=np.r_[False,(data.ball_xy[1:]==data.ball_xy[:-1]).all(axis=1)]&contiguous
    origin=np.isclose(data.ball_xy[:,0],52.65,atol=.001)&np.isclose(data.ball_xy[:,1],34,atol=.001)
    result={}
    for name,mask in [('active',data.reference<2),('inactive',data.reference==2)]:
        values=dict(frames=int(mask.sum()),finite_xy=int((mask&finite).sum()),
                    same_xy_as_previous_contiguous_frame=int((mask&same).sum()),raw_origin_sentinel=int((mask&origin).sum()))
        result[name]=values
        for key,value in values.items():
            totals[name][key]+=value
    matches[match]=result
report=dict(schema_version=1,model_id=manifest['artifact_sha256'],post_freeze_validity_audit=True,
            used_for_model_selection=False,model_or_policy_changed=False,totals=totals,matches=matches,
            interpretation='Inactive numeric ball positions are almost always carried forward. Finite availability is not fresh observation. Motion features can exploit a provider convention; D agreement does not establish transferable physical stoppage detection.',
            M_definition='minute of play, per primary paper; not a measurement-validity flag',
            primary_source='https://pmc.ncbi.nlm.nih.gov/articles/PMC11787359/')
path=root/'reports'/'provider-coordinate-audit.json'
path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(totals,indent=2))
