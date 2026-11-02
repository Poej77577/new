"""Adult-scale vocal tract, editable bilateral source + non-destructive sagittal cut.
Blender 4.3+. Run: blender -b --threads 8 --python build_vocal_tract.py -- --output DIR
Geometry specified in mm, stored in meters. No armature or animation.
"""
import bpy, math, os, sys, json, bmesh
import numpy as np
from mathutils import Vector
from math import sin,cos,pi,exp,sqrt
A=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
OUT=A[A.index('--output')+1] if '--output' in A else os.path.dirname(os.path.abspath(__file__))
os.makedirs(OUT,exist_ok=True); os.makedirs(OUT+'/textures',exist_ok=True)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
for c in list(bpy.data.collections):bpy.data.collections.remove(c)
C={}
for key,title in [('support','01 | Supporting tissue'),('bone','02 | Skeleton and dental arches'),('mobile','03 | Articulators - editable full meshes'),('airway','04 | Nasal and laryngeal anatomy'),('detail','05 | Anatomical detail'),('guides','06 | Articulation reference pivots'),('cutters','90 | Sagittal presentation cutters'),('studio','99 | Studio')]:
 c=bpy.data.collections.new(title);bpy.context.scene.collection.children.link(c);C[key]=c
M={}; rng=np.random.default_rng(77577)

def material(key,color,rough=.48,texture='tissue',sub=.0):
 m=bpy.data.materials.new(key);m.use_nodes=True;m.diffuse_color=(*color,1)
 n=m.node_tree.nodes;p=n.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough
 p.inputs['Subsurface Weight'].default_value=sub;p.inputs['Subsurface Radius'].default_value=(.6,.25,.15)
 if texture:
  N=512; y,x=np.mgrid[0:N,0:N].astype(float)/N;noise=rng.normal(0,1,(N,N))
  if texture=='muscle':
   detail=.035*np.sin(2*pi*(125*y+1.7*np.sin(2*pi*x)))+.025*np.sin(2*pi*(51*y+.7*np.sin(x*19)))+.012*noise
  elif texture=='bone':detail=.055*np.sin(x*143+np.sin(y*62)*5)*np.sin(y*181+np.sin(x*23))+.03*noise
  elif texture=='tongue':detail=.035*np.sin(x*391)*np.sin(y*313)+.035*noise
  else:detail=.018*np.sin(x*123+y*67)+.018*noise
  rgb=np.clip(np.asarray(color)[None,None,:]*(1+detail[:,:,None]),0,1)
  rgba=np.ones((N,N,4),dtype=np.float32);rgba[:,:,:3]=rgb
  img=bpy.data.images.new(key+'_albedo',N,N,alpha=False);img.pixels.foreach_set(rgba.ravel());img.filepath_raw=OUT+'/textures/'+key+'.png';img.file_format='PNG';img.save();img.pack()
  t=n.new('ShaderNodeTexImage');t.image=img;m.node_tree.links.new(t.outputs['Color'],p.inputs['Base Color'])
  bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.16;bump.inputs['Distance'].default_value=.00012 if texture!='bone' else .00022
  m.node_tree.links.new(t.outputs['Color'],bump.inputs['Height']);m.node_tree.links.new(bump.outputs['Normal'],p.inputs['Normal'])
 M[key]=m;return m
skin=material('skin',(.57,.33,.25),.58,sub=.035)
softcut=material('supporting_tissue_cut',(.62,.40,.30),.64,'muscle')
bone=material('cortical_bone',(.83,.76,.58),.52,'bone')
marrow=material('cancellous_bone',(.61,.44,.28),.65,'bone')
mucosa=material('mucosa',(.49,.18,.16),.38,sub=.06)
muscle=material('muscle',(.49,.095,.09),.51,'muscle',.025)
tongueM=material('tongue_surface',(.55,.16,.155),.39,'tongue',.07)
tongueCut=material('tongue_cut',(.48,.115,.11),.53,'muscle')
lipM=material('lip_vermilion',(.48,.115,.12),.4,'tissue',.06)
gumM=material('gingiva',(.53,.20,.18),.39,'tissue',.08)
enamel=material('enamel',(.89,.86,.73),.25,None)
dentin=material('dentin',(.70,.59,.39),.5,None)
cart=material('cartilage',(.70,.65,.45),.48,'tissue')
disc=material('intervertebral_disc',(.42,.40,.34),.55,'tissue')

