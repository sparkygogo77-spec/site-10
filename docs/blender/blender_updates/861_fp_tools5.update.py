# Pass 861: first-person tools, round 5 variations (rings/suits chat, 2026-10-15, range 800-899). Follows 852.
# J's 852 ratings (NEXT-ROUNDS "Added 2026-10-15 22:56"). Only the 15 new takes are here; 852 keeps its own takes
# (KEEP: P1b3, S2a1, S2b1, S2b2, S2c1, S3a1, S3a2, S3c2, S3c3; DROP: P1b1, P1c1, S2c3; the noted ones are changed in 852).
# J's sword direction carried from his KEEPs: heavy and slow with a short charge before the cut (a green charge shell
# over the blade, the ring flares); S2c1 is the speed floor, J: "this is good every sword strike needs a cooldown of
# some sort there is no spamming ... no faster than this, the charge should maybe be different per click as a mixup".
# So every cut here takes at least 4 ticks and hits are at least 10 ticks apart, and charges differ per cut.
# Mobs react on contact (knocked back and tilted at the hit frame, the heaviest hit knocks furthest).
# J's new pickaxe rule (on 852 P1c2/P1c3): "pickaxe should only mine in the crosshair" / "has to mine on center".
# Every pick take is solved so the striking spike tip sits on the crosshair at the hit (the arm's yaw and pitch at the
# hit key are corrected until the tip projects to the screen centre), the block's face is placed there, and the
# script projects the tip through the eye camera at the hit frame and prints the result (should be 0.500, 0.500).
# First-person rules as 852: 120 deg view with a crosshair, the ring on the punching face, the working edge leads.
#
# 1. No-note IMPROVEs (J's standing rule: "3 new variations each"); each keeps its parent's build family and forms
#    its own way:
#   P1b21 pickaxe: side-on strike from the right after a held wind-up, two-stage wrench of the head out
#         (forms: guide beam, then grows behind a bright edge with sparks, grip to tip, as P1b2)
#   P1b22 pickaxe: side-on strike from the left, head twisted out the other way and levered up
#         (forms: guide beam, then grows from the tip back to the fist behind the bright edge)
#   P1b23 pickaxe: low flat side swing with the head on its side, the head rolls up 90 deg to twist out
#         (forms: guide beam, the bright edge jumps out in three steps, a spark burst at each)
#   S2b31 sword: reverse diagonal, the blade rolls flat low right, charge at the hip, heavy flat return sweep, step in
#         (forms: ratchets out in four clicks, as S2b3)
#   S2b32 sword: reverse diagonal, the blade wraps up over the right shoulder, charge, chest-high flat return sweep
#         (forms: two heavy clicks, a rim flash on each)
#   S2b33 sword: long held charge, reverse diagonal bites and holds, low flat return sweep with a deep step that
#         carries past (forms: ratchets out tip first)
#   S2c21 sword: X cut at the S2c1 pace, a different charge before each cut, the blade rolls flat between,
#         reaches in on the second (forms: sections unfold out of the grip, as S2c2)
#   S2c22 sword: X cut, the blade spins over the head between, you step in on the second and back out
#         (forms: sections unfold in pairs from beside the haft)
#   S2c23 sword: mirrored X (high left first), a flick turn low, a longer charge, a step and the heavier second cut
#         (forms: sections telescope out of each other)
#   S3c11 sword: three alternating flat sweeps, the third after a long charge with a step, heaviest knock
#         (forms: sections fly in and lock, as S3c1)
#   S3c12 sword: three sweeps all right to left, the blade dips under between, the third charged with a step
#         (forms: sections stream in from beyond the tip)
#   S3c13 sword: three alternating sweeps, the charge grows each time (2, 3, 5 ticks), you sink into the last
#         (forms: sections fly in from behind the shoulder, tip first)
# 2. S3a3 sword sweep pair the same way, blade loops back overhead: J "could be used for another weapon maybe".
#    The same pattern (two sweeps right to left, the weapon looping back overhead between) with three other construct
#    weapons, each a solid 3D construct (glass shell, glowing core, bright edge), edge or head leading:
#   W1 construct axe, one hand: bearded bit, stepped wedge section; head-heavy, 4-tick charge, the bit leads
#   W2 construct maul, two hands: long haft, big stepped head; slowest, 6-tick charge, you sink on each hit
#   W3 construct glaive, two hands: long pole, single-edged curved blade; widest reach, the edge leads
#   (a glaive, not a spear: J on 808 "there is also already a spear in the game we should just use that new one")
#   (forms: pixel jet, tip first, as S3a3)
#
# Cameras: "Cam <take>" first person (120 deg, crosshair; on the stepping takes it moves with you), "Cam <take> side"
# third person from the right. Bays 80 m apart, each with a backdrop wall. Every take forms over ticks 0-14 (20 ticks a
# second), then swings twice with a 6-tick rest. Writes LanternLive\combat\fp_tools5_poses.json, builds
# LanternLive\combat\fp_tools5.blend.
import json, math, os
import bpy
import numpy as np
from mathutils import Matrix, Euler, Vector
from bpy_extras.object_utils import world_to_camera_view

R = math.radians
OUT = os.path.join(FOLDER, "combat", "fp_tools5.blend")
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
SCENE_NAME = "FP Tools 5"
old = bpy.data.scenes.get(SCENE_NAME)
if old:
    bpy.data.scenes.remove(old)
scene = bpy.data.scenes.new(SCENE_NAME)
col = scene.collection
scene.render.fps = 20
win = bpy.context.window
if win:
    win.scene = scene
FORM = 14                 # forming ticks
GAP = 6                   # rest ticks between the two swings
P = 1 / 16
PX = P * 1.05             # first-person pixel (as 803/844)


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


SKIN = mat("FT5 skin", (0.62, 0.42, 0.3)); SLEEVE = mat("FT5 sleeve", (0.04, 0.28, 0.12))
RINGM = mat("FT5 ring face", (0.02, 0.85, 0.15), emit=2.0); GOLDM = mat("FT5 ring gold", (0.95, 0.7, 0.2), rough=0.25, metal=1.0)
GLASS = mat("FT5 hard-light glass", (0.03, 0.45, 0.16), emit=0.8, alpha=0.62, rough=0.15)
GLOW = mat("FT5 construct glow", (0.05, 0.9, 0.22), emit=3.5)
RIM = mat("FT5 construct rim", (0.08, 1.0, 0.28), emit=4.5)
GRIP = mat("FT5 construct grip", (0.02, 0.2, 0.08), emit=0.6, rough=0.3)
PIX = mat("FT5 forming pixel", (0.06, 1.0, 0.28), emit=4.0)
SCAN = mat("FT5 scan plate", (0.05, 0.95, 0.25), emit=3.0, alpha=0.45)
BEAM = mat("FT5 guide beam", (0.04, 0.95, 0.22), emit=5.0, alpha=0.7)
CHG = mat("FT5 charge shell", (0.03, 0.8, 0.2), emit=2.2, alpha=0.28, rough=0.2)
WAVE = mat("FT5 shockwave", (0.04, 0.85, 0.2), emit=3.0, alpha=0.6)
XH = mat("FT5 crosshair", (0.85, 0.85, 0.85), emit=1.0)
FLOOR = mat("FT5 floor", (0.18, 0.2, 0.22), rough=0.9)
WALL = mat("FT5 backdrop", (0.24, 0.26, 0.3), rough=0.95)
STONE = mat("FT5 block", (0.32, 0.33, 0.35), rough=0.9)
DIRT = mat("FT5 dirt", (0.35, 0.24, 0.15), rough=0.95)
DUMMY = mat("FT5 dummy", (0.07, 0.11, 0.08), rough=0.85)
DUMMYH = mat("FT5 dummy head", (0.1, 0.16, 0.1), rough=0.85)
HIT = mat("FT5 hit flash", (0.04, 0.7, 0.18), emit=1.6, alpha=0.8)
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
    """One mesh from many (a, b, material) boxes, origin at `origin` (parent space)."""
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


def curve_at(pts, t):
    """[(tick, value)] -> value at tick t (smooth between points, held outside)."""
    if not pts:
        return 0.0
    if t <= pts[0][0]:
        return pts[0][1]
    for (ta, a), (tb, b) in zip(pts, pts[1:]):
        if ta <= t <= tb:
            return a + (b - a) * smooth((t - ta) / (tb - ta))
    return pts[-1][1]




