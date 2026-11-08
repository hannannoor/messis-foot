"""Source-only preflight: impossible confidence gates, not prediction correctness."""
import argparse,itertools,json,sys
from pathlib import Path
if __name__=='__main__':sys.path.insert(0,str(Path(__file__).resolve().parent))
from gap_solver.temporal_feasibility import confidence_feasibility


def inspect_artifact(artifact,grid=False):
    if not isinstance(artifact,dict) or type(artifact.get('schema_version')) is not int or artifact['schema_version']!=1:
        raise ValueError('Expected schema_version1 artifact object')
    try:
        model=artifact['model'];cost=artifact['transition_cost']
        if grid:
            temperatures={float(k):v for k,v in artifact['temperatures'].items()}
            if len(temperatures)!=len(artifact['temperatures']) or set(temperatures)!={.5,1.,2.}:raise ValueError('Expected the fixed three calibrated switch multipliers')
            configurations=[(dict(confidence=c,max_gap_s=g,minimum_players=3,switch_multiplier=m),temperatures[m])
                for c,g,m in itertools.product((.9,.95,.975),(2.,5.,10.),(.5,1.,2.))]
        else:configurations=[(artifact['policy'],artifact['temperature'])]
        policies=[confidence_feasibility(model,cost,t,p) for p,t in configurations]
    except (KeyError,TypeError,AttributeError) as error:raise ValueError('Missing or malformed artifact fields; draft inspection requires --grid') from error
    return dict(schema_version=1,scope='baseline_X_only',grid=grid,policies=policies,
        provably_impossible_policies=sum(p['status']=='provably_impossible' for p in policies),
        not_ruled_out_policies=sum(p['status']=='not_ruled_out' for p in policies),
        correctness_measured=False,local_inference_performed=False,
        warning='A ceiling can disprove confidence feasibility; it cannot establish attainable predictions, accuracy or eligible evidence.')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('artifact',type=Path);parser.add_argument('--grid',action='store_true')
    parser.add_argument('--fail-on-impossible',action='store_true',help='exit1 if any configured gate is provably impossible')
    args=parser.parse_args()
    try:
        def reject_constant(value):raise ValueError('Nonstandard JSON numeric constant: '+value)
        artifact=json.loads(args.artifact.read_text(encoding='utf-8'),parse_constant=reject_constant)
        report=inspect_artifact(artifact,args.grid)
    except (OSError,ValueError,OverflowError) as error:
        print(json.dumps(dict(error=str(error)),allow_nan=False));return 2
    print(json.dumps(report,indent=2,allow_nan=False))
    return 1 if args.fail_on_impossible and report['provably_impossible_policies'] else 0


if __name__=='__main__':raise SystemExit(main())
