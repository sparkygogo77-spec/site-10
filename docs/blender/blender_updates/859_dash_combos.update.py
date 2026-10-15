# Pass 859: sword dash combos, 10 more (rings/suits chat, 2026-10-15, range 800-899). Follows 852 (C1d1-3) and 844 C1a.
# J on 844 C1a (NEXT-ROUNDS "Added 2026-10-15 19:20"): "make a few variations of the mix up between cross cross DASH strike
# like 12 blocks forward? but the charge up for the dash final hit is like .7s and I need the sword to prime upword and be
# held at 20 degree angle from pointed at them, and then a another 10 10" -- his answer (DECISIONS): "another 10 10" =
# "10 more variations" of the cross, cross, dash combo. 852 built C1d1-3; these are ten more, none repeating them.
# Round 4 sword direction: heavier and slower, the sword feels weighty; a short charge before the big hit; the mob reacts
# on contact (knocked back / flinch at the hit frame); recovery stays quick.
#
# Every take: cross, cross (directions, heights, rhythm and steps vary), then a 0.7 s charge (14 ticks) with the sword
# primed upward and held exactly 20 deg above pointing at the mob (solved per take from where the hand is: the blade's
# line is the grip-to-mob line turned 20 deg up; the build prints the measured angle), then a dash of about 12 blocks
# (the sword's far end meets the mob 12 m from where you started), a strike, and the mob reacts on contact. The prime
# position, the dash and the strike differ in every take. The first-person camera rides the dash; a wide side camera
# watches from the right. All ten form as a pixel stream like C1a (a1 grip first, a2 spiral up the forearm, a3 tip first).
#   C1e1  two quick stepping crosses (high diagonal, waist backhand); primed out at the right side; dash, rising cut,
#         the mob is launched up
#   C1e2  slow heavy X (a held set before each cut); primed above the left shoulder; leaping dash, overhead cleave,
#         the mob is slammed down
#   C1e3  vertical chop then a rising cut, stepping back; primed low across the body at the left hip; dash past the mob
#         with a backhand, carry on through and turn to face it; the mob spins away
#   C1e4  quick cross then a delayed heavy cross; primed pulled in at the chest; dash, skewer thrust and flick, the mob is
#         thrown up and off to the right
#   C1e5  flat crosses at chest then head height; primed at full reach, arm straight, aiming; spinning dash (a full turn),
#         flat sweep, the mob is knocked to the left
#   C1e6  two rising crosses stepping in; primed high right; dash, diagonal cleave down to the left, the mob is knocked
#         down to its side
#   C1e7  two short high crosses; primed at eye height drawn far back while you hop back a block; dash, X finish
#         (two cuts), the mob flinches then is knocked back
#   C1e8  two heavy knee-height crosses; primed low and wide at the right, coiled back; dash, skid stop, flat backhand
#         cleave, the mob is knocked right
#   C1e9  head-height flat cut then a vertical chop; hop and prime in the air, hand above the brow; diving dash, downward
#         thrust, the mob is driven into the ground
#   C1e10 waist backhand then a falling diagonal; primed low in front; zigzag dash, rising launcher then a slam on the
#         mob in the air
#
# Cameras: "Cam <take>" first person (120 deg, crosshair, rides the body) and "Cam <take> side" (wide, from the right).
# Bays 80 m apart, each with a backdrop wall. Forms over ticks 0-14 (20 ticks a second), then the combo plays once.
# Writes LanternLive\combat\dash_combos_poses.json and builds LanternLive\combat\dash_combos.blend.
import json, math, os
import bpy
import numpy as np
from mathutils import Matrix, Euler, Vector

R = math.radians
OUT = os.path.join(FOLDER, "combat", "dash_combos.blend")
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
SCENE_NAME = "Dash Combos"
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


SKIN = mat("DC5 skin", (0.62, 0.42, 0.3)); SLEEVE = mat("DC5 sleeve", (0.04, 0.28, 0.12))
RINGM = mat("DC5 ring face", (0.02, 0.85, 0.15), emit=2.0); GOLDM = mat("DC5 ring gold", (0.95, 0.7, 0.2), rough=0.25, metal=1.0)
GLASS = mat("DC5 hard-light glass", (0.03, 0.45, 0.16), emit=0.8, alpha=0.62, rough=0.15)
GLOW = mat("DC5 construct glow", (0.05, 0.9, 0.22), emit=3.5)
RIM = mat("DC5 construct rim", (0.08, 1.0, 0.28), emit=4.5)
GRIP = mat("DC5 construct grip", (0.02, 0.2, 0.08), emit=0.6, rough=0.3)
PIX = mat("DC5 forming pixel", (0.06, 1.0, 0.28), emit=4.0)
CHG = mat("DC5 charge shell", (0.03, 0.8, 0.2), emit=2.2, alpha=0.28, rough=0.2)
STREAK = mat("DC5 dash streak", (0.03, 0.8, 0.2), emit=2.0, alpha=0.35, rough=0.2)
XH = mat("DC5 crosshair", (0.85, 0.85, 0.85), emit=1.0)
FLOOR = mat("DC5 floor", (0.18, 0.2, 0.22), rough=0.9)
WALL = mat("DC5 backdrop", (0.24, 0.26, 0.3), rough=0.95)
DUMMY = mat("DC5 dummy", (0.07, 0.11, 0.08), rough=0.85)
DUMMYH = mat("DC5 dummy head", (0.1, 0.16, 0.1), rough=0.85)
HIT = mat("DC5 hit flash", (0.04, 0.7, 0.18), emit=1.6, alpha=0.8)
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