# ------------------------------------------------------------------ swings
# (tick, arm pitch, yaw, roll, tool tilt, reach m). Pitch 90 = straight ahead, >90 raised; yaw + = toward the left
# (- = right); roll twists the forearm; tilt leans the tool forward in the fist; reach moves the shoulder (+ forward).
REST = (96, 14, 0, 22, 0.0)
T = {}


def take(code, name, tool, build, keys, hits, fixed=(), charge=(), main=None, plays=2, knock=0.6, knocks=(), body=(),
         hop=(), parent=None, note="", aim=(), lefty=None):
    T[code] = dict(name=name, tool=tool, build=build, keys=[(0, *REST)] + [tuple(k) for k in keys], hits=hits,
                   fixed=list(fixed), charge=list(charge), main=hits[0] if main is None else main, plays=plays,
                   knock=knock, knocks=list(knocks), body=list(body), hop=list(hop), parent=parent, note=note,
                   aim=list(aim), lefty=lefty)


NN = "no note: 3 new variations (J's standing rule)"
PK = ("no note: 3 new variations; J's pickaxe rule (852 P1c2/P1c3): \"pickaxe should only mine in the crosshair\" / "
      "\"has to mine on center\"")
WN = "\"could be used for another weapon maybe\" (on 852 S3a3)"
# ---- P1b2 pickaxe side-on strike, twist the head out (extrude: guide beam + bright edge). The hit key (and its hold)
#      is re-aimed by the solver below so the striking spike tip lands on the crosshair.
take("P1b21", "Pickaxe: side-on strike from the right, two-stage wrench out", "pickaxe", "b2",
     [(4, 128, -24, -40, -10, -0.04), (7, 130, -26, -42, -12, -0.05), (11, 74, 6, -12, 78, 0.06), (13, 74, 6, -12, 78, 0.06),
      (15, 76, 6, 20, 74, 0.04), (17, 78, 6, 50, 66, 0.02), (19, 86, 6, 50, 50, 0.0), (23, *REST)], [11], aim=[11, 13],
     parent="P1b2", note=PK)
take("P1b22", "Pickaxe: side-on strike from the left, twist the other way, lever up", "pickaxe", "b2r",
     [(4, 124, 30, 40, -6, -0.04), (7, 126, 31, 42, -8, -0.05), (10, 74, 2, 14, 78, 0.06), (12, 74, 2, 14, 78, 0.06),
      (14, 74, 2, -30, 74, 0.04), (16, 92, 2, -30, 52, -0.02), (20, *REST)], [10], aim=[10, 12], parent="P1b2", note=PK)
take("P1b23", "Pickaxe: low flat side swing, the head rolls up to twist out", "pickaxe", "b2s",
     [(4, 92, -46, -80, 60, -0.04), (7, 92, -48, -80, 60, -0.05), (10, 86, 4, -80, 74, 0.08), (12, 86, 4, -80, 74, 0.08),
      (14, 86, 4, 10, 74, 0.06), (16, 90, 0, 10, 50, -0.02), (20, *REST)], [10], aim=[10, 12], parent="P1b2", note=PK)
# ---- S2b3 sword reverse diagonal, then a heavy flat return sweep (extrude: ratchet). S2c1 pace: every cut 4+ ticks,
#      hits 10+ ticks apart, a different charge before each cut.
take("S2b31", "Sword: reverse diagonal, roll flat low right, charge, heavy flat return with a step", "sword", "b3",
     [(4, 140, 30, 36, -20, -0.06), (8, 141, 31, 37, -22, -0.07), (12, 62, -28, -30, 80, 0.1), (14, 60, -32, -32, 82, 0.08),
      (16, 84, -52, -80, 62, -0.04), (19, 84, -53, -80, 62, -0.05), (23, 88, 46, -80, 62, 0.16), (25, 88, 54, -80, 60, 0.12),
      (29, *REST)], [11, 21], charge=[(4, 8), (16, 19)], body=[(0, 0.0), (17, 0.0), (22, 0.35), (25, 0.35), (29, 0.0)],
     knocks=[0.7, 1.3], parent="S2b3", note=NN)
take("S2b32", "Sword: reverse diagonal, wrap up over the right shoulder, charge, chest-high flat return", "sword", "b3t",
     [(4, 138, 30, 36, -18, -0.06), (7, 139, 31, 37, -20, -0.07), (11, 64, -26, -30, 80, 0.1), (13, 60, -30, -32, 82, 0.08),
      (16, 130, -40, -60, 10, -0.04), (19, 131, -41, -61, 8, -0.05), (21, 100, -40, -80, 62, 0.0), (25, 100, 48, -80, 62, 0.12),
      (27, 100, 56, -80, 60, 0.1), (31, *REST)], [10, 23], charge=[(4, 7), (16, 19)], knocks=[0.7, 1.2], parent="S2b3",
     note=NN)
take("S2b33", "Sword: long charge, reverse diagonal bites and holds, low flat return with a deep step", "sword", "b3r",
     [(4, 142, 32, 38, -24, -0.08), (10, 143, 33, 39, -26, -0.09), (14, 66, -24, -28, 78, 0.1), (16, 66, -24, -28, 78, 0.1),
      (20, 76, -48, -80, 66, -0.02), (25, 76, 48, -80, 66, 0.2), (27, 78, 58, -80, 64, 0.16), (31, *REST)], [13, 23],
     charge=[(4, 10)], body=[(0, 0.0), (20, 0.0), (25, 0.6), (28, 0.6), (31, 0.0)], knocks=[0.5, 1.4], parent="S2b3",
     note=NN)
# ---- S2c2 sword X cut, blade turns between, steps in on the second (lock-in: unfold out of the grip)
take("S2c21", "Sword: X at the S2c1 pace, a different charge per cut, blade rolls flat between, reaches in", "sword", "c2",
     [(4, 140, -30, -35, -20, -0.06), (6, 141, -30, -36, -22, -0.07), (10, 62, 30, 30, 80, 0.1), (12, 92, 40, 90, 40, 0.02),
      (15, 130, 30, 36, -12, -0.02), (19, 131, 31, 37, -14, -0.03), (23, 62, -30, -30, 80, 0.2), (25, 58, -34, -32, 82, 0.16),
      (29, *REST)], [9, 22], charge=[(4, 6), (15, 19)], knocks=[0.6, 1.0], parent="S2c2", note=NN)
take("S2c22", "Sword: X cut, the blade circles over the head between, step in and back out", "sword", "c2p",
     [(4, 138, -28, -34, -16, -0.04), (7, 139, -29, -35, -18, -0.05), (11, 62, 30, 30, 80, 0.08), (13, 130, 50, 60, 10, 0.0),
      (15, 162, 10, 0, -30, -0.02), (17, 134, 32, 40, -14, 0.0), (18, 135, 33, 41, -16, -0.01), (22, 60, -32, -32, 82, 0.1),
      (24, 58, -36, -34, 84, 0.08), (28, *REST)], [10, 21], charge=[(4, 7), (17, 18)],
     body=[(0, 0.0), (16, 0.0), (21, 0.5), (24, 0.5), (28, 0.0)], knocks=[0.6, 1.1], parent="S2c2", note=NN)
take("S2c23", "Sword: mirrored X, a flick turn low, longer charge, step into a heavier second cut", "sword", "c2t",
     [(4, 138, 30, 36, -18, -0.04), (7, 139, 31, 37, -20, -0.05), (11, 62, -28, -30, 80, 0.08), (13, 70, -34, -60, 70, 0.0),
      (15, 136, -30, -36, -16, -0.02), (21, 138, -31, -37, -20, -0.05), (25, 60, 32, 32, 82, 0.22), (27, 56, 36, 34, 86, 0.18),
      (31, *REST)], [10, 24], charge=[(4, 7), (15, 21)], body=[(0, 0.0), (20, 0.0), (25, 0.45), (28, 0.45), (31, 0.0)],
     knocks=[0.6, 1.4], parent="S2c2", note=NN)
