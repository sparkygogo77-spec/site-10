# Pass 844: first-person construct tools, variations (Chat C, 2026-10-15, range 800-899).
# J rated 803 A1 C1 C2 H1 H2 P1 S2 S3 S4 V1 IMPROVE with no note: "3 new variations each", labelled, he picks. S1 dropped,
# O1 (hoe) not part of this round. Only the 30 new variations are here.
# First-person rules (DECISIONS): "i should see the arm relative to the crosshair at about 120 degree FOV"; crosshair in
# every first-person camera; the ring sits where the jar puts it (RingModels placement(): on the fist's punching face, over
# the middle finger, 1 px in from the back of the hand); the ring arm leads; the working edge leads (as 803).
# Each variation changes the motion AND the way the construct is built:
#   a = pixel stream (pixels fly from the ring and each section of the tool grows in, grip first)
#   b = extrude (the tool pushes out of the fist along its length behind a glowing scan plate)
#   c = lock-in (the tool's sections fly in from around the fist and snap into place, grip first)
# Hammer takes also change the head: H?a construct block hammer (803), H?b heavy hammer (bigger head, longer haft),
# H?c wedge hammer (flat striking face + wedge peen).
#   A1a axe: straight overhead chop, bites, wrenched free          A1b axe: two chops into one notch
#   A1c axe: level felling swing from the right
#   C1a sword combo: rising cut, overhead chop, thrust             C1b sword combo: four-hit flurry
#   C1c sword combo: slash, backhand, wide spinning sweep
#   C2a sword combo: thrust, then sweep out                        C2b sword combo: sweep, double stab
#   C2c sword combo: low sweep, rising thrust
#   H1a hammer: snap overhead, no hold                             H1b heavy hammer: full wind-up, crushing smash
#   H1c wedge hammer: setting tap, then full smash
#   H2a hammer: backhand side swing into the wall                  H2b heavy hammer: side swing that follows through
#   H2c wedge hammer: side swing, then an uppercut
#   P1a pickaxe: quick mining taps (3)                             P1b pickaxe: big strike, pry, pull out
#   P1c pickaxe: diagonal strike from the left
#   S2a sword: tight shoulder diagonal                             S2b sword: reverse diagonal, upper left to lower right
#   S2c sword: X cut (two crossing diagonals)
#   S3a sword: high fast sweep pair                                S3b sword: stepping wide sweep pair
#   S3c sword: three sweeps, right-left-right
#   S4a sword: quick flat jab                                      S4b sword: deep lunge
#   S4c sword: stab and twist out
#   V1a shovel: scoop and toss to the right                        V1b shovel: stomp dig, lever back
#   V1c shovel: two flat scrapes
# Readable in first person: targets (dark, low dummies or a block) meet the tool's far end on their near face at the
# first hit; thrusts cock the blade up 16 deg; shovels dig a little toward the crosshair; hit flashes green; take labels
# sit on the backdrop where only the side cameras see them.
# Cameras: "Cam <take>" first person (120 deg, crosshair), "Cam <take> side" third person from the right. Bays are 40 m
# apart with a backdrop wall so no camera sees a neighbour. Writes LanternLive\combat\fp_tools3_poses.json and builds
# LanternLive\combat\fp_tools3.blend.
import json, math, os
import bpy
import numpy as np
from mathutils import Matrix, Euler, Vector

R = math.radians
OUT = os.path.join(FOLDER, "combat", "fp_tools3.blend")
os.makedirs(os.path.dirname(OUT), exist_ok=True)
BB = None
for d_ in (os.path.join(FOLDER, "kl_assets"), os.path.join(os.getcwd(), "src", "main", "resources", "assets", "lanternring", "bbmodel")):
    if os.path.exists(os.path.join(d_, "construct_sword_green.bbmodel")):
        BB = d_; break
if bpy.data.filepath:
    try:
        bpy.ops.wm.save_mainfile()
    except Exception as e:
        print("save current:", e)
old = bpy.data.scenes.get("FP Tools 3")
if old:
    bpy.data.scenes.remove(old)
scene = bpy.data.scenes.new("FP Tools 3")
col = scene.collection
scene.render.fps = 20
win = bpy.context.window
if win:
    win.scene = scene
FORM = 14                 # forming ticks
GAP = 6                   # rest ticks between the two swings
P = 1 / 16                # one Minecraft pixel
PX = P * 1.05             # first-person pixel (a touch larger, as 803)


def link(o):
    col.objects.link(o)
    return o


def cam(name, loc, look, lens=40):
    c = link(bpy.data.objects.new(name, bpy.data.cameras.new(name)))
    c.location = loc; c.data.lens = lens; c.data.clip_start = 0.02
    d = np.array(look, float) - np.array(loc, float)
    c.rotation_euler = (math.atan2(math.hypot(d[0], d[1]), -d[2]), 0, math.atan2(d[1], d[0]) - math.pi / 2)
    return c


