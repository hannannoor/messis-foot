"""Write only aggregate contract facts from automatic ATD inputs."""
import argparse,json
from pathlib import Path
from gap_solver.input_contract import audit_source,protect_report_path,write_new_report

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--prefix',required=True);p.add_argument('--scope',choices=['tactical','broadcast'],required=True);p.add_argument('--out',required=True)
    a=p.parse_args();paths=[Path(a.prefix+s) for s in ('_atd.xml','_atd.txt','_homography.csv')];out=Path(a.out)
    protect_report_path(out,paths)
    result=audit_source(*paths,a.scope);write_new_report(out,result,paths)
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
