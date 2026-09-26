using LevelUp.NavTableUpdater.Core.Aircraft;
using LevelUp.NavTableUpdater.Core.Content;
using LevelUp.NavTableUpdater.Core.State;
var package=Path.GetFullPath(args[0]);
var temp=Path.Combine(Path.GetTempPath(),"gse-mtk-"+Guid.NewGuid());
Directory.CreateDirectory(temp);
try {
 var aircraft=Path.Combine(temp,"aircraft");Directory.CreateDirectory(aircraft);
 var acf=Path.Combine(aircraft,"737_70NG.acf");File.WriteAllText(acf,"1200 Version\n");
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
 Console.WriteLine("MTK actual package: schema4 load/install/repeat/foreign-owner blocking/restore passed.");
} finally {Directory.Delete(temp,true);}