def mat(name, rgb, emit=0.0, alpha=1.0, rough=0.4, metal=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
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


SKIN = mat("FT3 skin", (0.62, 0.42, 0.3)); SLEEVE = mat("FT3 sleeve", (0.04, 0.28, 0.12))
RINGM = mat("FT3 ring face", (0.02, 0.85, 0.15), emit=2.0); GOLDM = mat("FT3 ring gold", (0.95, 0.7, 0.2), rough=0.25, metal=1.0)
GLASS = mat("FT3 hard-light glass", (0.03, 0.45, 0.16), emit=0.8, alpha=0.62, rough=0.15)
GLOW = mat("FT3 construct glow", (0.05, 0.9, 0.22), emit=3.5)
RIM = mat("FT3 construct rim", (0.08, 1.0, 0.28), emit=4.5)
GRIP = mat("FT3 construct grip", (0.02, 0.2, 0.08), emit=0.6, rough=0.3)
PIX = mat("FT3 forming pixel", (0.06, 1.0, 0.28), emit=4.0)
SCAN = mat("FT3 scan plate", (0.05, 0.95, 0.25), emit=3.0, alpha=0.45)
XH = mat("FT3 crosshair", (0.85, 0.85, 0.85), emit=1.0)
FLOOR = mat("FT3 floor", (0.18, 0.2, 0.22), rough=0.9)
WALL = mat("FT3 backdrop", (0.24, 0.26, 0.3), rough=0.95)
STONE = mat("FT3 block", (0.32, 0.33, 0.35), rough=0.9)
DIRT = mat("FT3 dirt", (0.35, 0.24, 0.15), rough=0.95)
DUMMY = mat("FT3 dummy", (0.07, 0.11, 0.08), rough=0.85)
HIT = mat("FT3 hit flash", (0.04, 0.7, 0.18), emit=1.6, alpha=0.8)
BOXF = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]


def box(name, a, b, m, parent=None, loc=None):
    a = np.array(a, float); b = np.array(b, float)
    v = [(x, y, z) for x in (a[0], b[0]) for y in (a[1], b[1]) for z in (a[2], b[2])]
    me = bpy.data.meshes.new(name); me.from_pydata(v, [], BOXF); me.update(); me.materials.append(m)
    o = link(bpy.data.objects.new(name, me))
    if parent is not None:
        o.parent = parent
    if loc is not None:
        o.location = loc
    return o


def multibox(name, boxes, parent, origin):
    """One mesh from many (a, b, material) boxes, origin at `origin` (parent space): fewer objects, faster build."""
    mats = []; verts = []; faces = []; fm = []
    for a, b, m in boxes:
        if m not in mats:
            mats.append(m)
        a = np.array(a, float) - origin; b = np.array(b, float) - origin
        base = len(verts)
        verts += [(x, y, z) for x in (a[0], b[0]) for y in (a[1], b[1]) for z in (a[2], b[2])]
        faces += [tuple(base + i for i in f) for f in BOXF]; fm += [mats.index(m)] * 6
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    for m in mats:
        me.materials.append(m)
    for p, i in zip(me.polygons, fm):
        p.material_index = i
    o = link(bpy.data.objects.new(name, me)); o.parent = parent; o.location = tuple(origin)
    return o


def key(o, f, loc=None, rot=None, sc=None):
    if loc is not None:
        o.location = loc; o.keyframe_insert("location", frame=f)
    if rot is not None:
        o.rotation_euler = rot; o.keyframe_insert("rotation_euler", frame=f)
    if sc is not None:
        o.scale = (sc,) * 3 if np.isscalar(sc) else sc; o.keyframe_insert("scale", frame=f)