# ------------------------------------------------------------------ takes
# Arm keys: (tick, arm pitch, yaw, roll, tool tilt, reach m). Pitch 90 = straight ahead, >90 raised; yaw + = toward the
# left (- = right); roll twists the forearm; tilt leans the sword forward in the fist; reach moves the shoulder.
# "PRIME" marks the two keys of the 14-tick prime hold: that pose starts from the take's guess and is solved so the blade
# points 20 deg above the line from the fist to the mob's chest.
# Body curves (ticks within the combo): fwd / side / up (m) and yaw (deg, + = turning left); ("H", d) = solved at the dash
# hit so the sword's far end meets the mob DASH m out (fwd) or the mob's head (up), plus d after it.
# react: the mob's keys after contact (dt ticks, x, y away from you, z, rx, ry, rz deg): rx < 0 tips it away, ry > 0 to the
# right, rz spins it.
REST = (96, 14, 0, 22, 0.0)
DASH = 12.0
HOLD = 14                 # 0.7 s prime
T = {}
C1A = ("make a few variations of the mix up between cross cross DASH strike like 12 blocks forward? but the charge up for "
       "the dash final hit is like .7s and I need the sword to prime upword and be held at 20 degree angle from pointed "
       "at them, and then a another 10 10")


def take(code, name, build, keys, p0, prime_start, hits, main, react, fwd, up=(), side=(), yaw=(), vyaw=None, vpitch=(),
         crosses="", prime_desc="", dash_desc="", strike_desc="", fixed=(), mob_top=True, react_desc=""):
    T[code] = dict(name=name, build=build, keys=[(0, *REST)] + list(keys), prime_start=prime_start, p0=p0, hits=hits, main=main,
                   react=react, fwd=list(fwd), up=list(up), side=list(side), yaw=list(yaw),
                   vyaw=list(yaw) if vyaw is None else list(vyaw), vpitch=list(vpitch), crosses=crosses,
                   prime_desc=prime_desc, dash_desc=dash_desc, strike_desc=strike_desc, fixed=list(fixed),
                   mob_top=mob_top, react_desc=react_desc)


H0 = ("H", 0.0)
take("C1e1", "Dash combo: stepping crosses, prime out right, dash rising cut", "a1",
     [(3, 136, -26, -34, -12, -0.04), (6, 64, 30, 30, 78, 0.1), (8, 96, 52, 100, 62, 0.0), (11, 96, -46, 100, 62, 0.1),
      (15, "PRIME"), (29, "PRIME"), (32, 68, -36, -30, 82, 0.02), (36, 134, 24, 30, 8, 0.12), (38, 138, 28, 32, 2, 0.1),
      (44, *REST)],
     (100, -42, -20, 70, -0.02), 15, [34], 34,
     [(2, -0.35, 0.8, 1.2, -25, -15, 10), (5, -0.6, 1.4, 1.9, -40, -25, 25), (9, -0.8, 1.9, 0.0, -70, -30, 30)],
     fwd=[(0, 0.0), (3, 0.0), (6, 0.35), (8, 0.35), (11, 0.7), (29, 0.7), (34, H0), (38, ("H", 0.4))],
     crosses="two quick stepping crosses: high right to low left, then a waist-high backhand left to right, a step on each",
     prime_desc="out at your right side, arm low and wide", dash_desc="straight dash",
     strike_desc="rising diagonal cut from low right to high left", react_desc="launched up and back, lands on its back")
take("C1e2", "Dash combo: slow heavy X, prime over left shoulder, leaping slam", "a2",
     [(4, 138, -28, -35, -16, -0.06), (7, 139, -29, -36, -18, -0.07), (11, 62, 30, 30, 80, 0.1), (14, 136, 30, 36, -16, -0.06),
      (17, 137, 31, 37, -18, -0.07), (21, 62, -30, -30, 80, 0.1), (25, "PRIME"), (39, "PRIME"), (42, 152, 34, 38, -24, -0.06),
      (46, 64, -22, -26, 82, 0.14), (48, 56, -30, -30, 88, 0.1), (54, *REST)],
     (150, 32, 30, 120, -0.08), 25, [45], 45,
     [(1, 0, 0.25, -0.1, -20, 8, 0), (3, 0.2, 0.9, 0.0, -82, 10, 0), (12, 0.2, 1.0, 0.0, -88, 10, 0)],
     fwd=[(0, 0.0), (39, 0.0), (45, H0), (48, ("H", 0.3))], up=[(0, 0.0), (39, 0.0), (42, 1.1), (45, 0.0), (47, -0.08), (50, 0.0)],
     vpitch=[(0, 0.0), (39, 0.0), (43, 6.0), (45, -8.0), (49, 0.0)],
     crosses="slow heavy X: a held set high right, cut to low left; a held set high left, cut to low right",
     prime_desc="held above the left shoulder", dash_desc="leaping dash (up a block and down onto the mob)",
     strike_desc="falling slam off the left shoulder down to the right", react_desc="slammed flat on its back")
