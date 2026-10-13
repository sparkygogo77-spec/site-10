# Pass 41, one batch (J: optimise the time in Blender):
#  1. Reference blocks: a diamond block and a crying obsidian block (the game's own textures, nearest-pixel).
#  2. Every Minecraft model in the mod (models_glb/*.glb from tools/bbmodel_to_glb.py) in a labelled grid,
#     true size next to the reference blocks, glow cubes lit like the game.
#  3. The fear parasite, three versions (fear_parasite_<v>.npz), undulating with a snapping maw.
# Renders: renders/lineup_all.png, lineup_a.png, lineup_b.png, parasite_f*.png, parasite_maw.png.
import os, math
import bpy
import numpy as np
from mathutils import Vector

scene = bpy.context.scene
R = math.radians
out_dir = os.path.join(FOLDER, "renders")
GRID = Vector((0.0, 80.0, 0.0))
COLS, STEP = 7, 3.5

for o in list(bpy.data.objects):
    if o.name.startswith(("Lineup", "Ref ", "Parasite")):
        bpy.data.objects.remove(o, do_unlink=True)


def closest(mat):
    if not mat or not mat.use_nodes:
        return
    for n in mat.node_tree.nodes:
        if n.type == "TEX_IMAGE":
            n.interpolation = "Closest"


def emit_from_texture(mat, strength):
    N, L = mat.node_tree.nodes, mat.node_tree.links
    bsdf = next((n for n in N if n.type == "BSDF_PRINCIPLED"), None)
    tex = next((n for n in N if n.type == "TEX_IMAGE"), None)
    if bsdf and tex:
        L.new(tex.outputs["Color"], bsdf.inputs["Emission Color"])
        bsdf.inputs["Emission Strength"].default_value = strength


def label(text, at):
    cu = bpy.data.curves.new(f"Lineup label {text}", "FONT")
    cu.body = text; cu.size = 0.32; cu.align_x = "CENTER"
    o = bpy.data.objects.new(f"Lineup label {text}", cu)
    o.location = at
    m = bpy.data.materials.get("lineup_label") or bpy.data.materials.new("lineup_label")
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Emission Color"].default_value = (1, 1, 1, 1); b.inputs["Emission Strength"].default_value = 2.0
    cu.materials.append(m)
    scene.collection.objects.link(o)


