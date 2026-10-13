# Pass 207: hard-light construct tools, Blue set, round 1 (lead Blender chat, 2026-10-13).
# Same spec and the same six tools as pass 204 (Green): "each corps gets its own set, Green first, then Blue".
# Built before J's Green pick so the Blue set is ready; the three looks mirror T1-T3 in Blue Lantern colours:
#   U1 Sapphire relic: hard-light blue heads in the blue construct texture with a pale rim, deep navy wrapped
#      handles, pearl-silver filigree bands, sapphire pommel gems.
#   U2 Pearl edge: solid navy heads with layered pearl-silver edges and a glowing sky-blue inlay channel.
#   U3 Pure hope: everything is blue hard light, handle included; rims and ribs glow.
# Builds LanternLive\construct_tools_blue.blend; textures from LanternLive\tool_tex\.
import math, os
import bpy
import numpy as np

R = math.radians
TEX = os.path.join(FOLDER, "tool_tex")
OUT = os.path.join(FOLDER, "construct_tools_blue.blend")
if bpy.data.filepath:
    try:
        bpy.ops.wm.save_mainfile()
    except Exception as e:
        print("save current:", e)
old = bpy.data.scenes.get("Construct Tools Blue")
if old:
    bpy.data.scenes.remove(old)
scene = bpy.data.scenes.new("Construct Tools Blue")
col = scene.collection
scene.render.fps = 20
scene.frame_start, scene.frame_end = 1, 160
win = bpy.context.window
if win:
    win.scene = scene
VX = 1 / 32


def link(o):
    col.objects.link(o)
    return o


# ------------------------------------------------------------------ 2D designs: (u, v) -> role; v runs pommel -> tip
HANDLE, WRAP, BAND, GEM, CORE, EDGE, INLAY, SPINE = range(8)
THICK = {HANDLE: 2, WRAP: 2, BAND: 3, GEM: 3, CORE: 3, EDGE: 1, INLAY: 4, SPINE: 4}


def handle(D, v0, v1, bands=()):
    for v in range(v0, v1):
        for u in (-1, 0):
            D[(u, v)] = WRAP if (u + v) % 3 == 0 else HANDLE
    for b in bands:
        for u in (-2, -1, 0, 1):
            D[(u, b)] = BAND
    for v in range(-3, 4):                                  # faceted pommel gem
        for u in range(-3, 3):
            if abs(u + 0.5) + abs(v) <= 3.0:
                D[(u, v0 - 3 + v)] = GEM


