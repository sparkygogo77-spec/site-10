"""Fallen Titan boss, round 4: J's three candidates (2026-10-19): "lets get a grizzly bear, an upgraded yellow lantern
ender man, and blue great white shark".

blender.exe -b --python titan_killer2_blend.py -- <out.blend> [--no-render]

  G1 Grizzly           a giant grizzly: shoulder hump, roaring, long pale claws (about 18 long, 10 at the shoulder)
  E1 Lantern Enderman  a Yellow Lantern enderman: 14 tall, stand-off yellow fear armour, a lantern core in its chest,
                       yellow construct blocks floating round it like the blocks endermen carry
  S1 Blue Great White  a great white, steel-blue on top and white below, blue hard-light gills, eyes and fin edges,
                       breaching out of a flooded room (about 22 long)
Each: a hero 3/4 view and a side profile, with a 1.8-block player for scale. Emission stays at or under 1.5.
"""
import math, os, sys
import bpy
import numpy as np
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import trial_blender_kit as K

argv = sys.argv[sys.argv.index("--") + 1:]
OUT = os.path.abspath(argv[0])
RENDER = "--no-render" not in argv
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
K.sc = sc
box, seg, mat, pmat, cmat, blob = K.box, K._seg, K.mat, K.pixel_mat, K.construct_mat, K._blob
M = dict(
    floor=pmat("titan floor", (0.10, 0.10, 0.12), (0.22, 0.22, 0.25)),
    fur=pmat("grizzly fur", (0.10, 0.06, 0.03), (0.30, 0.19, 0.10), 1.0),
    fur_tip=pmat("grizzly fur tips", (0.35, 0.26, 0.16), (0.55, 0.43, 0.30), 1.0),
    snout=pmat("snout", (0.25, 0.18, 0.12), (0.42, 0.32, 0.22), 0.8),
    nose=mat("nose", (0.02, 0.02, 0.02), 0.3),
    claw=pmat("claws", (0.60, 0.57, 0.50), (0.85, 0.82, 0.74), 0.4),
    mouth=mat("mouth", (0.25, 0.04, 0.04), 0.5),
    tooth=mat("teeth", (0.92, 0.90, 0.82), 0.4),
    eye_dark=mat("dark eye", (0.02, 0.01, 0.01), 0.2),
    ender=pmat("enderman black", (0.02, 0.02, 0.025), (0.07, 0.06, 0.08), 0.6),
    yellow=cmat("yellow fear armour", 1.0, 0.7),
    yglow=mat("yellow glow", (1, 0.78, 0.15), 0.3, (1, 0.72, 0.08), 1.5),
    gold=pmat("lantern gold", (0.45, 0.30, 0.05), (0.85, 0.65, 0.20), 0.3),
    shark=pmat("shark back", (0.10, 0.20, 0.32), (0.22, 0.36, 0.52), 0.35),
    belly=pmat("shark belly", (0.80, 0.82, 0.85), (0.95, 0.96, 0.97), 0.4),
    bglow=mat("blue glow", (0.2, 0.55, 1.0), 0.3, (0.2, 0.55, 1.0), 1.5),
    bfin=mat("blue hard light", (0.25, 0.55, 1.0), 0.3, (0.2, 0.5, 1.0), 1.0, alpha=0.65),
    water=mat("water", (0.03, 0.12, 0.22), 0.04, alpha=0.8),
    spray=mat("spray", (0.8, 0.9, 1.0), 0.2, alpha=0.8),
)
cams = []
rng = np.random.default_rng(21)


def V(*a):
    return Vector(a)