# All source meshes keep quad loops. Planar tissue caps/terminal caps are n-gons.
# The cut modifier comes LAST, so the underlying bilateral mesh remains editable.
objects=[];cutcache={}
def cutter(offset):
 key=round(offset,3)
 if key in cutcache:return cutcache[key]
 bpy.ops.mesh.primitive_cube_add(size=1,location=(0,(-300+offset)/1000,0))
 o=bpy.context.object;o.name='CUT_Y_'+str(key)+'mm';o.dimensions=(1.2,.6,1.2);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 for c in list(o.users_collection):c.objects.unlink(o)
 C['cutters'].objects.link(o);o.hide_render=True;o.hide_set(True);o.display_type='WIRE'
 o.data.materials.append(softcut);o.data.materials.append(softcut)
 for p in o.data.polygons:p.material_index=1
 cutcache[key]=o;return o

def mesh(name,v,f,mat,coll='mobile',cutmat=None,cutoff=-.1,subdiv=0,uvs=None):
 me=bpy.data.meshes.new(name+'_quad_source');me.from_pydata([tuple(a/1000 for a in p) for p in v],[],f);me.update()
 ob=bpy.data.objects.new(name,me);C[coll].objects.link(ob);me.materials.append(mat);me.materials.append(cutmat or mat)
 for p in me.polygons:p.use_smooth=len(p.vertices)==4
 uv=me.uv_layers.new(name='anatomical_uv')
 for p in me.polygons:
  for li in p.loop_indices:
   vi=me.loops[li].vertex_index;co=v[vi]
   uv.data[li].uv=uvs[vi] if uvs else ((co[0]+100)/200,(co[2]+140)/280)
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
 if subdiv:
  mod=ob.modifiers.new('Surface refinement - before articulation','SUBSURF');mod.levels=subdiv;mod.render_levels=subdiv
 if cutoff is not None:
  mod=ob.modifiers.new('Sagittal display - disable for full anatomy','BOOLEAN');mod.object=cutter(cutoff);mod.operation='DIFFERENCE';mod.solver='EXACT';mod.material_mode='INDEX'
 ob['source_geometry']='Full bilateral anatomy, dimensions in meters. Disable LAST Boolean to view full mesh.'
 ob['rigging_order']='Armature/deformation modifiers must precede Sagittal display Boolean.'
 objects.append(ob);return ob

def cat(p,n=5,closed=False):
 o=[];N=len(p)
 for i in range(N if closed else N-1):
  a=p[(i-1)%N] if closed or i else p[0];b=p[i];c=p[(i+1)%N];d=p[(i+2)%N] if closed or i+2<N else p[-1]
  for j in range(n):
   t=j/n;o.append(tuple(.5*(2*q+(-r+s)*t+(2*r-5*q+4*s-u)*t*t+(-r+3*q-3*s+u)*t**3) for r,q,s,u in zip(a,b,c,d)))
 if not closed:o.append(p[-1])
 return o

def sweep(name,stations,mat,coll='mobile',cutmat=None,cutoff=-.1,N=32,samples=5,tongue=False,subdiv=1):
 st=cat(stations,samples);v=[];f=[];uv=[]
 for i,(x,z,r,w) in enumerate(st):
  a=st[max(0,i-1)];b=st[min(len(st)-1,i+1)];dx=b[0]-a[0];dz=b[1]-a[1];L=math.hypot(dx,dz);nx=-dz/L;nz=dx/L
  for j in range(N):
   t=2*pi*j/N; yy=w*sin(t); rr=r*cos(t)
   xx=x+nx*rr;zz=z+nz*rr
   if tongue:
    # Dorsal median sulcus, and natural lateral fullness. No random silhouette noise.
    zz-=.65*exp(-(yy/2.5)**2)*max(0,cos(t))**4*sin(pi*i/(len(st)-1))**2
    zz+=.13*sin(i*.47+j*.7)*sin(t)**2*max(0,cos(t))
   v.append((xx,yy,zz));uv.append((i/(len(st)-1),j/N))
 for i in range(len(st)-1):
  for j in range(N):f.append((i*N+j,(i+1)*N+j,(i+1)*N+(j+1)%N,i*N+(j+1)%N))
 f.extend([tuple(reversed(range(N))),tuple((len(st)-1)*N+j for j in range(N))])
 return mesh(name,v,f,mat,coll,cutmat,cutoff,subdiv,uv)

