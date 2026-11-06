"""Rebuild the user's one-file entry point from the local modules, without data."""
import ast
from pathlib import Path

root=Path(__file__).resolve().parent
original=(root/'football_pipeline.original.py').read_text(encoding='utf-8')
tree=ast.parse(original)
sources={}
for file in sorted((root/'gap_solver').glob('*.py')):
    key='gap_solver' if file.name=='__init__.py' else 'gap_solver.'+file.stem
    sources[key]=file.read_text(encoding='utf-8')
prefix='''Temporal external research update, 6 November 2026

New motion/reference adapters and a portable temporal model support independent
development experiments. These research modules do not change the existing
tactical command or install a new local prediction policy. See
TEMPORAL_RECOVERY.md for eligibility, held-out results and limitations.

Frozen tactical possession update, 5 November 2026

The experimental new route is tactical-only. Its small state model was fitted on
four licensed external matches, selected on a fifth, frozen and evaluated on two
held-out matches. Raw BallStatus/BallPossession labels never enter prediction
features. Standard-library inference and model data are embedded in this file.

python football_pipeline.py tactical run --data-dir "C:\\football-data" --out outputs/tactical-validated

This route uses tracking geometry and the existing homography reliability gate.
It does not use video, challenge ground truth, Smart Tagging as model features,
or the disputed fixed pre-kickoff D interval. Local reports measure coverage and
behavior; challenge accuracy remains unmeasured. Model leaf support is not a
calibrated correctness probability. Keep residual uncertainty instead of blindly
filling unknown frames. Reproducible external metrics and limitations are recorded
in FOUR_GOALS.md. External inactive coordinates are usually frozen; motion features
can exploit this provider convention. External D agreement is not proof of robust
stoppage recognition, and conditional H/A metrics slightly regress. This is a
candidate for further independent validation. The historical camera experiment below remains available but
is paused; do not interpret clock discovery as verified possession evidence.

Automatic dense synchronization update, 5 November 2026

Run camera auto-sync with both original video paths and both discovery reports.
It derives processing windows/crops automatically, uses the published tactical
evaluation half windows as structural metadata and leaves overlapping half clocks
ambiguous. It writes a separate automatic output folder. It uses unchanged .7
OCR confidence, stride 5 and .25-second combined timing limits. No fitting,
parameter tuning, manual game labels or prediction/video checks are performed.

Example:
python football_pipeline.py camera auto-sync --tactical-video "data/tactical cam/BAR-ATH_tactical.mp4" --broadcast-video "data/broadcast cam/BAR-ATH_broadcast.mp4" --tactical-discovery outputs/tactical-discovery.json --broadcast-discovery outputs/broadcast-discovery.json --out outputs/automatic-sync

These are clock candidates, not replay-verified possession evidence.
No fusion is performed, live_verified/ready_for_fusion remain false, and
unsupported timing is left blank. This stage does not apply the disputed
pre-kickoff D labels. Earlier guide content below records historical experiments.

'''
replacements=[]
for node in tree.body:
    if not isinstance(node,ast.Assign):
        continue
    names=[n.id for n in node.targets if isinstance(n,ast.Name)]
    if 'SOURCES' in names:
        content='SOURCES = {\n'+''.join('    {!r}: r\'\'\'{}\'\'\',\n'.format(key,value) for key,value in sources.items())+'}'
    elif 'VERSION' in names:
        content="VERSION = '2026.11.06-temporal-research'"
    elif 'GUIDE' in names:
        content='GUIDE = '+repr(prefix+ast.literal_eval(node.value))
    else:
        continue
    replacements.append((node.lineno-1,node.end_lineno,content))
lines=original.splitlines(keepends=True)
for start,end,content in sorted(replacements,reverse=True):
    lines[start:end]=[content+'\n']
output=''.join(lines)
route='    importlib.import_module(module).main()'
assert output.count(route)==1
output=output.replace(route,'    if len(sys.argv) > 1 and sys.argv[1] == "tactical":\n        sys.argv.pop(1)\n        module = "gap_solver.tactical_cli"\n'+route)
ast.parse(output,feature_version=(3,9))
(root/'football_pipeline.py').write_text(output,encoding='utf-8')
bundled=next(ast.literal_eval(n.value) for n in ast.parse(output).body if isinstance(n,ast.Assign)
             and any(isinstance(t,ast.Name) and t.id=='SOURCES' for t in n.targets))
assert bundled==sources
print('Rebuilt standalone with exact parity across {} modules; Python 3.9 syntax verified.'.format(len(sources)))
