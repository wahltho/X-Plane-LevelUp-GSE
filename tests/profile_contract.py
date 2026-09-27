"""Reject modified ACFs and mixed release OBJ pairs using actual release fixtures."""
import argparse,importlib.util,json,shutil,subprocess,tempfile,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser()
for n in ('zip','reference','other-reference','luajit','xlua-init','xplane-root'):p.add_argument('--'+n,required=True,type=Path)
a=p.parse_args()
with tempfile.TemporaryDirectory() as t:
 base=Path(t).resolve();pkg=base/'package'
 with zipfile.ZipFile(a.zip) as z:z.extractall(pkg)
 spec=importlib.util.spec_from_file_location('installer',pkg/'z_Install.py');installer=importlib.util.module_from_spec(spec);spec.loader.exec_module(installer)
 data=json.loads((pkg/'profiles.json').read_text())
 for name,legacy in data['variants'].items():
  root=base/name;root.mkdir();(root/'plugins/xlua/scripts').mkdir(parents=True)
  obj=root/legacy['door_object']['path'];obj.parent.mkdir(parents=True)
  shutil.copy2(a.reference/name,root/name);shutil.copy2(a.reference/legacy['door_object']['path'],obj)
  installer.run('check',root,pkg)
  for case in ('modified-acf','mixed-obj'):
   if case=='modified-acf':
    original=(root/name).read_bytes();(root/name).write_bytes(original+b'\n# local edit\n')
   else:
    original=obj.read_bytes();shutil.copy2(a.other_reference/legacy['door_object']['path'],obj)
   try:installer.run('install',root,pkg)
   except installer.InstallError:pass
   else:raise AssertionError('Unsupported fixture installed')
   assert not (root/installer.STATE).exists()
   r=subprocess.run([str(a.luajit),str(ROOT/'tests/lifecycle.lua'),str(ROOT),str(root),str(a.xplane_root),str(a.xlua_init),str(pkg/'modules/gse/plugins/xlua/scripts/LU_737NG.GSE'),str(pkg/'modules/gse/objects/LU_GSE_stairs'),name,'reject'],capture_output=True,text=True)
   assert r.returncode==0,r.stdout+r.stderr
   (root/name if case=='modified-acf' else obj).write_bytes(original)
   print(name,case,'installer rejects without writes; runtime suppresses PASS',flush=True)
