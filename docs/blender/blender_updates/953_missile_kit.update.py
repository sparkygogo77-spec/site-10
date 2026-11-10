# Pass 953: construct missile kit, a barrage that rains in from above, and five explosions (chat "titanic", 2026-11-09).
# J: "I want a missile set built that will rain in from above and some explosion animations modeled for me" / "do the
# missiles in a single pass here, different detail portions and let me mix and match ... so i can mix match compare
# contrast and decide which pieces look how and which to refine and build another 3 variations of given my choices".
# One missile, real size (6 m long, 0.5 m across: a cruise missile; 1 block = 1 m, voxels of 1/16 block), cut into
# portions. Every portion has options, built differently, and a slider picks which one is on the missile:
#   nose      1 N1 Ogive, 2 N2 Sharp cone, 3 N3 Blunt dome, 4 N4 Seeker eye, 5 N5 Penetrator spike
#   body      1 B1 Banded tube, 2 B2 Conduit and panels, 3 B3 Two-stage, 4 B4 Carrier box
#   fins      1 F1 Cruise wings, 2 F2 Delta fins, 3 F3 Grid fins, 4 F4 Canards and tail, 5 F5 Strakes only
#   engine    1 G1 Bell nozzle, 2 G2 Air-breather, 3 G3 Four nozzles, 4 G4 Petal tail
#   trail     1 T1 Solid beam, 2 T2 Pixel smoke, 3 T3 Corkscrew, 4 T4 Jagged lightning
#   explosion 1 E1 Ground burst, 2 E2 Airburst and embers, 3 E3 Penetrator plume, 4 E4 Cluster carpet, 5 E5 Lightning scorch
# Sliders: Properties > Scene > Custom Properties (nose, body, fins, engine, trail, explosion, missile_size).
# Move a slider and the mix missile, all 14 missiles of the barrage and every impact change together.
# Shades of green stand for colours (J: "shades of green representing color"): dark bands, bright noses, lime fins,
# yellow-green stripes, glowing cores. Saturated, never white.
# Barrage: 14 missiles, one every 6 ticks, 60 blocks a second down a steep line into a 44-block field; each explodes
# on contact (no wind-up, the scorch mark is there the same tick). Frames 1-140.
# Cameras are numbered and carry the option's name: "1 Mix - side", "2 Mix - three-quarter",
# "3 N1 Ogive - shelf" ... one per option, "25 E1 Ground burst - shelf" ... "30 Barrage - wide",
# "31 Barrage - ground level", "32 Barrage - from above".
# Builds LanternLive\constructs\953_missile_kit.blend.
SCENE_NAME = "Missile Kit"
OUT_REL = "constructs/953_missile_kit.blend"
SEED = 953
import math, os
import bpy
import numpy as np
from mathutils import Vector

OUT = os.path.join(FOLDER, *OUT_REL.split("/"))
os.makedirs(os.path.dirname(OUT), exist_ok=True)
if bpy.data.filepath:
    try:
        bpy.ops.wm.save_mainfile()
    except Exception as e:
        print("save current:", e)
old = bpy.data.scenes.get(SCENE_NAME)
if old:
    bpy.data.scenes.remove(old)
scene = bpy.data.scenes.new(SCENE_NAME)
col = scene.collection
scene.render.fps = 20
win = bpy.context.window
if win:
    win.scene = scene
END = 140
scene.frame_start, scene.frame_end = 1, END
PX = 1 / 16.0
rng = np.random.default_rng(SEED)


def link(o, c=None):
    (c or col).objects.link(o)
    return o


# ------------------------------------------------------------------ sliders
SLIDERS = (("nose", 1, 1, 5, "1 N1 Ogive, 2 N2 Sharp cone, 3 N3 Blunt dome, 4 N4 Seeker eye, 5 N5 Penetrator spike"),
           ("body", 1, 1, 4, "1 B1 Banded tube, 2 B2 Conduit and panels, 3 B3 Two-stage, 4 B4 Carrier box"),
           ("fins", 1, 1, 5, "1 F1 Cruise wings, 2 F2 Delta fins, 3 F3 Grid fins, 4 F4 Canards and tail, 5 F5 Strakes only"),
           ("engine", 1, 1, 4, "1 G1 Bell nozzle, 2 G2 Air-breather, 3 G3 Four nozzles, 4 G4 Petal tail"),
           ("trail", 1, 1, 4, "1 T1 Solid beam, 2 T2 Pixel smoke, 3 T3 Corkscrew, 4 T4 Jagged lightning"),
           ("explosion", 1, 1, 5, "1 E1 Ground burst, 2 E2 Airburst and embers, 3 E3 Penetrator plume, 4 E4 Cluster carpet, 5 E5 Lightning scorch"),
           ("missile_size", 2.0, 0.5, 8.0, "Size of the barrage's missiles: 1 = real size (6 blocks long), 2 = twice"))
for name, default, lo, hi, tip in SLIDERS:
    scene[name] = default
    scene.id_properties_ui(name).update(min=lo, max=hi, soft_min=lo, soft_max=hi, description=tip)


def drive_scale(o, prop, value=None):
    """Scale 1 when the scene slider equals value (or = the slider itself when value is None), else 0."""
    for i in range(3):
        d = o.driver_add("scale", i).driver
        v = d.variables.new(); v.name = "v"; v.type = "SINGLE_PROP"
        v.targets[0].id_type = "SCENE"; v.targets[0].id = scene; v.targets[0].data_path = f'["{prop}"]'
        if value is None:
            d.type = "AVERAGE"
        else:
            d.type = "SCRIPTED"
            d.expression = f"1 if abs(v - {value}) < 0.5 else 0"


