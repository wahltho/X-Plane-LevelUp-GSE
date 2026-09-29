import importlib.util,json,tempfile,unittest,shutil,hashlib,os,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
installer=load('installer',ROOT/'z_Install.py');builder=load('builder',ROOT/'tools/build_package.py')
class PackageTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.package=builder.build()
 def test_option_b_package_has_complete_mtk_scope_contract(self):
  m=json.loads((self.package/'package-manifest.json').read_text())
  self.assertEqual(m['schemaVersion'],4)
  self.assertEqual(m['packageId'],installer.PACKAGE_ID)
  self.assertEqual(m['supportedProducts'],['levelup-737ng'])
  module=m['modules'][0]
  self.assertEqual([s['relativePath'] for s in module['managedScopes']],list(installer.SCOPES))
  self.assertTrue(all(s['mode']=='flatExclusive' for s in module['managedScopes']))
  targets={t['relativePath'] for t in module['targets']}
  retired={r['relativePath'] for r in module['retiredFiles']}
  self.assertFalse(targets & retired)
  self.assertTrue(all(str(Path(p).parent).replace('\\','/') in installer.SCOPES for p in targets | retired))
  self.assertEqual(len(targets),10)
  self.assertEqual(len(retired),68)
  self.assertIn(installer.SCRIPT_DIR+'/LU_737NG.GSE.lua',targets)
  self.assertIn('objects/LU_GSE_stairs/LU_fallback_stairs_265.obj',targets)
  self.assertIn('objects/LU_GSE_stairs/LU_fallback_stairs_285.obj',targets)
  self.assertIn('objects/LU_GSE_stairs/LU_fallback_stairs_305.obj',targets)
  self.assertNotIn('objects/GSE/Zibo_stairs_fwd.obj',targets)
 def test_official_lu_originals_are_accepted(self):
  official=json.loads((ROOT/'packaging/official_lu_gse.json').read_text())
  m=json.loads((self.package/'package-manifest.json').read_text())
  allowed={r['relativePath']:r['sourceSha256'] for r in m['modules'][0]['retiredFiles']}
  for source in official['sources']:
   self.assertEqual(len(source['files']),12)
   for path,digest in source['files'].items():
    self.assertIn(digest,allowed[path],source['tag']+': '+path)
 def test_upgrade_allowlist_matches_reviewed_previous_payloads(self):
  known=json.loads((ROOT/'packaging/previous_payloads.json').read_text())
  m=json.loads((self.package/'package-manifest.json').read_text())
  for target in m['modules'][0]['targets']:
   self.assertEqual(target['sourceSha256'],known[target['relativePath']])
 def test_update_from_previous_preview_preserves_original_backups(self):
  manifest_path=self.pkg/'package-manifest.json'
  manifest=json.loads(manifest_path.read_text())
  self.assertEqual(manifest['packageVersion'],builder.VERSION)
  manifest['packageVersion']='0.2.0-preview.1'
  manifest_path.write_text(json.dumps(manifest))
  native=self.root/'objects/GSE/synthetic.obj'
  original=b'known native fixture'
  native.parent.mkdir(parents=True)
  native.write_bytes(original)
  manifest['modules'][0]['retiredFiles'].append({'relativePath':'objects/GSE/synthetic.obj','sourceSha256':[installer.sha(original)]})
  manifest_path.write_text(json.dumps(manifest))
  self.run_install('install')
  self.assertFalse(native.exists())
  manifest['packageVersion']=builder.VERSION
  manifest_path.write_text(json.dumps(manifest))
  self.run_install('install')
  self.assertFalse(native.exists())
  self.run_install('uninstall')
  self.assertEqual(native.read_bytes(),original)
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.base=Path(self.temp.name);self.root=self.base/'aircraft';self.root.mkdir();self.pkg=self.base/'package';shutil.copytree(self.package,self.pkg)
  p=json.loads((self.pkg/'profiles.json').read_text());variant=next(iter(p['variants'].values()));variant['door_object']={'path':'objects/test.obj','sha256':installer.sha(b'fixture')}
  p['variants']={'737_60NG.acf':variant};(self.pkg/'profiles.json').write_text(json.dumps(p))
  lines=[f'P {k} {v}' for k,v in (variant['signature']|variant['object_signature']).items()]
  variant['acf_sha256']=installer.sha('\n'.join(lines).encode());p['aircraft_profiles']={'737_60NG.acf':[variant]};(self.pkg/'profiles.json').write_text(json.dumps(p));(self.root/'737_60NG.acf').write_text('\n'.join(lines));(self.root/'plugins/xlua/scripts').mkdir(parents=True);(self.root/'objects').mkdir();(self.root/'objects/test.obj').write_bytes(b'fixture')
 def tearDown(self):self.temp.cleanup()
 def run_install(self,command):return installer.run(command,self.root,self.pkg)
 def test_fresh_repeat_verify_restore(self):
  self.run_install('check');self.assertFalse((self.root/installer.STATE).exists())
  self.run_install('install');self.run_install('verify');self.assertIn('Already',self.run_install('install'))
  self.assertTrue((self.root/installer.MARKER).exists());self.run_install('uninstall')
  for scope in installer.SCOPES:self.assertFalse((self.root/scope).exists())
 def test_known_native_restored(self):
  m=json.loads((self.pkg/'package-manifest.json').read_text());m['modules'][0]['retiredFiles'].append({'relativePath':'objects/GSE/synthetic.obj','sourceSha256':[installer.sha(b'original')]});(self.pkg/'package-manifest.json').write_text(json.dumps(m))
  p=self.root/'objects/GSE/synthetic.obj';p.parent.mkdir();p.write_bytes(b'original')
  self.run_install('install');self.assertFalse(p.exists());self.run_install('uninstall');self.assertEqual(p.read_bytes(),b'original')
 def test_unknown_blocks_before_writes(self):
  p=self.root/'objects/GSE/unknown.obj';p.parent.mkdir();p.write_bytes(b'unknown')
  with self.assertRaises(installer.InstallError):self.run_install('install')
  self.assertEqual(p.read_bytes(),b'unknown');self.assertFalse((self.root/installer.STATE).exists())
 def test_changed_target_blocks_uninstall(self):
  self.run_install('install');p=self.root/installer.SCRIPT_DIR/'geometry.lua';p.write_bytes(b'user edit')
  with self.assertRaises(installer.InstallError):self.run_install('uninstall')
  self.assertEqual(p.read_bytes(),b'user edit')
 def test_foreign_owner_blocks(self):
  p=self.root/installer.SCRIPT_DIR;p.mkdir();(p/'foreign.lua').write_text('foreign')
  with self.assertRaises(installer.InstallError):self.run_install('install')
 def test_geometry_signature_blocks(self):
  (self.root/'737_60NG.acf').write_text('P acf/_board_1/0 900')
  with self.assertRaises(installer.InstallError):self.run_install('install')
 def test_corrupt_payload_blocks(self):
  p=next((self.pkg/'modules').rglob('geometry.lua'));p.write_text('corrupted')
  with self.assertRaises(installer.InstallError):self.run_install('install')
 def test_symlink_blocks(self):
  (self.root/'objects/GSE').symlink_to(self.base,target_is_directory=True)
  with self.assertRaises(installer.InstallError):self.run_install('install')
 def test_native_reappearance_preserved(self):
  self.run_install('install');p=self.root/'objects/GSE/new.obj';p.write_text('new upstream')
  with self.assertRaises(installer.InstallError):self.run_install('uninstall')
  self.assertEqual(p.read_text(),'new upstream')
 def test_failure_rolls_back(self):
  real=installer.atomic;calls=[0]
  def fail(root,path,data):
   if path.startswith(installer.SCRIPT_DIR):
    calls[0]+=1
    if calls[0]==3:raise OSError('injected write failure')
   return real(root,path,data)
  installer.atomic=fail
  try:
   with self.assertRaises(OSError):self.run_install('install')
  finally:installer.atomic=real
  self.assertFalse((self.root/installer.STATE).exists());self.assertFalse((self.root/installer.SCRIPT_DIR).exists())
 def test_package_no_third_party_assets(self):
  forbidden={h for hs in json.loads((ROOT/'packaging/retired.json').read_text()).values() for h in hs}
  for p in (self.pkg/'modules').rglob('*'):
   if p.is_file():self.assertNotIn(installer.sha(p.read_bytes()),forbidden)
  objects=list((self.pkg/'modules').rglob('*.obj'));self.assertEqual(len(objects),3)
 def test_committed_install_recovery(self):
  real=installer.finish_transaction
  installer.finish_transaction=lambda *args: (_ for _ in ()).throw(SystemExit('simulated process exit'))
  try:
   with self.assertRaises(SystemExit):self.run_install('install')
  finally:installer.finish_transaction=real
  self.assertIn('cleanup',self.run_install('recover'));self.run_install('verify');self.run_install('uninstall')
 def test_committed_uninstall_recovery(self):
  self.run_install('install');real=installer.finish_transaction
  installer.finish_transaction=lambda *args: (_ for _ in ()).throw(SystemExit('simulated exit'))
  try:
   with self.assertRaises(SystemExit):self.run_install('uninstall')
  finally:installer.finish_transaction=real
  self.run_install('recover');self.assertFalse((self.root/installer.STATE).exists())
 def test_unknown_completed_directory_preserved(self):
  p=self.root/(installer.STATE+'.completed');p.mkdir();(p/'user.txt').write_text('retain')
  with self.assertRaises(installer.InstallError):self.run_install('install')
  self.assertEqual((p/'user.txt').read_text(),'retain')
 def test_recovery_rejects_new_scope_file(self):
  real=installer.finish_transaction
  installer.finish_transaction=lambda *args: (_ for _ in ()).throw(SystemExit())
  try:
   with self.assertRaises(SystemExit):self.run_install('install')
  finally:installer.finish_transaction=real
  p=self.root/'objects/GSE/user.obj';p.write_bytes(b'user')
  with self.assertRaises(installer.InstallError):self.run_install('recover')
  self.assertEqual(p.read_bytes(),b'user')
 def test_running_simulator_blocks(self):
  from unittest.mock import patch
  with patch.object(installer.subprocess,'check_output',return_value='/Applications/X-Plane.app/Contents/MacOS/X-Plane\n'):
   with self.assertRaises(installer.InstallError):installer.ensure_offline()
if __name__=='__main__':unittest.main()