# 1. Reference blocks.
def ref_block(name, png, at, emit=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=at + Vector((0, 0, 0.5)))
    o = bpy.context.active_object
    o.name = f"Ref {name}"
    m = bpy.data.materials.new(f"ref_{name}")
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    b = N.get("Principled BSDF")
    t = N.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(os.path.join(FOLDER, "ref", png), check_existing=True)
    t.interpolation = "Closest"
    L.new(t.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.35
    if emit:
        L.new(t.outputs["Color"], b.inputs["Emission Color"]); b.inputs["Emission Strength"].default_value = emit
    o.data.materials.append(m)
    # Every face shows the whole texture, like the game's cube_all.
    uv = o.data.uv_layers.active.data
    for poly in o.data.polygons:
        for li, (u, v) in zip(poly.loop_indices, ((0, 0), (1, 0), (1, 1), (0, 1))):
            uv[li].uv = (u, v)
    label(name.replace("_", " "), at + Vector((0, -0.9, 0.01)))


ref_block("diamond_block", "diamond_block.png", GRID + Vector((-STEP, 0, 0)))
ref_block("crying_obsidian", "crying_obsidian.png", GRID + Vector((-STEP, -STEP, 0)), emit=0.6)

# 2. The mod's models.
glb_dir = os.path.join(FOLDER, "models_glb")
names = sorted(f[:-4] for f in os.listdir(glb_dir) if f.endswith(".glb"))
for k, name in enumerate(names):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(glb_dir, name + ".glb"))
    new = [o for o in bpy.data.objects if o not in before]
    holder = bpy.data.objects.new(f"Lineup {name}", None)
    scene.collection.objects.link(holder)
    for o in new:
        o.name = f"Lineup {name} {o.name}"
        if o.parent is None:
            o.parent = holder
        if o.type == "MESH":
            for m in o.data.materials:
                closest(m)
                if m and "_glow" in m.name:
                    emit_from_texture(m, 4.0)
    slot = GRID + Vector(((k % COLS) * STEP, -(k // COLS) * STEP, 0))
    holder.location = slot
    label(name.replace("_", " "), slot + Vector((0, -1.2, 0.01)))

# 3. The fear parasites.
MATS = [bpy.data.materials.get(n) for n in ("runner_dark", "runner_dark", "runner_dark", "runner_dark",
                                           "runner_amber", "runner_amber", "runner_edge", "runner_eye")]
PBASE = Vector((-30.0, 62.0, 0.0))
FR = 24
for vi, v in enumerate("abc"):
    d = np.load(os.path.join(FOLDER, f"fear_parasite_{v}.npz"))
    pn = [str(n) for n in d["names"]]; par = d["parents"]; piv = d["pivots"]
    root = bpy.data.objects.new(f"Parasite {v}", None)
    root.location = PBASE + Vector(((vi - 1) * 7.0, 0, 0)); root.scale = (1 / 16,) * 3
    scene.collection.objects.link(root)
    E = []
    for n, name in enumerate(pn):
        e = bpy.data.objects.new(f"Parasite {v} pivot {name}", None)
        p = int(par[n])
        e.parent = root if p < 0 else E[p]
        e.location = Vector(piv[n]) - (Vector((0, 0, 0)) if p < 0 else Vector(piv[p]))
        scene.collection.objects.link(e)
        E.append(e)
        q = d[f"q{n}"]
        if not len(q):
            continue
        verts = q.reshape(-1, 3)
        me = bpy.data.meshes.new(f"Parasite {v} {name}")
        me.from_pydata(verts.tolist(), [], np.arange(len(verts)).reshape(-1, 4).tolist())
        lin = (np.asarray(d[f"c{n}"], np.float32) / 255.0) ** 2.2
        a = me.color_attributes.new("col", "FLOAT_COLOR", "CORNER")
        a.data.foreach_set("color", np.hstack([np.repeat(lin, 4, axis=0), np.ones((len(verts), 1))]).ravel())
        for m in MATS:
            me.materials.append(m)
        me.polygons.foreach_set("material_index", np.asarray(d[f"k{n}"], np.int32))
        o = bpy.data.objects.new(f"Parasite {v} {name}", me)
        o.parent = e
        scene.collection.objects.link(o)
    byname = dict(zip(pn, E))
    for f in range(FR + 1):
        p = 2 * math.pi * f / FR
        for i in range(sum(1 for x in pn if x.startswith("seg"))):
            e = byname[f"seg{i}"]
            e.rotation_euler = (R(5 * math.sin(2 * p - 0.5 * i)), 0, R(13 * math.sin(p - 0.55 * i)))
            e.keyframe_insert("rotation_euler", frame=1 + f)
        h = byname["head"]
        h.rotation_euler = (R(4 * math.sin(2 * p)), 0, R(-9 * math.sin(p + 0.4)))
        h.keyframe_insert("rotation_euler", frame=1 + f)
        j = byname["jaw"]
        j.rotation_euler = (R(-(6 + 34 * max(0.0, math.sin(2 * p)) ** 0.6)), 0, 0)
        j.keyframe_insert("rotation_euler", frame=1 + f)
        root.location.z = PBASE.z + 0.15 * math.sin(p)
        root.keyframe_insert("location", index=2, frame=1 + f)
    lamp = bpy.data.lights.new(f"Parasite {v} glow", "POINT")
    lamp.color = (1.0, 0.72, 0.12); lamp.energy = 90
    lo = bpy.data.objects.new(f"Parasite {v} glow", lamp)
    lo.parent = byname["head"]; lo.location = (0, 8, 2)
    scene.collection.objects.link(lo)

# Renders.
sun_d = bpy.data.lights.new("Lineup sun", "SUN"); sun_d.energy = 3.0
sun = bpy.data.objects.new("Lineup sun", sun_d); sun.rotation_euler = (R(50), 0, R(30))
scene.collection.objects.link(sun)
cd = bpy.data.cameras.new("Lineup Camera"); cam = bpy.data.objects.new("Lineup Camera", cd)
scene.collection.objects.link(cam)
keep = (scene.frame_current, scene.render.filepath, scene.render.resolution_percentage, scene.camera)
scene.camera = cam
scene.render.resolution_percentage = 75
rows = (len(names) + COLS - 1) // COLS


def shoot(tag, at, target, lens):
    cd.lens = lens
    cam.location = at
    cam.rotation_euler = (target - at).to_track_quat("-Z", "Y").to_euler()
    scene.render.filepath = os.path.join(out_dir, tag + ".png")
    bpy.ops.render.render(write_still=True)


mid = GRID + Vector(((COLS - 1) * STEP / 2, -(rows - 1) * STEP / 2, 0.5))
shoot("lineup_all", mid + Vector((0, -26, 20)), mid, 30)
top = GRID + Vector(((COLS - 1) * STEP / 2, -STEP * 1, 0.8))
bot = GRID + Vector(((COLS - 1) * STEP / 2, -STEP * 4, 0.8))
shoot("lineup_a", top + Vector((0, -13, 8)), top, 30)
shoot("lineup_b", bot + Vector((0, -13, 8)), bot, 30)
sun.hide_render = True
for f in (4, 10, 16):
    scene.frame_set(f)
    shoot(f"parasite_f{f:02d}", PBASE + Vector((14, 9, 6)), PBASE + Vector((0, -1.5, 1.4)), 35)
scene.frame_set(7)
shoot("parasite_maw", PBASE + Vector((0, 9, 1.8)), PBASE + Vector((0, 0, 1.5)), 40)
scene.frame_set(keep[0])
scene.render.filepath, scene.render.resolution_percentage, scene.camera = keep[1], keep[2], keep[3]
