# Pass 10: translucent jade. The textures now carry how see-through each pixel is: the stone itself
# lets light through (cloudier in patches), while the cracks, sparks, flecks and the outline are solid.
# Through a face you see into the block and out the far side, so cracks on the back faces show
# behind the front ones, at depth. Inside, a faint green glow fills the stone, thicker where the
# construct is deeper, the way light hangs inside real jade.
import os
import bpy

for img in bpy.data.images:
    if img.name.startswith("jade_"):
        img.filepath = os.path.join(FOLDER, img.name)
        img.alpha_mode = "STRAIGHT"
        img.reload()

for mat in bpy.data.materials:
    if not mat.name.startswith("jade_"):
        continue
    nt = mat.node_tree
    N, L = nt.nodes, nt.links
    tex = next(n for n in N if n.type == "TEX_IMAGE")
    bsdf = next(n for n in N if n.type == "BSDF_PRINCIPLED")
    out = next(n for n in N if n.type == "OUTPUT_MATERIAL")
    for l in list(bsdf.inputs["Alpha"].links):
        L.remove(l)
    L.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
    bsdf.inputs["Roughness"].default_value = 0.08
    # the inside: green light caught in the stone
    vol = next((n for n in N if n.type == "PRINCIPLED_VOLUME"), None) or N.new("ShaderNodeVolumePrincipled")
    vol.inputs["Color"].default_value = (0.35, 1.0, 0.5, 1)
    vol.inputs["Density"].default_value = 1.1
    vol.inputs["Absorption Color"].default_value = (0.85, 0.12, 0.6, 1)   # soaks up red and blue: green
    vol.inputs["Emission Color"].default_value = (0.2, 1.0, 0.4, 1)
    vol.inputs["Emission Strength"].default_value = 0.35
    if not out.inputs["Volume"].links:
        L.new(vol.outputs[0], out.inputs["Volume"])
    mat.use_backface_culling = False
    for attr, val in (("surface_render_method", "DITHERED"), ("use_transparency_overlap", True),
                      ("use_raytrace_refraction", False), ("blend_method", "HASHED")):
        try:
            setattr(mat, attr, val)
        except Exception:
            pass

if bpy.data.filepath:
    try:
        bpy.ops.wm.save_mainfile()
    except Exception:
        pass
