# Pass 77: the next lanterns, isolated, and a nicer Blast Drill (J: "I need the Torus lantern isolated and worked
# on next, red lantern, yellow lantern, nebula lantern", "Blue lantern maybe one last look and perfect on it",
# "I would also like a nicer drill model").
#   Lantern row: Torus (first, the next to work on), Red, Yellow, Nebula, Blue - the game's own models as they
#   are now, each on its own plinth with its own camera, turning slowly, glow cubes lit like the game.
#   Drill row: today's Blast Drill, then three new ones (tools/pixel_blast_drill.py), spinning:
#     D1 auger (two-start helical flute, glowing cutting edges, light up the core)
#     D2 tiered (crowns of teeth, smaller toward the tip, a ring of light between each)
#     D3 crystal (faceted hex spike, spiral grooves full of light, shards round its base)
# Builds LanternLive\lanterns_and_drill.blend, plays it, keeps the watcher on. Stills to renders/77_*.png.
import os, math
import bpy, bmesh
import numpy as np
from mathutils import Vector

R = math.radians
SRC = os.path.join(FOLDER, "lanterns_drill")
OUT = os.path.join(FOLDER, "lanterns_and_drill.blend")
if bpy.data.filepath:
    bpy.ops.wm.save_mainfile()
old = bpy.data.scenes.get("Lanterns and Drill")
if old:
    bpy.data.scenes.remove(old)
scene = bpy.data.scenes.new("Lanterns and Drill")
col = scene.collection
scene.render.fps = 24
scene.frame_start, scene.frame_end = 1, 240
win = bpy.context.window
if win:
    win.scene = scene


def link(o):
    for c in list(o.users_collection):
        c.objects.unlink(o)
    col.objects.link(o)
    return o


def label(text, at, size=0.22):
    cu = bpy.data.curves.new("lab " + text, "FONT"); cu.body = text; cu.size = size; cu.align_x = "CENTER"
    o = bpy.data.objects.new("Label " + text, cu); o.location = at; o.rotation_euler = (R(90), 0, 0)
    m = bpy.data.materials.new("lab " + text); m.use_nodes = True
    p = m.node_tree.nodes.get("Principled BSDF")
    p.inputs["Emission Color"].default_value = (0.9, 1, 0.92, 1); p.inputs["Emission Strength"].default_value = 2.0
    cu.materials.append(m)
    col.objects.link(o)


def spin(holder, frames, turns=1.0):
    holder.rotation_euler = (0, 0, 0); holder.keyframe_insert("rotation_euler", index=2, frame=1)
    holder.rotation_euler = (0, 0, 2 * math.pi * turns); holder.keyframe_insert("rotation_euler", index=2, frame=frames + 1)
    try:
        for fc in holder.animation_data.action.fcurves:
            for k in fc.keyframe_points:
                k.interpolation = "LINEAR"
            fc.modifiers.new("CYCLES")
    except Exception:
        pass


def plinth(at):
    me = bpy.data.meshes.new("plinth")
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=32, radius1=0.75, radius2=0.75, depth=0.12); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new("Plinth", me); o.location = at + Vector((0, 0, -0.06)); col.objects.link(o)
    m = bpy.data.materials.get("plinth") or bpy.data.materials.new("plinth"); m.use_nodes = True
    m.node_tree.nodes.get("Principled BSDF").inputs["Base Color"].default_value = (0.05, 0.055, 0.06, 1)
    me.materials.append(m)


def camera(name, target, dist, height, lens=50):
    cd = bpy.data.cameras.new(name); cd.lens = lens
    c = bpy.data.objects.new(name, cd); col.objects.link(c)
    c.location = target + Vector((0, -dist, height))
    c.rotation_euler = (target - c.location).to_track_quat("-Z", "Y").to_euler()
    return c


def light_glb(path, name, at, glow=4.0):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    holder = bpy.data.objects.new(name, None); col.objects.link(holder)
    for o in new:
        link(o)
        if o.parent is None:
            o.parent = holder
        if o.type == "MESH":
            for m in o.data.materials:
                if not m or not m.use_nodes:
                    continue
                for n in m.node_tree.nodes:
                    if n.type == "TEX_IMAGE":
                        n.interpolation = "Closest"
                if "_glow" in m.name:
                    bsdf = next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
                    tex = next((n for n in m.node_tree.nodes if n.type == "TEX_IMAGE"), None)
                    if bsdf and tex:
                        m.node_tree.links.new(tex.outputs["Color"], bsdf.inputs["Emission Color"])
                        bsdf.inputs["Emission Strength"].default_value = glow
    holder.location = at
    return holder