# ------------------------------------------------------------------ materials
def attr_material(name):
    """Tone and glow come from per-face attributes."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree
    for nd in list(nt.nodes):
        nt.nodes.remove(nd)
    tone = nt.nodes.new("ShaderNodeAttribute"); tone.attribute_name = "tone"
    glow = nt.nodes.new("ShaderNodeAttribute"); glow.attribute_name = "glow"
    b = nt.nodes.new("ShaderNodeBsdfPrincipled"); b.inputs["Roughness"].default_value = 0.35
    st = nt.nodes.new("ShaderNodeMath"); st.operation = "MULTIPLY_ADD"
    st.inputs[1].default_value = 0.85; st.inputs[2].default_value = 0.5
    nt.links.new(glow.outputs["Fac"], st.inputs[0])
    nt.links.new(tone.outputs["Color"], b.inputs["Base Color"]); nt.links.new(tone.outputs["Color"], b.inputs["Emission Color"])
    nt.links.new(st.outputs[0], b.inputs["Emission Strength"])
    out = nt.nodes.new("ShaderNodeOutputMaterial"); nt.links.new(b.outputs[0], out.inputs["Surface"])
    return m


def blast_material():
    """Colour and fade come from the object's own colour (keyframed), so every blast piece fades on its own."""
    m = bpy.data.materials.new("Blast"); m.use_nodes = True
    try:
        m.surface_render_method = "DITHERED"
    except Exception:
        pass
    nt = m.node_tree
    for nd in list(nt.nodes):
        nt.nodes.remove(nd)
    info = nt.nodes.new("ShaderNodeObjectInfo")
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.inputs["Base Color"].default_value = (0, 0, 0, 1)
    b.inputs["Emission Strength"].default_value = 1.0                 # kept low: saturated green, not mint
    nt.links.new(info.outputs["Color"], b.inputs["Emission Color"]); nt.links.new(info.outputs["Alpha"], b.inputs["Alpha"])
    out = nt.nodes.new("ShaderNodeOutputMaterial"); nt.links.new(b.outputs[0], out.inputs["Surface"])
    return m


def flat_material(name, rgb, emit=0.4):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1); b.inputs["Emission Color"].default_value = (*rgb, 1)
    b.inputs["Emission Strength"].default_value = emit
    return m


KIT = attr_material("Missile construct")
BLAST = blast_material()
DARK = flat_material("Ground", (0.030, 0.034, 0.040), 0.0)
TEXT = flat_material("Label", (0.20, 0.95, 0.35), 0.9)

# ------------------------------------------------------------------ voxel meshes
BODY, BAND, NOSE, FIN, STRIPE, NOZ, CORE, GLASS, PANEL = range(1, 10)
PAL = np.array([(0, 0, 0), (0.030, 0.400, 0.110), (0.008, 0.100, 0.040), (0.100, 0.800, 0.220), (0.140, 0.900, 0.260),
                (0.420, 0.800, 0.040), (0.006, 0.060, 0.028), (0.200, 1.000, 0.350), (0.120, 0.950, 0.300),
                (0.020, 0.270, 0.080)], np.float32)
GLOW = np.array([0, 0, 0, 0.1, 0.15, 0.4, 0, 1.0, 0.9, 0], np.float32)
DIRS = (((1, 0, 0), ((1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1))), ((-1, 0, 0), ((0, 0, 0), (0, 0, 1), (0, 1, 1), (0, 1, 0))),
        ((0, 1, 0), ((0, 1, 0), (0, 1, 1), (1, 1, 1), (1, 1, 0))), ((0, -1, 0), ((0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1))),
        ((0, 0, 1), ((0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1))), ((0, 0, -1), ((0, 0, 0), (0, 1, 0), (1, 1, 0), (1, 0, 0))))
LIGHT = (1.0, 0.80, 0.90, 0.70, 1.12, 0.55)
W = 56                                                    # grid width across (px); the axis runs down the middle


def grid(nx):
    x, y, z = np.meshgrid(np.arange(nx) + 0.5, np.arange(W) + 0.5 - W / 2, np.arange(W) + 0.5 - W / 2, indexing="ij")
    return np.zeros((nx, W, W), np.uint8), x, y, z, np.hypot(y, z)


def vox_mesh(name, role, x0=0.0, unit=PX, centre=True):
    """Outside faces of a role grid as one mesh. x0 = where the grid's x = 0 sits (px)."""
    solid = role > 0
    p = np.pad(solid, 1)
    n = solid.shape
    verts, tone, glow = [], [], []
    for li, ((dx, dy, dz), corners) in enumerate(DIRS):
        face = solid & ~p[1 + dx:1 + dx + n[0], 1 + dy:1 + dy + n[1], 1 + dz:1 + dz + n[2]]
        idx = np.argwhere(face)
        if not len(idx):
            continue
        verts.append((idx[:, None, :] + np.array(corners)[None, :, :]).reshape(-1, 3))
        r = role[face]
        tone.append(PAL[r] * LIGHT[li]); glow.append(GLOW[r])
    VI = np.vstack(verts).astype(np.int64)
    nf = len(VI) // 4
    key = (VI[:, 0] << 40) | (VI[:, 1] << 20) | VI[:, 2]
    uk, inv = np.unique(key, return_inverse=True)
    V = np.stack([uk >> 40, (uk >> 20) & 0xFFFFF, uk & 0xFFFFF], 1).astype(np.float32)
    V[:, 0] += x0
    if centre:
        V[:, 1] -= n[1] / 2; V[:, 2] -= n[2] / 2
    V *= unit
    me = bpy.data.meshes.new(name)
    me.vertices.add(len(V)); me.loops.add(nf * 4); me.polygons.add(nf)
    me.vertices.foreach_set("co", V.ravel())
    me.loops.foreach_set("vertex_index", inv.astype(np.int32))
    me.polygons.foreach_set("loop_start", np.arange(0, nf * 4, 4, dtype=np.int32))
    me.polygons.foreach_set("loop_total", np.full(nf, 4, np.int32))
    me.update()
    C = np.concatenate(tone)
    me.attributes.new("tone", "BYTE_COLOR", "FACE").data.foreach_set("color", np.hstack([C, np.ones((nf, 1), np.float32)]).ravel())
    me.attributes.new("glow", "FLOAT", "FACE").data.foreach_set("value", np.concatenate(glow))
    me.materials.append(KIT)
    return me


