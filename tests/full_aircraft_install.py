"""Run against an expendable COMPLETE supported aircraft export, never a live install.
The caller supplies the built package and scratch aircraft. Every file is hashed
before/after restore; the original ACFs are retained after each variant test.
"""
from pathlib import Path
import argparse,subprocess,hashlib
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--package',required=True,type=Path)
parser.add_argument('--scratch-aircraft',required=True,type=Path)
args=parser.parse_args()
pkg=args.package.resolve();root=args.scratch_aircraft.resolve()
def snapshot(root):
 return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file()}
def run(root,cmd,ok=True):
 r=subprocess.run(['python3',str(pkg/'z_Install.py'),cmd,'--aircraft-root',str(root)],capture_output=True,text=True)
 if ok:assert r.returncode==0,(cmd,r.stdout,r.stderr)
 else:assert r.returncode!=0,(cmd,r.stdout,r.stderr)
 return (r.stdout+r.stderr).strip()
assert len(list(root.glob('*.acf')))==5,'Expected all five original ACFs'
native=root/'objects/GSE'
assert not native.exists() or len(list(native.iterdir()))==12,'Expected absent or complete original GSE scope'
for acf in sorted(root.glob('*.acf')):
 others={p:p.read_bytes() for p in root.glob('*.acf') if p!=acf}
 for p in others:p.unlink()
 try:
  before=snapshot(root)
  run(root,'check');run(root,'install');run(root,'verify')
  assert 'Already installed' in run(root,'install')
  run(root,'uninstall');assert snapshot(root)==before
  print(acf.name, 'check/install/verify/repeat/full restore PASS',flush=True)
 finally:
  for p,b in others.items():p.write_bytes(b)

before=snapshot(root)
for name in ['737misc2.dds','asu.obj','gpu.obj']:
 p=root/'objects/GSE'/name
 if not p.exists():continue
 b=p.read_bytes()
 try:
  p.write_bytes(b+b'altered');bad=snapshot(root)
  for cmd in ['check','install']:
   assert 'Unrecognized original' in run(root,cmd,False)
   assert snapshot(root)==bad,'Rejected operation changed files'
 finally:p.write_bytes(b)
existed=native.exists();native.mkdir(exist_ok=True)
p=root/'objects/GSE/unknown-test.obj'
assert not p.exists()
try:
 p.write_bytes(b'unknown');bad=snapshot(root)
 for cmd in ['check','install']:
  assert 'Unknown native GSE' in run(root,cmd,False)
  assert snapshot(root)==bad
finally:
 p.unlink()
 if not existed:native.rmdir()
assert snapshot(root)==before
print('Modified and unknown originals rejected without writes')