def tissue(name,profile,width,mat=skin,cutmat=softcut,coll='support',cutoff=.25):
 p=cat(profile,5,True);N=len(p);cx=sum(x for x,z in p)/N;cz=sum(z for x,z in p)/N;v=[];f=[];L=19
 for j in range(L):
  theta=-pi/2+pi*j/(L-1);s=1-.10*(1-cos(theta))
  for x,z in p:v.append((cx+(x-cx)*s,width*sin(theta),cz+(z-cz)*s))
 for j in range(L-1):
  for i in range(N):f.append((j*N+i,j*N+(i+1)%N,(j+1)*N+(i+1)%N,(j+1)*N+i))
 f.extend([tuple(reversed(range(N))),tuple((L-1)*N+i for i in range(N))])
 return mesh(name,v,f,mat,coll,cutmat,cutoff)

# Midface / cranial base / cervical envelope. Its interior contour leaves actual airspace.
tissue('cranio_cervical_tissue',[(-85,61),(-76,77),(-70,95),(-65,118),(-53,132),(-13,140),(34,134),(69,114),(82,77),(80,21),(72,-43),(63,-94),(60,-129),(40,-129),(37,-94),(43,-61),(47,-21),(47,27),(40,68),(24,90),(0,101),(-28,100),(-49,87),(-62,69),(-68,57),(-79,55)],66)
# Thin skin edge at the nose and lower facial profile is physically rounded.
sweep('nasal_bridge_cartilage',[(-65,107,2,12),(-69,89,3,14),(-76,75,4,16),(-82,63,4,15),(-75,56,3,15)],cart,'support',cart,.12,N=32)
tissue('maxillary_support',[(-69,55),(-57,49),(-41,45),(-19,44),(2,42),(4,36),(-19,34),(-43,30),(-56,28),(-60,20),(-66,21),(-68,35)],28,bone,marrow,'bone',-.10)
sweep('nasolabial_tissue',[(-74,54,3,14),(-68,43,4,18),(-67,30,4,21),(-69,19,3,22)],skin,'support',softcut,.12)
sweep('hard_palate',[(-57,31,1.8,15),(-45,34,2.0,23),(-29,37,2.1,27),(-13,39,2.0,26),(3,39,1.6,22)],bone,'bone',bone,-.35,N=40)
sweep('palatal_mucosa',[(-56,28,1.0,15),(-44,31.5,1.0,23),(-28,34.4,1.1,26),(-12,36.5,1.0,25),(3,36.8,.8,21)],mucosa,'airway',mucosa,-.45,N=40)
velum=sweep('soft_palate',[(2,38,1.8,22),(11,35,2.5,20),(19,28,2.7,17),(23,19,2.4,11),(21,11,1.5,5)],mucosa,'mobile',muscle,-.6,N=40,samples=7)
sweep('uvula',[(21,13,1.7,3.2),(20,8,2.2,3.0),(19,4,1.5,2.3),(19,2,.3,.5)],mucosa,'detail',muscle,-.7,N=24)
tongue=sweep('tongue',[(-59,1,.8,4),(-54,1,2.8,13),(-44,2,5.8,22),(-30,1,9.5,27),(-15,-1,14,29),(-2,-11,15,25),(8,-26,12,21),(12,-40,9,15),(12,-51,4,9)],tongueM,'mobile',tongueCut,-.75,N=64,samples=7,tongue=True)
# Subtle transverse palatal rugae, anterior to the soft palate.
for k in range(5):
 x=-48+5*k;z=31.5+.19*(x+44)
 st=[]
 for j in range(9):
  y=-18+36*j/8;st.append((x+2.0*cos(y/18*pi/2),y,z-1.1-.6*(y/18)**2,.65))
 # Actual continuous 3D ridge follows the transverse palatal vault.
 def tube3(name,st,mat,coll='detail',cutoff=-.3,N=16):
  sp=cat(st,4);vv=[];ff=[]
  for i,(x,y,z,r) in enumerate(sp):
   p=Vector(sp[max(0,i-1)][:3]);q=Vector(sp[min(len(sp)-1,i+1)][:3]);t=(q-p).normalized();a=t.cross(Vector((0,0,1)))
   if a.length<.1:a=t.cross(Vector((0,1,0)))
   a.normalize();b=t.cross(a).normalized()
   for j in range(N):
    c=Vector((x,y,z))+r*(a*cos(2*pi*j/N)+b*sin(2*pi*j/N));vv.append(tuple(c))
  for i in range(len(sp)-1):
   for j in range(N):ff.append((i*N+j,(i+1)*N+j,(i+1)*N+(j+1)%N,i*N+(j+1)%N))
  ff.extend([tuple(reversed(range(N))),tuple((len(sp)-1)*N+j for j in range(N))])
  return mesh(name,vv,ff,mat,coll,mat,cutoff,1)
 tube3('palatal_ruga_'+str(k+1),st,mucosa)