def outline(D, roles=(CORE,)):
    """Pixels of a head region that touch empty space become the thin bright edge."""
    out = dict(D)
    for (u, v), r in D.items():
        if r in roles:
            if any((u + du, v + dv) not in D for du, dv in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                out[(u, v)] = EDGE
    D.clear(); D.update(out)


def sword():
    D = {}
    handle(D, 4, 15, bands=(8, 12))
    for u in range(-8, 8):                                  # thin crossguard, swept tips
        D[(u, 15)] = BAND; D[(u, 16)] = BAND
    D[(-9, 17)] = BAND; D[(8, 17)] = BAND
    for v in range(17, 58):
        half = 3 if v < 50 else max(0, round(3 * (58 - v) / 8))
        for u in range(-half, half):
            D[(u, v)] = CORE
    outline(D)
    for v in range(18, 52):                                 # the centre highlight / inlay line
        D[(-1, v)] = INLAY; D[(0, v)] = INLAY if v % 6 else SPINE
    return D


def pickaxe():
    D = {}
    handle(D, 4, 50, bands=(10, 22, 34, 46))
    cx, cy = 0, 38
    for u in range(-26, 27):
        for v in range(36, 60):
            d = math.hypot(u - cx, v - cy)
            a = abs(math.degrees(math.atan2(u, v - cy)))
            if a > 82:
                continue
            w = 2.6 * (1 - (a / 82) ** 1.6) + 0.5           # thin arc tapering to needle points
            if 17 - w <= d <= 17 + w * 0.6:
                D[(u, v)] = CORE
    for u in range(-3, 3):                                  # collar where head meets handle
        for v in range(50, 56):
            D[(u, v)] = BAND if v in (50, 55) else CORE
    outline(D)
    for u in range(-12, 12):                                # rib along the arc's crown
        v = int(round(cy + math.sqrt(max(0, 17 ** 2 - u * u)))) - 1
        if (u, v) in D and D[(u, v)] != BAND:
            D[(u, v)] = SPINE
    return D


def axe():
    D = {}
    handle(D, 4, 56, bands=(10, 22, 34, 46))
    for u in range(-22, 1):                                 # crescent: between two offset circles
        for v in range(30, 62):
            if math.hypot(u - 2, v - 46) <= 16 and math.hypot(u - 8, v - 46) >= 13.5 and u <= -1:
                D[(u, v)] = CORE
    for v in range(44, 50):                                 # back spike
        for u in range(1, 1 + max(1, 10 - abs(v - 47) * 3)):
            D[(u, v)] = CORE
    outline(D)
    for v in range(36, 57):                                 # layered inlay following the blade's curve
        u = int(round(2 - math.sqrt(max(0, 13 ** 2 - (v - 46) ** 2))))
        for du in (0, 1):
            if (u + du, v) in D and D[(u + du, v)] == CORE:
                D[(u + du, v)] = INLAY
    return D


def shovel():
    D = {}
    handle(D, 4, 44, bands=(10, 20, 30, 40))
    for u in range(-12, 13):                                # mace head: oval, flanged, four spikes
        for v in range(40, 64):
            e = (u / 7.5) ** 2 + ((v - 51) / 8.5) ** 2
            if e <= 1:
                D[(u, v)] = CORE
    for u, v in [(0, 60 + k) for k in range(4)] + [(-8 - k, 51) for k in range(4)] + [(7 + k, 51) for k in range(4)]:
        D[(u, v)] = CORE
    outline(D)
    for k in range(-5, 6):                                  # flanges / ribs across the head
        for u in (-4, 3):
            if (u, 51 + k) in D:
                D[(u, 51 + k)] = SPINE
    D[(0, 51)] = INLAY; D[(-1, 51)] = INLAY; D[(0, 52)] = INLAY; D[(-1, 52)] = INLAY
    return D


def hoe():
    D = {}
    handle(D, 4, 56, bands=(10, 22, 34, 46))
    for u in range(-26, 4):                                 # scythe hook curling off the top
        for v in range(36, 64):
            d = math.hypot(u + 9, v - 50)
            a = math.degrees(math.atan2(v - 50, u + 9))    # 0 = right, 90 = up
            if -40 <= a <= 185:
                t = (a + 40) / 225
                w = 2.4 * (1 - t) ** 0.8 + 0.4
                if 10 - w * 0.4 <= d <= 10 + w:
                    D[(u, v)] = CORE
    outline(D)
    for a in range(0, 150, 6):
        u = int(round(-9 + 10.6 * math.cos(R(a)))); v = int(round(50 + 10.6 * math.sin(R(a))))
        if (u, v) in D:
            D[(u, v)] = SPINE
    return D


def hammer():
    D = {}
    handle(D, 4, 46, bands=(10, 20, 30, 40))
    for u in range(-12, 12):                                # head with chamfered corners
        for v in range(44, 58):
            cu, cv = min(u + 12, 11 - u), min(v - 44, 57 - v)
            if cu + cv >= 2:
                D[(u, v)] = CORE
    outline(D)
    for u in range(-10, 10):                                # rune line across both faces
        if u % 4 != 0:
            D[(u, 51)] = INLAY
    for v in range(46, 56):
        D[(-12 + 1, v)] = SPINE; D[(10, v)] = SPINE
    return D


TOOLS = [("sword", sword), ("pickaxe", pickaxe), ("axe", axe), ("shovel", shovel), ("hoe", hoe), ("hammer", hammer)]


# ------------------------------------------------------------------ materials per take
def tex_mat(name, img_name, alpha=False, emit=0.0, rough=0.35, scale=1.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree; N, L = nt.nodes, nt.links
    N.clear()
    out = N.new("ShaderNodeOutputMaterial"); p = N.new("ShaderNodeBsdfPrincipled")
    tc = N.new("ShaderNodeTexCoord"); mp = N.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (scale, scale, scale)
    t = N.new("ShaderNodeTexImage")
    img = bpy.data.images.get("tt_" + img_name) or bpy.data.images.load(os.path.join(TEX, img_name + ".png"))
    img.name = "tt_" + img_name
    t.image = img; t.interpolation = "Closest"; t.projection = "BOX"; t.projection_blend = 0.0
    L.new(tc.outputs["Object"], mp.inputs["Vector"]); L.new(mp.outputs["Vector"], t.inputs["Vector"])
    L.new(t.outputs["Color"], p.inputs["Base Color"])
    p.inputs["Roughness"].default_value = rough
    if alpha:
        mx = N.new("ShaderNodeMath"); mx.operation = "MAXIMUM"; mx.inputs[1].default_value = 0.45
        L.new(t.outputs["Alpha"], mx.inputs[0]); L.new(mx.outputs[0], p.inputs["Alpha"])
        try:
            m.surface_render_method = "BLENDED"
        except Exception:
            pass
        m.use_backface_culling = False
    if emit:
        L.new(t.outputs["Color"], p.inputs["Emission Color"]); p.inputs["Emission Strength"].default_value = emit
    L.new(p.outputs["BSDF"], out.inputs["Surface"])
    return m


def flat(name, rgb, emit=0.0, rough=0.4, metal=0.0, alpha=1.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes.get("Principled BSDF")
    p.inputs["Base Color"].default_value = (*rgb, 1); p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metal
    if emit:
        p.inputs["Emission Color"].default_value = (*rgb, 1); p.inputs["Emission Strength"].default_value = emit
    if alpha < 1:
        p.inputs["Alpha"].default_value = alpha
        try:
            m.surface_render_method = "BLENDED"
        except Exception:
            pass
    return m


JADE_DARK = flat("CU navy", (0.02, 0.055, 0.2), rough=0.25)
JADE_WRAP = flat("CU navy wrap", (0.02, 0.05, 0.16), rough=0.45)
GOLD = flat("CU pearl silver", (0.78, 0.84, 0.92), rough=0.22, metal=1.0)
EMERALD = flat("CU sapphire", (0.03, 0.2, 0.85), emit=1.0, rough=0.1)
RIM = flat("CU rim", (0.7, 0.86, 1.0), emit=5.0)
GLOWLINE = flat("CU inlay", (0.25, 0.65, 1.0), emit=4.0)
HL = tex_mat("CU hard light", "construct_brick_blue", alpha=True, emit=1.4, scale=1.0)
HL_SOLID = tex_mat("CU hard light solid", "construct_inner_blue", alpha=False, emit=0.9, scale=1.0)
HL_HANDLE = tex_mat("CU hard light handle", "construct_rim_blue", alpha=True, emit=1.2, scale=2.0)

TAKES = {
    "T1": {HANDLE: JADE_DARK, WRAP: JADE_WRAP, BAND: GOLD, GEM: EMERALD, CORE: HL, EDGE: RIM, INLAY: HL_SOLID,
           SPINE: GOLD},
    "T2": {HANDLE: JADE_DARK, WRAP: GOLD, BAND: GOLD, GEM: EMERALD, CORE: JADE_DARK, EDGE: GOLD, INLAY: GLOWLINE,
           SPINE: GOLD},
    "T3": {HANDLE: HL_HANDLE, WRAP: RIM, BAND: RIM, GEM: EMERALD, CORE: HL, EDGE: RIM, INLAY: GLOWLINE, SPINE: RIM},
}
ORDER = [HANDLE, WRAP, BAND, GEM, CORE, EDGE, INLAY, SPINE]


def build_tool(name, D, mats):
    verts, faces, mi = [], [], []
    vox = {}
    for (u, v), r in D.items():
        t = THICK[r]
        for w in range(-(t // 2), t - t // 2):
            vox[(u, v, w)] = r
    for (u, v, w), r in vox.items():
        for (du, dv, dw), quad in (((1, 0, 0), [(1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)]),
                                   ((-1, 0, 0), [(0, 1, 0), (0, 0, 0), (0, 0, 1), (0, 1, 1)]),
                                   ((0, 1, 0), [(1, 1, 0), (0, 1, 0), (0, 1, 1), (1, 1, 1)]),
                                   ((0, -1, 0), [(0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)]),
                                   ((0, 0, 1), [(0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)]),
                                   ((0, 0, -1), [(0, 1, 0), (1, 1, 0), (1, 0, 0), (0, 0, 0)])):
            n = vox.get((u + du, v + dv, w + dw))
            if n is not None and (mats[n] is mats[r] or mats[n].surface_render_method != "BLENDED"):
                continue
            b = len(verts)
            # x = u, z = v (up), y = w (depth)
            verts.extend(((u + a) * VX, (w + c) * VX, (v + bb) * VX) for a, bb, c in quad)
            faces.append((b, b + 1, b + 2, b + 3)); mi.append(ORDER.index(r))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    for r in ORDER:
        me.materials.append(mats[r])
    me.polygons.foreach_set("material_index", mi)
    me.update()
    return link(bpy.data.objects.new(name, me))


ROWS = {"T1": 0.0, "T2": -3.2, "T3": -6.4}
for take, z0 in ROWS.items():
    for i, (tname, fn) in enumerate(TOOLS):
        o = build_tool(f"CU {take} {tname}", fn(), TAKES[take])
        o.location = (i * 1.6, 0, z0)
        o.rotation_euler = (0, R(-35), 0)                   # leaning like an item sprite
        # a slow turntable so the layered edges and faces catch the light
        o.rotation_mode = "ZXY"
        o.keyframe_insert("rotation_euler", frame=1)
        o.rotation_euler.z = R(360); o.keyframe_insert("rotation_euler", frame=161)
        try:
            fcs = list(o.animation_data.action.fcurves)
        except Exception:
            fcs = [fc for layer in o.animation_data.action.layers for s in layer.strips for cb in s.channelbags
                   for fc in cb.fcurves]
        for fc in fcs:
            for k in fc.keyframe_points:
                k.interpolation = "LINEAR"
    cu = bpy.data.curves.new("CU label " + take, "FONT")
    cu.body = {"T1": "U1 Sapphire relic", "T2": "U2 Pearl edge", "T3": "U3 Pure hope"}[take]
    cu.size = 0.35
    t = link(bpy.data.objects.new("CU label " + take, cu)); t.location = (-1.4, 0, z0 + 2.2)
    t.rotation_euler = (R(90), 0, 0)
    t.data.materials.append(flat("CU label", (0.8, 0.9, 1.0), emit=2.0))

world = bpy.data.worlds.get("CU world") or bpy.data.worlds.new("CU world")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.05, 0.06, 0.07, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.0
scene.world = world
for nm, rotv, e in (("CT key", (R(55), 0, R(-30)), 3.5), ("CT rim light", (R(-120), 0, R(160)), 2.0)):
    s = link(bpy.data.objects.new(nm, bpy.data.lights.new(nm, "SUN")))
    s.data.energy = e; s.rotation_euler = rotv
try:
    scene.render.engine = "BLENDER_EEVEE"
except Exception:
    scene.render.engine = "BLENDER_EEVEE_NEXT"
scene.render.resolution_x, scene.render.resolution_y = 1600, 900
scene.render.film_transparent = False
try:
    scene.view_settings.view_transform = "Standard"
except Exception:
    pass


def cam(name, loc, look, ortho=0.0, lens=50):
    c = link(bpy.data.objects.new(name, bpy.data.cameras.new(name)))
    c.location = loc
    if ortho:
        c.data.type = "ORTHO"; c.data.ortho_scale = ortho
    else:
        c.data.lens = lens
    d = np.array(look, float) - np.array(loc, float)
    c.rotation_euler = (math.atan2(math.hypot(d[0], d[1]), -d[2]), 0, math.atan2(d[1], d[0]) - math.pi / 2)
    return c


cams = {k: cam("Cam " + k, (4.1, -12, z + 1.1), (4.1, 0, z + 1.1), ortho=8.8) for k, z in ROWS.items()}
cams["all"] = cam("Cam all", (4.0, -20, -2.6), (4.0, 0, -2.6), ortho=10.0)
cams["turn"] = cam("Cam turn", (2.2, -4.5, 2.2), (1.6, 0, 1.0), lens=45)
scene.camera = cams["all"]

rdir = os.path.join(FOLDER, "renders"); os.makedirs(rdir, exist_ok=True)
if not os.environ.get("LL_NO_RENDER"):
    for key, c in cams.items():
        scene.camera = c; scene.frame_set(1 if key != "turn" else 30)
        scene.render.filepath = os.path.join(rdir, f"207_tools_blue_{key}.png")
        bpy.ops.render.render(write_still=True, scene=scene.name)
    scene.camera = cams["all"]
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
                    for sp in a.spaces:
                        if sp.type == "VIEW_3D":
                            sp.region_3d.view_perspective = "CAMERA"
                            sp.shading.type = "MATERIAL"
                    with bpy.context.temp_override(window=w, area=a):
                        if not bpy.context.screen.is_animation_playing:
                            bpy.ops.screen.animation_play()
                    return None
    except Exception as e:
        print("after:", e)
    return None


if bpy.app.background is False:
    bpy.app.timers.register(_after, first_interval=4.0)
print("saved", OUT)
