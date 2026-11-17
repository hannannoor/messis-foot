"""One-shot acquisition of pinned public Metrica sample assets; no scoring."""
import argparse,hashlib,json,re
from pathlib import Path,PurePosixPath
import urllib.request
from gap_solver.input_contract import reject_linked_ancestors
from touch_experiment import write_new,read

REPOSITORY='metrica-sports/sample-data'


def download_asset(root,item,commit,opener=urllib.request.urlopen):
    root=Path(root);name=item['path'];parts=PurePosixPath(name)
    if (not re.fullmatch('[0-9a-f]{40}',commit) or parts.is_absolute() or '..' in parts.parts
        or '\\' in name or ':' in name or not name or not re.fullmatch('[0-9a-f]{40}',item['git_blob_sha1'])
        or type(item['bytes']) is not int or item['bytes']<=0):raise ValueError('Unsafe public source manifest')
    target=root.joinpath(*parts.parts);reject_linked_ancestors(target)
    if target.exists():raise FileExistsError('Source asset already exists')
    root.mkdir(parents=True,exist_ok=True)
    key=hashlib.sha256(name.encode()).hexdigest()
    write_new(root/'claims'/(key+'.json'),dict(path=name,commit=commit,expected_blob=item['git_blob_sha1']))
    target.parent.mkdir(parents=True,exist_ok=True)
    identity=hashlib.sha1(b'blob '+str(item['bytes']).encode()+b'\0');digest=hashlib.sha256();size=0
    url='https://raw.githubusercontent.com/'+REPOSITORY+'/'+commit+'/'+name
    with target.open('xb') as destination,opener(urllib.request.Request(url,headers={'User-Agent':'MESSIS-FOOT-source-reproduction'}),timeout=90) as source:
        for block in iter(lambda:source.read(1024*1024),b''):
            size+=len(block)
            if size>item['bytes']:raise ValueError('Source exceeds pinned size')
            identity.update(block);digest.update(block);destination.write(block)
    if size!=item['bytes'] or identity.hexdigest()!=item['git_blob_sha1']:raise ValueError('Pinned source identity differs')
    return dict(path=name,bytes=size,git_blob_sha1=identity.hexdigest(),sha256=digest.hexdigest())


def acquire(manifest_path,directory,report):
    manifest=read(manifest_path);directory=Path(directory);report=Path(report)
    if manifest['repository']!=REPOSITORY or directory.exists() or report.exists():raise FileExistsError('Acquisition requires new owned paths')
    directory.mkdir(parents=True)
    write_new(directory/'acquisition-entry.json',dict(manifest_sha256=hashlib.sha256(Path(manifest_path).read_bytes()).hexdigest()))
    result=[]
    for item in manifest['assets']:
        value=download_asset(directory,item,manifest['commit']);result.append(value)
        print(json.dumps(dict(acquired=len(result),total=len(manifest['assets']),path=item['path'])),flush=True)
    receipt=dict(schema_version=1,repository=REPOSITORY,commit=manifest['commit'],assets=result,
        manifest_sha256=hashlib.sha256(Path(manifest_path).read_bytes()).hexdigest(),complete=True,
        raw_data_published=False,inference_calls=0,scoring_calls=0)
    write_new(directory/'acquisition-receipt.json',receipt);write_new(report,receipt)
    return dict(complete=True,assets=len(result),scoring_calls=0)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--manifest',required=True);parser.add_argument('--directory',required=True);parser.add_argument('--report',required=True)
    args=parser.parse_args()
    try:result=acquire(args.manifest,args.directory,args.report)
    except Exception as error:
        raise SystemExit('Metrica acquisition stopped: '+type(error).__name__+'; claim/partial files preserved; no automatic retry.') from None
    print(json.dumps(result,sort_keys=True))

if __name__=='__main__':main()
