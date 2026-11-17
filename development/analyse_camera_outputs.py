"""Local aggregate camera audit. No video display, possession scoring or parameter tuning."""
import argparse
import csv
import json
from collections import Counter
from math import isfinite
from pathlib import Path
from statistics import median
import xml.etree.ElementTree as ET

from gap_solver.fusion import Scene,verify_geometry
from gap_solver.io import BLOCKS,_number


def camera(root,source,discovery,selected):
    stem=root/(source+' cam')/('BAR-ATH_'+source)
    metadata=ET.parse(str(stem)+'_atd.xml').getroot()
    team_nodes=list(metadata.iter('Team'))
    teams=[t.get('id') for t in team_nodes]
    names=[t.findtext('Name') or '' for t in team_nodes]
    slots=[teams.index(p.get('teamId')) for p in metadata.iter('Player')]
    transforms=[]
    error_values=[]
    with open(str(stem)+'_homography.csv',newline='',encoding='utf-8-sig') as handle:
        for i,row in enumerate(csv.DictReader(handle)):
            if int(row['frame'])!=i:
                raise ValueError(source+' homography IDs are not contiguous')
            matrix=[_number(row['h'+str(a)+str(b)]) for a in range(3) for b in range(3)]
            valid=row['valid'].strip()=='1' and all(v is not None for v in matrix)
            if valid:
                a,b,c,d,e,f,g,h,j=matrix
                determinant=a*(e*j-f*h)-b*(d*j-f*g)+c*(d*h-e*g)
                scale=max(abs(v) for v in matrix)
                valid=scale>0 and abs(determinant)>1e-12*scale**3
            error=_number(row['reprojection_error'])
            transforms.append((valid,error if error is not None else float('inf')))
            if valid and error is not None:
                error_values.append(error)
    counts=Counter()
    ball_mask=[]
    scenes={}
    visible_player_totals=[0,0]
    with open(str(stem)+'_atd.txt',encoding='utf-8-sig') as handle:
        for i,line in enumerate(handle):
            parts=line.strip().split(':')
            if len(parts)!=3 or int(parts[0])!=i+1:
                raise ValueError(source+' tracking IDs are not contiguous')
            players=parts[1].split(';')
            if len(players)!=len(slots):
                raise ValueError(source+' tracking player slots disagree with metadata')
            coords=parts[2].split(',')
            x,y=_number(coords[0]),_number(coords[1])
            observed=x is not None and y is not None
            ball_mask.append(observed)
            counts['tracking_frames']+=1
            counts['ball_observed_frames']+=observed
            graded=source=='tactical' and any(first<=i<=last for _,first,last in BLOCKS)
            counts['graded_frames']+=graded
            counts['graded_ball_observed_frames']+=graded and observed
            positions=[[],[]]
            for side,player in zip(slots,players):
                xyz=player.split(',')
                px,py=_number(xyz[0]),_number(xyz[1])
                if px is not None and py is not None:
                    visible_player_totals[side]+=1
                    if i in selected:
                        positions[side].append((px*105.3,py*68))
            if i in selected and i<len(transforms):
                valid,error=transforms[i]
                scenes[i]=Scene(tuple(positions[0]),tuple(positions[1]),
                                (x*105.3,y*68) if observed else None,valid,error)
    counts=dict(counts)
    counts.update(video_frames=discovery['frame_count'],homography_rows=len(transforms),
                  tracking_minus_video_frames=counts['tracking_frames']-discovery['frame_count'],
                  homography_valid_frames=sum(v for v,_ in transforms),
                  homography_within_existing_error_limit_frames=sum(v and e<=3 for v,e in transforms),
                  median_valid_reprojection_error=median(error_values) if error_values else None,
                  ball_observed_percent=round(100*counts['ball_observed_frames']/counts['tracking_frames'],3),
                  average_observed_players_by_team=[round(n/counts['tracking_frames'],3) for n in visible_player_totals],
                  sparse_samples=discovery['sample_count'],sparse_clock_samples=discovery['samples_with_clock_candidate'],
                  sparse_clock_percent=round(100*discovery['samples_with_clock_candidate']/discovery['sample_count'],3),
                  sparse_segments=discovery['candidate_segment_count'])
    if counts['graded_frames']:
        counts['graded_missing_ball_frames']=counts['graded_frames']-counts['graded_ball_observed_frames']
    if len(transforms)!=counts['tracking_frames']:
        raise ValueError(source+' homography and tracking dimensions differ')
    return counts,ball_mask,scenes,names


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--data-root',required=True)
    parser.add_argument('--sync-dir',required=True)
    parser.add_argument('--out',required=True)
    args=parser.parse_args()
    root,sync=Path(args.data_root),Path(args.sync_dir)
    reports={s:json.loads((root/'run files'/'outputs'/(s+'-discovery.json')).read_text()) for s in ('tactical','broadcast')}
    mapping=[]
    statuses=Counter()
    with (sync/'alignment.csv').open(newline='',encoding='utf-8-sig') as handle:
        for i,row in enumerate(csv.DictReader(handle)):
            if int(row['tactical_frame'])!=i:
                raise ValueError('alignment tactical frame index mismatch')
            statuses[row['status']]+=1
            if row['status']=='clock_candidate':
                mapping.append((i,int(row['broadcast_frame']),float(row['uncertainty_s'])))
    selected={'tactical':{i for i,j,u in mapping},'broadcast':{j for i,j,u in mapping}}
    inputs={s:camera(root,s,reports[s],selected[s]) for s in ('tactical','broadcast')}
    t_stats,t_ball,t_scenes,t_teams=inputs['tactical']
    b_stats,b_ball,b_scenes,b_teams=inputs['broadcast']
    norm=lambda value:value.lower().replace('fc ','').replace('atletic','athletic').strip()
    if tuple(map(norm,t_teams))==tuple(reversed(tuple(map(norm,b_teams)))):
        b_scenes={i:Scene(s.away,s.home,s.ball,s.homography_valid,s.reprojection_error) for i,s in b_scenes.items()}
    elif tuple(map(norm,t_teams))!=tuple(map(norm,b_teams)):
        raise ValueError('team identities do not agree between camera exports')
    geometry=Counter()
    geometry_ok={}
    opportunity=Counter()
    for i,j,uncertainty in mapping:
        if i not in t_scenes or j not in b_scenes:
            raise ValueError('candidate refers to unavailable original tracking frame')
        verification=verify_geometry(t_scenes[i],b_scenes[j])
        geometry[verification.reason]+=1
        geometry_ok[i]=verification.accepted
        opportunity['clock_candidates_with_missing_tactical_ball']+=not t_ball[i]
        opportunity['broadcast_ball_visible_when_tactical_missing']+=not t_ball[i] and b_ball[j]
        opportunity['geometry_consistent_with_broadcast_ball_when_tactical_missing']+=(
            not t_ball[i] and b_ball[j] and verification.accepted)
    neighborhoods=[i for i in geometry_ok if i-25 in geometry_ok and i+25 in geometry_ok]
    result=dict(schema_version=1,cameras={'tactical':t_stats,'broadcast':b_stats},
                alignment_status_counts=dict(statuses),candidate_frames=len(mapping),
                candidate_duration_seconds=round(len(mapping)/25,3),
                max_candidate_uncertainty_s=max((u for i,j,u in mapping),default=None),
                geometry_reason_counts=dict(geometry),missing_ball_opportunities=dict(opportunity),
                temporal_geometry_diagnostic=dict(neighbor_spacing_seconds=1,
                    candidate_frames_with_both_neighbors=len(neighborhoods),
                    all_three_geometry_consistent_frames=sum(all(geometry_ok[x] for x in (i-25,i,i+25)) for i in neighborhoods),
                    replay_classifier=False),
                automatic_checks_only=True,parameters_changed_from_match_feedback=False,
                ground_truth_used=False,predictions_checked_against_video=False,accuracy_measured=False,
                possession_fusion_performed=False,
                notes=['Tracking/video count differences are reported, never padded, trimmed or shifted.',
                       'Spatial and temporal geometry concurrence does not establish that pictures are live.',
                       'No possession decisions were changed by this audit.'])
    out=Path(args.out)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    main()