take("C1e3", "Dash combo: chop and rising cut, prime at left hip, pass through and turn", "a3",
     [(4, 142, -4, 0, -20, -0.06), (8, 72, 2, 0, 80, 0.08), (10, 70, 4, 0, 80, 0.0), (14, 134, -6, 0, 2, 0.04),
      (18, "PRIME"), (32, "PRIME"), (34, 84, 44, 100, 62, -0.04), (38, 84, -50, 100, 62, 0.1), (40, 86, -80, 100, 60, 0.04),
      (48, *REST)],
     (58, 36, 20, 110, -0.04), 18, [37], 37,
     [(2, 0.6, 0.4, 0.0, -10, 25, 90), (6, 1.3, 0.7, 0.0, -5, 30, 200), (10, 1.5, 0.8, 0.0, 0, 0, 230)],
     fwd=[(0, 0.0), (6, 0.2), (14, -0.6), (32, -0.6), (37, H0), (40, ("H", 3.4))], side=[(0, 0.0), (32, 0.0), (36, -0.45)],
     yaw=[(0, 0.0), (39, 0.0), (45, 180.0)],
     crosses="vertical chop, then a rising cut straight up, stepping back on it",
     prime_desc="low across the body at the left hip", dash_desc="dash past the mob's left side and on 3 blocks",
     strike_desc="backhand cut left to right as you pass, then turn round to face it", react_desc="spun away to the right")
take("C1e4", "Dash combo: quick cross, delayed heavy cross, prime at chest, skewer and flick", "a1",
     [(3, 134, -26, -34, -10, -0.02), (6, 66, 30, 30, 78, 0.08), (8, 70, 30, 30, 76, 0.06), (11, 140, 32, 38, -24, -0.08),
      (14, 141, 33, 38, -26, -0.09), (18, 60, -30, -32, 84, 0.1), (22, "PRIME"), (36, "PRIME"), (39, 90, 4, 0, 76, -0.16),
      (41, 90, 4, 0, 74, 0.44), (42, 90, 4, 0, 74, 0.44), (45, 124, -30, -30, 40, 0.2), (51, *REST)],
     (84, 14, 0, 64, -0.26), 22, [41], 41,
     [(1, 0.0, 0.35, 0.0, -12, 0, 0), (3, 0.0, 0.5, 0.15, -15, 0, 0), (6, 1.0, 1.0, 1.6, -20, 45, 30),
      (11, 2.0, 1.5, 0.0, -10, 88, 40)],
     fwd=[(0, 0.0), (36, 0.0), (41, H0), (43, ("H", 0.25))], fixed=[(36, 43, 90)],
     crosses="quick cross high right to low left, then a delayed heavy cross from a held set high left",
     prime_desc="pulled in at the chest", dash_desc="straight dash", strike_desc="skewering thrust, then a flick up and right",
     react_desc="skewered, then thrown up and off to the right, lands on its side")
take("C1e5", "Dash combo: chest and head crosses, prime at full reach, spinning sweep", "a2",
     [(3, 98, -54, -80, 62, -0.04), (7, 96, 48, -80, 62, 0.08), (9, 118, 54, 100, 56, 0.0), (13, 116, -48, 100, 58, 0.1),
      (16, "PRIME"), (30, "PRIME"), (33, 98, -72, -80, 62, 0.0), (35, 98, -60, -80, 62, 0.04), (38, 96, 42, -80, 62, 0.1),
      (40, 96, 52, -80, 60, 0.06), (46, *REST)],
     (96, 6, 0, 76, 0.16), 16, [37], 37,
     [(2, -0.7, 0.45, 0.1, -10, -30, -20), (6, -1.7, 0.9, 0.0, -10, -20, -40), (11, -2.0, 1.0, 0.0, 0, 0, -45)],
     fwd=[(0, 0.0), (30, 0.0), (37, H0), (40, ("H", 0.3))], yaw=[(0, 0.0), (30, 0.0), (36, 360.0)],
     vyaw=[(0, 0.0)],
     crosses="flat crosses: chest height right to left, then head height left to right",
     prime_desc="at full reach, arm straight out, aiming", dash_desc="spinning dash: the body turns a full circle (your view stays on the mob)",
     strike_desc="the spin carries into a flat forehand sweep right to left", react_desc="knocked away to the left")
take("C1e6", "Dash combo: two rising crosses stepping in, prime high right, diagonal cleave", "a3",
     [(3, 64, 34, 32, 82, -0.02), (7, 130, -24, -32, 4, 0.08), (10, 64, -32, -30, 82, 0.0), (14, 130, 26, 32, 2, 0.1),
      (18, "PRIME"), (32, "PRIME"), (34, 144, -30, -36, -14, -0.04), (38, 62, 30, 30, 80, 0.12), (40, 58, 34, 32, 84, 0.08),
      (46, *REST)],
     (136, -30, -26, 116, -0.06), 18, [36], 36,
     [(2, -0.4, 0.5, 0.0, -15, -35, 0), (6, -0.8, 0.9, 0.0, -10, -88, 0), (12, -0.85, 0.95, 0.0, -10, -88, 0)],
     fwd=[(0, 0.0), (3, 0.0), (7, 0.4), (10, 0.4), (14, 0.8), (32, 0.8), (36, H0), (39, ("H", 0.3))],
     crosses="two rising crosses, low left to high right then low right to high left, stepping in on each",
     prime_desc="high on the right", dash_desc="straight dash", strike_desc="diagonal cleave from high right down to low left",
     react_desc="knocked down onto its side")
