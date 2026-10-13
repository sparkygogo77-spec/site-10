"""Blender edit (J, 2026-10-13): "I don't like the way the colours go onto my lantern, it needs to be smooth and
massively like the centre of the crimson diamond". The battery's stone faces drop the tiled gem pattern and take
the crimson diamond's centre colour (sRGB 188, 30, 47) as one smooth glossy surface; a very soft large-scale
variation keeps it from looking flat, shadowed parts a shade deeper. Glow parts unchanged."""
import bpy
bpy.ops.wm.open_mainfile(filepath="/mnt/user-data/outputs/rage_battery_c.blend")
CRIMSON = (188 / 255) ** 2.2, (30 / 255) ** 2.2, (47 / 255) ** 2.2
for k, dark in ((0, 0.5), (1, 1.0), (3, 1.25)):
    m = bpy.data.materials.get(f"battery2 kind {k}")
    nt = m.node_tree; N, L = nt.nodes, nt.links
    p = N.get("Principled BSDF")
    for n in [n for n in N if n.type in ("TEX_IMAGE", "MIX_RGB", "MIX", "MAPPING", "TEX_COORD", "BRIGHTCONTRAST", "ATTRIBUTE", "TEX_NOISE", "VALTORGB")]:
        N.remove(n)
    tc = N.new("ShaderNodeTexCoord")
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 0.08; nz.inputs["Detail"].default_value = 1.0
    L.new(tc.outputs["Object"], nz.inputs["Vector"])
    rp = N.new("ShaderNodeValToRGB")
    c = [x * dark for x in CRIMSON]
    rp.color_ramp.elements[0].position = 0.3; rp.color_ramp.elements[0].color = (c[0] * 0.85, c[1] * 0.8, c[2] * 0.85, 1)
    rp.color_ramp.elements[1].position = 0.7; rp.color_ramp.elements[1].color = (min(1, c[0] * 1.1), c[1] * 1.1, c[2] * 1.1, 1)
    L.new(nz.outputs["Fac"], rp.inputs["Fac"]); L.new(rp.outputs["Color"], p.inputs["Base Color"])
    p.inputs["Roughness"].default_value = 0.12
    p.inputs["Specular IOR Level"].default_value = 0.8
    p.inputs["Coat Weight"].default_value = 0.6; p.inputs["Coat Roughness"].default_value = 0.05
bpy.ops.wm.save_as_mainfile(filepath="/mnt/user-data/outputs/rage_battery_c.blend", compress=True)
import os
if os.environ.get("RENDER"):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"; sc.cycles.samples = 16; sc.render.resolution_x = 640; sc.render.resolution_y = 360
    for f in range(1, 31):
        sc.frame_set(f)
    sc.camera = bpy.data.objects["Cam diamond"]; sc.render.filepath = os.environ["S"] + "/smooth.png"; bpy.ops.render.render(write_still=True)
