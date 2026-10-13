# Pass 81: the Red corps power battery, three takes from J's reference sheet, each with its own blood effect
# radiating from it (J: "3 iterations of a blender build of this battery, I want new blood effects radiating
# from it"). Models: tools/pixel_rage_battery.py (original runes and a new claw sigil, no existing emblem).
#   B1 monolith  - weathered stone, molten cracks, glowing runes.   Effect: rings of blood-light pulsing out from
#                  the port on every heartbeat, and embers of blood rising round it.
#   B2 bleeding  - darker stone, blood channels into a brimming basin, drips under the port.   Effect: blood
#                  dripping from the port and running down, the basin and channels throbbing with the beat.
#   B3 engine    - iron bands, opened side panels with glowing ribs, spiked crown.   Effect: on every heartbeat
#                  a burst of blood spray flies out in all directions, with a shockwave flash.
# Everything throbs with one heartbeat (a double beat every 2 s). Builds LanternLive\rage_battery.blend.
# Cameras: Cam B1, Cam B2, Cam B3, Cam all.
import math, os
import bpy, bmesh
import numpy as np
from mathutils import Vector

R = math.radians
SRC = os.path.join(FOLDER, "rage_battery")
OUT = os.path.join(FOLDER, "rage_battery.blend")
if bpy.data.filepath:
    bpy.ops.wm.save_mainfile()
old = bpy.data.scenes.get("Rage Battery")
if old:
    bpy.data.scenes.remove(old)
scene = bpy.data.scenes.new("Rage Battery")
col = scene.collection
scene.render.fps = 24
scene.frame_start, scene.frame_end = 1, 240
win = bpy.context.window
if win:
    win.scene = scene
BEAT = "pow(max(0, sin(frame / 7.64)), 12) + 0.6 * pow(max(0, sin(frame / 7.64 - 0.55)), 12)"   # lub-dub, 2 s


def emissive(name, rgb, strength_expr, base=None, rough=0.4):
    m = bpy.data.materials.new(name); m.use_nodes = True
    p = m.node_tree.nodes.get("Principled BSDF")
    p.inputs["Base Color"].default_value = (base or rgb) + (1,)
    p.inputs["Emission Color"].default_value = rgb + (1,)
    p.inputs["Roughness"].default_value = rough
    d = p.inputs["Emission Strength"].driver_add("default_value").driver
    d.type = "SCRIPTED"; d.expression = strength_expr
    return m


def kind_materials(tag):
    """One material per voxel kind, coloured by the per-face colours; the lit kinds throb with the heartbeat."""
    mats = {}
    for k, (rough, emit) in {0: (0.85, None), 1: (0.75, None), 3: (0.5, None), 4: ("0.25", f"0.5 + 1.2 * ({BEAT})"),
                             5: (0.4, f"1.0 + 2.6 * ({BEAT})"), 6: (0.3, f"2.5 + 5 * ({BEAT})")}.items():
        m = bpy.data.materials.new(f"battery {tag} kind {k}"); m.use_nodes = True
        nt = m.node_tree; p = nt.nodes.get("Principled BSDF")
        a = nt.nodes.new("ShaderNodeAttribute"); a.attribute_name = "col"
        nt.links.new(a.outputs["Color"], p.inputs["Base Color"])
        p.inputs["Roughness"].default_value = float(rough)
        if emit:
            nt.links.new(a.outputs["Color"], p.inputs["Emission Color"])
            d = p.inputs["Emission Strength"].driver_add("default_value").driver
            d.type = "SCRIPTED"; d.expression = emit
            if k == 4:
                p.inputs["Coat Weight"].default_value = 0.8
        mats[k] = m
    return mats


