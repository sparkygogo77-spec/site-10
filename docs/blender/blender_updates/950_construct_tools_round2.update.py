# Pass 950: hard-light construct tools, round 2 - new designs (project thread "Hard light tool designs", 2026-10-14).
# J: "I need at least several new design options ... all kinds of models like double swords but large and curved
# like the axe there". Same voxel method and materials as passes 204/207 (half-model-pixel voxels, the construct
# texture on the broad faces, layered rim + inner inlay line), twelve new designs D1-D12, each in Green "Jade relic"
# (as T1) and Blue "Pure hope" (as U3). One camera per design ("Cam green_D1" ...).
# Pass number 950 is outside the lead Blender chat's 200+ sequence on purpose so the two never collide.
# Builds LanternLive\construct_tools_round2.blend; textures from LanternLive\tool_tex\ (same as pass 204/207).
import math

HANDLE, WRAP, BAND, GEM, CORE, EDGE, INLAY, SPINE = range(8)
R = math.radians


def handle(D, v0, v1, bands=(), pommel=True, u0=0):
    for v in range(v0, v1):
        for u in (u0 - 1, u0):
            D[(u, v)] = WRAP if (u + v) % 3 == 0 else HANDLE
    for b in bands:
        for u in range(u0 - 2, u0 + 2):
            D[(u, b)] = BAND
    if pommel:
        gem(D, u0, v0 - 3, 3)


def gem(D, cu, cv, r, role=GEM):
    for v in range(-r, r + 1):
        for u in range(-r, r):
            if abs(u + 0.5) + abs(v) <= r:
                D[(cu + u, cv + v)] = role


def disk(D, cu, cv, r, role=CORE, keep=None):
    for u in range(int(cu - r) - 1, int(cu + r) + 2):
        for v in range(int(cv - r) - 1, int(cv + r) + 2):
            if math.hypot(u - cu, v - cv) <= r and (keep is None or keep(u, v)):
                D[(u, v)] = role


def crescent(D, c1, r1, c2, r2, keep=None, role=CORE):
    """Inside circle 1, outside circle 2."""
    for u in range(int(c1[0] - r1) - 1, int(c1[0] + r1) + 2):
        for v in range(int(c1[1] - r1) - 1, int(c1[1] + r1) + 2):
            if math.hypot(u - c1[0], v - c1[1]) <= r1 and math.hypot(u - c2[0], v - c2[1]) >= r2:
                if keep is None or keep(u, v):
                    D[(u, v)] = role


def arcband(D, cu, cv, r, a0, a1, win, wout, role=CORE):
    """Band along a circle from angle a0 to a1 (degrees, counter-clockwise); widths are functions of t in 0..1."""
    span = (a1 - a0) % 360 or 360
    m = r + 12
    for u in range(int(cu - m), int(cu + m) + 1):
        for v in range(int(cv - m), int(cv + m) + 1):
            a = math.degrees(math.atan2(v - cv, u - cu))
            t = ((a - a0) % 360) / span
            if t > 1:
                continue
            d = math.hypot(u - cu, v - cv)
            if r - win(t) <= d <= r + wout(t):
                D[(u, v)] = role


def poly(D, pts, role=CORE):
    us = [p[0] for p in pts]; vs = [p[1] for p in pts]
    for u in range(int(min(us)) - 1, int(max(us)) + 2):
        for v in range(int(min(vs)) - 1, int(max(vs)) + 2):
            x, y = u + 0.5, v + 0.5
            inside = False
            for i in range(len(pts)):
                (x1, y1), (x2, y2) = pts[i], pts[i - 1]
                if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
                    inside = not inside
            if inside:
                D[(u, v)] = role