# ------------------------------------------------------------------ G1 grizzly
def grizzly(p):
    r = K.empty("G1 Grizzly", tuple(p))
    s = 1.0
    blob("G1 body", (0, 0, 7.5), (8.5, 15, 8), M["fur"], r)
    blob("G1 hump", (0, -4.5, 11.5), (7, 6, 4.5), M["fur"], r)          # shoulder hump
    blob("G1 rump", (0, 6, 8), (8, 6, 7), M["fur"], r)
    for k in range(60):                                               # shaggy tips
        u = rng.uniform(-1, 1, 3) * np.array([4, 7.5, 3.5])
        box(f"G1 tuft{k}", (u[0], u[1], 7.5 + abs(u[2]) + 0.8), (0.6, 0.6, 1.2), M["fur_tip"], r).rotation_euler = tuple(rng.uniform(-0.4, 0.4, 3))
    # head lowered and forward, mouth open
    blob("G1 head", (0, -11, 9.5), (6, 6, 5.5), M["fur"], r)
    box("G1 snout", (0, -15, 8.6), (3.4, 4, 2.6), M["snout"], r)
    box("G1 nose", (0, -17.1, 9.4), (1.6, 0.6, 1), M["nose"], r)
    box("G1 jaw", (0, -14.6, 6.4), (3.0, 3.6, 1.2), M["snout"], r).rotation_euler = (math.radians(18), 0, 0)
    box("G1 mouth", (0, -15, 7.4), (2.6, 3.4, 1.0), M["mouth"], r)
    for k in range(5):
        x = -1.2 + k * 0.6
        box(f"G1 tooth top{k}", (x, -16.4, 7.8), (0.3, 0.3, 0.7), M["tooth"], r)
        box(f"G1 tooth low{k}", (x, -16.0, 6.9), (0.3, 0.3, 0.6), M["tooth"], r)
    for sx in (-1, 1):
        box(f"G1 ear{sx}", (sx * 2.4, -10, 12.6), (1.4, 1, 1.4), M["fur"], r)
        box(f"G1 eye{sx}", (sx * 1.6, -13.7, 10.6), (0.6, 0.4, 0.6), M["eye_dark"], r)
    # legs, the front pair thicker; long pale claws
    for sx in (-1, 1):
        for (y, top, th) in ((-6, 9, 3.6), (6, 8, 3.2)):
            hip = V(sx * 3.6, y, top)
            knee = hip + V(sx * 0.4, -0.6, -4.2)
            paw = V(sx * 4.2, y - 1.2, 0.9)
            seg(f"G1 leg{sx}{y}a", hip, knee, th, M["fur"], r)
            seg(f"G1 leg{sx}{y}b", knee, paw, th * 0.85, M["fur"], r)
            box(f"G1 paw{sx}{y}", tuple(paw + V(0, -0.6, -0.3)), (th, th * 1.2, 1.2), M["fur"], r)
            for c in range(4):
                seg(f"G1 claw{sx}{y}{c}", paw + V((c - 1.5) * th * 0.25, -th * 0.6, -0.3), paw + V((c - 1.5) * th * 0.28, -th * 0.6 - 2.0, -0.85), 0.32, M["claw"], r)
    return r


# ------------------------------------------------------------------ E1 Yellow Lantern Enderman
def lantern_enderman(p):
    r = K.empty("E1 Lantern Enderman", tuple(p))
    H = 14.0
    box("E1 torso", (0, 0, H * 0.62), (2.2, 1.2, 4.0), M["ender"], r)
    box("E1 head", (0, 0, H * 0.86), (2.6, 2.6, 2.6), M["ender"], r)
    for sx in (-1, 1):
        box(f"E1 eye{sx}", (sx * 0.65, -1.32, H * 0.86), (0.9, 0.1, 0.35), M["yglow"], r)
    # jaw open a crack, like an angry enderman, glowing inside
    box("E1 jaw glow", (0, -1.31, H * 0.81), (1.6, 0.08, 0.2), M["yglow"], r)
    # legs and arms: long and thin
    for sx in (-1, 1):
        seg(f"E1 leg{sx}", V(sx * 0.6, 0, H * 0.46), V(sx * 0.8, 0.2, 0), 0.65, M["ender"], r)
        sh = V(sx * 1.5, 0, H * 0.76)
        hand = sh + V(sx * 1.2, -1.6, -H * 0.42)
        seg(f"E1 arm{sx}", sh, hand, 0.55, M["ender"], r)
    # Yellow Lantern armour: plates standing off the body (the 838 stand-off rule), a lantern core in the chest
    for sx in (-1, 1):
        box(f"E1 pauldron{sx}", (sx * 1.9, 0, H * 0.79), (1.6, 1.8, 0.4), M["yellow"], r).rotation_euler = (0, sx * math.radians(25), 0)
        box(f"E1 pauldron edge{sx}", (sx * 1.9, 0, H * 0.79), (1.62, 1.82, 0.42), M["yglow"], r, wire=0.06).rotation_euler = (0, sx * math.radians(25), 0)
        box(f"E1 greave{sx}", (sx * 0.7, -0.5, H * 0.2), (0.5, 0.3, 2.4), M["yellow"], r)
        box(f"E1 bracer{sx}", tuple(V(sx * 1.5, 0, H * 0.76).lerp(V(sx * 2.7, -1.6, H * 0.34), 0.7) + V(0, -0.45, 0)), (0.5, 0.3, 1.8), M["yellow"], r)
    box("E1 chest plate", (0, -0.95, H * 0.66), (2.6, 0.25, 2.4), M["yellow"], r)
    box("E1 chest plate edge", (0, -0.95, H * 0.66), (2.62, 0.27, 2.42), M["yglow"], r, wire=0.06)
    box("E1 lantern core", (0, -1.2, H * 0.62), (0.9, 0.5, 1.2), M["yglow"], r)
    box("E1 lantern frame", (0, -1.2, H * 0.62), (1.1, 0.6, 1.4), M["gold"], r, wire=0.1)
    box("E1 crown", (0, 0, H * 0.86 + 1.6), (2.8, 2.8, 0.3), M["gold"], r, wire=0.12)
    # the ring on its hand, and yellow construct blocks floating round it
    box("E1 ring", tuple(V(1.5, 0, H * 0.76) + V(1.2, -1.6, -H * 0.42) + V(0, -0.2, 0.3)), (0.35, 0.35, 0.35), M["yglow"], r)
    for k in range(7):
        a = k / 7 * math.tau
        c = V(math.cos(a) * 4.5, math.sin(a) * 4.5, H * 0.5 + math.sin(a * 3) * 2)
        b = box(f"E1 held block{k}", tuple(c), (1, 1, 1), M["yellow"], r)
        b.rotation_euler = tuple(rng.uniform(0, 0.8, 3))
        box(f"E1 held block edge{k}", tuple(c), (1.02, 1.02, 1.02), M["yglow"], r, wire=0.05).rotation_euler = b.rotation_euler
    for k in range(40):   # fear particles drifting off it (yellow, not ender purple)
        c = V(rng.uniform(-3, 3), rng.uniform(-3, 3), rng.uniform(0.5, H))
        box(f"E1 particle{k}", tuple(c), (0.12, 0.12, 0.12), M["yglow"], r)
    return r