def battery(tag, at):
    d = np.load(os.path.join(SRC, f"battery_{tag.lower()}.npz"))
    verts = d["quads"].reshape(-1, 3)
    me = bpy.data.meshes.new("battery " + tag)
    me.from_pydata(verts.tolist(), [], np.arange(len(verts)).reshape(-1, 4).tolist())
    lin = (np.asarray(d["col"], np.float32) / 255.0) ** 2.2
    ca = me.color_attributes.new("col", "FLOAT_COLOR", "CORNER")
    ca.data.foreach_set("color", np.hstack([np.repeat(lin, 4, axis=0), np.ones((len(verts), 1))]).ravel())
    mats = kind_materials(tag)
    order = [0, 1, 3, 4, 5, 6]
    for k in order:
        me.materials.append(mats[k])
    kind = np.asarray(d["kind"])
    me.polygons.foreach_set("material_index", np.searchsorted(order, kind).astype(np.int32))
    o = bpy.data.objects.new("Battery " + tag, me); col.objects.link(o)
    o.scale = (1 / 16,) * 3; o.location = at
    li = bpy.data.lights.new("battery light " + tag, "POINT"); li.color = (1, 0.12, 0.08); li.shadow_soft_size = 0.4
    dd = li.driver_add("energy").driver; dd.type = "SCRIPTED"; dd.expression = f"20 + 50 * ({BEAT})"
    lo = bpy.data.objects.new("Battery light " + tag, li); lo.location = at + Vector((0, -1.6, 1.5)); col.objects.link(lo)
    return o


PORT = Vector((0, -15.0 / 16, 24.0 / 16))       # the port, in battery space (model px / 16)


def drop_object(name, rgb, size=0.035, glow="0.6"):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=size); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); col.objects.link(o)
    o.location = (0, 0, -50)                     # parked out of sight; the particles instance it
    me.materials.append(emissive(name, rgb, glow, base=tuple(c * 0.6 for c in rgb), rough=0.15))
    return o


def emitter(name, at, size, rot=(0, 0, 0)):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new(); bmesh.ops.create_circle(bm, cap_ends=True, segments=16, radius=size); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); col.objects.link(o)
    o.location = at; o.rotation_euler = rot
    o.show_instancer_for_viewport = True
    return o


def particles(o, name, inst, count, start, end, life, normal_v, rand_v, gravity, size=1.0, size_rand=0.5, emit_from="FACE"):
    mod = o.modifiers.new(name, "PARTICLE_SYSTEM")
    ps = mod.particle_system.settings
    ps.count = count; ps.frame_start = start; ps.frame_end = end; ps.lifetime = life; ps.lifetime_random = 0.4
    ps.emit_from = emit_from
    ps.normal_factor = normal_v; ps.factor_random = rand_v
    ps.effector_weights.gravity = gravity
    ps.render_type = "OBJECT"; ps.instance_object = inst
    ps.particle_size = size; ps.size_random = size_rand
    ps.use_rotations = True; ps.rotation_factor_random = 1.0
    o.show_instancer_for_render = False
    return ps


def plinth(at, r=1.4):
    me = bpy.data.meshes.new("plinth")
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=48, radius1=r, radius2=r, depth=0.14); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new("Plinth", me); o.location = at + Vector((0, 0, -0.07)); col.objects.link(o)
    m = bpy.data.materials.get("plinth") or bpy.data.materials.new("plinth"); m.use_nodes = True
    m.node_tree.nodes.get("Principled BSDF").inputs["Base Color"].default_value = (0.03, 0.025, 0.025, 1)
    me.materials.append(m)


def label(text, at, size=0.3):
    cu = bpy.data.curves.new("lab " + text, "FONT"); cu.body = text; cu.size = size; cu.align_x = "CENTER"
    o = bpy.data.objects.new("Label " + text, cu); o.location = at; o.rotation_euler = (R(90), 0, 0)
    m = bpy.data.materials.new("lab " + text); m.use_nodes = True
    p = m.node_tree.nodes.get("Principled BSDF")
    p.inputs["Emission Color"].default_value = (1, 0.75, 0.7, 1); p.inputs["Emission Strength"].default_value = 2.0
    cu.materials.append(m); col.objects.link(o)


def camera(name, target, dist, height, lens=50):
    cd = bpy.data.cameras.new(name); cd.lens = lens
    c = bpy.data.objects.new(name, cd); col.objects.link(c)
    c.location = target + Vector((0, -dist, height))
    c.rotation_euler = (target - c.location).to_track_quat("-Z", "Y").to_euler()
    return c