def box_mesh(name, boxes):
    """Boxes [(centre, size, role)] in px as one mesh (trails and bolts)."""
    V, F, tone, glow = [], [], [], []
    for (cx, cy, cz), (sx, sy, sz), r in boxes:
        b = len(V)
        for dx in (-.5, .5):
            for dy in (-.5, .5):
                for dz in (-.5, .5):
                    V.append(((cx + dx * sx) * PX, (cy + dy * sy) * PX, (cz + dz * sz) * PX))
        for q, li in (((4, 6, 7, 5), 0), ((0, 1, 3, 2), 1), ((2, 3, 7, 6), 2), ((0, 4, 5, 1), 3), ((1, 5, 7, 3), 4), ((0, 2, 6, 4), 5)):
            F.append(tuple(b + i for i in q)); tone.append(PAL[r] * LIGHT[li]); glow.append(GLOW[r])
    me = bpy.data.meshes.new(name)
    me.from_pydata(V, [], F); me.update()
    C = np.array(tone, np.float32)
    me.attributes.new("tone", "BYTE_COLOR", "FACE").data.foreach_set("color", np.hstack([C, np.ones((len(F), 1), np.float32)]).ravel())
    me.attributes.new("glow", "FLOAT", "FACE").data.foreach_set("value", np.array(glow, np.float32))
    me.materials.append(KIT)
    return me


R = 4.0                                                   # body radius, px (0.5 m across)
BL, NX0 = 72, 72                                          # body length; the nose starts where the body ends


# ---- noses (x from the body's front)
def nose(kind):
    n = {1: 20, 2: 28, 3: 10, 4: 13, 5: 36}[kind]
    g, x, y, z, r = grid(n)
    if kind == 1:
        g[r <= R * (1 - (x / n) ** 1.8) ** 0.6] = NOSE
        g[(g > 0) & (x < 2)] = BAND; g[(g > 0) & (x >= 5) & (x < 7)] = STRIPE
    elif kind == 2:
        g[r <= R * (1 - x / n) + 0.3] = NOSE
        g[(g > 0) & (x > n - 8)] = BAND; g[(g > 0) & (x >= 3) & (x < 5)] = STRIPE; g[(g > 0) & (x < 1)] = BAND
    elif kind == 3:
        g[r <= R * np.sqrt(np.clip(1 - (x / n) ** 2, 0, 1))] = NOSE
        g[(g > 0) & (x < 2)] = BAND; g[(g > 0) & (x > 6)] = PANEL
    elif kind == 4:
        g[(r <= R) & (x < 6)] = BAND
        g[(r <= R + 0.8) & (x >= 4) & (x < 6)] = STRIPE
        g[(r <= R * np.sqrt(np.clip(1 - ((x - 6) / 7) ** 2, 0, 1)) - 0.3) & (x >= 6)] = GLASS
    else:
        g[(r <= R) & (x < 5)] = BAND
        g[(r <= R + 0.8) & (x >= 1) & (x < 3)] = STRIPE
        g[(r <= R * (1 - (x - 5) / 6)) & (x >= 5) & (x < 9)] = BAND
        g[(r <= 1.6) & (x >= 5) & (x < n - 6)] = NOZ
        g[(r <= 1.6 * (n - x) / 6) & (x >= n - 6)] = NOSE
    return g


def body(kind):
    g, x, y, z, r = grid(BL)
    if kind == 1:
        g[r <= R] = BODY
        for a in (10, 40):
            g[(g > 0) & (x >= a) & (x < a + 2)] = BAND
        g[(g > 0) & (x >= 60) & (x < 62)] = STRIPE
    elif kind == 2:
        g[r <= R] = BODY
        g[(g > 0) & (x % 12 < 1)] = PANEL
        g[(np.abs(y) < 1) & (z >= R - 0.5) & (z < R + 1.5) & (x >= 6) & (x < 66)] = BAND        # the conduit along the top
        g[(g == BODY) & (y > R - 1.2) & (np.abs(z) < 2) & (x >= 28) & (x < 36)] = STRIPE        # an access hatch
        g[(g == BODY) & (y < -R + 1.2) & (np.abs(z) < 2) & (x >= 44) & (x < 50)] = BAND
    elif kind == 3:
        rr = np.where(x < 30, R + 1.6, np.where(x < 34, R + 1.6 * (34 - x) / 4, R))
        g[r <= rr] = BODY
        g[(g > 0) & (x < 30)] = PANEL
        g[(g > 0) & (x >= 30) & (x < 34)] = STRIPE
        g[(g > 0) & (x >= 2) & (x < 4)] = BAND; g[(g > 0) & (x >= 26) & (x < 28)] = BAND
        g[(g > 0) & (x >= 62) & (x < 64)] = BAND
    else:
        sq = (np.abs(y) <= R) & (np.abs(z) <= R) & (np.abs(y) + np.abs(z) <= 2 * R - 1.5)
        g[sq & (x >= 0)] = BODY
        g[(g > 0) & ((np.abs(y) < 0.6) | (np.abs(z) < 0.6)) & (x >= 8) & (x < 64)] = BAND       # door seams
        for a in (8, 26, 45, 63):
            g[(g > 0) & (x >= a) & (x < a + 1)] = BAND
        g[(g == BODY) & (x >= 66) & (x < 68)] = STRIPE
    return g


