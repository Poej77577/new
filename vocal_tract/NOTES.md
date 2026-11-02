# Vocal tract v2 — detailed adult-scale anatomical base

## ما تغير

أعيد بناء النموذج بأبعاد اسمية لرأس بالغ، ومجسمات أصلية كاملة على جانبي خط المنتصف، مع عرض سهمي غير هدّام. أضيفت تفاصيل تيجان الأسنان وجذورها واللثة والعظم السنخي، وثنيات الحنك، وأخدود اللسان وحليماته الخلفية، والمحارات الأنفية، ولسان المزمار والطيات الحنجرية والمريء والقصبة الهوائية وحلقاتها الغضروفية والعظم اللامي وأجسام الفقرات العنقية.

77 anatomical source meshes; 73 nonempty meshes in the cutaway GLB. Anatomy is separated into supporting tissue, skeleton/dentition, articulators, airway, and detail collections. Empty reference pivots and hidden Boolean cutters occupy their own collections. No armature, animation, educational labels or UI.

## Dimensions and coordinate system

Model coordinates are stored in **meters**, with Blender displaying millimeters. Scale length = 1, so a 0.08 m tongue remains 80 mm in Blender and GLB. X points posteriorly, Y laterally, Z superiorly. The presentation retains Y >= approximately 0. Full source dimensions, before the sagittal display modifier:

| Source part | X extent | Full Y width | Z extent |
| --- | ---: | ---: | ---: |
| Tongue | 80.13 mm | 58.11 mm | 63.85 mm |
| Upper lip | 24.04 mm | 52.00 mm | 11.35 mm |
| Lower lip | 24.04 mm | 52.00 mm | 13.30 mm |
| Soft palate | 23.89 mm | 44.00 mm | 29.20 mm |
| Mandible | 109.50 mm | 117.89 mm | 74.52 mm |
| Upper dental crowns, complete arch | 62.34 mm | 63.22 mm | 11.44 mm |

The displayed head/neck region is 273.19 mm high. These are axis-aligned bounds; tongue X extent is not a centerline arc length. Nominal adult proportions were selected; no patient image or measurements were supplied.

## Future articulation

- `tongue`, `upper_lip`, `lower_lip`, `soft_palate`, `epiglottis`, labial supports, floor muscles, jaws, dental crowns, roots and gingiva remain separate.
- Native source meshes are complete bilateral volumes. **Disable each object's final `Sagittal display` Boolean to see its full geometry.** The cutaway GLB is the evaluated presentation mesh; use the Blender file for rigging.
- Source topology is 99.65% quads by face count, with small terminal n-gons and larger planar supporting-tissue caps. Tongue, lip and velum sources have longitudinal/transverse deformation loops; supporting tissues prioritize readable cutaway anatomy.
- Tongue groups: `tongue_tip`, `tongue_blade`, `tongue_body`, `tongue_root`. Lip groups: `lip_center`, `lip_commissure`. Velum groups: `velum_attachment`, `velum_free_edge`. Weights are normalized semantic masks, **not an armature skinning solution**.
- `jaw_rotation_reference` is centered at (35, 0, 25) mm. TMJ markers sit at (35, ±52, 25) mm. The mandible, lower dentition/roots/gingiva, lower alveolar bone and lower labial components follow this reference empty. A real jaw rig still needs bilateral joint constraints and condylar translation.
- Add future armature/deformation modifiers **before** the last sagittal Boolean. Deform the full source and then evaluate its cut plane. Do not bind a rig to the triangulated GLB cut caps.
- A temporary -12° Y rotation of the jaw reference moved the lower incisors inferiorly by 18.25 mm and left the upper arch stationary. The asset was not saved in this test pose. Tongue/lip deformation, contact, phoneme motion, swallowing and physiological motion ranges have not been validated.

## Materials, views and limitations

Twelve packed color texture maps, different tissue/bone/enamel materials, and subtle surface bump are included in the Blender file. The GLB embeds all twelve color maps and PBR base materials; Blender-specific subsurface/bump shading may differ between viewers. The `textures/` folder contains the external source maps as well.

`side_view.png`, `perspective_view.png` and `front_angled_view.png` use Blender's studio viewport renderer. `anatomy_detail.png` and `articulators_detail.png` use Cycles with tissue shaders and lighting.

This is a detailed **synthetic anatomical base**, not a scan or a medically validated reconstruction. The nasal septum and lateral cheek are omitted from the cutaway so the nasal conchae and dental arches remain visible. Bone roots, muscles and support volumes have intentional tissue-interface overlaps; this is an articulated collection, not a fused anatomical union. Cut planes differ by at most 1.05 mm to prevent coincident interface faces. Local retopology and collision tuning may be needed for extreme deformations.

## Checks and rebuild

All 77 source meshes passed closed-manifold and zero-area-face checks. Core deformer masks sum to one. The GLB was re-imported successfully: 73 nonempty meshes, 12 embedded images, height 0.27319 m. Full measurements and results are in `mesh_report.json` and `validation.json`.

    blender -b --threads 8 --python build_vocal_tract.py -- --output /path/to/output --beauty
    blender -b --threads 2 --python validate_model.py -- /path/to/output

Use Blender 4.3 or newer. `--beauty` adds the two Cycles views; omit it for faster studio viewport captures.
