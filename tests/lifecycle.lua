-- Actual XLua loader integration; native SDK calls are mocked.
local root,lu,xp,init=assert(arg[1]),assert(arg[2]),assert(arg[3]),assert(arg[4], 'supply actual XLua init.lua')
local runtime=arg[5] or root..'/runtime'
local stairs=arg[6] or root..'/assets/stairs'
local original_dofile,original_open=dofile,io.open
local P=original_dofile(runtime..'/profiles.lua')
local name=arg[7] or '737_80NG.acf'
local f=assert(io.open(lu..'/'..name,'rb'));local acf=f:read('*a');f:close()
local digest=original_dofile(runtime..'/sha256.lua')(acf)
local v
for _,candidate in ipairs(P.aircraft_profiles[name]) do if candidate.acf_sha256==digest then v=candidate;break end end
local reject=arg[8]=='reject'
assert(v or reject,'fixture must have an explicit verified profile')
v=v or P.aircraft_profiles[name][1]
local state={local_x=0,local_y=2.65-v.doors.L1[2]+v.cg[2],local_z=0,theta=0,phi=0,psi=0,groundspeed=0,onground_any=1,front=0}
local loads,closed,created,destroyed=0,0,0,0
local phase='idle'
local function lifecycle_phase()
 assert(phase=='before_physics' or phase=='flight_start' or phase=='aircraft_unload',
        'instance lifecycle in forbidden phase: '..phase)
end
local S={}
function S.log(s)end
function S.paths()return xp..'/',name,lu..'/' end
function S.ref(name)
 local key=name:match('([^/]+)$')
 if state[key]~=nil then return function()return state[key]end end
 if key=='fwd_stairs_hide' then return function()return state.front end end
 return function()return 1 end
end
function S.probe()return {sample=function(x,y,z)return {x,0,z}end,close=function()end}end
function S.load(path,names)
 loads=loads+1
 local e={active=false}
 function e:hide()if self.active then lifecycle_phase();destroyed=destroyed+1;self.active=false end end
 function e:show(p,vals)assert(phase=='before_physics','instance show outside before_physics: '..phase);if not self.active then lifecycle_phase();created=created+1;self.active=true end;return true end
 function e:close()self:hide();closed=closed+1 end
 return e
end
-- Use the actual XLua namespace and dofile closure, not stock Lua dofile.
original_dofile(init)
function XLuaGetCode(name)
 if name=='sdk.lua' then return function()
  -- Execute the real adapter/export; only the native library is unavailable here.
  local ffi=require('ffi');local native_load=ffi.load
  ffi.load=function() return {} end
  local ok,err=pcall(setfenv(assert(loadfile(runtime..'/sdk.lua')),getfenv(1)))
  ffi.load=native_load;assert(ok,err)
  assert(type(LU_GSE_sdk)=='table' and type(LU_GSE_sdk.paths)=='function')
  real_table('LU_GSE_sdk',S)
 end end
 return assert(loadfile(runtime..'/'..name))
end
io.open=function(path,mode)
 if path:find('/objects/LU_GSE_stairs/',1,true) then path=stairs..'/'..path:match('([^/]+)$') end
 return original_open(path,mode)
end
run_module_in_namespace(assert(loadfile(runtime..'/LU_737NG.GSE.lua')))
assert(rawget(n.LU_GSE_profiles,'variants'),'profiles must remain a raw table')
assert(n.dofile('geometry.lua')==nil,'XLua dofile must discard return values')
local function call(name)
 phase=name
 if n[name] then n[name]() end
 phase='idle'
end
local function flight_start()call('flight_start')end
local function aircraft_unload()call('aircraft_unload')end
local function frame()
 call('before_physics');call('after_physics')
end
flight_start()
if reject then
 assert(loads==0,'unknown ACF/OBJ must not load any model');frame();aircraft_unload()
 print('Unsupported aircraft correctly suppressed');return
end
assert(loads>10,'models loaded')
for i=1,20 do frame() end
assert(created==1 and destroyed==0,'visible stair instance must persist across frames')
local y=state.local_y;state.local_y=y+2;frame();assert(destroyed==1,'bad fit hides')
state.local_y=y;frame();assert(created==1,'failure latched until service toggled')
state.front=1;frame();state.front=0;frame();assert(created==2,'service reactivates')
state.groundspeed=1;frame();assert(destroyed==created,'moving hides')
state.groundspeed=0;frame();assert(created==destroyed+1,'stopped reactivates')
state.onground_any=0;frame();assert(destroyed==created,'airborne hides')
state.onground_any=1;frame();assert(created==destroyed+1,'ground reactivates')
flight_start();assert(destroyed==created,'restart releases active instances');frame()
aircraft_unload();assert(closed==loads,'all objects released');assert(destroyed==created,'all instances destroyed')
flight_start();frame();aircraft_unload()
assert(closed==loads and destroyed==created,'repeated flight lifecycle releases all resources')
io.open=original_open;dofile=original_dofile
print('Mocked SDK lifecycle passed: pre-physics phase, persistence, fit latch, service reset, movement/airborne, restart/unload')
