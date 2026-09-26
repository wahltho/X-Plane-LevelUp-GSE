-- Pure numeric geometry; X-Plane body axes: right, up, aft.
local M={}
local function rad(d)return d*math.pi/180 end
function M.rotate(v,heading,pitch,roll)
 local h,p,r=rad(heading),rad(pitch or 0),rad(roll or 0)
 local x=math.cos(r)*v[1]+math.sin(r)*v[2]
 local y=-math.sin(r)*v[1]+math.cos(r)*v[2]
 local z=v[3]
 y,z=math.cos(p)*y-math.sin(p)*z,math.sin(p)*y+math.cos(p)*z
 return {math.cos(h)*x-math.sin(h)*z,y,math.sin(h)*x+math.cos(h)*z}
end
function M.world(point,pose,cg)
 local d=M.rotate({point[1]-cg[1],point[2]-cg[2],point[3]-cg[3]},pose.heading,pose.pitch,pose.roll)
 return {pose.x+d[1],pose.y+d[2],pose.z+d[3]}
end
function M.plane(points)
 local a,b,c=points[1],points[2],points[3]
 local u,v={b[1]-a[1],b[2]-a[2],b[3]-a[3]},{c[1]-a[1],c[2]-a[2],c[3]-a[3]}
 local nx,ny,nz=u[2]*v[3]-u[3]*v[2],u[3]*v[1]-u[1]*v[3],u[1]*v[2]-u[2]*v[1]
 if math.abs(ny)<1e-6 then return nil end
 local sx,sz=-nx/ny,-nz/ny
 if sx*sx+sz*sz>0.04 then return nil end -- >11 degrees: not a normal GSE stand
 return {sx=sx,sz=sz,base=a[2]-sx*a[1]-sz*a[3]}
end
function M.height(p,x,z)return p.base+p.sx*x+p.sz*z end
function M.orientation(p,heading)
 local h=rad(heading)
 local sx=p.sx*math.cos(h)+p.sz*math.sin(h)
 local sz=-p.sx*math.sin(h)+p.sz*math.cos(h)
 -- Local ground normal, with rotation Ry(-heading)*Rx(pitch)*Rz(-roll).
 local pitch=-math.atan(sz)
 local roll=-math.atan(sx/math.sqrt(1+sz*sz))
 return pitch*180/math.pi,roll*180/math.pi
end
function M.stairs(contact,heading,models,probe)
 local best
 for _,model in ipairs(models) do
  local points={}
  for _,wheel in ipairs(model.wheel_ground_points_xyz_m) do
   local d=M.rotate(wheel,heading,0,0)
   local hit=probe(contact[1]+d[1],contact[2]+5,contact[3]+d[3])
   if not hit then return nil,'TERRAIN_MISS' end
   points[#points+1]=hit
  end
  local plane=M.plane(points)
  if plane then
   local pitch,roll=M.orientation(plane,heading)
   local d=M.rotate(model.contact_point_xyz_m,heading,pitch,roll)
   local x,z=contact[1]-d[1],contact[3]-d[3]
   local y=M.height(plane,x,z)
   local error=math.abs(y+d[2]-contact[2])
   for _,wheel in ipairs(model.wheel_ground_points_xyz_m) do
    local w=M.rotate(wheel,heading,pitch,roll)
    local hit=probe(x+w[1],contact[2]+5,z+w[3])
    if not hit then return nil,'TERRAIN_MISS' end
    error=math.max(error,math.abs(y+w[2]-hit[2]))
   end
   if error<=0.1 and (not best or error<best.error) then
    best={model=model,x=x,y=y,z=z,heading=heading,pitch=pitch,roll=roll,error=error}
   end
  end
 end
 return best,best and nil or 'MODEL_FIT'
end
function M.validate_acf(text,profile)
 local values={};local strings={}
 for key,value in text:gmatch('P%s+([^%s]+)%s+([^%s]+)') do
  strings[key]=value
  local n=tonumber(value)
  if n and n==n and math.abs(n)<1e9 then values[key]=n end
 end
 for key,value in pairs(profile.object_signature or {}) do
  if strings[key]~=value then return nil,key end
 end
 for key,value in pairs(profile.signature) do
  if not values[key] or math.abs(values[key]-value)>0.001 then return nil,key end
 end
 if not values['acf/_cgY'] or not values['acf/_cgZ'] then return nil,'CG reference' end
 return {0,values['acf/_cgY']*.3048,values['acf/_cgZ']*.3048}
end
function M.equipment(target,heading,profile,probe,fixed_u)
 local curves=profile.curve
 if #curves==0 then curves={{u=0,point={0,profile.ground[1][2],0}}} end
 local best
 for _,candidate in ipairs(curves) do
  if not fixed_u or candidate.u==fixed_u then
   local contact=M.rotate(candidate.point,heading,0,0)
   local ox,oz=target[1]-contact[1],target[3]-contact[3]
   local samples={}
   for _,w in ipairs(profile.ground) do
    local d=M.rotate(w,heading,0,0)
    local hit=probe(ox+d[1],target[2]+15,oz+d[3])
    if not hit then return nil,'TERRAIN_MISS' end
    samples[#samples+1]=hit
   end
   local plane=M.plane(samples)
   if plane then
    local pitch,roll=M.orientation(plane,heading)
    contact=M.rotate(candidate.point,heading,pitch,roll)
    ox,oz=target[1]-contact[1],target[3]-contact[3]
    local base=M.rotate({0,profile.ground[1][2],0},heading,pitch,roll)
    local oy=M.height(plane,ox+base[1],oz+base[3])-base[2]
    local error=#profile.curve>0 and math.abs(oy+contact[2]-target[2]) or 0
    for _,w in ipairs(profile.ground) do
     local d=M.rotate(w,heading,pitch,roll)
     local hit=probe(ox+d[1],target[2]+15,oz+d[3])
     if not hit then return nil,'TERRAIN_MISS' end
     error=math.max(error,math.abs(oy+d[2]-hit[2]))
    end
    if error<=.1 and (not best or error<best.error) then
     best={x=ox,y=oy,z=oz,heading=heading,pitch=pitch,roll=roll,error=error,u=candidate.u}
    end
   end
  end
 end
 return best,best and nil or 'MODEL_FIT'
end
return M