# ------------------------------------------------------------------ S1 blue great white
def great_white(p, pitch=-35):
    r = K.empty("S1 Blue Great White", tuple(p))
    r.rotation_euler = (math.radians(pitch), 0, 0)
    L = 22.0
    # body: a torpedo of blocks, thickest a third back; dark blue above, white below
    for i in range(16):
        t = i / 15
        y = -L / 2 + t * L
        th = (math.sin(min(1, t * 1.4) * math.pi) ** 0.8) * 3.4 + 0.5 if t < 0.9 else 0.8
        box(f"S1 back{i}", (0, y, th * 0.25), (th * 1.15, L / 15 + 0.2, th * 1.0), M["shark"], r)
        box(f"S1 belly{i}", (0, y, -th * 0.45), (th * 1.0, L / 15 + 0.2, th * 0.7), M["belly"], r)
    # snout, open jaws with rows of teeth
    box("S1 snout", (0, -L / 2 - 1.2, 0.6), (2.4, 2.6, 1.6), M["shark"], r)
    box("S1 jaw", (0, -L / 2 + 0.3, -1.6), (2.8, 3.0, 0.8), M["belly"], r).rotation_euler = (math.radians(-22), 0, 0)
    box("S1 mouth", (0, -L / 2 + 0.6, -0.6), (2.4, 2.6, 1.0), M["mouth"], r)
    for k in range(7):
        x = -1.1 + k * 0.37
        box(f"S1 tooth top{k}", (x, -L / 2 - 0.4, -0.2), (0.22, 0.22, 0.6), M["tooth"], r)
        box(f"S1 tooth low{k}", (x, -L / 2 - 0.1, -1.2), (0.22, 0.22, 0.55), M["tooth"], r)
    for sx in (-1, 1):
        box(f"S1 eye{sx}", (sx * 1.25, -L / 2 + 1.2, 1.0), (0.2, 0.5, 0.5), M["bglow"], r)
        for g in range(5):   # blue hard-light gill slits
            box(f"S1 gill{sx}{g}", (sx * 1.6, -L / 2 + 3.2 + g * 0.55, 0.0), (0.12, 0.18, 1.6), M["bglow"], r)
        # pectoral fins: hard light with glowing edges
        fin = box(f"S1 pectoral{sx}", (sx * 4.2, -L / 2 + 6.5, -1.4), (5, 2.6, 0.3), M["bfin"], r)
        fin.rotation_euler = (0, sx * math.radians(-20), sx * math.radians(-25))
        box(f"S1 pectoral edge{sx}", fin.location, (5.02, 2.62, 0.32), M["bglow"], r, wire=0.08).rotation_euler = fin.rotation_euler
    dor = box("S1 dorsal", (0, -1.0, 4.2), (0.4, 4, 4.2), M["shark"], r); dor.rotation_euler = (math.radians(-25), 0, 0)
    box("S1 dorsal edge", dor.location, (0.42, 4.02, 4.22), M["bglow"], r, wire=0.08).rotation_euler = dor.rotation_euler
    for k, (zz, rot) in enumerate(((2.2, -35), (-1.8, 30))):   # the tail, upper lobe bigger
        t = box(f"S1 tail{k}", (0, L / 2 + 1.5, zz), (0.4, 3.2, 4.6 if k == 0 else 3.4), M["shark"], r)
        t.rotation_euler = (math.radians(rot), 0, 0)
        box(f"S1 tail edge{k}", t.location, (0.42, 3.22, (4.6 if k == 0 else 3.4) + 0.02), M["bglow"], r, wire=0.08).rotation_euler = t.rotation_euler
    return r