BLOOD = (0.55, 0.0, 0.02)
EMBER = (1.0, 0.12, 0.05)
cams = {}

# ---- B1: rings of blood-light pulsing out, embers rising --------------------------------------------------
at = Vector((0, 0, 0)); plinth(at); battery("B1", at); label("B1  monolith  -  blood rings + rising embers", at + Vector((0, -1.2, 3.9)), 0.22)
for i, off in enumerate((0, 16, 32)):
    bpy.ops.mesh.primitive_torus_add(major_radius=0.45, minor_radius=0.014, major_segments=48, minor_segments=8)
    ring = bpy.context.active_object
    for c in list(ring.users_collection):
        c.objects.unlink(ring)
    col.objects.link(ring)
    ring.name = f"Blood ring {i}"; ring.location = at + PORT + Vector((0, -0.08, 0)); ring.rotation_euler = (R(90), 0, 0)
    phase = f"fmod(frame + {off}, 48) / 48"
    for ax in range(3):
        dr = ring.driver_add("scale", ax).driver; dr.type = "SCRIPTED"; dr.expression = f"1 + 2.2 * {phase}"
    ring.data.materials.append(emissive(f"blood ring {i}", (1.0, 0.05, 0.04), f"5 * pow(1 - {phase}, 2)", base=(0.2, 0, 0)))
e1 = emitter("Ember emitter B1", at + Vector((0, 0, 0.55)), 1.0)
particles(e1, "embers", drop_object("Blood ember", EMBER, 0.05, "4"), 500, 1, 240, 70, 0.4, 0.5, -0.05, 1.0, 0.6)
cams["B1"] = camera("Cam B1", at + Vector((0, 0, 1.7)), 11.5, 0.6)

# ---- B2: blood dripping and running, basin and channels throbbing ----------------------------------------
at = Vector((5.0, 0, 0)); plinth(at); battery("B2", at); label("B2  bleeding  -  dripping blood + throbbing basin", at + Vector((0, -1.2, 3.9)), 0.22)
e2 = emitter("Drip emitter B2", at + PORT + Vector((0, -0.05, -0.42)), 0.32, rot=(0, 0, 0))
particles(e2, "drips", drop_object("Blood drop", BLOOD, 0.08, "0.8"), 260, 1, 240, 40, 0.0, 0.05, 1.0, 1.0, 0.5)
e2b = emitter("Spill emitter B2", at + Vector((0, -0.72, 0.5)), 0.12, rot=(R(90), 0, 0))
particles(e2b, "spill", drop_object("Blood spill", BLOOD, 0.06, "0.5"), 180, 1, 240, 30, 0.6, 0.2, 1.0, 1.0, 0.5)
cams["B2"] = camera("Cam B2", at + Vector((0, 0, 1.7)), 11.5, 0.6)

# ---- B3: a burst of blood spray on every heartbeat, with a shockwave flash ----------------------------------
at = Vector((10.0, 0, 0)); plinth(at); battery("B3", at); label("B3  engine  -  heartbeat blood bursts", at + Vector((0, -1.2, 3.9)), 0.22)
spray = drop_object("Blood spray", (0.8, 0.02, 0.03), 0.07, "1.5")
for k, f0 in enumerate(range(10, 240, 48)):                     # the beat peaks at frame ~12 + 48 n
    eb = emitter(f"Burst emitter B3 {k}", at + PORT + Vector((0, -0.05, 0)), 0.38, rot=(R(90), 0, 0))
    particles(eb, f"burst {k}", spray, 220, f0, f0 + 3, 34, 4.5, 2.4, 0.5, 1.0, 0.7)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, segments=32, ring_count=16)
wave = bpy.context.active_object
for c in list(wave.users_collection):
    c.objects.unlink(wave)
col.objects.link(wave)
wave.name = "Shockwave B3"; wave.location = at + PORT
ph = "fmod(frame + 36, 48) / 48"
for ax in range(3):
    dr = wave.driver_add("scale", ax).driver; dr.type = "SCRIPTED"; dr.expression = f"0.2 + 5 * {ph}"