cams = {}
# ---- the lanterns ------------------------------------------------------------------------------------------
LANTERNS = [("torus_lantern", "TORUS  (next to work on)"), ("red_lantern", "RED"), ("yellow_lantern", "YELLOW"),
            ("nebula_lantern", "NEBULA"), ("blue_lantern", "BLUE  (one last look)")]
for i, (key, title) in enumerate(LANTERNS):
    at = Vector((i * 3.0, 0, 0))
    plinth(at)
    h = light_glb(os.path.join(SRC, key + ".glb"), "Lantern " + key, at)
    spin(h, 240)
    label(title, at + Vector((0, 0, 1.9)))
    cams[key] = camera("Cam " + key.split("_")[0], at + Vector((0, 0, 0.7)), 3.6, 0.6)
    li = bpy.data.lights.new("glow " + key, "POINT"); li.energy = 25; li.shadow_soft_size = 0.3
    li.color = {"red_lantern": (1, 0.25, 0.2), "yellow_lantern": (1, 0.85, 0.3), "blue_lantern": (0.35, 0.6, 1),
                "nebula_lantern": (0.4, 1, 0.5), "torus_lantern": (0.4, 1, 0.5)}[key]
    lo = bpy.data.objects.new("Glow light " + key, li); lo.location = at + Vector((0, -0.2, 0.7)); col.objects.link(lo)

# ---- the drills --------------------------------------------------------------------------------------------
def drill_material(name, kind):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    p = N.get("Principled BSDF")
    a = N.new("ShaderNodeAttribute"); a.attribute_name = "col"
    L.new(a.outputs["Color"], p.inputs["Base Color"])
    p.inputs["Roughness"].default_value = 0.25
    if kind in (4, 6):
        L.new(a.outputs["Color"], p.inputs["Emission Color"])
        p.inputs["Emission Strength"].default_value = 1.4 if kind == 4 else 6.0
        p.inputs["Coat Weight"].default_value = 0.6
    return m


DMATS = {k: drill_material(f"drill kind {k}", k) for k in (0, 1, 4, 6)}
y_d = -4.5
h = light_glb(os.path.join(SRC, "blast_drill.glb"), "Drill today", Vector((0, y_d, 0)), glow=3.0)
spin(h, 48, 1.0)
plinth(Vector((0, y_d, 0)))
label("TODAY'S DRILL", Vector((0, y_d, 2.9)))
for i, (v, title) in enumerate((("d1", "D1  auger"), ("d2", "D2  tiered"), ("d3", "D3  crystal"))):
    at = Vector(((i + 1) * 3.0, y_d, 0))
    d = np.load(os.path.join(SRC, f"drill_{v}.npz"))
    verts = d["quads"].reshape(-1, 3)
    me = bpy.data.meshes.new(f"drill {v}")
    me.from_pydata(verts.tolist(), [], np.arange(len(verts)).reshape(-1, 4).tolist())
    lin = (np.asarray(d["col"], np.float32) / 255.0) ** 2.2
    ca = me.color_attributes.new("col", "FLOAT_COLOR", "CORNER")
    ca.data.foreach_set("color", np.hstack([np.repeat(lin, 4, axis=0), np.ones((len(verts), 1))]).ravel())
    for k in range(7):
        me.materials.append(DMATS.get(k, DMATS[1]))
    me.polygons.foreach_set("material_index", np.asarray(d["kind"], np.int32))
    o = bpy.data.objects.new(f"Drill {v}", me); col.objects.link(o)
    o.scale = (1 / 16,) * 3
    holder = bpy.data.objects.new(f"Drill holder {v}", None); col.objects.link(holder)
    holder.location = at; o.parent = holder
    spin(holder, 48, 1.0)
    plinth(at)
    label(title, at + Vector((0, 0, 2.9)))
cams["drills"] = camera("Cam drills", Vector((4.5, y_d, 1.2)), 11.0, 1.0)

