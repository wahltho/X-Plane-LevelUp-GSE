using LevelUp.NavTableUpdater.Core.Aircraft;
using LevelUp.NavTableUpdater.Core.Content;
using LevelUp.NavTableUpdater.Core.State;
var package=Path.GetFullPath(args[0]);
var temp=Path.Combine(Path.GetTempPath(),"gse-mtk-"+Guid.NewGuid());
Directory.CreateDirectory(temp);
try {
 var aircraft=Path.Combine(temp,"aircraft");Directory.CreateDirectory(aircraft);
 var name=Environment.GetEnvironmentVariable("GSE_TEST_VARIANT")??"737_70NG";
 var acf=Path.Combine(aircraft,name+".acf");
 var reference=Environment.GetEnvironmentVariable("GSE_TEST_AIRCRAFT_REF");
 if(reference is null)File.WriteAllText(acf,"1200 Version\n");
 else File.Copy(Path.Combine(reference,name+".acf"),acf);
 var variant=new AircraftVariantViewAnalysis("levelup-737-700","LevelUp 737-700","LevelUp",acf,Path.ChangeExtension(acf,null)+"_prefs.txt","test","test","V2.S1.51","V2.S1.51",null,null,null,null,0,0,null,null,null,null,"test","test","test","test");
 var store=new ToolStateStore(Path.Combine(temp,"state"),Path.Combine(temp,"backups"));
 var op=new CompatibilityPackageOperation(store,()=>false);
 var loaded=CompatibilityPackageLoader.LoadDirectory(package);
 if(loaded.Manifest.SchemaVersion!=4)throw new Exception("Wrong schema");
 var result=await op.RunAsync(ContentPatchAction.Install,variant,package,["gse"]);
 if(!result.Succeeded)throw new Exception(result.Message);
 result=await op.RunAsync(ContentPatchAction.Update,variant,package,["gse"]);
 if(!result.Succeeded||result.Changed)throw new Exception("Repeat was not idempotent: "+result.Message);
 var marker=Path.Combine(aircraft,"plugins/xlua/scripts/LU_737NG.GSE/.standalone-owner");File.WriteAllText(marker,"foreign owner");
 result=await op.RunAsync(ContentPatchAction.Repair,variant,package,["gse"]);
 if(result.Succeeded)throw new Exception("Foreign ownership marker was ignored");File.Delete(marker);
 var restored=op.Restore(variant,package);if(!restored.Succeeded)throw new Exception(restored.Message);
 foreach(var path in new[]{"objects/GSE","objects/LU_GSE_stairs","plugins/xlua/scripts/LU_737NG.GSE"})
  if(Directory.Exists(Path.Combine(aircraft,path)))throw new Exception("Fresh scope survived restore: "+path);
 if(args.Length>1) {
  var native=Path.Combine(aircraft,"objects/GSE/gpu.obj");Directory.CreateDirectory(Path.GetDirectoryName(native)!);
  var original=File.ReadAllBytes(args[1]);File.WriteAllBytes(native,original);
  result=await op.RunAsync(ContentPatchAction.Install,variant,package,["gse"]);
  if(!result.Succeeded||File.Exists(native))throw new Exception("Native retirement failed: "+result.Message);
  restored=op.Restore(variant,package);
  if(!restored.Succeeded||!File.ReadAllBytes(native).SequenceEqual(original))throw new Exception("Native byte-identical restore failed");
 }
 foreach(var previous in args.Skip(2)) {
  result=await op.RunAsync(ContentPatchAction.Install,variant,Path.GetFullPath(previous),["gse"]);
  if(!result.Succeeded)throw new Exception("Previous install: "+result.Message);
  result=await op.RunAsync(ContentPatchAction.Update,variant,package,["gse"]);
  if(!result.Succeeded)throw new Exception("Upgrade: "+result.Message);
  foreach(var file in Directory.GetFiles(Path.Combine(package,"modules/gse"),"*",SearchOption.AllDirectories)) {
   var relative=Path.GetRelativePath(Path.Combine(package,"modules/gse"),file);
   if(!File.ReadAllBytes(file).SequenceEqual(File.ReadAllBytes(Path.Combine(aircraft,relative))))throw new Exception("Upgrade payload mismatch: "+relative);
  }
  result=await op.RunAsync(ContentPatchAction.Update,variant,package,["gse"]);
  if(!result.Succeeded||result.Changed)throw new Exception("Upgrade repeat failed");
  restored=op.Restore(variant,package);
  if(!restored.Succeeded)throw new Exception("Upgrade restore: "+restored.Message);
  if(args.Length>1&&!File.ReadAllBytes(Path.Combine(aircraft,"objects/GSE/gpu.obj")).SequenceEqual(File.ReadAllBytes(args[1])))throw new Exception("Upgrade lost native original");
  Console.WriteLine("MTK previous ZIP upgrade/repeat/payload/restore PASS: "+previous);
 }
 var originals=Environment.GetEnvironmentVariable("GSE_TEST_ORIGINAL_GSE");
 if(originals is not null) {
  var scope=Path.Combine(aircraft,"objects/GSE");
  if(Directory.Exists(scope))Directory.Delete(scope,true);
  Directory.CreateDirectory(scope);
  var originalsByName=Directory.GetFiles(originals).ToDictionary(p=>Path.GetFileName(p)!,p=>File.ReadAllBytes(p));
  foreach(var entry in originalsByName)File.WriteAllBytes(Path.Combine(scope,entry.Key!),entry.Value);
  result=await op.RunAsync(ContentPatchAction.Install,variant,package,["gse"]);
  if(!result.Succeeded)throw new Exception("Complete original scope: "+result.Message);
  result=await op.RunAsync(ContentPatchAction.Update,variant,package,["gse"]);
  if(!result.Succeeded||result.Changed)throw new Exception("Complete scope repeat failed");
  restored=op.Restore(variant,package);
  if(!restored.Succeeded)throw new Exception("Complete scope restore: "+restored.Message);
  if(Directory.GetFiles(scope).Length!=originalsByName.Count)throw new Exception("Original scope count changed");
  foreach(var entry in originalsByName)
   if(!File.ReadAllBytes(Path.Combine(scope,entry.Key!)).SequenceEqual(entry.Value))throw new Exception("Original scope bytes changed: "+entry.Key);
  var changed=Path.Combine(scope,"gpu.obj");File.AppendAllText(changed,"modified");
  var bad=File.ReadAllBytes(changed);
  result=await op.RunAsync(ContentPatchAction.Install,variant,package,["gse"]);
  if(result.Succeeded||!File.ReadAllBytes(changed).SequenceEqual(bad))throw new Exception("Modified original accepted or changed");
  Console.WriteLine("MTK complete original GSE scope install/repeat/restore and changed-original rejection PASS: "+originals);
 }
 Console.WriteLine("MTK actual package: schema4 load/install/repeat/foreign-owner blocking/restore passed.");
} finally {Directory.Delete(temp,true);}