take("C1e7", "Dash combo: short high crosses, hop back and prime, dash X finish", "a1",
     [(3, 128, -16, -24, 10, 0.0), (5, 110, 16, 18, 50, 0.06), (7, 128, 16, 24, 10, 0.0), (9, 110, -16, -18, 50, 0.06),
      (13, "PRIME"), (27, "PRIME"), (29, 138, -26, -34, -14, -0.04), (33, 64, 30, 30, 78, 0.1), (35, 138, 30, 35, -18, -0.04),
      (39, 62, -28, -30, 80, 0.1), (45, *REST)],
     (122, 4, 10, 104, -0.32), 13, [31, 37], 31,
     [(1, 0.0, 0.15, 0.0, -10, 0, 0), (5, 0.0, 0.0, 0.0, 0, 0, 0), (7, 0.3, 0.9, 0.0, -25, 15, 0), (10, 0.5, 1.6, 0.0, -15, 10, 0),
      (14, 0.55, 1.7, 0.0, 0, 0, 0)],
     fwd=[(0, 0.0), (9, 0.0), (13, -1.0), (27, -1.0), (31, H0), (37, ("H", 0.45))],
     up=[(0, 0.0), (9, 0.0), (11, 0.45), (13, 0.0)],
     crosses="two short, quick crosses high in front (small cuts)",
     prime_desc="beside the head at eye height, drawn far back, after a hop back of one block", dash_desc="straight dash",
     strike_desc="X finish: high right to low left on arrival, then high left to low right",
     react_desc="flinches on the first cut, knocked back on the second")
take("C1e8", "Dash combo: knee-height crosses, prime low right, skid and low sweep", "a2",
     [(4, 74, -52, -80, 64, -0.04), (6, 74, -54, -80, 64, -0.05), (10, 72, 50, -80, 66, 0.08), (12, 74, 52, 100, 64, 0.0),
      (13, 74, 53, 100, 64, -0.02), (17, 72, -50, 100, 66, 0.08), (21, "PRIME"), (35, "PRIME"), (38, 78, -62, -80, 62, -0.04),
      (42, 74, 50, -80, 66, 0.1), (44, 74, 58, -80, 64, 0.06), (50, *REST)],
     (74, -62, -40, 64, -0.16), 21, [40], 40,
     [(2, -0.5, 0.3, 0.0, -35, -20, 0), (6, -1.0, 0.6, 0.0, -85, -15, 0), (12, -1.05, 0.65, 0.0, -88, -15, 0)],
     fwd=[(0, 0.0), (35, 0.0), (40, H0), (44, ("H", 0.8))], up=[(0, 0.0), (37, 0.0), (40, -0.18), (44, -0.12), (48, 0.0)],
     vpitch=[(0, 0.0), (38, 0.0), (41, 4.0), (45, 0.0)],
     crosses="two heavy knee-height crosses, right to left then a backhand left to right, each from a held set",
     prime_desc="low and wide on the right, coiled back", dash_desc="dash that skids to a stop (about 1 block of slide)",
     strike_desc="low flat sweep right to left at knee height", react_desc="legs swept, falls back onto the ground")
take("C1e9", "Dash combo: head cut and chop, hop and prime in the air, diving thrust", "a3",
     [(3, 118, -54, -80, 56, -0.04), (7, 114, 50, -80, 58, 0.08), (10, 142, -4, 0, -20, -0.06), (14, 72, 2, 0, 80, 0.1),
      (18, "PRIME"), (32, "PRIME"), (35, 112, 4, 0, 94, -0.12), (37, 76, 4, 0, 100, 0.34), (38, 76, 4, 0, 100, 0.34),
      (45, *REST)],
     (140, 4, 0, 122, -0.06), 18, [37], 37,
     [(1, 0.0, 0.05, -0.25, -6, 0, 0), (3, 0.0, 0.1, -0.6, -10, 0, 0), (12, 0.0, 0.1, -0.62, -10, 0, 0)],
     fwd=[(0, 0.0), (32, 0.0), (37, H0), (39, ("H", 0.1))], up=[(0, 0.0), (14, 0.0), (18, 1.1), (32, 1.2), (37, H0), (42, 0.0)],
     vpitch=[(0, 0.0), (32, 0.0), (35, -18.0), (38, -14.0), (43, 0.0)], fixed=[(32, 39, 90)], mob_top=False,
     crosses="head-height flat cut right to left, then a vertical chop",
     prime_desc="up in the air (a ring hop of about 1 block), the fist above the brow", dash_desc="diving dash down onto the mob",
     strike_desc="downward thrust into the mob from above", react_desc="driven half into the ground")
take("C1e10", "Dash combo: backhand and falling cross, prime low, zigzag dash, launch and slam", "a1",
     [(4, 96, 50, 100, 62, -0.04), (6, 96, 52, 100, 62, -0.05), (10, 96, -46, 100, 62, 0.1), (13, 140, 30, 35, -20, -0.06),
      (17, 62, -28, -30, 80, 0.1), (21, "PRIME"), (35, "PRIME"), (38, 66, 2, 0, 84, 0.0), (42, 140, -2, 0, -12, 0.1),
      (45, 152, 0, 0, -32, -0.04), (48, 66, 2, 0, 86, 0.14), (50, 60, 2, 0, 90, 0.1), (56, *REST)],
     (68, 4, 0, 46, 0.0), 21, [40, 48], 40,
     [(2, 0.0, 0.3, 0.9, -15, 0, 20), (4, 0.0, 0.4, 1.35, -25, 0, 35), (7, 0.0, 0.45, 1.4, -30, 0, 40),
      (8, 0.0, 0.5, 0.6, -60, 0, 40), (9, 0.0, 0.6, 0.0, -88, 0, 40), (16, 0.0, 0.6, 0.0, -88, 0, 40)],
     fwd=[(0, 0.0), (35, 0.0), (40, H0), (42, ("H", 0.2))], side=[(0, 0.0), (35, 0.0), (37, -1.0), (39, 0.7), (40, 0.0)],
     up=[(0, 0.0), (40, 0.0), (44, 1.1), (48, 0.0)], vpitch=[(0, 0.0), (40, 0.0), (44, 10.0), (48, -10.0), (51, 0.0)],
     crosses="waist-high backhand left to right from a held set, then a falling cross high left to low right",
     prime_desc="low in front of you", dash_desc="zigzag dash (left, right, in)",
     strike_desc="rising launcher straight up, a hop after it, then a slam down on the mob in the air",
     react_desc="launched up on the first hit, slammed flat on the second")