# ---- room, glow, cameras -------------------------------------------------------------------------------------
world = bpy.data.worlds.new("Lineup World"); world.use_nodes = True
bg = world.node_tree.nodes.get("Background"); bg.inputs[0].default_value = (0.02, 0.024, 0.03, 1)
scene.world = world
fl = bpy.data.meshes.new("lineup floor")
bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=20); bm.to_mesh(fl); bm.free()
fo = bpy.data.objects.new("Lineup floor", fl); fo.location = (6, -2, -0.12); col.objects.link(fo)
fm = bpy.data.materials.new("lineup floor"); fm.use_nodes = True
fm.node_tree.nodes.get("Principled BSDF").inputs["Base Color"].default_value = (0.04, 0.045, 0.05, 1)
fl.materials.append(fm)
key = bpy.data.lights.new("lineup key", "AREA"); key.energy = 300; key.size = 6
ko = bpy.data.objects.new("lineup key", key); ko.location = (6, -9, 6); ko.rotation_euler = (R(50), 0, 0); col.objects.link(ko)
cams["all"] = camera("Cam all lanterns", Vector((6.0, 0, 0.8)), 15.0, 1.5)
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x, scene.render.resolution_y = 1600, 900
try:
    scene.view_settings.view_transform = "Standard"
except Exception:
    pass
try:
    tree = bpy.data.node_groups.new("Lineup Glow", "CompositorNodeTree")
    tree.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    rl = tree.nodes.new("CompositorNodeRLayers"); go = tree.nodes.new("NodeGroupOutput")
    gl = tree.nodes.new("CompositorNodeGlare")
    if "Type" in gl.inputs:
        gl.inputs["Type"].default_value = "Bloom"
    for nm, val in (("Size", 0.6), ("Strength", 0.4), ("Threshold", 1.0)):
        if nm in gl.inputs:
            gl.inputs[nm].default_value = val
    tree.links.new(rl.outputs["Image"], gl.inputs["Image"]); tree.links.new(gl.outputs["Image"], go.inputs[0])
    scene.compositing_node_group = tree
except Exception as e:
    print("no glow:", e)
rdir = os.path.join(FOLDER, "renders"); os.makedirs(rdir, exist_ok=True)
if not os.environ.get("LL_NO_RENDER"):
    for k in ("all", "drills", "torus_lantern"):
        scene.camera = cams[k]; scene.frame_set(1)
        scene.render.filepath = os.path.join(rdir, f"77_{k}.png")
        bpy.ops.render.render(write_still=True, scene=scene.name)
scene.camera = cams["torus_lantern"]
scene.frame_set(1)

for sc in list(bpy.data.scenes):
    if sc != scene:
        bpy.data.scenes.remove(sc)
try:
    bpy.ops.outliner.orphans_purge(do_recursive=True)
except Exception:
    pass
bpy.ops.wm.save_as_mainfile(filepath=OUT)
for w in bpy.context.window_manager.windows:
    for a in w.screen.areas:
        if a.type == "VIEW_3D":
            for sp in a.spaces:
                if sp.type == "VIEW_3D":
                    sp.region_3d.view_perspective = "CAMERA"
                    sp.shading.type = "RENDERED"
            a.tag_redraw()


def _after():
    try:
        for ob in bpy.context.scene.objects:
            if ob.type in {"MESH", "EMPTY"} and ob.name.startswith("Lantern") is False and ob.name in ("Lantern", "lantern"):
                ob.hide_viewport = True; ob.hide_render = True
        for ob in bpy.context.scene.objects:
            if ob.type == "MESH" and ob.name.lower().startswith("lantern model"):
                ob.hide_viewport = True; ob.hide_render = True
        sc = bpy.context.scene
        if hasattr(sc, "lantern_live_watch") and not sc.lantern_live_watch:
            sc.lantern_live_watch = True
        for w in bpy.context.window_manager.windows:
            for a in w.screen.areas:
                if a.type == "VIEW_3D":
                    with bpy.context.temp_override(window=w, area=a):
                        if not bpy.context.screen.is_animation_playing:
                            bpy.ops.screen.animation_play()
                    return None
    except Exception as e:
        print("after:", e)
    return None


bpy.app.timers.register(_after, first_interval=4.0)
print("saved", OUT)
