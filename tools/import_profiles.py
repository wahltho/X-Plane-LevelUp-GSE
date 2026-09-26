"""Import numeric profiles and hashes only. Never copies Laminar/Zibo assets."""
import hashlib,json,re
from model_geometry import sample
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
XP=LR=LU=OLD=PORT=ZIBO=None
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def lua(v):
 if isinstance(v,dict):return '{'+','.join('['+json.dumps(str(k))+']='+lua(x) for k,x in v.items())+'}'
 if isinstance(v,list):return '{'+','.join(map(lua,v))+'}'
 if v is None:return 'nil'
 if isinstance(v,bool):return 'true' if v else 'false'
 return json.dumps(v)
def build():
 port=PORT.read_text()
 section=port.split('kLevelUpGeometries[] = {')[1].split('\n};')[0]
 geoms={}
 keys=['nose','tail','wing','l1','r1','l2','r2','cargo_fwd','cargo_aft','electrical','pneumatic','conditioned_air','fuel']
 for name,body in re.findall(r'Variant::levelup_(\w+),.*?\n(.*?)(?=\n\s*\{Variant|\Z)',section,re.S):
  pairs=[list(map(float,m)) for m in re.findall(r'\{(-?[0-9.]+)f, (-?[0-9.]+)f\}',body)]
  if len(pairs)!=len(keys):raise ValueError((name,len(pairs)))
  station=-pairs[0][0]
  geoms[name]={key:[-xy[1],0,xy[0]+station] for key,xy in zip(keys,pairs)}
 measured=json.loads((ROOT/'docs/levelup_stair_measurements.json').read_text())
 variants={}
 for v,name in zip(measured['variants'],['737_60NG','737_70NG','737_80NG','737_90NG','737_9ENG']):
  vals={};rawvals={}
  for line in (LU/(name+'.acf')).read_text(errors='replace').splitlines():
   t=line.split()
   if len(t)==3 and t[0]=='P':
    rawvals[t[1]]=t[2]
    try:vals[t[1]]=float(t[2])
    except ValueError:pass
  anchors={n:[vals['acf/_'+n+'/'+str(i)]*.3048 for i in range(3)] for n in ['bagg_1','bagg_2','food_1','food_2','board_1','board_2','fueling'] if 'acf/_'+n+'/0' in vals}
  signature={k:x for k,x in vals.items() if re.match(r'acf/_(board_[12]|bagg_[12]|food_[12])/[012]$',k)}
  door_ref=next(k.rsplit('/',1)[0] for k,x in rawvals.items() if k.endswith('_v10_att_file_stl') and Path(x).name==Path(v['fuselage_obj']['path']).name)
  object_signature={k:x for k,x in rawvals.items() if k.startswith(door_ref+'/')}
  variants[name+'.acf']={'object_signature':object_signature,'service':geoms[{'737_60NG':'600','737_70NG':'700','737_80NG':'800','737_90NG':'900','737_9ENG':'900er'}[name]],'id':v['variant'],'signature':signature,'anchors':anchors,'doors':{k:d['xyz_m'] for k,d in v['door_thresholds'].items()},'door_object':{'path':'objects/'+Path(v['fuselage_obj']['path']).parent.name+'/'+Path(v['fuselage_obj']['path']).name,'sha256':v['fuselage_obj']['sha256']},'cg':[0,vals['acf/_cgY']*.3048,vals['acf/_cgZ']*.3048]}
 paths={'gpu':'Ramp_Equipment/GPU_1.obj','asu':'Ramp_Equipment/Air_Start_1.obj','cones':'Common_Elements/Miscellaneous/traffic_cone_1.obj','deice':'snow_equipment/aircraft_deicing_truck_1.obj','bus1':'Ramp_Equipment/pax_bus_1.obj','bus2':'Ramp_Equipment/pax_bus_2.obj','fuel1':'Common_Elements/Vehicles/fuel_truck_large.obj','fuel2':'Common_Elements/Vehicles/fuel_truck_small.obj','catering':'Dynamic_Vehicles/catering_truck.obj','catering_driver':'Dynamic_Vehicles/catering_truck__driver.obj','belt':'Dynamic_Vehicles/TUG_660.obj','belt_driver':'Dynamic_Vehicles/TUG_660__driver.obj'}
 models={}
 for role,rel in paths.items():
  p=LR/rel; deps=[]; refs=set();verts=[]
  for line in p.read_text(errors='replace').splitlines():
   t=line.split()
   if not t or t[0].startswith('#'):continue
   if t[0]=='VT':verts.append(list(map(float,t[1:4])))
   if t[0] in ('TEXTURE','TEXTURE_NORMAL','TEXTURE_LIT') and len(t)>1:
    q=p.parent/t[-1]
    if not q.exists() and q.suffix=='.png':q=q.with_suffix('.dds')
    if not q.is_file():raise ValueError(q)
    deps.append({'path':q.resolve().relative_to(LR.resolve()).as_posix(),'sha256':sha(q)})
   if t[0].startswith('ANIM') and '/' in t[-1]:refs.add(t[-1])
  bounds=[[min(v[i] for v in verts),max(v[i] for v in verts)] for i in range(3)]
  rendered=[v for tri in sample(p,2.8) for v in tri]
  ground=min(v[1] for v in rendered)
  ground_points=[[bounds[0][0]*.8,ground,bounds[2][0]*.7],[bounds[0][1]*.8,ground,bounds[2][0]*.7],[bounds[0][0]*.8,ground,bounds[2][1]*.7],[bounds[0][1]*.8,ground,bounds[2][1]*.7]]
  curve=[]
  if role in ('belt','catering'):
   upper=[v for tri in sample(p,4.0) for v in tri]
   lower=[v for tri in sample(p,1.2) for v in tri]
   moving=[i for i,(a,b) in enumerate(zip(lower,upper)) if b[1]-a[1]>1]
   for step in range(12,41):
    u=step/10
    points=[v for tri in sample(p,u) for v in tri]
    moving_points=[points[i] for i in moving]
    zmin=min(v[2] for v in moving_points)
    tip=[v for v in moving_points if v[2]<zmin+.15]
    top=max(v[1] for v in tip)
    edge=[v for v in tip if v[1]>top-.015]
    contact=[(min(v[0] for v in edge)+max(v[0] for v in edge))/2,top,min(v[2] for v in edge)]
    curve.append({'u':u,'point':contact})
  models[role]={'ground':ground_points,'curve':curve,'path':rel,'sha256':sha(p),'dependencies':deps,'refs':sorted(refs),'bounds':bounds}
 stairs=json.loads((ROOT/'assets/stairs/model_profiles.json').read_text())
 data={'variants':variants,'models':models,'stairs':stairs['models'],'stair_texture_hash':stairs['family']['common_texture']['sha256']}
 (ROOT/'packaging/profiles.json').write_text(json.dumps(data,indent=2)+'\n')
 # Conflict paths and local own model hashes are appended below.
 (ROOT/'runtime/profiles.lua').write_text('-- Generated numeric profiles; no third-party mesh or texture data.\nreturn '+lua(data)+'\n')
 # Known native and old renamed objects are retirements, never package payloads.
 retired={}
 for base in [ZIBO,OLD]:
  for p in sorted(base.iterdir()):
   if p.is_file() and p.suffix.lower() in ('.obj','.png','.dds'):
    retired.setdefault('objects/GSE/'+p.name,[]).append(sha(p))
 (ROOT/'packaging/retired.json').write_text(json.dumps({k:sorted(set(v)) for k,v in retired.items()},indent=2)+'\n')
 for model in data['stairs']:model['sha256']=sha(ROOT/'assets/stairs'/model['obj8'])
 data['conflicts']=sorted(p for p in retired if p.endswith('.obj'))
 (ROOT/'packaging/profiles.json').write_text(json.dumps(data,indent=2)+'\n')
 (ROOT/'runtime/profiles.lua').write_text('-- Generated numeric profiles; no third-party mesh or texture data.\nreturn '+lua(data)+'\n')
if __name__=='__main__':
 import argparse
 parser=argparse.ArgumentParser(description=__doc__)
 for name in ['xplane-root','lu-reference','port-source','zibo-gse','legacy-gse']:
  parser.add_argument('--'+name,required=True,type=Path)
 args=parser.parse_args()
 XP=args.xplane_root;LR=XP/'Resources/default scenery/airport scenery'
 LU=args.lu_reference;PORT=args.port_source;ZIBO=args.zibo_gse;OLD=args.legacy_gse
 build()
