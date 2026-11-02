"""Editable sagittal vocal-tract base mesh, Blender 4.3+.
Run: blender -b --python build_vocal_tract.py -- --output /path/to/output
Coordinates: X posterior, Y left lateral (retained half), Z superior.
One Blender unit = 10 mm. No armatures, animation, labels or UI.
"""
import bpy, math, os, sys, json
from mathutils import Vector
from math import sin, cos, pi
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
OUT=args[args.index('--output')+1] if '--output' in args else os.path.dirname(os.path.abspath(__file__))
os.makedirs(OUT,exist_ok=True)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
for c in list(bpy.data.collections):
    if c.name!='Collection': bpy.data.collections.remove(c)
base=bpy.data.collections.get('Collection'); base.name='01 · Supporting anatomy'
cols={'support':base}
for k,n in [('mobile','02 · Articulators'),('dental','03 · Dentition'),('airway','04 · Airway boundaries'),('studio','05 · Presentation')]:
    c=bpy.data.collections.new(n); bpy.context.scene.collection.children.link(c); cols[k]=c

def mat(name,color,rough=.5):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF'); p.inputs['Base Color'].default_value=(*color,1); p.inputs['Roughness'].default_value=rough
    return m
skin=mat('Supporting tissue · warm rose',(.53,.29,.25))
cut=mat('Cut tissue · pale terracotta',(.68,.41,.34))
bone=mat('Bone · warm ivory',(.86,.73,.52))
tongue_mat=mat('Tongue · muscular coral',(.61,.115,.135),.48)
mucosa=mat('Mucosa · muted rose',(.52,.21,.23))
lip_mat=mat('Vermilion · dusty carmine',(.58,.16,.18))
enamel=mat('Enamel · ivory',(.94,.89,.73),.28)
cart=mat('Cartilage · pale ochre',(.72,.59,.40))

def mesh_obj(name,verts,faces,material,coll='support',cut_faces=()):
    me=bpy.data.meshes.new(name+'_mesh'); me.from_pydata(verts,[],faces); me.update()
    ob=bpy.data.objects.new(name,me); cols[coll].objects.link(ob); me.materials.append(material)
    for f in me.polygons: f.use_smooth=True
    if cut_faces:
        me.materials.append(cut if material==skin else material)
        for i in cut_faces: me.polygons[i].use_smooth=False; me.polygons[i].material_index=1
    bpy.context.view_layer.objects.active=ob; ob.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.normals_make_consistent(inside=False); bpy.ops.object.mode_set(mode='OBJECT'); ob.select_set(False)
    ob['anatomy']='Left sagittal half; exposed medial plane Y=0'
    return ob

def catmull(points,n=5,closed=False):
    result=[]; N=len(points)
    for i in range(N if closed else N-1):
        p0=points[(i-1)%N] if closed or i else points[0]
        p1=points[i]; p2=points[(i+1)%N]; p3=points[(i+2)%N] if closed or i+2<N else points[-1]
        for j in range(n):
            t=j/n
            result.append(tuple(.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t**3) for a,b,c,d in zip(p0,p1,p2,p3)))
    if not closed: result.append(points[-1])
    return result

# Rounded, depth-varying tissue volumes. The sagittal profile is not extruded:
# successive transverse contours contract and shift to form a curved lateral surface.
def tissue(name,profile,width,material,center=None,coll='support'):
    p=catmull(profile,4,True); N=len(p)
    cx,cz=center or (sum(x for x,z in p)/N,sum(z for x,z in p)/N)
    v=[]; f=[]; layers=10
    for j in range(layers):
        a=(pi/2)*j/(layers-1); s=1-.16*(1-cos(a))
        for x,z in p:
            local=width
            v.append((cx+(x-cx)*s,local*sin(a),cz+(z-cz)*s))
    for j in range(layers-1):
        for i in range(N): f.append((j*N+i,j*N+(i+1)%N,(j+1)*N+(i+1)%N,(j+1)*N+i))
    # Medial and lateral tissue caps; immobile supporting parts only.
    f.append(tuple(reversed(range(N)))); cutidx=len(f)-1
    f.append(tuple((layers-1)*N+i for i in range(N)))
    ob=mesh_obj(name,v,f,material,coll,[cutidx]); ob['topology']='Quad lateral contours; planar n-gon cut cap on supporting anatomy'
    return ob