wm = bpy.data.materials.new("shockwave"); wm.use_nodes = True
nt = wm.node_tree; nt.nodes.clear()
lw = nt.nodes.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.15
em = nt.nodes.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (1, 0.06, 0.04, 1)
dr = em.inputs["Strength"].driver_add("default_value").driver; dr.type = "SCRIPTED"; dr.expression = f"3 * pow(1 - {ph}, 3)"
tr = nt.nodes.new("ShaderNodeBsdfTransparent"); mx = nt.nodes.new("ShaderNodeMixShader"); out = nt.nodes.new("ShaderNodeOutputMaterial")
nt.links.new(lw.outputs["Facing"], mx.inputs[0]); nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(em.outputs[0], mx.inputs[2])
nt.links.new(mx.outputs[0], out.inputs[0])
try:
    wm.surface_render_method = "BLENDED"
except Exception:
    pass
wave.data.materials.append(wm)
cams["B3"] = camera("Cam B3", at + Vector((0, 0, 1.7)), 11.5, 0.6)

# ---- room, glow ---------------------------------------------------------------------------------------------
world = bpy.data.worlds.new("Battery World"); world.use_nodes = True
world.node_tree.nodes.get("Background").inputs[0].default_value = (0.01, 0.006, 0.006, 1)
scene.world = world
fl = bpy.data.meshes.new("battery floor")
bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=25); bm.to_mesh(fl); bm.free()
fo = bpy.data.objects.new("Battery floor", fl); fo.location = (5, 3, -0.14); col.objects.link(fo)
fm = bpy.data.materials.new("battery floor"); fm.use_nodes = True
fm.node_tree.nodes.get("Principled BSDF").inputs["Base Color"].default_value = (0.03, 0.02, 0.02, 1)
fm.node_tree.nodes.get("Principled BSDF").inputs["Roughness"].default_value = 0.3
fl.materials.append(fm)
key = bpy.data.lights.new("battery key", "AREA"); key.energy = 900; key.size = 8
ko = bpy.data.objects.new("battery key", key); ko.location = (5, -9, 8); ko.rotation_euler = (R(48), 0, 0); col.objects.link(ko)
cams["all"] = camera("Cam all", Vector((5, 0, 1.8)), 19.0, 1.5, lens=40)
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x, scene.render.resolution_y = 1600, 900
try:
    scene.view_settings.view_transform = "Standard"
except Exception:
    pass
try:
    tree = bpy.data.node_groups.new("Battery Glow", "CompositorNodeTree")
    tree.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    rl = tree.nodes.new("CompositorNodeRLayers"); go = tree.nodes.new("NodeGroupOutput")
    gl = tree.nodes.new("CompositorNodeGlare")
    if "Type" in gl.inputs:
        gl.inputs["Type"].default_value = "Bloom"
    for nm, val in (("Size", 0.65), ("Strength", 0.5), ("Threshold", 1.0)):
        if nm in gl.inputs:
            gl.inputs[nm].default_value = val
    tree.links.new(rl.outputs["Image"], gl.inputs["Image"]); tree.links.new(gl.outputs["Image"], go.inputs[0])
    scene.compositing_node_group = tree
except Exception as e:
    print("no glow:", e)
rdir = os.path.join(FOLDER, "renders"); os.makedirs(rdir, exist_ok=True)
if not os.environ.get("LL_NO_RENDER"):
    for k in ("all", "B1", "B2", "B3"):
        scene.camera = cams[k]; scene.frame_set(14)
        scene.render.filepath = os.path.join(rdir, f"81_{k}.png")
        bpy.ops.render.render(write_still=True, scene=scene.name)
scene.camera = cams["all"]
scene.frame_set(1)
for sc in list(bpy.data.scenes):
    if sc != scene:
        bpy.data.scenes.remove(sc)
try:
    bpy.ops.outliner.orphans_purge(do_recursive=True)
except Exception:
    pass
bpy.ops.wm.save_as_mainfile(filepath=OUT)


def _after():
    try:
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