BUILD_NAME = {"a1": "pixel stream, grip first", "a2": "pixels spiral up the forearm", "a3": "pixel jet, tip first"}


def pose_at(keys, t):
    for (ta, *a), (tb, *b) in zip(keys, keys[1:]):
        if ta <= t <= tb:
            w = smooth((t - ta) / (tb - ta))
            return [x + (y - x) * w for x, y in zip(a, b)]
    return list(keys[-1][1:])


# ------------------------------------------------------------------ tool models -> (a, b, material) boxes, tool space
def tool_boxes(tool):
    out = []
    d = json.load(open(os.path.join(BB, f"construct_{tool}_green.bbmodel")))
    for e in d["elements"]:
        nm = e["name"]
        m = GRIP if nm.startswith("handle") else RIM if nm.startswith("glow_rim") else GLOW if nm.startswith("glow") else GLASS
        inf = float(e.get("inflate", 0) or 0) / 32.0
        out.append((np.array(e["from"], float) / 32.0 - inf, np.array(e["to"], float) / 32.0 + inf, m))
    return out


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


def rot_body(pitch_d, yaw_d):
    return (Matrix.Rotation(R(yaw_d), 3, "Z") @ Matrix.Rotation(R(pitch_d), 3, "X"))


def solve_prime(p0, body_pos, rb, target):
    """Arm pose near p0 whose blade points 20 deg above the line from the fist to `target`: the arm stays where the take
    puts it (pitch / yaw held close), the forearm roll and the sword's tilt in the fist do the aiming; reach is kept."""
    def blade_and_fist(p):
        e_, m_ = arm_matrix(p)
        fist = body_pos + rb @ (m_ @ GRIP_LOC)
        blade = rb @ (m_.to_3x3() @ Matrix.Rotation(R(-p[3]), 3, "X") @ Vector((0, 1, 0)))
        return blade.normalized(), fist

    def want(p):
        _, fist = blade_and_fist(p)
        d = (target - fist).normalized()
        ax = d.cross(Vector((0, 0, 1))).normalized()
        return Matrix.Rotation(R(20), 3, ax) @ d

    def cost(p):
        b, _ = blade_and_fist(p)
        err = math.degrees(b.angle(want(p)))
        return err * err + 0.02 * ((p[0] - p0[0]) ** 2 + (p[1] - p0[1]) ** 2) + 1e-4 * (p[2] - p0[2]) ** 2

    p = list(p0)
    best = cost(p)
    for step in (8, 4, 2, 1, 0.5, 0.25, 0.1, 0.05, 0.02):
        improved = True
        while improved:
            improved = False
            for i in (0, 1, 2, 3):
                for sgn in (1, -1):
                    q = list(p); q[i] += sgn * step
                    cq = cost(q)
                    if cq < best - 1e-9:
                        p, best, improved = q, cq, True
    b, fist = blade_and_fist(p)
    d = (target - fist).normalized()
    above = math.degrees(math.asin(max(-1, min(1, b.z)))) - math.degrees(math.asin(max(-1, min(1, d.z))))
    return tuple(round(x, 2) for x in p), round(math.degrees(b.angle(d)), 2), round(above, 2), fist


dump = {"format": "per take: per tick right-arm rotation (pitch, yaw, roll in degrees, pitch 90 = ahead), shoulder reach "
                  "(m, + forward), tool tilt and twist, body offset (m: right, forward, up) and body yaw / view pitch (deg); "
                  "'hit' = the tick the sword connects; forming ticks 0-14 come first. 20 ticks a second.", "takes": {}}