# Deformable sweep. Each anatomical station has an organic half-elliptical
# cross-section, closed medially by a structured quad strip. No booleans/remesh.
def sweep(name,stations,material,coll='mobile',samples=5,arcs=16):
    s=catmull(stations,samples); v=[]; f=[]; cuts=[]; K=arcs+1
    for i,(x,z,r,w) in enumerate(s):
        prev=s[max(0,i-1)]; nex=s[min(len(s)-1,i+1)]
        dx=nex[0]-prev[0]; dz=nex[1]-prev[1]; L=math.hypot(dx,dz) or 1
        nx=-dz/L; nz=dx/L
        for j in range(K):
            a=pi*j/arcs; v.append((x+nx*r*cos(a),max(0,w*sin(a)),z+nz*r*cos(a)))
    for i in range(len(s)-1):
        for j in range(arcs): f.append((i*K+j,(i+1)*K+j,(i+1)*K+j+1,i*K+j+1))
        f.append((i*K,i*K+arcs,(i+1)*K+arcs,(i+1)*K)); cuts.append(len(f)-1)
    # end caps restricted to terminals, away from bending zones
    f.extend([tuple(reversed(range(K))),tuple((len(s)-1)*K+j for j in range(K))])
    ob=mesh_obj(name,v,f,material,coll,cuts); ob['topology']='Longitudinal quad loops and medial quad closure; terminal n-gons'
    return ob

# Envelope follows the face, nasal vault and posterior neck, leaving the
# nasopharyngeal, oral and hypopharyngeal lumina open on the cut plane.
tissue('cranio_cervical_tissue',[(-3.85,3.0),(-3.1,3.9),(-2.85,4.95),(-2.4,5.55),(-.6,6.0),(1.6,5.85),(3.15,4.65),(3.48,2.2),(3.35,-.5),(3.05,-4.5),(1.92,-4.5),(2.0,-2.4),(2.17,-.2),(2.15,2.0),(1.6,3.55),(.45,3.95),(-1.0,3.8),(-2.3,3.35),(-3.1,2.95)],2.7,skin,center=(1.3,1.5))
tissue('upper_jaw',[(-3.25,2.83),(-2.6,2.55),(-1.55,2.35),(.25,2.26),(.6,1.94),(-.5,1.72),(-1.9,1.6),(-2.65,1.33),(-2.91,.87),(-3.17,1.28),(-3.22,2.05)],2.15,bone,center=(-1.3,2.02))
sweep('hard_palate',[(-2.8,1.38,.09,1.25),(-2.2,1.52,.12,1.75),(-1.3,1.68,.12,1.9),(-.35,1.76,.11,1.65),(.35,1.72,.09,1.3)],bone,'support')
sweep('soft_palate',[(.18,1.78,.12,1.28),(.57,1.62,.16,1.15),(.93,1.29,.17,.9),(1.1,.86,.14,.56),(1.12,.5,.08,.22)],mucosa)
# Tongue: thin mobile tip, blade, arched body and descending broad root.
sweep('tongue',[(-2.72,-.12,.055,.16),(-2.5,-.05,.16,.68),(-2.02,-.03,.30,1.18),(-1.4,-.02,.48,1.56),(-.65,-.1,.70,1.76),(.02,-.42,.79,1.7),(.49,-1.05,.64,1.42),(.72,-1.75,.46,1.1),(.78,-2.45,.24,.72)],tongue_mat,samples=6,arcs=24)
tissue('submandibular_tissue',[(-3.12,-.91),(-2.65,-1.6),(-1.6,-2.02),(-.2,-2.16),(.54,-2.75),(1.1,-3.8),(1.25,-4.5),(-.03,-4.5),(-.25,-3.42),(-1.35,-2.94),(-2.67,-2.35),(-3.35,-1.7)],2.1,skin,center=(-1.15,-2.6))
sweep('lower_jaw',[(-2.92,-.92,.18,1.08),(-2.88,-1.5,.29,1.32),(-2.18,-1.98,.25,1.7),(-1.25,-2.2,.22,1.96),(-.32,-2.15,.24,2.0),(.56,-1.62,.26,1.87),(1.05,-.72,.23,1.68),(1.0,.03,.2,1.47)],bone,'support')
sweep('oral_cavity_boundary',[(-2.72,-.72,.13,.9),(-2.1,-.96,.16,1.35),(-1.28,-1.15,.17,1.66),(-.4,-1.44,.16,1.63),(.35,-2.05,.17,1.18)],mucosa,'airway')
sweep('upper_lip',[(-3.20,1.7,.12,.22),(-3.34,1.28,.19,.88),(-3.43,.91,.18,1.17),(-3.45,.69,.09,1.30)],lip_mat)
sweep('lower_lip',[(-3.43,-.23,.10,1.20),(-3.44,-.45,.18,1.12),(-3.34,-.73,.18,.83),(-3.13,-.99,.10,.24)],lip_mat)
sweep('pharynx',[(1.76,3.18,.12,1.47),(2.03,2.45,.13,1.50),(2.15,1.45,.14,1.54),(2.18,.35,.14,1.48),(2.1,-.8,.15,1.35),(1.96,-1.9,.17,1.17),(1.8,-3.0,.17,.95),(1.75,-4.45,.16,.80)],mucosa,'airway')
# Nasal passage is an open roof/floor channel, not a solid obstruction.
sweep('nasal_cavity',[(-3.42,3.04,.085,.32),(-2.75,3.45,.10,.85),(-1.9,3.77,.10,1.1),(-.8,3.95,.1,1.28),(.3,3.99,.11,1.34),(1.25,3.65,.11,1.38),(1.7,3.07,.10,1.4)],mucosa,'airway')
for name,st in [('inferior_nasal_concha',[(-2.45,2.7,.10,.38),(-1.65,2.89,.13,.68),(-.7,2.99,.14,.87),(.25,3.00,.11,.67),(.85,2.8,.045,.32)]),('middle_nasal_concha',[(-2.0,3.23,.065,.3),(-1.24,3.42,.1,.62),(-.35,3.5,.11,.72),(.53,3.38,.05,.34)])]:
    ob=sweep(name,st,mucosa,'airway');
    # Turbinates arise from the lateral nasal wall; medial gap preserves airway.
    for vert in ob.data.vertices: vert.co.y+=.55