# ---- S3c1 sword three sweeps, the last charged and heaviest (lock-in: fly in and lock)
take("S3c11", "Sword: three alternating flat sweeps, the third after a long charge with a step", "sword", "c1",
     [(3, 96, -50, -80, 60, -0.04), (5, 96, -52, -80, 60, -0.05), (9, 92, 50, -80, 60, 0.08), (11, 94, 56, 100, 60, 0.04),
      (14, 95, 57, 100, 60, 0.03), (19, 94, -48, 100, 60, 0.1), (21, 94, -54, -80, 60, 0.0), (23, 96, -56, -80, 60, -0.05),
      (29, 97, -57, -80, 60, -0.07), (34, 92, 54, -80, 60, 0.2), (36, 92, 60, -80, 58, 0.16), (40, *REST)], [7, 17, 32],
     charge=[(3, 5), (11, 14), (23, 29)], body=[(0, 0.0), (29, 0.0), (34, 0.5), (37, 0.5), (40, 0.0)],
     knocks=[0.5, 0.5, 1.8], parent="S3c1", note=NN)
take("S3c12", "Sword: three sweeps all right to left, the blade dips under between, the third charged", "sword", "c1s",
     [(3, 98, -52, -80, 60, -0.04), (5, 98, -53, -80, 60, -0.05), (9, 94, 50, -80, 60, 0.08), (12, 64, 10, -80, 90, -0.22),
      (15, 98, -54, -80, 60, -0.04), (16, 98, -55, -80, 60, -0.05), (20, 94, 50, -80, 60, 0.08), (23, 64, 10, -80, 90, -0.22),
      (26, 98, -56, -80, 60, -0.05), (32, 99, -57, -80, 60, -0.07), (37, 92, 54, -80, 60, 0.2), (39, 92, 60, -80, 58, 0.16),
      (43, *REST)], [7, 18, 35], charge=[(3, 5), (15, 16), (26, 32)],
     body=[(0, 0.0), (32, 0.0), (37, 0.5), (40, 0.5), (43, 0.0)], knocks=[0.5, 0.6, 1.8], parent="S3c1", note=NN)
take("S3c13", "Sword: three alternating sweeps, the charge grows each time, sink into the last", "sword", "c1b",
     [(3, 90, -50, -80, 60, -0.04), (5, 90, -51, -80, 60, -0.05), (9, 88, 50, -80, 60, 0.08), (11, 96, 54, 100, 60, 0.04),
      (14, 97, 55, 100, 60, 0.03), (19, 98, -48, 100, 60, 0.1), (21, 110, -54, 0, 50, 0.0), (23, 120, -56, -60, 40, -0.04),
      (28, 121, -57, -61, 38, -0.06), (33, 86, 50, -80, 66, 0.14), (35, 84, 56, -80, 66, 0.1), (39, *REST)], [7, 17, 31],
     charge=[(3, 5), (11, 14), (23, 28)], hop=[(0, 0.0), (28, 0.0), (31, -0.2), (34, -0.2), (39, 0.0)],
     knocks=[0.5, 0.6, 1.7], parent="S3c1", note=NN)
# ---- S3a3's move on other construct weapons: two sweeps right to left, the weapon loops back overhead between
take("W1", "Construct axe: sweep pair the same way, the axe loops back overhead", "axe3d", "a3",
     [(4, 104, -56, -80, 62, -0.05), (8, 105, -57, -80, 62, -0.06), (12, 98, 50, -80, 62, 0.12), (15, 148, 12, -40, 8, 0.0),
      (18, 108, -58, -80, 62, -0.04), (19, 108, -59, -80, 62, -0.05), (23, 98, 50, -80, 62, 0.14), (25, 98, 58, -80, 60, 0.1),
      (29, *REST)], [10, 21], charge=[(4, 8), (18, 19)], knocks=[0.9, 1.1], parent="S3a3", note=WN)
take("W2", "Construct maul, two hands: sweep pair the same way, the maul loops back overhead", "maul", "a3",
     [(5, 104, -58, -80, 62, -0.06), (11, 105, -59, -80, 62, -0.07), (16, 96, 44, -80, 64, 0.1), (18, 94, 54, -80, 62, 0.06),
      (22, 150, 14, -40, 6, -0.02), (26, 108, -58, -80, 62, -0.06), (29, 108, -59, -80, 62, -0.07), (34, 96, 44, -80, 64, 0.12),
      (36, 94, 54, -80, 62, 0.08), (41, *REST)], [14, 32], charge=[(5, 11), (26, 29)],
     hop=[(0, 0.0), (12, 0.0), (14, -0.12), (17, -0.1), (21, 0.0), (30, 0.0), (32, -0.14), (35, -0.12), (40, 0.0)],
     knocks=[1.3, 1.6], parent="S3a3", note=WN, lefty=-0.22)
take("W3", "Construct glaive, two hands: sweep pair the same way, the glaive loops back overhead", "glaive", "a3",
     [(4, 100, -62, -80, 64, -0.04), (8, 101, -63, -80, 64, -0.05), (12, 98, 56, -80, 64, 0.14), (15, 152, 8, -40, 6, 0.0),
      (18, 102, -62, -80, 64, -0.04), (20, 103, -63, -80, 64, -0.05), (24, 98, 56, -80, 64, 0.16), (26, 98, 64, -80, 62, 0.12),
      (30, *REST)], [10, 22], charge=[(4, 8), (18, 20)], knocks=[1.0, 1.2], parent="S3a3", note=WN, lefty=-0.34)

BUILD_NAME = {"a3": "pixel jet, tip first (as S3a3)",
              "b2": "guide beam, then grows grip to tip behind a bright edge with sparks (as P1b2)",
              "b2r": "guide beam, then grows tip back to the fist behind the bright edge",
              "b2s": "guide beam, the bright edge jumps out in three steps with a spark burst each",
              "b3": "ratchets out in four clicks (as S2b3)", "b3t": "two heavy clicks, a rim flash on each",
              "b3r": "ratchets out tip first",
              "c2": "sections unfold out of the grip (as S2c2)", "c2p": "sections unfold in pairs from beside the haft",
              "c2t": "sections telescope out of each other",
              "c1": "sections fly in and lock (as S3c1)", "c1s": "sections stream in from beyond the tip",
              "c1b": "sections fly in from behind the shoulder, tip first"}
ONE_SIDED = ("axe3d", "glaive")
LEFT_SH = Vector((-0.36, 0.12, -0.42))


def pose_at(keys, t):
    for (ta, *a), (tb, *b) in zip(keys, keys[1:]):
        if ta <= t <= tb:
            w = smooth((t - ta) / (tb - ta))
            return [x + (y - x) * w for x, y in zip(a, b)]
    return list(keys[-1][1:])


