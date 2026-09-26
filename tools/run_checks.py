"""Explicit developer checks, supplied local reference paths; no live deployment."""
import argparse,hashlib,json,subprocess,sys
from pathlib import Path
from build_package import VERSION
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--luajit',required=True);p.add_argument('--lu-reference',required=True);p.add_argument('--xplane-root',required=True);p.add_argument('--mtk-root',required=True);p.add_argument('--native-gpu',required=True)
a=p.parse_args();out=ROOT/'dist/validation';out.mkdir(parents=True,exist_ok=True)
commands={
'python':[sys.executable,'-m','unittest','discover','-s','tests','-v'],
'lua-numeric':[a.luajit,'tests/runtime.lua',str(ROOT)],
'lua-lifecycle':[a.luajit,'tests/lifecycle.lua',str(ROOT),a.lu_reference,a.xplane_root],
'stair-assets':[sys.executable,'asset_sources/stairs/validate_fallback_stairs.py','--objects','assets/stairs','--measurements','docs/levelup_stair_measurements.json','--output',str(out/'stairs')],
'mtk':['dotnet','run','--project','tests/mtk/Smoke.csproj','-p:MtkRoot='+a.mtk_root,'--',str(ROOT/'dist/levelup-gse-'+VERSION),a.native_gpu],
}
results={}
for name,cmd in commands.items():
 r=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True)
 (out/(name+'.log')).write_text(r.stdout+r.stderr)
 results[name]={'exit_code':r.returncode};print(name,'PASS' if r.returncode==0 else 'FAIL',flush=True)
 if r.returncode:print((r.stdout+r.stderr)[-3000:]);break
results['package_sha256']=hashlib.sha256((ROOT/'dist'/('levelup-gse-'+VERSION+'.zip')).read_bytes()).hexdigest()
(out/'results.json').write_text(json.dumps(results,indent=2)+'\n')
sys.exit(0 if len(results)==len(commands)+1 and all(v['exit_code']==0 for v in results.values() if isinstance(v,dict)) else 1)