# Oral floor and genioglossus: separate muscular supports, not an empty triangle.
sweep('genioglossus',[(-51,-17,2,7),(-39,-21,5,14),(-24,-26,8,20),(-10,-35,9,20),(3,-46,5,12)],muscle,'mobile',tongueCut,-.5,N=40)
sweep('oral_cavity_boundary',[(-57,-9,1.4,14),(-43,-14,2.6,24),(-27,-22,3.4,28),(-12,-33,3,25),(3,-46,2,14)],mucosa,'airway',muscle,-.8,N=40)
tissue('submandibular_tissue',[(-66,-12),(-68,-29),(-60,-43),(-42,-54),(-20,-61),(-3,-76),(8,-102),(12,-129),(39,-129),(30,-96),(20,-70),(8,-53),(-12,-41),(-37,-29),(-57,-22)],32)

# Continuous lip volume follows the real transverse mouth arch.
def lip(name,upper):
 N=40;L=65;v=[];f=[];uv=[]
 for i in range(L):
  y=-26+52*i/(L-1);t=y/26;edge=max(.08,(1-t*t)**.6)
  x=-72+19*t*t;z=(12-6*t*t+1.0*cos(3*pi*t)*exp(-4*t*t)) if upper else (-4+9*t*t)
  for j in range(N):
   a=2*pi*j/N;fold=.15*sin(18*a+1.1*t)*edge
   v.append((x+(4.2*edge+.25)*cos(a),y,z+(3.6*edge+.2+fold)*sin(a)));uv.append((i/(L-1),j/N))
 for i in range(L-1):
  for j in range(N):f.append((i*N+j,(i+1)*N+j,(i+1)*N+(j+1)%N,i*N+(j+1)%N))
 f.extend([tuple(reversed(range(N))),tuple((L-1)*N+j for j in range(N))])
 return mesh(name,v,f,lipM,'mobile',muscle,-.9,1,uv)
upperlip=lip('upper_lip',True);lowerlip=lip('lower_lip',False)
upper_lip_support=tissue('upper_lip_support',[(-69,37),(-61,33),(-57,26),(-59,17),(-67,10),(-73,9),(-75,14),(-70,23)],24,skin,softcut,'mobile',.08)
lower_lip_support=tissue('lower_lip_support',[(-72,-3),(-66,-8),(-58,-12),(-57,-22),(-62,-31),(-67,-27),(-70,-16),(-75,-7)],25,skin,softcut,'mobile',.05)
# Orbicularis attachment fields behind the vermilion.
sweep('upper_orbicularis_attachment',[(-67,23,2,22),(-67,18,2.5,24),(-67,13,1.8,24)],muscle,'mobile',muscle,-.25,N=32)
sweep('lower_orbicularis_attachment',[(-66,-6,2,23),(-64,-12,3,24),(-61,-18,2,23)],muscle,'mobile',muscle,-.25,N=32)

# True 3D mandibular half-arches meet at the symphysis; condyles stay lateral.
def jawmesh():
 half=[(-58,0,-26,10,6),(-54,12,-29,9,6),(-41,23,-33,8,6),(-21,30,-37,7,6),(0,33,-39,8,6),(22,42,-36,10,7),(35,48,-22,8,7),(39,50,-3,7,6),(36,52,16,6,5),(34,52,26,4.5,7)]
 st=[(x,-y,z,r,w) for x,y,z,r,w in reversed(half[1:])]+half
 sp=cat(st,5);v=[];f=[];N=32
 for i,(x,y,z,r,w) in enumerate(sp):
  a=Vector(sp[max(0,i-1)][:3]);b=Vector(sp[min(len(sp)-1,i+1)][:3]);t=(b-a).normalized();n=t.cross(Vector((0,0,1)))
  if n.length<.1:n=Vector((1,0,0))
  n.normalize();up=n.cross(t).normalized()
  for j in range(N):
   p=Vector((x,y,z))+n*w*sin(2*pi*j/N)+up*r*cos(2*pi*j/N);v.append(tuple(p))
 for i in range(len(sp)-1):
  for j in range(N):f.append((i*N+j,(i+1)*N+j,(i+1)*N+(j+1)%N,i*N+(j+1)%N))
 f.extend([tuple(reversed(range(N))),tuple((len(sp)-1)*N+j for j in range(N))])
 return mesh('lower_jaw',v,f,bone,'bone',marrow,-.3,1)
