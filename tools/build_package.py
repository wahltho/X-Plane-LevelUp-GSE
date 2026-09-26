"""Build an Option-B-only schema-4 MTK package and standalone distribution."""
import hashlib,json,shutil,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
VERSION='0.2.0-preview.3'
PACKAGE='jt8d17.levelup-737ng.gse'
SCRIPT='plugins/xlua/scripts/LU_737NG.GSE'
SCOPES=['objects/GSE','objects/LU_GSE_stairs',SCRIPT]
def sha(b):return hashlib.sha256(b).hexdigest()
def build():
 out=ROOT/'dist'/('levelup-gse-'+VERSION)
 if out.exists():shutil.rmtree(out)
 out.mkdir(parents=True)
 previous=json.loads((ROOT/'packaging/previous_payloads.json').read_text())
 sources={SCRIPT+'/'+p.name:p.read_bytes() for p in sorted((ROOT/'runtime').glob('*.lua'))}
 for p in sorted((ROOT/'assets/stairs').iterdir()):
  if p.suffix in ('.obj','.png'):sources['objects/LU_GSE_stairs/'+p.name]=p.read_bytes()
 sources['objects/GSE/README_LU_GSE.txt']=b'Native GSE objects retired reversibly by LevelUp GSE Option B. Use the installing tool to restore.\n'
 profiles=json.loads((ROOT/'packaging/profiles.json').read_text())
 forbidden={v['sha256'] for m in profiles['models'].values() for v in [m]+m['dependencies']}
 retired=json.loads((ROOT/'packaging/retired.json').read_text())
 forbidden.update(h for hs in retired.values() for h in hs)
 if any(sha(v) in forbidden for v in sources.values()):raise ValueError('Third-party asset in package')
 module=dict(moduleId='gse',displayName='LevelUp GSE (Option B)',description='Local Laminar equipment and original static fallback stairs. Preview: simulator fit acceptance pending.',policy='optional',defaultEnabled=False,installationOrder=50,supportedUpstreamReleases=[],requires=[],conflictsWith=[],payloads=[],targets=[],retiredFiles=[dict(relativePath=k,sourceSha256=v) for k,v in sorted(retired.items())],managedScopes=[dict(relativePath=s,mode='flatExclusive') for s in SCOPES])
 for target,content in sorted(sources.items()):
  p=out/'modules/gse'/target;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(content)
  module['payloads'].append(dict(path=target,size=len(content),sha256=sha(content)))
  module['targets'].append(dict(operation='copy-file-v1',payload=target,relativePath=target,sourceSha256=previous.get(target,[]),resultSha256=sha(content)))
 manifest=dict(schemaVersion=4,packageType='compatibilityPackage',packageId=PACKAGE,packageVersion=VERSION,repositoryUrl='https://github.com/wahltho/X-Plane-LevelUp-GSE',aircraftFamily='LevelUp 737NG',supportedProducts=['levelup-737ng'],supportedUpstreamReleases=[],restartRequired=True,modules=[module])
 (out/'package-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 (out/'profiles.json').write_text(json.dumps(profiles,indent=2)+'\n')
 for name in ['z_Install.py','README.md','INSTALLATION.md','LICENSE']:
  if (ROOT/name).is_file():shutil.copy2(ROOT/name,out/name)
 archive=out.parent/(out.name+'.zip')
 with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
  for p in sorted(out.rglob('*')):
   if p.is_file():
    i=zipfile.ZipInfo(p.relative_to(out).as_posix(),(2026,1,1,0,0,0));i.compress_type=zipfile.ZIP_DEFLATED;i.external_attr=0o100644<<16;z.writestr(i,p.read_bytes())
 archive.with_suffix('.zip.sha256').write_text(sha(archive.read_bytes())+'  '+archive.name+'\n')
 print(archive);return out
if __name__=='__main__':build()
