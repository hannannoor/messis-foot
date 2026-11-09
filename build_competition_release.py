"""Deterministically build the selected-only artifact without importing its sources."""
import argparse
import ast
import hashlib
import json
from pathlib import Path


LOADER = '''
import hashlib as _hashlib
import importlib.abc as _abc
import importlib.util as _util
import importlib as _importlib
from pathlib import Path as _Path
import sys as _sys

if set(SOURCES) != set(SOURCE_PATHS) or set(MANIFEST['sources']) != set(SOURCE_PATHS.values()):
    raise SystemExit('Embedded source inventory mismatch')
for _name, _source in SOURCES.items():
    if _hashlib.sha256(_source.encode('utf-8')).hexdigest() != MANIFEST['sources'][SOURCE_PATHS[_name]]:
        raise SystemExit('Embedded source identity mismatch')

_ARTIFACT = _Path(__file__).resolve()
class _SourceLoader(_abc.MetaPathFinder, _abc.Loader):
    def find_spec(self, fullname, path=None, target=None):
        if fullname in SOURCES:
            return _util.spec_from_loader(fullname, self, is_package=fullname == 'gap_solver')
        return None
    def create_module(self, spec):
        return None
    def exec_module(self, module):
        module.__file__ = str(_ARTIFACT) + '!/' + SOURCE_PATHS[module.__name__]
        exec(compile(SOURCES[module.__name__], module.__file__, 'exec'), module.__dict__)

_sys.meta_path.insert(0, _SourceLoader())
_runtime = _importlib.import_module('release_runtime')
_runtime._BUNDLE_MANIFEST = MANIFEST
_runtime._BUNDLE_ARTIFACT = _ARTIFACT
for _name in ('run_source', 'predict_selected', 'load_source', 'semantic_sha256', 'submission_bytes'):
    globals()[_name] = getattr(_runtime, _name)
if __name__ == '__main__':
    raise SystemExit(_runtime.main())
'''


def _parts(root: Path):
    root = Path(root)
    tree = ast.parse((root/'release_runtime.py').read_bytes().decode('utf-8'))
    constants = {node.targets[0].id: ast.literal_eval(node.value) for node in tree.body
                 if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name)
                 and node.targets[0].id in ('SOURCE_FILES', 'RELEASE_SETTINGS')}
    paths = dict(sorted(constants['SOURCE_FILES'].items()))
    sources = {name: (root/path).read_bytes().decode('utf-8') for name, path in paths.items()}
    hashes = {paths[name]: hashlib.sha256(source.encode('utf-8')).hexdigest() for name, source in sources.items()}
    manifest = dict(constants['RELEASE_SETTINGS'], sources=dict(sorted(hashes.items())))
    return paths, sources, manifest


def build_release(root: Path) -> bytes:
    paths, sources, manifest = _parts(root)
    result = ('"""Generated frozen-control release. Rebuild with build_competition_release.py."""\n'
              'SOURCES = '+repr(sources)+'\nSOURCE_PATHS = '+repr(paths)+'\nMANIFEST = '+repr(manifest)+'\n'+LOADER)
    ast.parse(result)
    return result.encode('utf-8')


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Check committed generated files without changing them')
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parent
    data = build_release(root)
    manifest = (json.dumps(_parts(root)[2], indent=2, sort_keys=True)+'\n').encode('utf-8')
    outputs = {root/'competition_release.py': data, root/'release/manifest.json': manifest}
    if args.check:
        if any(not path.is_file() or path.read_bytes() != value for path, value in outputs.items()):
            parser.error('Generated release differs; rebuild the selected artifact')
        print('Release artifact and manifest match selected sources')
    else:
        for path, value in outputs.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(value)
        print('Built selected-only release: '+hashlib.sha256(data).hexdigest())
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