mandible=jawmesh()
# Dental gingival arches: model full arch to preserve jaw motion as a unit.
def arch_st(z,r):
 st=[]
 for i in range(33):
  a=-1.66+3.32*i/32;st.append((-57+53*(1-cos(a)),27*sin(a),z+1.8*(1-cos(a)),r))
 return st
uppergum=tube3('upper_gingiva',arch_st(27,4.8),gumM,'bone',-.7,24)
lowergum=tube3('lower_gingiva',arch_st(-14,4.4),gumM,'bone',-.7,24)
upperalveolar=tube3('upper_alveolar_bone',arch_st(35,7),bone,'bone',-.2,24)
loweralveolar=tube3('lower_alveolar_bone',arch_st(-25,8),bone,'bone',-.2,24)

# Individual incisors, canine, bicuspids and four-cusp molars, with anatomical roots.
# Islands remain separable by loose parts inside each arch mesh.
def dental(upper,roots=False):
 v=[];f=[];N=24
 for side in [-1,1]:
  for k,a in enumerate([.105,.30,.51,.73,.95,1.17,1.39,1.61]):
   x=-57+53*(1-cos(a));y=side*27*sin(a);orient=side*a
   wx=[5.4,5.2,6.1,7,7,9,10,9.5][k];wy=[8.2,6.8,7.4,7.5,8.2,10,10.8,10][k]
   h=10.5 if upper else 9.2;incisal=13 if upper else -1;sign=1 if upper else -1
   rootspec=[(0,0)] if k<3 else [(-wx*.2,0),(wx*.2,0)] if k<5 else [(-wx*.22,-wy*.2),(wx*.23,-wy*.15),(0,wy*.22)]
   pieces=rootspec if roots else [(0,0)]
   for ox,oy in pieces:
    start=len(v);L=11
    for ring in range(L):
     t=ring/(L-1)
     if roots:zz=incisal+sign*(h+2+14*t);scale=(1-t)**.72*.46+.015
     else:zz=incisal+sign*h*t;scale=.79+.19*sin(pi*t)-.18*t**4
     for j in range(N):
      ang=2*pi*j/N;cx=math.copysign(abs(cos(ang))**.65,cos(ang));cy=math.copysign(abs(sin(ang))**.65,sin(ang))
      xx=ox+wx*.5*scale*cx;yy=oy+wy*.5*scale*cy;dz=0
      if not roots:
       if k==2:cusps=.9*exp(-((ang-pi/2)/.6)**2)
       elif k>=3:cusps=.9*cos((2 if k<5 else 4)*ang)+.32*sin(ang*2)
       else:cusps=.15*cos(2*ang)
       dz=-sign*cusps*exp(-t*8)
      v.append((x+xx*cos(orient)-yy*sin(orient),y+xx*sin(orient)+yy*cos(orient),zz+dz))
    for ring in range(L-1):
     for j in range(N):f.append((start+ring*N+j,start+(ring+1)*N+j,start+(ring+1)*N+(j+1)%N,start+ring*N+(j+1)%N))
    # Occlusal quad concentric patch, with fissures between cusps.
    capstart=len(v)
    for j in range(N):
     p=v[start+j];basez=incisal if not roots else incisal+sign*(h+2)
     v.append((x+(p[0]-x)*.30,y+(p[1]-y)*.30,basez+sign*(.85 if k>=3 and not roots else .12)))
    for j in range(N):f.append((start+j,start+(j+1)%N,capstart+(j+1)%N,capstart+j))
    f.append(tuple(capstart+j for j in reversed(range(N))))
    f.append(tuple(start+(L-1)*N+j for j in range(N)))
 return mesh(('upper' if upper else 'lower')+('_tooth_roots' if roots else '_teeth'),v,f,dentin if roots else enamel,'bone',dentin if roots else enamel,-.85,1)
upperteeth=dental(True);lowerteeth=dental(False);upperroots=dental(True,True);lowerroots=dental(False,True)

