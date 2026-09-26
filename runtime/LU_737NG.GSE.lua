-- Option B only: local Laminar objects and original static fallback stairs.
dofile('geometry.lua')
local G=assert(LU_GSE_geometry, 'Missing GSE geometry export')
dofile('profiles.lua')
local P=assert(LU_GSE_profiles, 'Missing GSE profiles export')
dofile('sha256.lua')
local hash=assert(LU_GSE_sha256, 'Missing GSE sha256 export')
dofile('sdk.lua')
local S=assert(LU_GSE_sdk, 'Missing GSE sdk export')
local entries,refs,logged,verified={},{},{},{}
local terrain,variant,cg,aircraft,lr
local function read(path)local f=io.open(path,'rb');if not f then return nil end;local v=f:read('*a');f:close();return v end
local function log(code,detail)
 local key=code..': '..detail
 if not logged[key] then S.log(key);logged[key]=true end
end
local function check(path,expected)
 if verified[path] then return verified[path]==expected end
 local bytes=read(path);if not bytes then log('ASSET_MISSING',path);return false end
 local actual=hash(bytes);verified[path]=actual
 if actual~=expected then log('ASSET_UNKNOWN',path);return false end
 return true
end
local function load_model(id)
 local p=P.models[id]
 if not p or not check(lr..p.path,p.sha256) then return nil end
 for _,d in ipairs(p.dependencies) do if not check(lr..d.path,d.sha256) then return nil end end
 local obj=S.load(lr..p.path,p.refs)
 if not obj then log('LOAD_FAILED',id) end
 return obj
end
local function visibility(name)
 local r=S.ref('laminar/B738/'..name)
 if not r then log('DATAREF_MISSING',name) end
 return r
end
local function add(id,model,hide,anchor,dx,dz,heading,driver)
 local vis=visibility(hide);if not vis then return end
 local a=variant.service[anchor]
 if not a then log('ANCHOR_MISSING',anchor);return end
 local object=load_model(model);if not object then return end
 local extra=driver and load_model(driver)
 if driver and not extra then object:close();return end
 local point={a[1]+dx,0,a[3]+dz}
 if model=='belt' or model=='catering' then
  local key=({cargo_fwd='bagg_1',cargo_aft='bagg_2',r1='food_1',r2='food_2'})[anchor]
  -- ACF service XYZ describes the contact, not a native object's origin.
  point=variant.anchors[key]
 end
 entries[#entries+1]={id=id,model=model,object=object,driver=extra,driverModel=driver,vis=vis,
  point=point,heading=heading,kind='equipment'}
end
local function values(model,u)
 local out={}
 for i,name in ipairs(P.models[model].refs) do
  -- Fixed working pose; no new vehicle/lift animation or writes to global refs.
  out[i]=name:find('engine_running',1,true) and 1 or
    (name:find('belt_loader_height_meters',1,true) and (u or 0) or 0)
 end
 return out
end
local function close()
 for _,e in ipairs(entries) do
  if e.object then e.object:close() end
  if e.driver then e.driver:close() end
  for _,m in ipairs(e.models or {}) do m.object:close() end
 end
 entries={}
 if terrain then terrain.close();terrain=nil end