BAY = 80.0
ORDER = list(T)
MODEL_AT = {}
MOB_TOP = 1.8
for bi, tk in enumerate(ORDER):
    S = T[tk]
    name, build, hits = S["name"], S["build"], S["hits"]
    tag = f"DC5 {tk} fp"
    wtag = f"DC5 {tk} world"
    bx = bi * BAY
    base = Vector((bx, 0.0, 1.62))
    raw = S["keys"]
    swing = raw[-1][0]
    total = FORM + swing + 10
    pk = [k[0] for k in raw if k[1] == "PRIME"]
    assert len(pk) == 2 and pk[1] - pk[0] == HOLD, tk
    tool = "sword"
    bxs = tool_boxes(tool)
    span = max(float(b[1]) for _, b, _ in bxs)

    def kk_of(t):
        return None if t < FORM or t - FORM > swing else t - FORM

    def curve(pts, k, hv=0.0):
        return curve_at([(a, (hv + b[1]) if isinstance(b, tuple) else b) for a, b in pts], k) if pts else 0.0

    def build_poses(prime):
        keys = [(k[0], *prime) if k[1] == "PRIME" else k for k in raw]
        return [list(REST) if kk_of(t) is None else pose_at(keys, kk_of(t)) for t in range(total + 1)]

    def body_state(t, fwd_h, up_h):
        k = kk_of(t)
        if k is None:
            k = 0 if t < FORM else swing
        pos = base + Vector((curve(S["side"], k), curve(S["fwd"], k, fwd_h), curve(S["up"], k, up_h)))
        return pos, curve(S["yaw"], k), curve(S["vyaw"], k), curve(S["vpitch"], k)

    # 1) the dash hit: solve the forward (and, for the dive, the height) so the far end meets the mob 12 m out
    t_main = FORM + S["main"]
    poses = build_poses(S["p0"])
    m_hit = arm_matrix(poses[t_main])[1] @ grip_matrix(poses[t_main][3])
    pos0, yw, _, vp = body_state(t_main, 0.0, 0.0)
    far0 = pos0 + rot_body(vp, yw) @ (m_hit @ Vector((0, span, 0)))
    fwd_h = DASH - far0.y
    up_h = 1.55 - far0.z if any(isinstance(b, tuple) for _, b in S["up"]) else 0.0
    pos_h, _, _, _ = body_state(t_main, fwd_h, up_h)
    tip_hit = pos_h + rot_body(vp, yw) @ (m_hit @ Vector((0, span, 0)))
    mob_x = tip_hit.x
    mob_home = Vector((mob_x, DASH + 0.03, 0.0))
    chest = Vector((mob_x, DASH + 0.2, 1.25))
    # 2) the prime: 20 deg above pointing at the mob's chest, from where the fist is during the hold
    tp = FORM + pk[0]
    pos_p, yw_p, _, vp_p = body_state(tp, fwd_h, up_h)
    prime, ang_, above_, fist_ = solve_prime(S["p0"], pos_p, rot_body(vp_p, yw_p), chest)
    S["prime_pose"], S["prime_angle"], S["prime_above"] = prime, ang_, above_
    poses = build_poses(prime)
    mats_ = [arm_matrix(p)[1] @ grip_matrix(p[3]) for p in poses]
    states = [body_state(t, fwd_h, up_h) for t in range(total + 1)]
    rbs = [rot_body(s[3], s[1]) for s in states]
    far_world = [states[t][0] + rbs[t] @ (mats_[t] @ Vector((0, span, 0))) for t in range(total + 1)]
    tips_local = [m_ @ Vector((0, 0.75, 0)) for m_ in mats_]
    path_y = [s[0].y for s in states]
    # ---- world: a long floor, a backdrop wall, the mob 12 blocks ahead
    y0, y1 = min(path_y) - 6, max(max(path_y), DASH) + 8
    box(f"{wtag} floor", (bx - 6, y0, -0.02), (bx + 14, y1, 0), FLOOR)
    box(f"{wtag} backdrop", (bx - 6.2, y0, 0), (bx - 6, y1, 7), WALL)
    for i in range(0, int(y1), 4):                                   # block-line marks every 4 blocks to read the distance
        box(f"{wtag} mark {i}", (bx - 1.5, i - 0.02, 0.0), (bx + 1.5, i + 0.02, 0.004), DUMMYH)
    tgt = link(bpy.data.objects.new(f"{wtag} mob pivot", None)); tgt.location = mob_home
    hb_ = [((-0.22, 0, 0), (0.22, 0.35, MOB_TOP - 0.3), DUMMY), ((-0.15, 0.03, MOB_TOP - 0.3), (0.15, 0.33, MOB_TOP), DUMMYH)]
    multibox(f"{wtag} mob", hb_, tgt, np.array((0.0, 0.17, 0.0)))
    tgt.rotation_mode = "XYZ"
    flash = box(f"{wtag} hit", (-0.2, -0.03, -0.2), (0.2, 0.0, 0.2), HIT)
    # ---- rig: body (position) -> torso (yaw, pitch) -> shoulder -> grip -> sword; body -> view (yaw, pitch) -> camera
    body = link(bpy.data.objects.new(f"{tag} body", None)); body.location = base
    torso = link(bpy.data.objects.new(f"{tag} torso", None)); torso.parent = body; torso.rotation_mode = "XYZ"
    view = link(bpy.data.objects.new(f"{tag} view", None)); view.parent = body; view.rotation_mode = "XYZ"
    sh, grip, ring_pt = make_arm(tag, torso)
    root = link(bpy.data.objects.new(f"{tag} tool", None)); root.parent = grip; root.rotation_mode = "XYZ"
    ticks = []
    hit_frames = []
    for t, p in enumerate(poses):
        pitch, yaw, roll, tilt, reach = p
        e_, _ = arm_matrix(p)
        sh.rotation_euler = e_; sh.keyframe_insert("rotation_euler", frame=t + 1)
        key(sh, t + 1, loc=tuple(SH_LOCAL + Vector((0, reach, 0))))
        key(grip, t + 1, rot=(R(-tilt), 0, 0))
        pos, yw, vyw, vp = states[t]
        key(body, t + 1, loc=tuple(pos))
        key(torso, t + 1, rot=(R(vp), 0, R(yw)))
        key(view, t + 1, rot=(R(vp), 0, R(vyw)))
        k_ = kk_of(t)
        hit_now = k_ is not None and k_ in hits
        if hit_now:
            hit_frames.append(t + 1)
        ticks.append({"arm": [round(pitch, 2), round(yaw, 2), round(roll, 2)], "tool_tilt": round(tilt, 2),
                      "reach": round(reach, 3), "hit": hit_now,
                      "body": [round(pos.x - bx, 3), round(pos.y, 3), round(pos.z - 1.62, 3)],
                      "body_yaw": round(yw, 2), "view_yaw": round(vyw, 2), "view_pitch": round(vp, 2)})
    for t in range(total + 1):                         # the green hit flash at the sword's far end on each hit
        hit_now = ticks[t]["hit"]
        if t == 0 or hit_now or ticks[t - 1]["hit"]:
            flash.location = far_world[t]; flash.keyframe_insert("location", frame=t + 1)
            flash.hide_render = not hit_now; flash.keyframe_insert("hide_render", frame=t + 1)
            flash.hide_viewport = not hit_now; flash.keyframe_insert("hide_viewport", frame=t + 1)
    # ---- the mob reacts on contact (from the dash hit): its own path per take, then it stays down
    f_main = t_main + 1
    key(tgt, 1, loc=tuple(mob_home), rot=(0, 0, 0)); key(tgt, f_main, loc=tuple(mob_home), rot=(0, 0, 0))
    for dt, x, y, z, rx, ry, rz in S["react"]:
        key(tgt, f_main + dt, loc=tuple(mob_home + Vector((x, y, z))), rot=(R(rx), R(ry), R(rz)))
    # ---- the working edge leads (body travel and turning don't turn the blade in the fist)
    phi_prev = 0.0
    for t in range(total + 1):
        k_ = kk_of(t)
        fx = None if k_ is None else next((dd for a_, b_, dd in S["fixed"] if a_ <= k_ <= b_), None)
        if fx is not None:
            phi = R(fx)
        else:
            v = tips_local[min(total, t + 1)] - tips_local[max(0, t - 1)]
            vg = mats_[t].to_3x3().inverted() @ v
            if math.hypot(vg.x, vg.z) > 0.004:
                phi = math.atan2(-vg.z, vg.x)
                alt = phi + math.pi
                phi = min((phi, alt), key=lambda a: abs((a - phi_prev + math.pi) % (2 * math.pi) - math.pi))
            else:
                phi = phi_prev
        phi = phi_prev + ((phi - phi_prev + math.pi) % (2 * math.pi) - math.pi)
        phi = phi_prev + (phi - phi_prev) * 0.65 if fx is None else phi
        phi_prev = phi
        key(root, t + 1, rot=(0, phi, 0))
        ticks[t]["tool_twist"] = round(math.degrees(phi), 2)
    # ---- the sword, in sections along its length
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
    lo_x = min(float(a[0]) for a, _, _ in bxs); hi_x = max(float(b[0]) for _, b, _ in bxs)
    lo_z = min(float(a[2]) for a, _, _ in bxs); hi_z = max(float(b[2]) for _, b, _ in bxs)
    # ---- the 0.7 s prime: a green charge shell over the blade, the ring flares, motes circle the blade
    c0, c1 = pk
    shell = box(f"{tag} charge shell", (lo_x - 0.02, -0.02, lo_z - 0.02), (hi_x + 0.02, span + 0.03, hi_z + 0.02), CHG, root)
    flare = box(f"{tag} ring flare", (-0.025, -0.025, -0.025), (0.025, 0.025, 0.025), PIX, sh, loc=tuple(ring_pt))
    motes = [box(f"{tag} charge mote {i}", (-0.012, -0.012, -0.012), (0.012, 0.012, 0.012), PIX, root) for i in range(6)]
    for t in range(total + 1):
        k_ = kk_of(t)
        on = k_ is not None and c0 <= k_ <= c1
        if on:
            w = (k_ - c0) / HOLD
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
    # ---- dash streak: a faint green trail on the floor-to-waist along the path, from release to just after the hit
    td0 = FORM + c1
    st = link(bpy.data.objects.new(f"{wtag} dash trail", None)); st.location = (states[td0][0].x, states[td0][0].y, 0.0)
    trail = [box(f"{wtag} dash streak {i}", (-0.01, 0, 0), (0.01, 1.0, 0.012), STREAK, st, loc=(dx_, 0, z_))
             for i, (dx_, z_) in enumerate(((-0.28, 0.55), (0.28, 0.75), (-0.18, 1.05), (0.2, 1.3)))]
    ys = states[td0][0].y; xs = states[td0][0].x
    Lh = max(0.001, states[t_main][0].y - ys)
    for t in range(total + 1):
        if t <= td0 or t > t_main + 5:
            key(st, t + 1, loc=(xs, ys, 0.0), sc=(1, 0.0001, 1))
        elif t <= t_main:
            key(st, t + 1, loc=(xs, ys, 0.0), sc=(1, max(0.0001, states[t][0].y - ys), 1))
        else:
            f_ = (t - t_main) / 5
            key(st, t + 1, loc=(xs, ys + f_ * Lh, 0.0), sc=(1, max(0.0001, Lh * (1 - f_)), 1))
    # ---- forming (ticks 0-14)
    rng = np.random.default_rng(859 + bi)
    m_rest = grip_matrix(REST[3])                     # tool space -> shoulder space during forming (twist 0)
    fam, var = build[0], build[1]
    if fam == "a":
        pm = bpy.data.meshes.new(f"{tag} px"); s_ = 0.022
        pm.from_pydata([(x, y, z) for x in (-s_, s_) for y in (-s_, s_) for z in (-s_, s_)], [], BOXF)
        pm.materials.append(PIX)
        for o, c in parts:
            frac = c[1] / span
            if var == "3":
                frac = 1 - frac                       # tip first
            f_arrive = 3 + int(round(frac * (FORM - 5)))
            if var == "3":
                key(o, 1, sc=0.0001); key(o, f_arrive - 1, sc=0.0001); key(o, f_arrive, sc=1.35); key(o, f_arrive + 2, sc=1.0)
            else:
                key(o, 1, sc=0.0001); key(o, f_arrive - 1, sc=0.0001); key(o, f_arrive + 1, sc=1.0)
            for j in range(3):
                px_ = link(bpy.data.objects.new(f"{tag} pixel", pm)); px_.parent = sh
                end = m_rest @ Vector(c + rng.uniform(-0.03, 0.03, 3))
                if var == "2":                        # spiral up the forearm from the elbow, then out to the part
                    th = rng.uniform(0, 2 * math.pi)
                    hel = [Vector((0.08 * math.cos(th + q * 2.1), 0.08 * math.sin(th + q * 2.1), -0.12 - 0.2 * q)) for q in range(3)]
                    f0 = max(1, f_arrive - 6 + j)
                    key(px_, 1, loc=hel[0], sc=0.0001); key(px_, f0, loc=hel[0], sc=0.0001)
                    key(px_, f0 + 1, loc=hel[0], sc=1.0); key(px_, f0 + 2, loc=hel[1], sc=1.0); key(px_, f0 + 3, loc=hel[2], sc=1.0)
                    key(px_, f_arrive + 1, loc=end, sc=0.5); key(px_, f_arrive + 2, loc=end, sc=0.0001)
                else:
                    start = ring_pt + Vector(rng.uniform(-0.015, 0.015, 3))
                    f0 = max(1, f_arrive - (2 if var == "3" else 4) + j - 1)
                    key(px_, 1, loc=start, sc=0.0001); key(px_, f0, loc=start, sc=0.0001); key(px_, f0 + 1, loc=start, sc=1.0)
                    if var == "1":
                        key(px_, f0 + 3, loc=(start + end) / 2 + Vector((0, 0.03, -0.03)), sc=1.0)
                    key(px_, f_arrive + 1, loc=end, sc=0.5); key(px_, f_arrive + 2, loc=end, sc=0.0001)
    # ---- record
    MODEL_AT[tk] = t_main + 1
    vis_far = eye_angles(mats_[t_main] @ Vector((0, span, 0)))
    dump["takes"][tk] = {"name": name, "build": BUILD_NAME[build], "forming_ticks": FORM, "combo_ticks": swing,
                         "hit_ticks": hits, "dash_hit_tick": S["main"], "prime_ticks": pk, "prime_pose": list(prime),
                         "prime_deg_above_mob": above_, "dash_m": round(states[t_main][0].y - states[FORM + pk[1]][0].y, 2),
                         "keys": [list(k) if k[1] != "PRIME" else [k[0], *prime] for k in raw], "ticks": ticks}
    # ---- cameras: the eye (rides the body), and a wide one from the right that sees the whole dash
    c = cam(f"Cam {tk}", (0, 0, 0), (0, 3, -0.25), 10.4)
    c.parent = view
    c.data.sensor_fit = "HORIZONTAL"; c.data.sensor_width = 36.0
    for nm_, a_, b_ in (("h", (-0.007, -0.0006, -0.2), (0.007, 0.0006, -0.2)), ("v", (-0.0006, -0.007, -0.2), (0.0006, 0.007, -0.2))):
        box(f"DC5 {tk} crosshair {nm_}", a_, b_, XH, c)
    ymid = (min(path_y) + max(max(path_y), DASH + 1.5)) / 2
    cam(f"Cam {tk} side", (bx + 12.5, ymid - 1.0, 3.2), (bx, ymid, 0.9), 18)
    cu = bpy.data.curves.new("DC5 label " + tk, "FONT"); cu.body = f"{tk}  {name}"
    cu.size = 0.3; cu.align_x = "CENTER"
    tl = link(bpy.data.objects.new("DC5 label " + tk, cu)); tl.location = (bx - 5.95, ymid, 3.6); tl.rotation_euler = (R(90), 0, R(90))
    tl.data.materials.append(GLOW)
    S["total"] = total
    print(tk, "| frames 1 -", total + 1, "| dash hit frame", t_main + 1, "| prime", prime, "blade", ang_, "deg off the mob line,",
          above_, "deg above it | dash", round(states[t_main][0].y - states[FORM + pk[1]][0].y, 2), "m, far end at",
          tuple(round(x - y, 2) for x, y in zip(far_world[t_main], (bx, 0, 0))), "| far end in view", vis_far, flush=True)

