#!/usr/bin/env python3
"""Standalone LevelUp GSE installer. Python 3.10+, standard library only."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import sys
import tempfile
import subprocess
import platform
import uuid

STATE = '.levelup-gse-patch'
PACKAGE_ID = 'jt8d17.levelup-737ng.gse'
SCRIPT_DIR = 'plugins/xlua/scripts/LU_737NG.GSE'
SCOPES = ('objects/GSE', 'objects/LU_GSE_stairs', SCRIPT_DIR)
MARKER = SCRIPT_DIR + '/.standalone-owner'


class InstallError(Exception):
    pass


def sha(data):
    return hashlib.sha256(data).hexdigest() if data is not None else None


def safe(root, relative):
    parts = PurePosixPath(relative).parts
    if (not parts or relative != '/'.join(parts) or '\\' in relative
            or any(p in ('.', '..') or ':' in p for p in parts)
            or PurePosixPath(relative).is_absolute()):
        raise InstallError(f'Unsafe path: {relative}')
    path = root
    for part in parts:
        if path.is_dir():
            for child in path.iterdir():
                if child.name.casefold() == part.casefold() and child.name != part:
                    raise InstallError(f'Case collision: {child}')
        path /= part
        if path.is_symlink() or (path.exists() and getattr(path.lstat(), 'st_file_attributes', 0)
                                 & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0)):
            raise InstallError(f'Linked path: {path}')
    return path


def read(root, relative):
    p = safe(root, relative)
    if not p.exists():
        return None
    if not p.is_file():
        raise InstallError(f'Not a regular file: {p}')
    return p.read_bytes()


def scope(root, relative):
    p = safe(root, relative)
    if not p.exists():
        return None
    if not p.is_dir():
        raise InstallError(f'Not a directory: {p}')
    return {relative + '/' + f.name: sha(read(root, relative + '/' + f.name))
            for f in p.iterdir()}


def atomic(root, relative, data):
    path = safe(root, relative)
    if data is None:
        path.unlink(missing_ok=True)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.gse-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True) + '\n').encode()


def package(root):
    raw=read(root,'package-manifest.json'); m=json.loads(raw)
    if m['schemaVersion']!=4 or m['packageId']!=PACKAGE_ID or len(m['modules'])!=1:
        raise InstallError('Unsupported package')
    module=m['modules'][0]
    if module['managedScopes'] != [dict(relativePath=s,mode='flatExclusive') for s in SCOPES]:
        raise InstallError('Unexpected scopes')
    payloads={}
    for p in module['payloads']:
        b=read(root,'modules/gse/'+p['path'])
        if b is None or len(b)!=p['size'] or sha(b)!=p['sha256']:raise InstallError('Corrupt payload: '+p['path'])
        payloads[p['path']]=b
    desired,allowed={},{}
    for t in module['targets']:
        path=t['relativePath']
        if t['operation']!='copy-file-v1' or path in desired or str(PurePosixPath(path).parent) not in SCOPES:raise InstallError('Invalid target')
        safe(root,path); b=payloads[t['payload']]
        if sha(b)!=t['resultSha256']:raise InstallError('Bad target hash')
        desired[path]=b;allowed[path]=t['sourceSha256']
    for t in module['retiredFiles']:
        path=t['relativePath']
        if str(PurePosixPath(path).parent)!='objects/GSE' or path in desired:raise InstallError('Bad retirement')
        safe(root,path);desired[path]=None;allowed[path]=t['sourceSha256']
    if len({p.casefold() for p in desired})!=len(desired):raise InstallError('Case-colliding paths')
    desired[MARKER]=b'Standalone installer owns this scope. Uninstall here before switching to MTK.\n';allowed[MARKER]=[]
    return m,sha(raw),desired,allowed

def snapshot(root):return {s:scope(root,s) for s in SCOPES}
def check_aircraft(root,package_root):
    profiles=json.loads(read(package_root,'profiles.json'))
    matched=0
    for name,p in profiles['variants'].items():
        b=read(root,name)
        if b is None:continue
        vals={};rawvals={}
        for line in b.decode(errors='replace').splitlines():
            t=line.split()
            if len(t)==3 and t[0]=='P':
                rawvals[t[1]]=t[2]
                try:vals[t[1]]=float(t[2])
                except ValueError:pass
        import math
        for key,want in p['signature'].items():
            got=vals.get(key)
            if got is None or not math.isfinite(got) or abs(got-want)>.001:raise InstallError('Unsupported ACF geometry: '+name+' '+key)
        for key,want in p.get('object_signature',{}).items():
            if rawvals.get(key)!=want:raise InstallError('Unsupported ACF object transform: '+key)
        obj=p['door_object']
        if sha(read(root,obj['path']))!=obj['sha256']:raise InstallError('Unsupported door geometry: '+obj['path'])
        matched+=1
    if not matched:raise InstallError('No supported LevelUp ACF')
    if not safe(root,'plugins/xlua/scripts').is_dir():raise InstallError('XLua scripts missing')

def load_state(root):
    b=read(root,STATE+'/state.json')
    if b is None:
        if safe(root,STATE).exists():raise InstallError('Incomplete standalone state; use recover, retain backups')
        return None
    s=json.loads(b)
    if s['packageId']!=PACKAGE_ID or s['schemaVersion']!=2:raise InstallError('Unknown/legacy installer state; use original installer')
    for path,r in s['files'].items():
        if str(PurePosixPath(path).parent) not in SCOPES:raise InstallError('Unsafe state target')
        if r['originalSha256'] is not None and sha(read(root,STATE+'/original/'+path))!=r['originalSha256']:raise InstallError('Corrupt original backup: '+path)
    return s

def verify(root,s):
    for path,r in s['files'].items():
        if sha(read(root,path))!=r['installedSha256']:raise InstallError('Installed file changed: '+path)
    for directory in SCOPES:
        expected={p:r['installedSha256'] for p,r in s['files'].items() if str(PurePosixPath(p).parent)==directory and r['installedSha256'] is not None}
        if scope(root,directory)!=expected:raise InstallError('Managed directory changed: '+directory)

def cleanup_completed(root):
    done=STATE+'.completed'
    raw=read(root,done+'/transaction/journal.json')
    if raw is None:raise InstallError('Unrecognized completion archive; retain it for manual recovery')
    j=json.loads(raw)
    if j.get('packageId')!=PACKAGE_ID or not j.get('committed') or not j.get('uninstall'):
        raise InstallError('Unrecognized completion archive ownership')
    previous=read(root,done+'/transaction/before/'+STATE+'/state.json')
    if previous is None or sha(previous)!=j['before'].get(STATE+'/state.json'):
        raise InstallError('Completion archive lacks verified original state')
    old=json.loads(previous)
    if old.get('packageId')!=PACKAGE_ID:raise InstallError('Foreign completion archive')
    expected={'transaction/journal.json'}
    expected.update('transaction/before/'+p for p,h in j['before'].items() if h is not None)
    expected.update('original/'+p for p,r in old['files'].items() if r['originalSha256'] is not None)
    for p in safe(root,done).rglob('*'):
        rel=p.relative_to(safe(root,done)).as_posix();safe(root,done+'/'+rel)
        if p.is_file() and rel not in expected:raise InstallError('Unknown completion archive file: '+rel)
    shutil.rmtree(safe(root,done))

def finish_transaction(root,j):
    if j.get('uninstall'):
        for directory,existed in j['restoreDirectories'].items():
            if not existed:
                try:safe(root,directory).rmdir()
                except FileNotFoundError:pass
        done=STATE+'.completed'
        if safe(root,done).exists():raise InstallError('Previous completion archive needs cleanup')
        os.replace(safe(root,STATE),safe(root,done))
        cleanup_completed(root)
    else:
        shutil.rmtree(safe(root,STATE+'/transaction'))

def recovery(root):
    txn=STATE+'/transaction';raw=read(root,txn+'/journal.json')
    if raw is None:raise InstallError('No recoverable journal; retain state for manual recovery')
    j=json.loads(raw)
    # Reject newly added files in any managed scope before recovery writes.
    for directory,old in j['scopes'].items():
        now=scope(root,directory)
        known=set(old or {})|{p for p in j['after'] if str(PurePosixPath(p).parent)==directory}
        if set(now or {})-known:raise InstallError('Recovery conflict in '+directory)
    for path,old in j['before'].items():
        if path not in j['after'] or (path!=STATE+'/state.json' and str(PurePosixPath(path).parent) not in SCOPES):raise InstallError('Unsafe journal target')
        if sha(read(root,path)) not in (old,j['after'][path]):raise InstallError('Recovery conflict: '+path)
        if old is not None and sha(read(root,txn+'/before/'+path))!=old:raise InstallError('Corrupt recovery image')
    if j.get('committed'):
        for path,want in j['after'].items():
            if sha(read(root,path))!=want:raise InstallError('Committed operation changed: '+path)
        finish_transaction(root,j)
        return 'Committed operation cleanup completed.'
    for path,old in j['before'].items():atomic(root,path,read(root,txn+'/before/'+path) if old is not None else None)
    for directory,old in j['scopes'].items():
        if old is None:
            try:safe(root,directory).rmdir()
            except FileNotFoundError:pass
        else:safe(root,directory).mkdir(parents=True,exist_ok=True)
    shutil.rmtree(safe(root,txn))
    if j['before'].get(STATE+'/state.json') is None:shutil.rmtree(safe(root,STATE))
    return 'Interrupted operation rolled back; original installation state restored.'

def transact(root,changes,old_scopes,restore_directories=None):
    txn=STATE+'/transaction'
    if safe(root,txn).exists():raise InstallError('Pending transaction; use recover')
    before={p:read(root,p) for p in changes}
    if snapshot(root)!=old_scopes:raise InstallError('Concurrent scope change')
    for p,b in before.items():
        if b is not None:atomic(root,txn+'/before/'+p,b)
    j=dict(packageId=PACKAGE_ID,before={p:sha(b) for p,b in before.items()},after={p:sha(b) for p,b in changes.items()},scopes=old_scopes,uninstall=restore_directories is not None,restoreDirectories=restore_directories,committed=False)
    atomic(root,txn+'/journal.json',encoded(j))
    try:
        if snapshot(root)!=old_scopes:raise InstallError('Concurrent scope change')
        for p,b in changes.items():
            if sha(read(root,p))!=j['before'][p]:raise InstallError('Concurrent file change: '+p)
            atomic(root,p,b)
    except BaseException:
        recovery(root);raise
    j['committed']=True
    atomic(root,txn+'/journal.json',encoded(j))
    finish_transaction(root,j)

def run(command,root,package_root):
    if safe(root,STATE+'.completed').exists():cleanup_completed(root)
    if command=='recover':return recovery(root)
    if safe(root,STATE+'/transaction').exists():raise InstallError('Pending transaction; use recover')
    s=load_state(root)
    if command in ('verify','uninstall'):
        if not s:raise InstallError('No standalone installation; use its original owner')
        verify(root,s)
        if command=='verify':return 'Verified '+s['packageVersion']
        changes={p:read(root,STATE+'/original/'+p) if r['originalSha256'] else None for p,r in s['files'].items()}
        changes[STATE+'/state.json']=None
        transact(root,changes,snapshot(root),s['directories'])
        return 'Uninstalled; original GSE restored.'
    check_aircraft(root,package_root)
    m,mhash,desired,allowed=package(package_root)
    old=snapshot(root)
    if s:
        verify(root,s)
        if set(s['files'])-set(desired):raise InstallError('Uninstall previous version first: removed targets')
    elif any(old[directory] for directory in SCOPES if directory!='objects/GSE'):
        raise InstallError('Existing GSE installation: uninstall through MTK/manual owner first')
    if set(old['objects/GSE'] or {})-set(desired):raise InstallError('Unknown native GSE files; no files changed')
    for p,b in desired.items():
        actual=sha(read(root,p))
        if (not s or p not in s['files']) and actual is not None and actual not in allowed[p]:raise InstallError('Unrecognized original: '+p)
    if command=='check':return 'Package/aircraft/scope checks passed; no files changed.'
    if s and s['manifestSha256']==mhash:return 'Already installed and verified.'
    records=dict(s['files']) if s else {}
    for p,b in desired.items():
        if p not in records:
            original=read(root,p);records[p]={'originalSha256':sha(original)}
            if original is not None:atomic(root,STATE+'/original/'+p,original)
        records[p]['installedSha256']=sha(b)
    state=dict(schemaVersion=2,packageId=PACKAGE_ID,packageVersion=m['packageVersion'],manifestSha256=mhash,files=records,directories=s['directories'] if s else {d:v is not None for d,v in old.items()})
    changes=dict(desired);changes[STATE+'/state.json']=encoded(state)
    transact(root,changes,old);verify(root,state)
    return 'Installed '+m['packageVersion']+'; restart X-Plane.'

def ensure_offline():
    if os.name=='nt':
        output=subprocess.check_output(['tasklist','/FO','CSV','/NH'],text=True,errors='replace')
    else:
        output=subprocess.check_output(['ps','-A','-o','comm='],text=True,errors='replace')
    for line in output.splitlines():
        name=Path(line.strip().strip('"').split('","')[0]).name.lower()
        if name in ('x-plane','x-plane.exe','x-plane-x86_64','x-plane-arm64'):
            raise InstallError('Close X-Plane before changing the aircraft.')

def acquire(root,recover=False):
    relative='.levelup-gse-install.lock';lock=safe(root,relative)
    try:lock.mkdir()
    except FileExistsError:
        if not recover:raise InstallError('Installer lock present; after the owner exits use recover')
        raw=read(root,relative+'/owner.json')
        if raw is None:raise InstallError('Incomplete lock: confirm all installers are closed before removing it manually')
        owner=json.loads(raw)
        if owner.get('host')!=platform.node():raise InstallError('Lock belongs to another host; resolve there')
        if os.name=='nt':
            import csv,io
            output=subprocess.check_output(['tasklist','/FI','PID eq '+str(int(owner['pid'])),'/FO','CSV','/NH'],text=True,errors='replace')
            if any(len(row)>1 and row[1]==str(owner['pid']) for row in csv.reader(io.StringIO(output))):
                raise InstallError('Lock owner still exists; concurrent recovery is forbidden')
        else:
            try:os.kill(int(owner['pid']),0)
            except ProcessLookupError:pass
            except PermissionError:raise InstallError('Cannot establish that the lock owner exited')
            else:raise InstallError('Lock owner still exists; concurrent recovery is forbidden')
        # Only a lock with exactly our metadata is removable; never sweep foreign content.
        if {p.name for p in lock.iterdir()}!={'owner.json'}:raise InstallError('Unknown lock contents')
        (lock/'owner.json').unlink();lock.rmdir();lock.mkdir()
    atomic(root,relative+'/owner.json',encoded(dict(pid=os.getpid(),host=platform.node(),token=uuid.uuid4().hex)))
    return lock

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['check','install','verify','uninstall','recover'])
    parser.add_argument('--aircraft-root',required=True,type=Path)
    args=parser.parse_args();root=args.aircraft_root.absolute();lock=None
    try:
        safe(Path(root.anchor),root.relative_to(root.anchor).as_posix())
        if not root.is_dir():raise InstallError('Aircraft directory missing')
        if args.command in ('install','uninstall','recover'):ensure_offline()
        lock=acquire(root,args.command=='recover')
        if args.command=='recover' and not safe(root,STATE+'/transaction').exists():
            if safe(root,STATE+'.completed').exists():
                cleanup_completed(root);print('Completed uninstall cleanup finished.');return 0
            if read(root,STATE+'/state.json') is not None:print('No pending transaction; stale lock cleared.');return 0
        print(run(args.command,root,Path(__file__).resolve().parent));return 0
    except (InstallError,OSError,ValueError,KeyError,TypeError,subprocess.SubprocessError) as e:
        print('GSE: '+str(e),file=sys.stderr);return 1
    finally:
        if lock is not None:
            (lock/'owner.json').unlink();lock.rmdir()
if __name__=='__main__':sys.exit(main())
