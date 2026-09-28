-- Exercise the real SDK adapter, mocking only the native C library boundary.
local source=assert(arg[1]);local ffi=require('ffi');local original=ffi
local declared=false;local calls=0;local closed=0;local current_root,expected
local C={
 XPLMGetSystemPath=function(buffer) ffi.copy(buffer,current_root) end,
 XPLMDebugString=function() end,
 XPLMLoadObject=function(path)
  assert(path:sub(1,1)~='/' and not path:find(':',1,true) and not path:find('\\',1,true),'SDK received absolute/native path: '..path)
  assert(path==expected,'wrong SDK path: '..path);calls=calls+1
  return ffi.cast('void*',1)
 end,
 XPLMUnloadObject=function() closed=closed+1 end,
}
local cases={
 {'Windows','C:\\Program Files (x86)\\Steam\\steamapps\\common\\X-Plane 12\\','c:/Program Files (x86)/Steam/steamapps/common/X-Plane 12/'},
 {'Windows','//server/share/X-Plane 12/','\\\\SERVER\\share\\X-Plane 12\\'},
 {'OSX','/Users/pilot/X-Plane 12/','/Users/pilot/X-Plane 12/'},
 {'Linux','/opt/X-Plane 12/','/opt/X-Plane 12/'},
}
for _,case in ipairs(cases) do
 current_root=case[2]
 package.loaded.ffi=setmetatable({os=case[1],load=function() return C end,
  cdef=function(s) if not declared then ffi.cdef(s);declared=true end end},{__index=original})
 local S=dofile(source)
 for _,relative in ipairs({'Resources/default scenery/airport scenery/Ramp_Equipment/GPU_1.obj','Aircraft/737NG Series/objects/LU_GSE_stairs/LU_fallback_stairs_285.obj'}) do
  expected=relative
  local entry=assert(S.load(case[3]..relative,{}));entry:close()
 end
 local before=calls
 for _,invalid in ipairs({'/outside/model.obj',case[3]..'../outside.obj',case[3]..'./model.obj',case[3]..'/model.obj',case[3]..'bad:obj',case[3]..'bad\0obj',case[3],current_root:gsub('[/\\]+$','')..'-other/model.obj'}) do
  assert(S.load(invalid,{})==nil,'invalid path accepted: '..invalid)
 end
 assert(calls==before,'invalid path reached SDK')
end
package.loaded.ffi=original
assert(calls==8 and closed==8)
print('SDK object paths PASS: Windows drive/UNC, macOS, Linux; LR and own stairs; invalid paths blocked')