def fins(kind):
    g, x, y, z, r = grid(BL)
    ay, az = np.abs(y), np.abs(z)
    flat_y = (az < 0.6) & (ay > R - 0.5)                  # a blade lying in the y plane
    flat_z = (ay < 0.6) & (az > R - 0.5)
    if kind == 1:
        g[flat_y & (ay < 24) & (x >= 34 - (ay - R) * 0.15) & (x < 44 - (ay - R) * 0.15)] = FIN     # long straight wings
        g[flat_y & (ay >= 22) & (ay < 24) & (x >= 31) & (x < 42)] = STRIPE
        tail = (x >= 1) & (x < 11 - 0 * x)
        g[(flat_y | flat_z) & tail & (np.maximum(ay, az) < R + 8 - np.clip(x - 5, 0, 9) * 0.9)] = FIN
    elif kind == 2:
        span = R + 12 * np.clip(1 - x / 20, 0, 1)
        g[(flat_y | flat_z) & (x < 20) & (np.maximum(ay, az) < span)] = FIN
        g[(g == FIN) & (x < 1.5)] = BAND
    elif kind == 3:
        for plane, a, b in ((flat_y, ay, x), (flat_z, az, x)):
            pass
        lat_y = (ay > R + 1) & (ay < R + 11) & (az < 5) & (x >= 4) & (x < 6)                        # lattice panels
        lat_z = (az > R + 1) & (az < R + 11) & (ay < 5) & (x >= 4) & (x < 6)
        hole_y = ((np.floor(ay - R) % 3) != 1) & ((np.floor(z + 5) % 3) != 0) & (az < 4) & (ay < R + 10) & (ay > R + 2)
        hole_z = ((np.floor(az - R) % 3) != 1) & ((np.floor(y + 5) % 3) != 0) & (ay < 4) & (az < R + 10) & (az > R + 2)
        g[lat_y & ~hole_y] = FIN; g[lat_z & ~hole_z] = FIN
        g[((ay > R - 0.5) & (ay <= R + 1) & (az < 1.2) | (az > R - 0.5) & (az <= R + 1) & (ay < 1.2)) & (x >= 3) & (x < 7)] = BAND
    elif kind == 4:
        g[(flat_y | flat_z) & (x >= 58) & (x < 66) & (np.maximum(ay, az) < R + 6 - np.clip(x - 60, 0, 6))] = STRIPE   # canards
        g[(flat_y | flat_z) & (x >= 0) & (x < 13) & (np.maximum(ay, az) < R + 10 - np.clip(x - 4, 0, 9))] = FIN
        g[(g == FIN) & (np.maximum(ay, az) > R + 8.5)] = BAND
    else:
        g[(flat_y | flat_z) & (x >= 0) & (x < 22) & (np.maximum(ay, az) < R + 1.6)] = FIN
        g[(r > R - 0.5) & (r <= R + 1.0) & (x >= 0) & (x < 2)] = BAND
    return g


def engine(kind):
    """x runs 0-26; the body's rear is at x = 10 (so a scoop can reach forward under the body)."""
    g, x, y, z, r = grid(26)
    back = 10 - x                                         # px behind the body, 0-10
    if kind == 1:
        rr = 2.2 + (R + 0.6 - 2.2) * np.clip(back / 10, 0, 1) ** 0.7
        g[(r <= rr) & (r > rr - 1.2) & (x < 10)] = NOZ
        g[(r <= 2.2) & (x >= 7) & (x < 10)] = NOZ
        g[(r <= rr - 1.2) & (x >= 2) & (x < 7)] = CORE
    elif kind == 2:
        g[(r <= 2.6) & (x < 10) & (x >= 4)] = NOZ
        g[(r <= 1.6) & (x < 6) & (x >= 3)] = CORE
        g[(r <= R * np.clip((x - 3) / 7, 0, 1) + 0.2) & (x < 10) & (x >= 4)] = BAND                 # boat tail
        scoop = (np.abs(y) < 3) & (z < -R + 0.5) & (z > -R - 4) & (x >= 10) & (x < 26)
        g[scoop] = PANEL
        g[scoop & (np.abs(y) < 2) & (z < -R - 0.5) & (z > -R - 3) & (x >= 22)] = CORE               # the intake mouth
        g[scoop & (x >= 21) & (x < 22)] = STRIPE
    elif kind == 3:
        g[(r <= R) & (x >= 8) & (x < 10)] = BAND
        for sy in (-2.2, 2.2):
            for sz in (-2.2, 2.2):
                rq = np.hypot(y - sy, z - sz)
                rr = 1.0 + 1.0 * np.clip(back / 8, 0, 1)
                g[(rq <= rr) & (x < 8)] = NOZ
                g[(rq <= rr - 0.9) & (x < 5) & (x >= 1)] = CORE
    else:
        rr = R - (R - 2.4) * np.clip(back / 8, 0, 1)
        g[(r <= rr) & (x < 10) & (x >= 2)] = BAND
        g[(r <= 1.7) & (x < 3)] = CORE
        ay, az = np.abs(y), np.abs(z)
        g[((az < 0.6) & (ay < R + 1) | (ay < 0.6) & (az < R + 1)) & (x < 6) & (np.maximum(ay, az) > 1.5)] = FIN   # petals
    return g


