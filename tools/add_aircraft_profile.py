"""Register hash-bound aircraft profiles from verified local release fixtures.
Only numeric measurements/hashes are written; no foreign artwork is packaged.
"""
import argparse,copy,importlib.util,json,sys
from pathlib import Path
from import_profiles import lua,sha
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('measure',ROOT/'asset_sources/stairs/measure_levelup_stairs.py')
measure=importlib.util.module_from_spec(spec);spec.loader.exec_module(measure)
def add(root,label,manifest=None):
 data=json.loads((ROOT/'packaging/profiles.json').read_text())
 dest=ROOT/'packaging/aircraft_profiles.json'
 profiles=json.loads(dest.read_text()) if dest.exists() else {}
 approved={f['path']:f['sha256'] for f in json.loads(manifest.read_text())['files']} if manifest else None
 for name,base in data['variants'].items():
  acf=root/name;obj=root/base['door_object']['path']
  if approved is not None:
   assert sha(acf)==approved[name] and sha(obj)==approved[base['door_object']['path']],name
  text=acf.read_text();raw={t[1]:t[2] for line in text.splitlines() if len(t:=line.split())==3 and t[0]=='P'}
  vals={k:float(raw[k]) for k in base['signature']}
  assert vals==base['signature'], 'service anchors require new calibration: '+name
  ref=next(k.rsplit('/',1)[0] for k,v in raw.items() if k.endswith('/_v10_att_file_stl') and v==base['door_object']['path'][8:])
  sig={k:v for k,v in raw.items() if k.startswith(ref+'/')}
  # Station coordinates are measured in body axes; require an identity attachment.
  for suffix in ('phi','psi','the'):
   assert float(raw[ref+'/_v10_att_'+suffix+'_ref'])==0
  for axis in 'xyz':assert float(raw[ref+'/_v10_att_'+axis+'_acf_prt_ref'])==0
  vertices,indices,lines=measure.parse_obj8(obj)
  doors={d:measure.door_threshold(vertices,indices,lines,d)['xyz_m'] for d in ('L1','L2')}
  assert doors==base['doors'], 'door geometry requires recalibration: '+name
  candidate=copy.deepcopy(base);candidate.update(release=label,acf_sha256=sha(acf),object_signature=sig,doors=doors,
      cg=[0,float(raw['acf/_cgY'])*.3048,float(raw['acf/_cgZ'])*.3048],door_object={'path':base['door_object']['path'],'sha256':sha(obj)})
  candidates=profiles.setdefault(name,[])
  candidates[:]=[p for p in candidates if p.get('release')!=label]
  candidates.append(candidate)
 dest.write_text(json.dumps(profiles,indent=2)+'\n')
 data['aircraft_profiles']=profiles
 (ROOT/'packaging/profiles.json').write_text(json.dumps(data,indent=2)+'\n')
 (ROOT/'runtime/profiles.lua').write_text('-- Generated numeric profiles; no third-party mesh or texture data.\nlocal P='+lua(data)+"\nif real_table then real_table('LU_GSE_profiles',P) else LU_GSE_profiles=P end\nreturn P\n")
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);p.add_argument('--label',required=True);p.add_argument('--manifest',type=Path)
 a=p.parse_args();add(a.root,a.label,a.manifest)