# Nasal vault, turbinates, pharyngeal posterior wall, epiglottis and larynx.
sweep('nasal_cavity',[(-75,57,1.1,12),(-60,74,1.1,17),(-41,88,1.2,21),(-18,96,1.3,22),(5,96,1.4,23),(25,86,1.4,23),(36,69,1.2,22)],mucosa,'airway',mucosa,-.55,N=40)
sweep('nasal_floor',[(-72,53,1.2,13),(-56,47,1.3,20),(-37,44,1.2,25),(-15,43,1.1,25),(4,43,1.1,22)],mucosa,'airway',mucosa,-.55,N=32)
# Scroll-shaped conchae have a free inferior edge and a curved bony core.
for name,x0,z0,l,w in [('inferior',-54,57,65,12),('middle',-44,74,50,10),('superior',-25,87,28,7)]:
 # A small curved roll in XZ, attached laterally away from the septal plane.
 st=[(x0,z0,1.0,w*.35),(x0+l*.23,z0+3,2.2,w*.7),(x0+l*.55,z0+4,2.8,w),(x0+l*.82,z0+1,2.4,w*.8),(x0+l,z0-3,1,w*.35)]
 ob=sweep(name+'_nasal_concha',st,mucosa,'airway',bone,None,N=32)
 # Both paired turbinates are full meshes. Move halves away from midline with duplications.
 ob.location.y=.014;ob.scale.y=.65
 dup=ob.copy();dup.data=ob.data.copy();C['airway'].objects.link(dup);dup.name=name+'_nasal_concha_contralateral';dup.location.y=-.014;objects.append(dup)
 for o in [ob,dup]:
  mod=o.modifiers.new('Sagittal display - disable for full anatomy','BOOLEAN');mod.object=cutter(-.15);mod.operation='DIFFERENCE';mod.solver='EXACT';mod.material_mode='INDEX'
sweep('pharynx',[(34,83,2.1,22),(42,63,2.2,23),(45,39,2.2,22),(45,14,2.4,21),(42,-13,2.5,20),(37,-39,2.8,18),(31,-63,2.5,15),(29,-83,2.2,12)],mucosa,'airway',muscle,-.7,N=40,samples=6)
epiglottis=sweep('epiglottis',[(14,-70,1.2,7),(17,-60,1.6,10),(20,-48,1.8,12),(23,-38,1.5,10),(23,-31,.6,3)],cart,'mobile',cart,-1.05,N=40,samples=6)
sweep('aryepiglottic_fold',[(24,-72,1.3,11),(29,-64,1.5,12),(28,-55,1.1,10)],mucosa,'airway',muscle,-.75,N=32)
sweep('laryngeal_anterior_wall',[(9,-75,2.0,11),(8,-85,2.1,12),(10,-96,1.8,11)],cart,'airway',cart,-.8,N=32)
sweep('laryngeal_posterior_wall',[(30,-70,1.8,11),(31,-81,2,12),(29,-95,1.7,10)],mucosa,'airway',muscle,-.7,N=32)
# Vocal folds are tissue shelves; no educational labels or animation.
for side in [-1,1]:
 ob=tube3('vocal_fold_'+('left' if side>0 else 'right'),[(11,side*2,-82,1),(17,side*3,-81,1.3),(25,side*6,-80,1)],enamel,'airway',-.7,20)

# Hollow airway and esophagus: inner and outer structured rings, not solid cylinders.
def hollow(name,cx,z0,z1,rx,ry,wall,mat,cutoff=-.6):
 v=[];f=[];N=48;L=25
 for inner in [False,True]:
  for k in range(L):
   z=z0+(z1-z0)*k/(L-1)
   for j in range(N):
    a=2*pi*j/N;v.append((cx+(rx-(wall if inner else 0))*cos(a),(ry-(wall if inner else 0))*sin(a),z))
 for side in range(2):
  off=side*L*N
  for k in range(L-1):
   for j in range(N):
    face=(off+k*N+j,off+k*N+(j+1)%N,off+(k+1)*N+(j+1)%N,off+(k+1)*N+j);f.append(face if side==0 else tuple(reversed(face)))
 for k in [0,L-1]:
  for j in range(N):f.append((k*N+j,L*N+k*N+j,L*N+k*N+(j+1)%N,k*N+(j+1)%N))
 return mesh(name,v,f,mat,'airway',mat,cutoff,1)
hollow('tracheal_wall',18,-94,-129,10,9,1.4,mucosa)
hollow('esophagus',37,-86,-129,5.8,8,1.5,muscle,-.5)
for i in range(8):
 z=-97-i*4.1;st=[]
 for j in range(19):
  a=-pi*.82+pi*1.64*j/18;st.append((18-10*cos(a),9*sin(a),z,1.05))
 tube3('tracheal_cartilage_'+str(i+1).zfill(2),st,cart,'detail',-.75,16)
# Hyoid horseshoe, tucked beneath tongue root.
st=[]
for j in range(25):
 a=-pi/2+pi*j/24;st.append((-2+17*(1-cos(a)),17*sin(a),-56+2*cos(a),2))
