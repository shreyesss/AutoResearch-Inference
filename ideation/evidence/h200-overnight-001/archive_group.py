"""Append an immutable evidence archive group, preserving workspace-relative paths."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import tarfile
ROOT=Path(__file__).resolve().parent
WORKSPACE=Path('/home/ubuntu')
def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(4*1024*1024),b''):h.update(block)
    return h.hexdigest()
ap=argparse.ArgumentParser();ap.add_argument('--name',required=True);ap.add_argument('paths',nargs='+',type=Path);a=ap.parse_args()
archive=ROOT/(a.name+'.tar.zst');manifest=ROOT/(a.name+'.files.json')
if archive.exists() or manifest.exists():raise SystemExit('Refusing to overwrite existing archive group')
files=[]
for path in a.paths:
    path=path.resolve()
    files.extend(p for p in (path.rglob('*') if path.is_dir() else [path]) if p.is_file() and '__pycache__' not in p.parts)
files=sorted(set(files))
rows=[]
for p in files:
    if p.is_symlink():raise ValueError('Archive source symlink: '+str(p))
    rows.append({'path':str(p.relative_to(WORKSPACE)),'bytes':p.stat().st_size,'sha256':digest(p),'mode':p.stat().st_mode&0o777})
with archive.open('xb') as output:
    compressor=subprocess.Popen(['zstd','-q','-T2','-8','-c'],stdin=subprocess.PIPE,stdout=output)
    try:
        with tarfile.open(fileobj=compressor.stdin,mode='w|') as tar:
            for p,row in zip(files,rows):tar.add(p,arcname=row['path'],recursive=False)
        compressor.stdin.close()
        if compressor.wait():raise RuntimeError('Compression failed')
    finally:
        if compressor.poll() is None:compressor.kill();compressor.wait()
if any(digest(p)!=row['sha256'] for p,row in zip(files,rows)):raise RuntimeError('Source changed during archival')
manifest.write_text(json.dumps(rows,indent=2)+'\n')
catalog=ROOT/'ARCHIVES.json';value=json.loads(catalog.read_text()) if catalog.exists() else {'schema_version':1,'groups':[]}
value['groups'].append({'name':a.name,'created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'manifest':manifest.name,'archive_sha256':digest(archive),'files':len(rows),'source_bytes':sum(x['bytes'] for x in rows),'parts':[{'path':archive.name,'bytes':archive.stat().st_size,'sha256':digest(archive)}]})
catalog.write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(value['groups'][-1],indent=2))
