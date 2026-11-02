import bpy,bmesh,json,math
from mathutils import Vector
import os,sys
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
O=args[0] if args else os.path.dirname(os.path.abspath(__file__))
bpy.ops.wm.open_mainfile(filepath=O+'/vocal_tract.blend')
s=bpy.context.scene
report=json.load(open(O+'/mesh_report.json'))
assert all(v['source_nonmanifold_edges']==0 and v['source_zero_area_faces']==0 for v in report.values())
assert not bpy.data.armatures and not bpy.data.actions
for name in ['tongue','soft_palate','upper_lip','lower_lip']:
 o=bpy.data.objects[name]
 assert o.modifiers[-1].type=='BOOLEAN'
 assert o.vertex_groups
 for v in o.data.vertices:
  assert abs(sum(g.weight for g in v.groups)-1)<1e-5,(name,v.index)
# Test the reference pivot reversibly, without saving an animation or changing the asset.
pivot=bpy.data.objects['jaw_rotation_reference'];upper=bpy.data.objects['upper_teeth'];lower=bpy.data.objects['lower_teeth']
base_u=[upper.matrix_world@v.co for v in upper.data.vertices]
base_l=[lower.matrix_world@v.co for v in lower.data.vertices]
assert abs(lower.matrix_world.translation.length)<1e-8,tuple(lower.matrix_world.translation)
assert abs(bpy.data.objects['lower_lip'].matrix_world.translation.length)<1e-8
before_upper=upper.matrix_world.copy()
pivot.rotation_euler.y=math.radians(-12);bpy.context.view_layer.update()
after_l=[lower.matrix_world@v.co for v in lower.data.vertices]
# The front incisors must move inferiorly; upper arch must remain fixed.
indices=[i for i,p in enumerate(base_l) if p.x<-.053]
opening_mm=sum((base_l[i].z-after_l[i].z)*1000 for i in indices)/len(indices)
assert opening_mm>15,opening_mm
assert all((upper.matrix_world@v.co-base_u[i]).length<1e-9 for i,v in enumerate(upper.data.vertices))
pivot.rotation_euler.y=0;bpy.context.view_layer.update()
# Bilateral transverse dimensions, measured on source vertices with real transforms.
source_dims={}
for name in ['tongue','upper_lip','lower_lip','soft_palate','lower_jaw','upper_teeth']:
 o=bpy.data.objects[name];p=[o.matrix_world@v.co for v in o.data.vertices]
 source_dims[name]=[round((max(v[a] for v in p)-min(v[a] for v in p))*1000,2) for a in range(3)]
assert 54<source_dims['tongue'][1]<62
assert 50<source_dims['upper_lip'][1]<55
assert 105<source_dims['lower_jaw'][1]<125
checks={'all_source_meshes_closed':True,'all_source_meshes_no_zero_area_faces':True,'deformer_group_weights_normalized':True,'no_armature_or_animation':True,'jaw_reference_test_rotation_deg':-12,'lower_incisor_mean_inferior_displacement_mm':round(opening_mm,2),'upper_arch_stationary_during_jaw_test':True,'source_bilateral_dimensions_mm_XYZ':source_dims,'motion_limits':'Reference jaw transform verified only; no soft tissue deformation, collision, phoneme or clinical simulation validated.'}
with open(O+'/validation.json','w') as f:json.dump(checks,f,indent=2)
print('SOURCE_AND_JAW_VALIDATION_OK',json.dumps(checks))
# GLB must reopen, contain textured materials and have a plausible physical scale.
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=O+'/vocal_tract.glb')
meshes=[o for o in bpy.data.objects if o.type=='MESH' and len(o.data.vertices)]
pts=[o.matrix_world@v.co for o in meshes for v in o.data.vertices]
height=max(p.z for p in pts)-min(p.z for p in pts)
assert .265<height<.285,height
assert len(meshes)>60,len(meshes)
assert len(bpy.data.images)>=10,len(bpy.data.images)
print('GLB_ROUNDTRIP_OK',len(meshes),'meshes',len(bpy.data.images),'images','height_m',height)
checks['glb_reimport_meshes']=len(meshes);checks['glb_height_m']=round(height,5);checks['glb_embedded_images']=len(bpy.data.images)
with open(O+'/validation.json','w') as f:json.dump(checks,f,indent=2)
