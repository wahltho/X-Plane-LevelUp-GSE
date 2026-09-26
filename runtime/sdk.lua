local ffi=require('ffi')
local bit=require('bit')
ffi.cdef[[
void XPLMGetSystemPath(char*); void XPLMGetNthAircraftModel(int,char*,char*);
void* XPLMFindDataRef(const char*); int XPLMGetDataRefTypes(void*);
int XPLMGetDatai(void*); float XPLMGetDataf(void*); double XPLMGetDatad(void*);
void* XPLMLoadObject(const char*); void XPLMUnloadObject(void*);
void* XPLMCreateInstance(void*,const char**); void XPLMDestroyInstance(void*);
typedef struct {int structSize; float x,y,z,pitch,heading,roll;} LU_GSE_Draw;
void XPLMInstanceSetPosition(void*,const LU_GSE_Draw*,const float*);
typedef struct {int structSize; float locationX,locationY,locationZ,normalX,normalY,normalZ,velocityX,velocityY,velocityZ; int is_wet;} LU_GSE_Probe;
void* XPLMCreateProbe(int); void XPLMDestroyProbe(void*);
int XPLMProbeTerrainXYZ(void*,float,float,float,LU_GSE_Probe*);
void XPLMDebugString(const char*);
]]
local lib=({Windows='XPLM_64',Linux='Resources/plugins/XPLM_64.so',OSX='Resources/plugins/XPLM.framework/XPLM'})[ffi.os]
local C=ffi.load(assert(lib,'Unsupported OS'))
local S={}
function S.log(s) C.XPLMDebugString('[LU GSE] '..s..'\n') end
function S.paths()
 local root,name,path=ffi.new('char[4096]'),ffi.new('char[4096]'),ffi.new('char[4096]')
 C.XPLMGetSystemPath(root);C.XPLMGetNthAircraftModel(0,name,path)
 return ffi.string(root):gsub('\\','/'),ffi.string(name),ffi.string(path):gsub('\\','/'):match('^(.*)/[^/]+$')..'/'
end
function S.ref(name)
 local r=C.XPLMFindDataRef(name)
 if r==nil then return nil end
 local kind=C.XPLMGetDataRefTypes(r)
 return function()
  if bit.band(kind,4)~=0 then return tonumber(C.XPLMGetDatad(r)) end
  if bit.band(kind,2)~=0 then return tonumber(C.XPLMGetDataf(r)) end
  return tonumber(C.XPLMGetDatai(r))
 end
end
function S.probe()
 local r=C.XPLMCreateProbe(0);if r==nil then return nil end
 local info=ffi.new('LU_GSE_Probe[1]');info[0].structSize=ffi.sizeof('LU_GSE_Probe')
 return {sample=function(x,y,z)
  if C.XPLMProbeTerrainXYZ(r,x,y,z,info)~=0 then return nil end
  return {tonumber(info[0].locationX),tonumber(info[0].locationY),tonumber(info[0].locationZ)}
 end,close=function()C.XPLMDestroyProbe(r)end}
end
function S.load(path,refs)
 local object=C.XPLMLoadObject(path);if object==nil then return nil end
 local names=ffi.new('const char*[?]',#refs+1);local pins={}
 for i,name in ipairs(refs) do pins[i]=ffi.new('char[?]',#name+1,name);names[i-1]=pins[i] end
 names[#refs]=nil
 local entry={object=object,names=names,pins=pins,instance=nil,draw=ffi.new('LU_GSE_Draw[1]'),values=ffi.new('float[?]',math.max(1,#refs))}
 entry.draw[0].structSize=ffi.sizeof('LU_GSE_Draw')
 function entry:hide()if self.instance~=nil then C.XPLMDestroyInstance(self.instance);self.instance=nil end end
 function entry:show(p,values)
  if self.instance==nil then self.instance=C.XPLMCreateInstance(self.object,self.names) end
  if self.instance==nil then return false end
  local d=self.draw[0];d.x=p.x;d.y=p.y;d.z=p.z;d.pitch=p.pitch or 0;d.heading=p.heading;d.roll=p.roll or 0
  for i=1,#refs do self.values[i-1]=values[i] or 0 end
  C.XPLMInstanceSetPosition(self.instance,self.draw,self.values);return true
 end
 function entry:close()self:hide();C.XPLMUnloadObject(self.object);self.object=nil end
 return entry
end
-- XLua's dofile discards return values; publish in the module namespace.
if real_table then real_table('LU_GSE_sdk',S) else LU_GSE_sdk=S end
return S
