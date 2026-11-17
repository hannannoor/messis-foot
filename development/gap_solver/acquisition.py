"""Verified external acquisition with no unverified resume or overwrite of edited caches."""
import hashlib
import os
from pathlib import Path
import tempfile
import urllib.request


def asset_digest(path,size,algorithm):
    digest=hashlib.sha256() if algorithm=='sha256' else hashlib.sha1()
    if algorithm=='git_blob_sha1':digest.update(b'blob '+str(size).encode()+b'\0')
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda:handle.read(4*1024*1024),b''):digest.update(chunk)
    return digest.hexdigest()


def acquire_asset(url,destination,size,expected,algorithm='sha256'):
    destination=Path(destination)
    length=64 if algorithm=='sha256' else 40
    if algorithm not in ('sha256','git_blob_sha1') or type(size) is not int or size<0 or len(expected)!=length or any(c not in '0123456789abcdef' for c in expected):
        raise ValueError('invalid immutable acquisition identity')
    if destination.is_symlink():raise ValueError('external asset destination cannot be a link')
    def verified(path):return path.stat().st_size==size and asset_digest(path,size,algorithm)==expected
    if destination.exists():
        if not destination.is_file() or not verified(destination):raise ValueError('Existing external asset differs; preserving it: '+str(destination))
        return dict(path=str(destination),bytes=size,digest=expected,cached=True)
    destination.parent.mkdir(parents=True,exist_ok=True)
    descriptor,temporary=tempfile.mkstemp(prefix='.'+destination.name+'.download-',suffix='.part',dir=destination.parent)
    temporary=Path(temporary)
    with os.fdopen(descriptor,'wb') as output:
        with urllib.request.urlopen(url,timeout=90) as response:
            for chunk in iter(lambda:response.read(4*1024*1024),b''):output.write(chunk)
    if not verified(temporary):raise ValueError('Source size/checksum mismatch; unverified partial preserved: '+str(temporary))
    if destination.exists():
        if not verified(destination):raise ValueError('External destination changed during acquisition; preserving both files')
        temporary.unlink()
    elif os.name=='nt':
        # Unlike POSIX rename, Windows rename refuses an existing destination.
        os.rename(temporary,destination)
    else:
        os.link(temporary,destination)
        temporary.unlink()
    return dict(path=str(destination),bytes=size,digest=expected,cached=False)
