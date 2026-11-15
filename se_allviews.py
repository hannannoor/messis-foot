"""Score tag@power with cfgs on clean dev + the 5 ball-loss views:  python se_allviews.py <tag@p> <cfg> [<cfg> ...]"""
import subprocess, sys
tag, cfgs = sys.argv[1], sys.argv[2:]
for extra in ([], ['--deg'], ['--view', 'cases_evalg1'], ['--view', 'cases_evalg2'], ['--view', 'cases_evalr1'],
              ['--view', 'cases_evalr2']):
    r = subprocess.run([sys.executable, '-W', 'ignore', 'se_score2.py', tag, *cfgs, *extra], capture_output=True, text=True)
    if r.returncode:
        print(r.stderr[-2000:]); sys.exit(1)
print('scored', tag, cfgs)
