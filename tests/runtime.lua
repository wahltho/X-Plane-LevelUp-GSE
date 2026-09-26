local root=assert(arg[1]);local G=dofile(root..'/runtime/geometry.lua');local P=dofile(root..'/runtime/profiles.lua')
local hash=dofile(root..'/runtime/sha256.lua')
assert(hash('')=='e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855')
assert(hash('abc')=='ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad')
local function near(a,b)assert(math.abs(a-b)<1e-5,tostring(a)..' != '..tostring(b))end
local v=G.rotate({0,0,-1},90,0,0);near(v[1],1);near(v[3],0)
v=G.rotate({0,0,-1},0,30,0);near(v[2],.5)
for _,slope in ipairs({-.04,0,.04}) do
 local plane={sx=slope,sz=.02,base=0};local pitch,roll=G.orientation(plane,35)
 for _,w in ipairs({{2,0,0},{0,0,3}}) do local d=G.rotate(w,35,pitch,roll);near(d[2],G.height(plane,d[1],d[3])) end
end
local count=0
for name,p in pairs(P.variants) do
 count=count+1
 for _,h in ipairs({2.573,2.65,2.85,3.05,3.106}) do
  local fit=G.stairs({0,h,0},90,P.stairs,function(x,y,z)return {x,0,z} end)
  assert(fit and fit.error<=.1,name..' '..h)
 end
 assert(not G.stairs({0,4,0},0,P.stairs,function(x,y,z)return {x,0,z} end))
end
assert(count==5)
for _,slope in ipairs({-.03,.03}) do
 local fit=G.stairs({0,2.85,0},0,P.stairs,function(x,y,z)return {x,slope*x,z} end)
 assert(fit,'slope fit');assert(fit.error<=.1)
end
for _,role in ipairs({'belt','catering'}) do
 local fit=G.equipment({0,2.85,0},270,P.models[role],function(x,y,z)return {x,0,z} end)
 assert(fit,role);assert(fit.error<=.1);assert(fit.u>1.2)
 local again=G.equipment({0,2.86,0},270,P.models[role],function(x,y,z)return {x,0,z} end,fit.u)
 assert(again);near(again.u,fit.u)
end
local bad=G.equipment({0,20,0},0,P.models.belt,function(x,y,z)return {x,0,z} end)
assert(not bad)
assert(not G.stairs({0,2.85,0},0,P.stairs,function()return nil end))
print('Runtime numeric/hash checks passed: 5 variants, 25 height cases, slopes, contact curves, misses, out-of-range')
