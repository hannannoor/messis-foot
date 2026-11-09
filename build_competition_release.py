"""Deterministically build the selected-only artifact without importing its sources."""
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import stat
import tempfile


LOADER = '''
import sys as _sys
if any(_name in _sys.modules for _name in SOURCES):
    raise SystemExit('Existing module conflicts with isolated release; use a fresh interpreter')
import hashlib as _hashlib
import importlib.abc as _abc
import importlib.util as _util
import importlib as _importlib
from pathlib import Path as _Path

if set(SOURCES) != set(SOURCE_PATHS) or set(MANIFEST['sources']) != set(SOURCE_PATHS.values()):
    raise SystemExit('Embedded source inventory mismatch')
for _name, _source in SOURCES.items():
    if _hashlib.sha256(_source.encode('utf-8')).hexdigest() != MANIFEST['sources'][SOURCE_PATHS[_name]]:
        raise SystemExit('Embedded source identity mismatch')

_ARTIFACT = _Path(__file__).resolve()
_ARTIFACT_SHA256 = _hashlib.sha256(_ARTIFACT.read_bytes()).hexdigest()
class _SourceLoader(_abc.MetaPathFinder, _abc.Loader):
    def find_spec(self, fullname, path=None, target=None):
        if fullname in SOURCES:
            return _util.spec_from_loader(fullname, self, is_package=fullname == 'gap_solver')
        return None
    def create_module(self, spec):
        return None
    def exec_module(self, module):
        module.__file__ = str(_ARTIFACT) + '!/' + SOURCE_PATHS[module.__name__]
        if module.__name__ == 'release_runtime':
            module.__dict__.update(_BUNDLE_MANIFEST=MANIFEST, _BUNDLE_ARTIFACT=_ARTIFACT,
                                   _BUNDLE_START_SHA256=_ARTIFACT_SHA256)
        exec(compile(SOURCES[module.__name__], module.__file__, 'exec'), module.__dict__)

_sys.meta_path.insert(0, _SourceLoader())
_runtime = _importlib.import_module('release_runtime')
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


def _render_release(paths, sources, manifest) -> bytes:
    result = ('"""Generated frozen-control release. Rebuild with build_competition_release.py."""\n'
              'SOURCES = '+repr(sources)+'\nSOURCE_PATHS = '+repr(paths)+'\nMANIFEST = '+repr(manifest)+'\n'+LOADER)
    ast.parse(result)
    return result.encode('utf-8')


def build_release(root: Path) -> bytes:
    return _render_release(*_parts(root))


def _reject_linked_output(path: Path) -> None:
    for part in (path, *path.parents):
        try:
            info = part.lstat()
        except FileNotFoundError:
            continue
        if (stat.S_ISLNK(info.st_mode)
                or getattr(info, 'st_file_attributes', 0) & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 1024)
                or part == path and stat.S_ISREG(info.st_mode) and info.st_nlink > 1):
            raise ValueError('Generated output must not use links or reparse points')


def _publish_owned_file(path: Path, data: bytes) -> None:
    _reject_linked_output(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    _reject_linked_output(path)
    descriptor, temporary = tempfile.mkstemp(prefix='.'+path.name+'.', suffix='.tmp', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'wb') as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        _reject_linked_output(path)
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Check committed generated files without changing them')
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parent
    parts = _parts(root)
    data = _render_release(*parts)
    manifest = (json.dumps(parts[2], indent=2, sort_keys=True)+'\n').encode('utf-8')
    outputs = {root/'competition_release.py': data, root/'release/manifest.json': manifest}
    if args.check:
        if any(not path.is_file() or path.read_bytes() != value for path, value in outputs.items()):
            parser.error('Generated release differs; rebuild the selected artifact')
        print('Release artifact and manifest match selected sources')
    else:
        for path in outputs:
            _reject_linked_output(path)
        for path, value in outputs.items():
            _publish_owned_file(path, value)
        print('Built selected-only release: '+hashlib.sha256(data).hexdigest())
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