# ------------------------------------------------------------------ tool models -> (a, b, material) boxes, tool space
# Tool space: +Y along the tool from the fist, X across (the working edge or face is on X), Z thickness.
def tool_boxes(tool):
    out = []

    def hb(a, b, m):
        out.append((np.array(a, float), np.array(b, float), m))
    if tool == "axe3d":                         # one-hand construct axe: bearded bit on +X, stepped wedge section
        hb((-0.025, -0.06, -0.025), (0.025, 0.74, 0.025), GLASS); hb((-0.012, -0.04, -0.012), (0.012, 0.7, 0.012), GLOW)
        hb((-0.029, -0.06, -0.029), (0.029, 0.1, 0.029), GRIP)
        for y in (0.06, 0.2, 0.34):
            hb((-0.032, y, -0.032), (0.032, y + 0.03, 0.032), GLOW)
        hb((-0.065, 0.5, -0.048), (0.065, 0.78, 0.048), GLASS)              # socket
        hb((-0.04, 0.54, -0.03), (0.04, 0.74, 0.03), GLOW)                  # core seen through the glass
        hb((0.065, 0.49, -0.036), (0.14, 0.79, 0.036), GLASS)               # wedge steps thin toward the edge
        hb((0.14, 0.45, -0.026), (0.22, 0.81, 0.026), GLASS)
        hb((0.22, 0.4, -0.016), (0.285, 0.83, 0.016), GLASS)
        hb((0.08, 0.56, -0.012), (0.24, 0.72, 0.012), GLOW)                 # inner glow plate
        hb((0.285, 0.4, -0.011), (0.3, 0.83, 0.011), RIM)                   # the bit's edge
        hb((0.16, 0.38, -0.016), (0.285, 0.4, 0.016), RIM)                  # beard hook
        hb((-0.12, 0.57, -0.04), (-0.065, 0.71, 0.04), GLASS)               # poll
        hb((-0.11, 0.6, -0.025), (-0.07, 0.68, 0.025), GLOW)
        hb((-0.032, 0.78, -0.032), (0.032, 0.82, 0.032), RIM)               # cap
        return out
    if tool == "maul":                          # two-hand construct maul: long haft, big stepped head, faces on +-X
        hb((-0.03, -0.32, -0.03), (0.03, 0.9, 0.03), GLASS); hb((-0.016, -0.3, -0.016), (0.016, 0.86, 0.016), GLOW)
        hb((-0.034, -0.3, -0.034), (0.034, 0.06, 0.034), GRIP)
        hb((-0.045, -0.34, -0.045), (0.045, -0.28, 0.045), GLOW)            # pommel
        for y in (-0.1, 0.12, 0.34, 0.56):
            hb((-0.04, y, -0.04), (0.04, y + 0.035, 0.04), GLOW)
        hb((-0.07, 0.8, -0.07), (0.07, 0.87, 0.07), RIM)                    # collar
        hb((-0.2, 0.86, -0.14), (0.2, 1.16, 0.14), GLASS)                   # head block
        hb((-0.15, 0.9, -0.08), (0.15, 1.12, 0.08), GLOW)                   # core
        for sx in (-1, 1):
            hb((sx * 0.2, 0.88, -0.115), (sx * 0.25, 1.14, 0.115), GLASS)   # stepped face plates
            hb((sx * 0.25, 0.91, -0.09), (sx * 0.272, 1.11, 0.09), RIM)     # striking face
        for y in (0.86, 1.14):
            hb((-0.205, y - 0.008, -0.145), (0.205, y + 0.008, 0.145), RIM)  # bands round the head (every edge face)
        return [(np.minimum(a, b), np.maximum(a, b), m) for a, b, m in out]
    if tool == "glaive":                        # two-hand construct glaive: long pole, one curved edge on +X
        hb((-0.022, -0.42, -0.022), (0.022, 1.14, 0.022), GLASS); hb((-0.011, -0.4, -0.011), (0.011, 1.1, 0.011), GLOW)
        hb((-0.026, -0.42, -0.026), (0.026, 0.06, 0.026), GRIP)
        hb((-0.034, -0.44, -0.034), (0.034, -0.38, 0.034), GLOW)
        for y in (-0.2, 0.1, 0.4, 0.7, 0.95):
            hb((-0.03, y, -0.03), (0.03, y + 0.03, 0.03), GLOW)
        hb((-0.045, 1.08, -0.04), (0.045, 1.15, 0.04), RIM)                 # collar
        ws = [0.07, 0.1, 0.12, 0.13, 0.13, 0.115, 0.09, 0.055]
        for i, w in enumerate(ws):
            y0 = 1.14 + 0.072 * i; x0 = -0.035 + 0.008 * i
            hb((x0, y0, -0.019), (x0 + w, y0 + 0.073, 0.019), GLASS)
            hb((x0 + 0.012, y0, -0.009), (x0 + 0.012 + w * 0.5, y0 + 0.073, 0.009), GLOW)
            hb((x0 + w, y0, -0.009), (x0 + w + 0.013, y0 + 0.073, 0.009), RIM)
        hb((0.02, 1.715, -0.012), (0.075, 1.75, 0.012), RIM)                # tip
        return out
    d = json.load(open(os.path.join(BB, f"construct_{tool}_green.bbmodel")))
    for e in d["elements"]:
        nm = e["name"]
        m = GRIP if nm.startswith("handle") else RIM if nm.startswith("glow_rim") else GLOW if nm.startswith("glow") else GLASS
        inf = float(e.get("inflate", 0) or 0) / 32.0
        out.append((np.array(e["from"], float) / 32.0 - inf, np.array(e["to"], float) / 32.0 + inf, m))
    return out


def strike_local(tool, span, sgn):
    """The point that does the work, in tool space before the twist (sgn = which X side leads)."""
    if tool == "pickaxe":                       # spike tips of the construct pick (bbmodel glow_rim_69 / 70)
        return Vector((-0.266 if sgn < 0 else 0.281, 0.664, 0.008))
    if tool == "axe3d":
        return Vector((0.3, 0.62, 0.0))
    if tool == "maul":
        return Vector((0.272 * sgn, 1.01, 0.0))
    if tool == "glaive":
        return Vector((0.13, 1.4, 0.0))
    return Vector((0, span, 0))


def ring_on_fist(tag, parent, end_z, px):
    """The jar's placement: on the punching face, 1 px in from the back of the hand, over the middle finger."""
    mt = link(bpy.data.objects.new(f"{tag} ring mount", None)); mt.parent = parent
    mt.location = (0, 0, end_z); mt.rotation_euler = (0, 0, R(90))
    c = 0.6 * px
    box(f"{tag} ring band", (1.95 * px, -0.55 * px, 0), (2.25 * px, 0.55 * px, 1.4 * px), GOLDM, mt)
    box(f"{tag} ring frame", (c - 1.25 * px, -1.25 * px, -0.45 * px), (c + 1.25 * px, 1.25 * px, 0), GOLDM, mt)
    box(f"{tag} ring face", (c - 0.95 * px, -0.95 * px, -1.0 * px), (c + 0.95 * px, 0.95 * px, -0.4 * px), RINGM, mt)
    return Vector((0, c, end_z - 1.0 * px))


GRIP_LOC = Vector((0, -1.1 * PX, -10.6 * PX))
SH_LOCAL = Vector((0.36, 0.12, -0.42))          # shoulder from the eye


def make_arm(tag, parent):
    sh = link(bpy.data.objects.new(f"{tag} shoulder", None)); sh.parent = parent; sh.location = SH_LOCAL
    sh.rotation_mode = "XYZ"
    box(f"{tag} sleeve", (-2 * PX, -2 * PX, -8 * PX), (2 * PX, 2 * PX, 0), SLEEVE, sh)
    box(f"{tag} hand", (-2 * PX, -2 * PX, -12 * PX), (2 * PX, 2 * PX, -8 * PX), SKIN, sh)
    box(f"{tag} knuckles", (-2.05 * PX, 1.2 * PX, -12.05 * PX), (2.05 * PX, 2.05 * PX, -11.1 * PX), SKIN, sh)
    ring_pt = ring_on_fist(tag, sh, -12 * PX, PX)
    grip = link(bpy.data.objects.new(f"{tag} grip", None)); grip.parent = sh
    grip.location = tuple(GRIP_LOC); grip.rotation_mode = "XYZ"
    return sh, grip, ring_pt


def arm_matrix(p):
    pitch, yaw, roll, tilt, reach = p
    e_ = Euler((R(pitch), 0, R(yaw)), "XYZ"); e_.rotate_axis("Z", R(roll))
    return e_, Matrix.Translation(SH_LOCAL + Vector((0, reach, 0))) @ e_.to_matrix().to_4x4()


def grip_matrix(tilt):
    return Matrix.Translation(GRIP_LOC) @ Matrix.Rotation(R(-tilt), 4, "X")


def eye_angles(v):
    """eye-space vector -> (deg right of the crosshair, deg above it); the eye camera looks 4.8 deg down."""
    h = math.degrees(math.atan2(v.x, v.y))
    vv = math.degrees(math.atan2(v.z, math.hypot(v.x, v.y))) + 4.76
    return round(h, 1), round(vv, 1)



def kk_factory(swing, plays):
    def kk_of(t):
        """tick t -> tick within the swing being played (None while forming or resting)."""
        if t < FORM:
            return None
        k = t - FORM
        for pl in range(plays):
            s0 = pl * (swing + GAP)
            if s0 <= k <= s0 + swing:
                return k - s0
        return None
    return kk_of


def twist_series(mats_, offs, kk_of, fixed, total, one_sided):
    """The working edge leads: turn the tool about its length (Y) so +X faces the tip's motion (either side for a
    two-edged tool; always +X for the axe bit and the glaive edge)."""
    tips = [m_ @ Vector((0, 0.75, 0)) for m_ in mats_]
    phis = []; phi_prev = 0.0
    for t in range(total + 1):
        k_ = kk_of(t)
        fx = None if k_ is None else next((dd for a_, b_, dd in fixed if a_ <= k_ <= b_), None)
        if fx is not None:
            phi = R(fx)
        else:
            v = tips[min(total, t + 1)] - tips[max(0, t - 1)]
            vg = mats_[t].to_3x3().inverted() @ v
            if math.hypot(vg.x, vg.z) > 0.004:
                phi = math.atan2(-vg.z, vg.x)
                if not one_sided:
                    alt = phi + math.pi
                    phi = min((phi, alt), key=lambda a: abs((a - phi_prev + math.pi) % (2 * math.pi) - math.pi))
            else:
                phi = phi_prev
        phi = phi_prev + ((phi - phi_prev + math.pi) % (2 * math.pi) - math.pi)
        phi = phi_prev + (phi - phi_prev) * 0.65 if fx is None else phi
        phi_prev = phi
        phis.append(phi)
    return phis