sweep('epiglottis',[(.82,-2.85,.10,.55),(.94,-2.35,.10,.63),(1.10,-1.9,.12,.64),(1.24,-1.54,.10,.48),(1.25,-1.34,.035,.18)],cart)
sweep('laryngeal_inlet',[(.82,-3.05,.11,.62),(.65,-3.42,.14,.69),(.62,-3.96,.14,.65),(.65,-4.45,.13,.62)],cart,'airway')

# Individual crowns on a true curved half dental arch; merged per jaw only.
def tooth(name,x,y,z,sx,sy,sz):
    v=[]; f=[]; sides=12
    for h,sc in [(-.5,.68),(-.40,.94),(.22,1.0),(.46,.82),(.5,.5)]:
        for j in range(sides):
            a=2*pi*j/sides
            # rounded rectangular crown cross section, rather than a sphere
            xx=math.copysign(abs(cos(a))**.55,cos(a)); yy=math.copysign(abs(sin(a))**.55,sin(a))
            v.append((x+sx*sc*xx/2,max(0,y+sy*sc*yy/2),z+sz*h))
    for k in range(4):
        for j in range(sides): f.append((k*sides+j,k*sides+(j+1)%sides,(k+1)*sides+(j+1)%sides,(k+1)*sides+j))
    f.extend([tuple(reversed(range(sides))),tuple(4*sides+j for j in range(sides))])
    ob=mesh_obj(name,v,f,enamel,'dental'); mod=ob.modifiers.new('Crown smoothing','SUBSURF'); mod.levels=1; mod.render_levels=1
    return ob
for upper in [True,False]:
    teeth=[]
    for i,a in enumerate([0,.24,.48,.73,.99,1.24,1.48,1.70]):
        x=-2.78+1.87*(1-cos(a)); y=1.92*sin(a)
        if not upper: x+=.13; y*=.96
        z=(.91 if upper else -.48)+.08*(1-cos(a))
        ob=tooth(('upper' if upper else 'lower')+'_tooth_'+str(i+1),x,y,z,.29 if i<3 else .46,.43 if i<3 else .48,.59 if upper else .49); teeth.append(ob)
    bpy.ops.object.select_all(action='DESELECT')
    for ob in teeth: ob.select_set(True)
    bpy.context.view_layer.objects.active=teeth[0]; bpy.ops.object.convert(target='MESH'); bpy.ops.object.join(); teeth[0].name='upper_teeth' if upper else 'lower_teeth'; teeth[0].select_set(False)