def water_and_spray(p, name):
    bpy.ops.mesh.primitive_plane_add(size=70, location=tuple(p))
    w = bpy.context.object; w.name = f"{name} water"; w.data.materials.append(M["water"])
    for k in range(60):
        a = rng.uniform(0, math.tau); d = rng.uniform(2, 9)
        c = p + V(math.cos(a) * d * 0.6, math.sin(a) * d, rng.uniform(0.2, 7) * (1 - d / 12))
        q = rng.uniform(0.25, 0.7)
        box(f"{name} spray{k}", tuple(c), (q, q, q), M["spray"], None).rotation_euler = tuple(rng.uniform(0, 1, 3))


# ------------------------------------------------------------------ stage each one
STAGES = [
    ("G1", "Grizzly", lambda p: grizzly(p), V(0, 0, 0), V(-11, -12, 0), V(0, -2, 7), 1.0),
    ("E1", "Lantern Enderman", lambda p: lantern_enderman(p), V(0, 0, 0), V(-4, -5, 0), V(0, 0, 7.5), 0.75),
    ("S1", "Blue Great White", lambda p: great_white(p + V(0, 0, 8)), V(0, 0, 0), V(-12, -12, 0.2), V(0, -3, 12), 1.3),
]
for si, (code, nm, build, off, player_at, tgt, dist) in enumerate(STAGES):
    o = V(si * 200.0, 0, 0)
    if code == "S1":
        water_and_spray(o + V(0, 4, 0.1), code)
        bpy.ops.mesh.primitive_plane_add(size=80, location=tuple(o + V(0, 0, -6)))
        bpy.context.object.data.materials.append(M["floor"])
        K.box(f"{code} ledge", tuple(o + player_at + V(0, 0, -0.5)), (6, 6, 1), M["floor"], None)
    else:
        bpy.ops.mesh.primitive_plane_add(size=80, location=tuple(o))
        bpy.context.object.data.materials.append(M["floor"])
    build(o + off)
    K.player(f"{code} player", tuple(o + player_at + (V(0, 0, 0) if code != "S1" else V(0, 0, 0))))
    t = o + tgt
    cams.append(K.camera(f"{len(cams) + 1:02d} {code} {nm} hero", tuple(t + V(24, -30, 6) * dist), tuple(t), 32))
    cams.append(K.camera(f"{len(cams) + 1:02d} {code} {nm} side", tuple(t + V(42, 0, 2) * dist), tuple(t), 32))
    K.light(f"{code} key", tuple(o + V(25, -30, 35)), 30000, (1, 0.95, 0.88), "AREA", 30)
    K.light(f"{code} rim", tuple(o + V(-25, 25, 22)), 18000, (0.6, 0.75, 1.0), "AREA", 25)

w = bpy.data.worlds.new("World"); sc.world = w
try:
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.05, 0.06, 0.08, 1)
except Exception as e:
    print("world", e)
sc.render.engine = "CYCLES"; sc.cycles.samples = 64; sc.cycles.use_denoising = True; sc.cycles.use_preview_denoising = True
prefs = bpy.context.preferences.addons["cycles"].preferences
for dt in ("OPTIX", "CUDA"):
    try:
        prefs.compute_device_type = dt; prefs.get_devices()
        if any(dv.type == dt for dv in prefs.devices):
            for dv in prefs.devices:
                dv.use = dv.type == dt
            sc.cycles.device = "GPU"; break
    except TypeError:
        continue
sc.render.resolution_x, sc.render.resolution_y = 1280, 720
sc.view_settings.view_transform = "Standard"
sc.camera = cams[0]
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
if RENDER:
    rdir = os.path.join(os.path.dirname(OUT), "renders_titan_killer2")
    os.makedirs(rdir, exist_ok=True)
    for cam in cams:
        sc.camera = cam
        sc.render.filepath = os.path.join(rdir, cam.name.replace(" ", "_") + ".png")
        bpy.ops.render.render(write_still=True)
    sc.camera = cams[0]
    bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("done", OUT)
