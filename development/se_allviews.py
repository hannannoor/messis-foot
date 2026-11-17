"""Score tag@power with cfgs on clean dev + the 5 ball-loss views:  python se_allviews.py <tag@p> <cfg> [<cfg> ...]"""
import subprocess, sys
args = sys.argv[1:]
extra_args = []
if '--bnd' in args:
    i = args.index('--bnd'); extra_args = args[i:i + 2]; del args[i:i + 2]
views = None
if '--views' in args:
    i = args.index('--views'); views = args[i + 1].split(','); del args[i:i + 2]
tag, cfgs = args[0], args[1:]
ALL = [[], ['--deg'], ['--view', 'cases_evalg1'], ['--view', 'cases_evalg2'], ['--view', 'cases_evalr1'],
       ['--view', 'cases_evalr2'], ['--view', 'cases_evalp'], ['--view', 'cases_evalrp']]
for extra in ALL if views is None else [v for v in ALL if (v[-1] if v else 'clean') in views or (v == ['--deg'] and 'deg' in views)]:
    r = subprocess.run([sys.executable, '-W', 'ignore', 'se_score2.py', tag, *cfgs, *extra, *extra_args], capture_output=True, text=True)
    if r.returncode:
        print(r.stderr[-2000:]); sys.exit(1)
print('scored', tag, cfgs)
