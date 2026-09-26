-- Read-only local-source integration fixture; SDK is entirely mocked.
local root,lu,xp=assert(arg[1]),assert(arg[2]),assert(arg[3])
local original_dofile,original_open=dofile,io.open
local P=original_dofile(root..'/runtime/profiles.lua')
local v=P.variants['737_80NG.acf']
local state={local_x=0,local_y=2.65-v.doors.L1[2]+v.cg[2],local_z=0,theta=0,phi=0,psi=0,groundspeed=0,onground_any=1,front=0}
local loads,closed,created,destroyed=0,0,0,0
local S={}
function S.log(s)end
function S.paths()return xp..'/','737_80NG.acf',lu..'/' end
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
 function e:hide()if self.active then destroyed=destroyed+1;self.active=false end end
 function e:show(p,vals)if not self.active then created=created+1;self.active=true end;return true end
 function e:close()self:hide();closed=closed+1 end
 return e
end
function dofile(name)
 if name=='sdk.lua' then return S end
 return original_dofile(root..'/runtime/'..name)
end
io.open=function(path,mode)
 if path:find('/objects/LU_GSE_stairs/',1,true) then path=root..'/assets/stairs/'..path:match('([^/]+)$') end
 return original_open(path,mode)
end
original_dofile(root..'/runtime/LU_737NG.GSE.lua')
flight_start();assert(loads>10,'models loaded')
for i=1,20 do after_physics() end
assert(created==1 and destroyed==0,'visible stair instance must persist across frames')
local y=state.local_y;state.local_y=y+2;after_physics();assert(destroyed==1,'bad fit hides')
state.local_y=y;after_physics();assert(created==1,'failure latched until service toggled')
state.front=1;after_physics();state.front=0;after_physics();assert(created==2,'service reactivates')
aircraft_unload();assert(closed==loads,'all objects released');assert(destroyed==created,'all instances destroyed')
io.open=original_open;dofile=original_dofile
print('Mocked SDK lifecycle passed: load, persistent instance, fit-failure latch, service reset, unload')
