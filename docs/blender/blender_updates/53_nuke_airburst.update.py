# Pass 53: the Fear Nuke's airburst (J: it never reaches the ground; a crater at least 4x larger; it
# incinerates but deals no damage). Over a field of blocks: the bomb hangs 12 blocks up, then a flash,
# a fireball, a shock ring racing out along the ground, a rising stem and a yellow mushroom cap, while
# the blocks in a 10-block radius flare yellow and burn away into a crater. 80 frames.
# Stills renders/airburst_f*.png.
import os, math, random
import bpy
import numpy as np
from mathutils import Vector

scene = bpy.context.scene
C = Vector((-130.0, 54.0, 0.0))
H = 12.0
CRATER = 10.0
for o in list(bpy.data.objects):
    if o.name.startswith("Airburst"):
        bpy.data.objects.remove(o, do_unlink=True)


def emit_mat(name, colour, strength, alpha=1.0, noise=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    N.clear()
    out = N.new("ShaderNodeOutputMaterial")
    em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = colour
    st = N.new("ShaderNodeValue"); st.outputs[0].default_value = strength
    if noise:
        tc = N.new("ShaderNodeTexCoord")
        nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = noise; nz.inputs["Detail"].default_value = 6
        L.new(tc.outputs["Object"], nz.inputs["Vector"])
        ramp = N.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].position = 0.35; ramp.color_ramp.elements[0].color = (0.05, 0.02, 0.0, 1)
        ramp.color_ramp.elements[1].position = 0.75; ramp.color_ramp.elements[1].color = colour
        L.new(nz.outputs["Fac"], ramp.inputs["Fac"])
        L.new(ramp.outputs["Color"], em.inputs["Color"])
    em.inputs["Strength"].default_value = strength
    if alpha < 1.0:
        tr = N.new("ShaderNodeBsdfTransparent")
        mix = N.new("ShaderNodeMixShader"); mix.inputs["Fac"].default_value = alpha
        L.new(tr.outputs[0], mix.inputs[1]); L.new(em.outputs[0], mix.inputs[2])
        L.new(mix.outputs[0], out.inputs["Surface"])
        m.surface_render_method = "BLENDED"
    else:
        L.new(em.outputs[0], out.inputs["Surface"])
    return m, em


def sphere(name, at, r, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=at, segments=32, ring_count=16)
    o = bpy.context.active_object; o.name = name
    o.data.materials.append(mat)
    return o


def key_scale(o, frames):
    for f, s in frames:
        o.scale = s if isinstance(s, tuple) else (s, s, s)
        o.keyframe_insert("scale", frame=f)


# The ground: a field of grass-and-dirt blocks, one shared mesh.
bpy.ops.mesh.primitive_cube_add(size=1)
block = bpy.context.active_object; block.name = "Airburst block proto"
gm = bpy.data.materials.new("airburst_grass")
gm.use_nodes = True
b = gm.node_tree.nodes.get("Principled BSDF"); b.inputs["Base Color"].default_value = (0.18, 0.34, 0.12, 1)
b.inputs["Emission Color"].default_value = (1.0, 0.7, 0.1, 1)
block.data.materials.append(gm)
bm_ = block.data
block.hide_render = True; block.hide_viewport = True
rnd = random.Random(3)
burning = bpy.data.materials.new("airburst_burning")
burning.use_nodes = True
bb = burning.node_tree.nodes.get("Principled BSDF")
bb.inputs["Base Color"].default_value = (0.25, 0.18, 0.05, 1)
bb.inputs["Emission Color"].default_value = (1.0, 0.72, 0.1, 1); bb.inputs["Emission Strength"].default_value = 6.0
R_FIELD = 15
for x in range(-R_FIELD, R_FIELD + 1):
    for y in range(-R_FIELD, R_FIELD + 1):
        d = math.hypot(x, y)
        if d > R_FIELD:
            continue
        depth = 3 if d < CRATER else 1
        for z in range(depth):
            o = bpy.data.objects.new(f"Airburst block {x} {y} {z}", bm_)
            o.location = C + Vector((x, y, -z - 0.5))
            scene.collection.objects.link(o)
            # Inside the crater: deeper towards the middle, the blocks burn away as the shock passes.
            gone = d < CRATER * math.sqrt(max(0.0, 1 - (z / 3.2) ** 2))
            if gone:
                t = 8 + d * 2.2 + rnd.random() * 3
                o.material_slots[0].link = "OBJECT"
                o.material_slots[0].material = burning
                key_scale(o, ((1, 1.0), (t, 1.0), (t + 6, 0.001)))