def solve(S):
    keys, plays = S["keys"], S["plays"]
    swing = keys[-1][0]
    total = FORM + plays * swing + (plays - 1) * GAP + 10
    kk_of = kk_factory(swing, plays)
    poses = [list(REST) if kk_of(t) is None else pose_at(keys, kk_of(t)) for t in range(total + 1)]
    mats_ = [arm_matrix(p)[1] @ grip_matrix(p[3]) for p in poses]
    bpts, hop = S["body"], S["hop"]

    def body_off(t):
        k = kk_of(t)
        if k is None:
            k = 0 if t < FORM else swing
        return Vector((0, curve_at(bpts, k) if bpts else 0.0, curve_at(hop, k) if hop else 0.0))
    offs = [body_off(t) for t in range(total + 1)]
    phis = twist_series(mats_, offs, kk_of, S["fixed"], total, S["tool"] in ONE_SIDED)
    return swing, total, kk_of, poses, mats_, offs, phis


def strike_eye(S, mats_, phis, t, span):
    """Eye-space point of the striking end at tick t; for the pick, whichever spike leads the motion."""
    tool = S["tool"]
    rot = lambda t_: Matrix.Rotation(phis[t_], 4, "Y")
    if tool in ("pickaxe", "maul"):
        cands = [strike_local(tool, span, s) for s in (-1, 1)]
        cen = mats_[t] @ rot(t) @ Vector((0, cands[0].y, 0))
        prev = mats_[max(0, t - 2)] @ rot(max(0, t - 2)) @ Vector((0, cands[0].y, 0))
        mv = cen - prev
        best = max(cands, key=lambda c: (mats_[t] @ rot(t) @ c - cen).dot(mv))
        return mats_[t] @ rot(t) @ best, best
    c = strike_local(tool, span, 1)
    return mats_[t] @ rot(t) @ c, c


dump = {"format": "per take: per tick right-arm rotation (pitch, yaw, roll in degrees, pitch 90 = ahead), shoulder reach "
                  "(m, + forward), tool tilt and twist, body offset (m: forward, up); 'hit' = the tick the tool connects; "
                  "forming ticks 0-14 come first. 20 ticks a second.", "takes": {}}