def line(D, p0, p1, w, role):
    n = int(max(abs(p1[0] - p0[0]), abs(p1[1] - p0[1])) * 2) + 1
    for i in range(n + 1):
        t = i / n
        u = p0[0] + (p1[0] - p0[0]) * t; v = p0[1] + (p1[1] - p0[1]) * t
        for du in range(-w // 2 + 1, w // 2 + 1):
            for dv in range(-w // 2 + 1, w // 2 + 1):
                D[(int(round(u)) + du, int(round(v)) + dv)] = role


def finish(D, layer=3, layer_role=INLAY, min_depth=6):
    """Outline the head (thin bright edge), then a second line `layer` px inside it where the head is deep enough."""
    heads = {k for k, r in D.items() if r == CORE}
    dist = {}
    front = [k for k in heads if any((k[0] + a, k[1] + b) not in D for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
    for k in front:
        dist[k] = 1
    i = 0
    while i < len(front):
        k = front[i]; i += 1
        for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (k[0] + a, k[1] + b)
            if n in heads and n not in dist:
                dist[n] = dist[k] + 1; front.append(n)
    deep = max(dist.values()) if dist else 0
    for k, d in dist.items():
        if d == 1:
            D[k] = EDGE
        elif layer and d == layer + 1 and deep >= min_depth:
            D[k] = layer_role
    return D


# ------------------------------------------------------------------ designs; v runs pommel -> tip
def twin_sabre():
    D = {}
    handle(D, 4, 18, bands=(8, 13))
    for u in range(-7, 8):
        v = 18 + round((abs(u) / 7) ** 2 * 3)
        D[(u, v)] = BAND; D[(u, v + 1)] = BAND
    gem(D, 0, 20, 2)
    w = lambda t: (7 + 4 * math.sin(math.pi * min(1, t * 1.1))) * (1 - t) ** 0.55 + 0.6
    arcband(D, -60, 21, 60, 0, 62, lambda t: w(t) * 0.7, lambda t: w(t) * 0.3)
    a = R(40); bu, bv = -60 + 62.5 * math.cos(a), 21 + 62.5 * math.sin(a)
    poly(D, [(bu - 3 * math.sin(a), bv + 3 * math.cos(a)), (bu + 7 * math.cos(a), bv + 7 * math.sin(a)),
             (bu + 3 * math.sin(a), bv - 3 * math.cos(a))])   # back spike on the spine
    finish(D)
    return D


def khopesh():
    D = {}
    handle(D, 4, 18, bands=(8, 13))
    for u in range(-6, 6):
        D[(u, 18)] = BAND; D[(u, 19)] = BAND
    for v in range(20, 36):
        for u in range(-3, 3):
            D[(u, v)] = CORE
    crescent(D, (-6, 47), 17, (-14, 54), 15, keep=lambda u, v: v >= 33)
    finish(D, layer=2)
    for v in range(21, 34):
        D[(-1, v)] = SPINE
    return D


def moon_glaive():
    D = {}
    handle(D, -18, 18, bands=(-12, -4, 4, 12), pommel=False)
    for s in (1, -1):
        crescent(D, (0, s * 30), 18, (0, s * 40), 17, keep=lambda u, v, s=s: s * v >= 17)
        for u in range(-3, 3):
            D[(u, s * 18)] = BAND; D[(u, s * 19)] = BAND
    finish(D, layer=2)
    gem(D, 0, 0, 3)
    return D


def labrys():
    D = {}
    handle(D, 4, 62, bands=(10, 22, 34, 46))
    for s in (-1, 1):
        crescent(D, (s * -2, 52), 19, (s * -11, 52), 17, keep=lambda u, v, s=s: s * u >= 3)
    for u in range(-3, 3):
        for v in range(40, 64):
            D[(u, v)] = CORE
    poly(D, [(-3, 64), (2, 64), (-0.5, 76)])
    finish(D, layer=3)
    gem(D, 0, 52, 2)
    return D


def war_scythe():
    D = {}
    handle(D, 4, 84, bands=(12, 28, 44, 60, 76))
    w = lambda t: 6.5 * (1 - t) ** 0.8 + 0.5
    arcband(D, -22, 64, 24, 15, 170, lambda t: w(t) * 0.4, lambda t: w(t) * 0.6)
    poly(D, [(-2, 84), (1, 84), (-0.5, 92)])
    for u in range(-3, 3):
        for v in range(78, 84):
            D[(u, v)] = CORE
    finish(D, layer=2)
    return D


def crescent_glaive():
    D = {}
    handle(D, 4, 72, bands=(12, 26, 40, 54, 66))
    for v in range(72, 98):
        t = (v - 72) / 26
        half = 5 * math.sin(math.pi * min(1, t * 1.15)) ** 0.8 + (1 if t < 0.95 else 0)
        for u in range(-int(round(half)), int(round(half))):
            D[(u, v)] = CORE
    w = lambda t: 3.5 * math.sin(math.pi * t) ** 0.6 + 0.5
    arcband(D, 0, 84, 15, 200, 340, lambda t: w(t) * 0.5, lambda t: w(t) * 0.5)
    finish(D, layer=2)
    for v in range(76, 94):
        D[(-1, v)] = SPINE
    return D


def halberd():
    D = {}
    handle(D, 4, 80, bands=(12, 26, 40, 54, 68))
    crescent(D, (-4, 66), 15, (2, 66), 10.5, keep=lambda u, v: u <= -2)
    for u in range(-3, 3):
        for v in range(56, 78):
            D[(u, v)] = CORE
    for v in range(78, 96):
        half = max(1, round(3 * (96 - v) / 18 + 0.5))
        for u in range(-half, half):
            D[(u, v)] = CORE
    arcband(D, 12, 72, 9, 160, 260, lambda t: 1.5 * (1 - t) + 0.4, lambda t: 1.5 * (1 - t) + 0.4)
    finish(D, layer=2)
    return D


def greatsword():
    D = {}
    handle(D, 4, 22, bands=(9, 15))
    for u in range(-13, 13):
        v = 22 + round((abs(u + 0.5) / 13) ** 2 * 5)
        for k in range(3):
            D[(u, v + k)] = BAND
    for v in range(25, 90):
        half = 6 if v < 76 else max(0, round(6 * (90 - v) / 14))
        for u in range(-half, half):
            D[(u, v)] = CORE
    finish(D, layer=3)
    for v in range(30, 74):
        D[(-1, v)] = INLAY; D[(0, v)] = INLAY
    gem(D, 0, 27, 2)
    return D


def chakram():
    D = {}
    arcband(D, -0.5, 0, 20, 0, 360, lambda t: 3, lambda t: 3)
    for k in range(8):
        a = R(k * 45 + 22.5)
        tip = (-0.5 + 30 * math.cos(a), 30 * math.sin(a))
        b1 = (-0.5 + 21 * math.cos(a - 0.22), 21 * math.sin(a - 0.22))
        b2 = (-0.5 + 21 * math.cos(a + 0.12), 21 * math.sin(a + 0.12))
        poly(D, [b1, tip, b2])
    finish(D, layer=3, min_depth=4)
    for u in range(-15, 15):
        for v in (-1, 0):
            D[(u, v)] = WRAP if (u + v) % 3 == 0 else HANDLE
    gem(D, 0, 0, 3)
    return D


def trident():
    D = {}
    handle(D, 4, 68, bands=(12, 26, 40, 54))
    for u in range(-10, 10):
        for v in (68, 69, 70):
            D[(u, v)] = CORE
    for v in range(70, 98):
        half = 2 if v < 90 else max(1, round(2 * (98 - v) / 8 + 0.4))
        for u in range(-half, half):
            D[(u, v)] = CORE
    poly(D, [(-2, 84), (-6, 82), (-2, 88)]); poly(D, [(1, 84), (5, 82), (1, 88)])
    for s in (-1, 1):
        arcband(D, s * 26 - 0.5, 70, 18, 90 if s > 0 else 0, 180 if s > 0 else 90,
                lambda t: 1.5 * (1 - t) + 0.6, lambda t: 1.5 * (1 - t) + 0.6)
    finish(D, layer=0)
    return D


def morningstar():
    D = {}
    handle(D, 4, 56, bands=(10, 22, 34, 46))
    for u in range(-10, 10):
        for v in range(54, 70):
            cu, cv = min(u + 10, 9 - u), min(v - 54, 69 - v)
            if cu + cv >= 3:
                D[(u, v)] = CORE
    poly(D, [(-3, 70), (2, 70), (-0.5, 84)])
    poly(D, [(10, 59), (10, 65), (22, 54)])
    poly(D, [(-10, 58), (-10, 66), (-16, 62)])
    finish(D, layer=3, min_depth=4)
    gem(D, 0, 62, 3)
    return D


def moon_pick():
    D = {}
    handle(D, 4, 52, bands=(10, 22, 34, 46))
    cy = 36
    for u in range(-30, 31):
        for v in range(40, 66):
            d = math.hypot(u, v - cy)
            a = abs(math.degrees(math.atan2(u, v - cy)))
            if a > 84:
                continue
            w = 5 * (1 - (a / 84) ** 1.4) + 0.6
            if 20 - w * 0.5 <= d <= 20 + w * 0.5:
                D[(u, v)] = CORE
    for u in range(-3, 3):
        for v in range(52, 57):
            D[(u, v)] = CORE
    finish(D, layer=2)
    gem(D, 0, 56, 3)
    return D


DESIGNS = [
    ("D1 Twin moon sabres", twin_sabre, "pair"),
    ("D2 Twin khopesh", khopesh, "pair"),
    ("D3 Moon glaive", moon_glaive, "one"),
    ("D4 Crescent labrys", labrys, "one"),
    ("D5 War scythe", war_scythe, "one"),
    ("D6 Crescent spear", crescent_glaive, "one"),
    ("D7 Halberd", halberd, "one"),
    ("D8 Greatsword", greatsword, "one"),
    ("D9 Chakram", chakram, "one"),
    ("D10 Trident", trident, "one"),
    ("D11 Star hammer", morningstar, "one"),
    ("D12 Moon pick", moon_pick, "one"),
]



# ------------------------------------------------------------------ Blender scene
import os
import bpy
import numpy as np

TEX = os.path.join(FOLDER, "tool_tex")
OUT = os.path.join(FOLDER, "construct_tools_round2.blend")
VX = 1 / 32
THICK = {HANDLE: 2, WRAP: 2, BAND: 3, GEM: 3, CORE: 3, EDGE: 1, INLAY: 4, SPINE: 4}
ORDER = [HANDLE, WRAP, BAND, GEM, CORE, EDGE, INLAY, SPINE]

old = bpy.data.scenes.get("Construct Tools R2")
if old:
    bpy.data.scenes.remove(old)
scene = bpy.data.scenes.new("Construct Tools R2")
col = scene.collection
if bpy.context.window:
    bpy.context.window.scene = scene


def link(o):
    col.objects.link(o)
    return o


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


def flat(name, rgb, emit=0.0, rough=0.4, metal=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes.get("Principled BSDF")
    p.inputs["Base Color"].default_value = (*rgb, 1); p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metal
    if emit:
        p.inputs["Emission Color"].default_value = (*rgb, 1); p.inputs["Emission Strength"].default_value = emit
    return m


# Green "Jade relic" (as T1) and Blue "Pure hope" (as U3)
LOOKS = {
    "green": {HANDLE: flat("R2 jade dark", (0.008, 0.06, 0.025), rough=0.25),
              WRAP: flat("R2 jade wrap", (0.02, 0.16, 0.06), rough=0.45),
              BAND: flat("R2 gold", (0.85, 0.6, 0.16), rough=0.25, metal=1.0),
              GEM: flat("R2 emerald", (0.02, 0.75, 0.22), emit=1.0, rough=0.1),
              CORE: tex_mat("R2 hard light", "construct_brick", alpha=True, emit=1.4),
              EDGE: flat("R2 rim", (0.55, 1.0, 0.65), emit=5.0),
              INLAY: tex_mat("R2 hard light solid", "construct_inner", emit=0.9),
              SPINE: flat("R2 gold", (0.85, 0.6, 0.16), rough=0.25, metal=1.0)},
}
_rim_b = flat("R2 blue rim", (0.7, 0.86, 1.0), emit=5.0)
LOOKS["blue"] = {HANDLE: tex_mat("R2 blue handle", "construct_rim_blue", alpha=True, emit=1.2, scale=2.0),
                 WRAP: _rim_b, BAND: _rim_b,
                 GEM: flat("R2 sapphire", (0.03, 0.2, 0.85), emit=1.0, rough=0.1),
                 CORE: tex_mat("R2 blue hard light", "construct_brick_blue", alpha=True, emit=1.4),
                 EDGE: _rim_b, INLAY: flat("R2 blue inlay", (0.25, 0.65, 1.0), emit=4.0), SPINE: _rim_b}


def build_tool(name, D, mats, mirror=False):
    verts, faces, mi = [], [], []
    vox = {}
    for (u, v), r in D.items():
        if mirror:
            u = -u - 1
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
            verts.extend(((u + a) * VX, (w + c) * VX, (v + bb) * VX) for a, bb, c in quad)
            faces.append((b, b + 1, b + 2, b + 3)); mi.append(ORDER.index(r))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    for r in ORDER:
        me.materials.append(mats[r])
    me.polygons.foreach_set("material_index", mi)
    me.update()
    return link(bpy.data.objects.new(name, me))


GROUPS = []                                                 # (key, label, [objects])
for li, (look, mats) in enumerate(LOOKS.items()):
    for i, (label, fn, kind) in enumerate(DESIGNS):
        D = fn()
        x0, z0 = i * 5.0, -li * 6.0
        objs = []
        if kind == "pair":                                  # two mirrored blades, crossed
            for s in (1, -1):
                o = build_tool(f"R2 {look} {label} {'R' if s > 0 else 'L'}", D, mats, mirror=s < 0)
                o.location = (x0 + s * 0.35, 0.02 * s, z0)
                o.rotation_euler = (0, math.radians(-14 * s), math.radians(18))
                objs.append(o)
        else:
            o = build_tool(f"R2 {look} {label}", D, mats)
            o.location = (x0, 0, z0)
            o.rotation_euler = (0, 0, math.radians(22))   # a quarter turn so the layered edges show
            objs.append(o)
        GROUPS.append((f"{look}_{label.split()[0]}", f"{label} ({look})", objs))

world = bpy.data.worlds.get("R2 world") or bpy.data.worlds.new("R2 world")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.05, 0.06, 0.07, 1)
scene.world = world
for nm, rotv, e in (("R2 key", (math.radians(55), 0, math.radians(-30)), 3.5),
                    ("R2 rim light", (math.radians(-120), 0, math.radians(160)), 2.0)):
    s = link(bpy.data.objects.new(nm, bpy.data.lights.new(nm, "SUN")))
    s.data.energy = e; s.rotation_euler = rotv
try:
    scene.view_settings.view_transform = "Standard"
except Exception:
    pass
scene.render.resolution_x = scene.render.resolution_y = 800
scene.view_layers[0].update()

cams = []
boxes = []
for key, label, objs in GROUPS:
    pts = np.array([o.matrix_world @ v.co for o in objs for v in o.data.vertices])
    boxes.append((pts.min(0), pts.max(0)))
SCALE = max(max(hi[0] - lo[0], hi[2] - lo[2]) for lo, hi in boxes) * 1.06   # one scale: true relative sizes
for (key, label, objs), (lo, hi) in zip(GROUPS, boxes):
    c = link(bpy.data.objects.new("Cam " + key, bpy.data.cameras.new("Cam " + key)))
    c.data.type = "ORTHO"; c.data.ortho_scale = SCALE
    c.location = ((lo[0] + hi[0]) / 2, -10, (lo[2] + hi[2]) / 2)
    c.rotation_euler = (math.radians(90), 0, 0)
    cams.append((key, c))
scene.camera = cams[0][1]

if not os.environ.get("LL_NO_RENDER"):
    if bpy.app.background:
        scene.render.engine = "CYCLES"; scene.cycles.samples = 32; scene.cycles.use_denoising = True
    else:
        try:
            scene.render.engine = "BLENDER_EEVEE"
        except Exception:
            scene.render.engine = "BLENDER_EEVEE_NEXT"
    rdir = os.path.join(FOLDER, "renders"); os.makedirs(rdir, exist_ok=True)
    for key, c in cams:
        scene.camera = c
        scene.render.filepath = os.path.join(rdir, f"r2_{key}.png")
        bpy.ops.render.render(write_still=True, scene=scene.name)
        print("rendered", key, flush=True)
    scene.camera = cams[0][1]
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("saved", OUT)