tube3('hyoid',st,bone,'bone',-.95,24)
# Cervical bodies and discs establish the posterior throat relationship.
for i,z in enumerate([-30,-51,-72,-93,-114]):
 tissue('cervical_body_'+str(i+3),[(54,z+8),(65,z+10),(76,z+6),(76,z-7),(65,z-10),(54,z-7)],14,bone,marrow,'bone',-.25)
 if i<4:tissue('cervical_disc_'+str(i+3),[(55,z-10),(74,z-10),(74,z-13),(55,z-13)],13,disc,disc,'bone',-.32)

# Lightly raised circumvallate papillae, connected later to the tongue as detail children.
for side in [-1,1]:
 for i in range(5):
  y=side*(4+i*3.8);x=-11+i*1.6;z=12-.12*i*i
  ob=sweep('vallate_papilla_'+str(side)+'_'+str(i),[(x-1,z,.18,.4),(x,z+.3,.7,1.1),(x+1,z,.18,.4)],tongueM,'detail',tongueCut,-.8,N=16,samples=3,subdiv=1)
  ob.parent=tongue

# Reference pivots and semantic vertex groups aid later rigging; no bones or keys.
def pivot(name,point,display=4):
 o=bpy.data.objects.new(name,None);C['guides'].objects.link(o);o.location=Vector(point)/1000;o.empty_display_type='PLAIN_AXES';o.empty_display_size=display/1000;o.hide_render=True;return o
jawpivot=pivot('jaw_rotation_reference',(35,0,25),8)
pivot('tmj_left',(35,52,25));pivot('tmj_right',(35,-52,25));pivot('velum_attachment_reference',(2,0,38));pivot('tongue_root_reference',(12,0,-45))
bpy.context.view_layer.update()
for ob in [mandible,lowergum,lowerteeth,lowerroots,lowerlip,loweralveolar,lower_lip_support,bpy.data.objects.get('lower_orbicularis_attachment')]:
 ob.parent=jawpivot;ob.matrix_parent_inverse=jawpivot.matrix_world.inverted()
# Origins have not moved the geometry. Set actual rotation origin on mandibular mesh too.
for ob in [tongue,velum,upperlip,lowerlip,upper_lip_support,lower_lip_support]:
 if ob==tongue:
  centers=[('tongue_tip',-56),('tongue_blade',-43),('tongue_body',-22),('tongue_root',8)]
  groups=[(ob.vertex_groups.new(name=n),cx) for n,cx in centers]
  for v in ob.data.vertices:
   x=v.co.x*1000;weights=[exp(-((x-cx)/16)**2) for g,cx in groups];tot=sum(weights)
   for (g,cx),w in zip(groups,weights):g.add([v.index],w/tot,'REPLACE')
 elif ob==velum:
  root=ob.vertex_groups.new(name='velum_attachment');free=ob.vertex_groups.new(name='velum_free_edge')
  for v in ob.data.vertices:
   w=max(0,min(1,(v.co.x*1000-2)/20));root.add([v.index],1-w,'REPLACE');free.add([v.index],w,'REPLACE')
 else:
  center=ob.vertex_groups.new(name='lip_center');corner=ob.vertex_groups.new(name='lip_commissure')
  for v in ob.data.vertices:
   w=min(1,abs(v.co.y*1000)/26);center.add([v.index],1-w,'REPLACE');corner.add([v.index],w,'REPLACE')

scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1;scene.unit_settings.length_unit='MILLIMETERS'
scene['version']='2.0 | adult-scale detailed reconstruction'
scene['coordinates']='X posterior, Y lateral, Z superior. Mesh coordinates in meters.'
scene['rigging']='Source articulators are complete bilateral quad meshes. Boolean sagittal display must remain LAST. No rig, animation or tested motion range.'
scene['reference']='No supplied reference image or patient data. Nominal adult dimensions; not medically validated.'
# Focus native viewport on anatomy, without cutters/lights overlays.
for sc in bpy.data.screens:
 for ar in sc.areas:
  if ar.type=='VIEW_3D':
   s=ar.spaces.active;s.shading.type='MATERIAL';s.overlay.show_overlays=False;s.clip_start=.001;s.clip_end=10
   s.region_3d.view_distance=.43;s.region_3d.view_location=(0,0,.004);s.region_3d.view_rotation=Vector((0,-1,0)).to_track_quat('Z','Y')