# The bomb hanging in the air, gone at the flash.
nuke = sphere("Airburst bomb", C + Vector((0, 0, H)), 0.9, emit_mat("airburst_bomb", (1.0, 0.7, 0.12, 1), 3.0)[0])
key_scale(nuke, ((1, 1.0), (4, 1.0), (5, 0.001)))
flash_m, flash_e = emit_mat("airburst_flash", (1.0, 0.97, 0.8, 1), 60.0)
flash = sphere("Airburst flash", C + Vector((0, 0, H)), 1.0, flash_m)
key_scale(flash, ((4, 0.001), (5, 3.0), (8, 9.0), (12, 0.001)))
fire_m, _ = emit_mat("airburst_fire", (1.0, 0.6, 0.08, 1), 12.0, noise=4.0)
fire = sphere("Airburst fireball", C + Vector((0, 0, H)), 1.0, fire_m)
key_scale(fire, ((5, 0.001), (10, 5.0), (24, 7.5), (40, 6.0), (55, 0.001)))
for f, z in ((5, H), (40, H + 6), (80, H + 14)):
    fire.location = C + Vector((0, 0, z)); fire.keyframe_insert("location", frame=f)
# The shock ring along the ground.
bpy.ops.mesh.primitive_torus_add(major_radius=1.0, minor_radius=0.08, location=C + Vector((0, 0, 0.3)))
ring = bpy.context.active_object; ring.name = "Airburst shock ring"
ring.data.materials.append(emit_mat("airburst_ring", (1.0, 0.85, 0.4, 1), 20.0, alpha=0.8)[0])
key_scale(ring, ((7, (0.5, 0.5, 1)), (30, (CRATER * 2.2, CRATER * 2.2, 3)), (36, (CRATER * 2.5, CRATER * 2.5, 0.001))))
# The stem and the mushroom cap of yellow smoke.
smoke_m, _ = emit_mat("airburst_smoke", (0.9, 0.62, 0.08, 1), 2.5, alpha=0.85, noise=2.5)
bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=1.0, location=C + Vector((0, 0, H / 2)))
stem = bpy.context.active_object; stem.name = "Airburst stem"; stem.data.materials.append(smoke_m)
key_scale(stem, ((14, (0.001, 0.001, 0.001)), (30, (1.8, 1.8, H)), (80, (2.6, 2.6, H + 12))))
for f, z in ((14, H / 2), (30, H / 2), (80, (H + 12) / 2)):
    stem.location = C + Vector((0, 0, z)); stem.keyframe_insert("location", frame=f)
cap = sphere("Airburst cap", C + Vector((0, 0, H + 4)), 1.0, smoke_m)
key_scale(cap, ((20, 0.001), (40, (7, 7, 3.2)), (80, (11, 11, 4.5))))
for f, z in ((20, H + 2), (40, H + 7), (80, H + 15)):
    cap.location = C + Vector((0, 0, z)); cap.keyframe_insert("location", frame=f)
lamp = bpy.data.lights.new("Airburst light", "POINT"); lamp.color = (1.0, 0.8, 0.3)
lo = bpy.data.objects.new("Airburst light", lamp); lo.location = C + Vector((0, 0, H))
scene.collection.objects.link(lo)
for f, e in ((4, 0), (5, 200000), (12, 60000), (30, 15000), (80, 3000)):
    lamp.energy = e; lamp.keyframe_insert("energy", frame=f)

cd = bpy.data.cameras.new("Airburst Camera"); cd.lens = 24
cam = bpy.data.objects.new("Airburst Camera", cd)
scene.collection.objects.link(cam)
cam.location = C + Vector((30, -26, 9))
cam.rotation_euler = (C + Vector((0, 0, 9)) - cam.location).to_track_quat("-Z", "Y").to_euler()
out_dir = os.path.join(FOLDER, "renders")
keep = (scene.frame_current, scene.render.filepath, scene.render.resolution_percentage, scene.camera)
scene.camera = cam
scene.render.resolution_percentage = 60
for f in (3, 6, 14, 26, 44, 80):
    scene.frame_set(f)
    scene.render.filepath = os.path.join(out_dir, f"airburst_f{f:02d}.png")
    bpy.ops.render.render(write_still=True)
scene.frame_set(keep[0])
scene.render.filepath, scene.render.resolution_percentage, scene.camera = keep[1], keep[2], keep[3]