end
function aircraft_unload() close() end
function flight_start()
 close();logged={};verified={};refs={}
 local root,name,folder=S.paths();aircraft=folder;lr=root..'Resources/default scenery/airport scenery/'
 variant=P.variants[name]
 if not variant then log('ACF_UNSUPPORTED',name);return end
 if not check(folder..variant.door_object.path,variant.door_object.sha256) then log('ACF_UNSUPPORTED','door geometry changed');return end
 local acf=read(folder..name)
 if not acf then log('ACF_MISSING',name);return end
 local reason;cg,reason=G.validate_acf(acf,variant)
 if not cg then log('ACF_UNSUPPORTED',tostring(reason));return end
 for _,path in ipairs(P.conflicts) do
  if read(folder..path) then log('NATIVE_GSE_CONFLICT',path..'; run installer repair/reinstall');return end
 end
 for key,path in pairs({x='local_x',y='local_y',z='local_z',heading='psi',pitch='theta',roll='phi',speed='groundspeed'}) do
  refs[key]=S.ref('sim/flightmodel/position/'..path)
  if not refs[key] then log('DATAREF_MISSING',path);return end
 end
 refs.ground=S.ref('sim/flightmodel/failures/onground_any')
 if not refs.ground then log('DATAREF_MISSING','onground_any');return end
 terrain=S.probe();if not terrain then log('PROBE_FAILED','terrain');return end
 -- Equipment origins based on port service stations. LR profile calibration is
 -- deliberately a simulator acceptance gate; these are stationary apron poses.
 add('gpu','gpu','gpu_hide','electrical',4,0,0)
 add('asu','asu','engine/hide_asu','pneumatic',6,0,0)
 add('fuel1','fuel1','fueltruck_hide','fuel',5,0,0)
 add('fuel2','fuel2','fueltruck_hide','fuel',9,4,30)
 add('deice1','deice','de_ice_truck/hide','wing',12,-5,0)
 add('deice2','deice','de_ice_truck/hide','tail',-6,2,150)
 add('bus1','bus1','pax_bus_hide','l1',-15,2,0)
 add('bus2','bus2','pax_bus2_hide','l2',-15,2,355)
 add('belt1','belt','belt_hide','cargo_fwd',4.368,.373,270,'belt_driver')
 add('belt2','belt','belt2_hide','cargo_aft',4.094,1.205,280,'belt_driver')
 add('catering1','catering','catering_hide','r1',4.666,-.419,265,'catering_driver')
 add('catering2','catering','catering2_hide','r2',4.322,.555,280,'catering_driver')
 for _,s in ipairs({{'nose',-3,-2},{'nose',3,-2},{'tail',-3,2},{'tail',3,2},{'wing',-19,0},{'wing',19,0}}) do
  add('cone_'..#entries,'cones','fms/cones_hide',s[1],s[2],s[3],0)
 end
 for _,d in ipairs({{'L1','fwd_stairs_hide'},{'L2','aft_stairs_hide'}}) do
  local vis=visibility(d[2]);local models={}
  if vis then
   for _,model in ipairs(P.stairs) do
    local path=folder..'objects/LU_GSE_stairs/'..model.obj8
    if check(path,model.sha256) and check(folder..'objects/LU_GSE_stairs/'..model.texture,P.stair_texture_hash) then
     local obj=S.load(path,{})
     if obj then models[#models+1]={profile=model,object=obj} end
    end
   end
   entries[#entries+1]={id=d[1],kind='stairs',vis=vis,point=variant.doors[d[1]],models=models}
  end
 end
 S.log('Option B initialized for '..variant.id..'; simulator fit validation required for this preview build.')
end
local function hide(e)
 if e.object then e.object:hide() end
 if e.driver then e.driver:hide() end
 for _,m in ipairs(e.models or {}) do m.object:hide() end
end
function after_physics()
 if not terrain then return end
 local pose={};for key,r in pairs(refs) do pose[key]=r() end
 for _,e in ipairs(entries) do
  if pose.ground==0 or pose.speed>0.5 or e.vis()~=0 then
   hide(e);e.selected=nil;e.failed=false;e.u=nil
  elseif not e.failed then
   local target=G.world(e.point,pose,cg)
   local fit,reason
   if e.kind=='stairs' then
    local models={}
    if e.selected then models={e.selected.profile}
    else for _,m in ipairs(e.models) do models[#models+1]=m.profile end end
    fit,reason=G.stairs(target,pose.heading,models,terrain.sample)
    if fit then
     if not e.selected then for _,m in ipairs(e.models) do if m.profile==fit.model then e.selected=m end end end
     e.selected.object:show(fit,{})
    end
   else
    fit,reason=G.equipment(target,pose.heading+e.heading,P.models[e.model],terrain.sample,e.u)
    if fit then
     e.u=fit.u;e.object:show(fit,values(e.model,e.u))
     if e.driver then e.driver:show(fit,values(e.driverModel,e.u)) end
    end
   end
   if not fit then hide(e);e.failed=true;log(reason or 'MODEL_FIT',e.id..'; toggle service after correcting fit') end
  end
 end
end