def smooth(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


# ------------------------------------------------------------------ swings
# (tick, arm pitch, yaw, roll, tool tilt, reach m). Pitch 90 = straight ahead, >90 raised; yaw + = toward the left
# (- = right); roll twists the forearm; tilt leans the tool forward in the fist; reach moves the shoulder (+ forward).
REST = (96, 14, 0, 22, 0.0)
# take: (name, tool, build, keys, hit ticks, blade side, fixed twists, J's 803 take)
# blade side: +1 working edge on the tool's +X, -1 on -X, 0 both. fixed twists: [(from, to, degrees)] held turns.
SWINGS = {
    "A1a": ("Axe: straight overhead chop, bite, wrench free", "axe", "a",
            [(0, *REST), (4, 130, -4, 0, -14, -0.03), (7, 72, 2, 0, 80, 0.07), (9, 72, 2, 0, 80, 0.07),
             (10, 76, 2, 10, 74, 0.06), (13, *REST)], [7], -1, []),
    "A1b": ("Axe: two chops into one notch", "axe", "b",
            [(0, *REST), (3, 118, -20, -22, 10, -0.02), (6, 80, 14, 20, 70, 0.05), (8, 100, -10, -12, 30, 0.0),
             (10, 128, -24, -28, -8, -0.04), (13, 72, 20, 26, 78, 0.07), (15, 74, 20, 26, 76, 0.07), (18, *REST)], [6, 13], -1, []),
    "A1c": ("Axe: level felling swing", "axe", "c",
            [(0, *REST), (4, 100, -58, -80, 48, -0.04), (6, 100, -62, -82, 50, -0.05), (9, 96, 22, -80, 64, 0.07),
             (10, 96, 20, -80, 62, 0.06), (14, *REST)], [9], -1, []),
    "C1a": ("Sword combo: rising cut, chop, thrust", "sword", "a",
            [(0, *REST), (2, 72, 30, 30, 70, 0), (5, 124, -22, -28, 40, 0.04), (7, 138, -26, -34, -18, -0.03),
             (11, 60, 26, 30, 82, 0.08), (14, 92, 6, 0, 88, -0.22), (16, 93, 2, 0, 90, -0.24), (18, 93, 0, 0, 90, 0.34),
             (22, *REST)], [4, 10, 18], 0, [(13, 20, 90)]),
    "C1b": ("Sword combo: four-hit flurry", "sword", "b",
            [(0, *REST), (2, 112, -24, -25, 45, 0), (4, 84, 26, 30, 62, 0.03), (6, 110, 24, 30, 50, 0),
             (8, 84, -24, -25, 62, 0.03), (10, 114, -22, -25, 45, 0), (12, 82, 28, 30, 66, 0.04), (14, 108, 22, 30, 50, 0.02),
             (16, 86, -22, -25, 62, 0.04), (19, *REST)], [3, 7, 11, 15], 0, []),
    "C1c": ("Sword combo: slash, backhand, spinning sweep", "sword", "c",
            [(0, *REST), (2, 125, -18, -25, 40, 0), (5, 72, 32, 35, 70, 0.05), (7, 80, 40, 30, 60, 0),
             (10, 128, -25, -30, 45, 0.04), (12, 100, -60, -85, 60, -0.04), (14, 98, -66, -88, 62, -0.05),
             (17, 94, 56, -85, 62, 0.08), (19, 94, 58, -85, 62, 0.06), (23, *REST)], [4, 9, 16], 0, []),
    "C2a": ("Sword combo: thrust, then sweep out", "sword", "a",
            [(0, *REST), (3, 92, 8, 0, 88, -0.22), (4, 94, 4, 0, 90, -0.24), (6, 93, 0, 0, 90, 0.34), (8, 93, 0, 0, 90, 0.3),
             (10, 96, -45, -80, 60, 0), (13, 92, 50, -80, 60, 0.05), (17, *REST)], [6, 12], 0, [(1, 8, 90)]),
    "C2b": ("Sword combo: sweep, double stab", "sword", "b",
            [(0, *REST), (3, 96, -45, -80, 60, 0), (6, 92, 50, -80, 60, 0.05), (8, 92, 8, 0, 88, -0.18),
             (10, 93, 0, 0, 90, 0.3), (11, 93, 2, 0, 90, -0.12), (13, 93, 0, 0, 90, 0.34), (17, *REST)], [5, 10, 13], 0,
            [(8, 15, 90)]),
    "C2c": ("Sword combo: low sweep, rising thrust", "sword", "c",
            [(0, *REST), (3, 74, -45, -80, 64, 0), (6, 70, 48, -80, 66, 0.05), (9, 84, 10, 0, 92, -0.22),
             (11, 86, 4, 0, 94, -0.24), (14, 104, 0, 0, 92, 0.34), (16, 104, 0, 0, 92, 0.32), (20, *REST)], [5, 14], 0,
            [(8, 18, 90)]),
    "H1a": ("Hammer: snap overhead", "hammer3d", "a",
            [(0, *REST), (4, 136, -4, 0, -30, -0.05), (8, 58, 4, 0, 86, 0.08), (10, 60, 4, 0, 84, 0.07), (14, *REST)], [8], 0, []),
    "H1b": ("Heavy hammer: full wind-up smash", "hammer_big", "b",
            [(0, *REST), (6, 150, -8, 0, -50, -0.08), (11, 152, -8, 0, -56, -0.09), (15, 54, 4, 0, 88, 0.1),
             (16, 60, 4, 0, 82, 0.08), (17, 56, 4, 0, 86, 0.09), (22, *REST)], [15], 0, []),
    "H1c": ("Wedge hammer: tap, then smash", "hammer_wedge", "c",
            [(0, *REST), (3, 112, -4, 0, 20, 0), (6, 74, 2, 0, 80, 0.05), (8, 80, 2, 0, 72, 0.03),
             (11, 142, -6, 0, -38, -0.06), (14, 58, 4, 0, 86, 0.08), (16, 60, 4, 0, 84, 0.07), (20, *REST)], [6, 14], 1, []),
    "H2a": ("Hammer: backhand side swing", "hammer3d", "a",
            [(0, *REST), (5, 98, 48, 90, 30, 0), (8, 95, -40, 90, 60, 0.05), (9, 95, -36, 90, 58, 0.04), (13, *REST)], [8], 0, []),
    "H2b": ("Heavy hammer: side swing, follow through", "hammer_big", "b",
            [(0, *REST), (5, 100, -68, -90, 30, -0.04), (9, 96, 10, -90, 60, 0.06), (12, 92, 70, -90, 64, 0.04),
             (14, 94, 60, -90, 50, 0.02), (18, *REST)], [9], 0, []),
    "H2c": ("Wedge hammer: side swing, then uppercut", "hammer_wedge", "c",
            [(0, *REST), (4, 98, -60, -90, 30, 0), (7, 95, 36, -90, 60, 0.05), (9, 80, 10, -30, 90, 0),
             (11, 64, 4, 0, 110, -0.04), (14, 118, 2, 0, 60, 0.06), (15, 120, 2, 0, 58, 0.05), (19, *REST)], [7, 14], 1, []),
    "P1a": ("Pickaxe: quick mining taps", "pickaxe", "a",
            [(0, *REST), (2, 112, -4, 0, 10, 0), (4, 80, 2, 0, 72, 0.04), (6, 108, -4, 0, 14, 0), (8, 80, 2, 0, 72, 0.04),
             (10, 108, -4, 0, 14, 0), (12, 80, 2, 0, 72, 0.04), (15, *REST)], [4, 8, 12], 0, []),
    "P1b": ("Pickaxe: strike, pry, pull out", "pickaxe", "b",
            [(0, *REST), (4, 138, -6, 0, -18, -0.05), (9, 72, 4, 0, 78, 0.06), (11, 72, 4, 0, 78, 0.06),
             (13, 80, 4, 0, 58, 0.02), (14, 84, 4, 0, 52, 0.0), (17, *REST)], [9], 0, []),
    "P1c": ("Pickaxe: diagonal strike from the left", "pickaxe", "c",
            [(0, *REST), (4, 130, 30, 30, -10, -0.04), (8, 74, -14, -20, 76, 0.06), (9, 78, -12, -18, 70, 0.05), (13, *REST)],
            [8], 0, []),
    "S2a": ("Sword: tight shoulder diagonal", "sword", "a",
            [(0, *REST), (3, 134, -28, -35, -10, -0.03), (7, 64, 30, 30, 78, 0.08), (8, 62, 32, 30, 80, 0.08), (12, *REST)],
            [6], 0, []),
    "S2b": ("Sword: reverse diagonal", "sword", "b",
            [(0, *REST), (4, 138, 30, 35, -18, -0.05), (6, 140, 32, 38, -24, -0.06), (9, 62, -28, -30, 80, 0.08),
             (11, 58, -30, -32, 84, 0.08), (15, *REST)], [9], 0, []),
    "S2c": ("Sword: X cut", "sword", "c",
            [(0, *REST), (4, 140, -30, -35, -20, -0.05), (8, 62, 30, 30, 80, 0.08), (10, 130, 30, 35, -10, -0.03),
             (14, 62, -30, -30, 80, 0.08), (18, *REST)], [7, 13], 0, []),
    "S3a": ("Sword: high fast sweep pair", "sword", "a",
            [(0, *REST), (2, 104, -45, -80, 62, 0), (5, 102, 50, -80, 62, 0.04), (6, 104, 52, 100, 62, 0),
             (9, 104, -42, 100, 62, 0.04), (12, *REST)], [4, 8], 0, []),
    "S3b": ("Sword: stepping wide sweep pair", "sword", "b",
            [(0, *REST), (3, 96, -62, -80, 60, -0.05), (6, 92, 60, -80, 60, 0.12), (8, 94, 62, 100, 60, 0.02),
             (11, 94, -58, 100, 60, 0.14), (15, *REST)], [5, 10], 0, []),
    "S3c": ("Sword: three sweeps", "sword", "c",
            [(0, *REST), (2, 96, -45, -80, 60, 0), (4, 92, 50, -80, 60, 0.04), (5, 94, 52, 100, 60, 0),
             (8, 94, -45, 100, 60, 0.04), (9, 94, -46, -80, 60, 0), (12, 92, 50, -80, 60, 0.04), (16, *REST)], [3, 7, 11], 0, []),
    "S4a": ("Sword: quick flat jab", "sword", "a",
            [(0, *REST), (3, 92, 6, 0, 88, -0.12), (5, 93, 0, 0, 90, 0.3), (6, 93, 0, 0, 90, 0.28), (9, *REST)], [5], 0,
            [(1, 8, 0)]),
    "S4b": ("Sword: deep lunge", "sword", "b",
            [(0, *REST), (5, 96, 10, 0, 86, -0.3), (7, 98, 4, 0, 88, -0.32), (10, 88, 0, 0, 96, 0.46),
             (13, 88, 0, 0, 96, 0.44), (17, *REST)], [10], 0, [(2, 15, 90)]),
    "S4c": ("Sword: stab and twist out", "sword", "c",
            [(0, *REST), (4, 92, 8, 0, 88, -0.22), (6, 95, 2, 0, 90, -0.24), (8, 93, 0, 0, 90, 0.34), (12, 93, 0, 60, 90, 0.33),
             (14, 93, 0, 60, 90, 0.1), (17, *REST)], [8], 0, [(2, 8, 90), (9, 9, 120), (10, 10, 150), (11, 14, 180)]),
    "V1a": ("Shovel: scoop and toss right", "shovel", "a",
            [(0, *REST), (3, 86, 4, 0, 96, 0.04), (5, 80, 4, 0, 106, 0.24), (8, 88, 4, 0, 76, 0.18), (10, 108, -30, -20, 40, 0.04),
             (11, 112, -44, -30, 26, 0.02), (15, *REST)], [5], 0, [(0, 15, 90)]),
    "V1b": ("Shovel: stomp dig, lever back", "shovel", "b",
            [(0, *REST), (4, 112, 2, 0, 40, 0.0), (7, 74, 2, 0, 120, 0.12), (9, 74, 2, 0, 120, 0.14), (11, 84, 2, 0, 80, 0.1),
             (13, 104, 0, 0, 40, 0.04), (16, *REST)], [7], 0, [(0, 16, 90)]),
    "V1c": ("Shovel: two flat scrapes", "shovel", "c",
            [(0, *REST), (2, 90, 4, 0, 90, -0.04), (4, 82, 4, 0, 104, 0.24), (6, 92, 4, 0, 80, 0.06), (8, 90, 4, 0, 90, -0.04),
             (10, 82, 4, 0, 104, 0.26), (12, 100, 0, 0, 60, 0.04), (15, *REST)], [4, 10], 0, [(0, 15, 90)]),
}
# Thrusts: a sword held dead along the forearm hides behind the fist in first person, so every thrust key (no roll,
# arm near level, tool tilt 86+) cocks the blade up 16 deg in the fist and drops the arm 3 deg: the point still drives
# forward, and the blade reads above the knuckles.
for _tk, _v in SWINGS.items():
    if _v[1] == "sword":
        _v[3][:] = [(k[0], k[1] - 3, k[2], k[3], k[4] - 16, k[5]) if (k[3] == 0 and k[4] >= 86 and abs(k[2]) <= 10)
                    else k for k in _v[3]]
# Shovels: dug straight ahead, the flat blade hides under the forearm in first person, so the dig keys swing the arm
# 14 deg in toward the crosshair and 5 deg up: the blade goes in beside the fist, in view.
for _tk, _v in SWINGS.items():
    if _v[1] == "shovel":
        _v[3][:] = [k if k[1:] == REST else (k[0], k[1] + 5, k[2] + 14, k[3], k[4], k[5]) for k in _v[3]]
BUILD_NAME = {"a": "pixel stream", "b": "extrude", "c": "lock-in"}


def pose_at(keys, t):
    for (ta, *a), (tb, *b) in zip(keys, keys[1:]):
        if ta <= t <= tb:
            w = smooth((t - ta) / (tb - ta))
            return [x + (y - x) * w for x, y in zip(a, b)]
    return list(keys[-1][1:])


# ------------------------------------------------------------------ tool models -> (a, b, material) boxes, tool space
def tool_boxes(tool):
    out = []
    if tool.startswith("hammer"):
        def hb(a, b, m):
            out.append((np.array(a, float), np.array(b, float), m))
        if tool == "hammer3d":                     # 803's construct block hammer
            hb((-0.03, 0.0, -0.03), (0.03, 0.62, 0.03), GRIP)
            for y in (0.08, 0.2, 0.32, 0.44):
                hb((-0.04, y, -0.04), (0.04, y + 0.03, 0.04), GLOW)
            hb((-0.2, 0.58, -0.12), (0.2, 0.82, 0.12), GLASS); hb((-0.12, 0.64, -0.06), (0.12, 0.76, 0.06), GLOW)
            for sx in (-1, 1):
                hb((sx * 0.2 - 0.015, 0.57, -0.13), (sx * 0.2 + 0.015, 0.83, 0.13), RIM)
                hb((sx * 0.23 - 0.02, 0.6, -0.1), (sx * 0.23 + 0.02, 0.8, 0.1), GLASS)
            hb((-0.2, 0.82, -0.12), (0.2, 0.84, 0.12), RIM)
        elif tool == "hammer_big":                 # heavy: long haft, wide deep head, stepped faces, collar
            hb((-0.035, 0.0, -0.035), (0.035, 0.8, 0.035), GRIP)
            for y in (0.06, 0.18, 0.3, 0.42, 0.54):
                hb((-0.045, y, -0.045), (0.045, y + 0.03, 0.045), GLOW)
            hb((-0.07, 0.66, -0.07), (0.07, 0.72, 0.07), RIM)                       # collar
            hb((-0.26, 0.72, -0.16), (0.26, 1.04, 0.16), GLASS); hb((-0.16, 0.8, -0.08), (0.16, 0.96, 0.08), GLOW)
            for sx in (-1, 1):
                hb((sx * 0.26 - 0.015, 0.71, -0.17), (sx * 0.26 + 0.015, 1.05, 0.17), RIM)
                hb((sx * 0.29 - 0.03, 0.75, -0.13), (sx * 0.29 + 0.03, 1.01, 0.13), GLASS)
                hb((sx * 0.32 - 0.01, 0.78, -0.1), (sx * 0.32 + 0.01, 0.98, 0.1), RIM)
        else:                                      # wedge: flat striking face at +X, a tapering peen at -X
            hb((-0.03, 0.0, -0.03), (0.03, 0.64, 0.03), GRIP)
            for y in (0.1, 0.24, 0.38):
                hb((-0.04, y, -0.04), (0.04, y + 0.03, 0.04), GLOW)
            hb((-0.12, 0.6, -0.12), (0.2, 0.84, 0.12), GLASS); hb((-0.06, 0.66, -0.05), (0.14, 0.78, 0.05), GLOW)
            hb((0.2, 0.59, -0.13), (0.23, 0.85, 0.13), RIM)                          # striking face
            for x0, x1, h in ((-0.18, -0.12, 0.09), (-0.24, -0.18, 0.055), (-0.29, -0.24, 0.025)):
                hb((x0, 0.62 + (0.12 - h), -0.11), (x1, 0.82 - (0.12 - h), 0.11), GLASS)
            hb((-0.3, 0.68, -0.11), (-0.28, 0.76, 0.11), RIM)                         # wedge edge
        return out
    d = json.load(open(os.path.join(BB, f"construct_{tool}_green.bbmodel")))
    for e in d["elements"]:
        nm = e["name"]
        m = GRIP if nm.startswith("handle") else RIM if nm.startswith("glow_rim") else GLOW if nm.startswith("glow") else GLASS
        inf = float(e.get("inflate", 0) or 0) / 32.0
        out.append((np.array(e["from"], float) / 32.0 - inf, np.array(e["to"], float) / 32.0 + inf, m))
    return out


def ring_on_fist(tag, parent, end_z, px):
    """The jar's placement (831): on the punching face (at end_z, facing -Z), 1 px in from the back of the hand (+Y here),
    over the middle finger. Gold frame, green face standing out, a band over the back."""
    mt = link(bpy.data.objects.new(f"{tag} ring mount", None)); mt.parent = parent
    mt.location = (0, 0, end_z); mt.rotation_euler = (0, 0, R(90))           # +X (back of hand) -> +Y
    c = 0.6 * px
    box(f"{tag} ring band", (1.95 * px, -0.55 * px, 0), (2.25 * px, 0.55 * px, 1.4 * px), GOLDM, mt)
    box(f"{tag} ring frame", (c - 1.25 * px, -1.25 * px, -0.45 * px), (c + 1.25 * px, 1.25 * px, 0), GOLDM, mt)
    box(f"{tag} ring face", (c - 0.95 * px, -0.95 * px, -1.0 * px), (c + 0.95 * px, 0.95 * px, -0.4 * px), RINGM, mt)
    return Vector((0, c, end_z - 1.0 * px))                                   # ring face point, shoulder space


GRIP_LOC = Vector((0, -1.1 * PX, -10.6 * PX))      # the handle sits on the palm side, clear of the ring


def make_arm(tag, base):
    """Minecraft right arm in first person: a 4x12x4 px box from the shoulder, sleeve then skin, knuckles on the back
    (+Y), the ring on the punching face."""
    sh = link(bpy.data.objects.new(f"{tag} shoulder", None)); sh.location = base; sh.rotation_mode = "XYZ"
    box(f"{tag} sleeve", (-2 * PX, -2 * PX, -8 * PX), (2 * PX, 2 * PX, 0), SLEEVE, sh)
    box(f"{tag} hand", (-2 * PX, -2 * PX, -12 * PX), (2 * PX, 2 * PX, -8 * PX), SKIN, sh)
    box(f"{tag} knuckles", (-2.05 * PX, 1.2 * PX, -12.05 * PX), (2.05 * PX, 2.05 * PX, -11.1 * PX), SKIN, sh)
    ring_pt = ring_on_fist(tag, sh, -12 * PX, PX)
    grip = link(bpy.data.objects.new(f"{tag} grip", None)); grip.parent = sh
    grip.location = tuple(GRIP_LOC); grip.rotation_mode = "XYZ"
    return sh, grip, ring_pt


def arm_matrix(p, shoulder0):
    pitch, yaw, roll, tilt, reach = p
    e_ = Euler((R(pitch), 0, R(yaw)), "XYZ"); e_.rotate_axis("Z", R(roll))
    return e_, Matrix.Translation(shoulder0 + Vector((0, reach, 0))) @ e_.to_matrix().to_4x4()


def grip_matrix(tilt):
    return Matrix.Translation(GRIP_LOC) @ Matrix.Rotation(R(-tilt), 4, "X")


dump = {"format": "per take: per tick right-arm rotation (pitch, yaw, roll in degrees, pitch 90 = ahead), shoulder reach (m, + forward), tool tilt in the fist and tool twist about its length (the edge leads); 'hit' = the tick the tool connects; forming ticks 0-14 come first. 20 ticks a second.",
        "takes": {}}
BAY = 40.0
ORDER = list(SWINGS)
for bi, tk in enumerate(ORDER):
    name, tool, build, keys, hits, side, fixed = SWINGS[tk]
    tag = f"FT3 {tk} fp"                      # fp_prefix: the arm, ring and tool only
    wtag = f"FT3 {tk} world"
    bx = bi * BAY
    eye = Vector((bx, 0.0, 1.62))
    shoulder0 = eye + Vector((0.36, 0.12, -0.42))
    swing = keys[-1][0]
    total = FORM + 2 * swing + GAP + 10
    poses = []
    for t in range(total + 1):
        if t < FORM:
            p = list(REST)
        else:
            k = t - FORM
            if k <= swing:
                p = pose_at(keys, k)
            elif k <= swing + GAP:
                p = list(REST)
            elif k <= 2 * swing + GAP:
                p = pose_at(keys, k - swing - GAP)
            else:
                p = list(REST)
        poses.append(p)
    L_tip = 0.75
    mats_ = [arm_matrix(p, shoulder0)[1] @ grip_matrix(p[3]) for p in poses]
    tips = [m_ @ Vector((0, L_tip, 0)) for m_ in mats_]
    # the world ahead: floor, a backdrop wall (hides the next bay from the side camera), and a target that meets the
    # tool's tip at the first hit
    box(f"{wtag} floor", (bx - 6, -6, -0.02), (bx + 3.5, 10, 0), FLOOR)
    box(f"{wtag} backdrop", (bx - 6.2, -8, 0), (bx - 6, 12, 7), WALL)
    # the target meets the tool's REAL far end (its full length, not 0.75 m) at the first hit, on its near face, so the
    # blade / head stays in front of it and reads in first person; dummies are dark and only as tall as the hit needs
    span_ = max(float(b[1]) for _, b, _ in tool_boxes(tool))
    tip_hit = mats_[FORM + hits[0]] @ Vector((0, span_, 0))
    if tool in ("pickaxe", "shovel"):
        tz = max(0.25, tip_hit.z - 0.03)                       # the point / blade just bites the top face
        tgt = box(f"{wtag} block", (-0.45, 0, -tz), (0.45, 0.9, 0), DIRT if tool == "shovel" else STONE,
                  loc=(tip_hit.x, tip_hit.y - 0.12, tz))
        flash = box(f"{wtag} hit", (-0.12, -0.12, 0.0), (0.12, 0.12, 0.01), HIT, loc=(tip_hit.x, tip_hit.y, tz))
    else:
        ty = tip_hit.y + 0.03
        top = min(1.8, max(0.6, tip_hit.z + 0.2))
        tgt = box(f"{wtag} dummy", (-0.22, 0, 0), (0.22, 0.35, top), DUMMY, loc=(tip_hit.x, ty, 0))
        flash = box(f"{wtag} hit", (-0.18, -0.03, -0.18), (0.18, 0.0, 0.18), HIT,
                    loc=(tip_hit.x, ty, min(top - 0.2, max(0.25, tip_hit.z))))
    tgt.rotation_mode = "XYZ"
    sh, grip, ring_pt = make_arm(tag, shoulder0)
    root = link(bpy.data.objects.new(f"{tag} tool", None)); root.parent = grip; root.rotation_mode = "XYZ"
    ticks = []
    for t, p in enumerate(poses):
        pitch, yaw, roll, tilt, reach = p
        e_, _ = arm_matrix(p, shoulder0)
        sh.rotation_euler = e_; sh.keyframe_insert("rotation_euler", frame=t + 1)
        key(sh, t + 1, loc=tuple(shoulder0 + Vector((0, reach, 0))))
        key(grip, t + 1, rot=(R(-tilt), 0, 0))
        k_ = t - FORM
        hit_now = t >= FORM and (k_ in hits or (k_ - swing - GAP) in hits)
        ticks.append({"arm": [round(pitch, 2), round(yaw, 2), round(roll, 2)], "tool_tilt": round(tilt, 2),
                      "reach": round(reach, 3), "hit": hit_now})
        if t == 0 or hit_now or ticks[t - 1]["hit"]:
            flash.hide_render = not hit_now; flash.keyframe_insert("hide_render", frame=t + 1)
            flash.hide_viewport = not hit_now; flash.keyframe_insert("hide_viewport", frame=t + 1)
        if hit_now:
            if tool in ("pickaxe", "shovel"):
                key(tgt, t, sc=1.0); key(tgt, t + 1, sc=(1.03, 1.03, 0.97)); key(tgt, t + 3, sc=1.0)
            else:
                key(tgt, t, rot=(0, 0, 0)); key(tgt, t + 1, rot=(R(10), 0, 0)); key(tgt, t + 4, rot=(0, 0, 0))
    # the working edge leads: turn the tool about its length to face the tip's motion (analytic, no frame_set)
    phi_prev = 0.0
    for t in range(total + 1):
        k_ = t - FORM
        kk = k_ if k_ <= swing else k_ - swing - GAP
        fx = next((d for a_, b_, d in fixed if a_ <= kk <= b_ and t >= FORM), None)
        if fx is not None:
            phi = R(fx)
        else:
            v = tips[min(total, t + 1)] - tips[max(0, t - 1)]
            vg = mats_[t].to_3x3().inverted() @ v
            if math.hypot(vg.x, vg.z) > 0.004:
                phi = math.atan2(-vg.z, vg.x) if side >= 0 else math.atan2(vg.z, -vg.x)
                if side == 0:
                    alt = phi + math.pi
                    phi = min((phi, alt), key=lambda a: abs((a - phi_prev + math.pi) % (2 * math.pi) - math.pi))
            else:
                phi = phi_prev
        phi = phi_prev + ((phi - phi_prev + math.pi) % (2 * math.pi) - math.pi)
        phi = phi_prev + (phi - phi_prev) * 0.65 if fx is None else phi
        phi_prev = phi
        key(root, t + 1, rot=(0, phi, 0))
        ticks[t]["tool_twist"] = round(math.degrees(phi), 2)
    # the tool, in sections along its length (grip first)
    bxs = tool_boxes(tool)
    span = max(float(b[1]) for _, b, _ in bxs)
    NB = 7
    bands = [[] for _ in range(NB)]
    for a, b, m in bxs:
        bands[min(NB - 1, int(((a[1] + b[1]) / 2) / span * NB))].append((a, b, m))
    parts = []
    for k, bl in enumerate(bands):
        if not bl:
            continue
        lo = np.min([a for a, _, _ in bl], 0); hi = np.max([b for _, b, _ in bl], 0)
        c = (lo + hi) / 2
        parts.append((multibox(f"{tag} tool part {k}", bl, root, c), c))
    rng = np.random.default_rng(844 + bi)
    m_rest = grip_matrix(REST[3])                     # tool space -> shoulder space during forming (twist 0)
    if build == "a":                                  # pixel stream from the ring
        pm = bpy.data.meshes.new(f"{tag} px"); s_ = 0.022
        pm.from_pydata([(x, y, z) for x in (-s_, s_) for y in (-s_, s_) for z in (-s_, s_)], [], BOXF)
        pm.materials.append(PIX)
        for o, c in parts:
            f_arrive = 3 + int(round((c[1] / span) * (FORM - 5)))
            key(o, 1, sc=0.0001); key(o, f_arrive - 1, sc=0.0001); key(o, f_arrive + 1, sc=1.0)
            for j in range(3):
                px_ = link(bpy.data.objects.new(f"{tag} pixel", pm)); px_.parent = sh
                start = ring_pt + Vector(rng.uniform(-0.015, 0.015, 3))
                end = m_rest @ Vector(c + rng.uniform(-0.03, 0.03, 3))
                f0 = max(1, f_arrive - 4 + j - 1)
                key(px_, 1, loc=start, sc=0.0001); key(px_, f0, loc=start, sc=0.0001); key(px_, f0 + 1, loc=start, sc=1.0)
                key(px_, f0 + 3, loc=(start + end) / 2 + Vector((0, 0.03, -0.03)), sc=1.0)
                key(px_, f_arrive + 1, loc=end, sc=0.5); key(px_, f_arrive + 2, loc=end, sc=0.0001)
    elif build == "b":                                # extrude out of the fist behind a scan plate
        key(root, 1, sc=(1, 0.001, 1)); key(root, 3, sc=(1, 0.001, 1)); key(root, FORM, sc=(1, 1, 1))
        sp = box(f"{tag} scan plate", (-0.11, -0.006, -0.06), (0.11, 0.006, 0.06), SCAN, root)
        lo = min(float(a[0]) for a, _, _ in bxs); hi = max(float(b[0]) for _, b, _ in bxs)
        sw = (hi - lo) / 0.22 + 0.2                 # the plate is as wide as the tool, riding on its growing tip
        sp.location = ((hi + lo) / 2, span, 0)
        key(sp, 1, sc=0.0001); key(sp, 3, sc=(sw, 1, 1)); key(sp, FORM, sc=(sw, 1, 1)); key(sp, FORM + 2, sc=0.0001)
    else:                                             # lock-in: sections fly in from around the fist and snap
        for o, c in parts:
            f_lock = 4 + int(round((c[1] / span) * (FORM - 6)))
            off = Vector(rng.uniform(-1, 1, 3)); off.y = abs(off.y) * 0.5; off = off.normalized() * 0.35
            home = Vector(c)
            key(o, 1, loc=home + off, sc=0.0001); key(o, max(2, f_lock - 4), loc=home + off, sc=0.0001)
            key(o, max(3, f_lock - 3), loc=home + off, sc=0.6)
            key(o, f_lock, loc=home, sc=1.0)
            o.rotation_mode = "XYZ"
            key(o, max(3, f_lock - 3), rot=(R(rng.uniform(-60, 60)), R(rng.uniform(-60, 60)), R(rng.uniform(-60, 60))))
            key(o, f_lock, rot=(0, 0, 0))
    dump["takes"][tk] = {"name": name, "tool": tool, "build": BUILD_NAME[build], "forming_ticks": FORM, "swing_ticks": swing,
                         "hit_ticks": hits, "keys": [list(k) for k in keys], "ticks": ticks}
    # cameras: the eye (first person, 120 deg horizontal like J plays, crosshair), and from the right to read the arc
    c = cam(f"Cam {tk}", tuple(eye), tuple(eye + Vector((0, 3, -0.25))), 10.4)
    c.data.sensor_fit = "HORIZONTAL"; c.data.sensor_width = 36.0
    for nm_, a_, b_ in (("h", (-0.007, -0.0006, -0.2), (0.007, 0.0006, -0.2)), ("v", (-0.0006, -0.007, -0.2), (0.0006, 0.007, -0.2))):
        box(f"FT3 {tk} crosshair {nm_}", a_, b_, XH, c)
    cam(f"Cam {tk} side", tuple(eye + Vector((3.2, 0.9, 0.2))), tuple(eye + Vector((0.3, 0.6, -0.3))), 35)
    cu = bpy.data.curves.new("FT3 label " + tk, "FONT"); cu.body = f"{tk}  {name}  ({BUILD_NAME[build]})"
    cu.size = 0.16; cu.align_x = "CENTER"
    tl = link(bpy.data.objects.new("FT3 label " + tk, cu)); tl.location = (bx - 5.95, 0.6, 2.3); tl.rotation_euler = (R(90), 0, R(90))   # on the backdrop, beside the eye: side camera only
    tl.data.materials.append(GLOW)
    print(tk, name, "built:", total, "ticks; tip at first hit", tuple(round(x - y, 2) for x, y in zip(tip_hit, (bx, 0, 0))),
          flush=True)

with open(os.path.join(FOLDER, "combat", "fp_tools3_poses.json"), "w") as fh:
    json.dump(dump, fh, separators=(",", ":"))

scene.frame_start, scene.frame_end = 1, max(FORM + 2 * SWINGS[t][3][-1][0] + GAP + 11 for t in ORDER)
world = bpy.data.worlds.new("FT3 world"); world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.32, 0.42, 0.55, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.7
scene.world = world
sun = link(bpy.data.objects.new("FT3 sun", bpy.data.lights.new("FT3 sun", "SUN")))
sun.data.energy = 3.0; sun.rotation_euler = (R(45), R(-10), R(-30))
try:
    scene.render.engine = "BLENDER_EEVEE"
except Exception:
    scene.render.engine = "BLENDER_EEVEE_NEXT"
scene.render.resolution_x, scene.render.resolution_y = 1600, 900
try:
    scene.view_settings.view_transform = "Standard"
except Exception:
    pass
try:
    tree = bpy.data.node_groups.new("FT3 Glow", "CompositorNodeTree")
    tree.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    rl = tree.nodes.new("CompositorNodeRLayers"); go = tree.nodes.new("NodeGroupOutput")
    gl = tree.nodes.new("CompositorNodeGlare")
    if "Type" in gl.inputs:
        gl.inputs["Type"].default_value = "Bloom"
    for nm_, val in (("Size", 0.5), ("Strength", 0.4), ("Threshold", 1.0)):
        if nm_ in gl.inputs:
            gl.inputs[nm_].default_value = val
    tree.links.new(rl.outputs["Image"], gl.inputs["Image"]); tree.links.new(gl.outputs["Image"], go.inputs[0])
    scene.compositing_node_group = tree
except Exception as e:
    print("no glow:", e)
scene.camera = bpy.data.objects["Cam A1a"]
scene.frame_set(FORM + 8)
try:
    bpy.ops.outliner.orphans_purge(do_recursive=True)
except Exception:
    pass
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("saved", OUT)
