# Vocal tract — editable sagittal anatomical base

Files: vocal_tract.blend, vocal_tract.glb, build_vocal_tract.py, three PNG viewport-style captures, mesh_report.json.

18 separate anatomical mesh objects, organized in collections:
- Articulators: tongue, upper_lip, lower_lip, soft_palate, epiglottis.
- Support: upper_jaw, lower_jaw, hard_palate, cranio_cervical_tissue, submandibular_tissue.
- Dentition: upper_teeth and lower_teeth, each containing eight disconnected crown islands.
- Airway boundaries: nasal_cavity (roof/passage lining), inferior_nasal_concha, middle_nasal_concha, oral_cavity_boundary, pharynx, laryngeal_inlet.

The nasal, oral and pharyngeal air spaces remain empty. Cavity objects represent tissue boundaries rather than solid air volumes. Retained left half: X posterior, Y lateral, Z superior. Native scale: one Blender unit = 10 mm. The GLB exports in meters. Structures have substantial transverse volume, up to 27 mm for the retained half; this is an open sagittal half model, not a complete bilateral head.

Future rigging: the articulators have longitudinal quad loops and quad medial closures. Tongue, lips, velum and jaws are independently editable. Small terminal n-gons remain on swept meshes; supporting tissues use planar n-gon cut/lateral caps. Teeth are disconnected crowns grouped per arch. All 18 meshes passed boundary-edge, nonmanifold-edge and zero-area-face checks. No armature, weights, animation, labels or UI are present. Rigging still requires anatomical joint placement, weights, deformation testing and possible local topology refinement; readiness for a particular motion range has not been tested.

The three PNGs use Blender's Workbench viewport rendering engine, with material colors and studio shading, from sagittal, slight perspective and anterior angled views. No image-based model or textures are used.

No reference image accompanied the uploaded instructions. This is a simplified anatomical base with nominal proportions, not a reference-matched or medically validated reconstruction. Supporting tissue interfaces intentionally overlap slightly; this is a collection of closed parts, not a single watertight union. Medial offsets of at most 0.8 mm avoid coplanar display artifacts. Jaw movement and airway simulation require further validation.

Rebuild with Blender 4.3+:

    blender -b --python build_vocal_tract.py -- --output /path/to/output