# Presentation camera and real area lighting.
def point(ob,t):ob.rotation_euler=(Vector(t)-ob.location).to_track_quat('-Z','Y').to_euler()
def light(name,loc,power,size):
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;o=bpy.data.objects.new(name,d);C['studio'].objects.link(o);o.location=loc;point(o,(0,0,0))
light('large_softbox',(-.22,-.35,.34),12,.26);light('soft_fill',(.28,-.25,.05),7,.23);light('edge_light',(.1,.25,.25),16,.19)
world=bpy.data.worlds.new('Anatomy studio');scene.world=world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.045,.055,.07,1);world.node_tree.nodes['Background'].inputs[1].default_value=.4
camdata=bpy.data.cameras.new('Anatomical camera');cam=bpy.data.objects.new('Anatomical camera',camdata);C['studio'].objects.link(cam);scene.camera=cam;camdata.type='ORTHO';camdata.ortho_scale=.328;camdata.clip_start=.001;camdata.clip_end=10
cam.location=(0,-.6,.004);point(cam,(0,0,.004))
scene.render.resolution_x=1600;scene.render.resolution_y=1800;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX'
scene.render.engine='CYCLES';scene.cycles.samples=64;scene.cycles.use_denoising=False
bpy.ops.object.select_all(action='DESELECT');tongue.select_set(True);bpy.context.view_layer.objects.active=tongue
# Capture source topology and cut/export geometry statistics separately.
dg=bpy.context.evaluated_depsgraph_get();report={}
for ob in objects:
 if ob.type!='MESH':continue
 bm=bmesh.new();bm.from_mesh(ob.data);source_nonmanifold=sum(not e.is_manifold for e in bm.edges);zero=sum(f.calc_area()<1e-14 for f in bm.faces);bm.free()
 ev=ob.evaluated_get(dg);me=ev.to_mesh();verts=[ev.matrix_world@v.co for v in me.vertices]
 dimensions=[round((max(p[a] for p in verts)-min(p[a] for p in verts))*1000,2) if verts else 0 for a in range(3)]
 report[ob.name]={'source_vertices':len(ob.data.vertices),'source_faces':len(ob.data.polygons),'source_quad_fraction':round(sum(len(p.vertices)==4 for p in ob.data.polygons)/len(ob.data.polygons),4),'source_nonmanifold_edges':source_nonmanifold,'source_zero_area_faces':zero,'display_dimensions_mm_XYZ':dimensions,'vertex_groups':list(ob.vertex_groups.keys())}
 ev.to_mesh_clear()
with open(OUT+'/mesh_report.json','w') as f:json.dump(report,f,indent=2)
bpy.ops.wm.save_as_mainfile(filepath=OUT+'/vocal_tract.blend')
# Export displayed sagittal anatomy, with actual materials/textures, excluding guides/cutters.
bpy.ops.object.select_all(action='DESELECT')
for ob in objects:
 if ob.type=='MESH':ob.select_set(True)
bpy.ops.export_scene.gltf(filepath=OUT+'/vocal_tract.glb',export_format='GLB',use_selection=True,export_apply=True,export_animations=False,export_cameras=False,export_lights=False,export_extras=True)
# Fast, consistent studio viewport captures. --beauty enables an additional Cycles image.
scene.render.engine='BLENDER_WORKBENCH';sh=scene.display.shading;sh.light='STUDIO';sh.studio_light='paint.sl';sh.color_type='MATERIAL';sh.show_shadows=True;sh.show_cavity=True;sh.cavity_type='BOTH';sh.curvature_ridge_factor=1.15;sh.curvature_valley_factor=1.0;sh.background_type='WORLD';world.color=(.045,.055,.07)
for name,loc,target in [('side_view',(0,-.65,.004),(0,0,.004)),('perspective_view',(-.17,-.60,.12),(0,.012,.003)),('front_angled_view',(-.36,-.55,.09),(-.005,.016,.003))]:
 cam.location=loc;point(cam,target);scene.render.filepath=OUT+'/'+name+'.png';bpy.ops.render.render(write_still=True)
if '--beauty' in A:
 scene.render.engine='CYCLES';cam.location=(-.12,-.65,.08);point(cam,(0,.008,.003));scene.render.filepath=OUT+'/anatomy_detail.png';bpy.ops.render.render(write_still=True)
if '--beauty' in A:
 scene.render.resolution_x=1600;scene.render.resolution_y=1300
 cam.data.ortho_scale=.145;cam.location=(-.25,-.43,.12);point(cam,(-.025,.012,-.010))
 scene.render.filepath=OUT+'/articulators_detail.png';bpy.ops.render.render(write_still=True)
print('BUILD_V2_COMPLETE',OUT)