BAY = 80.0
ORDER = list(T)
MODEL_AT = {}
CHECK = {}
for bi, tk in enumerate(ORDER):
    S = T[tk]
    name, tool, build, hits = S["name"], S["tool"], S["build"], S["hits"]
    bxs = tool_boxes(tool)
    span = max(float(b[1]) for _, b, _ in bxs)
    lo_y = min(float(a[1]) for a, _, _ in bxs)
    # ---- J's pickaxe rule: re-aim the hit keys until the striking spike tip sits on the crosshair
    if tool == "pickaxe":
        for it in range(30):
            swing, total, kk_of, poses, mats_, offs, phis = solve(S)
            tp, _ = strike_eye(S, mats_, phis, FORM + S["main"], span)
            h, vv = eye_angles(tp)
            h = math.degrees(math.atan2(tp.x, tp.y)); vv = math.degrees(math.atan2(tp.z, math.hypot(tp.x, tp.y))) + 4.764
            if abs(h) < 0.05 and abs(vv) < 0.05:
                break
            for i, k in enumerate(S["keys"]):
                if k[0] in S["aim"]:
                    S["keys"][i] = (k[0], k[1] - 0.8 * vv, k[2] + 0.8 * h, *k[3:])
        S["aim_err"] = (round(h, 2), round(vv, 2))
    swing, total, kk_of, poses, mats_, offs, phis = solve(S)
    keys, plays = S["keys"], S["plays"]
    tag = f"FT5 {tk} fp"
    wtag = f"FT5 {tk} world"
    bx = bi * BAY
    eye0 = Vector((bx, 0.0, 1.62))
    long_bay = bool(S["body"]) and max(v for _, v in S["body"]) > 2
    t_main = FORM + S["main"]
    strike_w = []
    for t in range(total + 1):
        p_, _ = strike_eye(S, mats_, phis, t, span)
        strike_w.append(eye0 + offs[t] + p_)
    tip_hit = strike_w[t_main]
    blade_pts = {}

    def blade_at(t):
        if t not in blade_pts:
            m4 = mats_[t] @ Matrix.Rotation(phis[t], 4, "Y")
            blade_pts[t] = [eye0 + offs[t] + m4 @ Vector((0, lo_y + (span - lo_y) * q, 0)) for q in np.linspace(0.4, 1.0, 13)]
        return blade_pts[t]

    def blade_gap(t, mx=None, my=None, top=None):
        """Closest distance from the blade / head (outer 60% of the tool) to the mob's body column (r 0.2 m)."""
        if tool == "pickaxe":
            return (strike_w[t] - tip_hit).length
        mx = tip_hit.x if mx is None else mx; my = tip_hit.y + 0.2 if my is None else my
        top = mob_top if top is None else top
        best = 9.0
        for p in blade_at(t):
            dz = max(0.0, p.z - top, -p.z)
            best = min(best, math.hypot(max(0.0, math.hypot(p.x - mx, p.y - my) - 0.2), dz))
        return best
    mob_top = min(1.8, max(0.6, tip_hit.z + 0.25))
    if tool != "pickaxe" and len(hits) > 1:
        # several hits: stand the mob where every hit's blade crosses it, each hit on its closest tick (+-5)
        def windows():
            out = []
            for i_, h_ in enumerate(hits):
                lo_k = max(1, h_ - 5) if i_ == 0 else max(h_ - 5, 1)
                out.append(range(lo_k, min(swing - 1, h_ + 5) + 1))
            return out
        wins = windows()
        best_c = None
        for mx in np.linspace(-1.2, 1.2, 25):
            for my in np.linspace(1.25, 2.45, 13):
                cost = 0.0; ks = []
                for i_, w_ in enumerate(wins):
                    k_b = min(w_, key=lambda k: blade_gap(FORM + k, bx + mx, my, 1.8))
                    g_ = blade_gap(FORM + k_b, bx + mx, my, 1.8); cost += g_ * g_; ks.append(k_b)
                if any(b_ - a_ < 10 for a_, b_ in zip(ks, ks[1:])):
                    cost += 5.0                        # keep the hits apart (S2c1 pace: no spamming)
                cost += 0.02 * abs(mx)                 # prefer in front of you
                if best_c is None or cost < best_c[0]:
                    best_c = (cost, mx, my, ks)
        _, mx, my, ks = best_c
        hits[:] = ks
        S["main"] = ks[-1] if S["knocks"] and S["knocks"][-1] == max(S["knocks"]) else ks[0]
        t_main = FORM + S["main"]
        k_t = min(range(len(blade_at(t_main))), key=lambda j: math.hypot(blade_at(t_main)[j].x - bx - mx, blade_at(t_main)[j].y - my))
        tip_hit = Vector((bx + mx, my - 0.2, blade_at(t_main)[k_t].z))
        mob_top = 1.8
    for h_ in hits:
        print("  ", tk, "hit", h_, "blade to mob body (m)", round(blade_gap(FORM + h_), 2))
    # ---- world: floor, backdrop, the mob (or the block in the wall at the crosshair)
    yfar = 26 if long_bay else 11
    box(f"{wtag} floor", (bx - 6, -6, -0.02), (bx + 3.5, yfar, 0), FLOOR)
    box(f"{wtag} backdrop", (bx - 6.2, -8, 0), (bx - 6, yfar + 2, 7), WALL)
    blocky = tool == "pickaxe"
    if blocky:
        # the block sits in a wall, centred on the crosshair ray; its face is where the spike tip strikes
        fy = tip_hit.y - 0.04
        tgt = link(bpy.data.objects.new(f"{wtag} block pivot", None)); tgt.location = (tip_hit.x, fy, tip_hit.z - 0.5)
        box(f"{wtag} block", (-0.5, 0, 0), (0.5, 1.0, 1.0), STONE, tgt)
        for dx, dz in ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, -1)):
            if tip_hit.z - 0.5 + dz >= -0.5:
                box(f"{wtag} wall {dx},{dz}", (tip_hit.x + dx - 0.5, fy + 0.02, max(0, tip_hit.z - 0.5 + dz)),
                    (tip_hit.x + dx + 0.5, fy + 1.0, tip_hit.z + 0.5 + dz), WALL)
        flash = box(f"{wtag} hit", (-0.12, -0.01, -0.12), (0.12, 0.0, 0.12), HIT, loc=(tip_hit.x, fy, tip_hit.z))
    else:
        ty = tip_hit.y + 0.03
        top = mob_top
        tgt = link(bpy.data.objects.new(f"{wtag} mob pivot", None)); tgt.location = (tip_hit.x, ty, 0)
        hb_ = [((-0.22, 0, 0), (0.22, 0.35, top - 0.3), DUMMY), ((-0.15, 0.03, top - 0.3), (0.15, 0.33, top), DUMMYH)]
        multibox(f"{wtag} mob", hb_, tgt, np.array((0.0, 0.17, 0.0)))
        flash = box(f"{wtag} hit", (-0.18, -0.03, -0.18), (0.18, 0.0, 0.18), HIT,
                    loc=(tip_hit.x, ty, min(top - 0.2, max(0.25, tip_hit.z))))
    tgt.rotation_mode = "XYZ"
    tgt_home = Vector(tgt.location)
    # ---- rig: body (eye) -> camera + shoulder -> grip -> tool root
    body = link(bpy.data.objects.new(f"{tag} body", None)); body.location = eye0
    sh, grip, ring_pt = make_arm(tag, body)
    root = link(bpy.data.objects.new(f"{tag} tool", None)); root.parent = grip; root.rotation_mode = "XYZ"
    ticks = []
    hit_frames = []
    for t, p in enumerate(poses):
        pitch, yaw, roll, tilt, reach = p
        e_, _ = arm_matrix(p)
        sh.rotation_euler = e_; sh.keyframe_insert("rotation_euler", frame=t + 1)
        key(sh, t + 1, loc=tuple(SH_LOCAL + Vector((0, reach, 0))))
        key(grip, t + 1, rot=(R(-tilt), 0, 0))
        key(root, t + 1, rot=(0, phis[t], 0))
        if S["body"] or S["hop"]:
            key(body, t + 1, loc=tuple(eye0 + offs[t]))
        k_ = kk_of(t)
        hit_now = k_ is not None and k_ in hits
        if hit_now:
            hit_frames.append(t + 1)
        ticks.append({"arm": [round(pitch, 2), round(yaw, 2), round(roll, 2)], "tool_tilt": round(tilt, 2),
                      "tool_twist": round(math.degrees(phis[t]), 2), "reach": round(reach, 3), "hit": hit_now,
                      "body": [round(offs[t].y, 3), round(offs[t].z, 3)]})
        if t == 0 or hit_now or ticks[t - 1]["hit"]:
            flash.hide_render = not hit_now; flash.keyframe_insert("hide_render", frame=t + 1)
            flash.hide_viewport = not hit_now; flash.keyframe_insert("hide_viewport", frame=t + 1)
    # the strike point, for the crosshair check
    _, sl = strike_eye(S, mats_, phis, t_main, span)
    sp_ = link(bpy.data.objects.new(f"{tag} strike point", None)); sp_.parent = root; sp_.location = sl
    sp_.empty_display_size = 0.02
    # ---- second hand on the haft for the two-handed weapons (maul, glaive)
    if S["lefty"] is not None:
        lh = box(f"{tag} left hand", (-2.05 * PX, -2 * PX, -2.05 * PX), (2.05 * PX, 2 * PX, 2.05 * PX), SKIN, root,
                 loc=(0, S["lefty"], 0))
        ls = box(f"{tag} left sleeve", (-2 * PX, -2 * PX, -1.0), (2 * PX, 2 * PX, 0), SLEEVE, body, loc=tuple(LEFT_SH))
        ls.rotation_mode = "QUATERNION"
        for t in range(total + 1):
            hand = mats_[t] @ Matrix.Rotation(phis[t], 4, "Y") @ Vector((0, S["lefty"], 0))
            d = hand - LEFT_SH
            L = max(0.05, d.length - 1.5 * PX)
            ls.rotation_quaternion = d.to_track_quat("-Z", "Y"); ls.keyframe_insert("rotation_quaternion", frame=t + 1)
            key(ls, t + 1, sc=(1, 1, L))
    # ---- the mob / block reacts on contact: knocked back along the swing and tilted (heavier hits further)
    for hi_, f in enumerate(hit_frames):
        t = f - 1
        gap = (hit_frames[hi_ + 1] - f) if hi_ + 1 < len(hit_frames) else 99
        v = strike_w[min(total, t + 1)] - strike_w[max(0, t - 1)]
        d = Vector((v.x, max(v.y, 0.0) + 0.6 * v.length + 0.3, 0))
        d.normalize()
        if blocky:
            key(tgt, f - 1, sc=1.0); key(tgt, f + 1, sc=(1.03, 0.94, 1.03)); key(tgt, f + 3, sc=1.0)
            continue
        kn = S["knocks"][hi_ % len(hits)] if S["knocks"] else S["knock"]
        ax = Vector((0, 0, 1)).cross(d)
        tilt_r = R(min(34, 12 + 12 * kn))
        e_tilt = Matrix.Rotation(tilt_r, 3, ax).to_euler("XYZ")
        e_half = Matrix.Rotation(tilt_r * 0.35, 3, ax).to_euler("XYZ")
        key(tgt, f - 1, loc=tuple(tgt_home), rot=(0, 0, 0))
        key(tgt, f + 1, loc=tuple(tgt_home + d * kn * 0.7), rot=tuple(e_tilt))
        back = min(f + 7, f + gap - 2)
        key(tgt, f + 3, loc=tuple(tgt_home + d * kn), rot=tuple(e_half))
        key(tgt, back, loc=tuple(tgt_home), rot=(0, 0, 0))
    # ---- the tool, in sections along its length
    NB = 7
    bands = [[] for _ in range(NB)]
    for a, b, m in bxs:
        bands[max(0, min(NB - 1, int(((a[1] + b[1]) / 2 - lo_y) / (span - lo_y) * NB)))].append((a, b, m))
    parts = []
    for k, bl in enumerate(bands):
        if not bl:
            continue
        lo = np.min([a for a, _, _ in bl], 0); hi = np.max([b for _, b, _ in bl], 0)
        c = (lo + hi) / 2
        parts.append((multibox(f"{tag} tool part {k}", bl, root, c), c))
    lo_x = min(float(a[0]) for a, _, _ in bxs); hi_x = max(float(b[0]) for _, b, _ in bxs)
    lo_z = min(float(a[2]) for a, _, _ in bxs); hi_z = max(float(b[2]) for _, b, _ in bxs)
    # ---- charge before the big swings: a green shell over the tool and a ring flare
    if S["charge"]:
        shell = box(f"{tag} charge shell", (lo_x - 0.02, lo_y - 0.02, lo_z - 0.02), (hi_x + 0.02, span + 0.03, hi_z + 0.02), CHG, root)
        flare = box(f"{tag} ring flare", (-0.025, -0.025, -0.025), (0.025, 0.025, 0.025), PIX, sh, loc=tuple(ring_pt))
        motes = [box(f"{tag} charge mote {i}", (-0.012, -0.012, -0.012), (0.012, 0.012, 0.012), PIX, root) for i in range(6)]
        for t in range(total + 1):
            k_ = kk_of(t)
            on = k_ is not None and any(a_ <= k_ <= b_ for a_, b_ in S["charge"])
            if on:
                a_, b_ = next((a_, b_) for a_, b_ in S["charge"] if a_ <= k_ <= b_)
                w = (k_ - a_) / max(1, b_ - a_)
                s_ = 0.85 + 0.15 * w + (0.03 if t % 2 else -0.03)
                key(shell, t + 1, sc=(s_, 1.0, s_)); key(flare, t + 1, sc=1.0 + 1.2 * w)
            else:
                key(shell, t + 1, sc=0.0001); key(flare, t + 1, sc=0.0001)
            for i, o in enumerate(motes):
                if on:
                    ph = (t * 0.45 + i * 1.05)
                    r_ = 0.16 * (1 - ((t + i) % 4) / 4)
                    key(o, t + 1, loc=(r_ * math.cos(ph), span * (0.35 + 0.1 * i), r_ * math.sin(ph)), sc=1.0)
                else:
                    key(o, t + 1, loc=(0, span * 0.5, 0), sc=0.0001)
    # ---- chips off the block at each pick strike
    if blocky:
        rng_d = np.random.default_rng(900 + bi)
        for hf_i, f in enumerate(hit_frames):
            for j in range(6):
                ch = box(f"{wtag} chip {hf_i}.{j}", (-0.035, -0.035, -0.035), (0.035, 0.035, 0.035), STONE)
                p0 = Vector((tip_hit.x, fy - 0.03, tip_hit.z)) + Vector(rng_d.uniform(-0.05, 0.05, 3))
                vel = Vector((rng_d.uniform(-1.4, 1.4), rng_d.uniform(-1.8, -0.6), rng_d.uniform(0.6, 2.0)))
                key(ch, 1, loc=tuple(p0), sc=0.0001); key(ch, f - 1, loc=tuple(p0), sc=0.0001)
                for s in range(0, 9):
                    tt = s / 20.0
                    pp = p0 + vel * tt + Vector((0, 0, -9.8 * tt * tt / 2))
                    pp.z = max(0.03, pp.z)
                    key(ch, f + s, loc=tuple(pp), sc=1.0 if s < 8 else 0.0001)
    # ---- forming (ticks 0-14)
    rng = np.random.default_rng(861 + bi)
    m_rest = grip_matrix(REST[3])
    fam = build[0]
    yfrac = lambda c: max(0.0, min(1.0, (c[1] - lo_y) / (span - lo_y)))
    if build == "a3":                                  # pixel jet, tip first (as S3a3)
        pm = bpy.data.meshes.new(f"{tag} px"); s_ = 0.022
        pm.from_pydata([(x, y, z) for x in (-s_, s_) for y in (-s_, s_) for z in (-s_, s_)], [], BOXF)
        pm.materials.append(PIX)
        for o, c in parts:
            f_arrive = 3 + int(round((1 - yfrac(c)) * (FORM - 5)))
            key(o, 1, sc=0.0001); key(o, f_arrive - 1, sc=0.0001); key(o, f_arrive, sc=1.35); key(o, f_arrive + 2, sc=1.0)
            for j in range(3):
                px_ = link(bpy.data.objects.new(f"{tag} pixel", pm)); px_.parent = sh
                end = m_rest @ Vector(c + rng.uniform(-0.03, 0.03, 3))
                start = ring_pt + Vector(rng.uniform(-0.015, 0.015, 3))
                f0 = max(1, f_arrive - 2 + j - 1)
                key(px_, 1, loc=start, sc=0.0001); key(px_, f0, loc=start, sc=0.0001); key(px_, f0 + 1, loc=start, sc=1.0)
                key(px_, f_arrive + 1, loc=end, sc=0.5); key(px_, f_arrive + 2, loc=end, sc=0.0001)
    elif fam == "b":
        gb = box(f"{tag} guide beam", (-0.007, lo_y, -0.007), (0.007, span, 0.007), BEAM, grip)
        ew = 0.012
        edge = [((lo_x - ew, -0.004, lo_z - ew), (hi_x + ew, 0.004, lo_z)), ((lo_x - ew, -0.004, hi_z), (hi_x + ew, 0.004, hi_z + ew)),
                ((lo_x - ew, -0.004, lo_z), (lo_x, 0.004, hi_z)), ((hi_x, -0.004, lo_z), (hi_x + ew, 0.004, hi_z))]
        if build in ("b2", "b2r", "b2s"):
            key(gb, 1, sc=(1, 0.001, 1)); key(gb, 4, sc=(1, 1, 1)); key(gb, FORM, sc=(1, 1, 1)); key(gb, FORM + 1, sc=0.0001)
            eo = multibox(f"{tag} build edge", [(a, b, BEAM) for a, b in edge], grip, np.zeros(3))
        else:
            key(gb, 1, sc=0.0001)
        if build == "b2":                              # grows grip to tip behind the bright edge (as P1b2)
            key(root, 1, sc=(1, 0.001, 1)); key(root, 5, sc=(1, 0.001, 1)); key(root, FORM, sc=(1, 1, 1))
            edge_y = lambda t: span * (0.0 if t <= 5 else min(1.0, smooth((t - 5) / (FORM - 5))))
        elif build == "b2r":                           # tip back to the fist: parts appear from the tip down
            for o, c in parts:
                f_on = 5 + int(round((1 - yfrac(c)) * (FORM - 6)))
                key(o, 1, sc=0.0001); key(o, f_on - 1, sc=0.0001); key(o, f_on, sc=(1, 0.3, 1)); key(o, f_on + 1, sc=1.0)
            edge_y = lambda t: span - (span - lo_y) * (0.0 if t <= 5 else min(1.0, smooth((t - 5) / (FORM - 5))))
        elif build == "b2s":                           # the edge jumps out in three steps
            stp = [(1, 0.001), (5, 0.001), (6, 0.36), (8, 0.36), (9, 0.7), (11, 0.7), (12, 1.0)]
            for f, s in stp:
                key(root, f, sc=(1, s, 1))
            edge_y = lambda t: span * next((s for f, s in reversed(stp) if f <= t), 0.0)
        if build in ("b2", "b2r", "b2s"):
            for t in range(1, FORM + 3):
                key(eo, t, loc=(0, max(edge_y(t), 0.001), 0), sc=1.0 if 5 <= t <= FORM else 0.0001)
            burst = [7, 9, 11, 13] if build != "b2s" else [6, 6, 9, 9, 12, 12]
            for j, f0 in enumerate(burst + burst[:2]):
                spk = box(f"{tag} spark {j}", (-0.01, -0.01, -0.01), (0.01, 0.01, 0.01), PIX, grip)
                p0 = Vector((rng.uniform(lo_x, hi_x), edge_y(f0), 0))
                dv = Vector((rng.uniform(-1, 1), rng.uniform(-0.3, 0.6), rng.uniform(-1, 1))).normalized() * 0.18
                key(spk, 1, loc=p0, sc=0.0001); key(spk, f0, loc=p0, sc=0.0001); key(spk, f0 + 1, loc=p0, sc=1.0)
                key(spk, f0 + 3, loc=p0 + dv, sc=0.6); key(spk, f0 + 4, loc=p0 + dv * 1.2, sc=0.0001)
        elif build in ("b3", "b3t"):                   # ratchet clicks (four, or two heavy ones)
            steps = ([(1, 0.001), (3, 0.001), (4, 0.28), (6, 0.28), (7, 0.52), (9, 0.52), (10, 0.76), (12, 0.76), (13, 1.0)]
                     if build == "b3" else [(1, 0.001), (5, 0.001), (6, 0.55), (10, 0.55), (11, 1.0)])
            for f, s in steps:
                key(root, f, sc=(1, s, 1))
            for i, (f, s) in enumerate(steps[2::2]):
                cl = box(f"{tag} click {i}", (lo_x - 0.03, -0.006, lo_z - 0.03), (hi_x + 0.03, 0.006, hi_z + 0.03), RIM, grip,
                         loc=(0, span * s, 0))
                key(cl, 1, sc=0.0001); key(cl, f - 1, sc=0.0001); key(cl, f, sc=1.0)
                key(cl, f + (2 if build == "b3t" else 1), sc=0.0001)
                if build == "b3t":
                    for o, c in parts:                 # rim flash on each click: the whole tool pulses
                        key(o, f - 1, sc=1.0); key(o, f, sc=(1.08, 1, 1.08)); key(o, f + 1, sc=1.0)
                    key(parts[0][0], 1, sc=1.0)
        else:                                          # b3r: four clicks, tip first
            groups = [[], [], [], []]
            for o, c in parts:
                groups[min(3, int((1 - yfrac(c)) * 4))].append((o, c))
            for i, g in enumerate(groups):
                f = 4 + 3 * i
                for o, c in g:
                    key(o, 1, sc=0.0001); key(o, f - 1, sc=0.0001); key(o, f, sc=1.0)
                if g:
                    yc = float(np.mean([c[1] for _, c in g]))
                    cl = box(f"{tag} click {i}", (lo_x - 0.03, -0.006, lo_z - 0.03), (hi_x + 0.03, 0.006, hi_z + 0.03), RIM,
                             grip, loc=(0, yc, 0))
                    key(cl, 1, sc=0.0001); key(cl, f - 1, sc=0.0001); key(cl, f, sc=1.0); key(cl, f + 1, sc=0.0001)
    else:
        for i, (o, c) in enumerate(parts):
            yf = yfrac(c)
            f_lock = 4 + int(round(yf * (FORM - 6)))
            home = Vector(c); o.rotation_mode = "XYZ"
            if build == "c1":                          # fly in and lock (as S3c1)
                off = Vector(rng.uniform(-1, 1, 3)); off.y = abs(off.y) * 0.5; off = off.normalized() * 0.35
                key(o, 1, loc=home + off, sc=0.0001); key(o, max(2, f_lock - 4), loc=home + off, sc=0.0001)
                key(o, max(3, f_lock - 3), loc=home + off, sc=0.6); key(o, f_lock, loc=home, sc=1.0)
                key(o, max(3, f_lock - 3), rot=(R(rng.uniform(-60, 60)), R(rng.uniform(-60, 60)), R(rng.uniform(-60, 60))))
                key(o, f_lock, rot=(0, 0, 0))
            elif build == "c1s":                       # stream in from beyond the tip, tip section first
                f_lock = 4 + int(round((1 - yf) * (FORM - 6)))
                st = Vector((home.x, span + 0.5, home.z))
                key(o, 1, loc=st, sc=0.0001); key(o, max(2, f_lock - 3), loc=st, sc=0.0001)
                key(o, max(3, f_lock - 2), loc=st * 0.6 + home * 0.4, sc=0.7); key(o, f_lock, loc=home, sc=1.0)
            elif build == "c1b":                       # from behind the shoulder, tip first
                f_lock = 4 + int(round((1 - yf) * (FORM - 6)))
                st = Vector((0.15, -0.5, 0.35)) + Vector(rng.uniform(-0.05, 0.05, 3))
                key(o, 1, loc=st, sc=0.0001); key(o, max(2, f_lock - 4), loc=st, sc=0.0001)
                key(o, max(3, f_lock - 3), loc=st, sc=0.6)
                key(o, max(3, f_lock - 1), loc=home + Vector((0.08, -0.05, 0.08)), sc=1.0); key(o, f_lock, loc=home, sc=1.0)
                key(o, max(3, f_lock - 3), rot=(R(-90), 0, 0)); key(o, f_lock, rot=(0, 0, 0))
            elif build == "c2":                        # unfold out of the grip (as S2c2)
                start = Vector((home.x, 0.05, home.z))
                key(o, 1, loc=start, sc=0.0001, rot=(R(180), 0, 0)); key(o, max(2, f_lock - 3), loc=start, sc=0.0001, rot=(R(180), 0, 0))
                key(o, max(3, f_lock - 2), loc=start, sc=0.8, rot=(R(160), 0, 0))
                key(o, f_lock, loc=home, sc=1.0, rot=(0, 0, 0))
            elif build == "c2p":                       # unfold in pairs from beside the haft
                pair = i // 2; sgn = 1 if i % 2 else -1
                f_lock = 4 + 2 * pair
                start = Vector((home.x + sgn * 0.12, home.y * 0.5, home.z))
                key(o, 1, loc=start, sc=0.0001, rot=(0, 0, R(90 * sgn))); key(o, f_lock - 2, loc=start, sc=0.0001, rot=(0, 0, R(90 * sgn)))
                key(o, f_lock - 1, loc=start, sc=0.8, rot=(0, 0, R(60 * sgn)))
                key(o, f_lock, loc=home, sc=1.0, rot=(0, 0, 0))
            else:                                      # c2t: telescope out of each other
                prev_y = parts[i - 1][1][1] if i else 0.0
                start = Vector((home.x, prev_y, home.z))
                key(o, 1, loc=start, sc=0.0001); key(o, f_lock - 1, loc=start, sc=(0.9, 0.3, 0.9))
                key(o, f_lock, loc=home, sc=1.0)
                ring_ = box(f"{tag} telescope ring {i}", (lo_x - 0.02, -0.005, lo_z - 0.02), (hi_x + 0.02, 0.005, hi_z + 0.02),
                            RIM, root, loc=(0, float(home.y), 0))
                key(ring_, 1, sc=0.0001); key(ring_, f_lock - 1, sc=0.0001); key(ring_, f_lock, sc=1.0); key(ring_, f_lock + 1, sc=0.0001)
    # ---- record
    MODEL_AT[tk] = t_main + 1
    dump["takes"][tk] = {"name": name, "tool": tool, "build": BUILD_NAME[build], "forming_ticks": FORM, "swing_ticks": swing,
                         "plays": plays, "hit_ticks": hits, "charge_ticks": S["charge"], "keys": [list(k) for k in keys],
                         "ticks": ticks}
    # ---- cameras: the eye (moves with the body), and from the right
    c = cam(f"Cam {tk}", (0, 0, 0), (0, 3, -0.25), 10.4)
    c.parent = body
    c.data.sensor_fit = "HORIZONTAL"; c.data.sensor_width = 36.0
    for nm_, a_, b_ in (("h", (-0.007, -0.0006, -0.2), (0.007, 0.0006, -0.2)), ("v", (-0.0006, -0.007, -0.2), (0.0006, 0.007, -0.2))):
        box(f"FT5 {tk} crosshair {nm_}", a_, b_, XH, c)
    far = 1.0 if tool == "sword" or tool == "pickaxe" or tool == "axe3d" else 1.45
    cam(f"Cam {tk} side", tuple(eye0 + Vector((3.2 * far, 0.9 + 0.3 * far, 0.2))), tuple(eye0 + Vector((0.3, 0.8 * far, -0.3))), 35)
    cu = bpy.data.curves.new("FT5 label " + tk, "FONT"); cu.body = f"{tk}  {name}  ({BUILD_NAME[build]})"
    cu.size = 0.11; cu.align_x = "RIGHT"
    tl = link(bpy.data.objects.new("FT5 label " + tk, cu)); tl.location = (bx - 5.95, -0.3, 2.3); tl.rotation_euler = (R(90), 0, R(90))
    tl.data.materials.append(GLOW)
    S["total"] = total
    print(tk, name, "| build", build, "| frames 1 -", total + 1, "| main hit frame", t_main + 1, "| strike point at",
          tuple(round(x - y, 2) for x, y in zip(tip_hit, (bx, 0, 0))), "| in view (deg right, up)", eye_angles(tip_hit - eye0 - offs[t_main]),
          "| aim err" if tool == "pickaxe" else "", S.get("aim_err", ""), flush=True)