# Small medial offsets prevent coplanar intersections at tissue interfaces.
# Maximum offset is 0.8 mm; transverse dimensions remain anatomically meaningful.
medial_offsets={'cranio_cervical_tissue':.04,'submandibular_tissue':.03,
 'upper_jaw':-.015,'lower_jaw':-.018,'tongue':-.055,
 'hard_palate':-.045,'soft_palate':-.06,'upper_lip':-.065,'lower_lip':-.065,
 'pharynx':-.035,'nasal_cavity':-.035,'oral_cavity_boundary':-.03,
 'epiglottis':-.075,'laryngeal_inlet':-.04}
for name,offset in medial_offsets.items():
    bpy.data.objects[name].location.y=offset

# Scene metadata and presentation. Anatomy is the only mesh content.
scene=bpy.context.scene; scene.unit_settings.system='METRIC'; scene.unit_settings.scale_length=.01
scene['model_notes']='Editable conceptual anatomical base. No supplied reference image. Open sagittal half, Y>=0. Validate against medical references before clinical/phonetic simulation.'
scene.render.engine='CYCLES'; scene.cycles.samples=56
scene.cycles.use_denoising=False
scene.render.resolution_x=1400; scene.render.resolution_y=1400; scene.render.resolution_percentage=100
scene.world.color=(.12,.12,.12)
world=scene.world; world.use_nodes=True; world.node_tree.nodes['Background'].inputs[0].default_value=(.055,.075,.095,1); world.node_tree.nodes['Background'].inputs[1].default_value=.45
scene.view_settings.view_transform='AgX'

def point(ob,target): ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()
def area(name,loc,power,size):
    d=bpy.data.lights.new(name,'AREA'); d.energy=power; d.shape='DISK'; d.size=size; ob=bpy.data.objects.new(name,d); cols['studio'].objects.link(ob); ob.location=loc; point(ob,(0,0,.5))
area('Key',(-6,-8,10),1100,7); area('Fill',(5,-5,3),850,6); area('Rim',(2,6,8),1200,5)
d=bpy.data.cameras.new('Anatomy camera'); camera=bpy.data.objects.new('Anatomy camera',d); cols['studio'].objects.link(camera); scene.camera=camera; d.type='ORTHO'; d.ortho_scale=12.2
views=[('side_view',(0,-22,.8),(0,0,.8)),('perspective_view',(-7,-20,6.8),(0,.6,.8)),('front_angled_view',(-13,-18,4.0),(-.15,.6,.8))]
# Give the native file a useful material preview and sagittal viewport.
for screen in bpy.data.screens:
    for area_ in screen.areas:
        if area_.type=='VIEW_3D':
            space=area_.spaces.active; space.shading.type='MATERIAL'; space.overlay.show_overlays=False
            space.region_3d.view_distance=15; space.region_3d.view_location=(0,0,.8)
            from mathutils import Quaternion
            space.region_3d.view_rotation=Vector((0,-1,0)).to_track_quat('Z','Y')
            space.clip_end=200
bpy.ops.object.select_all(action='DESELECT')
for ob in bpy.data.objects:
    if ob.type=='MESH': ob.select_set(True)
bpy.context.view_layer.objects.active=bpy.data.objects.get('tongue')
# GLB includes anatomy only, leaving lighting/camera in native file.
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,'vocal_tract.glb'),export_format='GLB',use_selection=True,export_apply=True,export_animations=False,export_cameras=False,export_lights=False)
camera.location=views[0][1]; point(camera,views[0][2]); bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'vocal_tract.blend'))
report={}
for ob in bpy.data.objects:
    if ob.type=='MESH':
        me=ob.data
        report[ob.name]={'vertices':len(me.vertices),'faces':len(me.polygons),'quad_faces':sum(len(p.vertices)==4 for p in me.polygons),'depth_mm':round(ob.dimensions.y*10,2)}
with open(os.path.join(OUT,'mesh_report.json'),'w') as f: json.dump(report,f,indent=2)
# Material-and-studio captures using Blender's viewport render engine.
scene.render.engine='BLENDER_WORKBENCH'
sh=scene.display.shading; sh.light='STUDIO'; sh.studio_light='paint.sl'
sh.color_type='MATERIAL'; sh.show_shadows=True; sh.show_cavity=True
sh.cavity_type='BOTH'; sh.curvature_ridge_factor=1.1; sh.curvature_valley_factor=1.0
sh.background_type='WORLD'; scene.world.color=(.055,.065,.08)
for name,loc,target in views:
    camera.location=loc; point(camera,target); scene.render.filepath=os.path.join(OUT,name+'.png'); bpy.ops.render.render(write_still=True)
print('BUILD_COMPLETE',OUT)