def trail(kind):
    """Behind the engine: from x = -10 back 12 blocks."""
    Lpx = 192
    b = []
    r2 = np.random.default_rng(SEED + kind)
    if kind == 1:
        for i in range(12):
            w = 5.0 * (1 - i / 13)
            b.append(((-10 - 8 - i * 16, 0, 0), (16, w, w), CORE))
            b.append(((-10 - 8 - i * 16, 0, 0), (16.2, w * 0.45, w + 0.4), NOZ if i < 9 else BAND))       # the darker core
    elif kind == 2:
        for i in range(18):
            s = 2 + i * 0.75
            b.append(((-12 - i * 10.5, r2.uniform(-1, 1) * i * 0.45, r2.uniform(-1, 1) * i * 0.45), (s, s, s),
                      (CORE, FIN, NOSE, BODY, PANEL, BAND)[min(5, i // 3)]))
    elif kind == 3:
        for i in range(64):
            a = i * 0.52
            rad = 2 + i * 0.09
            b.append(((-11 - i * 3, rad * math.cos(a), rad * math.sin(a)), (3.4, 2, 2), CORE if i % 4 else STRIPE))
            if i % 2 == 0:
                b.append(((-11 - i * 3, -rad * math.cos(a), -rad * math.sin(a)), (3.4, 1.4, 1.4), FIN))
    else:
        p = np.array([-10.0, 0, 0])
        for i in range(22):
            q = p + np.array([-r2.uniform(6, 11), r2.uniform(-5, 5), r2.uniform(-5, 5)])
            q[1:] *= 0.75
            n = int(np.abs(q - p).max() / 1.5) + 1
            for t in np.linspace(0, 1, n):
                c = p + (q - p) * t
                b.append((tuple(c), (2.2, 1.6, 1.6), CORE if i % 3 else STRIPE))
            p = q
    return box_mesh(f"trail T{kind}", b)


NAMES = {"nose": ("N1 Ogive", "N2 Sharp cone", "N3 Blunt dome", "N4 Seeker eye", "N5 Penetrator spike"),
         "body": ("B1 Banded tube", "B2 Conduit and panels", "B3 Two-stage", "B4 Carrier box"),
         "fins": ("F1 Cruise wings", "F2 Delta fins", "F3 Grid fins", "F4 Canards and tail", "F5 Strakes only"),
         "engine": ("G1 Bell nozzle", "G2 Air-breather", "G3 Four nozzles", "G4 Petal tail"),
         "trail": ("T1 Solid beam", "T2 Pixel smoke", "T3 Corkscrew", "T4 Jagged lightning"),
         "explosion": ("E1 Ground burst", "E2 Airburst and embers", "E3 Penetrator plume", "E4 Cluster carpet", "E5 Lightning scorch")}
MESH = {}
for k in range(1, 6):
    MESH["nose", k] = vox_mesh(NAMES["nose"][k - 1], nose(k), x0=BL)
    MESH["fins", k] = vox_mesh(NAMES["fins"][k - 1], fins(k))
for k in range(1, 5):
    MESH["body", k] = vox_mesh(NAMES["body"][k - 1], body(k))
    MESH["engine", k] = vox_mesh(NAMES["engine"][k - 1], engine(k), x0=-10)
    MESH["trail", k] = trail(k); MESH["trail", k].name = NAMES["trail"][k - 1]

# the kit: every option at the same place, the sliders decide which shows
kit = bpy.data.collections.new("Missile kit (driven by the sliders)")
col.children.link(kit)
for (group, k), me in MESH.items():
    o = link(bpy.data.objects.new(f"kit {me.name}", me), kit)
    drive_scale(o, group, k)

CAMS = []


def camera(name, loc, target, lens=35, ortho=None, far=900):
    name = f"{len(CAMS) + 1} {name}"
    c = link(bpy.data.objects.new(name, bpy.data.cameras.new(name)))
    c.data.lens = lens; c.data.clip_start = 0.05; c.data.clip_end = far
    if ortho:
        c.data.type = "ORTHO"; c.data.ortho_scale = ortho
    c.location = loc
    dx, dy, dz = (target[i] - loc[i] for i in range(3))
    c.rotation_euler = (math.atan2(math.hypot(dx, dy), -dz), 0, math.atan2(dy, dx) - math.pi / 2)
    CAMS.append(name)
    return c


def label(text, loc, size=0.5):
    cu = bpy.data.curves.new("Label " + text, "FONT"); cu.body = text; cu.size = size; cu.align_x = "CENTER"
    o = link(bpy.data.objects.new("Label " + text, cu)); o.location = loc
    o.rotation_euler = (math.radians(90), 0, 0); cu.materials.append(TEXT)
    return o


def cube(name, size, loc, mat):
    me = bpy.data.meshes.new(name)
    sx, sy, sz = size
    v = [(x, y, z) for x in (0, sx) for y in (0, sy) for z in (0, sz)]
    f = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    me.from_pydata(v, [], f); me.update(); me.materials.append(mat)
    o = link(bpy.data.objects.new(name, me)); o.location = loc
    return o


# 1-2: the mix (the kit itself sits at the origin, nose toward +x)
camera("Mix - side", (2.2, -9.5, 0.4), (2.2, 0, 0), 35, ortho=10.5, far=22)
camera("Mix - three-quarter", (9.5, -5.5, 2.6), (2.6, 0, 0), 40, far=30)
label("your mix: move the sliders", (2.2, 0, 2.2), 0.45)
cube("Mix player (2 blocks)", (0.6, 0.6, 1.8), (6.6, 1.5, -0.9), TEXT)

# the shelf: every option on its own, one camera each
SHELF_Y = 40.0
row = 0
for group in ("nose", "body", "fins", "engine", "trail"):
    for k, nm in enumerate(NAMES[group], start=1):
        x0 = (k - 1) * 16.0
        y0 = SHELF_Y + row * 14.0
        o = link(bpy.data.objects.new(f"shelf {nm}", MESH[group, k])); o.location = (x0, y0, 0)
        if group in ("fins", "engine"):                   # shown on a plain body so the fit reads
            g = link(bpy.data.objects.new(f"shelf {nm} (on B1)", MESH["body", 1])); g.location = (x0, y0, 0)
        cx = {"nose": 5.1, "body": 2.25, "fins": 2.25, "engine": 0.6, "trail": -6.5}[group]
        width = {"nose": 3.4, "body": 6.0, "fins": 6.5, "engine": 4.6, "trail": 14.0}[group]
        label(nm, (x0 + cx, y0, {"fins": 2.2, "trail": 1.4}.get(group, 1.1)), 0.32 if group != "trail" else 0.6)
        d = width * 1.5
        camera(f"{nm} - shelf", (x0 + cx + d * 0.55, y0 - d, d * 0.35), (x0 + cx, y0, 0.1), 40)
    row += 1


# ------------------------------------------------------------------ explosions
def sphere_grid(n=24, half=False, shell=1.6):
    c = (np.arange(n) + 0.5 - n / 2)
    x, y, z = np.meshgrid(c, c, c, indexing="ij")
    r = np.sqrt(x * x + y * y + z * z)
    g = np.zeros((n, n, n), np.uint8)
    g[(r <= n / 2) & (r > n / 2 - shell)] = CORE
    if half:
        g[:, :, :n // 2] = 0
    return g


def blast_mesh(name, role, n):
    me = vox_mesh(name, role, unit=1.0 / (n / 2), centre=False)          # radius 1
    for v in me.vertices:
        v.co.x -= 1.0; v.co.y -= 1.0; v.co.z -= 1.0
    me.materials.clear(); me.materials.append(BLAST)
    return me


def ring_grid(n=40):
    c = (np.arange(n) + 0.5 - n / 2)
    x, y, zi = np.meshgrid(c, c, np.arange(n), indexing="ij")
    r = np.hypot(x, y)
    g = np.zeros((n, n, n), np.uint8)
    g[(r <= n / 2) & (r > n / 2 - 2.2) & (zi >= n // 2) & (zi < n // 2 + 1)] = CORE
    return g


def disc_grid(n=40):
    c = (np.arange(n) + 0.5 - n / 2)
    x, y, zi = np.meshgrid(c, c, np.arange(n), indexing="ij")
    r = np.hypot(x, y)
    g = np.zeros((n, n, n), np.uint8)
    jag = n / 2 - 2.5 + 2.5 * np.sin(np.arctan2(y, x) * 7) * np.cos(np.arctan2(y, x) * 3)
    g[(r <= jag) & (zi == n // 2)] = CORE
    return g


def column_grid(n=24):
    c = (np.arange(n) + 0.5 - n / 2)
    x, y, zi = np.meshgrid(c, c, np.arange(n), indexing="ij")
    r = np.hypot(x, y)
    g = np.zeros((n, n, n), np.uint8)
    g[(r <= n / 2) & (r > n / 2 - 2)] = CORE
    return g


M_DOME = blast_mesh("blast dome", sphere_grid(24, half=True), 24)
M_BALL = blast_mesh("blast ball", sphere_grid(24), 24)
M_RING = blast_mesh("blast ring", ring_grid(40), 40)
M_DISC = blast_mesh("blast scorch", disc_grid(40), 40)
M_COL = blast_mesh("blast column", column_grid(24), 24)
M_BIT = blast_mesh("blast bit", np.full((2, 2, 2), CORE, np.uint8), 2)
HOT, MID, DEEP, SCORCH = (0.07, 0.90, 0.18), (0.05, 0.62, 0.16), (0.012, 0.20, 0.07), (0.004, 0.035, 0.016)


def key(o, path, frame, value, interp="LINEAR"):
    setattr(o, path, value)
    o.keyframe_insert(path, frame=frame)


def piece(parent, mesh, name, loc, keys, colours):
    """keys: [(frame, scale)]  colours: [(frame, rgb, alpha)].  Hidden (scale 0) before its first key."""
    o = link(bpy.data.objects.new(name, mesh)); o.parent = parent; o.location = loc
    f0 = keys[0][0]
    o.scale = (0, 0, 0); o.keyframe_insert("scale", frame=max(1, f0 - 1))
    for f, s in keys:
        o.scale = s if isinstance(s, tuple) else (s, s, s)
        o.keyframe_insert("scale", frame=f)
    for f, rgb, a in colours:
        o.color = (*rgb, a); o.keyframe_insert("color", frame=f)
    return o


def bits(parent, name, origin, t0, n, speed, grav, life, r3, size=0.28, up=1.0):
    for i in range(n):
        a = r3.uniform(0, 2 * math.pi); el = r3.uniform(0.25, 1.2) * up
        v = np.array([math.cos(a) * math.cos(el), math.sin(a) * math.cos(el), math.sin(el)]) * speed * r3.uniform(0.6, 1.2)
        o = link(bpy.data.objects.new(f"{name} bit {i}", M_BIT)); o.parent = parent
        o.scale = (0, 0, 0); o.keyframe_insert("scale", frame=max(1, t0 - 1))
        for k in range(0, life + 1, 2):
            p = np.array(origin) + v * k + np.array([0, 0, -0.5 * grav * k * k])
            p[2] = max(p[2], 0.1)
            o.location = tuple(p); o.keyframe_insert("location", frame=t0 + k)
        s = size * r3.uniform(0.7, 1.4)
        o.scale = (s, s, s); o.keyframe_insert("scale", frame=t0)
        o.scale = (s * 0.5,) * 3; o.keyframe_insert("scale", frame=t0 + life)
        o.color = (*HOT, 1); o.keyframe_insert("color", frame=t0)
        o.color = (*MID, 0.0); o.keyframe_insert("color", frame=t0 + life)


def bolt_mesh(seed, height=55):
    r3 = np.random.default_rng(seed)
    b = []
    p = np.array([r3.uniform(-3, 3), r3.uniform(-3, 3), 0.0]) * 16
    top = height * 16
    while p[2] < top:
        q = p + np.array([r3.uniform(-40, 40), r3.uniform(-40, 40), r3.uniform(50, 110)])
        n = int(np.abs(q - p).max() / 6) + 1
        for t in np.linspace(0, 1, n):
            b.append((tuple(p + (q - p) * t), (7, 7, 7), CORE))
        p = q
    me = box_mesh("bolt", b); me.materials.clear(); me.materials.append(BLAST)
    return me


def explosion(kind, parent, t0, seed):
    """Build explosion E<kind> under parent, going off at frame t0."""
    r3 = np.random.default_rng(seed)
    nm = parent.name
    if kind == 1:        # ground burst: dome, shock ring, debris, instant scorch
        piece(parent, M_DISC, nm + " scorch", (0, 0, 0.03), [(t0, 5.5)], [(t0, SCORCH, 1.0)])
        piece(parent, M_DOME, nm + " dome", (0, 0, 0), [(t0, 1.2), (t0 + 3, 6.0), (t0 + 16, 7.0)],
              [(t0, HOT, 0.95), (t0 + 4, MID, 0.8), (t0 + 18, DEEP, 0.0)])
        piece(parent, M_DOME, nm + " core", (0, 0, 0), [(t0, 0.8), (t0 + 2, 3.2), (t0 + 9, 3.6)],
              [(t0, HOT, 1.0), (t0 + 9, MID, 0.0)])
        piece(parent, M_RING, nm + " ring", (0, 0, 0.3), [(t0, 1.0), (t0 + 8, 11.0), (t0 + 12, 12.5)],
              [(t0, HOT, 1.0), (t0 + 12, MID, 0.0)])
        bits(parent, nm, (0, 0, 0.3), t0, 12, 0.75, 0.07, 20, r3)
    elif kind == 2:      # airburst 9 up: flash ball, flat ring, embers that drift down
        piece(parent, M_BALL, nm + " flash", (0, 0, 9), [(t0, 1.0), (t0 + 2, 5.0), (t0 + 10, 5.6)],
              [(t0, HOT, 1.0), (t0 + 3, MID, 0.7), (t0 + 12, DEEP, 0.0)])
        piece(parent, M_RING, nm + " ring", (0, 0, 9), [(t0, 1.0), (t0 + 6, 9.0), (t0 + 10, 10.5)],
              [(t0, HOT, 1.0), (t0 + 10, MID, 0.0)])
        bits(parent, nm, (0, 0, 9), t0, 22, 0.42, 0.018, 34, r3, size=0.22, up=0.35)
    elif kind == 3:      # penetrator: a small entry, then a tall plume 6 ticks later
        piece(parent, M_DISC, nm + " scorch", (0, 0, 0.03), [(t0, 2.0)], [(t0, SCORCH, 1.0)])
        piece(parent, M_DOME, nm + " entry", (0, 0, 0), [(t0, 0.5), (t0 + 2, 1.5), (t0 + 6, 1.6)],
              [(t0, HOT, 1.0), (t0 + 6, MID, 0.0)])
        t1 = t0 + 6
        piece(parent, M_COL, nm + " plume", (0, 0, 0), [(t1, (1.6, 1.6, 0.5)), (t1 + 4, (2.0, 2.0, 18.0)), (t1 + 18, (2.6, 2.6, 21.0))],
              [(t1, HOT, 1.0), (t1 + 5, MID, 0.85), (t1 + 20, DEEP, 0.0)])
        piece(parent, M_COL, nm + " plume core", (0, 0, 0), [(t1, (0.8, 0.8, 0.5)), (t1 + 3, (1.0, 1.0, 20.0)), (t1 + 10, (1.1, 1.1, 22.0))],
              [(t1, HOT, 1.0), (t1 + 10, HOT, 0.0)])
        piece(parent, M_RING, nm + " ring", (0, 0, 0.3), [(t1, 1.0), (t1 + 6, 7.0), (t1 + 10, 8.0)], [(t1, HOT, 1.0), (t1 + 10, MID, 0.0)])
        bits(parent, nm, (0, 0, 0.3), t1, 10, 0.5, 0.05, 22, r3, up=1.3)
    elif kind == 4:      # cluster carpet: nine small bursts walking across the ground
        for j in range(9):
            a = r3.uniform(0, 2 * math.pi); d = r3.uniform(1.5, 8.5)
            p = (d * math.cos(a), d * math.sin(a), 0)
            tj = t0 + int(j * 1.5)
            piece(parent, M_DISC, f"{nm} scorch {j}", (p[0], p[1], 0.03), [(tj, 1.8)], [(tj, SCORCH, 1.0)])
            piece(parent, M_DOME, f"{nm} pop {j}", p, [(tj, 0.5), (tj + 2, 2.1), (tj + 9, 2.5)],
                  [(tj, HOT, 1.0), (tj + 3, MID, 0.8), (tj + 11, DEEP, 0.0)])
            piece(parent, M_RING, f"{nm} ring {j}", (p[0], p[1], 0.3), [(tj, 0.5), (tj + 5, 3.6)], [(tj, HOT, 1.0), (tj + 6, MID, 0.0)])
        bits(parent, nm, (0, 0, 0.3), t0 + 4, 10, 0.5, 0.06, 18, r3, size=0.2)
    else:                # lightning scorch: bolts flicker twice, a low dome, a wide ring
        piece(parent, M_DISC, nm + " scorch", (0, 0, 0.03), [(t0, 6.5)], [(t0, SCORCH, 1.0)])
        for j in range(4):
            o = link(bpy.data.objects.new(f"{nm} bolt {j}", bolt_mesh(seed * 7 + j))); o.parent = parent
            o.color = (*HOT, 1.0)
            for f, s in ((max(1, t0 - 1), 0), (t0 + j % 2, 1), (t0 + 2 + j % 2, 0), (t0 + 4, 1), (t0 + 7 + j, 0)):
                o.scale = (s, s, s); o.keyframe_insert("scale", frame=f)
            for fc in (o.animation_data.action.fcurves if hasattr(o.animation_data.action, "fcurves") else []):
                for kp in fc.keyframe_points:
                    kp.interpolation = "CONSTANT"
        piece(parent, M_DOME, nm + " dome", (0, 0, 0), [(t0, 0.8), (t0 + 2, 3.0), (t0 + 10, 3.4)], [(t0, HOT, 1.0), (t0 + 12, MID, 0.0)])
        piece(parent, M_RING, nm + " ring", (0, 0, 0.3), [(t0, 1.0), (t0 + 5, 9.0), (t0 + 9, 10.0)], [(t0, HOT, 1.0), (t0 + 9, MID, 0.0)])
        bits(parent, nm, (0, 0, 0.3), t0, 8, 0.6, 0.06, 16, r3, size=0.2)


def empty(name, loc=(0, 0, 0), parent=None):
    o = link(bpy.data.objects.new(name, None)); o.location = loc; o.empty_display_size = 0.3
    if parent:
        o.parent = parent
    return o


# the explosion shelf: all five, going off at frames 10 and 80
EX = (220.0, SHELF_Y)
cube("Shelf E ground", (220, 60, 1), (EX[0] - 30, EX[1] - 30, -1), DARK)
for k, nm in enumerate(NAMES["explosion"], start=1):
    c = (EX[0] + (k - 1) * 40.0, EX[1], 0)
    for rep, t0 in enumerate((10, 80)):
        explosion(k, empty(f"shelf {nm} {rep + 1}", c), t0, 100 + k)
    label(nm, (c[0], c[1] - 2, 24), 2.0)
    cube(f"shelf {nm} player (2 blocks)", (0.6, 0.6, 1.8), (c[0] + 9, c[1] - 2, 0), TEXT)
    camera(f"{nm} - shelf", (c[0] + 14, c[1] - 36, 12), (c[0], c[1], 8), 30)

# ------------------------------------------------------------------ the barrage
BX, BY = 0.0, -260.0
cube("Barrage ground", (160, 160, 1), (BX - 80, BY - 80, -1), DARK)
cube("Barrage player (2 blocks)", (0.6, 0.6, 1.8), (BX + 26, BY - 30, 0), TEXT)
cube("Barrage house 7 x 7 x 6", (7, 7, 6), (BX - 30, BY + 10, 0), flat_material("House", (0.10, 0.11, 0.12), 0.0))
NOSE_AHEAD = (BL + 20) * PX                               # the nose tip is this far ahead of the kit's origin
FLY = 90.0                                                # blocks flown; 3 blocks a tick = 60 blocks a second
for i in range(14):
    hit = Vector((BX + rng.uniform(-22, 22), BY + rng.uniform(-22, 22), 0))
    d = Vector((0.34 + rng.uniform(-0.07, 0.07), 0.20 + rng.uniform(-0.07, 0.07), -0.92)).normalized()
    f0 = 4 + i * 6 + int(rng.integers(0, 3))
    f1 = f0 + int(FLY / 3)
    carrier = empty(f"missile {i + 1} path")
    carrier.rotation_euler = Vector((1, 0, 0)).rotation_difference(d).to_euler()
    for f, p in ((f0, hit - d * FLY), (f1, hit)):
        carrier.location = p; carrier.keyframe_insert("location", frame=f)
    for f, s in ((max(1, f0 - 1), 0), (f0, 1), (f1, 0)):
        carrier.scale = (s, s, s); carrier.keyframe_insert("scale", frame=f)
    inst = empty(f"missile {i + 1}", (0, 0, 0), carrier)
    inst.instance_type = "COLLECTION"; inst.instance_collection = kit
    inst.location = (-NOSE_AHEAD * 2.0, 0, 0)             # nose tip on the path's point at missile_size 2
    drive_scale(inst, "missile_size")
    site = empty(f"impact {i + 1}", hit)
    for k in range(1, 6):
        e = empty(f"impact {i + 1} E{k}", (0, 0, 0), site)
        drive_scale(e, "explosion", k)
        explosion(k, e, f1, 500 + i * 10 + k)
# straight-line flight and on/off scales: no easing
for o in scene.objects:
    ad = o.animation_data
    if not ad or not ad.action or not (o.name.startswith("missile") and o.name.endswith("path")):
        continue
    try:
        fcs = list(ad.action.fcurves)
    except Exception:
        fcs = [fc for layer in ad.action.layers for strip in layer.strips for bag in strip.channelbags for fc in bag.fcurves]
    for fc in fcs:
        for kp in fc.keyframe_points:
            kp.interpolation = "CONSTANT" if fc.data_path == "scale" else "LINEAR"
camera("Barrage - wide", (BX + 72, BY - 80, 38), (BX - 4, BY, 13), 28)
camera("Barrage - ground level", (BX + 34, BY - 40, 1.7), (BX - 6, BY + 4, 13), 20)
camera("Barrage - from above", (BX - 30, BY - 20, 120), (BX, BY, 0), 30)
print("CAMS", CAMS, flush=True)
print("STATS", {me.name: len(me.polygons) for me in MESH.values()}, flush=True)

# ------------------------------------------------------------------ light, world, glow
world = bpy.data.worlds.new("Missile night"); world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.012, 0.016, 0.024, 1)
scene.world = world
sun = link(bpy.data.objects.new("Moonlight", bpy.data.lights.new("Moonlight", "SUN")))
sun.data.energy = 1.6; sun.rotation_euler = (math.radians(52), 0, math.radians(-35))
try:
    scene.view_settings.view_transform = "Standard"
except Exception:
    pass
try:
    scene.render.engine = "BLENDER_EEVEE"
except Exception:
    scene.render.engine = "BLENDER_EEVEE_NEXT"
scene.render.resolution_x, scene.render.resolution_y = 1280, 720
try:
    tree = bpy.data.node_groups.new("Missile Glow", "CompositorNodeTree")
    tree.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    rl = tree.nodes.new("CompositorNodeRLayers"); go = tree.nodes.new("NodeGroupOutput")
    gl = tree.nodes.new("CompositorNodeGlare")
    if "Type" in gl.inputs:
        gl.inputs["Type"].default_value = "Bloom"
    for nm, val in (("Size", 0.5), ("Strength", 0.4), ("Threshold", 1.0)):
        if nm in gl.inputs:
            gl.inputs[nm].default_value = val
    tree.links.new(rl.outputs["Image"], gl.inputs["Image"]); tree.links.new(gl.outputs["Image"], go.inputs[0])
    scene.compositing_node_group = tree
except Exception as e:
    print("no glow:", e)

scene.camera = bpy.data.objects[CAMS[0]]
scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("saved", OUT)