scene.frame_start, scene.frame_end = 1, max(T[t]["total"] + 1 for t in ORDER)
# ---- J's pickaxe rule, checked through the real camera: project the strike point at each hit frame
for tk in ORDER:
    sp_ = bpy.data.objects[f"FT5 {tk} fp strike point"]
    cm_ = bpy.data.objects[f"Cam {tk}"]
    scene.frame_set(MODEL_AT[tk])
    bpy.context.view_layer.update()
    p = world_to_camera_view(scene, cm_, sp_.matrix_world.translation)
    CHECK[tk] = [round(p.x, 3), round(p.y, 3), round(p.z, 3)]
    print("screen check", tk, "strike point at hit frame", MODEL_AT[tk], "->", CHECK[tk], "(0.5, 0.5 = crosshair)")

with open(os.path.join(FOLDER, "combat", "fp_tools5_poses.json"), "w") as fh:
    json.dump(dump, fh, separators=(",", ":"))
with open(os.path.join(FOLDER, "combat", "fp_tools5_takes.json"), "w") as fh:
    json.dump({tk: {"frames": [1, T[tk]["total"] + 1], "model_at": MODEL_AT[tk], "hits": T[tk]["hits"],
                    "plays": T[tk]["plays"], "build": T[tk]["build"], "name": T[tk]["name"], "parent": T[tk]["parent"],
                    "note": T[tk]["note"], "swing": T[tk]["keys"][-1][0], "charge": T[tk]["charge"],
                    "tool": T[tk]["tool"], "screen_at_hit": CHECK[tk]} for tk in ORDER}, fh, indent=1)

world = bpy.data.worlds.new("FT5 world"); world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.32, 0.42, 0.55, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.7
scene.world = world
sun = link(bpy.data.objects.new("FT5 sun", bpy.data.lights.new("FT5 sun", "SUN")))
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
    tree = bpy.data.node_groups.new("FT5 Glow", "CompositorNodeTree")
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
scene.camera = bpy.data.objects["Cam P1b21"]
scene.frame_set(MODEL_AT["P1b21"])
try:
    bpy.ops.outliner.orphans_purge(do_recursive=True)
except Exception:
    pass
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("saved", OUT)