with open(os.path.join(FOLDER, "combat", "dash_combos_poses.json"), "w") as fh:
    json.dump(dump, fh, separators=(",", ":"))
with open(os.path.join(FOLDER, "combat", "dash_combos_takes.json"), "w") as fh:
    json.dump({tk: {"frames": [1, T[tk]["total"] + 1], "model_at": MODEL_AT[tk], "hits": T[tk]["hits"],
                    "build": T[tk]["build"], "name": T[tk]["name"], "prime": T[tk]["prime_pose"],
                    "prime_above": T[tk]["prime_above"], "crosses": T[tk]["crosses"], "prime_desc": T[tk]["prime_desc"],
                    "dash_desc": T[tk]["dash_desc"], "strike_desc": T[tk]["strike_desc"],
                    "react_desc": T[tk]["react_desc"], "combo": T[tk]["keys"][-1][0]} for tk in ORDER}, fh, indent=1)

scene.frame_start, scene.frame_end = 1, max(T[t]["total"] + 1 for t in ORDER)
world = bpy.data.worlds.new("DC5 world"); world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.32, 0.42, 0.55, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.7
scene.world = world
sun = link(bpy.data.objects.new("DC5 sun", bpy.data.lights.new("DC5 sun", "SUN")))
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
    tree = bpy.data.node_groups.new("DC5 Glow", "CompositorNodeTree")
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
scene.frame_set(MODEL_AT["C1e1"])
try:
    bpy.ops.outliner.orphans_purge(do_recursive=True)
except Exception:
    pass
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("saved", OUT)
