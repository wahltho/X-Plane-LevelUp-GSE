"""Read-only OBJ8 animation sampler. Emits only derived numeric contact profiles."""
import math
from collections import defaultdict
I=lambda:[[float(i==j) for j in range(4)] for i in range(4)]
def mul(a,b):return [[sum(a[i][k]*b[k][j] for k in range(4)) for j in range(4)] for i in range(4)]
def trans(v):
 m=I()
 for i in range(3):m[i][3]=v[i]
 return m
def rotate(axis,angle):
 n=math.sqrt(sum(v*v for v in axis));x,y,z=[v/n for v in axis];c=math.cos(math.radians(angle));s=math.sin(math.radians(angle));d=1-c
 return [[c+x*x*d,x*y*d-z*s,x*z*d+y*s,0],[y*x*d+z*s,c+y*y*d,y*z*d-x*s,0],[z*x*d-y*s,z*y*d+x*s,c+z*z*d,0],[0,0,0,1]]
def apply(m,p):return [sum(m[i][j]*p[j] for j in range(3))+m[i][3] for i in range(3)]
def interp(keys,u):
 keys=sorted(keys)
 if u<=keys[0][0]:return keys[0][1:]
 if u>=keys[-1][0]:return keys[-1][1:]
 for a,b in zip(keys,keys[1:]):
  if a[0]<=u<=b[0]:return [x+(y-x)*(u-a[0])/(b[0]-a[0]) for x,y in zip(a[1:],b[1:])]
def sample(path,height):
 lines=[l.split() for l in path.read_text().splitlines() if l.strip() and not l.lstrip().startswith('#')]
 verts=[];indices=[];stack=[I()];out=[];i=0
 def value(name):return height if 'belt_loader_height_meters' in name else (1 if 'engine_running' in name else 0)
 while i<len(lines):
  t=lines[i];op=t[0];i+=1
  if op=='VT':verts.append(list(map(float,t[1:4])))
  elif op in ('IDX','IDX10'):indices.extend(map(int,t[1:]))
  elif op=='ANIM_begin':stack.append([r[:] for r in stack[-1]])
  elif op=='ANIM_end':stack.pop()
  elif op in ('ANIM_rotate_begin','ANIM_trans_begin'):
   keys=[];name=t[-1]
   while i<len(lines):
    row=lines[i];i+=1
    if row[0] in ('ANIM_rotate_end','ANIM_trans_end'):break
    if row[0] in ('ANIM_rotate_key','ANIM_trans_key'):keys.append(list(map(float,row[1:])))
   v=interp(keys,value(name))
   m=rotate(list(map(float,t[1:4])),v[0]) if op=='ANIM_rotate_begin' else trans(v)
   stack[-1]=mul(stack[-1],m)
  elif op in ('ANIM_rotate','ANIM_trans'):
   nums=list(map(float,t[1:6 if op=='ANIM_rotate' else 7]))
   if op=='ANIM_rotate':
    a,b=nums[3:];u0,u1=(map(float,t[6:8]) if len(t)>=9 else (0,0));u=value(t[-1]) if len(t)>=9 else 0
    m=rotate(nums[:3],a if u0==u1 else a+(b-a)*max(0,min(1,(u-u0)/(u1-u0))))
   else:
    a,b=nums[:3],nums[3:];u0,u1=(map(float,t[7:9]) if len(t)>=10 else (0,0));u=value(t[-1]) if len(t)>=10 else 0
    f=0 if u0==u1 else max(0,min(1,(u-u0)/(u1-u0)))
    m=trans([x+(y-x)*f for x,y in zip(a,b)])
   stack[-1]=mul(stack[-1],m)
  elif op=='TRIS':
   start,count=map(int,t[1:3])
   out.extend([[apply(stack[-1],verts[k]) for k in indices[j:j+3]] for j in range(start,start+count,3)])
 return out
if __name__=='__main__':
 from pathlib import Path
 root=Path('/Users/wahltho/X-Plane 12/Resources/default scenery/airport scenery/Dynamic_Vehicles')
 for name in ['TUG_660.obj','catering_truck.obj']:
  for u in [1.2,1.7,2.2,2.8,3.5]:
   faces=sample(root/name,u);areas=defaultdict(float)
   for tri in faces:
    a,b,c=tri
    if max(p[1] for p in tri)-min(p[1] for p in tri)<.006:
     areas[round(sum(p[1] for p in tri)/3,2)]+=abs((b[0]-a[0])*(c[2]-a[2])-(c[0]-a[0])*(b[2]-a[2]))/2
   print(name,u,[(h,round(s,2)) for h,s in sorted(areas.items()) if s>.5 and h>1])
